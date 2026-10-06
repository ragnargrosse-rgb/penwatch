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
    brand: str | None = None
    model: str | None = None
    year: str | None = None
    colour: str | None = None
    condition: str | None = None
    nib: str | None = None
    price: Decimal | None = None
    currency: str = "EUR"

    @property
    def searchable_text(self) -> str:
        parts = [
            self.title,
            self.brand or "",
            self.model or "",
            self.year or "",
            self.colour or "",
            self.condition or "",
            self.nib or "",
        ]

        return "\n".join(
            part for part in parts if part
        )


class PenboardMonitor:
    SOURCE = "penboard"

    WHATS_NEW_URL = "https://www.penboard.de/shop/whatsnew"

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

        return self.parse_html(
            response.text,
            self.WHATS_NEW_URL,
        )

    @staticmethod
    def _clean(value: str | None) -> str | None:
        if value is None:
            return None

        value = " ".join(value.split())

        return value or None

    @staticmethod
    def _parse_price(value: str | None) -> Decimal | None:
        if not value:
            return None

        match = re.search(
            r"€\s*([\d.]+(?:,\d{1,2})?)",
            value,
        )

        if not match:
            return None

        normalized = (
            match.group(1)
            .replace(".", "")
            .replace(",", ".")
        )

        return Decimal(normalized)

    @classmethod
    def parse_html(
        cls,
        html: str,
        source_url: str,
    ) -> list[PenboardItem]:
        soup = BeautifulSoup(html, "html.parser")

        items = []

        # Penboard listings expose their item number in the
        # visible item information. We use each heading as the
        # beginning of a candidate listing block.
        for heading in soup.find_all(["h2", "h3"]):
            title = cls._clean(
                heading.get_text(" ", strip=True)
            )

            if not title:
                continue

            container = heading.find_parent()

            if container is None:
                continue

            text = container.get_text(
                "\n",
                strip=True,
            )

            item_match = re.search(
                r"(?:Item No\.|Artikelnummer)\s*([A-Za-z0-9_-]+)",
                text,
                re.IGNORECASE,
            )

            if not item_match:
                continue

            item_id = item_match.group(1)

            def field(*labels: str) -> str | None:
                for label in labels:
                    pattern = (
                        rf"{re.escape(label)}\s*"
                        rf"([^\n]+)"
                    )

                    match = re.search(
                        pattern,
                        text,
                        re.IGNORECASE,
                    )

                    if match:
                        return cls._clean(
                            match.group(1)
                        )

                return None

            price_text = field(
                "EU price incl. VAT",
                "EU Preis inkl. Steuer",
                "EU price",
                "Export price",
                "Export Preis",
            )

            link = heading.find("a", href=True)

            url = source_url

            if link:
                url = requests.compat.urljoin(
                    source_url,
                    link["href"],
                )

            items.append(
                PenboardItem(
                    item_id=item_id,
                    title=title,
                    url=url,
                    brand=field(
                        "Brand",
                        "Marke",
                    ),
                    model=field(
                        "Model",
                        "Modell",
                    ),
                    year=field(
                        "Year",
                        "Jahr",
                    ),
                    colour=field(
                        "Colour",
                        "Farbe",
                    ),
                    condition=field(
                        "Condition",
                        "Zustand",
                    ),
                    nib=field(
                        "Nib",
                        "Feder",
                    ),
                    price=cls._parse_price(
                        price_text
                    ),
                )
            )

        # Avoid duplicate item numbers if Penboard's HTML
        # presents the same item more than once.
        unique = {}

        for item in items:
            unique[item.item_id] = item

        return list(unique.values())
