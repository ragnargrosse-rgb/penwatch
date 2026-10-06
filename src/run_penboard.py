import argparse

from database import Database
from monitors.penboard import PenboardMonitor
from notifications.ntfy import NtfyNotifier
from watchlist import Watchlist


def build_message(item, matched_terms: list[str]) -> str:
    parts = []

    if item.price is not None:
        parts.append(f"Price: {item.price} {item.currency}")

    if item.condition:
        parts.append(f"Condition: {item.condition}")

    if item.year:
        parts.append(f"Year: {item.year}")

    if matched_terms:
        parts.append(
            "Matched: " + ", ".join(matched_terms)
        )

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
    monitor = PenboardMonitor()

    notifier = None

    if not args.dry_run:
        notifier = NtfyNotifier()

    items = monitor.fetch()
    entries = watchlist.enabled()

    print(
        f"Penboard: {len(items)} items, "
        f"{len(entries)} enabled watchlists"
    )

    new_items = 0
    matches_found = 0

    for item in items:
        known = database.has_source_item(
            monitor.SOURCE,
            item.item_id,
        )

        if known:
            print(
                f"KNOWN: {item.item_id} | "
                f"{item.title[:80]}"
            )
            continue

        new_items += 1

        print(
            f"NEW: {item.item_id} | "
            f"{item.title[:80]}"
        )

        text = item.searchable_text

        for entry in entries:
            matched_terms = Watchlist.matches(
                entry,
                text,
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

            message = build_message(
                item,
                matched_terms,
            )

            notifier.send(
                title=notification_title,
                message=message,
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

        # Important:
        # only mark the source item after all watchlists
        # have been evaluated successfully.
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
