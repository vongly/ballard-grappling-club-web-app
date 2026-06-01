from datetime import datetime
from zoneinfo import ZoneInfo

def format_class_details(class_details: dict):
    dt = datetime.fromisoformat(class_details["class_datetime"].replace("Z", "+00:00"))
    dt = dt.astimezone(ZoneInfo("America/Los_Angeles"))

    html_str = (
        f"{class_details["name"]}<br>"
        f"{dt.strftime("%A %-I:%M %p")}<br>"
        f"{dt.strftime("%B %-d, %Y")}<br>"
        f"({class_details["duration"]} min)"
    )

    str = (
        f"{class_details["name"]}"
        f"{dt.strftime("%A %-I:%M %p")}"
        f"{dt.strftime("%B %-d, %Y")}"
        f"({class_details["duration"]} min)"
    )
    return {
        "string": str,
        "html": html_str,
    }