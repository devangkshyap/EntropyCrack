# Have I Been Pwned (HIBP) API Integration Guide

## Overview

This application integrates with the **Have I Been Pwned (HIBP)** API to provide real-time breach detection for both passwords and email addresses. The integration includes two separate features:

### 1. **Password Breach Detection** (Public API - No Key Required)
- **Endpoint**: `https://api.pwnedpasswords.com/range/`
- **Authentication**: None required
- **Privacy Model**: k-anonymity (5-character hash prefix only)
- **Real-time**: Yes, live breach data
- **Cost**: Free

### 2. **Email Breach Detection** (Authenticated API - Requires API Key)
- **Endpoint**: `https://haveibeenpwned.com/api/v3/breachedaccount/`
- **Authentication**: API key required via `hibp-api-key` header
- **Real-time**: Yes, live breach data
- **Cost**: Free with API key registration

---

## How It Works

### Password Breach Checking

The password checker uses the **k-anonymity model** for maximum privacy:

1. **Hash the password** using SHA-1 algorithm
2. **Send only the first 5 characters** of the hash to HIBP
3. **Receive all hashes** starting with those 5 characters
4. **Check locally** if our full hash matches any returned hashes

**Example Flow**:
- User enters password: `MyPassword123`
- Hash (SHA-1): `F1D572645D88D5FF18F6401F6B1666C8F8E3C09B`
- Send to HIBP: `F1D57`
- HIBP returns: ~500 hashes starting with `F1D57`
- App checks locally if `2645D88D5FF18F6401F6B1666C8F8E3C09B` is in the list
- ✅ Your full password hash is never sent to HIBP

**Key Benefits**:
- No password ever transmitted
- Full password hash never transmitted
- Even 5-character prefix has 1,048,576 possible combinations
- Rate limited but no key required

### Email Breach Checking

The email checker queries the full HIBP database for breaches:

1. **User enters email address**
2. **Validate email format** locally
3. **Send email to HIBP API** with authentication key (if available)
4. **Receive list of breaches** where this email was found
5. **Display breach details** (breach name, date, type, etc.)

**Fallback Behavior**:
- If no API key is configured, the app uses **local pattern detection**
- Checks for suspicious email patterns (admin@, test@, demo@, etc.)
- Identifies high-risk domains commonly found in breaches
- Checks if username matches common wordlist entries

---

## Setup Instructions

### Step 1: Get Your HIBP API Key

