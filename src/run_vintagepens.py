import argparse

from database import Database
from monitors.vintagepens import VintagePensMonitor
from notifications.ntfy import NtfyNotifier
from watchlist import Watchlist


def build_message(item, matched_terms: list[str]) -> str:
    parts = []

    if item.category:
        parts.append(f"Brand: {item.category}")

    if item.published_at:
        parts.append(f"Published: {item.published_at}")

    if matched_terms:
        parts.append("Matched: " + ", ".join(matched_terms))

    return "\n".join(parts)


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not send notifications or write to the database.",
    )

    args = parser.parse_args()

    database = Database()
    watchlist = Watchlist()
    monitor = VintagePensMonitor()

    notifier = None

    if not args.dry_run:
        notifier = NtfyNotifier()

    items = monitor.fetch()
    entries = watchlist.enabled()

    print(
        f"VintagePens: {len(items)} items, "
        f"{len(entries)} enabled watchlists"
    )

    new_items = 0
    matches_found = 0

    for item in items:
        if database.has_source_item(
            monitor.SOURCE,
            item.item_id,
        ):
            print(
                f"KNOWN: {item.item_id} | "
                f"{item.title[:100]}"
            )
            continue

        new_items += 1

        print(
            f"NEW: {item.item_id} | "
            f"{item.title[:100]}"
        )

        for entry in entries:
            matched_terms = Watchlist.matches(
                entry,
                item.searchable_text,
            )

            if not matched_terms:
                continue

            watchlist_id = entry.get(
                "id",
                entry.get("name", "unknown"),
            )

            if database.has_seen(
                monitor.SOURCE,
                item.item_id,
                watchlist_id,
            ):
                continue

            matches_found += 1

            watchlist_name = entry.get(
                "name",
                watchlist_id,
            )

            print(
                f"  MATCH: {watchlist_name} | "
                f"{', '.join(matched_terms)}"
            )

            if args.dry_run:
                continue

            notification = entry.get(
                "notification",
                {},
            )

            notification_title = notification.get(
                "title",
                f"PenWatch - {watchlist_name}",
            )

            notifier.send(
                title=notification_title,
                message=build_message(
                    item,
                    matched_terms,
                ),
                url=item.url,
                priority="default",
            )

            database.mark_seen(
                monitor.SOURCE,
                item.item_id,
                watchlist_id,
                item.title,
                item.url,
            )

        if not args.dry_run:
            database.mark_source_item(
                monitor.SOURCE,
                item.item_id,
                item.title,
                item.url,
            )

    print()
    print(
        f"Done: new={new_items}, "
        f"matches={matches_found}, "
        f"dry_run={args.dry_run}"
    )


if __name__ == "__main__":
    main()
