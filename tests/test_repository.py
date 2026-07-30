"""Tests for db/repository.py's mark_seen and get_recent_matches, in both
fake (no Supabase configured) and real (mocked Supabase client) modes."""
import unittest
from unittest.mock import Mock, patch

from adapters.base import Listing
from db import repository


def _listing(site_item_id, title="Item", price=10.0, url="https://example.com/item"):
    return Listing(site="nellis", site_item_id=site_item_id, title=title, price=price, url=url, location="Mesa")


class RepositoryFakeModeTests(unittest.TestCase):
    """No Supabase client configured — exercises repository.py's in-memory fallback."""

    def setUp(self):
        patcher = patch("db.repository.get_client", return_value=None)
        patcher.start()
        self.addCleanup(patcher.stop)
        repository._fake_seen.clear()
        repository._fake_matches.clear()

    def test_mark_seen_records_full_listing_details(self):
        repository.mark_seen("fake-1", _listing("999", title="Fake Title", price=42.0, url="https://x/999"))

        self.assertIn("999", repository.get_seen_site_item_ids("fake-1"))
        match = repository._fake_matches[-1]
        self.assertEqual(match["title"], "Fake Title")
        self.assertEqual(match["price"], 42.0)
        self.assertEqual(match["url"], "https://x/999")
        self.assertEqual(match["watchlist_item_name"], "Dyson V15")

    def test_get_recent_matches_returns_newest_first(self):
        repository.mark_seen("fake-1", _listing("1", title="First"))
        repository.mark_seen("fake-1", _listing("2", title="Second"))

        matches = repository.get_recent_matches("irrelevant-in-fake-mode", limit=10)

        self.assertEqual([m["title"] for m in matches], ["Second", "First"])

    def test_get_recent_matches_respects_limit(self):
        for i in range(5):
            repository.mark_seen("fake-1", _listing(str(i)))

        matches = repository.get_recent_matches("irrelevant-in-fake-mode", limit=2)

        self.assertEqual(len(matches), 2)


class RepositorySupabaseModeTests(unittest.TestCase):
    """A Supabase client is configured — verifies the query/insert shape sent to it."""

    def test_mark_seen_inserts_title_price_and_url(self):
        mock_client = Mock()

        with patch("db.repository.get_client", return_value=mock_client):
            repository.mark_seen("w1", _listing("120", title="Some Shirt", price=8.0, url="https://x/120"))

        mock_client.table.assert_called_with("seen_items")
        payload = mock_client.table.return_value.insert.call_args[0][0]
        self.assertEqual(payload["watchlist_item_id"], "w1")
        self.assertEqual(payload["site_item_id"], "120")
        self.assertEqual(payload["title"], "Some Shirt")
        self.assertEqual(payload["price"], 8.0)
        self.assertEqual(payload["url"], "https://x/120")
        self.assertIn("first_seen_at", payload)

    def test_get_recent_matches_joins_and_filters_by_user_then_flattens(self):
        mock_client = Mock()
        execute = (
            mock_client.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute
        )
        execute.return_value = Mock(
            data=[
                {
                    "id": "s1",
                    "watchlist_item_id": "w1",
                    "site_item_id": "120",
                    "title": "Some Shirt",
                    "price": 8,
                    "url": "https://x/120",
                    "first_seen_at": "2026-07-29T00:00:00+00:00",
                    "watchlist_items": {"name": "Polo", "user_id": "u1"},
                }
            ]
        )

        with patch("db.repository.get_client", return_value=mock_client):
            matches = repository.get_recent_matches("u1", limit=10)

        mock_client.table.assert_called_with("seen_items")
        select = mock_client.table.return_value.select
        select.assert_called_with("*, watchlist_items!inner(name, user_id)")
        select.return_value.eq.assert_called_with("watchlist_items.user_id", "u1")
        select.return_value.eq.return_value.order.assert_called_with("first_seen_at", desc=True)
        select.return_value.eq.return_value.order.return_value.limit.assert_called_with(10)

        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["watchlist_item_name"], "Polo")
        self.assertNotIn("watchlist_items", matches[0])


if __name__ == "__main__":
    unittest.main()
