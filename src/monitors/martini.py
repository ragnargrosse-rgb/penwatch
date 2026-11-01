import time
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Optional
from urllib.parse import urljoin, urlparse, parse_qs

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


    def fetch(
        self,
        full_scan: bool = False,
        delay: float = 10.0,
        max_pages: int = 300,
    ) -> list[MartiniItem]:
        """
        Fetch newly listed MARTINI items.

        Regular scan: first two pages.
        Full scan: follow pagination until the final page.
        """
        if delay < 10:
            raise ValueError("MARTINI requires at least 10 seconds crawl delay.")

        session = requests.Session()
        session.headers.update({
            "User-Agent": (
                "PenWatch/1.0 "
                "(personal non-commercial collector monitor)"
            )
        })

        items = []
        seen_ids = set()
        page = 1
        last_request = None
        expected_last_page = None

        while True:
            if last_request is not None:
                remaining = delay - (time.monotonic() - last_request)
                if remaining > 0:
                    time.sleep(remaining)

            params = {
                "order_by_sort": "mod_desc",
                "sort": "2",
                "page": page,
            }

            last_request = time.monotonic()
            response = session.get(
                self.BROWSE_URL,
                params=params,
                timeout=self.timeout,
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            rows = soup.select("div.update_item[data-id]")

            if not rows:
                raise RuntimeError(
                    f"MARTINI page {page}: no items found; "
                    "possible parser or website error."
                )

            page_items = []

            for row in rows:
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
                href = link.get("href")

                if not title or not href:
                    continue

                description_node = row.select_one("div.description")
                description = (
                    description_node.get_text(" ", strip=True)
                    if description_node else ""
                )

                current_bid_node = row.select_one("span.current_bid")
                buy_now_node = row.select_one("span.buy_now_price")

                image = image_box.find("img") if image_box else None
                image_url = (
                    urljoin(self.BASE_URL, image.get("src"))
                    if image and image.get("src")
                    else None
                )

                page_items.append(
                    MartiniItem(
                        item_id=str(item_id),
                        title=title.strip(),
                        url=urljoin(self.BASE_URL, href),
                        description=description,
                        current_bid=self._parse_price(
                            current_bid_node.get_text(" ", strip=True)
                            if current_bid_node else None
                        ),
                        buy_now_price=self._parse_price(
                            buy_now_node.get_text(" ", strip=True)
                            if buy_now_node else None
                        ),
                        image_url=image_url,
                    )
                )

            if not page_items:
                raise RuntimeError(
                    f"MARTINI page {page}: HTML rows found, "
                    "but no valid items parsed."
                )

            new_on_page = 0
            for item in page_items:
                if item.item_id not in seen_ids:
                    seen_ids.add(item.item_id)
                    items.append(item)
                    new_on_page += 1

            if new_on_page == 0:
                raise RuntimeError(
                    f"MARTINI page {page}: all item IDs repeated; "
                    "pagination may be broken."
                )

            print(
                f"MARTINI page {page}: "
                f"{len(page_items)} parsed, "
                f"{len(items)} unique total",
                flush=True,
            )

            if not full_scan and page >= 2:
                break

            if full_scan:
                current_page = page
                has_next = False
                linked_pages = set()

                for anchor in soup.select("a[href]"):
                    href = urljoin(
                        response.url,
                        anchor.get("href", ""),
                    )
                    parsed = urlparse(href)
                    query = parse_qs(parsed.query)

                    if parsed.path.rstrip("/") != "/browse.php":
                        continue

                    try:
                        target_page = int(
                            query.get("page", ["0"])[0]
                        )
                    except ValueError:
                        continue

                    linked_pages.add(target_page)

                    if target_page == current_page + 1:
                        has_next = True

                if page == 1:
                    expected_last_page = max(linked_pages | {1})
                    print(
                        f"MARTINI expected last page: {expected_last_page}",
                        flush=True,
                    )

                if expected_last_page is not None:
                    if page >= expected_last_page:
                        break

                    # Continue up to the last page discovered on page 1,
                    # even if the direct next-page link is missing.
                elif not has_next:
                    break

            if page >= max_pages:
                raise RuntimeError(
                    f"MARTINI scan reached safety limit "
                    f"of {max_pages} pages."
                )

            page += 1

        return items
