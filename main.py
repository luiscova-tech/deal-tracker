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
from collections import defaultdict

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


def build_email_target() -> tuple[EmailNotifier, str] | None:
    """
    Email stays global for now (per request — nobody has SMTP configured
    yet in practice, so this path is unused either way). Per-user email is
    a follow-up: it'd need to read the target address off each watchlist
    item's owning user the same way ntfy_topic does below, plus a real
    per-user email column (profiles only has ntfy_topic today).
    """
    if os.environ.get("SMTP_HOST") and os.environ.get("NOTIFY_EMAIL_TO"):
        return EmailNotifier(), os.environ["NOTIFY_EMAIL_TO"]
    return None


def resolve_ntfy_topic(user_id: str | None, item: dict) -> str | None:
    """
    Real watchlist items carry their owning user's ntfy_topic (joined in
    db/repository.py's get_watchlist_items()). Fake/no-Supabase mode has
    no real user at all (user_id is None), so it falls back to the shared
    NTFY_TOPIC env var used for local dev testing.
    """
    if user_id is None:
        return os.environ.get("NTFY_TOPIC")
    return item.get("ntfy_topic")


def build_notifiers() -> list[tuple]:
    """
    Global notifiers, used only by check_reminders() below.

    TODO: bid_reminders has the same "global broadcast" problem
    check_watchlist() used to have — a reminder belongs to one watchlist
    item, which belongs to one user, but this still fires to whatever's
    configured in NTFY_TOPIC/SMTP_* for everyone. Not fixed here since
    nothing creates reminders yet (bid_reminders is empty in practice) —
    flagging it rather than leaving it silently wrong.
    """
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


def check_watchlist() -> None:
    email_target = build_email_target()
    ntfy_notifier = NtfyNotifier()

    messages_by_user: dict[str | None, list[str]] = defaultdict(list)
    ntfy_topic_by_user: dict[str | None, str | None] = {}

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
                message = (
                    f"New match for '{item['name']}': {listing.title} "
                    f"— ${listing.price} ({listing.url})"
                )

                if email_target:
                    notifier, target = email_target
                    notifier.send(message, target)

                user_id = item.get("user_id")
                messages_by_user[user_id].append(message)
                ntfy_topic_by_user[user_id] = resolve_ntfy_topic(user_id, item)

    for user_id, messages in messages_by_user.items():
        ntfy_topic = ntfy_topic_by_user[user_id]
        if not ntfy_topic:
            log.info(
                "No ntfy_topic for user %s — skipping %d match notification(s)",
                user_id,
                len(messages),
            )
            continue
        for message in messages:
            ntfy_notifier.send(message, ntfy_topic)


def check_reminders(notifiers: list[tuple]) -> None:
    reminders = repository.get_unsent_reminders()
    for reminder in get_due_reminders(reminders):
        item = repository.get_watchlist_item(reminder["watchlist_item_id"])
        name = item["name"] if item else reminder["watchlist_item_id"]
        notify_all(notifiers, f"Reminder: check on your bid for '{name}'")
        repository.mark_reminder_sent(reminder["id"])


def main():
    check_watchlist()
    notifiers = build_notifiers()
    check_reminders(notifiers)


if __name__ == "__main__":
    main()
