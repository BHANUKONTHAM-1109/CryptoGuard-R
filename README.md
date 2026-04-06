# CryptoGuard-R

AI & Cryptography Based Defense Against AI-Powered Phishing Attacks on Robotic and Enterprise Systems.

---

## Quick Start

```powershell
cd cryptoguard-r
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
copy .env.example .env
cd backend
..\venv\Scripts\python.exe -c "from app.ai.phishing_model import train_and_save; train_and_save()"
..\venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Then open http://localhost:8000/ui/ and http://localhost:8000/docs

---

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────────┐
│  Frontend   │────▶│  API Layer  │────▶│ Command Gateway │
│  (HTML/JS)  │     │  FastAPI    │     │  (sign+replay)  │
└─────────────┘     └─────────────┘     └────────┬────────┘
       │                    │                     │
       │                    │            ┌────────▼────────┐
       │                    │            │ Robot Simulator │
       │                    │            └─────────────────┘
       │                    │
       │            ┌───────▼───────┐
       │            │ Phishing AI   │
       │            │ (TF-IDF+LR)   │
       │            └───────────────┘
       │
       └────────────▶ Crypto (RSA-PSS, AES-256-GCM)
```

- **Frontend**: Minimal HTML/CSS/JS dashboard; phishing check, signed robot commands
- **API**: FastAPI routes for phishing, crypto (sign/verify), robot
- **Command Gateway**: Verifies signature, replay check, phishing risk; forwards to simulator
- **Phishing AI**: NLTK + scikit-learn TF-IDF + LogisticRegression
- **Crypto**: RSA-2048 signatures, AES-256-GCM, SHA-256

---

## Threat Model

| Threat | Mitigation |
|--------|------------|
| **AI-powered phishing** (deceptive messages) | ML classifier scores text; high-risk source rejected |
| **Unauthorized commands** | RSA-PSS signature required; only holder of private key can sign |
| **Replay attacks** | Duplicate (command, signature) within 5 min rejected |
| **Injection** | Pydantic validation; env `extra="ignore"`; input sanitization |
| **DoS** | Rate limiting (100 req/min per IP) |
| **Tampering** | AES-GCM auth tag; RSA-PSS integrity |

---

## How Phishing is Prevented

1. **Detection**: Messages/emails are scored by a trained TF-IDF + LogisticRegression model. Phishing-like text (urgent, free, click, etc.) gets a high score (0.7+).

2. **Command gate**: When a robot command is submitted with optional `source_context`, that context is scored. If score ≥ 0.7, the command is rejected—assumed to come from a phishing or deceptive source.

3. **Signatures**: Commands must be signed with the server's private key. An attacker cannot forge valid signatures without the key.

4. **Replay**: Same signed command cannot be replayed within 5 minutes; hash of (command, signature) is stored and checked.

---

## STEP 1: Environment Setup

### Prerequisites

- Python 3.10 or higher
- pip

### Commands (Windows PowerShell)

```powershell
# 1. Navigate to project
cd cryptoguard-r

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
.\venv\Scripts\Activate.ps1

# 4. Upgrade pip
python -m pip install --upgrade pip

# 5. Install dependencies
pip install -r backend\requirements.txt

# 6. Copy environment template
copy .env.example .env

# 7. Verify FastAPI (run server)
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Commands (Linux / macOS)

```bash
# 1. Navigate to project
cd cryptoguard-r

# 2. Create virtual environment
python3 -m venv venv

# 3. Activate virtual environment
source venv/bin/activate

# 4. Install dependencies
pip install -r backend/requirements.txt

# 5. Copy environment template
cp .env.example .env

# 6. Verify FastAPI
cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Expected Output

When FastAPI runs successfully, you should see:

