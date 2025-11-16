from flask import Blueprint, request, jsonify, g, abort
from app.config import Config
from app.db.session import get_session
from app.db.models import User, Subscription
from app.api.utils import _cfg
import stripe


bp = Blueprint("billing_api", __name__)


@bp.post("/checkout-sessions")
def create_checkout_session():
    data = request.get_json() or {}
    user_id = data.get("user_id")
    teams = data.get("teams")

    if not user_id or not teams:
        return jsonify({"error": "user_id and teams are required"}), 400

    with get_session() as session:
        user = session.query(User).filter(User.user_id == int(user_id)).first()
        if not user:
            return jsonify({"error": "user not found"}), 404

        user_email = user.email

    price_id = _cfg("STRIPE_PRICE_ID")
    if not price_id:
        return jsonify({"error": "Stripe price ID not configured"}), 500

    stripe_session = stripe.checkout.Session.create(
        mode="subscription",
        success_url=_cfg("STRIPE_SUCCESS_URL"),
        cancel_url=_cfg("STRIPE_CANCEL_URL"),
        customer_email=user_email,
        line_items=[
            {
                "price": price_id,
                "quantity": int(teams),
            }
        ],
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


@bp.get("/subscriptions")
def list_subscriptions():
    user_email = request.args.get("user_email")
    user_id = request.args.get("user_id")

    # always extract data inside the session block
    with get_session() as session:
        q = session.query(Subscription)
        if user_email:
            q = q.join(User).filter(User.email == user_email)
        if user_id:
            q = q.filter(Subscription.user_id == int(user_id))

        subs = q.all()

        # convert inside session
        results = [
            {
                "id": s.subscription_id,
                "user_id": s.user_id,
                "stripe_subscription_id": s.stripe_subscription_id,
                "current_teams": s.current_teams,
                "future_teams": s.future_teams,
                "status": s.status.value,
                "current_period_end": (
                    s.current_period_end.isoformat()
                    if s.current_period_end is not None
                    else None
                ),
            }
            for s in subs
        ]

    return jsonify(results)


@bp.get("/subscriptions/<int:sub_id>")
def get_subscription(sub_id):
    with get_session() as session:
        s = (
            session.query(Subscription)
            .filter(Subscription.subscription_id == sub_id)
            .first()
        )

        if not s:
            return jsonify({"error": "subscription not found"}), 404

        result = {
            "id": s.subscription_id,
            "user_id": s.user_id,
            "stripe_subscription_id": s.stripe_subscription_id,
            "current_teams": s.current_teams,
            "future_teams": s.future_teams,
            "status": s.status.value,
            "current_period_end": (
                s.current_period_end.isoformat()
                if s.current_period_end is not None
                else None
            ),
        }

    return jsonify(result)


@bp.patch("/subscriptions/<int:sub_id>")
def update_subscription(sub_id):
    """
    PATCH /api/v1/billing/subscriptions/<sub_id>

    Supports:
    - { "future_teams": X } → next period change
    - { "current_teams": X } → immediate increase only (prorated now)
    """
    with get_session() as session:
        s = session.query(Subscription).filter(Subscription.id == sub_id).first()

        if not s:
            return jsonify({"error": "subscription not found"}), 404

        data = request.get_json() or {}

        if "current_teams" in data:
            new_current = int(data["current_teams"])

            if new_current < s.current_teams:  # type: ignore
                return (
                    jsonify(
                        {
                            "error": "Immediate decrease is not allowed. Use 'future_teams' for next cycle."
                        }
                    ),
                    400,
                )

            if new_current > s.current_teams:  # type: ignore
                # --- Stripe prorated update ---
                stripe_sub = stripe.Subscription.retrieve(
                    s.stripe_subscription_id, expand=["items"]
                )
                item_id = stripe_sub["items"]["data"][0]["id"]

                # Update with proration
                stripe.Subscription.modify(
                    s.stripe_subscription_id,
                    items=[{"id": item_id, "quantity": new_current}],
                    proration_behavior="create_prorations",
                    billing_cycle_anchor="unchanged",
                    payment_behavior="allow_incomplete",
                )

                # Create + finalize + pay invoice with the proration cost
                invoice = stripe.Invoice.create(
                    customer=s.stripe_customer_id,
                    pending_invoice_items_behavior="include",
                    collection_method="charge_automatically",
                    auto_advance=False,
                )
                invoice = stripe.Invoice.finalize_invoice(invoice.id)  # type: ignore
                invoice = stripe.Invoice.pay(invoice.id)

                s.current_teams = new_current  # type: ignore
                # keep future_teams >= current_teams logically
                if s.future_teams < new_current:  # type: ignore
                    s.future_teams = new_current  # type: ignore

        #
        # ✅ 2. Handle deferred change (next cycle)
        #
        if "future_teams" in data:
            new_future = int(data["future_teams"])
            if new_future < 1:
                return jsonify({"error": "future_teams must be >= 1"}), 400

            s.future_teams = new_future  # type: ignore

        return jsonify(
            {
                "id": s.id,
                "current_teams": s.current_teams,
                "future_teams": s.future_teams,
            }
        )
