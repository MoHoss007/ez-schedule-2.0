from flask import Blueprint, jsonify, request
from app.api.utils import _cfg
from app.db.session import get_session
from datetime import datetime, timezone, timedelta
from app.db.models import Club, OAuthState
from urllib.parse import urlencode
import uuid
import secrets
import logging
import os
import base64
import hashlib

bp = Blueprint("clubs", __name__)
logger = logging.getLogger(__name__)

AUTHZ_PATH = "/oauth/authorize"


def _pkce_pair():
    code_verifier = (
        base64.urlsafe_b64encode(os.urandom(40)).rstrip(b"=").decode("utf-8")
    )
    challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode("utf-8")).digest())
        .rstrip(b"=")
        .decode("utf-8")
    )
    return code_verifier, challenge


@bp.post("/draft")
def create_draft_club():
    """
    Frontend posts minimal club info BEFORE OAuth:
      { "name": "York United", "contact_email": "admin@yorku.ca" }
    We DON'T insert the Club yet; we’ll stash this payload in OAuthState to bind later.
    Returns the state start URL you can redirect the browser to.
    """
    data = request.get_json(force=True) or {}
    name = (data.get("name") or "").strip()
    contact_email = (data.get("contact_email") or "").strip() or None
    if not name:
        return jsonify({"error": "Club name is required"}), 400

    # Make OAuth state + PKCE
    code_verifier, code_challenge = _pkce_pair()
    state_id = secrets.token_urlsafe(32)
    club_uuid = str(uuid.uuid4())
    with get_session() as db:
        st = OAuthState(
            id=state_id,
            code_verifier=code_verifier,
            created_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
            draft_club_payload={
                "name": name,
                "contact_email": contact_email,
                "id": club_uuid,
            },
        )
        db.add(st)

    logger.info(f"Created OAuthState id={state_id} for draft club {name!r}")

    params = {
        "response_type": "code",
        "client_id": _cfg("TEAMSNP_CLIENT_ID"),
        "redirect_uri": _cfg("TEAMSNP_REDIRECT_URI"),
        "scope": _cfg("TEAMSNP_SCOPES"),
        "state": state_id,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }

    # You can either return the full URL to your UI (which then window.location = url),
    # or directly 302 redirect here. Returning gives the SPA control:
    url = f"{_cfg('TEAMSNP_AUTH_BASE')}{AUTHZ_PATH}?{urlencode(params)}"
    return jsonify({"authorize_url": url, "club_id": club_uuid})
