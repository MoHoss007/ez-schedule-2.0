from __future__ import annotations
import logging, secrets
from urllib.parse import urlencode

from flask import Blueprint, current_app, jsonify, redirect, request, session

import requests

bp = Blueprint("teamsnap_auth", __name__)
log = logging.getLogger(__name__)

# Conventional OAuth2 paths (adjust if TeamSnap shows different in your app settings)
AUTHZ_PATH = "/oauth/authorize"
TOKEN_PATH = "/oauth/token"


def _cfg(key: str) -> str:
    return current_app.config[key]


@bp.get("/login")
def login():
    """
    Step 1: send user to TeamSnap authorize URL with a CSRF 'state'.
    """
    state = secrets.token_urlsafe(24)
    session["oauth_state"] = state

    params = {
        "response_type": "code",
        "client_id": _cfg("TEAMSNP_CLIENT_ID"),
        "redirect_uri": _cfg("TEAMSNP_REDIRECT_URI"),
        "scope": _cfg("TEAMSNP_SCOPES"),
        "state": state,
    }
    url = f"{_cfg('TEAMSNP_AUTH_BASE')}{AUTHZ_PATH}?{urlencode(params)}"
    return redirect(url, code=302)


@bp.get("/callback")
def callback():
    """
    Step 2: TeamSnap redirects here with ?code=...&state=...
    Exchange code for tokens; for now we just log and return them as JSON.
    """
    if err := request.args.get("error"):
        log.error("OAuth error from provider: %s", err)
        return jsonify({"ok": False, "error": err}), 400

    # CSRF state check
    state = request.args.get("state")
    if not state or state != session.get("oauth_state"):
        return jsonify({"ok": False, "error": "invalid_state"}), 400

    code = request.args.get("code")
    if not code:
        return jsonify({"ok": False, "error": "missing_code"}), 400

    token_url = f"{_cfg('TEAMSNP_AUTH_BASE')}{TOKEN_PATH}"
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": _cfg("TEAMSNP_REDIRECT_URI"),
        "client_id": _cfg("TEAMSNP_CLIENT_ID"),
        "client_secret": _cfg("TEAMSNP_CLIENT_SECRET"),
    }

    resp = requests.post(token_url, data=data, timeout=20)
    if not resp.ok:
        log.error("Token exchange failed: %s %s", resp.status_code, resp.text)
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "token_exchange_failed",
                    "status": resp.status_code,
                }
            ),
            502,
        )

    tokens = resp.json()
    # DEV ONLY: print to logs
    log.info("TeamSnap tokens: %s", tokens)

    # Return tokens (again, for early testing only)
    return jsonify({"ok": True, "tokens": tokens})
