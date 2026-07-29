"""Nellis Auction adapter.

Hits Nellis's own search endpoint directly (confirmed via DevTools — no
login required): GET /search?query=<kw>&_data=routes/search returns JSON
with a `products` list.

Results are scoped by a "shopping location" cookie; without it, Nellis
defaults to Las Vegas and returns no Mesa/Phoenix listings at all, so a
missing cookie is treated as a hard stop rather than silently querying the
wrong region.
"""
import logging
import os
import re
from datetime import datetime

import requests

from adapters.base import Adapter, Filters, Listing

log = logging.getLogger(__name__)

SEARCH_URL = "https://www.nellisauction.com/search"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
REQUEST_TIMEOUT = 10


def _slugify(title: str, max_len: int = 60) -> str:
    """Product URLs embed a slug, but Nellis's router only actually looks up
    the trailing id — any slug resolves, so this just needs to look reasonable.
    Real titles run long, so trim to a word boundary rather than repeating the
    whole (often 150+ char) title in every notification and log line."""
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", title).strip("-").lower()
    if len(slug) > max_len:
        slug = slug[:max_len].rsplit("-", 1)[0]
    return slug or "item"


def _parse_close_time(product: dict) -> datetime | None:
    value = (product.get("closeTime") or {}).get("value")
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _to_listing(product: dict) -> Listing:
    item_id = product["id"]
    return Listing(
        site="nellis",
        site_item_id=str(item_id),
        title=product["title"],
        price=product["currentPrice"],
        url=f"https://www.nellisauction.com/p/{_slugify(product['title'])}/{item_id}",
        location=(product.get("location") or {}).get("name"),
        close_time=_parse_close_time(product),
        bid_count=product.get("bidCount"),
        next_bid=(product.get("userState") or {}).get("nextBid"),
    )


class NellisAdapter(Adapter):
    site_name = "nellis"

    def fetch_listings(self, filters: Filters) -> list[Listing]:
        cookie_value = os.environ.get("NELLIS_SHOPPING_LOCATION_COOKIE", "").strip()
        cookie_value = cookie_value.removeprefix("__shopping-location=")
        if not cookie_value:
            log.warning(
                "NELLIS_SHOPPING_LOCATION_COOKIE is not set — skipping Nellis "
                "(without it, results default to Las Vegas, not Mesa/Phoenix)"
            )
            return []

        headers = {
            "User-Agent": USER_AGENT,
            "Cookie": f"__shopping-location={cookie_value}",
        }
        params = {"query": filters.keyword, "_data": "routes/search"}

        try:
            response = requests.get(SEARCH_URL, params=params, headers=headers, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            products = response.json().get("products", [])
        except (requests.RequestException, ValueError) as e:
            log.warning("Nellis search request failed for %r: %s", filters.keyword, e)
            return []

        listings = []
        for product in products:
            if product.get("isClosed") or product.get("marketStatus") != "open":
                continue

            location_name = (product.get("location") or {}).get("name") or ""
            if filters.location and filters.location.lower() != "both":
                if location_name.lower() != filters.location.lower():
                    continue

            try:
                listings.append(_to_listing(product))
            except (KeyError, TypeError, AttributeError) as e:
                log.warning("Skipping unparseable Nellis product %r: %s", product.get("id"), e)

        return listings
