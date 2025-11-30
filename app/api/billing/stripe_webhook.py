# app/api/billing/stripe_webhooks.py
from __future__ import annotations

from datetime import datetime, timezone

import logging

import stripe
from flask import Blueprint, request

from sqlalchemy.exc import IntegrityError

from app.db.session import get_session
from app.db.models import (
    User,
    Subscription,
    SubscriptionStatus,
    LeagueSeason,
)
from app.api.utils import _cfg
from stripe.error import SignatureVerificationError


logger = logging.getLogger(__name__)

bp = Blueprint("stripe", __name__)


@bp.post("/webhook")
def webhook():
    payload = request.data
    sig = request.headers.get("Stripe-Signature")

    stripe.api_key = _cfg("STRIPE_SECRET_KEY")
    endpoint_secret = _cfg("STRIPE_WEBHOOK_SECRET")

    try:
        event = stripe.Webhook.construct_event(payload, sig, endpoint_secret)
        logger.info(f"Received event: {event['type']}")
    except ValueError:
        logger.error("Invalid payload")
        return "invalid payload", 400
    except SignatureVerificationError:
        logger.error("Bad signature")
        return "bad sig", 400

    etype = event["type"]
    obj = event["data"]["object"]

    if etype == "checkout.session.completed":
        return _handle_checkout_session_completed(obj)

    elif etype == "customer.subscription.updated":
        return _handle_customer_subscription_updated(obj)

    elif etype == "customer.subscription.deleted":
        return _handle_customer_subscription_deleted(obj)

    elif etype == "invoice.payment_succeeded":
        return _handle_invoice_payment_succeeded(obj)

    # Other events we don't care about (yet)
    return "ok", 200


# ---------------- Handlers -----------------


def _handle_checkout_session_completed(session_obj):
    """
    When a Checkout Session completes, create or update our Subscription row.
    """
    with get_session() as db:
        customer_id = session_obj.get("customer")
        subscription_id = session_obj.get("subscription")

        # We put metadata on either `session_obj["metadata"]` or `subscription_data.metadata`
        md = session_obj.get("metadata") or {}
        user_id_str = md.get("user_id") or session_obj.get("client_reference_id")
        league_season_id_str = md.get("league_season_id")
        team_limit_str = md.get("team_limit")

        if not (
            customer_id and subscription_id and user_id_str and league_season_id_str
        ):
            logger.error(
                "checkout.session.completed missing required fields "
                f"(customer_id={customer_id}, subscription_id={subscription_id}, "
                f"user_id={user_id_str}, league_season_id={league_season_id_str})"
            )
            return "missing fields", 200

        try:
            user_id = int(user_id_str)
            league_season_id = int(league_season_id_str)
        except Exception:
            logger.exception("Invalid user_id or league_season_id in metadata")
            return "bad metadata", 200

        team_limit = int(team_limit_str) if team_limit_str else None

        user = db.get(User, user_id)
        if not user:
            # In practice, the user should always exist (logged-in when starting checkout)
            logger.error(
                f"User with id={user_id} not found for checkout.session.completed"
            )
            return "user not found", 200

        league_season = db.get(LeagueSeason, league_season_id)
        if not league_season:
            logger.error(
                f"LeagueSeason with id={league_season_id} not found for checkout.session.completed"
            )
            return "league_season not found", 200

        # Retrieve subscription from Stripe to get quantity, status, etc.
        stripe_sub = stripe.Subscription.retrieve(subscription_id, expand=["items"])
        logger.info(
            f"Retrieved subscription from Stripe: {stripe_sub}, "
            f"keys are {list(stripe_sub.keys())}"
        )
        item = stripe_sub["items"]["data"][0]
        quantity = item["quantity"]
        stripe_status = stripe_sub.get("status")

        # Use quantity from Stripe as source of truth for team_limit
        team_limit = quantity

        existing = (
            db.query(Subscription)
            .filter(
                Subscription.user_id == user_id,
                Subscription.league_season_id == league_season_id,
            )
            .first()
        )

        billing_start_at = league_season.season_start
        now = datetime.now(timezone.utc)

        if existing:
            logger.info(
                f"Updating existing subscription for user_id={user_id}, "
                f"league_season_id={league_season_id}"
            )
            existing.stripe_customer_id = customer_id
            existing.stripe_subscription_id = subscription_id
            existing.team_limit = team_limit
            existing.billed_team_count = team_limit
            existing.status = (  # type: ignore
                SubscriptionStatus(stripe_status)
                if stripe_status
                else SubscriptionStatus.ACTIVE
            )
            existing.billing_start_at = billing_start_at
            existing.updated_at = now  # type: ignore
        else:
            logger.info(
                f"Creating new subscription for user_id={user_id}, "
                f"league_season_id={league_season_id}"
            )
            sub = Subscription(
                user_id=user_id,
                league_season_id=league_season_id,
                stripe_customer_id=customer_id,
                stripe_subscription_id=subscription_id,
                team_limit=team_limit,
                billed_team_count=team_limit,
                status=(
                    SubscriptionStatus(stripe_status)
                    if stripe_status
                    else SubscriptionStatus.ACTIVE
                ),
                billing_start_at=billing_start_at,
                created_at=now,
                updated_at=now,
            )
            db.add(sub)

        try:
            db.flush()
        except IntegrityError:
            db.rollback()
            logger.error(
                "Integrity error while flushing subscription data", exc_info=True
            )
            return "conflict", 409

        return "ok", 200


