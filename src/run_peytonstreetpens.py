
import argparse

from database import Database
from monitors.peytonstreetpens import PeytonStreetPensMonitor
from notifications.ntfy import NtfyNotifier
from watchlist import Watchlist


def build_message(item, matched_terms: list[str]) -> str:
    parts = [item.title]

    if item.price is not None:
        parts.append(f"Price: {item.price} {item.currency}")

    if item.sku:
        parts.append(f"SKU: {item.sku}")

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
        help="Scan all available product listing pages.",
    )

    args = parser.parse_args()

    monitor = PeytonStreetPensMonitor()
    watchlist = Watchlist()
    entries = watchlist.enabled()

    # Fetch before initializing the notifier.
    items = monitor.fetch(full_scan=args.full_scan)

    database = Database()
    notifier = None if args.dry_run else NtfyNotifier()

    print(
        f"Peyton Street Pens: {len(items)} items, "
        f"{len(entries)} enabled watchlists, "
        f"full_scan={args.full_scan}",
        flush=True,
    )

    new_items = 0
    matches_found = 0

    for item in items:
        known = database.has_source_item(
            monitor.SOURCE,
            item.item_id,
        )

        if not known:
            new_items += 1

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
                f"MATCH: {watchlist_name} | "
                f"{item.title} | "
                f"{item.url}",
                flush=True,
            )

            if args.dry_run:
                continue

            notification = entry.get("notification", {})
            notification_title = notification.get(
                "title",
                f"PenWatch - {watchlist_name}",
            )

            notifier.send(
                title=notification_title,
                message=build_message(item, matched_terms),
                url=item.url,
                priority="default",
            )

            # Mark only after successful notification.
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

    print(
        f"Done: new={new_items}, "
        f"matches={matches_found}, "
        f"dry_run={args.dry_run}",
        flush=True,
    )


if __name__ == "__main__":
    main()
