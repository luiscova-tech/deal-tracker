"""Tests for main.py's per-user notification routing in check_watchlist()."""
import unittest
from unittest.mock import Mock, patch

from adapters.base import Listing
from db import repository
import main


def _listing(site_item_id, title="Widget Deal", price=10.0):
    return Listing(
        site="nellis",
        site_item_id=site_item_id,
        title=title,
        price=price,
        url=f"https://example.com/{site_item_id}",
    )


def _item(item_id, user_id, ntfy_topic, name="Widget"):
    return {
        "id": item_id,
        "user_id": user_id,
        "ntfy_topic": ntfy_topic,
        "name": name,
        "site": "nellis",
        "location": None,
        "price_ceiling": None,
        "size": None,
    }


class CheckWatchlistNotificationRoutingTests(unittest.TestCase):
    def setUp(self):
        # Deterministic regardless of the developer's real .env.
        env_patcher = patch.dict(
            "os.environ", {"SMTP_HOST": "", "NOTIFY_EMAIL_TO": ""}
        )
        env_patcher.start()
        self.addCleanup(env_patcher.stop)

        seen_patcher = patch.object(repository, "get_seen_site_item_ids", return_value=set())
        seen_patcher.start()
        self.addCleanup(seen_patcher.stop)

        mark_seen_patcher = patch.object(repository, "mark_seen")
        mark_seen_patcher.start()
        self.addCleanup(mark_seen_patcher.stop)

    @patch("main.NtfyNotifier")
    def test_user_with_ntfy_topic_receives_notification(self, mock_ntfy_cls):
        mock_notifier = Mock()
        mock_ntfy_cls.return_value = mock_notifier

        item = _item("w1", user_id="user-a", ntfy_topic="topic-a")
        mock_adapter = Mock()
        mock_adapter.fetch_listings.return_value = [_listing("1", title="Widget Deal One")]

        with patch.object(repository, "get_watchlist_items", return_value=[item]), \
                patch.dict(main.ADAPTERS, {"nellis": mock_adapter}, clear=True):
            main.check_watchlist()

        mock_notifier.send.assert_called_once()
        message, target = mock_notifier.send.call_args[0]
        self.assertEqual(target, "topic-a")
        self.assertIn("Widget Deal One", message)

    @patch("main.NtfyNotifier")
    def test_user_without_ntfy_topic_skips_without_error(self, mock_ntfy_cls):
        mock_notifier = Mock()
        mock_ntfy_cls.return_value = mock_notifier

        item = _item("w2", user_id="user-b", ntfy_topic=None)
        mock_adapter = Mock()
        mock_adapter.fetch_listings.return_value = [_listing("2", title="Widget Deal Two")]

        with patch.object(repository, "get_watchlist_items", return_value=[item]), \
                patch.dict(main.ADAPTERS, {"nellis": mock_adapter}, clear=True), \
                self.assertLogs("deal-tracker", level="INFO") as logs:
            main.check_watchlist()

        mock_notifier.send.assert_not_called()
        self.assertTrue(any("skipping" in message.lower() for message in logs.output))

    @patch.dict("os.environ", {"NTFY_TOPIC": "dev-fallback-topic"})
    @patch("main.NtfyNotifier")
    def test_fake_mode_falls_back_to_global_ntfy_topic(self, mock_ntfy_cls):
        mock_notifier = Mock()
        mock_ntfy_cls.return_value = mock_notifier

        # Fake mode: no real user/profile context at all (user_id is None).
        item = _item("fake-1", user_id=None, ntfy_topic=None)
        mock_adapter = Mock()
        mock_adapter.fetch_listings.return_value = [_listing("3", title="Widget Deal Three")]

        with patch.object(repository, "get_watchlist_items", return_value=[item]), \
                patch.dict(main.ADAPTERS, {"nellis": mock_adapter}, clear=True):
            main.check_watchlist()

        mock_notifier.send.assert_called_once()
        message, target = mock_notifier.send.call_args[0]
        self.assertEqual(target, "dev-fallback-topic")
        self.assertIn("Widget Deal Three", message)


if __name__ == "__main__":
    unittest.main()
