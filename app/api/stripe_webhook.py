import stripe
from flask import Blueprint, request, current_app
from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError
from app.db.session import get_session
from app.db.models import User, Subscription, SubscriptionStatus
from stripe.error import SignatureVerificationError

bp = Blueprint("stripe", __name__)


@bp.post("/webhook")
def webhook():
    with get_session() as db:
        payload = request.data
        sig = request.headers.get("Stripe-Signature")

        # Better: set once at app startup. Safe here too.
        stripe.api_key = current_app.config["STRIPE_SECRET_KEY"]
        endpoint_secret = current_app.config["STRIPE_WEBHOOK_SECRET"]

        # 1) Safer construction: catch JSON parse + sig errors
        try:
            event = stripe.Webhook.construct_event(payload, sig, endpoint_secret)
        except ValueError:
            return "invalid payload", 400
        except SignatureVerificationError:
            return "bad sig", 400

        # 2) Idempotency guard (optional but recommended)
        # if db.query(StripeEventLog).filter_by(event_id=event["id"]).first():
        #     return "ok", 200
        # db.add(StripeEventLog(event_id=event["id"]))

        etype = event["type"]
        obj = event["data"]["object"]

        # 1) When checkout finishes
        if etype == "checkout.session.completed":
            session_obj = obj
            customer_id = session_obj.get("customer")
            subscription_id = session_obj.get("subscription")
            email = (session_obj.get("customer_details", {}) or {}).get(
                "email"
            ) or session_obj.get("customer_email")

            if not (customer_id and subscription_id and email):
                # Don’t proceed if critical identifiers are missing
                return "missing fields", 200

            # Fetch sub to read quantity and current_period_end
            stripe_sub = stripe.Subscription.retrieve(subscription_id, expand=["items"])
            item = stripe_sub["items"]["data"][0]
            quantity = item["quantity"]
            cpe = datetime.fromtimestamp(
                stripe_sub["current_period_end"], tz=timezone.utc
            )

            # user
            user = db.query(User).filter(User.email == email).first()
            if not user:
                user = User(email=email)
                db.add(user)
                db.flush()  # so user.id is available

            # one-sub-per-user policy: update existing row if present
            existing = (
                db.query(Subscription).filter(Subscription.user_id == user.id).first()
            )
            if existing:
                existing.stripe_customer_id = customer_id
                existing.stripe_subscription_id = subscription_id
                existing.current_teams = quantity
                existing.future_teams = quantity
                existing.current_period_end = cpe  # type: ignore
                existing.status = SubscriptionStatus.active
            else:
                sub = Subscription(
                    user_id=user.id,
                    stripe_customer_id=customer_id,
                    stripe_subscription_id=subscription_id,
                    current_teams=quantity,
                    future_teams=quantity,
                    current_period_end=cpe,
                    status=SubscriptionStatus.active,
                )
                db.add(sub)

            # If you have uniques on stripe ids, guard for races
            try:
                # commit is done by context manager on exit, but this
                # helps surface integrity errors here if you prefer:
                db.flush()
            except IntegrityError:
                db.rollback()
                return "conflict", 409

            return "ok", 200

        # 2) Before Stripe invoices -> sync our future_teams to Stripe
        elif etype == "invoice.upcoming":
            invoice = obj
            sub_id = invoice.get("subscription")
            if not sub_id:
                return "ok", 200

            sub_rec = (
                db.query(Subscription)
                .filter(Subscription.stripe_subscription_id == sub_id)
                .first()
            )
            if not sub_rec:
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

        # 3) Keep status & period end in sync during lifecycle updates
        elif etype == "customer.subscription.updated":
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
                    pass

                cpe = sub.get("current_period_end")
                if cpe:
                    rec.current_period_end = datetime.fromtimestamp(  # type: ignore
                        cpe, tz=timezone.utc
                    )

            return "ok", 200

        # 4) Subscription ended
        elif etype == "customer.subscription.deleted":
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

        # 5) (Optional but useful) Mark the new period after payment success
        elif etype == "invoice.payment_succeeded":
            inv = obj
            sub_id = inv.get("subscription")
            if sub_id:
                rec = (
                    db.query(Subscription)
                    .filter(Subscription.stripe_subscription_id == sub_id)
                    .first()
                )
                if rec:
                    # On payment success, the period has advanced; refresh from Stripe for accurate CPE
                    s = stripe.Subscription.retrieve(sub_id)
                    rec.current_period_end = datetime.fromtimestamp(  # type: ignore
                        s["current_period_end"], tz=timezone.utc
                    )
            return "ok", 200

        return "ok", 200
