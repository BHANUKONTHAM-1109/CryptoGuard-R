"""
CryptoGuard-R - Security Utilities
Rate limiting, input sanitization, replay prevention.
"""

import hashlib
import time
from collections import defaultdict
from typing import Dict, Tuple

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("security")

# In-memory rate limit: client -> (count, window_start)
_rate_store: Dict[str, Tuple[int, float]] = defaultdict(lambda: (0, 0.0))

# Replay prevention: hash(command + nonce) -> expiry
_replay_store: Dict[str, float] = {}
_REPLAY_TTL = 300  # 5 minutes


def check_rate_limit(client_id: str) -> Tuple[bool, str]:
    """
    Basic rate limiting per client.
    Returns (allowed, message).
    """
    now = time.time()
    count, window_start = _rate_store.get(client_id, (0, 0.0))
    if now - window_start >= settings.rate_limit_window:
        count, window_start = 0, now
    if count >= settings.rate_limit_requests:
        return False, "Rate limit exceeded"
    _rate_store[client_id] = (count + 1, window_start)
    return True, ""


def _purge_expired_replay() -> None:
    """Remove expired entries from replay store."""
    now = time.time()
    expired = [k for k, v in _replay_store.items() if v < now]
    for k in expired:
        del _replay_store[k]


def check_replay(command: str, signature_b64: str) -> bool:
    """
    Replay attack prevention: reject duplicate (command, signature) within TTL.
    Same signed command replayed = same hash. Returns True if replay (reject).
    """
    _purge_expired_replay()
    key = hashlib.sha256(f"{command}:{signature_b64}".encode()).hexdigest()
    if key in _replay_store:
        logger.warning("Replay attack detected: duplicate command+signature")
        return True
    _replay_store[key] = time.time() + _REPLAY_TTL
    return False


def sanitize_string(s: str, max_len: int = 10000) -> str:
    """Sanitize input: strip, truncate, remove null bytes."""
    if not isinstance(s, str):
        return ""
    s = s.replace("\x00", "").strip()
    return s[:max_len] if len(s) > max_len else s
