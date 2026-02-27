# HIBP Integration - Visual Guides & Diagrams

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                                   │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐      │
│  │  Password Input  │  │   Email Input    │  │  Other Features  │      │
│  └────────┬─────────┘  └────────┬─────────┘  └──────────────────┘      │
│           │                     │                                       │
└───────────┼─────────────────────┼───────────────────────────────────────┘
            │                     │
            ▼                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         FLASK BACKEND                                    │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │ /analyze              │ /check-email                            │   │
│  │ (POST)                │ (POST)                                  │   │
│  └────────┬───────────────┴────────────────┬───────────────────────┘   │
│           │                                │                           │
│           ▼                                ▼                           │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │ check_hibp_breach()      │  check_email_breach()                │   │
│  │ (Password Checker)       │  (Email Checker)                     │   │
│  └────────┬──────────────────┴────────────┬──────────────────────┬─┘   │
│           │                               │                      │     │
│           ▼                               ▼                      ▼     │
│  ┌──────────────────┐        ┌──────────────────┐   ┌─────────────┐   │
│  │ Check API Key    │        │ Validate Email   │   │ Local Check │   │
│  │ Available?       │        │ Format           │   │ (Fallback)  │   │
│  └────────┬─────────┘        └────────┬─────────┘   └─────────────┘   │
│           │                           │                               │
└───────────┼───────────────────────────┼───────────────────────────────┘
            │                           │
            │                           │
            ├─ YES ──────┐              │
            │            ▼              │
            │    ┌──────────────────┐   │
            │    │ Use API Key?     │   │
            │    │ Y = Send to HIBP │   │
            │    │ N = Local Only   │   │
            │    └────────┬─────────┘   │
            │             │             │
            │             ▼             ▼
            │    ┌──────────────────────────────┐
            │    │ EXTERNAL API CALLS           │
            │    ├──────────────────────────────┤
            │    │ pwnedpasswords.com/range/    │
            │    │ haveibeenpwned.com/api/v3/   │
            │    └────────┬───────────────────┬─┘
            │             │                   │
            │             ▼                   ▼
            │    ┌──────────────────┐  ┌──────────────────┐
            │    │ Parse Response   │  │ Extract Breaches │
            │    │ 200 OK ✓         │  │ List Breach Names│
            │    │ 404 Not Found    │  │ Show Severity    │
            │    │ 429 Rate Limited │  │                  │
            │    └────────┬─────────┘  └────────┬─────────┘
            │             │                     │
            └─────────────┴─────────────────────┘
                          │
                          ▼
            ┌─────────────────────────────────┐
            │ Format Response for User        │
            │ - Status (Safe/Breached)        │
            │ - Severity Level                │
            │ - Breach Count                  │
            │ - Specific Breaches (if email)  │
            └─────────────────────────────────┘
                          │
                          ▼
            ┌─────────────────────────────────┐
            │ Return JSON to Frontend         │
            └─────────────────────────────────┘
                          │
                          ▼
            ┌─────────────────────────────────┐
            │ Display Results to User         │
            │ - Color-coded status            │
            │ - Informative messages          │
            │ - Action recommendations        │
            └─────────────────────────────────┘
```

---

## Password Checking - Data Flow

### K-Anonymity Model (Privacy Protected)

```
Step 1: User enters password
┌────────────────────────────────────┐
│ User: "MyPassword123"              │
└────────────┬───────────────────────┘
             │
Step 2: Hash with SHA-1
         │
         ▼
┌────────────────────────────────────────────────────┐
│ SHA-1: F1D572645D88D5FF18F6401F6B1666C8F8E3C09B   │
└────────────┬───────────────────────────────────────┘
             │
Step 3: Split into prefix & suffix
         │
         ├─ SENT TO HIBP ──→ "F1D57"     (5 chars only!)
         │
         └─ KEPT LOCAL ───→ "2645D88D5FF18F6401F6B1666C8F8E3C09B"
             (confidential)
             │
Step 4: HIBP returns all hashes with prefix F1D57
         │
         ▼
┌────────────────────────────────────────────────────┐
│ HIBP Response (~500 hashes):                       │
│ 2645D88D5FF18F6401F6B1666C8F8E3C09B:2254650       │ ← MATCH!
│ 264C2B8D5...                        │
│ 264D5A7F1...                        │
│ ... (500 total)                     │
└────────────┬───────────────────────────────────────┘
             │
Step 5: App checks locally
         │
         ▼
┌────────────────────────────────────────────────────┐
│ Local Check:                                       │
│ "Is 2645D88D5FF18F6401F6B1666C8F8E3C09B in list?" │
│ YES! → BREACHED (2,254,650 times)                │
└────────────────────────────────────────────────────┘
```

**Security Benefit**: Even if HIBP were hacked, the attacker only has 5-character prefixes. With 1,048,576 possible combinations for 5 hex chars, recovering full password would be computationally infeasible.

---

## Email Checking - Two Modes

### Mode 1: With API Key (Real Data)

```
┌─────────────────┐
│ User Email      │
│ test@gmail.com  │
└────────┬────────┘
         │
         ▼
