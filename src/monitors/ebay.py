from dataclasses import dataclass
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class EbayItem:
    item_id: str
    title: str
    url: str
    price: Decimal | None = None
    currency: str | None = None
    condition: str | None = None
    location: str | None = None
    image_url: str | None = None

    @property
    def searchable_text(self) -> str:
        """Text used by the PenWatch watchlist engine."""
        parts = [
            self.title,
            self.condition or "",
            self.location or "",
        ]
        return "\n".join(part for part in parts if part)


class EbayMonitor:
    """
    eBay data source for PenWatch.

    The live Browse API integration will be activated after
    eBay Developer production access has been granted.
    """

    SOURCE = "ebay"

    def __init__(self, marketplace: str = "EBAY_DE") -> None:
        self.marketplace = marketplace

    def search(self, query: str, limit: int = 50) -> list[EbayItem]:
        """
        Search eBay for current listings.

        Live API access is intentionally disabled until valid
        eBay Developer credentials are available.
        """
        raise RuntimeError(
            "eBay Browse API is not configured yet. "
            "Developer access is still pending."
        )

    @staticmethod
    def parse_item(data: dict[str, Any]) -> EbayItem:
        """
        Convert an eBay Browse API item summary into PenWatch's
        internal EbayItem representation.
        """
        price_data = data.get("price") or {}
        location_data = data.get("itemLocation") or {}
        image_data = data.get("image") or {}

        price_value = price_data.get("value")

        return EbayItem(
            item_id=str(data["itemId"]),
            title=data.get("title", ""),
            url=data.get("itemWebUrl", ""),
            price=Decimal(str(price_value)) if price_value is not None else None,
            currency=price_data.get("currency"),
            condition=data.get("condition"),
            location=location_data.get("country"),
            image_url=image_data.get("imageUrl"),
        )
