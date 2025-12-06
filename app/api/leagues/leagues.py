from flask import Blueprint, request, jsonify
from datetime import datetime, timezone
from app.db.session import get_session
from app.db.models import League
import logging

logger = logging.getLogger(__name__)

bp = Blueprint("leagues_routes", __name__)


def _parse_after_param():
    """Parses ?after= timestamp into a Python datetime."""
    val = request.args.get("after")
    if not val:
        return None

    try:
        # Try ISO8601 first
        dt = datetime.fromisoformat(val)
        # If no timezone → treat as UTC naive
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt
    except Exception:
        return None


@bp.route("", methods=["GET"], strict_slashes=False)
def list_leagues():
    """
    GET /api/v1/leagues
    Optional: ?after=<ISO 8601 timestamp>
    """
    after = _parse_after_param()

    try:
        with get_session() as session:
            q = session.query(League)

            if after:
                q = q.filter(League.created_at >= after)

            leagues = q.order_by(League.league_id.asc()).all()

            results = [
                {
                    "league_id": l.league_id,
                    "name": l.name,
                    "code": l.code,
                    "timezone": l.timezone,
                    "created_at": l.created_at.isoformat() if l.created_at is not None else None,  # type: ignore
                }
                for l in leagues
            ]
    except Exception as e:
        logger.error(f"Error listing leagues {e}", exc_info=True)
        return jsonify({"error": "internal server error"}), 500

    return jsonify(results)


@bp.route("/<int:league_id>", methods=["GET"], strict_slashes=False)
def get_league(league_id: int):
    """
    GET /api/v1/leagues/<league_id>
    """
    try:
        with get_session() as session:
            l = session.query(League).filter(League.league_id == league_id).first()
            if not l:
                return jsonify({"error": "league not found"}), 404

            result = {
                "league_id": l.league_id,
                "name": l.name,
                "code": l.code,
                "timezone": l.timezone,
                "created_at": l.created_at.isoformat() if l.created_at is not None else None,  # type: ignore
            }
    except Exception as e:
        logger.error(f"Error getting league {league_id}: {e}", exc_info=True)
        return jsonify({"error": "internal server error"}), 500

    return jsonify(result)
