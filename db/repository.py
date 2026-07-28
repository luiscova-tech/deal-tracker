"""
Data access layer sitting in front of Supabase (schema: db/schema.sql).

Every function falls back to simple in-memory fake data when no Supabase
client is configured (db/client.py returns None), so main.py can run
end-to-end before the database exists. Once Supabase is connected, these
fakes just stop being reachable — no other code needs to change.
"""
from datetime import datetime, timezone

from db.client import get_client

_FAKE_WATCHLIST = [
    {
        "id": "fake-1",
        "name": "Dyson V15",
        "site": "nellis",
        "location": "mesa",
        "price_ceiling": 200.0,
        "size": None,
    },
    {
        "id": "fake-2",
        "name": "Steam Deck",
        "site": "nellis",
        "location": "both",
        "price_ceiling": 300.0,
        "size": None,
    },
]

_fake_seen: dict[str, set[str]] = {}
_fake_reminders: list[dict] = []


def get_watchlist_items() -> list[dict]:
    client = get_client()
    if client is None:
        return _FAKE_WATCHLIST
    return client.table("watchlist_items").select("*").execute().data


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


def mark_seen(watchlist_item_id: str, site_item_id: str) -> None:
    client = get_client()
    if client is None:
        _fake_seen.setdefault(watchlist_item_id, set()).add(site_item_id)
        return
    client.table("seen_items").insert(
        {
            "watchlist_item_id": watchlist_item_id,
            "site_item_id": site_item_id,
            "first_seen_at": datetime.now(timezone.utc).isoformat(),
        }
    ).execute()


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
