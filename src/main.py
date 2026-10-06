import os

from database import Database
from notifications.ntfy import NtfyNotifier


def main() -> None:
    database = Database(
        os.getenv("PENWATCH_DB", "data/penwatch.db")
    )
    notifier = NtfyNotifier()

    # Simulierter Treffer zum Test der gesamten PenWatch-Pipeline
    source = "test"
    item_id = "penwatch-test-001"
    watchlist_id = "soennecken"
    title = "Testtreffer: Soennecken 111"
    url = "https://www.reddit.com/r/Pen_Swap/"

    if database.has_seen(source, item_id, watchlist_id):
        print("Treffer bereits bekannt – keine Benachrichtigung.")
        return

    notifier.send(
        title="PenWatch – Soennecken",
        message=title,
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

    print("Neuer Treffer – Push gesendet und in Datenbank gespeichert.")


if __name__ == "__main__":
    main()
