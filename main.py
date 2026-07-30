"""
Entry point for the scheduled check. Wires together:

    watchlist -> adapter.fetch_listings -> dedup -> matcher -> notifications

Run with `python main.py`. Until Supabase and the Nellis adapter are wired
up for real, this runs against fake in-memory data (db/repository.py) and
the nellis adapter always reports zero listings (adapters/nellis.py), so
you can watch the whole pipeline execute before either exists.
"""
import logging
import os

from dotenv import load_dotenv

load_dotenv()

from adapters.base import Filters
from adapters.nellis import NellisAdapter
from core.dedup import filter_new
from core.matcher import matches
from core.reminders import get_due_reminders
from db import repository
from notifications.email_notifier import EmailNotifier
from notifications.ntfy_notifier import NtfyNotifier

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("deal-tracker")

ADAPTERS = {
    "nellis": NellisAdapter(),
}


def build_notifiers() -> list[tuple]:
    """Only wire up channels that have their required config set."""
    notifiers = []
    if os.environ.get("SMTP_HOST") and os.environ.get("NOTIFY_EMAIL_TO"):
        notifiers.append((EmailNotifier(), os.environ["NOTIFY_EMAIL_TO"]))
    if os.environ.get("NTFY_TOPIC"):
        notifiers.append((NtfyNotifier(), os.environ["NTFY_TOPIC"]))
    return notifiers


def notify_all(notifiers: list[tuple], message: str) -> None:
    if not notifiers:
        log.info("No notification channels configured — would have sent: %s", message)
        return
    for notifier, target in notifiers:
        notifier.send(message, target)


def check_watchlist(notifiers: list[tuple]) -> None:
    for item in repository.get_watchlist_items():
        adapter = ADAPTERS.get(item["site"])
        if adapter is None:
            log.warning("No adapter for site %r (watchlist item %r)", item["site"], item["name"])
            continue

        filters = Filters(
            keyword=item["name"],
            location=item.get("location"),
            price_ceiling=item.get("price_ceiling"),
            size=item.get("size"),
        )
        listings = adapter.fetch_listings(filters)
        log.info("[%s] %r: fetched %d listing(s)", item["site"], item["name"], len(listings))

        seen_ids = repository.get_seen_site_item_ids(item["id"])
        for listing in filter_new(listings, seen_ids):
            repository.mark_seen(item["id"], listing)
            if matches(item, listing):
                notify_all(
                    notifiers,
                    f"New match for '{item['name']}': {listing.title} — ${listing.price} ({listing.url})",
                )


def check_reminders(notifiers: list[tuple]) -> None:
    reminders = repository.get_unsent_reminders()
    for reminder in get_due_reminders(reminders):
        item = repository.get_watchlist_item(reminder["watchlist_item_id"])
        name = item["name"] if item else reminder["watchlist_item_id"]
        notify_all(notifiers, f"Reminder: check on your bid for '{name}'")
        repository.mark_reminder_sent(reminder["id"])


def main():
    notifiers = build_notifiers()
    check_watchlist(notifiers)
    check_reminders(notifiers)


if __name__ == "__main__":
    main()
