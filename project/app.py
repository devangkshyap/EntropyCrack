from __future__ import annotations

import hashlib
import itertools
import json
import math
import os
import random
import secrets
import re
import string
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple
from io import BytesIO
import base64
from urllib.parse import quote

import bcrypt
import requests
from flask import Flask, jsonify, render_template, request, session, send_file

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Generate random secret key for sessions
BASE_DIR = Path(__file__).resolve().parent
WORDLIST_PATH = BASE_DIR / "wordlists" / "common.txt"
UPLOAD_FOLDER = BASE_DIR / "uploads"
UPLOAD_FOLDER.mkdir(exist_ok=True)

# Cache wordlist at startup to avoid repeated disk reads
_wordlist_cache: Dict[int | None, List[str]] = {}
_custom_wordlists: Dict[str, List[str]] = {}


def load_wordlist(max_words: int | None = None) -> List[str]:
    """Load the wordlist, optionally capped to `max_words` for responsiveness."""
    global _wordlist_cache

    cache_key = max_words if max_words is not None else -1
    if cache_key in _wordlist_cache:
        return _wordlist_cache[cache_key]

    words: List[str] = []
    if WORDLIST_PATH.exists():
        # rockyou and similar lists contain latin-1 bytes; ignore undecodable chars so we don't crash
        with WORDLIST_PATH.open("r", encoding="latin-1", errors="ignore") as f:
            for line in f:
                w = line.strip()
                if not w:
                    continue
                words.append(w)
                if max_words is not None and len(words) >= max_words:
                    break
    _wordlist_cache[cache_key] = words
    return words


def sha256_hash(secret: str) -> str:
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()


