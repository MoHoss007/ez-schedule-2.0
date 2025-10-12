# app/api/billing.py
from flask import Blueprint, request, jsonify, current_app
import stripe
import os
from decimal import Decimal, ROUND_HALF_UP

PRICE_PER_TEAM_CAD = Decimal("0.50")

billing_bp = Blueprint("billing_bp", __name__, url_prefix="/billing")

def _frontend_url() -> str:
    # If you serve vite dev on 5173 locally, keep this default.
    return os.getenv("FRONTEND_URL", "http://localhost:5173")

@billing_bp.before_app_first_request
def _configure_stripe():
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY")  # set in your env

@billing_bp.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    # 0) Guard: Stripe key configured
    if not stripe.api_key:
        return jsonify({"ok": False, "error": "Stripe not configured"}), 500

    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip() or None
    club  = (data.get("club") or "").strip() or None
    items = data.get("items") or []  # Expect [{ "id": <teamId> }, ...]

    # 1) Validate cart: require team ids, dedupe
    if not isinstance(items, list) or not items:
        return jsonify({"ok": False, "error": "No items provided"}), 400
    try:
        team_ids = [int(i["id"]) for i in items]
    except Exception:
        return jsonify({"ok": False, "error": "Invalid item format"}), 400
    team_ids = list(dict.fromkeys(team_ids))
    quantity = len(team_ids)
    if quantity <= 0:
        return jsonify({"ok": False, "error": "No valid teams"}), 400

    # (Optional) cross-check team_ids exist & belong to this club in your DB
    # e.g., assert_club_owns_teams(club, team_ids)

    # 2) Compute unit amount on server (Stripe uses cents as int)
    unit_amount_cents = int((PRICE_PER_TEAM_CAD * 100).to_integral_value(rounding=ROUND_HALF_UP))
    if unit_amount_cents < 50:  # Stripe minimum for USD is $0.50
        return jsonify({"ok": False, "error": "Amount below Stripe minimum"}), 400

    line_items = [{
        "price_data": {
            "currency": "usd",
            "product_data": {
                "name": "Team Registrations",
                "metadata": {"club": club or "", "team_ids": ",".join(map(str, team_ids))},
            },
            "unit_amount": unit_amount_cents,
        },
        "quantity": quantity,
    }]

    success_url = f"{_frontend_url()}/payment/success"
    cancel_url  = f"{_frontend_url()}/payment"

    try:
        session = stripe.checkout.Session.create(
            mode="payment",
            line_items=line_items,
            success_url=success_url,
            cancel_url=cancel_url,
            customer_email=email,
            # payment_method_types=['card'],  # optional; modern Stripe defaults are fine
            metadata={"club": club or "", "team_ids": ",".join(map(str, team_ids)), "source": "ez-schedule-2.0"},
        )
        return jsonify({"ok": True, "url": session.url})
    except Exception as e:
        current_app.logger.exception("Stripe session error")
        return jsonify({"ok": False, "error": str(e)}), 500
