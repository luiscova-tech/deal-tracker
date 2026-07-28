import requests

from notifications.base import Notifier


class NtfyNotifier(Notifier):
    """Sends push notifications via ntfy.sh. `target` is the ntfy topic name."""

    def __init__(self, base_url: str = "https://ntfy.sh"):
        self.base_url = base_url

    def send(self, message: str, target: str) -> None:
        requests.post(f"{self.base_url}/{target}", data=message.encode("utf-8"), timeout=10)
