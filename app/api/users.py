# app/api/users.py
from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional

from flask import Blueprint, request, jsonify, make_response

from app.config import Config
from app.db.session import get_session
from app.db.models import User
from app.security.auth import (
    hash_password,
    verify_password,
    make_access_token,
    make_refresh_token,
    decode_token,
)
import logging

logger = logging.getLogger(__name__)

bp = Blueprint("users", __name__)


# ------------ Cookie helpers ------------


def _set_auth_cookies(resp, access_token: str, refresh_token: str):
    """
    Attach JWTs as HttpOnly cookies. For cross-origin requests:
      - set secure=True (required for SameSite=None)
      - set samesite="None" (allows cross-origin cookie sending)
      - don't set domain (for cross-origin compatibility)
    """
    cookie_args = dict(
        httponly=True,
        secure=Config.COOKIE_SECURE,  # Required for SameSite=None
        samesite=Config.COOKIE_SAMESITE,  # Allow cross-origin cookie sending
        domain=Config.COOKIE_DOMAIN,  # Don't restrict domain for cross-origin
    )
    # Access cookie (short TTL; refreshed by /refresh)
    resp.set_cookie("access_token", access_token, **cookie_args)
    # Refresh cookie (longer TTL)
    resp.set_cookie("refresh_token", refresh_token, **cookie_args)
    return resp


def _clear_auth_cookies(resp):
    resp.delete_cookie(
        "access_token",
        domain=Config.COOKIE_DOMAIN,
        secure=Config.COOKIE_SECURE,
        samesite=Config.COOKIE_SAMESITE,
    )
    resp.delete_cookie(
        "refresh_token",
        domain=Config.COOKIE_DOMAIN,
        secure=Config.COOKIE_SECURE,
        samesite=Config.COOKIE_SAMESITE,
    )
    return resp


def _current_user_id_from_request() -> Optional[int]:
    """
    Reads the access token from Authorization: Bearer ... or HttpOnly cookie.
    Returns user_id (int) or None.
    """
    auth = request.headers.get("Authorization", "")
    token = auth[7:] if auth.startswith("Bearer ") else None
    logger.info(f"Authorization header token: {'***' if token else 'None'}")

    if not token:
        token = request.cookies.get("access_token")
        logger.info(f"Cookie access_token: {'***' if token else 'None'}")

    if not token:
        logger.info("No token found in headers or cookies")
        return None

    payload = decode_token(token)
    logger.info(f"Token payload: {payload}")

    if not payload or payload.get("typ") != "access":
        logger.warning(f"Invalid token payload or wrong type: {payload}")
        return None

    try:
        user_id = int(payload["sub"])
        logger.info(f"Extracted user_id: {user_id}")
        return user_id
    except Exception as e:
        logger.error(f"Error extracting user_id from payload: {e}")
        return None


# ------------ Endpoints ------------


@bp.post("/signup")
def signup():
    """
    Body: { "email": "...", "password": "...", "username": "..." }
    Returns 201 + sets HttpOnly cookies (access/refresh).
    """
    data = request.get_json(force=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    username = (data.get("username") or "").strip() or None

    if not email or not password or not username:
        return jsonify({"error": "email, password, and username are required"}), 400

    with get_session() as db:
        existing_email = db.query(User).filter_by(email=email).first()
        if existing_email:
            return jsonify({"error": "email already registered"}), 409

        existing_username = db.query(User).filter_by(username=username).first()
        if existing_username:
            return jsonify({"error": "username already taken"}), 409

        user = User(
            email=email, username=username, password_hash=hash_password(password)
        )
        db.add(user)
        db.flush()  # get user.id

        user.last_login_at = datetime.now(timezone.utc)  # type: ignore

        access = make_access_token(user.id)  # type: ignore
        refresh = make_refresh_token(user.id)  # type: ignore

        resp = make_response(
            jsonify(
                {
                    "id": user.id,
                    "ok": True,
                    "email": user.email,
                    "username": user.username,
                }
            )
        )
        return _set_auth_cookies(resp, access, refresh), 201


@bp.post("/login")
def login():
    """
    Body: { "email": "...", "password": "..." }
    Returns 200 + sets HttpOnly cookies (access/refresh).
    """
    import logging

    logger = logging.getLogger(__name__)

    data = request.get_json(force=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    logger.info(f"Login attempt for email: {email}")

    if not email or not password:
        logger.warning("Login failed: missing email or password")
        return jsonify({"ok": False, "error": "email and password are required"}), 400

    with get_session() as db:
        user = db.query(User).filter_by(email=email).first()
        if not user or not verify_password(password, user.password_hash):  # type: ignore
            logger.warning(f"Login failed: invalid credentials for {email}")
            return jsonify({"ok": False, "error": "invalid credentials"}), 401

        user.last_login_at = datetime.now(timezone.utc)  # type: ignore

        access = make_access_token(user.id)  # type: ignore
        refresh = make_refresh_token(user.id)  # type: ignore

        logger.info(f"Login successful for user {user.id} ({email})")

        resp = make_response(
            jsonify(
                {
                    "ok": True,
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                }
            )
        )
        return _set_auth_cookies(resp, access, refresh)


@bp.post("/refresh")
def refresh():
    """
    Uses refresh_token cookie to mint a new access_token.
    Returns 200 + sets a new access token cookie (refresh remains the same).
    """
    rtoken = request.cookies.get("refresh_token")
    if not rtoken:
        return jsonify({"error": "no refresh token"}), 401

    payload = decode_token(rtoken)
    if not payload or payload.get("typ") != "refresh":
        return jsonify({"error": "invalid refresh token"}), 401

    try:
        user_id = int(payload["sub"])
    except Exception:
        return jsonify({"error": "invalid refresh token"}), 401

    access = make_access_token(user_id)
    resp = make_response(jsonify({"access_refreshed": True, "ok": True}))
    # Keep the same refresh cookie; only rotate if you want sliding sessions
    return _set_auth_cookies(resp, access, rtoken)


@bp.get("/me")
def me():
    """
    Returns the current user's profile (via access token).
    """
    import logging

    logger = logging.getLogger(__name__)

    logger.info("GET /me endpoint called")

    # Log cookies for debugging
    cookies = request.cookies
    logger.info(f"Cookies received: {dict(cookies)}")

    uid = _current_user_id_from_request()
    logger.info(f"User ID from request: {uid}")

    if not uid:
        logger.info("No valid user ID found, returning unauthenticated")
        return jsonify({"authenticated": False}), 200

    with get_session() as db:
        u = db.get(User, uid)
        if not u:
            # token valid but user deleted
            logger.warning(f"Token valid but user {uid} not found in database")
            resp = make_response(jsonify({"authenticated": False}))
            return _clear_auth_cookies(resp)

        logger.info(f"User {uid} authenticated successfully")
        return jsonify(
            {
                "authenticated": True,
                "ok": True,
                "id": u.id,
                "email": u.email,
                "username": u.username,
                "last_login_at": (
                    u.last_login_at.isoformat() if u.last_login_at else None  # type: ignore
                ),
            }
        )


@bp.post("/logout")
def logout():
    """
    Clears auth cookies.
    """
    resp = make_response(jsonify({"ok": True}))
    return _clear_auth_cookies(resp)
