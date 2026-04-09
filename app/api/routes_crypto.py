"""
CryptoGuard-R - Crypto Verification API
"""

import base64
from pathlib import Path

from fastapi import APIRouter, HTTPException

from pydantic import BaseModel, Field

from app.core.config import settings
from app.crypto.key_manager import get_or_create_rsa_keys, load_rsa_public_key
from app.crypto.signature import sign_string, verify_string_signature

router = APIRouter(prefix="/api/crypto", tags=["crypto"])


class SignRequest(BaseModel):
    """Request to sign a message."""

    message: str = Field(..., min_length=1, max_length=10000)


class SignResponse(BaseModel):
    """Signed message response."""

    message: str
    signature_b64: str


class VerifyRequest(BaseModel):
    """Request to verify a signature."""

    message: str = Field(..., min_length=1, max_length=10000)
    signature_b64: str = Field(..., min_length=1)


class VerifyResponse(BaseModel):
    """Verification result."""

    valid: bool
    message: str


def _get_key_paths() -> tuple[Path, Path]:
    base = Path(__file__).resolve().parent.parent.parent
    priv = Path(settings.rsa_private_key_path)
    pub = Path(settings.rsa_public_key_path)
    if not priv.is_absolute():
        priv = base / priv
    if not pub.is_absolute():
        pub = base / pub
    return priv, pub


@router.post("/sign", response_model=SignResponse)
def sign_message(req: SignRequest) -> SignResponse:
    """Sign a message with the server's private key."""
    priv_path, pub_path = _get_key_paths()
    priv, _ = get_or_create_rsa_keys(priv_path, pub_path)
    sig = sign_string(req.message, priv)
    return SignResponse(message=req.message, signature_b64=base64.b64encode(sig).decode())


@router.post("/verify", response_model=VerifyResponse)
def verify_message(req: VerifyRequest) -> VerifyResponse:
    """Verify a signature against the server's public key."""
    try:
        sig_bytes = base64.b64decode(req.signature_b64)
    except Exception:
        return VerifyResponse(valid=False, message="Invalid signature encoding")
    _, pub_path = _get_key_paths()
    if not pub_path.exists():
        raise HTTPException(status_code=503, detail="Public key not found")
    pub = load_rsa_public_key(pub_path)
    valid = verify_string_signature(req.message, sig_bytes, pub)
    return VerifyResponse(valid=valid, message="Signature valid" if valid else "Signature invalid")
