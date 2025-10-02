from flask import Blueprint, redirect, request
from app.api.utils import _cfg, encrypt
from db.session import get_session
from datetime import datetime, timezone, timedelta
from app.db.models import Club, OAuthState, TeamSnapAccount
from app.clients.teamsnap_client import TeamSnapClient
import logging
import requests


bp = Blueprint("teamsnap_auth", __name__)
logger = logging.getLogger(__name__)

TOKEN_PATH = "/oauth/token"


@bp.get("/callback")
def teamsnap_callback():
    code = request.args.get("code")
    state_id = request.args.get("state")
    if not code or not state_id:
        return "Missing code or state", 400

    # Lookup state and grab code_verifier + draft payload
    with get_session() as db:
        st = db.get(OAuthState, state_id)
        if st is None:
            logger.warning(f"OAuthState not found for id={state_id}")
            return "Invalid state", 400
        if not st or st.expires_at < datetime.now(timezone.utc):  # type: ignore
            logger.warning(f"OAuthState expired for id={state_id}")
            return "Invalid or expired state", 400
        code_verifier = st.code_verifier
        draft = st.draft_club_payload or {}

    # Exchange code → tokens (PKCE)
    token_url = f"{_cfg('TEAMSNP_AUTH_BASE')}{TOKEN_PATH}"
    resp = requests.post(
        token_url,
        data={
            "grant_type": "authorization_code",
            "client_id": _cfg("TEAMSNP_CLIENT_ID"),
            "code": code,
            "redirect_uri": _cfg("TEAMSNP_REDIRECT_URI"),
            "code_verifier": code_verifier,
        },
        timeout=20,
    )
    if resp.status_code != 200:
        logger.error("Token exchange failed: %s %s", resp.status_code, resp.text)
        return f"Token exchange failed: {resp.text}", 400

    tok = resp.json()
    access_token = tok["access_token"]
    refresh_token = tok.get("refresh_token")
    expires_in = int(tok.get("expires_in", 3600))
    access_exp = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

    # (Optional) get TeamSnap user id to keep a stable mapping
    teamsnap_client = TeamSnapClient(
        bearer_token=access_token, base_url=_cfg("TEAMSNP_API_BASE")
    )
    teamsnap_user_id = teamsnap_client.get_user_id()

    # Upsert Club + TeamSnapAccount, then delete state
    with get_session() as db:
        st = db.get(OAuthState, state_id)  # re-fetch inside txn
        name = (draft.get("name") or "").strip()
        club_id = draft.get("id")
        if not name:
            logger.warning(f"Draft club name missing for state_id={state_id}")
            return "Draft club name missing", 400

        if not club_id:
            logger.warning(f"Draft club id missing for state_id={state_id}")
            return "Draft club id missing", 400

        # Upsert Club by unique name
        club = db.query(Club).filter_by(name=name).first()
        if not club:
            club = Club(id=club_id, name=name, contact_email=draft.get("contact_email"))
            db.add(club)
            db.flush()  # get club.id
        else:
            # Optionally update display fields from draft
            if draft.get("contact_email"):
                club.contact_email = str(draft["contact_email"])  # type: ignore

        # Upsert TeamSnapAccount per (club_id, teamsnap_user_id)
        tsa = (
            db.query(TeamSnapAccount)
            .filter_by(club_id=club.id, teamsnap_user_id=teamsnap_user_id)
            .first()
        )
        if not tsa:
            tsa = TeamSnapAccount(
                club_id=club.id,
                teamsnap_user_id=teamsnap_user_id,
                scope=tok.get("scope"),
                access_token_enc=encrypt(access_token),
                refresh_token_enc=encrypt(refresh_token),
                access_token_expires_at=access_exp,
            )
            db.add(tsa)
        else:
            tsa.scope = tok.get("scope")
            tsa.access_token_enc = encrypt(access_token)  # type: ignore
            if refresh_token:
                tsa.refresh_token_enc = encrypt(refresh_token)  # type: ignore
            tsa.access_token_expires_at = access_exp  # type: ignore

        # Cleanup state
        db.delete(st)
        logger.info(
            f"Created Club id={club.id} name={club.name!r} with TeamSnapAccount id={tsa.id} user_id={teamsnap_user_id}"
        )

    # Send them back to your UI
    return redirect(_cfg("POST_AUTH_REDIRECT"), code=302)
