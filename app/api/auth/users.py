# app/api/auth/users.py
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from hashlib import sha256
from typing import Optional

from flask import Blueprint, request, jsonify, make_response

from app.db.session import get_session
from app.db.models import User, Session as UserSession
from app.security.auth import (
    hash_password,
    verify_password,
    make_access_token,
    make_refresh_token,
    decode_token,
)
from app.api.utils import _cfg
import logging


logger = logging.getLogger(__name__)

bp = Blueprint("users", __name__)


# ------------ Helpers ------------


def _set_auth_cookies(resp, access_token: str, refresh_token: str):
    """
    Attach JWTs as HttpOnly cookies.
    """
    cookie_args = dict(
        httponly=True,
        secure=_cfg("COOKIE_SECURE"),
        samesite=_cfg("COOKIE_SAMESITE"),
        domain=_cfg("COOKIE_DOMAIN"),
    )
    resp.set_cookie("access_token", access_token, **cookie_args)
    resp.set_cookie("refresh_token", refresh_token, **cookie_args)
    return resp


def _clear_auth_cookies(resp):
    resp.delete_cookie(
        "access_token",
        domain=_cfg("COOKIE_DOMAIN"),
        secure=_cfg("COOKIE_SECURE"),
        samesite=_cfg("COOKIE_SAMESITE"),
    )
    resp.delete_cookie(
        "refresh_token",
        domain=_cfg("COOKIE_DOMAIN"),
        secure=_cfg("COOKIE_SECURE"),
        samesite=_cfg("COOKIE_SAMESITE"),
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


def _hash_refresh_token(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()


def _session_ttl() -> timedelta:
    """
    TTL for refresh sessions, in days.
    Controlled via config: SESSION_TTL_DAYS (default 30).
    """
    try:
        days = int(_cfg("SESSION_TTL_DAYS"))
    except Exception:
        days = 30
    return timedelta(days=days)


# ------------ Endpoints ------------


@bp.route("/signup", methods=["POST"], strict_slashes=False)
def signup():
    """
    Body: { "email": "...", "password": "...", "username": "..." }
    Returns 201 + sets HttpOnly cookies (access/refresh) + creates Session row.
    """
    data = request.get_json(force=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    username = (data.get("username") or "").strip() or None

    if not email or not password or not username:
        return jsonify({"error": "email, password, and username are required"}), 400

    now = datetime.now(timezone.utc)

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
        db.flush()  # get user.user_id

        user.last_login_at = now  # type: ignore

        access = make_access_token(user.user_id)  # type: ignore
        refresh = make_refresh_token(user.user_id)  # type: ignore

        # Create session row bound to this refresh token
        sess = UserSession(
            user_id=user.user_id,  # type: ignore
            refresh_token_hash=_hash_refresh_token(refresh),
            created_at=now,
            last_seen_at=now,
            expires_at=now + _session_ttl(),
            is_revoked=False,
        )
        db.add(sess)

        resp = make_response(
            jsonify(
                {
                    "id": user.user_id,
                    "ok": True,
                    "email": user.email,
                    "username": user.username,
                }
            )
        )
        return _set_auth_cookies(resp, access, refresh), 201


@bp.route("/login", methods=["POST"], strict_slashes=False)
def login():
    """
    Body: { "email": "...", "password": "..." }
    Returns 200 + sets HttpOnly cookies (access/refresh) + creates Session row.
    """
    data = request.get_json(force=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    logger.info(f"Login attempt for email: {email}")

    if not email or not password:
        logger.warning("Login failed: missing email or password")
        return jsonify({"ok": False, "error": "email and password are required"}), 400

    now = datetime.now(timezone.utc)

    with get_session() as db:
        user = db.query(User).filter_by(email=email).first()
        if not user or not verify_password(password, user.password_hash):  # type: ignore
            logger.warning(f"Login failed: invalid credentials for {email}")
            return jsonify({"ok": False, "error": "invalid credentials"}), 401

        user.last_login_at = now  # type: ignore

        access = make_access_token(user.user_id)  # type: ignore
        refresh = make_refresh_token(user.user_id)  # type: ignore

        # New session for this device/browser
        sess = UserSession(
            user_id=user.user_id,  # type: ignore
            refresh_token_hash=_hash_refresh_token(refresh),
            created_at=now,
            last_seen_at=now,
            expires_at=now + _session_ttl(),
            is_revoked=False,
        )
        db.add(sess)

        logger.info(f"Login successful for user {user.user_id} ({email})")

        resp = make_response(
            jsonify(
                {
                    "ok": True,
                    "id": user.user_id,
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
    Only works if there is a non-revoked Session row matching this token.
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

    token_hash = _hash_refresh_token(rtoken)
    now = datetime.now(timezone.utc)

    with get_session() as db:
        sess = (
            db.query(UserSession)
            .filter(
                UserSession.user_id == user_id,
                UserSession.refresh_token_hash == token_hash,
                UserSession.is_revoked.is_(False),
                UserSession.expires_at > now,
            )
            .first()
        )
        if not sess:
            return jsonify({"error": "session not found or revoked"}), 401

        sess.last_seen_at = now  # type: ignore

    access = make_access_token(user_id)
    resp = make_response(jsonify({"access_refreshed": True, "ok": True}))
    # Keep the same refresh cookie; if you want rotation, you can mint a new refresh + update hash here.
    return _set_auth_cookies(resp, access, rtoken)


@bp.route("/me", methods=["GET"], strict_slashes=False)
def me():
    """
    Returns the current user's profile (via access token).
    """
    logger.info("GET /me endpoint called")

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
            logger.warning(f"Token valid but user {uid} not found in database")
            resp = make_response(jsonify({"authenticated": False}))
            return _clear_auth_cookies(resp)

        logger.info(f"User {uid} authenticated successfully")
        return jsonify(
            {
                "authenticated": True,
                "ok": True,
                "id": u.user_id,
                "email": u.email,
                "username": u.username,
                "last_login_at": (
                    u.last_login_at.isoformat() if u.last_login_at else None  # type: ignore
                ),
            }
        )


@bp.route("/logout", methods=["POST"], strict_slashes=False)
def logout():
    """
    Clears auth cookies and revokes the matching Session row (if any).
    """
    rtoken = request.cookies.get("refresh_token")
    if rtoken:
        payload = decode_token(rtoken)
        if payload and payload.get("typ") == "refresh":
            try:
                user_id = int(payload["sub"])
            except Exception:
                user_id = None

            if user_id is not None:
                token_hash = _hash_refresh_token(rtoken)
                now = datetime.now(timezone.utc)
                with get_session() as db:
                    sess = (
                        db.query(UserSession)
                        .filter(
                            UserSession.user_id == user_id,
                            UserSession.refresh_token_hash == token_hash,
                            UserSession.is_revoked.is_(False),
                        )
                        .first()
                    )
                    if sess:
                        sess.is_revoked = True  # type: ignore
                        sess.expires_at = now  # type: ignore

    resp = make_response(jsonify({"ok": True}))
    return _clear_auth_cookies(resp)
