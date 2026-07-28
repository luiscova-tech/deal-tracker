from adapters.base import Adapter, Filters, Listing


class NellisAdapter(Adapter):
    site_name = "nellis"

    def fetch_listings(self, filters: Filters) -> list[Listing]:
        # TODO: Nellis Auction listings API/scrape goes here.
        #
        # Next step: inspect nellisauction.com's network traffic to find the
        # underlying listings endpoint (likely a JSON API) and how it accepts
        # keyword/location/price query params, then map its response into
        # Listing objects. Until then this adapter always returns no results.
        return []
