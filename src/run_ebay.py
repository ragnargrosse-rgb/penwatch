import argparse

from database import Database
from monitors.ebay import EbayMonitor
from notifications.ntfy import NtfyNotifier
from watchlist import Watchlist


def build_message(item, matched_terms: list[str]) -> str:
    parts = []

    if item.price is not None:
        price = f"{item.price}"
        if item.currency:
            price += f" {item.currency}"
        parts.append(f"Price: {price}")

    if item.condition:
        parts.append(f"Condition: {item.condition}")

    if item.location:
        parts.append(f"Location: {item.location}")

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

    parser.add_argument(
        "--baseline",
        action="store_true",
        help=(
            "Store all currently discovered eBay listings as known "
            "without sending notifications."
        ),
    )

    args = parser.parse_args()

    if args.dry_run and args.baseline:
        parser.error("--dry-run and --baseline cannot be used together")

    database = Database()
    watchlist = Watchlist()
    monitor = EbayMonitor()

    notifier = None

    if not args.dry_run and not args.baseline:
        notifier = NtfyNotifier()

    entries = []

    for entry in watchlist.enabled():
        ebay_config = (
            entry.get("sources", {})
            .get("ebay", {})
        )

        if ebay_config.get("enabled", False):
            entries.append(entry)

    print(
        f"eBay: {len(entries)} enabled watchlists "
        f"on {monitor.marketplace}"
    )

    # An item can be returned by several eBay searches.
    # Keep one copy per eBay item ID.
    discovered_items = {}

    for entry in entries:
        watchlist_id = entry.get(
            "id",
            entry.get("name", "unknown"),
        )

        ebay_config = (
            entry.get("sources", {})
            .get("ebay", {})
        )

        queries = ebay_config.get("queries", [])

        if not queries:
            print(
                f"WARNING: no eBay search query for "
                f"{watchlist_id}"
            )
            continue

        for query in queries:
            print(
                f"SEARCH: {watchlist_id} | {query}"
            )

            items = monitor.search(
                query,
                limit=100,
            )

            print(
                f"  RESULTS: {len(items)}"
            )

            for item in items:
                discovered_items[item.item_id] = item

    print(
        f"UNIQUE ITEMS: {len(discovered_items)}"
    )

    new_items = 0
    matches_found = 0

    if args.baseline:
        baseline_added = 0

        for item in discovered_items.values():
            if database.has_source_item(
                monitor.SOURCE,
                item.item_id,
            ):
                continue

            database.mark_source_item(
                monitor.SOURCE,
                item.item_id,
                item.title,
                item.url,
            )
            baseline_added += 1

        print()
        print(
            f"Baseline complete: "
            f"discovered={len(discovered_items)}, "
            f"added={baseline_added}"
        )
        return

    for item in discovered_items.values():
        known = database.has_source_item(
            monitor.SOURCE,
            item.item_id,
        )

        if known:
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

        # Mark every discovered listing after all watchlists
        # have been evaluated. This establishes the baseline
        # and prevents notifications for old listings later.
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
