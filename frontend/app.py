import os
import sys
from pathlib import Path
import requests

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    make_response,
    flash,
    session,
    send_file,
    abort,
    Response,
    Request,
)

from routes.api.register import register_bp
from routes.api.dashboard import dashboard_bp
from routes.api.stripe import stripe_ui_bp
from routes.api.class_ import class_bp

from utils.qr_codes import create_qr_code

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

sys.path.append(str(Path(__file__).resolve().parents[2]))

from utils.helpers import format_class_details
from env import API_BASE, SECRET_KEY


def api_get(path):
    try:
        res = requests.get(
            f"{API_BASE}{path}",
            timeout=10,
        )

        if res.status_code == 401:
            return "UNAUTHORIZED"

        if res.status_code != 200:
            return None

        return res.json()

    except requests.RequestException:
        return None

def require_auth():
    token = session.get("token")
    if not token:
        return redirect(url_for("signin"))
    return None

def redirect_if_authenticated():
    if session.get("token"):
        return redirect(url_for("dashboard.dashboard"))
    return None

app = Flask(__name__)
app.secret_key = SECRET_KEY

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/comingsoon")
def comingsoon():
    return render_template("comingsoon.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/price")
def price():
    products = api_get("/products") or []

    active_products = sorted(
        [p for p in products if p.get("active") == 1],
        key=lambda p: p.get("product_order"),
    )

    return render_template("price.html", products=active_products)

@app.route("/schedule")
def schedule():
    return render_template("schedule.html")

@app.route("/faq")
def faq():
    return render_template("faq.html")

@app.route("/signout")
def signout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/signin", methods=["GET", "POST"])
def signin():

    next = request.args.get("next")
    prompt = request.args.get("prompt")

    redirect_response = redirect_if_authenticated()
    if redirect_response:
        return redirect_response

    if request.method == "GET":
        return render_template("signin.html", next=next, prompt=prompt)

    email = request.form.get("email")
    password = request.form.get("password")
    next_url = request.form.get("next")

    res = requests.post(f"{API_BASE}/auth", json={"email": email, "password": password})

    if res.status_code != 200:
        flash("Invalid login")
        return redirect(url_for("signin", next=next_url))

    session["token"] = res.json().get("access_token")

    if next_url and next_url.startswith("/"):
        return redirect(next_url)

    return redirect(url_for("dashboard.dashboard"))


app.register_blueprint(register_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(stripe_ui_bp)
app.register_blueprint(class_bp)


@app.route("/qr")
def qr():
    url = request.args.get("url")

    if not url:
        abort(400, "Missing ?url=")

    svg = create_qr_code(url=url)

    return render_template("qr.html", svg=svg)


@app.route("/qr/class/<int:class_id>")
def qr_class(class_id: int):
    # Fetch class data
    try:
        response = requests.get(
            f"{API_BASE}/class/{class_id}",
            timeout=5,
        )
        response.raise_for_status()
    except requests.RequestException:
        abort(502, "Failed to fetch class data")

    data = response.json()

    class_details = "Scan to Check into:<br>" + format_class_details(data)["html"]

    url = f"{request.host_url}class/{class_id}/checkin"

    svg = create_qr_code(url=url)

    return render_template(
        "qr.html",
        svg=svg,
        class_details=class_details,
        class_id=class_id,
        url=url,
    )

# Static endpints -> logos, photos....

@app.route("/logo/main_compass_svg")
def logo_compass():
    return send_file(
        os.path.join(
            BASE_DIR,
            "static/images/logo/logo_main_compass.svg"
        ),
        mimetype="image/svg+xml"
    )

@app.route("/logo/main_compass_clear_svg")
def logo_compass_clear():
    return send_file(
        os.path.join(
            BASE_DIR,
            "static/images/logo/logo_main_compass_clear.svg"
        ),
        mimetype="image/svg+xml"
    )

print(app.url_map)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True, use_reloader=False)