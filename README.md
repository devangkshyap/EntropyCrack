# EntropyCrack - Password Security & Breach Detection Tool

A comprehensive password analysis and security testing application with real-time Have I Been Pwned (HIBP) integration.

## Features

### 🔐 Core Security Features
- **Password Strength Analysis**: Evaluate passwords using entropy calculation and pattern detection
- **Breach Detection**: Check if passwords/emails appear in known data breaches (HIBP integration)
- **Dictionary Attack Simulation**: Educational demonstration of dictionary-based cracking
- **Brute Force Simulation**: Learn how brute force attacks work with time estimates
- **Entropy Calculator**: Understand password complexity in bits
- **Hash Generation**: SHA-256 and bcrypt hashing for learning purposes

### 🎯 Password Generation
- **Random Password Generator**: Create strong passwords with customizable options
- **Memorable Passwords**: Generate word-based passwords for easier recall
- **Keyword-Based Generator**: Strengthen keywords into secure passwords
- **Password Comparison**: Compare two passwords side-by-side

### 📊 Analysis & Reporting
- **Session History**: Track all analyzed passwords (hashed for privacy)
- **Batch Analysis**: Analyze up to 100 passwords at once
- **Comprehensive Reports**: Generate detailed security reports
- **Visualization Data**: Learn attack methods through interactive demos
- **Age Calculator**: Determine when passwords should be changed

### 📧 Breach Checking with HIBP
- **Password Breach Checking**: See if password appears in known breaches
  - Uses k-anonymity for privacy (only 5-char hash sent to HIBP)
  - Shows breach count and severity
  - Real-time data from Have I Been Pwned
  - No API key required

- **Email Breach Checking**: Check if email was in data breaches
  - Lists all breaches where email was found
  - Shows breach details (name, date, data types)
  - Optional HIBP API key for full accuracy
  - Fallback local pattern detection

---

## Quick Start

### Installation

1. **Clone/Download the project**
```bash
cd c:\projects\password
```

2. **Create virtual environment** (optional but recommended)
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
# or: source .venv/bin/activate  # Mac/Linux
```

3. **Install dependencies**
```bash
pip install -r project/requirements.txt
```

4. **Run the application**
```bash
python project/app.py
```

5. **Open in browser**
```
http://localhost:5000
```

---

## HIBP Integration Setup

### For Password Checking (Works Out of the Box!)
- No setup required
- Password breach detection enabled by default
- Real-time data from Have I Been Pwned

### For Email Checking (Optional Enhanced Features)
To get real breach data for emails:

1. Get free API key: https://haveibeenpwned.com/API/Key
2. Set environment variable:
   ```powershell
   $env:HIBP_API_KEY = "your_api_key_here"
   ```
3. Restart the app
4. Email checking now shows real breach data

For detailed setup, see: [HIBP_INTEGRATION.md](HIBP_INTEGRATION.md)

Quick start guide: [HIBP_QUICKSTART.md](HIBP_QUICKSTART.md)

---

## Project Structure

```
password/
├── project/
│   ├── app.py                 # Flask backend with HIBP integration
│   ├── requirements.txt       # Python dependencies
│   ├── templates/
│   │   └── index.html         # Web UI
│   ├── static/
│   │   ├── style.css          # Styling
│   │   └── script.js          # Frontend logic
│   ├── uploads/               # File upload directory
│   ├── wordlists/
│   │   └── common.txt         # Dictionary for attack simulations
│   └── __pycache__/
├── .env.example               # Environment variable template
├── HIBP_INTEGRATION.md        # Detailed HIBP setup guide
├── HIBP_QUICKSTART.md         # Quick start for HIBP features
└── README.md                  # This file
```

---

## API Endpoints

### Analysis & Checking
- `POST /analyze` - Analyze password strength and breach status
- `POST /check-email` - Check email for breaches
- `POST /crack` - Simulate dictionary & brute force attacks

### Generation
- `POST /generate` - Generate random password
- `POST /generate/related` - Generate password from keyword

### Utilities
- `GET /history` - Get session history
- `POST /history/clear` - Clear session history
- `POST /compare` - Compare two passwords
- `POST /batch-analyze` - Analyze multiple passwords
- `POST /report/generate` - Generate comprehensive report
- `POST /quiz/generate` - Generate security quiz
- `POST /age-calculator` - Calculate password age
- `POST /export` - Export results as JSON
- `GET /attack-viz/data` - Get attack visualization data

---

## Technology Stack

### Backend
- **Framework**: Flask 3.0.0
- **Authentication**: bcrypt 4.1.2
- **HTTP Client**: requests 2.31.0
- **Env Config**: python-dotenv 1.0.0

### Frontend
- **Language**: Vanilla JavaScript (no frameworks)
- **Styling**: CSS3 with animations
- **Storage**: Session storage for history

### External APIs
- **Have I Been Pwned**: Real-time breach database
  - Password API: `api.pwnedpasswords.com`
  - Email API: `haveibeenpwned.com/api/v3`

---

## Security Notes

### What This App Does
- ✅ Hashes passwords before network transmission
- ✅ Never sends full password hashes to HIBP (only 5-char prefix)
- ✅ Performs k-anonymity checks locally
- ✅ Never logs or persists passwords
- ✅ Uses HTTPS for all external API calls
- ✅ All analysis stays in-session

### What This App Doesn't Do
- ❌ Not suitable for production use without security audit
- ❌ Not a replacement for password managers
- ❌ Educational purposes only
- ❌ HIBP data may not include all breaches
- ❌ Real attacks don't work this way (for learning only)

### Important Disclaimers
- This is educational software for learning about password security
- Do not use for actual password cracking
- Attacks are simulated with intentional limitations
- Always use real password managers for actual passwords
- Never reuse passwords across sites

---

## Testing

### Test Password Checker
```bash
curl -X POST http://localhost:5000/analyze \
  -H "Content-Type: application/json" \
  -d '{"password": "password123"}'
