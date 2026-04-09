"""
CryptoGuard-R - Key Management
RSA/ECC key pair generation and secure storage simulation.
"""

from pathlib import Path
from typing import Tuple

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from cryptography.hazmat.backends import default_backend

# SECURITY: RSA-2048 provides ~112-bit security; minimum recommended by NIST.
# ECC P-256 provides equivalent security with smaller keys (256-bit).
RSA_KEY_SIZE = 2048
ECC_CURVE = ec.SECP256R1  # NIST P-256


def generate_rsa_keypair() -> Tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey]:
    """
    Generate RSA key pair for digital signatures and asymmetric crypto.
    Choice: RSA-2048 - industry standard, widely supported, FIPS-approved.
    """
    private_key = rsa.generate_private_key(
        public_exponent=65537,  # Standard; avoids small-exponent attacks
        key_size=RSA_KEY_SIZE,
        backend=default_backend(),
    )
    public_key = private_key.public_key()
    return private_key, public_key


def generate_ecc_keypair() -> Tuple[ec.EllipticCurvePrivateKey, ec.EllipticCurvePublicKey]:
    """
    Generate ECC key pair (alternative to RSA).
    Choice: P-256 - same security as RSA-3072 with smaller keys; NIST approved.
    """
    private_key = ec.generate_private_key(ECC_CURVE(), default_backend())
    public_key = private_key.public_key()
    return private_key, public_key


def save_rsa_private_key(key: rsa.RSAPrivateKey, path: Path) -> None:
    """
    Serialize RSA private key to PEM file.
    SECURITY: Use encryption in production (password); simulated as unencrypted for dev.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    path.write_bytes(pem)


def save_rsa_public_key(key: rsa.RSAPublicKey, path: Path) -> None:
    """Serialize RSA public key to PEM file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    pem = key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    path.write_bytes(pem)


def load_rsa_private_key(path: Path) -> rsa.RSAPrivateKey:
    """Load RSA private key from PEM file."""
    pem = path.read_bytes()
    return serialization.load_pem_private_key(
        pem, password=None, backend=default_backend()
    )


def load_rsa_public_key(path: Path) -> rsa.RSAPublicKey:
    """Load RSA public key from PEM file."""
    pem = path.read_bytes()
    return serialization.load_pem_public_key(pem, backend=default_backend())


def get_or_create_rsa_keys(private_path: Path, public_path: Path) -> Tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey]:
    """
    Load existing RSA keys or generate and persist new ones.
    Simulates secure key storage: keys on disk, restricted permissions in production.
    """
    if private_path.exists() and public_path.exists():
        priv = load_rsa_private_key(private_path)
        pub = load_rsa_public_key(public_path)
        return priv, pub
    priv, pub = generate_rsa_keypair()
    save_rsa_private_key(priv, private_path)
    save_rsa_public_key(pub, public_path)
    return priv, pub
