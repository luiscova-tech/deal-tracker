"""Common interface every site adapter implements."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Filters:
    """Search criteria derived from a watchlist item."""

    keyword: str
    location: Optional[str] = None
    price_ceiling: Optional[float] = None
    size: Optional[str] = None


@dataclass
class Listing:
    """A single item found on a site, normalized to a common shape."""

    site: str
    site_item_id: str
    title: str
    price: float
    url: str
    location: Optional[str] = None
    close_time: Optional[datetime] = None
    bid_count: Optional[int] = None
    next_bid: Optional[float] = None


class Adapter:
    """Base class for a site integration."""

    site_name: str

    def fetch_listings(self, filters: Filters) -> list[Listing]:
        """Return current listings on this site matching `filters`."""
        raise NotImplementedError