```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

Visit http://localhost:8000 in a browser or run:

```bash
curl http://localhost:8000
```

Response:

```json
{
  "status": "ok",
  "service": "CryptoGuard-R",
  "message": "AI & Cryptography defense system is running"
}
```

### Dataset Requirements (for later steps)

| Step  | Dataset                    | Location              | Purpose                               |
|-------|----------------------------|------------------------|---------------------------------------|
| STEP 4| `phishing_emails.csv`      | `datasets/`            | Train AI phishing detection model     |

**Format for `phishing_emails.csv`:** Two columns required:
- `text` (or `email_text`, `message`): Email/message content
- `label` (or `is_phishing`): `1` = phishing, `0` = legitimate

Example sources (public datasets):
- [Spam Assassin Public Corpus](http://www.aueb.gr/users/ion/data/enron-spam/)
- [SMS Spam Collection (UCI)](https://archive.ics.uci.edu/ml/datasets/SMS+Spam+Collection)
- [Phishing Corpus (PhishTank, etc.)](https://www.phishsite.com/)

You will add this dataset in **STEP 4** before training the model.

---

## STEP 2: Configuration & Logging

### Implemented

- **`backend/app/core/config.py`**: Centralized configuration via `pydantic-settings`
  - Loads from `.env` (searches upward from backend/)
  - Validates `SECRET_KEY` (min 16 chars), `DATABASE_URL` (no path traversal)
  - Type coercion for port, rate limits, etc.
  - `extra="ignore"` to reject unknown env vars (injection prevention)

- **`backend/app/core/logging.py`**: Centralized logging
  - Console + file handler (`logs/cryptoguard-r.log`)
  - Log level from `DEBUG` setting
  - Structured format: timestamp | level | logger | message
  - Never log secrets (documented in module)

- **`backend/app/main.py`**: Uses config and logging
  - Lifespan events for startup/shutdown logs
  - Warns if default SECRET_KEY is used in non-production

### How to Run

```powershell
cd cryptoguard-r\backend
..\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### Expected Output

- Console: `Starting CryptoGuard-R (env=development)`
- Log file: `cryptoguard-r/logs/cryptoguard-r.log` created with startup entries

### Security Reasoning

- No secrets in code; all from env
- `extra="ignore"` prevents env var injection
- Path validation prevents traversal in DB URL

---

## STEP 3: Cryptography Layer

### Implemented

- **`backend/app/crypto/key_manager.py`**: RSA/ECC key generation and storage
  - RSA-2048 keypairs (NIST-approved)
  - Load/save PEM; auto-generate if missing
  - ECC P-256 support (alternative)

- **`backend/app/crypto/signature.py`**: Digital signatures
  - RSA-PSS with SHA-256 (provably secure)
  - Sign/verify strings and bytes

- **`backend/app/crypto/encryption.py`**: Symmetric crypto and hashing
  - AES-256-GCM (authenticated encryption)
  - SHA-256 and SHA-3-256 hashes
  - PBKDF2 password-derived keys

### Cryptographic Choices

| Component | Choice | Reason |
|-----------|--------|--------|
| Asymmetric | RSA-2048 | Industry standard, FIPS-approved |
| Signature | RSA-PSS | Resistant to forgeries; probabilistic |
| Hash | SHA-256 | NIST approved, widely supported |
| Hash alt | SHA-3-256 | Different construction; future-proof |
| Symmetric | AES-256-GCM | Confidentiality + integrity (auth tag) |
| KDF | PBKDF2-HMAC-SHA256 | OWASP-recommended iterations |

### How to Run (Verify)

```powershell
cd cryptoguard-r\backend
..\venv\Scripts\python.exe -c "
from pathlib import Path
from app.crypto import get_or_create_rsa_keys, sign_string, verify_string_signature, sha256_hash, aes_encrypt_with_password, aes_decrypt_with_password
priv, pub = get_or_create_rsa_keys(Path('keys/rsa_private.pem'), Path('keys/rsa_public.pem'))
print('Sign/verify:', verify_string_signature('MOVE 5', sign_string('MOVE 5', priv), pub))
print('AES:', aes_decrypt_with_password(aes_encrypt_with_password(b'x', 'pwd'), 'pwd') == b'x')
"
```

