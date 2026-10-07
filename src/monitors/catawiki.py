import math
import re
import time
import requests
from dataclasses import dataclass
from bs4 import BeautifulSoup


@dataclass
class CatawikiItem:
    item_id: str
    title: str
    price: float | None
    currency: str | None
    url: str
    image_url: str | None
    searchable_text: str


class CatawikiMonitor:
    SOURCE = "catawiki"
    URL = "https://www.catawiki.com/en/x/31353-fountain-pen"

    HEADERS = {
        "User-Agent": (
            "PenWatch/1.0 "
            "(personal non-commercial collector monitor)"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }

    REQUEST_DELAY = 0.5
    TIMEOUT = 20

    def _fetch_page(self, page: int) -> tuple[list[CatawikiItem], int | None]:
        url = self.URL if page == 1 else f"{self.URL}?page={page}"

        response = requests.get(
            url,
            headers=self.HEADERS,
            timeout=self.TIMEOUT,
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        total = None

        next_data = soup.find("script", id="__NEXT_DATA__")
        if next_data and next_data.string:
            try:
                import json

                data = json.loads(next_data.string)
                total = (
                    data
                    .get("props", {})
                    .get("pageProps", {})
                    .get("collectionLots", {})
                    .get("total")
                )
            except (ValueError, TypeError, AttributeError):
                total = None

        items = []
        seen_ids = set()

        for card in soup.select("a.c-lot-card[href]"):
            href = card.get("href", "")

            match = re.search(r"/en/l/(\d+)", href)
            if not match:
                continue

            item_id = match.group(1)

            if item_id in seen_ids:
                continue

            seen_ids.add(item_id)

            if href.startswith("/"):
                item_url = "https://www.catawiki.com" + href
            else:
                item_url = href

            title_node = card.select_one(".c-lot-card__title")
            if title_node:
                title = title_node.get_text(" ", strip=True)
            else:
                title = card.get_text(" ", strip=True)

            image_node = card.find("img")
            image_url = None

            if image_node:
                image_url = (
                    image_node.get("src")
                    or image_node.get("data-src")
                )

            searchable_text = " ".join(
                part
                for part in [
                    title,
                    card.get_text(" ", strip=True),
                ]
                if part
            )

            items.append(
                CatawikiItem(
                    item_id=item_id,
                    title=title,
                    price=None,
                    currency=None,
                    url=item_url,
                    image_url=image_url,
                    searchable_text=searchable_text,
                )
            )

        return items, total

    def fetch(self) -> list[CatawikiItem]:
        first_page, total = self._fetch_page(1)

        if not first_page:
            return []

        items_per_page = len(first_page)

        if total is None or total <= items_per_page:
            return first_page

        total_pages = math.ceil(total / items_per_page)

        all_items = []
        seen_ids = set()

        def add_items(page_items):
            for item in page_items:
                if item.item_id in seen_ids:
                    continue

                seen_ids.add(item.item_id)
                all_items.append(item)

        add_items(first_page)

        for page in range(2, total_pages + 1):
            time.sleep(self.REQUEST_DELAY)

            page_items, _ = self._fetch_page(page)

            if not page_items:
                break

            add_items(page_items)

        return all_items
