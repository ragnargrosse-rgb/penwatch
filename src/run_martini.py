import argparse

from database import Database
from monitors.martini import MartiniMonitor
from notifications.ntfy import NtfyNotifier
from watchlist import Watchlist


def build_message(item, matched_terms: list[str]) -> str:
    parts = []

    if item.current_bid is not None:
        parts.append(f"Current bid: {item.current_bid} {item.currency}")

    if item.buy_now_price is not None:
        parts.append(f"Buy now: {item.buy_now_price} {item.currency}")

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

    parser.add_argument(
        "--full-scan",
        action="store_true",
        help="Scan all available MARTINI catalogue pages.",
    )

    args = parser.parse_args()

    database = Database()
    watchlist = Watchlist()
    monitor = MartiniMonitor()

    notifier = None

    if not args.dry_run:
        notifier = NtfyNotifier()

    items = monitor.fetch(full_scan=args.full_scan)
    entries = watchlist.enabled()

    print(
        f"MARTINI: {len(items)} items, "
        f"{len(entries)} enabled watchlists"
    )

    new_items = 0
    matches_found = 0

    for item in items:
        is_known = database.has_source_item(
            monitor.SOURCE,
            item.item_id,
        )

        if not is_known:
            new_items += 1

        status = "KNOWN" if is_known else "NEW"
        print(
            f"{status}: {item.item_id} | "
            f"{item.title[:80]}"
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
