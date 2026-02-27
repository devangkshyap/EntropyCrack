# Have I Been Pwned Integration - Quick Start

## What's New ✨

Your password security app now integrates with **Have I Been Pwned (HIBP)** - the world's largest database of breached passwords and hashed emails. This provides real-time checking to see if passwords or emails have appeared in known data breaches.

---

## Features

### 1. 🔐 **Real-Time Password Breach Checking**
- Checks if your password has been exposed in data breaches
- Uses **k-anonymity** - your password hash is never fully sent to HIBP
- Works without API key (completely free)
- Shows how many times a password has been seen in breaches

**Example**: Checking "password123" shows it's been seen **2,254,650 times** in breaches!

### 2. 📧 **Email Breach Verification**
- Checks if your email appears in known data breaches
- Lists all breaches where the email was found
- Shows breach severity levels (critical, high, medium)
- Optional API key for accurate results (free tier available)

---

## How to Use

### Password Checking (No Setup Required!)
1. Go to **Breach Detection** section
2. Enter any password
3. Click **Check Breach**
4. Get instant results showing breach history

### Email Checking (Optional Setup for Full Features)
1. Go to **Email Security** section
2. Enter your email address
3. Click **Check Email**
4. Works with or without API key!

---

## Setting Up Email Checking with Real Data

To see real breach data for emails, get your FREE HIBP API key:

### Quick Setup (5 minutes)

1. **Get API Key**
   - Visit: https://haveibeenpwned.com/API/Key
   - Sign up with your email
   - Verify your email
   - Copy your API key

2. **Configure Key** (Choose ONE option)

   **Option A - Temporary (Current Session Only)**
   ```powershell
   $env:HIBP_API_KEY = "your_api_key_here"
   python project/app.py
   ```

   **Option B - Permanent (Windows)**
   1. Press `Win + X` → "System"
   2. Click "Advanced system settings"
   3. Click "Environment Variables"
   4. New variable: `HIBP_API_KEY`
   5. Paste your API key
   6. Restart app

   **Option C - Using .env File**
   1. Copy `.env.example` to `.env`
   2. Add your API key: `HIBP_API_KEY=your_key_here`
   3. Restart app

3. **Test It**
   - Enter an email you own
   - Click "Check Email"
   - See real breach data!

---

## How It Works

### Password Checking (k-anonymity Model)

```
You type password:     "MyPassword123"
         ↓
App hashes (SHA-1):    "F1D572645D88D5FF18F..."
         ↓
Only send first 5:     "F1D57" ← Your full hash never sent!
         ↓
HIBP sends back:       "500 hashes starting with F1D57"
         ↓
App checks locally:    "Is my full hash in this list?"
         ↓
Result:                "YES / NO" - Your privacy protected!
```

### Email Checking

```
You type email:        "you@example.com"
         ↓
API key validates
         ↓
HIBP searches database
         ↓
Shows all breaches:    "Found in 3 breaches"
         ↓
Result:                Full breach details
```

---

## Test Results ✅

### Tested & Working:
- ✅ Password checker connects to HIBP API
- ✅ Detects breached passwords (tested with "password123" → 2.2M+ breaches)
- ✅ Email checker falls back to local patterns when no API key
- ✅ k-anonymity privacy model working correctly

---

## What's Protected?

| Data | Status | How |
|------|--------|-----|
| Your Password | ✅ Protected | Only partial hash sent to HIBP |
| Full Password Hash | ✅ Protected | Never transmitted to HIBP |
| Your Email | ✅ Protected | Only sent when checking email breaches |
| Session Data | ✅ Protected | Stored locally in session only |
| Passwords Stored | ✅ Never | No persistence - educational only |

---

## Common Questions

**Q: Does my password get sent to HIBP?**
A: No! Only a 5-character hash prefix is sent. The app checks locally if your full hash matches.

**Q: Do I need an API key?**
A: For emails: Optional (works without it, but uses local pattern detection)
   For passwords: No key needed! Works instantly.

**Q: What if HIBP API is down?**
A: App falls back to local checks automatically. Never crashes!

**Q: Is this safe to use?**
A: Yes! This is educational software. No data is stored or logged.

**Q: How often is HIBP data updated?**
A: Real-time as breaches are disclosed. Check Twitter: @troyhunt

---

## Technical Details

### Dependencies
- `requests` - For API calls to HIBP
- `python-dotenv` - For environment variables

### API Endpoints Used
- **Password**: `https://api.pwnedpasswords.com/range/` (Free, no auth)
- **Email**: `https://haveibeenpwned.com/api/v3/breachedaccount/` (Free with API key)

### Rate Limits
- **Password**: ~120 requests/minute
- **Email**: Depends on tier (free is ~10 req/sec)

If rate limited, app automatically falls back to local checks.

---

## Troubleshooting

**"Email checker says safe but I think I'm breached"**
→ You need to set the `HIBP_API_KEY` environment variable to get real data

**"API key rejected error"**
→ Check your key is correct at https://haveibeenpwned.com/API/Key

**"Service unavailable error"**
→ HIBP might be down. Check: https://twitter.com/troyhunt

**"Rate limit exceeded"**
→ Wait a few minutes and try again. App uses local fallback.

---

## Learn More

- **HIBP Official Site**: https://haveibeenpwned.com
- **HIBP API Docs**: https://haveibeenpwned.com/API/v3
- **K-Anonymity Explained**: https://en.wikipedia.org/wiki/K-anonymity
- **Password Security Best Practices**: https://www.nist.gov/publications/sp-800-63-3

---

## Full Setup Guide

For detailed setup instructions, see: [HIBP_INTEGRATION.md](HIBP_INTEGRATION.md)

---

**Status**: ✅ Integration Complete & Tested  
**Last Updated**: January 2026  
**HIBP Data**: Real-time & Accurate
