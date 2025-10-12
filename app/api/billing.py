# app/api/billing.py
from flask import Blueprint, request, jsonify, current_app
import stripe
import os

billing_bp = Blueprint("billing_bp", __name__, url_prefix="/billing")

def _frontend_url() -> str:
    # If you serve vite dev on 5173 locally, keep this default.
    return os.getenv("FRONTEND_URL", "http://localhost:5173")

@billing_bp.before_app_first_request
def _configure_stripe():
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY")  # set in your env

@billing_bp.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    """
    Expects JSON:
      {
        "email": "club@org.com",         # optional but recommended
        "club": "My Club",               # optional
        "items": [ { "id": 1, "amount": 0.5 }, ... ]
      }
    Returns:
      { "ok": true, "url": "https://checkout.stripe.com/..." }
    """
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip() or None
    club  = (data.get("club") or "").strip() or None
    items = data.get("items") or []  # [{id, amount}, ...]

    if not isinstance(items, list) or len(items) == 0:
        return jsonify({"ok": False, "error": "No items provided"}), 400

    # Build dynamic line_items from your $/team selections
    line_items = []
    for entry in items:
        try:
            team_id = int(entry["id"])
            amount  = float(entry["amount"])  # 0.5 => $0.50
        except (KeyError, ValueError, TypeError):
            return jsonify({"ok": False, "error": "Invalid item format"}), 400

        line_items.append({
            "price_data": {
                "currency": "usd",
                "product_data": {
                    "name": f"Team Registration (Team ID: {team_id})",
                    "metadata": {"team_id": str(team_id), "club": club or ""},
                },
                # Stripe expects cents
                "unit_amount": int(round(amount * 100)),
            },
            "quantity": 1,
        })

    # success/cancel URLs for your SPA
    success_url = f"{_frontend_url()}/payment/success"
    cancel_url  = f"{_frontend_url()}/payment"

    try:
        session = stripe.checkout.Session.create(
            mode="payment",
            line_items=line_items,
            success_url=success_url,
            cancel_url=cancel_url,
            customer_email=email,  # Stripe sends receipt if email is provided + receipts enabled
            metadata={
                "club": club or "",
                "source": "ez-schedule-2.0",
            },
        )
        return jsonify({"ok": True, "url": session.url})
    except Exception as e:
        current_app.logger.exception("Stripe session error")
        return jsonify({"ok": False, "error": str(e)}), 500