1. Visit [https://haveibeenpwned.com/API/Key](https://haveibeenpwned.com/API/Key)
2. Create a free account if you don't have one
3. Verify your email address
4. Copy your API key (you'll see a string like `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`)

### Step 2: Configure Environment Variable

#### Option A: Windows (PowerShell)
```powershell
$env:HIBP_API_KEY = "your_api_key_here"
python app.py
```

#### Option B: Windows (Command Prompt)
```cmd
set HIBP_API_KEY=your_api_key_here
python app.py
```

#### Option C: Create .env file
Create a file named `.env` in the project root:
```
HIBP_API_KEY=your_api_key_here
```

Then install python-dotenv and load it:
```bash
pip install python-dotenv
```

Add to `app.py` at the top:
```python
from dotenv import load_dotenv
load_dotenv()
```

#### Option D: Permanent Environment Variable (Windows)
1. Press `Win + X` and select "System"
2. Click "Advanced system settings"
3. Click "Environment Variables"
4. Under "User variables", click "New"
5. Variable name: `HIBP_API_KEY`
6. Variable value: `your_api_key_here`
7. Click OK and restart your terminal/IDE

### Step 3: Verify Installation

Run the app and test both features:

```bash
python app.py
```

Navigate to:
- **Password Checker**: Enter a password and click "Check Breach"
- **Email Checker**: Enter an email and click "Check Email"

---

## API Response Examples

### Password Breach - Found
```json
{
  "is_leaked": true,
  "message": "⚠️ CRITICAL: This password has been seen 3,547,823 times in data breaches. Change it immediately!",
  "severity": "critical",
  "breach_count": 3547823,
  "source": "Have I Been Pwned API"
}
```

### Password Breach - Not Found
```json
{
  "is_leaked": false,
  "message": "Good news! This password was not found in any known data breaches.",
  "severity": "safe",
  "breach_count": 0,
  "source": "Have I Been Pwned API"
}
```

### Email Breach - Found
```json
{
  "is_leaked": true,
  "message": "⚠️ CRITICAL: This email has been found in 7 data breaches!",
  "severity": "critical",
  "breach_count": 7,
  "breaches": [
    "Adobe",
    "Dropbox",
    "LinkedIn",
    "Yahoo",
    "MySpace",
    "Equifax",
    "Twitter"
  ],
  "source": "Have I Been Pwned API (email)"
}
```

### Email Breach - Not Found
```json
{
  "is_leaked": false,
  "message": "Good news! This email was not found in any known data breaches.",
  "severity": "safe",
  "breach_count": 0,
  "breaches": [],
  "source": "Have I Been Pwned API (email)"
}
```

---

## Fallback Behavior

### When API Key is NOT Available

If `HIBP_API_KEY` environment variable is not set:

1. **Password Checker**: Continues to work (uses pwnedpasswords.com API - no key needed)
2. **Email Checker**: Falls back to local pattern detection:
   - Detects suspicious email patterns (admin@, test@, demo@)
   - Identifies risky domains (mail.ru, list.ru, etc.)
   - Checks username against common wordlist
   - Shows warnings instead of definitive breach results

### When API Key IS Available

- Email checker gets real breach data from HIBP
- Lists all breaches where the email was found
- Shows breach severity and count

---

## Rate Limiting

### Password Checker (pwnedpasswords.com)
- **Limit**: ~120 requests per minute per IP
- **Status Code 429**: If rate limited
- **Fallback**: Local wordlist check

### Email Checker (haveibeenpwned.com)
- **Limit**: Depends on API key tier (free tier: ~10 requests per second)
- **Status Code 429**: If rate limited
- **Fallback**: Falls back to local email pattern check

---

## API Errors & Troubleshooting

### Error: "HIBP API key rejected (401)"
**Cause**: Invalid or expired API key
**Solution**: 
1. Verify the API key is correct
2. Check if the key has been revoked
3. Re-register at https://haveibeenpwned.com/API/Key

### Error: "HIBP rate limit hit (429)"
**Cause**: Too many requests in short time
**Solution**:
1. Wait a few minutes before retrying
2. Implement request queuing for batch operations

### Error: "HIBP service unavailable (5xx)"
**Cause**: HIBP servers are down
**Solution**:
1. Check HIBP status at https://twitter.com/troyhunt
2. Retry in a few minutes
3. App automatically falls back to local checks

### Email Checker Not Checking Real Breaches
**Cause**: `HIBP_API_KEY` environment variable not set
**Solution**:
1. Follow "Configure Environment Variable" steps above
2. Restart the application
3. Verify in app console that the key is loaded

---

## API Documentation Links

- **HIBP API Docs**: https://haveibeenpwned.com/API/v3
- **Pwned Passwords API**: https://haveibeenpwned.com/API/v3#PwnedPasswords
- **Breached Account API**: https://haveibeenpwned.com/API/v3#BreachedAccount
- **Rate Limiting Info**: https://haveibeenpwned.com/API/v3#RateLimitation

---

## Security & Privacy Notes

✅ **What This App Does Right**:
- Passwords are hashed (SHA-1 & SHA-256) before any network transmission
- Password hashes are never sent to HIBP (only 5-char prefix)
- Full password never logged or persisted
- Email-to-breach mapping comes from HIBP, not stored locally
- All data remains in-session

⚠️ **Important Disclaimers**:
- This is educational software for learning about password security
- Do not use in production without proper security audit
- HIBP data is based on publicly disclosed breaches (may not include all breaches)
- Real breaches may not be immediately added to HIBP database

---

## Advanced Configuration

### Custom Error Handling

Edit `app.py` in the `check_email_breach()` function to customize error messages:

```python
except requests.Timeout:
    print("HIBP API timeout - falling back to local checks")
    return check_email_breach_local(email)
```

### Enable Detailed Logging

Add to `app.py`:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Then in functions:
logger.info(f"Checking email: {email}")
logger.debug(f"HIBP response: {response.status_code}")
```

### Cache Breach Results

Implement caching to avoid repeated API calls:

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def cached_check_email_breach(email: str):
    return check_email_breach(email)
```

---

## Testing

### Test Password Checker
```bash
curl -X POST http://localhost:5000/analyze \
  -H "Content-Type: application/json" \
  -d '{"password": "password123"}'
```

### Test Email Checker (with API key)
```bash
curl -X POST http://localhost:5000/check-email \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'
```

---

## Support & Additional Resources

- **HIBP API Support**: https://haveibeenpwned.com/Contact
- **Report a Breach**: https://haveibeenpwned.com/NotifyMe
- **Python Requests Docs**: https://requests.readthedocs.io/

---

## Version History

- **v1.0**: Initial HIBP integration with k-anonymity password checking
- **v1.1**: Added email breach checking with API key support
- **v1.2**: Added fallback pattern detection for emails
- **v1.3**: Enhanced error handling and rate limit management

---

**Last Updated**: January 2026
**HIBP Integration Status**: ✅ Active & Functional
