"""
CryptoGuard-R - Command Gateway
Enforces cryptographic verification and phishing risk checks before robot execution.
Rejects unsigned or high-risk commands.
"""

import base64
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from app.core.config import settings
from app.core.logging import get_logger
from app.core.security import check_replay
from app.crypto.key_manager import get_or_create_rsa_keys
from app.crypto.signature import verify_string_signature

logger = get_logger("command_gateway")

# Phishing score threshold: commands with source/message above this are rejected
PHISHING_RISK_THRESHOLD = 0.7


def _get_key_paths() -> Tuple[Path, Path]:
    """Resolve RSA key paths from config."""
    base = Path(__file__).resolve().parent.parent.parent  # backend/
    priv = Path(settings.rsa_private_key_path)
    pub = Path(settings.rsa_public_key_path)
    if not priv.is_absolute():
        priv = base / priv
    if not pub.is_absolute():
        pub = base / pub
    return priv, pub


def verify_command_signature(command: str, signature_b64: str) -> bool:
    """
    Verify that command is signed with the trusted public key.
    signature_b64: Base64-encoded RSA-PSS signature.
    Returns True if valid.
    """
    try:
        sig_bytes = base64.b64decode(signature_b64)
    except Exception as e:
        logger.warning("Invalid signature encoding: %s", e)
        return False
    _, pub_path = _get_key_paths()
    if not pub_path.exists():
        logger.error("Public key not found at %s", pub_path)
        return False
    from app.crypto.key_manager import load_rsa_public_key
    pub = load_rsa_public_key(pub_path)
    return verify_string_signature(command, sig_bytes, pub)


def check_phishing_risk(text: str) -> Tuple[float, bool]:
    """
    Check phishing score for command source/message.
    Returns (score, is_high_risk).
    Commands embedded in phishing-like text may indicate compromised source.
    """
    try:
        from app.ai.phishing_model import get_model, get_phishing_score
        model = get_model()
    except Exception as e:
        logger.debug("Phishing model unavailable: %s", e)
        return 0.0, False
    if model is None:
        return 0.0, False
    score = get_phishing_score(model, text)
    return score, score >= PHISHING_RISK_THRESHOLD


def submit_command(
    command: str,
    signature_b64: Optional[str] = None,
    source_context: Optional[str] = None,
    operator_id: str = "UNKNOWN",
) -> Dict[str, Any]:
    """
    Submit command through the gateway.
    - Rejects if signature missing or invalid
    - Rejects if source_context has high phishing score (optional check)
    - Executes via simulator if all checks pass
    """
    from app.database.store import get_isolation_status, set_isolation_status, add_transaction
    
    # 0. Check Network Isolation
    if get_isolation_status():
        logger.warning(f"Command blocked by Active Defense Network Isolation. Operator: {operator_id}")
        return {
            "success": False,
            "message": "Self-Healing Network Isolation is Active. Terminal locked.",
            "code": "NETWORK_ISOLATED",
        }

    # 1. Require valid signature
    if not signature_b64:
        logger.warning("Command rejected: missing signature")
        return {
            "success": False,
            "message": "Signature required",
            "code": "MISSING_SIGNATURE",
        }
    if not verify_command_signature(command, signature_b64):
        logger.warning("Command rejected: invalid signature")
        return {
            "success": False,
            "message": "Invalid signature",
            "code": "INVALID_SIGNATURE",
        }

    # 1b. Replay attack prevention: reject duplicate (command, signature)
    if check_replay(command, signature_b64):
        return {
            "success": False,
            "message": "Replay detected: duplicate command+signature",
            "code": "REPLAY_DETECTED",
        }

    # 2. Mandatory Phishing Command Gate & Asimov Semantic Safety
    if not source_context or not source_context.strip():
        logger.warning(f"Command rejected: Mandatory source context missing. Operator: {operator_id}")
        return {
            "success": False,
            "message": "Protocol Violation: Origin instruction context must be provided for AI analysis.",
            "code": "CONTEXT_REQUIRED",
        }

    from app.ai.semantic_safety import evaluate_safety
    is_safe, safety_reason = evaluate_safety(source_context)
    if not is_safe:
        logger.critical(f"ASIMOV PROTOCOL VIOLATION: {safety_reason}")
        set_isolation_status(True)
        add_transaction(operator_id, command, "DENIED (SAFETY)", 1.0, signature_b64[:30] + "...")
        return {
            "success": False,
            "message": safety_reason,
            "code": "SAFETY_VIOLATION"
        }

    score, is_high = check_phishing_risk(source_context)
    final_score = score
    if is_high:
        logger.critical(f"CYBER THREAT DETECTED. Engaged Network Isolation (Score: {score:.2f})")
        set_isolation_status(True)
        add_transaction(operator_id, command, "DENIED (THREAT)", round(score, 4), signature_b64[:30] + "...")
        return {
            "success": False,
            "message": f"Source flagged as phishing risk (score={score:.2f})",
            "code": "PHISHING_RISK",
            "phishing_score": round(score, 4),
        }
            
    # Conditional logic based on our score
    from app.database.store import add_transaction
    
    if final_score >= 0.3 and final_score < 0.7:
        # PENDING ADMIN APPROVAL
        add_transaction(operator_id, command, "PENDING", round(final_score, 4), signature_b64[:30] + "...")
        return {
            "success": False,
            "message": "Transaction suspicious. Sent to Admin for approval.",
            "code": "PENDING_APPROVAL",
            "phishing_score": round(final_score, 4)
        }

    # 3. Execute via simulator (APPROVED)
    tx_id = add_transaction(operator_id, command, "APPROVED", round(final_score, 4), signature_b64[:30] + "...")
    from app.robot.simulator import get_simulator
    sim = get_simulator()
    result = sim.execute(command)
    result["transaction_id"] = tx_id
    return result
