"""Common interface every notification channel implements."""


class Notifier:
    def send(self, message: str, target: str) -> None:
        """Deliver `message` to `target` (channel-specific: email address, ntfy topic, ...)."""
        raise NotImplementedError
