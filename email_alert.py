import smtplib
from email.message import EmailMessage
import os

from config import (
    EMAIL_ENABLED,
    SENDER_EMAIL,
    SENDER_PASSWORD,
    RECIPIENTS_FILE,
    RAM_WARNING_LIMIT
)


def load_recipients():
    recipients = []

    if not os.path.exists(RECIPIENTS_FILE):
        return recipients

    with open(RECIPIENTS_FILE, "r") as file:
        for line in file:
            email = line.strip()

            if email:
                recipients.append(email)

    return recipients


def send_email_alert(data, dashboard_html, chart_images=None):

    if not EMAIL_ENABLED:
        return False

    recipients = load_recipients()

    if not recipients:
        return False

    subject = f"RAM Warning Alert: {data['ram_percent']}% Usage Detected"

    body = f"""
Server Resource Warning Alert

RAM usage has reached {data['ram_percent']}%.

Configured Warning Threshold: {RAM_WARNING_LIMIT}%

System Details:
Hostname: {data['hostname']}
IP Address: {data['ip_address']}
Operating System: {data['os']}

Resource Usage:
RAM Used: {data['ram_used_gb']} GB / {data['ram_total_gb']} GB
RAM Usage: {data['ram_percent']}%
CPU Usage: {data['cpu_percent']}%

Process Summary:
Total Processes: {data['total_processes']}
Running Processes: {data['running']}
Sleeping / Idle Processes: {data['sleeping']}

This is an automated alert from the Server Resource Monitor.
"""

    msg = EmailMessage()

    msg["From"] = SENDER_EMAIL
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject

    msg.set_content(body)
    msg.add_alternative(dashboard_html, subtype="html")

    if chart_images:
        html_part = msg.get_payload()[1]

        for cid, image_bytes in chart_images.items():
            html_part.add_related(
                image_bytes,
                maintype="image",
                subtype="png",
                cid=f"<{cid}>"
            )

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
            smtp.starttls()

            smtp.login(SENDER_EMAIL, SENDER_PASSWORD)

            smtp.send_message(msg)

        return True

    except Exception:
        return False