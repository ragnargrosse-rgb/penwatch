from dataclasses import dataclass
from decimal import Decimal
import re
import time

import requests
from bs4 import BeautifulSoup


@dataclass(frozen=True)
class PenboardItem:
    item_id: str
    title: str
    url: str
    description: str
    price: Decimal | None = None
    currency: str = "EUR"
    condition: str | None = None
    year: str | None = None
    image_url: str | None = None

    @property
    def searchable_text(self) -> str:
        parts = [
            self.title,
            self.description,
            self.condition or "",
            self.year or "",
        ]

        return "\n".join(
            part for part in parts if part
        )


class PenboardMonitor:
    SOURCE = "penboard"

    BASE_URL = "https://www.penboard.de"
    WHATS_NEW_URL = f"{BASE_URL}/shop/whatsnew"
    SEARCH_URL = f"{BASE_URL}/shop/searchshop/"

    SEARCH_TERMS = (
        "Pelikan",
        "Soennecken",
    )

    FULL_SCAN_TERMS = (
        "100",
        "100N",
        "140",
        "400",
        "400N",
        "400NN",
        "660",
        "M800",
        "Knickebein",
        "Schildpatt",
        "Warenkunde",
        "Preisliste",
        "Soennecken 111",
        "Soennecken 222",
    )

    def __init__(self, timeout: int = 20) -> None:
        self.timeout = timeout

    def fetch(
        self,
        full_scan: bool = False,
        delay: float = 2.0,
    ) -> list[PenboardItem]:
        if delay < 2.0:
            raise ValueError("Penboard scan delay must be at least 2 seconds.")

        session = requests.Session()
        session.headers.update({
            "User-Agent": (
                "PenWatch/1.0 "
                "(personal non-commercial collector monitor)"
            )
        })

        all_items: dict[str, PenboardItem] = {}

        def add_items(items: list[PenboardItem]) -> None:
            for item in items:
                previous = all_items.get(item.item_id)
                if previous is None or len(item.searchable_text) > len(previous.searchable_text):
                    all_items[item.item_id] = item

        response = session.get(
            self.WHATS_NEW_URL,
            timeout=self.timeout,
        )
        response.raise_for_status()
        add_items(self.parse_html(response.text))

        if full_scan:
            # Discover seller IDs from the live shop navigation.
            time.sleep(delay)
            response = session.get(
                f"{self.BASE_URL}/shop/home",
                timeout=self.timeout,
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            seller_options = soup.select("#searchseller option")

            if not seller_options:
                raise RuntimeError(
                    "Penboard seller navigation not found; "
                    "full scan cannot verify seller coverage."
                )

            seller_ids = list(dict.fromkeys(
                option.get("value")
                for option in seller_options
                if option.get("value") is not None
            ))

            if "0" not in seller_ids:
                raise RuntimeError(
                    "Penboard all-sellers option missing."
                )

            terms = ("",) + tuple(dict.fromkeys(
                self.SEARCH_TERMS + self.FULL_SCAN_TERMS
            ))
        else:
            seller_ids = ["0"]
            terms = self.SEARCH_TERMS

        for term in terms:
            for seller_id in seller_ids:
                time.sleep(delay)

                response = session.get(
                    self.SEARCH_URL,
                    params={
                        "srchvalue": term,
                        "shop_seller": seller_id,
                    },
                    timeout=self.timeout,
                )
                response.raise_for_status()

                add_items(self.parse_search_html(response.text))

        return list(all_items.values())


    @staticmethod
    def _clean(value: str | None) -> str | None:
        if not value:
            return None

        value = " ".join(value.split())
        return value or None

    @staticmethod
    def _parse_price(text: str) -> Decimal | None:
        match = re.search(
            r"(\d{1,3}(?:\.\d{3})*|\d+),(\d{2})\s*(?:€|euro)",
            text,
            re.IGNORECASE,
        )

        if not match:
            return None

        whole = match.group(1).replace(".", "")
        cents = match.group(2)

        return Decimal(f"{whole}.{cents}")

    @staticmethod
    def _extract_field(
        text: str,
        field: str,
    ) -> str | None:
        match = re.search(
            rf"\b{re.escape(field)}\s*:\s*"
            rf"(.+?)(?=\s+[A-Z][A-Za-z ]{{1,20}}\s*:|\s+Details\s*$|$)",
            text,
            re.IGNORECASE,
        )

        if not match:
            return None

        return " ".join(match.group(1).split())

    @classmethod
    def parse_search_html(cls, html: str) -> list[PenboardItem]:
        soup = BeautifulSoup(html, "html.parser")

        items: list[PenboardItem] = []

        # Search/inventory pages use:
        # <td id="T114721"> ... </td>
        listing_blocks = soup.find_all(
            "td",
            id=re.compile(r"^T[A-Za-z0-9]+$"),
        )

        for block in listing_blocks:
            text = cls._clean(
                block.get_text(" ", strip=True)
            )

            if not text:
                continue

            id_match = re.search(
                r"\bItem No\.\s*([A-Za-z0-9]+)",
                text,
                re.IGNORECASE,
            )

            if id_match:
                item_id = id_match.group(1)
            else:
                raw_id = block.get("id", "")
                item_id = (
                    raw_id[1:]
                    if raw_id.startswith("T")
                    else raw_id
                )

            if not item_id:
                continue

            title_node = block.find("h2")

            title = (
                cls._clean(
                    title_node.get_text(" ", strip=True)
                )
                if title_node
                else None
            )

            if not title:
                continue

            # Stable item-specific HTTP URL available on these pages.
            url = requests.compat.urljoin(
                cls.BASE_URL,
                f"/shop/enquiry/{item_id}",
            )

            image = block.find("img", src=True)
            image_url = None

            if image:
                image_url = requests.compat.urljoin(
                    cls.BASE_URL,
                    image["src"],
                )

            # Keep marketplace metadata such as prices, quantities,
            # shipping costs and item numbers out of watchlist matching.
            # On Penboard search pages these fields begin after "Actions".
            description = re.split(
                r"\s+Actions\s+",
                text,
                maxsplit=1,
                flags=re.IGNORECASE,
            )[0].strip()

            items.append(
                PenboardItem(
                    item_id=item_id,
                    title=title,
                    url=url,
                    description=description,
                    price=cls._parse_price(text),
                    condition=cls._extract_field(
                        text,
                        "Condition",
                    ),
                    year=cls._extract_field(
                        text,
                        "Year",
                    ),
                    image_url=image_url,
                )
            )

        unique = {
            item.item_id: item
            for item in items
        }

        return list(unique.values())

    @classmethod
    def parse_html(cls, html: str) -> list[PenboardItem]:
        soup = BeautifulSoup(html, "html.parser")

        items: list[PenboardItem] = []

        # Actual Penboard structure:
        # <div class="row" id="hd_0"> ... /shop/details/114596 ... </div>
        listing_blocks = soup.find_all(
            "div",
            id=re.compile(r"^hd_\d+$"),
        )

        for block in listing_blocks:
            details_link = block.find(
                "a",
                href=re.compile(r"/shop/details/\d+"),
            )

            if details_link is None:
                continue

            href = details_link.get("href", "")

            id_match = re.search(
                r"/shop/details/(\d+)",
                href,
            )

            if not id_match:
                continue

            item_id = id_match.group(1)

            url = requests.compat.urljoin(
                cls.BASE_URL,
                href,
            )

            text = cls._clean(
                block.get_text(" ", strip=True)
            )

            if not text:
                continue

            # Remove price and trailing "Details" from the text
            description = re.sub(
                r"^\s*\d+(?:[.,]\d+)?\s*(?:€|euro)\s*",
                "",
                text,
                flags=re.IGNORECASE,
            )

            description = re.sub(
                r"\s*Details\s*$",
                "",
                description,
                flags=re.IGNORECASE,
            )

            description = cls._clean(description) or text

            # Penboard's first descriptive words are useful enough
            # as a compact notification title.
            title = description

            if len(title) > 120:
                title = title[:117].rstrip() + "..."

            image = block.find("img", src=True)

            image_url = None

            if image:
                image_url = requests.compat.urljoin(
                    cls.BASE_URL,
                    image["src"],
                )

            items.append(
                PenboardItem(
                    item_id=item_id,
                    title=title,
                    url=url,
                    description=description,
                    price=cls._parse_price(text),
                    condition=cls._extract_field(
                        text,
                        "Condition",
                    ),
                    year=cls._extract_field(
                        text,
                        "Year",
                    ),
                    image_url=image_url,
                )
            )

        # Defensive duplicate removal
        unique = {
            item.item_id: item
            for item in items
        }

        return list(unique.values())
