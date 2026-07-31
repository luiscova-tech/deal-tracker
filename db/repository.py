"""
Data access layer sitting in front of Supabase (schema: db/schema.sql).

Every function falls back to simple in-memory fake data when no Supabase
client is configured (db/client.py returns None), so main.py can run
end-to-end before the database exists. Once Supabase is connected, these
fakes just stop being reachable — no other code needs to change.
"""
from datetime import datetime, timezone

from adapters.base import Listing
from db.client import get_client

_FAKE_WATCHLIST = [
    {
        "id": "fake-1",
        "name": "Dyson V15",
        "site": "nellis",
        "location": "mesa",
        "price_ceiling": 200.0,
        "size": None,
        "user_id": None,
        "ntfy_topic": None,
    },
    {
        "id": "fake-2",
        "name": "Steam Deck",
        "site": "nellis",
        "location": "both",
        "price_ceiling": 300.0,
        "size": None,
        "user_id": None,
        "ntfy_topic": None,
    },
]

_fake_seen: dict[str, set[str]] = {}
_fake_matches: list[dict] = []
_fake_reminders: list[dict] = []


def get_watchlist_items() -> list[dict]:
    """
    All watchlist items, each with its owning user's ntfy_topic attached
    under the "ntfy_topic" key, so main.py can route notifications
    per-user without a separate query per item.

    watchlist_items.user_id and profiles.id both reference auth.users
    independently (no direct FK between the two tables), so PostgREST
    can't auto-embed profiles onto watchlist_items — this does two
    queries and joins them in Python instead.

    Fake mode has no real user/profile concept, so fake items carry
    user_id=None, ntfy_topic=None — main.py treats a None user_id as
    "fall back to the shared NTFY_TOPIC env var for local testing."
    """
    client = get_client()
    if client is None:
        return _FAKE_WATCHLIST

    items = client.table("watchlist_items").select("*").execute().data
    profiles = client.table("profiles").select("id, ntfy_topic").execute().data
    ntfy_topic_by_user_id = {profile["id"]: profile["ntfy_topic"] for profile in profiles}

    for item in items:
        item["ntfy_topic"] = ntfy_topic_by_user_id.get(item["user_id"])
    return items


def get_watchlist_item(watchlist_item_id: str) -> dict | None:
    client = get_client()
    if client is None:
        return next((i for i in _FAKE_WATCHLIST if i["id"] == watchlist_item_id), None)
    result = client.table("watchlist_items").select("*").eq("id", watchlist_item_id).execute()
    return result.data[0] if result.data else None


def get_seen_site_item_ids(watchlist_item_id: str) -> set[str]:
    client = get_client()
    if client is None:
        return _fake_seen.get(watchlist_item_id, set())
    result = (
        client.table("seen_items")
        .select("site_item_id")
        .eq("watchlist_item_id", watchlist_item_id)
        .execute()
    )
    return {row["site_item_id"] for row in result.data}


def mark_seen(watchlist_item_id: str, listing: Listing) -> None:
    client = get_client()
    if client is None:
        _fake_seen.setdefault(watchlist_item_id, set()).add(listing.site_item_id)
        watchlist_item = get_watchlist_item(watchlist_item_id)
        _fake_matches.append(
            {
                "watchlist_item_id": watchlist_item_id,
                "watchlist_item_name": watchlist_item["name"] if watchlist_item else None,
                "site_item_id": listing.site_item_id,
                "title": listing.title,
                "price": listing.price,
                "url": listing.url,
                "first_seen_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        return
    client.table("seen_items").insert(
        {
            "watchlist_item_id": watchlist_item_id,
            "site_item_id": listing.site_item_id,
            "title": listing.title,
            "price": listing.price,
            "url": listing.url,
            "first_seen_at": datetime.now(timezone.utc).isoformat(),
        }
    ).execute()


def get_recent_matches(user_id: str, limit: int = 50) -> list[dict]:
    """
    Recent matches (seen_items) for `user_id`'s watchlist, newest first —
    what the dashboard's match-history view will call. Joins in the parent
    watchlist_item's name and flattens it to `watchlist_item_name`.

    Fake mode doesn't model multiple users, so `user_id` is ignored there.
    """
    client = get_client()
    if client is None:
        return list(reversed(_fake_matches))[:limit]

    result = (
        client.table("seen_items")
        .select("*, watchlist_items!inner(name, user_id)")
        .eq("watchlist_items.user_id", user_id)
        .order("first_seen_at", desc=True)
        .limit(limit)
        .execute()
    )
    return [_flatten_match(row) for row in result.data]


def _flatten_match(row: dict) -> dict:
    watchlist_item = row.pop("watchlist_items", {}) or {}
    row["watchlist_item_name"] = watchlist_item.get("name")
    return row


def get_unsent_reminders() -> list[dict]:
    client = get_client()
    if client is None:
        return [r for r in _fake_reminders if not r["sent"]]
    return client.table("bid_reminders").select("*").eq("sent", False).execute().data


def mark_reminder_sent(reminder_id: str) -> None:
    client = get_client()
    if client is None:
        for r in _fake_reminders:
            if r["id"] == reminder_id:
                r["sent"] = True
        return
    client.table("bid_reminders").update({"sent": True}).eq("id", reminder_id).execute()
