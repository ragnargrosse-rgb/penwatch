import re
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

    def fetch(self) -> list[CatawikiItem]:
        response = requests.get(
            self.URL,
            headers={
                "User-Agent": (
                    "PenWatch/1.0 "
                    "(personal non-commercial collector monitor)"
                ),
                "Accept-Language": "en-US,en;q=0.9",
            },
            timeout=20,
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

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
                url = "https://www.catawiki.com" + href
            else:
                url = href

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
                    url=url,
                    image_url=image_url,
                    searchable_text=searchable_text,
                )
            )

        return items
