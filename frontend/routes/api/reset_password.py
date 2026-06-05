import sys
from pathlib import Path

from flask import Blueprint, render_template, request, redirect, url_for, flash
import requests

sys.path.append(str(Path(__file__).resolve().parents[2]))

from env import API_BASE

reset_password_bp = Blueprint("reset_password", __name__)


@reset_password_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "GET":
        return render_template("forgot_password.html")

    email = request.form.get("email")

    try:
        res = requests.post(
            f"{API_BASE}/auth/forgot-password",
            json={"email": email},
            timeout=5
        )

        data = res.json()

        return render_template(
            "forgot_password.html",
            success=data.get("message", "If email exists, reset link sent.")
        )

    except Exception:
        return render_template(
            "forgot_password.html",
            error="Something went wrong. Please try again."
        )

@reset_password_bp.route("/reset-password", methods=["GET"])
def reset_password_page():
    token = request.args.get("token")

    if not token:
        return render_template("reset_password.html", error="Missing token")

    return render_template("reset_password.html", token=token)


@reset_password_bp.route("/reset-password", methods=["POST"])
def reset_password_submit():
    token = request.form.get("token")
    new_password = request.form.get("new_password")

    if not token or not new_password:
        flash("Missing token or password", "error")
        return redirect(request.url)

    try:
        response = requests.post(
            f"{API_BASE}/auth/reset-password",
            json={
                "token": token,
                "new_password": new_password
            },
            timeout=10
        )

        try:
            data = response.json()
        except Exception:
            data = {"detail": "Unexpected server response"}

        if response.status_code != 200:
            flash(data.get("detail", "Error resetting password"), "error")
            return redirect(request.url)

    except Exception as e:
        print("Reset password error:", str(e))
        flash("Server error. Try again.", "error")
        return redirect(request.url)

    flash("Password updated successfully!", "success")
    return redirect(url_for("signin"))

