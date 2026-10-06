import os

from dotenv import load_dotenv

from database import Database
from notifications.ntfy import NtfyNotifier
from watchlist import Watchlist


load_dotenv()


def main() -> None:
    database = Database(
        os.getenv("PENWATCH_DB", "data/penwatch.db")
    )
    notifier = NtfyNotifier()
    watchlist = Watchlist()

    # Simulierter Marktplatz-Treffer
    source = "test"
    item_id = "penwatch-test-002"
    title = "Vintage Soennecken 111 Extra for sale"
    description = "Restored fountain pen with original gold nib."
    url = "https://www.reddit.com/r/Pen_Swap/"

    searchable_text = f"{title}\n{description}"

    for entry in watchlist.enabled():
        matched_keywords = watchlist.matches(entry, searchable_text)

        if not matched_keywords:
            continue

        watchlist_id = entry["id"]

        if database.has_seen(source, item_id, watchlist_id):
            print(
                f"Treffer für '{entry['name']}' bereits bekannt "
                "- keine Benachrichtigung."
            )
            continue

        notification_title = (
            entry.get("notification", {}).get("title")
            or f"PenWatch - {entry['name']}"
        )

        message = (
            f"{title}\n\n"
            f"Treffer: {', '.join(matched_keywords)}\n"
            f"Quelle: {source}"
        )

        notifier.send(
            title=notification_title.replace("–", "-"),
            message=message,
            url=url,
            priority="high",
        )

        database.mark_seen(
            source=source,
            item_id=item_id,
            watchlist_id=watchlist_id,
            title=title,
            url=url,
        )

        print(
            f"Neuer Treffer für '{entry['name']}' - "
            "Push gesendet und gespeichert."
        )


if __name__ == "__main__":
    main()
