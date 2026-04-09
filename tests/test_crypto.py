"""Tests for cryptography layer."""

import base64
import pytest
from pathlib import Path

sys_path = Path(__file__).resolve().parent.parent
import sys
if str(sys_path) not in sys.path:
    sys.path.insert(0, str(sys_path))


def test_sign_verify():
    """Signed data should verify correctly."""
    from app.crypto import get_or_create_rsa_keys, sign_string, verify_string_signature
    priv_path = sys_path / "keys" / "rsa_private.pem"
    pub_path = sys_path / "keys" / "rsa_public.pem"
    priv, pub = get_or_create_rsa_keys(priv_path, pub_path)
    msg = "MOVE_FORWARD 10"
    sig = sign_string(msg, priv)
    assert verify_string_signature(msg, sig, pub)


def test_invalid_signature():
    """Invalid signature should fail verification."""
    from app.crypto import get_or_create_rsa_keys, verify_string_signature
    priv_path = sys_path / "keys" / "rsa_private.pem"
    pub_path = sys_path / "keys" / "rsa_public.pem"
    _, pub = get_or_create_rsa_keys(priv_path, pub_path)
    assert not verify_string_signature("MOVE 5", b"invalid", pub)


def test_aes_encrypt_decrypt():
    """AES encrypt/decrypt roundtrip."""
    from app.crypto import aes_encrypt_with_password, aes_decrypt_with_password
    plain = b"secret"
    enc = aes_encrypt_with_password(plain, "password")
    dec = aes_decrypt_with_password(enc, "password")
    assert dec == plain


def test_sha256_hash():
    """SHA-256 hash length."""
    from app.crypto import sha256_hash
    h = sha256_hash(b"test")
    assert len(h) == 32
