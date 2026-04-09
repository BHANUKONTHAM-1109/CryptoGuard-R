"""
CryptoGuard-R - Digital Signatures
Create and verify RSA-PSS signatures for command authenticity.
"""

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.backends import default_backend

# SECURITY: SHA-256 for hash - NIST approved, no known practical collisions.
# PSS padding - probabilistic, more secure than PKCS1v15 against certain attacks.
SIGNATURE_HASH = hashes.SHA256()
PSS_SALT_LENGTH = 32  # Max for SHA-256; recommended for security


def sign_data(data: bytes, private_key: rsa.RSAPrivateKey) -> bytes:
    """
    Sign data with RSA-PSS.
    Choice: PSS over PKCS1v15 - provably secure, resistant to signature forgeries.
    """
    signature = private_key.sign(
        data,
        padding.PSS(
            mgf=padding.MGF1(SIGNATURE_HASH),
            salt_length=PSS_SALT_LENGTH,
        ),
        SIGNATURE_HASH,
    )
    return signature


def verify_signature(data: bytes, signature: bytes, public_key: rsa.RSAPublicKey) -> bool:
    """
    Verify RSA-PSS signature.
    Returns True if valid, False otherwise.
    """
    try:
        public_key.verify(
            signature,
            data,
            padding.PSS(
                mgf=padding.MGF1(SIGNATURE_HASH),
                salt_length=PSS_SALT_LENGTH,
            ),
            SIGNATURE_HASH,
        )
        return True
    except Exception:
        return False


def sign_string(message: str, private_key: rsa.RSAPrivateKey) -> bytes:
    """Sign a string (UTF-8 encoded)."""
    return sign_data(message.encode("utf-8"), private_key)


def verify_string_signature(message: str, signature: bytes, public_key: rsa.RSAPublicKey) -> bool:
    """Verify signature of a string."""
    return verify_signature(message.encode("utf-8"), signature, public_key)
