from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


@dataclass
class InterpensItem:
    item_id: str
    title: str
    url: str
    price: Optional[Decimal] = None
    currency: str = "EUR"
    image_url: Optional[str] = None

    @property
    def searchable_text(self) -> str:
        return self.title


class InterpensMonitor:
    SOURCE = "interpens"
    BASE_URL = "https://interpens.shop/"
    NEW_PRODUCTS_URL = urljoin(BASE_URL, "en/new-products")

    def __init__(self, timeout: int = 20) -> None:
        self.timeout = timeout

    @staticmethod
    def _parse_price(value: str | None) -> Optional[Decimal]:
        if not value:
            return None

        cleaned = (
            value.replace("€", "")
            .replace("EUR", "")
            .replace("\xa0", "")
            .replace(" ", "")
            .strip()
        )

        # Interpens currently uses e.g. €495.00
        try:
            return Decimal(cleaned)
        except InvalidOperation:
            return None

    def fetch(self) -> list[InterpensItem]:
        response = requests.get(
            self.NEW_PRODUCTS_URL,
            headers={
                "User-Agent": (
                    "PenWatch/1.0 "
                    "(personal non-commercial collector monitor)"
                )
            },
            timeout=self.timeout,
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        items: list[InterpensItem] = []

        for article in soup.select(
            "article.product-miniature[data-id-product]"
        ):
            item_id = article.get("data-id-product")

            if not item_id:
                continue

            link = article.select_one("a.product-thumbnail")

            if not link or not link.get("href"):
                continue

            url = urljoin(
                self.BASE_URL,
                link.get("href"),
            )

            image = link.find("img")

            title = None
            image_url = None

            if image:
                title = image.get("alt")

                image_src = (
                    image.get("data-full-size-image-url")
                    or image.get("src")
                )

                if image_src:
                    image_url = urljoin(
                        self.BASE_URL,
                        image_src,
                    )

            # Fallback if image alt is unavailable
            if not title:
                title_node = article.select_one(
                    ".product-title a"
                )

                if title_node:
                    title = title_node.get_text(
                        " ",
                        strip=True,
                    )

            if not title:
                continue

            price_node = article.select_one(
                "span.price"
            )

            price = self._parse_price(
                price_node.get_text(" ", strip=True)
                if price_node
                else None
            )

            items.append(
                InterpensItem(
                    item_id=str(item_id),
                    title=title.strip(),
                    url=url,
                    price=price,
                    image_url=image_url,
                )
            )

        return items
