from dataclasses import dataclass
from decimal import Decimal
import re

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

    def __init__(self, timeout: int = 20) -> None:
        self.timeout = timeout

    def fetch(self) -> list[PenboardItem]:
        response = requests.get(
            self.WHATS_NEW_URL,
            timeout=self.timeout,
            headers={
                "User-Agent": (
                    "PenWatch/1.0 "
                    "(personal non-commercial collector monitor)"
                )
            },
        )

        response.raise_for_status()

        return self.parse_html(response.text)

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