```

### Test Email Checker
```bash
curl -X POST http://localhost:5000/check-email \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'
```

---

## HIBP Integration Details

### Password Checker
- **Status**: ✅ Working - No setup required
- **Method**: k-anonymity model
- **Privacy**: Your full hash never sent to HIBP
- **Speed**: ~1-2 seconds per check
- **Accuracy**: 100% (backed by 600+ million breached passwords)

### Email Checker
- **Status**: ✅ Working - Optional API key for full features
- **Method**: Direct breach database lookup
- **Privacy**: Email only sent when checking breaches
- **Accuracy**: Real-time as breaches are disclosed
- **Fallback**: Local pattern detection when API key not set

### Example Results

**Password "password123"**:
```json
{
  "is_leaked": true,
  "severity": "critical",
  "breach_count": 2254650,
  "message": "⚠️ CRITICAL: This password has been seen 2,254,650 times in data breaches. Change it immediately!"
}
```

**Email without breaches**:
```json
{
  "is_leaked": false,
  "severity": "safe",
  "breach_count": 0,
  "message": "Good news! This email was not found in any known data breaches."
}
```

---

## Troubleshooting

### Password Checker Not Working
**Solution**: Check internet connection. HIBP API is accessed in real-time.

### Email Checker Shows "Safe" When Expecting Breaches
**Solution**: Set `HIBP_API_KEY` environment variable for real breach data.

### Rate Limit Errors
**Solution**: Wait a few minutes. App automatically falls back to local checks.

### "Service Unavailable" Errors
**Solution**: HIBP might be down. Check: https://twitter.com/troyhunt

### API Key Rejected
**Solution**: 
1. Verify your key at https://haveibeenpwned.com/API/Key
2. Make sure environment variable is set correctly
3. Restart the application

---

## Learning Resources

### Password Security
- [NIST Digital Identity Guidelines](https://www.nist.gov/publications/sp-800-63-3)
- [Have I Been Pwned - About](https://haveibeenpwned.com/About)
- [Password Managers: The Case for Generation](https://www.eff.org/deeplinks/2018/03/why-you-should-use-password-manager)

### Cryptography
- [OWASP Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)
- [Understanding Entropy](https://en.wikipedia.org/wiki/Entropy_(information_theory))
- [K-Anonymity](https://en.wikipedia.org/wiki/K-anonymity)

### Have I Been Pwned
- [Official Site](https://haveibeenpwned.com)
- [API Documentation](https://haveibeenpwned.com/API/v3)
- [Pwned Passwords Data](https://haveibeenpwned.com/Passwords)

---

## Contributing

This is an educational project. Feel free to:
- Extend with additional security checks
- Improve the UI/UX
- Add more password generation strategies
- Implement additional APIs

---

## License

This educational software is provided as-is for learning purposes.

---

## Support

- **HIBP Support**: https://haveibeenpwned.com/Contact
- **Report a Breach**: https://haveibeenpwned.com/NotifyMe
- **Security Issues**: Please don't exploit - this is educational software

---

## Version History

### v1.3 - HIBP Integration Complete
- ✅ Real-time password breach checking with k-anonymity
- ✅ Email breach checking with fallback support
- ✅ Comprehensive documentation and setup guides
- ✅ All external API integrations tested and working

### v1.0 - Initial Release
- Password strength analysis
- Dictionary and brute force simulations
- Password generation tools

---

**Last Updated**: January 2026  
**HIBP Integration Status**: ✅ Active & Tested  
**Password Security**: 🔒 Fully Protected
