
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from urllib.parse import urljoin
import re
import time

import requests
from bs4 import BeautifulSoup


@dataclass
class PeytonStreetPensItem:
    item_id: str
    title: str
    url: str
    price: Decimal | None = None
    currency: str = "USD"
    sku: str | None = None
    image_url: str | None = None
    available: bool | None = None

    @property
    def searchable_text(self) -> str:
        return self.title


class PeytonStreetPensMonitor:
    SOURCE = "peytonstreetpens"
    BASE_URL = "https://www.peytonstreetpens.com"
    LIST_URL = BASE_URL + "/brands/ofs/?sort=newest"

    def __init__(
        self,
        timeout: int = 20,
        delay: int = 10,
        max_pages: int = 100,
    ) -> None:
        self.timeout = timeout
        self.delay = delay
        self.max_pages = max_pages

    @staticmethod
    def _parse_price(text: str | None) -> Decimal | None:
        if not text:
            return None
        cleaned = re.sub(r"[^\d.]", "", text)
        try:
            return Decimal(cleaned) if cleaned else None
        except InvalidOperation:
            return None

    def fetch(
        self,
        full_scan: bool = False,
    ) -> list[PeytonStreetPensItem]:
        items = []
        seen_ids = set()
        visited_urls = set()

        url = self.LIST_URL
        page_number = 0
        limit = self.max_pages if full_scan else 2

        session = requests.Session()
        session.headers.update({
            "User-Agent": (
                "PenWatch/1.0 "
                "(personal non-commercial collector monitor)"
            )
        })

        while url and page_number < limit:
            if url in visited_urls:
                raise RuntimeError(
                    f"Pagination loop detected: {url}"
                )

            if page_number:
                time.sleep(self.delay)

            visited_urls.add(url)

            response = session.get(
                url,
                timeout=self.timeout,
            )
            response.raise_for_status()

            soup = BeautifulSoup(
                response.text,
                "html.parser",
            )

            cards = soup.select(".productGrid .product")

            if not cards:
                raise RuntimeError(
                    f"No product cards found: {url}"
                )

            page_number += 1

            for card in cards:
                id_node = card.select_one("[data-product-id]")
                title_node = card.select_one(".card-title a")

                if not id_node or not title_node:
                    continue

                item_id = id_node.get("data-product-id")
                href = title_node.get("href")
                title = title_node.get_text(" ", strip=True)

                if not item_id or not href or not title:
                    continue

                if item_id in seen_ids:
                    continue

                seen_ids.add(item_id)

                price_node = card.select_one(
                    ".price--withoutTax"
                )
                sku_node = card.select_one(".sku-value")
                image_node = card.select_one(
                    "img.card-image"
                )

                cart_button = card.select_one(
                    ".add-to-cart-button a"
                )

                image_url = None
                if image_node:
                    src = (
                        image_node.get("data-src")
                        or image_node.get("src")
                    )
                    if src:
                        image_url = urljoin(self.BASE_URL, src)

                items.append(
                    PeytonStreetPensItem(
                        item_id=str(item_id),
                        title=title,
                        url=urljoin(self.BASE_URL, href),
                        price=self._parse_price(
                            price_node.get_text(" ", strip=True)
                            if price_node else None
                        ),
                        sku=(
                            sku_node.get_text(" ", strip=True)
                            if sku_node else None
                        ),
                        image_url=image_url,
                        available=True if cart_button else None,
                    )
                )

            print(
                f"Peyton Street Pens: page {page_number}, "
                f"{len(cards)} cards, {len(items)} unique items",
                flush=True,
            )

            next_link = soup.select_one(
                '.pagination a[aria-label="Next"]'
            )

            if not next_link:
                next_link = next(
                    (
                        a for a in soup.select(".pagination a[href]")
                        if a.get_text(" ", strip=True).lower()
                        == "next"
                    ),
                    None,
                )

            next_url = (
                urljoin(self.BASE_URL, next_link["href"])
                if next_link and next_link.get("href")
                else None
            )

            if not full_scan and page_number >= 2:
                break

            if next_url and next_url in visited_urls:
                raise RuntimeError(
                    f"Pagination loop detected: {next_url}"
                )

            url = next_url

        if full_scan and url and page_number >= self.max_pages:
            raise RuntimeError(
                f"Full scan incomplete: reached "
                f"{self.max_pages}-page safety limit"
            )

        return items
