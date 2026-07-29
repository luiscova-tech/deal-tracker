"""Matching a listing against a watchlist item's criteria."""
from adapters.base import Listing


def matches(watchlist_item: dict, listing: Listing) -> bool:
    """
    True if `listing` satisfies the watchlist item's keyword/location/price criteria.

    `watchlist_item` is a plain dict shaped like the watchlist_items table
    (see db/schema.sql): name, location, price_ceiling, size.
    """
    keyword = watchlist_item["name"].lower()
    if keyword not in listing.title.lower():
        return False

    # Site location names (e.g. Nellis's "Mesa") aren't guaranteed to match
    # the watchlist's casing convention (e.g. "mesa"), so compare lowercase.
    location = watchlist_item.get("location")
    if location and location.lower() != "both" and listing.location and listing.location.lower() != location.lower():
        return False

    price_ceiling = watchlist_item.get("price_ceiling")
    if price_ceiling is not None and listing.price > price_ceiling:
        return False

    # `size` isn't used yet — reserved for future adapters that expose it.

    return True
