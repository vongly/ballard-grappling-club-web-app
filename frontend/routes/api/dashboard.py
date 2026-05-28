import sys
from pathlib import Path
from datetime import datetime

from flask import Blueprint, render_template, redirect, session, request, jsonify
import requests

sys.path.append(str(Path(__file__).resolve().parents[3]))

from env import API_BASE


STRIPE_CHECKOUT_ENDPOINT = f"{API_BASE}/stripe/checkout"

dashboard_bp = Blueprint("dashboard", __name__)


def format_phone(phone: str | None) -> str:
    if not phone:
        return ""

    digits = "".join(c for c in phone if c.isdigit())

    if len(digits) < 10:
        return ""
    return f"({digits[:3]}) {digits[3:6]}-{digits[6:10]}"

def format_date(value):
    if not value:
        return ""

    if isinstance(value, str):
        value = datetime.fromisoformat(value)

    return value.strftime("%-m/%-d/%Y")

def api_get(path, token):
    try:
        res = requests.get(
            f"{API_BASE}{path}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )

        if res.status_code == 401:
            return "UNAUTHORIZED"

        if res.status_code != 200:
            return None

        return res.json()

    except requests.RequestException:
        return None


# -----------------------------
# DASHBOARD
# -----------------------------
@dashboard_bp.route("/dashboard")
def dashboard():

    token = session.get("token")

    if not token:
        return redirect("/signin")

    student = api_get("/students/me", token)
    if student == "UNAUTHORIZED" or not student:
        session.clear()
        return redirect("/signin")

    student["birthdate_formatted"] = format_date(student["birthdate"])
    student["phone_formatted"] = format_phone(student["phone"])
    student["emergency_contact_phone_formatted"] = format_phone(student["emergency_contact_phone"])

    subscription_record = api_get("/subscriptions/me", token)

    products = api_get("/products", token) or []

    '''
    Checks for subscription record
    -> if subscription record exists find the product
        also remove products to purchase
    -> if not set to null
    '''
    active_products = [p for p in products if p.get("active") == 1]
    subscription_product = None

    if subscription_record:
        if subscription_record["status"] in [1,2]:
            subscription_product = [p for p in products if p.get("price_id") == subscription_record.get("stripe_price_id")][0]
            active_products = []

    active_products.sort(key=lambda p: p.get("product_order", 0))


    return render_template(
        "dashboard.html",
        student=student,
        products=active_products,
        subscription=subscription_record,
        subscription_product=subscription_product,
        stripe_checkout_endpoint=STRIPE_CHECKOUT_ENDPOINT,
    )


@dashboard_bp.route("/checkout", methods=["POST"])
def checkout():

    token = session.get("token")
    data = request.get_json()
    product_id = data.get("product_id")

    try:
        res = requests.post(
            STRIPE_CHECKOUT_ENDPOINT,
            headers={"Authorization": f"Bearer {token}"},
            json={"product_id": product_id},
            timeout=10
        )

        # IMPORTANT: handle non-JSON safely
        try:
            payload = res.json()
        except Exception:
            return {
                "error": "invalid_response",
                "status_code": res.status_code,
                "raw": res.text
            }, 500

        return payload, res.status_code

    except requests.RequestException as e:
        return {
            "error": "network_error",
            "detail": str(e)
        }, 500