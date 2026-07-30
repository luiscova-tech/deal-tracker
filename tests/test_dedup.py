"""Tests for core/dedup.py."""
import unittest

from adapters.base import Listing
from core.dedup import filter_new


def _listing(site_item_id):
    return Listing(site="nellis", site_item_id=site_item_id, title="t", price=1.0, url="u")


class FilterNewTests(unittest.TestCase):
    def test_drops_already_seen_listings(self):
        listings = [_listing("1"), _listing("2"), _listing("3")]

        new = filter_new(listings, seen_site_item_ids={"2"})

        self.assertEqual([listing.site_item_id for listing in new], ["1", "3"])

    def test_empty_seen_set_returns_everything(self):
        listings = [_listing("1"), _listing("2")]

        new = filter_new(listings, seen_site_item_ids=set())

        self.assertEqual(len(new), 2)

    def test_all_seen_returns_empty(self):
        listings = [_listing("1"), _listing("2")]

        new = filter_new(listings, seen_site_item_ids={"1", "2"})

        self.assertEqual(new, [])


if __name__ == "__main__":
    unittest.main()
