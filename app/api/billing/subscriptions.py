# app/api/billing/subscriptions.py
from __future__ import annotations

from datetime import datetime, timezone

from flask import Blueprint, request, jsonify

import stripe

from app.db.session import get_session
from app.db.models import (
    User,
    Subscription,
    SubscriptionStatus,
    LeagueSeason,
    LeagueSeasonProduct,
)
from app.api.utils import _cfg
import logging

logger = logging.getLogger(__name__)


bp = Blueprint("billing_api", __name__)


@bp.post("/checkout-sessions")
def create_checkout_session():
    """
    Create a Stripe Checkout Session for a subscription tied to a specific league season.

    Body:
    {
      "user_id": 123,
      "league_season_id": 10,
      "team_limit": 8
    }
    """
    data = request.get_json() or {}
    user_id = data.get("user_id")
    league_season_id = data.get("league_season_id")
    team_limit = data.get("team_limit")

    if not user_id or not league_season_id or not team_limit:
        return (
            jsonify(
                {"error": "user_id, league_season_id, and team_limit are required"}
            ),
            400,
        )

    team_limit = int(team_limit)

    now = datetime.now(timezone.utc)
    try:
        with get_session() as session:
            user = session.query(User).filter(User.user_id == int(user_id)).first()
            if not user:
                return jsonify({"error": "user not found"}), 404

            league_season = (
                session.query(LeagueSeason)
                .filter(LeagueSeason.league_season_id == int(league_season_id))
                .first()
            )
            if not league_season:
                return jsonify({"error": "league_season not found"}), 404

            # Optional: enforce subscription window
            logger.info(
                f"Checking subscription window for league_season_id={league_season_id} at {now.isoformat()}"
            )
            logger.info(
                f"Subscription open at: {league_season.subscription_open_at}, close at: {league_season.subscription_close_at}"
            )
            if not (
                league_season.subscription_open_at  # type: ignore
                <= now
                <= league_season.subscription_close_at
            ):
                return (
                    jsonify(
                        {
                            "error": "subscriptions are not open for this season",
                            "season_id": league_season_id,
                        }
                    ),
                    400,
                )

            product = (
                session.query(LeagueSeasonProduct)
                .filter(
                    LeagueSeasonProduct.league_season_id
                    == league_season.league_season_id
                )
                .first()
            )
            if not product:
                return (
                    jsonify(
                        {
                            "error": "Stripe price not configured for this league season",
                            "league_season_id": league_season_id,
                        }
                    ),
                    500,
                )

            user_email = user.email

        stripe_price_id = product.stripe_price_id

        stripe.api_key = _cfg("STRIPE_SECRET_KEY")

        # Encode useful metadata so webhooks can reconstruct Subscription rows
        stripe_session = stripe.checkout.Session.create(
            mode="subscription",
            success_url=_cfg("STRIPE_SUCCESS_URL"),
            cancel_url=_cfg("STRIPE_CANCEL_URL"),
            customer_email=user_email,
            line_items=[
                {
                    "price": stripe_price_id,
                    "quantity": team_limit,
                }
            ],
            client_reference_id=str(user_id),
            subscription_data={
                "metadata": {
                    "user_id": str(user_id),
                    "league_season_id": str(league_season_id),
                    "team_limit": str(team_limit),
                }
            },
            metadata={
                "user_id": str(user_id),
                "league_season_id": str(league_season_id),
                "team_limit": str(team_limit),
            },
        )

        return (
            jsonify(
                {
                    "checkout_session_id": stripe_session.id,  # type: ignore
                    "url": stripe_session.url,  # type: ignore
                }
            ),
            201,
        )
    except Exception as e:
        logger.error(f"Error creating checkout session: {e}")
        return jsonify({"error": "internal server error"}), 500


