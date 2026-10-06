from decimal import Decimal

from dotenv import load_dotenv

load_dotenv("/opt/penwatch/.env")

from monitors.penboard import PenboardItem
from notifications.ntfy import NtfyNotifier
from watchlist import Watchlist
from run_penboard import build_message


def main() -> None:
    item = PenboardItem(
        item_id="TEST-M800-OCEAN-SWIRL",
        title="Pelikan M800 Ocean Swirl fountain pen",
        url="https://www.penboard.de/",
        description=(
            "Pelikan M800 Ocean Swirl fountain pen "
            "in excellent condition"
        ),
        price=Decimal("850.00"),
        currency="EUR",
        condition="excellent",
        year="2017",
    )

    watchlist = Watchlist()
    notifier = NtfyNotifier()

    matches_found = 0

    for entry in watchlist.enabled():
        matched_terms = Watchlist.matches(
            entry,
            item.searchable_text,
        )

        if not matched_terms:
            continue

        matches_found += 1

        name = entry.get(
            "name",
            entry.get("id", "unknown"),
        )

        print(
            f"MATCH: {name} | "
            f"{', '.join(matched_terms)}"
        )

        notifier.send(
            title=f"TEST - PenWatch - {name}",
            message=build_message(
                item,
                matched_terms,
            ),
            url=item.url,
            priority="default",
        )

    print(f"Matches found: {matches_found}")


if __name__ == "__main__":
    main()
