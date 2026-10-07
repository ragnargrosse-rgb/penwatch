from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


@dataclass
class MartiniItem:
    item_id: str
    title: str
    url: str
    description: str = ""
    current_bid: Optional[Decimal] = None
    buy_now_price: Optional[Decimal] = None
    currency: str = "EUR"
    image_url: Optional[str] = None

    @property
    def searchable_text(self) -> str:
        return " ".join(
            part
            for part in (
                self.title,
                self.description,
            )
            if part
        )


class MartiniMonitor:
    SOURCE = "martiniauctions"
    BASE_URL = "https://www.martiniauctions.com/"
    BROWSE_URL = urljoin(BASE_URL, "browse.php")

    def __init__(self, timeout: int = 20) -> None:
        self.timeout = timeout

    @staticmethod
    def _parse_price(value: str | None) -> Optional[Decimal]:
        if not value:
            return None

        cleaned = (
            value.replace("EUR", "")
            .replace("\xa0", " ")
            .strip()
            .replace(".", "")
            .replace(",", ".")
        )

        try:
            return Decimal(cleaned)
        except InvalidOperation:
            return None

    def fetch(self) -> list[MartiniItem]:
        response = requests.get(
            self.BROWSE_URL,
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
        items: list[MartiniItem] = []

        for row in soup.select("div.update_item[data-id]"):
            item_id = row.get("data-id")

            if not item_id:
                continue

            image_box = row.select_one("div.image")
            link = image_box.find("a") if image_box else None

            if not link:
                continue

            title = (
                link.get("title")
                or link.get("aria-label")
                or link.get_text(" ", strip=True)
            )

            if not title:
                continue

            href = link.get("href")

            if not href:
                continue

            description_node = row.select_one("div.description")
            description = (
                description_node.get_text(" ", strip=True)
                if description_node
                else ""
            )

            current_bid_node = row.select_one("span.current_bid")
            buy_now_node = row.select_one("span.buy_now_price")

            current_bid = self._parse_price(
                current_bid_node.get_text(" ", strip=True)
                if current_bid_node
                else None
            )

            buy_now_price = self._parse_price(
                buy_now_node.get_text(" ", strip=True)
                if buy_now_node
                else None
            )

            image = image_box.find("img") if image_box else None
            image_url = None

            if image and image.get("src"):
                image_url = urljoin(
                    self.BASE_URL,
                    image.get("src"),
                )

            items.append(
                MartiniItem(
                    item_id=str(item_id),
                    title=title.strip(),
                    url=urljoin(self.BASE_URL, href),
                    description=description,
                    current_bid=current_bid,
                    buy_now_price=buy_now_price,
                    image_url=image_url,
                )
            )

        return items
