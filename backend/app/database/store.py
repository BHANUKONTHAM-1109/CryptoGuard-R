from typing import Dict, List, Any
import datetime
import uuid
import json
from pathlib import Path

# In-Memory Transaction Store
transactions: Dict[str, Dict[str, Any]] = {}
ISOLATION_ENGAGED: bool = False

# File persistence for users and admin config
DB_DIR = Path(__file__).resolve().parent
ADMIN_DB_PATH = DB_DIR / "admin.json"
OPERATORS_DB_PATH = DB_DIR / "operators.json"

def _load_json(path: Path, default: Any):
    if path.exists():
        try:
            with open(path, "r") as f:
                return json.load(f)
        except:
            pass
    return default

def _save_json(path: Path, data: Any):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)

def check_admin_credentials(username: str, password_attempt: str) -> bool:
    admin_data = _load_json(ADMIN_DB_PATH, {"username": "admin", "password": "admin"})
    return username == admin_data["username"] and password_attempt == admin_data["password"]

def change_admin_password(new_password: str):
    admin_data = _load_json(ADMIN_DB_PATH, {"username": "admin", "password": "admin"})
    admin_data["password"] = new_password
    _save_json(ADMIN_DB_PATH, admin_data)

def add_operator(operator_id: str, face_hash: str):
    ops = _load_json(OPERATORS_DB_PATH, {})
    ops[operator_id] = {
        "operator_id": operator_id,
        "registered_at": datetime.datetime.utcnow().isoformat() + "Z",
        "face_hash": face_hash
    }
    _save_json(OPERATORS_DB_PATH, ops)

def get_operators() -> List[Dict[str, Any]]:
    ops = _load_json(OPERATORS_DB_PATH, {})
    return list(ops.values())

def remove_operator(operator_id: str) -> bool:
    ops = _load_json(OPERATORS_DB_PATH, {})
    if operator_id in ops:
        del ops[operator_id]
        _save_json(OPERATORS_DB_PATH, ops)
        return True
    return False

def is_operator_valid(operator_id: str) -> bool:
    ops = _load_json(OPERATORS_DB_PATH, {})
    # For demo purposes, we always allow CG-001 so the previous default still works if file is empty
    if operator_id == "CG-001" and operator_id not in ops:
        return True
    return operator_id in ops

def set_isolation_status(status: bool):
    global ISOLATION_ENGAGED
    ISOLATION_ENGAGED = status

def get_isolation_status() -> bool:
    return ISOLATION_ENGAGED

def add_transaction(operator_id: str, command: str, status: str, phishing_score: float, crypto_hash: str) -> str:
    tx_id = str(uuid.uuid4())
    transactions[tx_id] = {
        "id": tx_id,
        "operator_id": operator_id or "UNKNOWN",
        "command": command,
        "status": status,
        "phishing_score": phishing_score,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "crypto_technique": "RSA-2048 PSS Signature",
        "crypto_hash": crypto_hash
    }
    return tx_id

def get_all_transactions() -> List[Dict[str, Any]]:
    return sorted(list(transactions.values()), key=lambda x: x["timestamp"], reverse=True)

def update_transaction_status(tx_id: str, status: str) -> bool:
    if tx_id in transactions:
        transactions[tx_id]["status"] = status
        return True
    return False

def get_transaction(tx_id: str) -> Dict[str, Any] | None:
    return transactions.get(tx_id)