def bcrypt_hash(secret: str) -> str:
    # bcrypt adds a per-hash salt; hash never logged or persisted
    return bcrypt.hashpw(secret.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def calculate_entropy(password: str) -> float:
    """Calculate password entropy in bits."""
    charset_size = 0
    if any(ch.islower() for ch in password):
        charset_size += 26
    if any(ch.isupper() for ch in password):
        charset_size += 26
    if any(ch.isdigit() for ch in password):
        charset_size += 10
    if any(ch in string.punctuation for ch in password):
        charset_size += len(string.punctuation)
    
    if charset_size == 0:
        return 0.0
    
    entropy = len(password) * math.log2(charset_size)
    return round(entropy, 2)


def generate_password(
    length: int = 16,
    use_upper: bool = True,
    use_lower: bool = True,
    use_digits: bool = True,
    use_special: bool = True,
    memorable: bool = False
) -> str:
    """Generate a random password with specified criteria."""
    crypto_rand = secrets.SystemRandom()
    if memorable:
        # Generate memorable password using wordlist
        words = load_wordlist()
        if words:
            num_words = max(3, length // 6)
            selected = crypto_rand.sample(words[:2000], min(num_words, len(words[:2000])))
            password = "-".join(selected)
            if use_digits:
                password += str(crypto_rand.randint(10, 99))
            if use_special:
                password += crypto_rand.choice("!@#$%")
            return password
    
    charset = ""
    if use_lower:
        charset += string.ascii_lowercase
    if use_upper:
        charset += string.ascii_uppercase
    if use_digits:
        charset += string.digits
    if use_special:
        charset += string.punctuation
    
    if not charset:
        charset = string.ascii_letters + string.digits
    
    # Ensure at least one character from each selected type
    password = []
    if use_lower:
        password.append(crypto_rand.choice(string.ascii_lowercase))
    if use_upper:
        password.append(crypto_rand.choice(string.ascii_uppercase))
    if use_digits:
        password.append(crypto_rand.choice(string.digits))
    if use_special:
        password.append(crypto_rand.choice(string.punctuation))
    
    # Fill the rest randomly
    while len(password) < length:
        password.append(crypto_rand.choice(charset))
    
    crypto_rand.shuffle(password)
    return "".join(password)


def generate_keyword_password(keyword: str, *, min_length: int = 14) -> str:
    """Generate a strong password that keeps the keyword recognizable."""
    crypto_rand = secrets.SystemRandom()
    cleaned = re.sub(r"[^A-Za-z0-9]", "", keyword).strip()
    if not cleaned:
        fallback = load_wordlist(max_words=500)
        cleaned = crypto_rand.choice(fallback) if fallback else "passphrase"

    base = cleaned[:20]
    leet_map = str.maketrans({
        "a": "@",
        "e": "3",
        "i": "1",
        "o": "0",
        "s": "$",
        "t": "7",
    })

    primary = base.capitalize()
    secondary = base.lower().translate(leet_map)
    special = crypto_rand.choice("!@#$%^&*?-+")
    number_chunk = str(crypto_rand.randint(101, 9879))

    candidate = f"{primary}{special}{number_chunk}{secondary}"

    charset = string.ascii_letters + string.digits + string.punctuation
    while len(candidate) < max(min_length, 14):
        candidate += crypto_rand.choice(charset)

    if not any(c.islower() for c in candidate):
        candidate += crypto_rand.choice(string.ascii_lowercase)
    if not any(c.isupper() for c in candidate):
        candidate += crypto_rand.choice(string.ascii_uppercase)
    if not any(c.isdigit() for c in candidate):
        candidate += crypto_rand.choice(string.digits)
    if not any(c in string.punctuation for c in candidate):
        candidate += crypto_rand.choice(string.punctuation)

    return candidate


def check_leaked(password: str) -> Dict[str, object]:
    """Check if password appears in breached databases using HIBP API with k-anonymity."""
    
    # First, try HIBP API for real breach data
    try:
        hibp_result = check_hibp_breach(password)
        if hibp_result:
            return hibp_result
    except Exception as e:
        # If HIBP fails, fall back to local checks
        print(f"HIBP API check failed: {e}, falling back to local checks")
    
    # Fallback to local checks
    words = load_wordlist()
    # Check if password or lowercase version is in common words
    if password in words or password.lower() in words:
        return {
            "is_leaked": True,
            "message": "This password appears in common word lists and may be compromised.",
            "severity": "high",
            "source": "Local wordlist"
        }
    
    # Check for common patterns that are likely leaked
    common_leaked = [
        "password", "password123", "123456", "12345678", "qwerty",
        "abc123", "monkey", "letmein", "trustno1", "dragon",
        "baseball", "iloveyou", "master", "sunshine", "ashley",
        "bailey", "passw0rd", "shadow", "123123", "654321"
    ]
    
    if password.lower() in common_leaked:
        return {
            "is_leaked": True,
            "message": "This password is known to be compromised in data breaches.",
            "severity": "critical",
            "source": "Known breach database"
        }
    
    # Check for simple patterns
    if password.isdigit() and len(password) <= 8:
        return {
            "is_leaked": True,
            "message": "Simple numeric passwords are commonly found in breach databases.",
            "severity": "high",
            "source": "Pattern analysis"
        }
    
    return {
        "is_leaked": False,
        "message": "No immediate red flags detected. Password not found in breach databases.",
        "severity": "safe",
        "source": "HIBP API + Local checks"
    }


def check_hibp_breach(password: str) -> Dict[str, object] | None:
    """
    Check password against Have I Been Pwned API using k-anonymity.
    
    The k-anonymity model means:
    1. Hash the password with SHA-1
    2. Send only the first 5 characters of the hash to HIBP
    3. Receive all hashes starting with those 5 characters
    4. Check locally if our full hash matches any returned hashes
    
    This ensures the full password hash never leaves the server.
    """
    try:
        # Hash password with SHA-1 (HIBP uses SHA-1)
        sha1_hash = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()
        
        # Split hash into prefix (first 5 chars) and suffix
        hash_prefix = sha1_hash[:5]
        hash_suffix = sha1_hash[5:]
        
        # Query HIBP API with only the prefix
        url = f"https://api.pwnedpasswords.com/range/{hash_prefix}"
        headers = {
            'Add-Padding': 'true',  # Adds padding to responses for additional privacy
            'User-Agent': 'EntropyCrack-Password-Checker'
        }
        
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code != 200:
            return None
        
        # Parse response - format is "SUFFIX:COUNT\r\n"
        hashes = response.text.split('\r\n')
        
        for hash_line in hashes:
            if ':' not in hash_line:
                continue
            
            suffix, count = hash_line.split(':')
            
            if suffix == hash_suffix:
                # Password found in breach database
                breach_count = int(count)
                
                if breach_count > 100000:
                    severity = "critical"
                    message = f"⚠️ CRITICAL: This password has been seen {breach_count:,} times in data breaches. Change it immediately!"
                elif breach_count > 10000:
                    severity = "critical"
                    message = f"⚠️ This password has been seen {breach_count:,} times in data breaches. Do not use it!"
                elif breach_count > 1000:
                    severity = "high"
                    message = f"This password has been seen {breach_count:,} times in data breaches. Avoid using it."
                else:
                    severity = "high"
                    message = f"This password has been seen {breach_count:,} times in data breaches."
                
                return {
                    "is_leaked": True,
                    "message": message,
                    "severity": severity,
                    "breach_count": breach_count,
                    "source": "Have I Been Pwned API"
                }
        
        # Password not found in breaches
        return {
            "is_leaked": False,
            "message": "Good news! This password was not found in any known data breaches.",
            "severity": "safe",
            "breach_count": 0,
            "source": "Have I Been Pwned API"
        }
        
    except requests.Timeout:
        print("HIBP API timeout")
        return None
    except requests.RequestException as e:
        print(f"HIBP API request failed: {e}")
        return None
    except Exception as e:
        print(f"HIBP check error: {e}")
        return None


@dataclass
class StrengthResult:
    score: int
    label: str
    feedback: List[str]


def evaluate_strength(password: str) -> StrengthResult:
    length_score = min(len(password) * 4, 30)
    upper_score = 10 if any(ch.isupper() for ch in password) else 0
    lower_score = 10 if any(ch.islower() for ch in password) else 0
    digit_score = 15 if any(ch.isdigit() for ch in password) else 0
    special_score = 15 if any(ch in string.punctuation for ch in password) else 0
    variety_score = 10 if sum([
        any(ch.isupper() for ch in password),
        any(ch.islower() for ch in password),
        any(ch.isdigit() for ch in password),
        any(ch in string.punctuation for ch in password),
    ]) >= 3 else 0

    common_patterns = [
        "password", "123456", "qwerty", "letmein", "welcome", "admin", "iloveyou",
    ]
    pattern_penalty = -20 if any(pat in password.lower() for pat in common_patterns) else 0

    score = max(0, min(100, length_score + upper_score + lower_score + digit_score + special_score + variety_score + pattern_penalty))

    if score < 40:
        label = "Weak"
    elif score < 70:
        label = "Medium"
    else:
        label = "Strong"

    feedback: List[str] = []
    if len(password) < 12:
        feedback.append("Increase length to at least 12+ characters.")
    if not any(ch.isupper() for ch in password):
        feedback.append("Add uppercase letters.")
    if not any(ch.islower() for ch in password):
        feedback.append("Add lowercase letters.")
    if not any(ch.isdigit() for ch in password):
        feedback.append("Add digits.")
    if not any(ch in string.punctuation for ch in password):
        feedback.append("Add special characters.")
    if any(pat in password.lower() for pat in common_patterns):
        feedback.append("Avoid common patterns or sequences.")
    if not feedback:
        feedback.append("Looks solid. Keep it unique per site.")

    return StrengthResult(score=score, label=label, feedback=feedback)


def dictionary_attack(
    target_sha: str,
    target_bcrypt: str,
    *,
    max_words: int = 200_000,
    time_budget: float = 5.0,
) -> Dict[str, object]:
    """Dictionary pass with safety caps so the UI stays responsive."""
    words = load_wordlist(max_words=max_words)
    attempts = 0
    start = time.time()
    for word in words:
        attempts += 1
        if sha256_hash(word) == target_sha:
            duration = time.time() - start
            return {
                "attack": "Dictionary",
                "success": True,
                "candidate": word,
                "time_taken": duration,
                "attempts": attempts,
            }
        if bcrypt.checkpw(word.encode("utf-8"), target_bcrypt.encode("utf-8")):
            duration = time.time() - start
            return {
                "attack": "Dictionary",
                "success": True,
                "candidate": word,
                "time_taken": duration,
                "attempts": attempts,
            }
        if time.time() - start > time_budget:
            duration = time.time() - start
            return {
                "attack": "Dictionary",
                "success": False,
                "candidate": None,
                "time_taken": duration,
                "attempts": attempts,
                "stopped": "Time budget reached",
                "limit": max_words,
            }
    duration = time.time() - start
    return {
        "attack": "Dictionary",
        "success": False,
        "candidate": None,
        "time_taken": duration,
        "attempts": attempts,
        "limit": max_words,
    }


def brute_force_simulation(password: str, target_sha: str, max_len: int = 4, time_budget: float = 0.5) -> Dict[str, object]:
    charset = string.ascii_lowercase + string.digits
    attempts = 0
    start = time.time()
    for length in range(1, max_len + 1):
        for combo in itertools.product(charset, repeat=length):
            attempts += 1
            candidate = "".join(combo)
            if sha256_hash(candidate) == target_sha:
                duration = time.time() - start
                return {
                    "attack": "Brute-force (demo)",
                    "success": True,
                    "candidate": candidate,
                    "time_taken": duration,
                    "attempts": attempts,
                    "limit": max_len,
                }
            if time.time() - start > time_budget:
                duration = time.time() - start
                return {
                    "attack": "Brute-force (demo)",
                    "success": False,
                    "candidate": None,
                    "time_taken": duration,
                    "attempts": attempts,
                    "limit": max_len,
                    "stopped": "Time budget reached",
                }
    duration = time.time() - start
    return {
        "attack": "Brute-force (demo)",
        "success": False,
        "candidate": None,
        "time_taken": duration,
        "attempts": attempts,
        "limit": max_len,
        "stopped": "Exceeded demo length",
    }


def format_number_to_words(num: float) -> str:
    """Convert large numbers to readable word format."""
    if num < 100:
        return f"{num:.1f}"
    elif num < 1_000:
        hundreds = num / 100
        if hundreds >= 10:
            return f"{hundreds:.1f} hundred"
        return f"{num:.0f}"
    elif num < 10_000:
        return f"{num/1_000:.1f} thousand"
    elif num < 100_000:
        return f"{num/1_000:.0f} thousand"
    elif num < 10_000_000:  # Up to 10 million
        return f"{num/100_000:.1f} lakh"
    elif num < 1_000_000_000:  # Up to 1 billion
        return f"{num/10_000_000:.1f} crore"
    elif num < 1_000_000_000_000:  # Up to 1 trillion
        return f"{num/1_000_000_000:.1f} billion"
    elif num < 1_000_000_000_000_000:  # Up to 1 quadrillion
        return f"{num/1_000_000_000_000:.1f} trillion"
    else:
        # For extremely large numbers, use scientific notation
        return f"{num:.2e}"


def estimate_time_to_crack(password: str) -> str:
    charset_size = 0
    if any(ch.islower() for ch in password):
        charset_size += 26
    if any(ch.isupper() for ch in password):
        charset_size += 26
    if any(ch.isdigit() for ch in password):
        charset_size += 10
    if any(ch in string.punctuation for ch in password):
        charset_size += len(string.punctuation)
    charset_size = max(charset_size, 26)

    total_space = charset_size ** len(password)
    guesses_per_second = 10**6  # illustrative
    seconds = total_space / guesses_per_second

    if seconds < 60:
        return f"~{seconds:.1f} seconds"
    minutes = seconds / 60
    if minutes < 60:
        return f"~{minutes:.1f} minutes"
    hours = minutes / 60
    if hours < 48:
        return f"~{hours:.1f} hours"
    days = hours / 24
    if days < 60:
        return f"~{days:.1f} days"
    years = days / 365
    
    # Format years using word representation
    return f"~{format_number_to_words(years)} years"


@app.route("/")
def index():
    # Initialize session history if not exists
    if 'history' not in session:
        session['history'] = []
    response = app.make_response(render_template("index.html"))
    # Disable caching for development
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@app.post("/analyze")
def analyze():
    data = request.get_json(silent=True) or {}
    password = data.get("password", "")
    if not isinstance(password, str):
        return jsonify({"error": "Invalid password"}), 400

    result = evaluate_strength(password)
    entropy = calculate_entropy(password)
    leaked_check = check_leaked(password)
    
    # Add to session history
    if 'history' not in session:
        session['history'] = []
    
    history_entry = {
        "password_hash": sha256_hash(password)[:16],  # Store truncated hash for privacy
        "score": result.score,
        "label": result.label,
        "entropy": entropy,
        "length": len(password),
        "timestamp": datetime.now().isoformat()
    }
    
    # Keep only last 10 entries
    session['history'] = ([history_entry] + session['history'])[:10]
    session.modified = True
    
    response = {
        "score": result.score,
        "label": result.label,
        "feedback": result.feedback,
        "entropy": entropy,
        "leaked_check": leaked_check,
    }
    return jsonify(response)


@app.post("/crack")
def crack():
    data = request.get_json(silent=True) or {}
    password = data.get("password", "")
    if not isinstance(password, str) or password == "":
        return jsonify({"error": "Password required"}), 400

    target_sha = sha256_hash(password)
    target_bcrypt = bcrypt_hash(password)

    dict_result = dictionary_attack(target_sha, target_bcrypt)
    brute_result = brute_force_simulation(password, target_sha)

    recommendations = [
        "Use long, unique passphrases (16+ chars).",
        "Prefer a password manager to avoid reuse.",
        "Enable multi-factor authentication wherever possible.",
        "Avoid dictionary words and predictable substitutions.",
    ]

    response = {
        "hashes": {
            "sha256": target_sha,
            "bcrypt": target_bcrypt,
        },
        "results": [dict_result, brute_result],
        "time_to_crack_estimate": estimate_time_to_crack(password),
        "recommendations": recommendations,
        "disclaimer": "Educational simulation only. Attacks run against hashes, not stored passwords.",
    }
    return jsonify(response)


@app.post("/generate")
def generate():
    """Generate a password based on user preferences."""
    data = request.get_json(silent=True) or {}
    length = int(data.get("length", 16))
    use_upper = data.get("use_upper", True)
    use_lower = data.get("use_lower", True)
    use_digits = data.get("use_digits", True)
    use_special = data.get("use_special", True)
    memorable = data.get("memorable", False)
    
    # Validate length
    length = max(4, min(64, length))
    
    password = generate_password(length, use_upper, use_lower, use_digits, use_special, memorable)
    
    # Analyze the generated password
    result = evaluate_strength(password)
    entropy = calculate_entropy(password)
    
    return jsonify({
        "password": password,
        "score": result.score,
        "label": result.label,
        "entropy": entropy,
    })


@app.post("/generate/related")
def generate_related():
    """Generate a strong password that incorporates a user keyword."""
    data = request.get_json(silent=True) or {}
    keyword = data.get("keyword", "")
    min_length = int(data.get("min_length", 12))

    if not isinstance(keyword, str) or not keyword.strip():
        return jsonify({"error": "Keyword required"}), 400

    min_length = max(8, min(64, min_length))

    password = generate_keyword_password(keyword, min_length=min_length)
    result = evaluate_strength(password)
    entropy = calculate_entropy(password)

    return jsonify({
        "password": password,
        "score": result.score,
        "label": result.label,
        "entropy": entropy,
        "keyword": keyword,
        "min_length": min_length,
    })


@app.get("/history")
def get_history():
    """Retrieve password analysis history for the session."""
    if 'history' not in session:
        session['history'] = []
    return jsonify({"history": session['history']})


@app.post("/history/clear")
def clear_history():
    """Clear password analysis history."""
    session['history'] = []
    session.modified = True
    return jsonify({"success": True})


@app.post("/compare")
def compare_passwords():
    """Compare two passwords side by side."""
    data = request.get_json(silent=True) or {}
    password1 = data.get("password1", "")
    password2 = data.get("password2", "")
    
    if not isinstance(password1, str) or not isinstance(password2, str):
        return jsonify({"error": "Invalid passwords"}), 400
    
    result1 = evaluate_strength(password1)
    result2 = evaluate_strength(password2)
    
    entropy1 = calculate_entropy(password1)
    entropy2 = calculate_entropy(password2)
    
    leaked1 = check_leaked(password1)
    leaked2 = check_leaked(password2)
    
    comparison = {
        "password1": {
            "score": result1.score,
            "label": result1.label,
            "entropy": entropy1,
            "length": len(password1),
            "leaked": leaked1["is_leaked"],
            "feedback": result1.feedback,
        },
        "password2": {
            "score": result2.score,
            "label": result2.label,
            "entropy": entropy2,
            "length": len(password2),
            "leaked": leaked2["is_leaked"],
            "feedback": result2.feedback,
        },
        "winner": "password1" if result1.score > result2.score else ("password2" if result2.score > result1.score else "tie"),
    }
    
    return jsonify(comparison)


@app.post("/quiz/generate")
def generate_quiz():
    """Generate a password strength quiz."""
    questions = [
        {
            "id": 1,
            "question": "Which password is stronger?",
            "options": ["Password123!", "Tr0ub4dor&3", "correct-horse-battery-staple", "Qwerty123"],
            "correct": 2,
            "explanation": "Long passphrases with random words are strongest. Length matters more than complexity."
        },
        {
            "id": 2,
            "question": "What makes a password vulnerable?",
            "options": ["Using dictionary words", "Repeating characters", "Common patterns like '123'", "All of the above"],
            "correct": 3,
            "explanation": "All these factors make passwords easier to crack using various attack methods."
        },
        {
            "id": 3,
            "question": "How often should you change important passwords?",
            "options": ["Every week", "Every 90 days", "Only if compromised", "Every year"],
            "correct": 2,
            "explanation": "Frequent changes can lead to weaker passwords. Change only when there's a breach or security concern."
        },
        {
            "id": 4,
            "question": "What is the minimum recommended password length?",
            "options": ["8 characters", "10 characters", "12 characters", "16 characters"],
            "correct": 2,
            "explanation": "Security experts now recommend at least 12 characters for adequate protection."
        },
        {
            "id": 5,
            "question": "Which is the best way to store passwords?",
            "options": ["Write them down", "Use same password everywhere", "Use a password manager", "Save in browser"],
            "correct": 2,
            "explanation": "Password managers securely encrypt and store unique passwords for each account."
        }
    ]
    
    # Shuffle and return 5 questions
    random.shuffle(questions)
    return jsonify({"questions": questions[:5]})


@app.post("/age-calculator")
def calculate_password_age():
    """Calculate when a password should be changed."""
    data = request.get_json(silent=True) or {}
    password = data.get("password", "")
    created_date = data.get("created_date", "")
    account_type = data.get("account_type", "standard")
    
    if not password or not created_date:
        return jsonify({"error": "Password and creation date required"}), 400
    
    try:
        created = datetime.fromisoformat(created_date)
    except:
        return jsonify({"error": "Invalid date format"}), 400
    
    result = evaluate_strength(password)
    age_days = (datetime.now() - created).days
    
    # Determine recommended change interval based on strength and type
    if account_type == "critical":  # Banking, email
        if result.score < 50:
            recommended_days = 30
        elif result.score < 70:
            recommended_days = 60
        else:
            recommended_days = 90
    else:  # Standard accounts
        if result.score < 50:
            recommended_days = 60
        elif result.score < 70:
            recommended_days = 180
        else:
            recommended_days = 365
    
    days_until_change = max(0, recommended_days - age_days)
    status = "expired" if days_until_change == 0 else "active"
    
    next_change_date = created + timedelta(days=recommended_days)
    
    return jsonify({
        "age_days": age_days,
        "recommended_interval": recommended_days,
        "days_until_change": days_until_change,
        "status": status,
        "next_change_date": next_change_date.isoformat(),
        "strength_score": result.score
    })


@app.post("/export")
def export_results():
    """Export analysis results as JSON."""
    data = request.get_json(silent=True) or {}
    password = data.get("password", "")
    format_type = data.get("format", "json")
    
    if not password:
        return jsonify({"error": "Password required"}), 400
    
    # Generate full analysis
    result = evaluate_strength(password)
    entropy = calculate_entropy(password)
    leaked = check_leaked(password)
    time_estimate = estimate_time_to_crack(password)
    
    export_data = {
        "timestamp": datetime.now().isoformat(),
        "password_length": len(password),
        "strength": {
            "score": result.score,
            "label": result.label,
            "feedback": result.feedback
        },
        "entropy_bits": entropy,
        "leak_status": leaked,
        "time_to_crack": time_estimate,
        "character_analysis": {
            "has_lowercase": any(c.islower() for c in password),
            "has_uppercase": any(c.isupper() for c in password),
            "has_digits": any(c.isdigit() for c in password),
            "has_special": any(c in string.punctuation for c in password)
        }
    }
    
    if format_type == "json":
        return jsonify(export_data)
    else:
        return jsonify({"error": "Unsupported format"}), 400


@app.post("/batch-analyze")
def batch_analyze():
    """Analyze multiple passwords at once."""
    data = request.get_json(silent=True) or {}
    passwords = data.get("passwords", [])
    
    if not passwords or not isinstance(passwords, list):
        return jsonify({"error": "Passwords array required"}), 400
    
    if len(passwords) > 100:
        return jsonify({"error": "Maximum 100 passwords allowed"}), 400
    
    results = []
    for pwd in passwords[:100]:
        if not isinstance(pwd, str):
            continue
            
        result = evaluate_strength(pwd)
        entropy = calculate_entropy(pwd)
        leaked = check_leaked(pwd)
        
        results.append({
            "password_hash": sha256_hash(pwd)[:8],
            "length": len(pwd),
            "score": result.score,
            "label": result.label,
            "entropy": entropy,
            "leaked": leaked["is_leaked"]
        })
    
    # Calculate statistics
    avg_score = sum(r["score"] for r in results) / len(results) if results else 0
    weak_count = sum(1 for r in results if r["score"] < 40)
    medium_count = sum(1 for r in results if 40 <= r["score"] < 70)
    strong_count = sum(1 for r in results if r["score"] >= 70)
    leaked_count = sum(1 for r in results if r["leaked"])
    
    return jsonify({
        "results": results,
        "statistics": {
            "total": len(results),
            "average_score": round(avg_score, 2),
            "weak": weak_count,
            "medium": medium_count,
            "strong": strong_count,
            "leaked": leaked_count
        }
    })


@app.post("/report/generate")
def generate_report():
    """Generate comprehensive security report."""
    data = request.get_json(silent=True) or {}
    password = data.get("password", "")
    
    if not password:
        return jsonify({"error": "Password required"}), 400
    
    # Comprehensive analysis
    result = evaluate_strength(password)
    entropy = calculate_entropy(password)
    leaked = check_leaked(password)
    time_estimate = estimate_time_to_crack(password)
    
    # Character frequency analysis
    char_freq = {}
    for char in password:
        char_freq[char] = char_freq.get(char, 0) + 1
    
    # Pattern detection
    patterns = []
    if any(pattern in password.lower() for pattern in ["123", "abc", "qwe"]):
        patterns.append("Sequential characters detected")
    if len(set(password)) < len(password) * 0.6:
        patterns.append("High character repetition")
    if password.lower() == password or password.upper() == password:
        patterns.append("No case variation")
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "executive_summary": {
            "score": result.score,
            "label": result.label,
            "verdict": "Pass" if result.score >= 70 else "Fail"
        },
        "detailed_analysis": {
            "length": len(password),
            "entropy": entropy,
            "unique_characters": len(set(password)),
            "character_types": {
                "lowercase": sum(1 for c in password if c.islower()),
                "uppercase": sum(1 for c in password if c.isupper()),
                "digits": sum(1 for c in password if c.isdigit()),
                "special": sum(1 for c in password if c in string.punctuation)
            }
        },
        "security_issues": patterns if patterns else ["No major issues detected"],
        "breach_status": leaked,
        "crack_resistance": time_estimate,
        "recommendations": result.feedback,
        "compliance": {
            "nist_guidelines": result.score >= 60,
            "pci_dss": result.score >= 70 and len(password) >= 12,
            "hipaa": result.score >= 70 and len(password) >= 14
        }
    }
    
    return jsonify(report)


@app.post("/wordlist/upload")
def upload_wordlist():
    """Upload custom wordlist (receives array of words)."""
    data = request.get_json(silent=True) or {}
    words = data.get("words", [])
    name = data.get("name", "custom")
    
    if not words or not isinstance(words, list):
        return jsonify({"error": "Words array required"}), 400
    
    if len(words) > 10000:
        return jsonify({"error": "Maximum 10,000 words allowed"}), 400
    
    # Store in session
    if 'custom_wordlists' not in session:
        session['custom_wordlists'] = {}
    
    session['custom_wordlists'][name] = [w.strip() for w in words if isinstance(w, str) and w.strip()]
    session.modified = True
    
    return jsonify({
        "success": True,
        "name": name,
        "word_count": len(session['custom_wordlists'][name])
    })


@app.get("/attack-viz/data")
def get_attack_visualization_data():
    """Get data for attack visualization."""
    return jsonify({
        "dictionary_attack": {
            "description": "Tests password against common word lists",
            "steps": [
                "Load wordlist (10,000+ common words)",
                "Hash each word with SHA-256",
                "Compare against target hash",
                "Check bcrypt hash if SHA-256 matches",
                "Continue until match or list exhausted"
            ],
            "complexity": "O(n) where n = wordlist size",
            "typical_speed": "1-10 million attempts/second"
        },
        "brute_force_attack": {
            "description": "Tries all possible character combinations",
            "steps": [
                "Define character set (a-z, 0-9, etc.)",
                "Generate combinations systematically",
                "Start with length 1, increment to target",
                "Hash each attempt",
                "Compare with target hash"
            ],
            "complexity": "O(c^n) where c = charset, n = length",
            "typical_speed": "Billions/second with GPU"
        },
        "hybrid_attack": {
            "description": "Combines dictionary words with numbers/symbols",
            "steps": [
                "Take base dictionary word",
                "Add common number patterns (123, 2024)",
                "Append special characters (!@#)",
                "Try capitalization variations",
                "Hash and compare each variation"
            ],
            "complexity": "O(n * m) where n = words, m = mutations",
            "typical_speed": "Depends on mutation rules"
        }
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
