# app/api/leagues/seasons.py
from flask import Blueprint, request, jsonify
from datetime import datetime, timezone
from app.db.session import get_session
from app.db.models import LeagueSeason

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
    GET /api/v1/league-seasons
    Optional query params:
      - league_id=<id> → filter by league
      - after=<timestamp> → return seasons starting after this date
    """
    league_id = request.args.get("league_id", type=int)
    after = _parse_after_param()

    with get_session() as session:
        q = session.query(LeagueSeason)

        if league_id:
            q = q.filter(LeagueSeason.league_id == league_id)

        if after:
            q = q.filter(LeagueSeason.season_start >= after)

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
                        if s.change_deadline_for_current  # type: ignore
                        else None
                    ),
                    "created_at": s.created_at.isoformat() if s.created_at else None,  # type: ignore
                }
            )

    return jsonify(results)


@bp.route("/<int:league_season_id>", methods=["GET"], strict_slashes=False)
def get_league_season(league_season_id: int):
    """
    GET /api/v1/league-seasons/<league_season_id>
    """
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
                if s.change_deadline_for_current  # type: ignore
                else None
            ),
            "created_at": s.created_at.isoformat() if s.created_at else None,  # type: ignore
        }

    return jsonify(result)
