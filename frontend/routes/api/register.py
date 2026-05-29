import sys
from pathlib import Path

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import requests

sys.path.append(str(Path(__file__).resolve().parents[2]))

from env import API_BASE

ENDPOINT = f'{API_BASE}/students'

register_bp = Blueprint("register", __name__)

@register_bp.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "GET":
        return render_template("register.html")

    try:
        required_fields = [
            "first",
            "last",
            "password",
            "phone",
            "email",
            "birthdate",
            "address_1",
            "city",
            "state",
            "zipcode",
            "emergency_contact_name",
            "emergency_contact_relationship",
            "emergency_contact_phone",
        ]

        data = {}

        for field in required_fields:
            value = request.form.get(field)

            if not value:
                flash(f"{field} is required", "error")
                return {"error": "Account already exists"}, 409

            data[field] = value

        data["address_2"] = request.form.get("address_2")

        profile = request.files.get("profile_picture")
        waiver = request.files.get("waiver_pdf") or request.files.get("waiver")

        if not profile or not profile.filename:
            flash("Profile picture is required", "error")
            return {"error": "Account already exists"}, 409

        if not waiver or not waiver.filename:
            flash("Waiver PDF is required", "error")
            return {"error": "Account already exists"}, 409

        files = {
            "profile_picture": (
                profile.filename,
                profile.stream,
                profile.mimetype,
            ),
            "waiver": (
                waiver.filename,
                waiver.stream,
                waiver.mimetype,
            ),
        }

        response = requests.post(
            f'{API_BASE}/students',
            data=data,
            files=files,
            timeout=30,
        )

        if response.status_code == 409:
            flash("Account already exists", "error")
            return {"error": "Account already exists"}, 409

        if not response.ok:
            try:
                error_msg = response.json().get("detail", "Unknown error")
            except Exception:
                error_msg = response.text

            flash(f"Registration failed: {error_msg}", "error")
            return {"error": "Account already exists"}, 409

        result = response.json()

        email = data["email"]
        password = data["password"]

        res = requests.post(
            f"{API_BASE}/auth",
            json={"email": email, "password": password}
        )

        if res.status_code != 200:
            flash("Invalid login")
            return redirect(url_for("signin"))

        session["token"] = res.json().get("access_token")
        return redirect(url_for("dashboard.dashboard"))

    except requests.RequestException as e:
        flash(f"Network error: {str(e)}", "error")
        return {"error": "Account already exists"}, 409

    except Exception as e:
        flash(f"Unexpected error: {str(e)}", "error")
        return {"error": "Account already exists"}, 409

