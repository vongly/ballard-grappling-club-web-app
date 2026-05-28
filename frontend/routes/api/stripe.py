import sys
from pathlib import Path
import requests

import stripe
from flask import Blueprint, request, render_template

sys.path.append(str(Path(__file__).resolve().parents[3]))

from env import STRIPE_KEY, API_BASE


stripe.api_key = STRIPE_KEY

stripe_ui_bp = Blueprint("stripe_ui", __name__)

UNWANTED_KEYS = {
    # UI / branding
    "branding_settings",
    "custom_text",
    "ui_mode",
    "locale",
    "client_secret",
    "success_url",
    "cancel_url",

    # Stripe internal / transport
    "livemode",
    "integration_identifier",
    "origin_context",
    "permissions",
    "managed_payments",
    "wallet_options",

    # checkout config noise
    "payment_method_options",
    "payment_method_configuration_details",
    "payment_method_collection",
    "saved_payment_method_options",

    # session mechanics
    "expires_at",
    "after_expiration",
    "recovered_from",

    # compliance / collection noise
    "collected_information",
    "consent",
    "consent_collection",

    # shipping / tax (if unused)
    "automatic_tax",
    "shipping_cost",
    "shipping_options",
    "shipping_address_collection",
}


def clean_stripe_session(session: dict, unwanted_keys=UNWANTED_KEYS) -> dict:
    def _strip(obj):
        if isinstance(obj, dict):
            return {
                k: _strip(v)
                for k, v in obj.items()
                if k not in unwanted_keys
            }
        elif isinstance(obj, list):
            return [_strip(i) for i in obj]
        else:
            return obj

    return _strip(session)

@stripe_ui_bp.route("/stripe/checkout/success")
def success():
    session_id = request.args.get("session_id")

    session = stripe.checkout.Session.retrieve(
        session_id,
        expand=[
            "line_items",
            "line_items.data.price.product",
            "customer",
            "payment_intent",
        ],
    )

    session_cleaned = clean_stripe_session(session)

    return render_template(
        "checkout-success.html",
        session_id=session_id,
        session=session_cleaned,
    )

@stripe_ui_bp.route("/stripe/checkout/cancel")
def cancel():
    return render_template("checkout-cancel.html")