### Expected Output

```
Sign/verify: True
AES: True
```

### Security Reasoning

- RSA-PSS over PKCS1v15: provably secure
- AES-GCM: detects tampering (auth tag)
- PBKDF2: 100k iterations per OWASP
- Keys stored in `backend/keys/` (add to .gitignore)

---

## STEP 4: AI Phishing Detection Engine

### Implemented

- **`backend/app/ai/nlp_utils.py`**: NLP preprocessing
  - NLTK tokenization, stopwords, lemmatization
  - URL/email removal, text cleaning

- **`backend/app/ai/phishing_model.py`**: ML model
  - Load dataset: `phishing_emails.csv` or `spam.csv` (v1/v2)
  - TF-IDF + LogisticRegression pipeline
  - Train, save, load, predict

### Feature Selection

| Feature | Reason |
|---------|--------|
| TF-IDF (unigram + bigram) | Discriminative terms: "free", "win", "click", "urgent" |
| max_features=10000 | Limit vocabulary; reduce overfitting |
| min_df=2 | Ignore rare tokens (noise) |
| LogisticRegression | Calibrated probabilities for thresholding |

### Supported Datasets

- `datasets/phishing_emails.csv`: columns `text`, `label` (1=phishing, 0=legit)
- `datasets/spam.csv` or `spam.csv`: columns `v1` (ham/spam), `v2` (message)

### How to Run

**1. Train model (once):**
```powershell
cd cryptoguard-r\backend
..\venv\Scripts\python.exe -c "from app.ai.phishing_model import train_and_save; train_and_save()"
```

**2. Inference:**
```powershell
..\venv\Scripts\python.exe -c "
from app.ai.phishing_model import get_model, get_phishing_score
m = get_model()
print(get_phishing_score(m, 'Free prize! Click here'))
"
```

### Expected Output

- Training: ~98% accuracy on UCI SMS spam
- Inference: spam text → ~0.9+, legit → ~0.1

---

## STEP 5: Robotic Command Simulation

### Implemented

- **`backend/app/robot/simulator.py`**: Simulated robot
  - Allowed commands: MOVE_FORWARD, MOVE_BACKWARD, TURN_LEFT, TURN_RIGHT, STOP
  - Maintains state: x, y, heading_deg
  - Whitelist-only; unknown commands rejected

- **`backend/app/robot/command_gateway.py`**: Security gate
  - Requires valid RSA-PSS signature on commands
  - Rejects unsigned commands
  - Rejects invalid signatures
  - Rejects commands with high phishing risk (source_context score ≥ 0.7)

### How to Run (Verify)

```powershell
cd cryptoguard-r\backend
..\venv\Scripts\python.exe -c "
import base64
from pathlib import Path
from app.crypto import get_or_create_rsa_keys, sign_string
from app.robot.command_gateway import submit_command

priv, _ = get_or_create_rsa_keys(Path('keys/rsa_private.pem'), Path('keys/rsa_public.pem'))
cmd = 'MOVE_FORWARD 5'
sig = base64.b64encode(sign_string(cmd, priv)).decode()
r = submit_command(cmd, signature_b64=sig)
print(r)
"
```

### Expected Output

```json
{"success": true, "message": "Executed MOVE_FORWARD", "command": "MOVE_FORWARD", "arg": 5.0, "state": {"x": 5.0, "y": 0.0, "heading_deg": 0.0, "is_moving": false}}
```

### Security Reasoning

- Whitelist: only known safe commands executed
- Signature: ensures commands originate from trusted key holder
- Phishing check: blocks commands from phishing-like sources (AI-powered attack vector)

---

## STEP 6: API Layer

### Implemented

- **`backend/app/api/routes_phishing.py`**: POST /api/phishing/check
  - Request: `{ "message": "..." }`
  - Response: `{ "score", "is_phishing", "message" }`

