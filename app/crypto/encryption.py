"""
CryptoGuard-R - Encryption and Hashing
AES-256 encryption, SHA-256/SHA-3 for integrity and validation.
"""

import os
from base64 import b64decode, b64encode
from typing import Tuple

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

# SECURITY: AES-256 - NIST standard, 256-bit key, no known practical attacks.
# GCM mode provides authenticated encryption (confidentiality + integrity).
AES_KEY_SIZE = 32  # 256 bits
IV_SIZE = 12  # 96 bits for GCM (NIST recommendation)
SALT_SIZE = 16
PBKDF2_ITERATIONS = 100000  # OWASP recommended minimum
TAG_SIZE = 16  # GCM auth tag


def sha256_hash(data: bytes) -> bytes:
    """
    SHA-256 hash.
    Choice: Widely supported, NIST approved, 256-bit output.
    """
    digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
    digest.update(data)
    return digest.finalize()


def sha3_256_hash(data: bytes) -> bytes:
    """
    SHA-3-256 hash (Keccak).
    Choice: Different construction than SHA-2; alternative if SHA-2 ever weakened.
    """
    digest = hashes.Hash(hashes.SHA3_256(), backend=default_backend())
    digest.update(data)
    return digest.finalize()


def verify_hash(data: bytes, expected_hash: bytes, use_sha3: bool = False) -> bool:
    """Verify data matches expected hash. Returns True if valid."""
    computed = sha3_256_hash(data) if use_sha3 else sha256_hash(data)
    return computed == expected_hash


def _derive_key(password: bytes, salt: bytes) -> bytes:
    """Derive AES key from password using PBKDF2-HMAC-SHA256."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=AES_KEY_SIZE,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
        backend=default_backend(),
    )
    return kdf.derive(password)


def aes_encrypt(plaintext: bytes, key: bytes) -> bytes:
    """
    AES-256-GCM encryption.
    Returns base64-encoded: salt (16) + iv (12) + ciphertext + tag (16).
    Choice: GCM provides authenticated encryption; detects tampering.
    """
    if len(key) != AES_KEY_SIZE:
        raise ValueError("Key must be 32 bytes for AES-256")
    salt = os.urandom(SALT_SIZE)
    iv = os.urandom(IV_SIZE)
    cipher = Cipher(algorithms.AES(key), modes.GCM(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(plaintext) + encryptor.finalize()
    tag = encryptor.tag
    payload = salt + iv + ciphertext + tag
    return b64encode(payload)


def aes_decrypt(encoded: bytes, key: bytes) -> bytes:
    """
    AES-256-GCM decryption.
    Expects base64-encoded payload from aes_encrypt.
    """
    if len(key) != AES_KEY_SIZE:
        raise ValueError("Key must be 32 bytes for AES-256")
    payload = b64decode(encoded)
    if len(payload) < SALT_SIZE + IV_SIZE + TAG_SIZE:
        raise ValueError("Invalid encrypted payload")
    salt = payload[:SALT_SIZE]
    iv = payload[SALT_SIZE : SALT_SIZE + IV_SIZE]
    tag = payload[-TAG_SIZE:]
    ciphertext = payload[SALT_SIZE + IV_SIZE : -TAG_SIZE]
    cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=default_backend())
    decryptor = cipher.decryptor()
    return decryptor.update(ciphertext) + decryptor.finalize()


def aes_encrypt_with_password(plaintext: bytes, password: str) -> bytes:
    """Encrypt using password-derived key. Salt is embedded in output."""
    salt = os.urandom(SALT_SIZE)
    key = _derive_key(password.encode("utf-8"), salt)
    iv = os.urandom(IV_SIZE)
    cipher = Cipher(algorithms.AES(key), modes.GCM(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(plaintext) + encryptor.finalize()
    tag = encryptor.tag
    payload = salt + iv + ciphertext + tag
    return b64encode(payload)


def aes_decrypt_with_password(encoded: bytes, password: str) -> bytes:
    """Decrypt using password-derived key."""
    payload = b64decode(encoded)
    if len(payload) < SALT_SIZE + IV_SIZE + TAG_SIZE:
        raise ValueError("Invalid encrypted payload")
    salt = payload[:SALT_SIZE]
    iv = payload[SALT_SIZE : SALT_SIZE + IV_SIZE]
    tag = payload[-TAG_SIZE:]
    ciphertext = payload[SALT_SIZE + IV_SIZE : -TAG_SIZE]
    key = _derive_key(password.encode("utf-8"), salt)
    cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=default_backend())
    decryptor = cipher.decryptor()
    return decryptor.update(ciphertext) + decryptor.finalize()