def _handle_customer_subscription_updated(sub):
    """
    Sync Stripe status & team_limit changes back into our Subscription row.
    """
    sub_id = sub["id"]
    stripe_status = sub.get("status")
    quantity = None

    try:
        item = sub["items"]["data"][0]
        quantity = item["quantity"]
    except Exception:
        pass

    with get_session() as db:
        rec = (
            db.query(Subscription)
            .filter(Subscription.stripe_subscription_id == sub_id)
            .first()
        )
        if not rec:
            logger.info(
                f"No subscription record found for stripe_subscription_id={sub_id}"
            )
            return "ok", 200

        if stripe_status:
            try:
                rec.status = SubscriptionStatus(stripe_status)  # type: ignore
            except Exception:
                logger.error(
                    f"Error updating subscription status for stripe_subscription_id={sub_id}",
                    exc_info=True,
                )

        if quantity is not None:
            rec.team_limit = quantity

        now = datetime.now(timezone.utc)
        rec.updated_at = now  # type: ignore

    return "ok", 200


def _handle_customer_subscription_deleted(sub):
    """
    Mark our Subscription row as canceled when Stripe deletes it.
    """
    sub_id = sub["id"]

    with get_session() as db:
        rec = (
            db.query(Subscription)
            .filter(Subscription.stripe_subscription_id == sub_id)
            .first()
        )
        if rec:
            rec.status = SubscriptionStatus.CANCELED  # type: ignore
            rec.updated_at = datetime.now(timezone.utc)  # type: ignore

    return "ok", 200


def _handle_invoice_payment_succeeded(inv):
    """
    When an invoice is paid, update billing_start_at or billed_team_count if needed.
    For now, just bump updated_at and ensure status is not UNPAID.
    """
    sub_id = inv.get("subscription")
    if not sub_id:
        return "ok", 200

    with get_session() as db:
        rec = (
            db.query(Subscription)
            .filter(Subscription.stripe_subscription_id == sub_id)
            .first()
        )
        if rec:
            # If it's the first invoice, ensure billing_start_at is set to invoice date
            inv_ts = inv.get("created")
            if inv_ts and not rec.billing_start_at:  # type: ignore
                rec.billing_start_at = datetime.fromtimestamp(inv_ts, tz=timezone.utc)  # type: ignore

            # If status was UNPAID, flip it to ACTIVE
            if rec.status == SubscriptionStatus.UNPAID:  # type: ignore
                rec.status = SubscriptionStatus.ACTIVE  # type: ignore
            rec.updated_at = datetime.now(timezone.utc)  # type: ignore

    return "ok", 200
