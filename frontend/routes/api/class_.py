import sys
from pathlib import Path

from flask import Blueprint, render_template, request, session, redirect, flash

from urllib.parse import urlencode
import requests

sys.path.append(str(Path(__file__).resolve().parents[2]))

from utils.helpers import format_class_details
from env import API_BASE

class_bp = Blueprint("class", __name__)


@class_bp.route("/class/<int:class_id>/checkin")
def class_checkin(class_id):
    response = requests.get(
        f"{API_BASE}/class/{class_id}",
        timeout=5,
    )
    class_details = "Sign in to Check into:<br>" + format_class_details(response.json())["html"]

    token = session.get("token")

    next_url = f"/class/{class_id}/checkin"
    signin_url = f"/signin?{urlencode({"next": next_url, "prompt": class_details})}"

    # If no auth token → redirect to signin with return path
    if not token:
        return redirect(signin_url)

    try:
        resp = requests.get(
            f"{API_BASE}/class/{class_id}/checkin",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )

        try:
            data = resp.json()
            reason = data.get("reason").title()

        except Exception:
            # Invalid response from API → show error page
            return render_template(
                "class_checkin.html",
                status="error",
                title="Invalid Response",
                reason=reason,
                message="Server returned an invalid response. Please try again.",
            )

    except requests.RequestException:
        # Service unreachable → show error page (not redirect, since this is backend failure)
        return render_template(
            "class_checkin.html",
            status="error",
            title="Service Error",
            reason=reason,
            message="Unable to reach check-in service. Please try again shortly.",
        )

    # Unauthorized response → clear session and redirect to signin with next
    if data == "UNAUTHORIZED" or not data.get("authenticated"):
        session.clear()
        flash("Please sign in in order to check into class.")
        return redirect(signin_url)

    # Success case → render success state
    if data.get("status") == "success":
        return render_template(
            "class_checkin.html",
            status="success",
            title="Checked In",
            reason=reason,
            message="You have successfully checked into class.",
        )

    # Failure case → show API-provided reason if available
    else:
        if reason == "ineligible":
            message = "No subscription or classes avialable, please navigate to your dashboard to purchase."
        else:
            message = reason

        return render_template(
            "class_checkin.html",
            status="failed",
            title="Check-In Failed",
            reason=message,
            message=message,
        )