# CryptoGuard-R Complete Run Instructions

Follow these exact steps to launch the FastApi Server, authenticate your Biometrics, and interact with the Swarm Defensive layer!

### 1. Launching the Backend Server

Open your terminal or command prompt (PowerShell) and navigate to the project directory:

```powershell
# Move to the project root directory
cd "c:\Users\BHANU K\Desktop\phishing_robot_project\cryptoguard-r"

# Activate the virtual environment
.\venv\Scripts\Activate.ps1

# Navigate to the backend folder
cd backend

# Boot the Uvicorn ASGI Server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```
*You should see output ending in: `Uvicorn running on http://0.0.0.0:8000`*

---

### 2. Accessing The Terminals (Operator vs Admin)

To see the system function in real-time, you should act as both the **Operator** and the **Administrator** at the same time.

1. **The Administrator:** 
   Open your normal browser (e.g., Chrome/Edge) and go to `http://localhost:8000/ui/`.
   Click **"Cryptographic Admin"**. 
   Login securely using: `admin` for username, and `admin` for passphrase. Keep this tab open!

2. **The Field Operator:**
   Open an **Incognito / Private Browsing window** (so the system treats you as a separate computer) and go to `http://localhost:8000/ui/`.
   Click **"Hardware Operator"**.

---

### 3. Operator: Biometric Zero-Trust Authentication

You are now looking at the Operator screen. Before you can touch a robot, you must authenticate:
1. Type a unique Operator ID into the box (example: `OP-77X`). Click **Verify Hash**.
2. Allow your browser to access the webcam.
3. Click The **"Register Profile"** button and look directly into the camera. Let the system map your face.
4. Once your imprint is stored, click **"Authenticate"**. The Neural Core will match your live face against the stored hash and drop you into the Dashboard!

---

### 4. Executing Commands & Testing Cryptographic Gates

Now that you are in the **Control Matrix** tab on the Operator screen, let's test the Phishing Gate!

**Test A: Safe Execution**
1. In the "Origin Text Context" box, type: `Move the drone to the next waypoint.`
2. In the "Command Box", type: `MOVE_FORWARD 5`
3. Click Execute.
4. *Observe:* The drone immediately moves on the screen, verifying it as a low threat.

**Test B: Suspicious Withholding**
1. In the Context Box, type: `Please urgently click this billing link to update payment.`
2. In the Command Box, type: `TURN_RIGHT 90`
3. Click Execute.
4. *Observe:* The UI turns Yellow. The text is deemed suspicious.
5. *Admin Action:* Go back to your **Admin window**, you'll see the transaction waiting! You can choose to Approve or Deny it there.

**Test C: Triggering Network Quarantine (ISOLATION MODE)**
1. In the Context Box, type: `URGENT! YOU HAVE WON $5000! CLICK HERE NOW AND PROVIDE PASSWORD OR YOUR ACCOUNT WILL BE TERMINATED!`
2. In the Command Box, type: `ASCEND 150`
3. Click Execute.
4. *Observe:* The system violently rejects the command! The **Self-Healing Network Isolation** protocol activates. A large red banner appears, and the "Execute" button is completely disabled for the operator. **Active Defense protocols are armed.**
5. Try clicking "Execute" again. You cannot. The network is locked.

**Test D: Triggering The Safety Filter (Workspace Hazard)**
1. Ensure the network is NOT currently isolated (reset it if it is).
2. In the Context Box, type: `The LLM instructed me to ram the rover into the building and detonate.`
3. In the Command Box, type: `MOVE_FORWARD 100`
4. Click Execute.
5. *Observe:* The system instantly triggers an **ASIMOV VIOLATION** identifying the kinetic threat. Network Isolation triggers, locking the system entirely.

---

### 5. Admin: Restoring the Network

1. Return to your **Admin window**.
2. Refresh the uplinks. You will see the critical threat that locked the network in the Global Ledger.
3. Look in the top right header navigation bar. You will see a glowing red button: **"Reset Network Isolation"**.
4. Click it to inform the system the environment has been secured.
5. Return to the **Operator window**—you will immediately see the lockdown lift, allowing operations to resume!