┌──────────────────────────────────────┐
│ Validate Format                      │
│ ✓ Contains @                         │
│ ✓ Valid domain                       │
│ ✓ Proper structure                   │
└────────┬───────────────────────────┐ │
         │                           │ │
    Valid│                   Invalid│ │
         │                           │ │
         ▼                           ▼
┌─────────────────┐      ┌───────────────────────┐
│ Check for API   │      │ Return Invalid Email  │
│ Key             │      │ Error Message         │
└────────┬────────┘      └───────────────────────┘
         │
    ✓ Key│
      Found
         │
         ▼
┌──────────────────────────────────────┐
│ Send to HIBP API:                    │
│ POST /api/v3/breachedaccount/        │
│ Headers: hibp-api-key: [YOUR_KEY]   │
│ Data: test@gmail.com                 │
└────────┬───────────────────────────┐ │
         │                           │ │
         │                    Status │ │
         │                    Codes: │ │
         │                           │ │
    ✓ 200│  404│  401│  429│  500+   │ │
         │     │     │     │         │ │
         ▼     ▼     ▼     ▼         ▼
    ┌───┐ ┌───┐┌──┐┌───┐ ┌───────┐
    │Got│ │No │┘Key│Rate│ │Server │
    │5 │ │Bre│ Err│Lim│ │  Down │
    │Br│ │ach│    │   │ │       │
    │ea│ │es │    │   │ │ Retry │
    │ch│ │   │    │   │ │Later  │
    │es│ │   │    │   │ │       │
    └───┘ └───┘    └───┘ └───────┘
      │    │        │       │
      ▼    ▼        ▼       ▼
  ┌─────────────────────────────────┐
  │ Format Response                 │
  │ - Breach list                   │
  │ - Severity level                │
  │ - Recommendation                │
  └─────────────────────────────────┘
```

### Mode 2: Without API Key (Fallback)

```
┌─────────────────┐
│ User Email      │
│ admin@test.com  │
└────────┬────────┘
         │
         ▼
┌──────────────────────────────────────┐
│ Validate Email Format                │
└────────┬───────────────────────────┐ │
         │                           │ │
    Valid│                   Invalid│ │
         │                           │ │
         ▼                           ▼
┌────────────────────┐   ┌─────────────────────┐
│ No API Key Set?    │   │ Return Invalid      │
│ Check Fallback     │   │ Format Error        │
└────────┬───────────┘   └─────────────────────┘
         │
    ✓ No │ Key
         │
         ▼
┌────────────────────────────────────────────┐
│ Local Pattern Detection:                   │
│                                            │
│ ✓ Check suspicious patterns:               │
│   - admin@  test@  demo@  guest@           │
│   - info@   support@  user1@               │
│                                            │
│ ✓ Check domain risk:                       │
│   - mail.ru  list.ru  bk.ru (high risk)   │
│   - gmail.com (normal)                    │
│                                            │
│ ✓ Check wordlist:                          │
│   - username in common.txt?               │
│                                            │
└────────┬───────────────────────────────────┘
         │
         ▼
    ┌────────────┬────────────┬────────────┐
    │            │            │            │
    ▼            ▼            ▼            ▼
┌────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐
│Pattern │ │ Domain   │ │Wordlist  │ │Safe    │
│Match:  │ │Risk:     │ │Match:    │ │Email   │
│ WARN   │ │ CAUTION  │ │ CAUTION  │ │ SAFE   │
│(High)  │ │(Medium)  │ │(Medium)  │ │(Safe)  │
└────────┘ └──────────┘ └──────────┘ └────────┘
    │         │           │             │
    └─────────┴───────────┴─────────────┘
              │
              ▼
  ┌──────────────────────────────┐
  │ Format Local Pattern Response │
  │ - Warning level              │
  │ - What was detected          │
  │ - Suggestion to verify       │
  └──────────────────────────────┘
```

---

## API Response Flowchart

```
┌────────────────────────┐
│ API Response Received  │
└────────────┬───────────┘
             │
             ▼
       ┌─────────────┐
       │ Status Code │
       └──┬──┬──┬──┬─┘
          │  │  │  │
    200───┘  │  │  └──── Other
       OK    │  │
            404 401 429 5xx
            │   │   │   │
            ▼   ▼   ▼   ▼
        Not │API │Rate│Server
        Found│Key │Limit│Down
            │Error│      │
            │     │      │
    ┌───────┴─┐   │      │
    │          │   │      │
    ▼          ▼   ▼      ▼
  Email    Invalid Rate   Retry
  Not      Key    Limit  Later
  Breached       Hit    (Fallback
  (Safe)         (Use    Local)
                Local)
             │   │       │
             └───┴───────┘
                 │
                 ▼
    ┌──────────────────────────┐
    │ Format Response JSON     │
    │ - is_leaked (bool)       │
    │ - message (string)       │
    │ - severity (string)      │
    │ - breach_count (int)     │
    │ - source (string)        │
    │ - breaches (array)       │
    └──────────────────────────┘
