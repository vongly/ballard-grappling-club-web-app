import sys
from pathlib import Path

from flask import Blueprint, render_template, request, session, redirect, flash, url_for

from urllib.parse import urlencode
import requests
from datetime import datetime, timedelta, date, timezone

sys.path.append(str(Path(__file__).resolve().parents[2]))

from utils.helpers import format_class_details
from env import API_BASE

class_bp = Blueprint("class", __name__)


@class_bp.route("/class/<int:class_id>/students")
def class_students(class_id):
    token = session.get("token")

    if not token:
        return redirect("/signin")

    try:
        response = requests.get(
            f"{API_BASE}/class_attendance/{class_id}/students",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )

        response.raise_for_status()
        students = response.json()

        response = requests.get(
            f"{API_BASE}/class/{class_id}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )

        response.raise_for_status()
        class_details = format_class_details(response.json())["html"]

    except requests.RequestException:
        students = []

    return render_template(
        "classes/class_students.html",
        students=students,
        class_details=class_details,
    )

@class_bp.route("/class/<int:class_id>/checkin")
def class_checkin(class_id):
    response = requests.get(
        f"{API_BASE}/class/{class_id}",
        timeout=5,
    )
    class_details = "Sign in to Check into:<br><br>" + format_class_details(response.json())["html"]

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
                "classes/class_checkin.html",
                status="error",
                title="Invalid Response",
                reason=reason,
                message="Server returned an invalid response. Please try again.",
            )

    except requests.RequestException:
        # Service unreachable → show error page (not redirect, since this is backend failure)
        return render_template(
            "classes/class_checkin.html",
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
        if reason == "hoa":
            message = "Hey it's Hoa, you're always welcome here!"
        else:
            message = reason

        return render_template(
            "classes/class_checkin.html",
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
            "classes/class_checkin.html",
            status="failed",
            title="Check-In Failed",
            reason=message,
            message=message,
        )

@class_bp.route("/class")
def class_list():
    token = session.get("token")

    if not token:
        return redirect("/signin")

    try:
        response = requests.get(
            f"{API_BASE}/class",
            headers={"Authorization": f"Bearer {token}"},
            timeout=20,
        )
        response.raise_for_status()
        classes = response.json()

    except requests.RequestException as e:
        print(f"Class API error: {e}")
        flash("Unable to load classes.", "danger")
        return render_template(
            "classes/class_list.html",
            next_week=[],
            current_week=[],
            current_month=[],
            last_month=[],
            older=[],
        )

    except ValueError:
        print("Invalid JSON returned from API")
        print(response.text)
        flash("Invalid response from server.", "danger")
        return render_template(
            "classes/class_list.html",
            next_week=[],
            current_week=[],
            current_month=[],
            last_month=[],
            older=[],
        )

    if isinstance(classes, dict):
        classes = classes.get("items", [])

    now = datetime.now()

    start_week = (now - timedelta(days=now.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    end_week = start_week + timedelta(days=7)

    start_next_week = end_week
    end_next_week = start_next_week + timedelta(days=7)

    start_month = now.replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    )

    if start_month.month == 1:
        start_last_month = start_month.replace(
            year=start_month.year - 1,
            month=12,
        )
    else:
        start_last_month = start_month.replace(
            month=start_month.month - 1,
        )

    next_week = []
    current_week = []
    current_month = []
    last_month = []
    older = []

    for cls in classes:
        class_dt = cls.get("class_datetime")
        if not class_dt:
            continue

        dt = datetime.fromisoformat(class_dt.replace("Z", "+00:00"))

        if dt.tzinfo:
            dt = dt.replace(tzinfo=None)

        cls["date_formatted_html"] = format_class_details(cls)["html"]

        # store parsed datetime so sorting is reliable
        cls["_dt"] = dt

        if start_next_week <= dt < end_next_week:
            next_week.append(cls)

        elif start_week <= dt < end_week:
            current_week.append(cls)

        elif start_month <= dt < start_week:
            current_month.append(cls)

        elif start_last_month <= dt < start_month:
            last_month.append(cls)

        else:
            older.append(cls)

    def sort_desc(bucket):
        return sorted(bucket, key=lambda x: x["_dt"], reverse=True)

    return render_template(
        "classes/class_list.html",
        today=datetime.now(timezone.utc).date() + timedelta(days=1),
        next_week=sort_desc(next_week),
        current_week=sort_desc(current_week),
        current_month=sort_desc(current_month),
        last_month=sort_desc(last_month),
        older=sort_desc(older),
    )

@class_bp.route("/class/create", methods=["GET", "POST"])
def class_create():
    token = session.get("token")

    if not token:
        return redirect("/signin")

    if request.method == "POST":

        class_date = request.form.get("class_date")
        class_time = request.form.get("class_time")

        try:
            class_datetime = datetime.strptime(
                f"{class_date} {class_time}",
                "%Y-%m-%d %H:%M"
            ).isoformat()
        except Exception:
            flash("Invalid date/time format", "danger")
            return redirect(url_for("class.class_create"))

        payload = {
            "name": request.form.get("name"),
            "description": request.form.get("description"),
            "class_datetime": class_datetime,
            "duration": int(request.form.get("duration") or 0),
            "promotion": int(request.form.get("promotion") or 0),
        }

        try:
            response = requests.post(
                f"{API_BASE}/class",
                json=payload,
                headers={"Authorization": f"Bearer {token}"},
                timeout=20,
            )

            if not response.ok:
                flash(f"Unable to create class: {response.text}", "danger")
                return redirect(url_for("class.class_create"))

            flash("Class created successfully.", "success")
            return redirect(url_for("class.class_list"))

        except requests.RequestException as e:
            flash(f"Request failed: {str(e)}", "danger")
            return redirect(url_for("class.class_create"))

    # ✅ THIS WAS MISSING (GET handler)
    return render_template("classes/class_create.html")