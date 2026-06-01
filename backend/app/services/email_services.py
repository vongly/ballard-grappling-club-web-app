import sys
from pathlib import Path

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

sys.path.append(str(Path(__file__).resolve().parents[2]))

from env import (
    FROM_EMAIL,
    FROM_EMAIL_APP_PASSWORD, 
    FORWARDING_EMAIL,
    FRONTEND_URL_PUBLIC,
    TEST_EMAIL,
)

TEST_EMAIL = bool(TEST_EMAIL)

def send_email_smtp(
    to_email: str,
    subject: str,
    body_html: str,
    from_email: str = FROM_EMAIL,
    from_email_app_password: str = FROM_EMAIL_APP_PASSWORD,
    reply_to_email: str = FORWARDING_EMAIL,
    test_email: bool = TEST_EMAIL,
):
    test_string = 'TEST EMAIL - ' if test_email else ''

    msg = MIMEMultipart()

    msg["From"] = "Ballard Grappling Club"
    msg["To"] = to_email
    msg["Subject"] = test_string + subject

    if reply_to_email:
        msg["Reply-To"] = reply_to_email
    else:
        msg["Reply-To"] = from_email

    msg.attach(MIMEText(body_html, "html"))

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()

        # ⚠️ login usually MUST match actual sending mailbox (Gmail requirement)
        server.login(from_email, from_email_app_password)

        server.send_message(msg)



from jinja2 import Environment, FileSystemLoader, select_autoescape
from datetime import datetime

env = Environment(
    loader=FileSystemLoader("backend/app/services/email_templates"),
    autoescape=select_autoescape(["html", "xml"])
)
def render_email(template_name: str, **context):
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
    send_email_smtp(
        to_email="vongly62@gmail.com",
        subject="Test Auto Email",
        body_html=html,
    )