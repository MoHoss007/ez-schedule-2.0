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

bp = Blueprint("users", __name__, url_prefix="/api/users")


# ------------ Cookie helpers ------------


def _set_auth_cookies(resp, access_token: str, refresh_token: str):
    """
    Attach JWTs as HttpOnly cookies. In production:
      - set COOKIE_SECURE=true (HTTPS only)
      - consider SameSite='Lax' (default below) or 'None' if cross-site is needed
    """
    cookie_args = dict(
        httponly=True,
        secure=Config.COOKIE_SECURE,
        samesite="Lax",
        domain=Config.COOKIE_DOMAIN,  # None for localhost
    )
    # Access cookie (short TTL; refreshed by /refresh)
    resp.set_cookie("access_token", access_token, **cookie_args)
    # Refresh cookie (longer TTL)
    resp.set_cookie("refresh_token", refresh_token, **cookie_args)
    return resp


def _clear_auth_cookies(resp):
    resp.delete_cookie("access_token", domain=Config.COOKIE_DOMAIN)
    resp.delete_cookie("refresh_token", domain=Config.COOKIE_DOMAIN)
    return resp


def _current_user_id_from_request() -> Optional[int]:
    """
    Reads the access token from Authorization: Bearer ... or HttpOnly cookie.
    Returns user_id (int) or None.
    """
    auth = request.headers.get("Authorization", "")
    token = auth[7:] if auth.startswith("Bearer ") else None
    if not token:
        token = request.cookies.get("access_token")
    if not token:
        return None
    payload = decode_token(token)
    if not payload or payload.get("typ") != "access":
        return None
    try:
        return int(payload["sub"])
    except Exception:
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
            jsonify({"id": user.id, "email": user.email, "username": user.username})
        )
        return _set_auth_cookies(resp, access, refresh), 201


@bp.post("/login")
def login():
    """
    Body: { "email": "...", "password": "..." }
    Returns 200 + sets HttpOnly cookies (access/refresh).
    """
    data = request.get_json(force=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400

    with get_session() as db:
        user = db.query(User).filter_by(email=email).first()
        if not user or not verify_password(password, user.password_hash):  # type: ignore
            return jsonify({"error": "invalid credentials"}), 401

        user.last_login_at = datetime.now(timezone.utc)  # type: ignore

        access = make_access_token(user.id)  # type: ignore
        refresh = make_refresh_token(user.id)  # type: ignore

        resp = make_response(
            jsonify({"id": user.id, "email": user.email, "username": user.username})
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
    resp = make_response(jsonify({"access_refreshed": True}))
    # Keep the same refresh cookie; only rotate if you want sliding sessions
    return _set_auth_cookies(resp, access, rtoken)


@bp.get("/me")
def me():
    """
    Returns the current user's profile (via access token).
    """
    uid = _current_user_id_from_request()
    if not uid:
        return jsonify({"authenticated": False}), 200

    with get_session() as db:
        u = db.get(User, uid)
        if not u:
            # token valid but user deleted
            resp = make_response(jsonify({"authenticated": False}))
            return _clear_auth_cookies(resp)

        return jsonify(
            {
                "authenticated": True,
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
