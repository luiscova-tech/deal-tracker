import os
import smtplib
from email.mime.text import MIMEText

from notifications.base import Notifier


class EmailNotifier(Notifier):
    """Sends notifications via SMTP. `target` is the recipient email address."""

    def __init__(self):
        self.host = os.environ["SMTP_HOST"]
        self.port = int(os.environ.get("SMTP_PORT", 587))
        self.username = os.environ["SMTP_USERNAME"]
        self.password = os.environ["SMTP_PASSWORD"]

    def send(self, message: str, target: str) -> None:
        msg = MIMEText(message)
        msg["Subject"] = "Deal Tracker Alert"
        msg["From"] = self.username
        msg["To"] = target

        with smtplib.SMTP(self.host, self.port) as server:
            server.starttls()
            server.login(self.username, self.password)
            server.send_message(msg)
