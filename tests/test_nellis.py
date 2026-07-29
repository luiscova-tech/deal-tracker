"""Tests for the Nellis adapter. All network calls are mocked — nothing here
hits the real site, so this is safe to run in CI."""
import unittest
from unittest.mock import Mock, patch

import requests

from adapters.base import Filters
from adapters.nellis import NellisAdapter

# Shaped after the real (trimmed) response confirmed via DevTools + a live check
# of the full field list, plus two extra products to exercise filtering.
FAKE_RESPONSE = {
    "products": [
        {
            "id": 120181369,
            "title": "Lacoste Men's Classic Fit L.12.12 Original Piqué Polo Shirt, Black, Small",
            "currentPrice": 8,
            "retailPrice": 88.62,
            "bidCount": 6,
            "isClosed": False,
            "marketStatus": "open",
            "closeTime": {"__type": "Date", "value": "2026-07-29T01:09:00.000Z"},
            "location": {"name": "Mesa"},
            "userState": {"nextBid": 9, "isAllowedToBid": True},
        },
        {
            "id": 2,
            "title": "Closed Item",
            "currentPrice": 5,
            "bidCount": 1,
            "isClosed": True,
            "marketStatus": "closed",
            "closeTime": {"__type": "Date", "value": "2026-07-20T01:09:00.000Z"},
            "location": {"name": "Mesa"},
        },
        {
            "id": 3,
            "title": "Wrong Warehouse Item",
            "currentPrice": 5,
            "bidCount": 1,
            "isClosed": False,
            "marketStatus": "open",
            "closeTime": {"__type": "Date", "value": "2026-07-30T01:09:00.000Z"},
            "location": {"name": "Las Vegas"},
        },
    ]
}


def _mock_response(payload):
    return Mock(json=Mock(return_value=payload), raise_for_status=Mock())


class NellisAdapterTests(unittest.TestCase):
    @patch("adapters.nellis.requests.get")
    @patch.dict("os.environ", {"NELLIS_SHOPPING_LOCATION_COOKIE": "fake-cookie-value"})
    def test_filters_closed_and_wrong_location_then_maps_fields(self, mock_get):
        mock_get.return_value = _mock_response(FAKE_RESPONSE)

        listings = NellisAdapter().fetch_listings(Filters(keyword="polo", location="mesa"))

        self.assertEqual(len(listings), 1)
        listing = listings[0]
        self.assertEqual(listing.site_item_id, "120181369")
        self.assertEqual(listing.price, 8)
        self.assertEqual(listing.location, "Mesa")
        self.assertEqual(listing.bid_count, 6)
        self.assertEqual(listing.next_bid, 9)
        self.assertEqual(listing.close_time.year, 2026)
        self.assertTrue(listing.url.endswith("/120181369"))

    @patch("adapters.nellis.requests.get")
    @patch.dict("os.environ", {"NELLIS_SHOPPING_LOCATION_COOKIE": "fake-cookie-value"})
    def test_location_both_returns_all_open_listings_regardless_of_warehouse(self, mock_get):
        mock_get.return_value = _mock_response(FAKE_RESPONSE)

        listings = NellisAdapter().fetch_listings(Filters(keyword="polo", location="both"))

        self.assertEqual({listing.site_item_id for listing in listings}, {"120181369", "3"})

    @patch("adapters.nellis.requests.get")
    @patch.dict("os.environ", {"NELLIS_SHOPPING_LOCATION_COOKIE": ""})
    def test_missing_cookie_skips_request_and_returns_empty(self, mock_get):
        listings = NellisAdapter().fetch_listings(Filters(keyword="polo"))

        self.assertEqual(listings, [])
        mock_get.assert_not_called()

    @patch("adapters.nellis.requests.get")
    @patch.dict("os.environ", {"NELLIS_SHOPPING_LOCATION_COOKIE": "fake-cookie-value"})
    def test_request_exception_returns_empty_instead_of_raising(self, mock_get):
        mock_get.side_effect = requests.ConnectionError("boom")

        listings = NellisAdapter().fetch_listings(Filters(keyword="polo"))

        self.assertEqual(listings, [])

    @patch("adapters.nellis.requests.get")
    @patch.dict("os.environ", {"NELLIS_SHOPPING_LOCATION_COOKIE": "fake-cookie-value"})
    def test_malformed_product_is_skipped_not_fatal(self, mock_get):
        mock_get.return_value = _mock_response(
            {"products": [{"id": 4, "isClosed": False, "marketStatus": "open", "location": {"name": "Mesa"}}]}
        )

        listings = NellisAdapter().fetch_listings(Filters(keyword="polo", location="mesa"))

        self.assertEqual(listings, [])


if __name__ == "__main__":
    unittest.main()
