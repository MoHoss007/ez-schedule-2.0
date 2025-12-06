# app/api/auth/sessions.py
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from typing import Optional

from flask import Blueprint, request, jsonify

from app.db.session import get_session
from app.db.models import Session as UserSession
from app.api.auth.users import _current_user_id_from_request
from app.security.auth import decode_token

import logging

logger = logging.getLogger(__name__)

bp = Blueprint("sessions", __name__)


# ------------ Helpers ------------


def _hash_refresh_token(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()


def _get_current_session_hash() -> Optional[str]:
    """
    If the caller has a refresh_token cookie, return its hash,
    so we can mark which session is 'current' in the listing.
    """
    rtoken = request.cookies.get("refresh_token")
    if not rtoken:
        return None
    return _hash_refresh_token(rtoken)


# ------------ Endpoints ------------


@bp.route("/sessions", methods=["GET"], strict_slashes=False)
def list_sessions():
    """
    List all active sessions for the current user.

    Response example:
    [
      {
        "id": 1,
        "created_at": "...",
        "last_seen_at": "...",
        "expires_at": "...",
        "ip_address": "1.2.3.4",
        "user_agent": "...",
        "is_revoked": false,
        "is_current": true
      },
      ...
    ]
    """
    user_id = _current_user_id_from_request()
    if not user_id:
        return jsonify({"error": "unauthorized"}), 401

    current_hash = _get_current_session_hash()
    now = datetime.now(timezone.utc)

    with get_session() as db:
        sessions = (
            db.query(UserSession)
            .filter(UserSession.user_id == user_id)
            .order_by(UserSession.created_at.desc())
            .all()
        )

        result = []
        for s in sessions:
            is_current = (
                current_hash is not None
                and s.refresh_token_hash == current_hash
                and not s.is_revoked  # type: ignore
            )

            result.append(
                {
                    "id": s.session_id,
                    "created_at": (
                        s.created_at.isoformat() if s.created_at is not None else None
                    ),
                    "last_seen_at": (
                        s.last_seen_at.isoformat()
                        if s.last_seen_at is not None
                        else None
                    ),
                    "expires_at": (
                        s.expires_at.isoformat() if s.expires_at is not None else None
                    ),
                    "ip_address": s.ip_address,
                    "user_agent": s.user_agent,
                    "is_revoked": bool(s.is_revoked),
                    "is_current": is_current,
                    "is_expired": bool(s.expires_at and s.expires_at < now),
                }
            )

    return jsonify(result)


@bp.route("/sessions/<int:session_id>", methods=["DELETE"], strict_slashes=False)
def revoke_session(session_id: int):
    """
    Revoke a specific session (log out that device).

    - Only the owner of the session can revoke it.
    - Does NOT touch cookies; this is more like "log out other device".
    """
    user_id = _current_user_id_from_request()
    if not user_id:
        return jsonify({"error": "unauthorized"}), 401

    now = datetime.now(timezone.utc)

    with get_session() as db:
        sess = (
            db.query(UserSession)
            .filter(
                UserSession.session_id == session_id,
                UserSession.user_id == user_id,
            )
            .first()
        )
        if not sess:
            return jsonify({"error": "session not found"}), 404

        sess.is_revoked = True  # type: ignore
        sess.expires_at = now  # type: ignore

    return jsonify({"ok": True, "revoked_session_id": session_id})


@bp.route("/sessions", methods=["DELETE"], strict_slashes=False)
def revoke_all_sessions():
    """
    Revoke ALL sessions for the current user.
    (Server-side logout everywhere; caller should also clear local cookies.)
    """
    user_id = _current_user_id_from_request()
    if not user_id:
        return jsonify({"error": "unauthorized"}), 401

    now = datetime.now(timezone.utc)

    with get_session() as db:
        q = db.query(UserSession).filter(UserSession.user_id == user_id)
        count = 0
        for sess in q:
            if not sess.is_revoked:  # type: ignore
                sess.is_revoked = True  # type: ignore
                sess.expires_at = now  # type: ignore
                count += 1

    return jsonify({"ok": True, "revoked_count": count})