@bp.get("/subscriptions")
def list_subscriptions():
    """
    Query params:
      - user_email
      - user_id
      - league_season_id
    """
    user_email = request.args.get("user_email")
    user_id = request.args.get("user_id")
    league_season_id = request.args.get("league_season_id")

    with get_session() as session:
        q = session.query(Subscription)

        if user_email:
            q = q.join(User).filter(User.email == user_email)
        if user_id:
            q = q.filter(Subscription.user_id == int(user_id))
        if league_season_id:
            q = q.filter(Subscription.league_season_id == int(league_season_id))

        subs = q.all()

        results = []
        for s in subs:
            ls = s.league_season  # lazy load OK while session open
            league = ls.league if ls else None

            results.append(
                {
                    "id": s.subscription_id,
                    "user_id": s.user_id,
                    "league_season_id": s.league_season_id,
                    "league_id": league.league_id if league else None,
                    "league_name": league.name if league else None,
                    "season_name": ls.name if ls else None,
                    "team_limit": s.team_limit,
                    "billed_team_count": s.billed_team_count,
                    "status": s.status.value if s.status else None,  # type: ignore
                    "billing_start_at": (
                        s.billing_start_at.isoformat()
                        if s.billing_start_at is not None
                        else None
                    ),
                    "created_at": (
                        s.created_at.isoformat() if s.created_at is not None else None
                    ),
                    "updated_at": (
                        s.updated_at.isoformat() if s.updated_at is not None else None
                    ),
                }
            )

    return jsonify(results)


@bp.get("/subscriptions/<int:sub_id>")
def get_subscription(sub_id: int):
    with get_session() as session:
        s = (
            session.query(Subscription)
            .filter(Subscription.subscription_id == sub_id)
            .first()
        )

        if not s:
            return jsonify({"error": "subscription not found"}), 404

        ls = s.league_season
        league = ls.league if ls else None

        result = {
            "id": s.subscription_id,
            "user_id": s.user_id,
            "league_season_id": s.league_season_id,
            "league_id": league.league_id if league else None,
            "league_name": league.name if league else None,
            "season_name": ls.name if ls else None,
            "team_limit": s.team_limit,
            "billed_team_count": s.billed_team_count,
            "status": s.status.value if s.status else None,  # type: ignore
            "billing_start_at": (
                s.billing_start_at.isoformat()
                if s.billing_start_at is not None
                else None
            ),
            "created_at": (
                s.created_at.isoformat() if s.created_at is not None else None
            ),
            "updated_at": (
                s.updated_at.isoformat() if s.updated_at is not None else None
            ),
        }

    return jsonify(result)


@bp.patch("/subscriptions/<int:sub_id>")
def update_subscription(sub_id: int):
    """
    PATCH /api/v1/billing/subscriptions/<sub_id>

    Supports:
    - { "team_limit": X }  # change team count for this season (pre-deadline)
    """
    data = request.get_json() or {}

    if "team_limit" not in data:
        return jsonify({"error": "team_limit is required"}), 400

    new_team_limit = int(data["team_limit"])
    if new_team_limit < 1:
        return jsonify({"error": "team_limit must be >= 1"}), 400

    now = datetime.now(timezone.utc)

    with get_session() as session:
        s = (
            session.query(Subscription)
            .filter(Subscription.subscription_id == sub_id)
            .first()
        )

        if not s:
            return jsonify({"error": "subscription not found"}), 404

        ls = s.league_season
        if not ls:
            return jsonify({"error": "league season not found for subscription"}), 500

        # Enforce season deadline for changes
        if ls.change_deadline_for_current and now > ls.change_deadline_for_current:
            return (
                jsonify(
                    {
                        "error": "change deadline passed for this season",
                        "change_deadline_for_current": ls.change_deadline_for_current.isoformat(),
                    }
                ),
                400,
            )

        s.team_limit = new_team_limit  # type: ignore

        # Update Stripe subscription quantity (no proration before season start)
        if s.stripe_subscription_id:  # type: ignore
            stripe.api_key = _cfg("STRIPE_SECRET_KEY")
            stripe_sub = stripe.Subscription.retrieve(
                s.stripe_subscription_id, expand=["items"]
            )
            item_id = stripe_sub["items"]["data"][0]["id"]

            stripe.Subscription.modify(
                s.stripe_subscription_id,
                items=[{"id": item_id, "quantity": new_team_limit}],
                proration_behavior="none",
                billing_cycle_anchor="unchanged",
            )

        return jsonify(
            {
                "id": s.subscription_id,
                "team_limit": s.team_limit,
            }
        )
