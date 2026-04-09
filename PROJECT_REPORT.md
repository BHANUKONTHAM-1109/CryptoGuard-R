# CryptoGuard-R: Complete Project Structure & Technical Report

## 1. Project Overview & Motivation
**CryptoGuard-R** is a unified AI & Cryptography defense framework designed to protect robotic swarms (UAVs and Ground Rovers) from advanced phishing attacks, unauthorized kinetic commands, and social engineering. 

In modern industrial setups, hardware is often controlled by human operators via dashboards. If an operator is tricked by a phishing email into sending a robotic command (e.g., instructing a forklift to drive off a ledge), standard cryptography (like simple encryption) is useless because the command *authentically* came from an authorized user. CryptoGuard-R intercepts these threats by deploying a **Natural Language Processing (NLP) AI Model** to analyze the semantic context behind a command, and pairs it strictly with **Zero-Trust Facial Biometrics** and **RSA-PSS Cryptography**.

---

## 2. Directory Structure & File Breakdown

The project operates universally on a Python FastAPI backend and a Vanilla Javascript frontend.

```text
cryptoguard-r/
├── frontend/
│   ├── index.html       # The Core User Interface (Landing Page, Master Admin Dashboard, Operator Dashboard)
│   ├── style.css        # The styling engine utilizing Glassmorphism and specialized CSS animations
│   └── app.js           # The frontend controller (Webcam integration, REST API fetches, 3D Plotly charts)
├── backend/
│   ├── requirements.txt # Python dependencies (OpenCV, scikit-learn, fastapi, pyjwt, cryptography)
│   ├── app/
│   │   ├── main.py      # The FastAPI application entrypoint. Initializes routes and the web server.
│   │   ├── core/
│   │   │   ├── config.py    # Environment variables bridging (Loading URLs, secret keys)
│   │   │   ├── auth.py      # JSON Web Token (JWT) generation and dependency verification logic
│   │   │   ├── logging.py   # System activity and error logging configurations
│   │   │   └── security.py  # Cache/Memory logic for preventing Cryptographic Replay Attacks
│   │   ├── crypto/
│   │   │   ├── key_manager.py # Generates and manages the RSA-2048 Private/Public key pairs
│   │   │   └── signature.py   # Executes the RSA-PSS mathematical hashing and padding logic
│   │   ├── ai/
│   │   │   ├── face_auth.py       # OpenCV (LBPH) facial mesh extraction, training, and liveness analysis (Anti-spoofing)
│   │   │   ├── phishing_model.py  # TF-IDF & Logistic Regression model trained on spam.csv to detect linguistic threats
│   │   │   └── semantic_safety.py # Hardcoded "Asimov" kinetic threat logic (Blocks words like "attack", "kill")
│   │   ├── robot/
│   │   │   ├── simulator.py       # The physics engine managing Geofencing, X/Y/Z mapping bounds, and Rover/UAV modes
│   │   │   └── command_gateway.py # The master gatekeeper. Intercepts commands, verifies RSA signatures, and checks ML risk scores
│   │   ├── api/
│   │   │   ├── routes_auth.py   # Endpoints for ID validation and Biometric JWT handshakes
│   │   │   ├── routes_crypto.py # Endpoints for frontend clients to request an RSA signature for their payload
│   │   │   ├── routes_phishing.py # Endpoints to manually score external text blocks for Social Engineering risks
│   │   │   └── routes_robot.py  # Endpoints exposing the hardware simulator, command transmission, and Admin isolation logic
│   │   └── database/
│   │       └── store.py # In-memory database storing biometric hashes, Operator profiles, and the Global Cryptographic Ledger
├── models/
│   └── (Generated via code) Stores the trained classifiers (e.g. face_recognizer.yml, phishing_model.pkl)
├── keys/
│   └── (Generated via code) Stores the RSA private/public `.pem` cryptographic keys
├── spam.csv             # The raw dataset of labeled threat/spam emails utilized to train the anti-phishing AI model
├── SYNOPSIS.md          # Theoretical documentation of the project
└── RUN_INSTRUCTIONS.md  # Terminal execution instructions
```

---

## 3. Substantial Features & Dashboard Workflows

The system has two primary interface modes built into `frontend/index.html`:

### A. The Operator Dashboard (Uplink Matrix)
This is what the hardware technician sees when operating the robot.
- **Biometric 2FA Module (`app.js` -> `routes_auth.py`)**: The operator must enter an ID (`CG-001`), followed by a live Webcam face scan. `face_auth.py` evaluates the `cv2.Laplacian` variance to ensure it's a real 3D human face, not a printed photograph.
- **The Simulator (`simulator.py`)**: The UI renders a live 3D Plotly Map displaying the Robot's trajectory. Operators can switch between **Rover Mode** (bound to a 50x50m grid) and **UAV Mode** (incorporating Z-axis Altitude with an FAA limit of 200m).
- **Asimov Safety & Phishing Rejection (`command_gateway.py`)**: When an operator executes a command based on an email they received (the Origin Context), the ML model scores the text. If the email is deemed a manipulative Phishing Attack, the dashboard visually aborts the command, overriding the human operator to protect the enterprise.

### B. The Cryptographic Admin Master Control
A high-level secure portal accessed via `Admin Gateway`.
- **Global Ledger (`store.py`)**: Displays every single transaction executed on the network, its mathematical RSA Hash block, the operator who sent it, and its exact AI Threat score.
- **Network Isolation Protocol (`semantic_safety.py`)**: If the AI detects a severe safety threshold violation, the system enters an automatic lockdown. Operators are fully locked out of their controls until the Administrator clicks the **Reset Network Isolation** button.
- **Operator Revocation**: Administrators can track active biometric profiles and instantly completely revoke an operator's access with a single button, terminating their physical interaction rights.

## 4. Why This Configuration?

This architecture was designed to prove that **Mathematical Encryption** is not impenetrable if the **Human using it** is compromised. 
By combining traditional backend components (`FastAPI`, `RSA-2048`) with AI sub-routines running as middleware constraints (`Scikit-Learn`, `OpenCV`), CryptoGuard-R perfectly illustrates a multi-layered defense-in-depth security approach for critical industrial networks.
