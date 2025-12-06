# app/api/leagues/seasons.py
from flask import Blueprint, request, jsonify
from datetime import datetime, timezone
from app.db.session import get_session
from app.db.models import LeagueSeason
import logging

logger = logging.getLogger(__name__)

bp = Blueprint("league_seasons_routes", __name__)


def _parse_after_param():
    val = request.args.get("after")
    if not val:
        return None

    try:
        dt = datetime.fromisoformat(val)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt
    except Exception:
        return None


@bp.route("", methods=["GET"], strict_slashes=False)
def list_league_seasons():
    """
    Optional query params:
        GET /api/v1/leagues/seasons
      - league_id=<id> → filter by league
      - after=<timestamp> → return seasons starting after this date
      - only_active=true → only return seasons where change_deadline_for_current is in the future
    """
    league_id = request.args.get("league_id", type=int)
    after = _parse_after_param()
    only_active = request.args.get("only_active", type=str) == "true"

    try:
        with get_session() as session:
            q = session.query(LeagueSeason)

            if league_id:
                q = q.filter(LeagueSeason.league_id == league_id)

            if after:
                q = q.filter(LeagueSeason.season_start >= after)

            if only_active:
                now = datetime.now(timezone.utc)
                q = q.filter(LeagueSeason.change_deadline_for_current > now)

            seasons = q.order_by(LeagueSeason.season_start.asc()).all()

            results = []
            for s in seasons:
                results.append(
                    {
                        "league_season_id": s.league_season_id,
                        "league_id": s.league_id,
                        "name": s.name,
                        "season_start": s.season_start.isoformat(),
                        "season_end": s.season_end.isoformat(),
                        "subscription_open_at": s.subscription_open_at.isoformat(),
                        "subscription_close_at": s.subscription_close_at.isoformat(),
                        "change_deadline_for_current": (
                            s.change_deadline_for_current.isoformat()
                            if s.change_deadline_for_current is not None  # type: ignore
                            else None
                        ),
                        "created_at": s.created_at.isoformat() if s.created_at is not None else None,  # type: ignore
                    }
                )

    except Exception as e:
        logger.error(f"Error listing league seasons {e}", exc_info=True)
        return jsonify({"error": "internal server error"}), 500

    return jsonify(results)


@bp.route("/<int:league_season_id>", methods=["GET"], strict_slashes=False)
def get_league_season(league_season_id: int):
    """
    GET /api/v1/leagues/seasons/<league_season_id>
    """
    try:
        with get_session() as session:
            s = (
                session.query(LeagueSeason)
                .filter(LeagueSeason.league_season_id == league_season_id)
                .first()
            )

            if not s:
                return jsonify({"error": "league_season not found"}), 404

            result = {
                "league_season_id": s.league_season_id,
                "league_id": s.league_id,
                "name": s.name,
                "season_start": s.season_start.isoformat(),
                "season_end": s.season_end.isoformat(),
                "subscription_open_at": s.subscription_open_at.isoformat(),
                "subscription_close_at": s.subscription_close_at.isoformat(),
                "change_deadline_for_current": (
                    s.change_deadline_for_current.isoformat()
                    if s.change_deadline_for_current is not None  # type: ignore
                    else None
                ),
                "created_at": s.created_at.isoformat() if s.created_at is not None else None,  # type: ignore
            }

    except Exception as e:
        logger.error(
            f"Error getting league season {league_season_id}: {e}", exc_info=True
        )
        return jsonify({"error": "internal server error"}), 500

    return jsonify(result)