- **`backend/app/api/routes_crypto.py`**: POST /api/crypto/sign, POST /api/crypto/verify
  - Sign: `{ "message": "..." }` → `{ "message", "signature_b64" }`
  - Verify: `{ "message", "signature_b64" }` → `{ "valid", "message" }`

- **`backend/app/api/routes_robot.py`**: GET /api/robot/state, POST /api/robot/command
  - State: `{ "state", "allowed_commands" }`
  - Command: `{ "command", "signature_b64", "source_context?" }`

### How to Run

```powershell
cd cryptoguard-r\backend
..\venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Visit http://localhost:8000/docs for Swagger UI.

---

## STEP 7: Frontend Dashboard

### Implemented

- **`frontend/index.html`**: Phishing check + Robot command sections
- **`frontend/style.css`**: Dark theme, clean layout
- **`frontend/app.js`**: Vanilla JS, no frameworks

### Features

- Input message/email → Show phishing score
- Send signed command → Display robot response
- API status indicator
- Served at `/ui/` when backend runs

### How to Run

1. Start backend: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
2. Visit http://localhost:8000/ui/

---

## STEP 8: Testing

### Implemented

- **`backend/tests/test_phishing.py`**: AI detection, dataset load
- **`backend/tests/test_crypto.py`**: Sign/verify, AES, SHA-256
- **`backend/tests/test_robot.py`**: Command rejection (unsigned, invalid sig, unknown), signed acceptance

### How to Run

```powershell
cd cryptoguard-r\backend
..\venv\Scripts\python.exe -m pytest tests/ -v
```

### Expected Output

```
tests/test_crypto.py::test_sign_verify PASSED
tests/test_crypto.py::test_invalid_signature PASSED
tests/test_crypto.py::test_aes_encrypt_decrypt PASSED
tests/test_crypto.py::test_sha256_hash PASSED
tests/test_phishing.py::test_phishing_score_spam PASSED
tests/test_phishing.py::test_phishing_score_legit PASSED
tests/test_phishing.py::test_load_dataset PASSED
tests/test_robot.py::test_command_rejected_unsigned PASSED
tests/test_robot.py::test_command_rejected_invalid_signature PASSED
tests/test_robot.py::test_command_accepted_signed PASSED
tests/test_robot.py::test_unknown_command_rejected PASSED
11 passed
```

---

## STEP 9: Security Hardening

### Implemented

- **Rate limiting**: 100 requests/60s per IP (configurable via .env)
- **Input validation**: Pydantic models with length limits, sanitization
- **Replay prevention**: Duplicate (command, signature) within 5 min rejected
- **Secure defaults**: No hardcoded secrets; env-based config

### Files

- `backend/app/core/security.py`: Rate limit, replay check, sanitize
- `backend/app/core/rate_limit.py`: Rate limit middleware
- `backend/app/robot/command_gateway.py`: Replay check before execution

---

## User Verification & External Needs

### Per-step verification

| Step | What to verify | External help needed? |
|------|----------------|------------------------|
| **1** | `uvicorn` runs, `/` returns JSON | None |
| **2** | Logs in `logs/cryptoguard-r.log` | None |
| **3** | Sign/verify, AES run in README | None |
| **4** | Train model, `get_phishing_score` returns 0–1 | Dataset: `spam.csv` or `phishing_emails.csv` |
| **5** | Signed command executes; unsigned rejected | None |
| **6** | Swagger at `/docs`, API calls succeed | None |
| **7** | Dashboard at `/ui/`, phishing check and robot work | None |
| **8** | `pytest tests/` — 12 passed | None |
| **9** | Replay test passes; rate limit returns 429 after threshold | None |
| **10** | README complete | None |

### External resources

- **Datasets**: `spam.csv` (UCI SMS) or `phishing_emails.csv` for STEP 4. See dataset section above.
- **API keys**: None required.
- **Hardware**: None; robot is simulated.
- **Third-party services**: None.
