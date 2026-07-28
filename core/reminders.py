"""Working out which bid reminders are due to fire."""
from datetime import datetime, timezone


def get_due_reminders(reminders: list[dict], now: datetime | None = None) -> list[dict]:
    """
    Return the unsent reminders whose remind_at has passed.

    `reminders` is a list of plain dicts shaped like the bid_reminders table
    (see db/schema.sql): watchlist_item_id, remind_at, sent.
    """
    now = now or datetime.now(timezone.utc)
    return [r for r in reminders if not r["sent"] and r["remind_at"] <= now]
