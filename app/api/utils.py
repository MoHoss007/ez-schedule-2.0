from flask import current_app
from cryptography.fernet import Fernet
import base64, hashlib, os


def _get_fernet() -> Fernet:
    # Derive a key from an env var (rotateable)
    secret = os.environ["TOKEN_ENC_SECRET"].encode("utf-8")  # 32+ chars recommended
    key = base64.urlsafe_b64encode(hashlib.sha256(secret).digest())
    return Fernet(key)


def _cfg(key: str) -> str:
    return current_app.config[key]


def encrypt(s: str) -> str:
    return _get_fernet().encrypt(s.encode("utf-8")).decode("utf-8")


def decrypt(s: str) -> str:
    return _get_fernet().decrypt(s.encode("utf-8")).decode("utf-8")
