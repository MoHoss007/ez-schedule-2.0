# app/security/auth.py
from __future__ import annotations

import time
from typing import Optional

import bcrypt
import jwt  # PyJWT

from app.config import Config


# ---------------- Password Hashing ---------------- #


def hash_password(plain: str) -> str:
    """
    Hash a plaintext password with bcrypt.
    Returns a UTF-8 string you can store in the DB.
    """
    if not isinstance(plain, str) or not plain:
        raise ValueError("Password must be a non-empty string")
    hashed = bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt(rounds=12))
    return hashed.decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """
    Verify a plaintext password against a bcrypt hash.
    Safe to call with bad inputs; returns False on failure.
    """
    try:
        if not plain or not hashed:
            return False
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


# ---------------- JWT Helpers ---------------- #


def _now() -> int:
    return int(time.time())


def make_access_token(user_id: int) -> str:
    """
    Create a short-lived access token.
    Claims:
      - sub: user id (string)
      - typ: "access"
      - iat/exp: issued-at / expiry
    """
    now = _now()
    payload = {
        "sub": str(user_id),
        "typ": "access",
        "iat": now,
        "exp": now + Config.JWT_ACCESS_TTL_MIN * 60,
    }
    return jwt.encode(payload, Config.JWT_SECRET, algorithm="HS256")


def make_refresh_token(user_id: int) -> str:
    """
    Create a longer-lived refresh token.
    Claims:
      - sub: user id (string)
      - typ: "refresh"
      - iat/exp
    """
    now = _now()
    payload = {
        "sub": str(user_id),
        "typ": "refresh",
        "iat": now,
        "exp": now + Config.JWT_REFRESH_TTL_DAYS * 86400,
    }
    return jwt.encode(payload, Config.JWT_SECRET, algorithm="HS256")


def decode_token(token: str) -> Optional[dict]:
    """
    Decode & verify a JWT. Returns the payload dict or None on failure.
    Uses HS256 and your Config.JWT_SECRET.
    """
    try:
        return jwt.decode(token, Config.JWT_SECRET, algorithms=["HS256"])
    except Exception:
        return None
