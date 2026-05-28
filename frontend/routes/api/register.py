import sys
from pathlib import Path

from flask import Blueprint, render_template, request, redirect, url_for, flash
import requests

sys.path.append(str(Path(__file__).resolve().parents[2]))

from env import API_BASE

ENDPOINT = f'{API_BASE}/students'

register_bp = Blueprint("register", __name__)

@register_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template(
            "register.html",
            ENDPOINT=ENDPOINT,
        )

    data = {
        "first": request.form.get("first"),
        "last": request.form.get("last"),
        "password": request.form.get("password"),
        "phone": request.form.get("phone"),
        "email": request.form.get("email"),
        "birthdate": request.form.get("birthdate"),
        "address_1": request.form.get("address_1"),
        "address_2": request.form.get("address_2"),
        "city": request.form.get("city"),
        "state": request.form.get("state"),
        "zipcode": request.form.get("zipcode"),
        "emergency_contact_name": request.form.get("emergency_contact_name"),
        "emergency_contact_relationship": request.form.get("emergency_contact_relationship"),
        "emergency_contact_phone": request.form.get("emergency_contact_phone"),
    }

    files = {}

    profile = request.files.get("profile_picture")
    waiver = request.files.get("waiver")

    if profile and profile.filename:
        files["profile_picture"] = (
            profile.filename,
            profile.stream,
            profile.mimetype
        )

    if waiver and waiver.filename:
        files["waiver"] = (
            waiver.filename,
            waiver.stream,
            waiver.mimetype
        )

    response = requests.post(
        ENDPOINT,
        data=data,
        files=files
    )

    print("STATUS:", response.status_code)
    print("RESPONSE:", response.text)

    if response.status_code == 409:
        flash("An account with this email already exists. Please log in.", "error")
        return redirect(url_for("login"))

    if not response.ok:
        flash(f"Registration failed: {response.json().get('detail', 'Unknown error')}", "error")
        return redirect(url_for("register"))

    if not response.ok:
        # something went wrong
        return f"Registration failed: {response.text}", 400

    # success → go to success page
    return redirect(url_for("register.success"))