```

---

## Setup Flow - Getting API Key

```
Day 1: Setup
┌──────────────────────────────────┐
│ User wants real email results    │
└────────────┬─────────────────────┘
             │
             ▼
┌──────────────────────────────────────────┐
│ Visit: https://haveibeenpwned.com/API/Key│
└────────────┬─────────────────────────────┘
             │
             ▼
┌──────────────────────────────────┐
│ Create Account                   │
│ - Enter email                    │
│ - Create password                │
│ - Agree to terms                 │
└────────────┬─────────────────────┘
             │
             ▼
┌──────────────────────────────────┐
│ Verify Email                     │
│ - Check inbox for link           │
│ - Click verification link        │
└────────────┬─────────────────────┘
             │
             ▼
┌──────────────────────────────────┐
│ Got API Key!                     │
│ Example:                         │
│ a7x1b2c3d4e5f6g7h8i9j0k1l2m3n4o│
└────────────┬─────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────┐
│ Set Environment Variable (Choose ONE):           │
│                                                  │
│ Option 1 - PowerShell (Temporary):              │
│ $env:HIBP_API_KEY = "a7x1b2c3d4e5f6g7h8i9j0..." │
│                                                  │
│ Option 2 - .env File (Persistent):              │
│ Create .env                                      │
│ HIBP_API_KEY=a7x1b2c3d4e5f6g7h8i9j0...         │
│                                                  │
│ Option 3 - Windows System Var (Permanent):      │
│ Set HIBP_API_KEY in Environment Variables       │
└────────────┬─────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────┐
│ Restart Application              │
└────────────┬─────────────────────┘
             │
             ▼
    ┌────────────────────────┐
    │ Email Checker Now      │
    │ Uses Real HIBP Data ✓  │
    └────────────────────────┘
```

---

## Error Handling Flow

```
┌──────────────────────────────┐
│ Exception Occurs             │
└────────────┬─────────────────┘
             │
             ▼
       ┌──────────────┐
       │ Error Type   │
       └──┬──┬──┬──┬──┘
          │  │  │  │
          │  │  │  └─ Exception
          │  │  │
    Timeout Conn Validation
     │      │    │
     ▼      ▼    ▼
  Return  Return Return
  None    None   Error
  (Fall   (Fall  (Show
   back)   back)  User)
    │      │    │
    └──────┴────┘
          │
          ▼
┌───────────────────────────────────┐
│ Fallback to Local Checks          │
│ (Password/Email Validation Only)  │
└───────────────────────────────────┘
```

---

## Rate Limiting Behavior

### Password Checker Rate Limiting

```
Requests per minute: ~120
Usage: Normal traffic

If Exceeded:
┌─────────────────────────┐
│ 429 Rate Limit Hit      │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────────────┐
│ Fall Back to Local Wordlist     │
│ Check password against common   │
│ words (still works!)            │
└─────────────────────────────────┘
```

### Email Checker Rate Limiting

```
Free tier: ~10 requests/second
Premium tier: Higher limits

If Exceeded:
┌─────────────────────────┐
│ 429 Rate Limit Hit      │
└────────────┬────────────┘
             │
             ▼
┌──────────────────────────────────┐
│ Fall Back to Local Patterns      │
│ Check email for suspicious       │
│ patterns and domains             │
└──────────────────────────────────┘
```

---

## Security Layers

```
Layer 1: Input Validation
┌────────────────────────────────┐
│ Validate password length       │
│ Validate email format          │
│ Sanitize inputs                │
└────────────┬───────────────────┘
             │
             ▼
Layer 2: Local Processing
┌────────────────────────────────┐
│ Hash passwords locally         │
│ Check k-anonymity              │
│ Format validation              │
└────────────┬───────────────────┘
             │
             ▼
Layer 3: Secure Transmission
┌────────────────────────────────┐
│ HTTPS only                     │
│ Hash prefixes (not full)       │
│ Proper headers                 │
└────────────┬───────────────────┘
             │
             ▼
Layer 4: Response Processing
┌────────────────────────────────┐
│ Parse safely                   │
│ Validate response              │
│ Remove sensitive data          │
└────────────┬───────────────────┘
             │
             ▼
Layer 5: User Display
┌────────────────────────────────┐
│ Display results safely         │
│ Don't store passwords          │
│ Clear sensitive data on logout │
└────────────────────────────────┘
```

---

**Visual Guide Version**: 1.0  
**Last Updated**: January 24, 2026  
**HIBP Integration**: ✅ Complete
