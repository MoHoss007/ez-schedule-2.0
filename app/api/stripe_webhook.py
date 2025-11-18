import stripe
from flask import Blueprint, request, current_app
from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError
from app.db.session import get_session
from app.db.models import User, Subscription, SubscriptionStatus
from stripe.error import SignatureVerificationError
from app.api.utils import _cfg
import logging


logger = logging.getLogger(__name__)

bp = Blueprint("stripe", __name__)


@bp.post("/webhook")
def webhook():
    with get_session() as db:
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
            logger.info("Processing checkout.session.completed webhook")
            session_obj = obj
            customer_id = session_obj.get("customer")
            subscription_id = session_obj.get("subscription")
            email = (session_obj.get("customer_details", {}) or {}).get(
                "email"
            ) or session_obj.get("customer_email")

            if not (customer_id and subscription_id and email):
                logger.error("Missing fields in checkout.session.completed webhook")
                return "missing fields", 200

            stripe_sub = stripe.Subscription.retrieve(subscription_id, expand=["items"])
            item = stripe_sub["items"]["data"][0]
            quantity = item["quantity"]
            cpe = datetime.fromtimestamp(
                stripe_sub["current_period_end"], tz=timezone.utc
            )

            user = db.query(User).filter(User.email == email).first()
            if not user:
                user = User(email=email)
                db.add(user)
                db.flush()

            existing = (
                db.query(Subscription)
                .filter(Subscription.user_id == user.user_id)
                .first()
            )
            if existing:
                logger.info(
                    f"Updating existing subscription for user_id={user.user_id}"
                )
                existing.stripe_customer_id = customer_id
                existing.stripe_subscription_id = subscription_id
                existing.current_teams = quantity
                existing.future_teams = quantity
                existing.current_period_end = cpe  # type: ignore
                existing.status = SubscriptionStatus.active
            else:
                logger.info(f"Creating new subscription for user_id={user.user_id}")
                sub = Subscription(
                    user_id=user.user_id,
                    stripe_customer_id=customer_id,
                    stripe_subscription_id=subscription_id,
                    current_teams=quantity,
                    future_teams=quantity,
                    current_period_end=cpe,
                    status=SubscriptionStatus.active,
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

        elif etype == "invoice.upcoming":
            logger.info("Processing invoice.upcoming webhook")
            invoice = obj
            sub_id = invoice.get("subscription")
            if not sub_id:
                logger.info("invoice.upcoming webhook missing subscription id")
                return "ok", 200

            sub_rec = (
                db.query(Subscription)
                .filter(Subscription.stripe_subscription_id == sub_id)
                .first()
            )
            if not sub_rec:
                logger.info(
                    f"No subscription record found for stripe_subscription_id={sub_id}"
                )
                return "ok", 200

            if sub_rec.future_teams != sub_rec.current_teams:  # type: ignore
                stripe_sub = stripe.Subscription.retrieve(sub_id, expand=["items"])
                item_id = stripe_sub["items"]["data"][0]["id"]

                stripe.Subscription.modify(
                    sub_id,
                    items=[{"id": item_id, "quantity": sub_rec.future_teams}],
                    proration_behavior="none",
                    billing_cycle_anchor="unchanged",
                )

                sub_rec.current_teams = (
                    sub_rec.future_teams
                )  # reflect the upcoming change

            return "ok", 200

        elif etype == "customer.subscription.updated":
            logger.info("Processing customer.subscription.updated webhook")
            sub = obj
            sub_id = sub["id"]

            rec = (
                db.query(Subscription)
                .filter(Subscription.stripe_subscription_id == sub_id)
                .first()
            )
            if rec:
                stripe_status = sub.get("status")
                try:
                    rec.status = SubscriptionStatus(stripe_status)
                except Exception:
                    logger.error(
                        f"Error updating subscription status for stripe_subscription_id={sub_id}",
                        exc_info=True,
                    )

                cpe = sub.get("current_period_end")
                if cpe:
                    rec.current_period_end = datetime.fromtimestamp(  # type: ignore
                        cpe, tz=timezone.utc
                    )

            return "ok", 200

        elif etype == "customer.subscription.deleted":
            logger.info("Processing customer.subscription.deleted webhook")
            sub = obj
            sub_id = sub["id"]

            rec = (
                db.query(Subscription)
                .filter(Subscription.stripe_subscription_id == sub_id)
                .first()
            )
            if rec:
                rec.status = SubscriptionStatus.canceled

            return "ok", 200

        elif etype == "invoice.payment_succeeded":
            logger.info("Processing invoice.payment_succeeded webhook")
            inv = obj
            sub_id = inv.get("subscription")
            if sub_id:
                rec = (
                    db.query(Subscription)
                    .filter(Subscription.stripe_subscription_id == sub_id)
                    .first()
                )
                if rec:
                    s = stripe.Subscription.retrieve(sub_id)
                    rec.current_period_end = datetime.fromtimestamp(  # type: ignore
                        s["current_period_end"], tz=timezone.utc
                    )
            return "ok", 200

        return "ok", 200
