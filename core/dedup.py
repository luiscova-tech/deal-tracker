"""Filtering out listings we've already notified on."""
from adapters.base import Listing


def filter_new(listings: list[Listing], seen_site_item_ids: set[str]) -> list[Listing]:
    """Return only the listings whose site_item_id isn't in `seen_site_item_ids`."""
    return [listing for listing in listings if listing.site_item_id not in seen_site_item_ids]
