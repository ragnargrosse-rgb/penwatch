import re
import requests
import xml.etree.ElementTree as ET
from dataclasses import dataclass


@dataclass
class VintagePensItem:
    item_id: str
    title: str
    url: str
    description: str
    category: str
    published_at: str
    searchable_text: str


class VintagePensMonitor:
    SOURCE = "vintagepens"
    FEED_URL = "https://www.vintagepens.com/RSSnew.xml"

    def fetch(self) -> list[VintagePensItem]:
        response = requests.get(
            self.FEED_URL,
            headers={
                "User-Agent": (
                    "PenWatch/1.0 "
                    "(personal non-commercial collector monitor)"
                )
            },
            timeout=20,
        )
        response.raise_for_status()

        xml_text = self._repair_xml(response.text)
        root = ET.fromstring(xml_text)

        results = []

        for node in root.findall(".//item"):
            title = self._text(node, "title")
            url = self._text(node, "link")
            guid = self._text(node, "guid")
            description = self._text(node, "description")
            category = self._text(node, "category")
            published_at = self._text(node, "pubDate")

            item_id = self._extract_item_id(guid, url)

            if not item_id or not title or not url:
                continue

            searchable_text = " ".join(
                value
                for value in (
                    title,
                    description,
                    category,
                )
                if value
            )

            results.append(
                VintagePensItem(
                    item_id=item_id,
                    title=title,
                    url=url,
                    description=description,
                    category=category,
                    published_at=published_at,
                    searchable_text=searchable_text,
                )
            )

        return results

    @staticmethod
    def _repair_xml(text: str) -> str:
        # VintagePens uses this HTML entity in its RSS XML.
        # It is valid HTML but undefined in XML.
        return text.replace("&frac12;", "½")

    @staticmethod
    def _text(node, tag: str) -> str:
        child = node.find(tag)

        if child is None:
            return ""

        return "".join(child.itertext()).strip()

    @staticmethod
    def _extract_item_id(guid: str, url: str) -> str:
        if guid:
            match = re.search(r"\bitem\s+(\d+)\b", guid, re.IGNORECASE)
            if match:
                return match.group(1)

        if url:
            match = re.search(r"#(\d+)(?:$|[/?&])", url)
            if match:
                return match.group(1)

        return ""
