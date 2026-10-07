import os
import time
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

import requests


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
        parts = [
            self.title,
            self.condition or "",
            self.location or "",
        ]
        return "\n".join(
            part for part in parts if part
        )


class EbayMonitor:
    SOURCE = "ebay"

    TOKEN_URL = (
        "https://api.ebay.com/"
        "identity/v1/oauth2/token"
    )

    SEARCH_URL = (
        "https://api.ebay.com/"
        "buy/browse/v1/item_summary/search"
    )

    SCOPE = "https://api.ebay.com/oauth/api_scope"
    TIMEOUT = 20

    def __init__(
        self,
        marketplace: str | None = None,
    ) -> None:
        self.client_id = os.environ.get(
            "EBAY_CLIENT_ID",
            "",
        )
        self.client_secret = os.environ.get(
            "EBAY_CLIENT_SECRET",
            "",
        )
        self.marketplace = (
            marketplace
            or os.environ.get(
                "EBAY_MARKETPLACE_ID",
                "EBAY_DE",
            )
        )

        if not self.client_id:
            raise RuntimeError(
                "EBAY_CLIENT_ID is not configured"
            )

        if not self.client_secret:
            raise RuntimeError(
                "EBAY_CLIENT_SECRET is not configured"
            )

        self._access_token = None
        self._access_token_expires_at = 0.0

    def _get_access_token(self) -> str:
        now = time.monotonic()

        if (
            self._access_token
            and now < self._access_token_expires_at
        ):
            return self._access_token

        response = requests.post(
            self.TOKEN_URL,
            auth=(
                self.client_id,
                self.client_secret,
            ),
            headers={
                "Content-Type":
                    "application/x-www-form-urlencoded",
            },
            data={
                "grant_type": "client_credentials",
                "scope": self.SCOPE,
            },
            timeout=self.TIMEOUT,
        )

        response.raise_for_status()

        data = response.json()

        access_token = data.get("access_token")

        if not access_token:
            raise RuntimeError(
                "eBay OAuth response did not contain "
                "an access token"
            )

        try:
            expires_in = int(data.get("expires_in", 7200))
        except (TypeError, ValueError):
            expires_in = 7200

        # Renew five minutes before the token actually expires.
        cache_seconds = max(0, expires_in - 300)

        self._access_token = access_token
        self._access_token_expires_at = (
            time.monotonic() + cache_seconds
        )

        return access_token

    def search(
        self,
        query: str,
        limit: int = 50,
    ) -> list[EbayItem]:
        if not query.strip():
            return []

        if limit < 1 or limit > 200:
            raise ValueError(
                "eBay search limit must be between 1 and 200"
            )

        access_token = self._get_access_token()

        response = requests.get(
            self.SEARCH_URL,
            headers={
                "Authorization":
                    f"Bearer {access_token}",
                "X-EBAY-C-MARKETPLACE-ID":
                    self.marketplace,
            },
            params={
                "q": query,
                "limit": str(limit),
                "filter": "itemLocationRegion:WORLDWIDE",
            },
            timeout=self.TIMEOUT,
        )

        response.raise_for_status()

        data = response.json()

        return [
            self.parse_item(item)
            for item in data.get(
                "itemSummaries",
                [],
            )
            if item.get("itemId")
        ]

    @staticmethod
    def parse_item(
        data: dict[str, Any],
    ) -> EbayItem:
        price_data = data.get("price") or {}
        location_data = (
            data.get("itemLocation") or {}
        )
        image_data = data.get("image") or {}

        price_value = price_data.get("value")

        return EbayItem(
            item_id=str(data["itemId"]),
            title=data.get("title", ""),
            url=data.get("itemWebUrl", ""),
            price=(
                Decimal(str(price_value))
                if price_value is not None
                else None
            ),
            currency=price_data.get("currency"),
            condition=data.get("condition"),
            location=location_data.get("country"),
            image_url=image_data.get("imageUrl"),
        )
