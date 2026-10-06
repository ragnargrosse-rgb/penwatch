import os

from dotenv import load_dotenv

from database import Database
from monitors.ebay import EbayMonitor
from notifications.ntfy import NtfyNotifier
from watchlist import Watchlist


load_dotenv()


def main() -> None:
    database = Database(
        os.getenv("PENWATCH_DB", "data/penwatch.db")
    )
    notifier = NtfyNotifier()
    watchlist = Watchlist()

    # Simulated response from the eBay Browse API
    mock_api_item = {
        "itemId": "v1|123456789|0",
        "title": "Vintage Soennecken 111 Extra Fountain Pen",
        "itemWebUrl": "https://www.ebay.de/itm/123456789",
        "price": {
            "value": "149.00",
            "currency": "EUR",
        },
        "condition": "Used",
        "itemLocation": {
            "country": "DE",
        },
        "image": {
            "imageUrl": "https://example.com/soennecken.jpg",
        },
    }

    item = EbayMonitor.parse_item(mock_api_item)

    for entry in watchlist.enabled():
        matched_keywords = watchlist.matches(
            entry,
            item.searchable_text,
        )

        if not matched_keywords:
            continue

        watchlist_id = entry["id"]

        if database.has_seen(
            EbayMonitor.SOURCE,
            item.item_id,
            watchlist_id,
        ):
            print(
                f"eBay-Treffer für '{entry['name']}' bereits bekannt "
                "- keine Benachrichtigung."
            )
            continue

        price_text = (
            f"{item.price} {item.currency}"
            if item.price is not None
            else "Preis nicht verfügbar"
        )

        message = (
            f"{item.title}\n\n"
            f"Preis: {price_text}\n"
            f"Zustand: {item.condition or 'nicht angegeben'}\n"
            f"Standort: {item.location or 'nicht angegeben'}\n"
            f"Treffer: {', '.join(matched_keywords)}"
        )

        notification_title = (
            entry.get("notification", {}).get("title")
            or f"PenWatch - {entry['name']}"
        )

        notifier.send(
            title=notification_title.replace("–", "-"),
            message=message,
            url=item.url,
            priority="high",
        )

        database.mark_seen(
            source=EbayMonitor.SOURCE,
            item_id=item.item_id,
            watchlist_id=watchlist_id,
            title=item.title,
            url=item.url,
        )

        print(
            f"Neuer eBay-Treffer für '{entry['name']}' - "
            "Push gesendet und gespeichert."
        )


if __name__ == "__main__":
    main()
