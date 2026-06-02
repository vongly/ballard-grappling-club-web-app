import sys

import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from pathlib import Path

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

from jinja2 import Environment, FileSystemLoader, select_autoescape

sys.path.append(str(Path(__file__).resolve().parents[2]))

from env import (
    FORWARDING_EMAIL,
    FRONTEND_URL_PUBLIC,
    TEST_EMAIL,
)

TEST_EMAIL = int(TEST_EMAIL)

from jinja2 import Environment, FileSystemLoader, select_autoescape
from datetime import datetime

TEMPLATE_DIR = Path(__file__).resolve().parent / "email_templates"

env = Environment(
    loader=FileSystemLoader(str(TEMPLATE_DIR)),
    autoescape=select_autoescape(["html", "xml"])
)

TEMPLATE_DIR = Path(__file__).resolve().parent / "email_templates"

env = Environment(
    loader=FileSystemLoader(str(TEMPLATE_DIR)),
    autoescape=select_autoescape(["html", "xml"])
)

# ----------------------------
# Gmail API setup
# ----------------------------
BASE_DIR = Path(__file__).resolve().parent
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


def get_gmail_service():
    creds = Credentials.from_authorized_user_file(
        str(BASE_DIR / "token.json"),
        SCOPES
    )
    return build("gmail", "v1", credentials=creds)


# ----------------------------
# EMAIL SEND (REPLACEMENT FOR SMTP)
# ----------------------------
def send_email(
    to_email: str,
    subject: str,
    body_html: str,
    reply_to_email: str = FORWARDING_EMAIL,
    test_email: int = TEST_EMAIL,
):
    # keep your test flag behavior
    subject = f"TEST EMAIL - {subject}" if test_email == 1 else subject

    msg = MIMEMultipart()
    msg["To"] = to_email
    msg["Subject"] = subject
    msg["From"] = f"Ballard Grappling Club <{FORWARDING_EMAIL}>"
    msg["Reply-To"] = reply_to_email

    msg.attach(MIMEText(body_html, "html"))

    # ---- Gmail API send ----
    service = get_gmail_service()

    raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode()

    service.users().messages().send(
        userId="me",
        body={"raw": raw_message}
    ).execute()


# ----------------------------
# TEMPLATE RENDERING (unchanged)
# ----------------------------
def render_email(template_name: str, frontend_url:str = FRONTEND_URL_PUBLIC, **context):
    context["frontend_url"] = FRONTEND_URL_PUBLIC

    template = env.get_template(template_name)

    return template.render(
        year=datetime.now().year,
        **context
    )


if __name__ == "__main__":
    html = render_email(
        "welcome.html",
        name="Vong",
        title="Welcome!",
        frontend_url=FRONTEND_URL_PUBLIC,
    )
    send_email(
        to_email="vongly62@gmail.com",
        subject="Test Auto Email",
        body_html=html,
    )