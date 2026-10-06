from watchlist import Watchlist


def run_test(
    name: str,
    entry: dict,
    text: str,
    should_match: bool,
) -> None:
    matches = Watchlist.matches(entry, text)
    matched = bool(matches)

    status = "PASS" if matched == should_match else "FAIL"

    print(
        f"{status}: {name} | "
        f"expected={should_match}, actual={matched}, "
        f"matches={matches}"
    )


def main() -> None:
    pelikan_entry = {
        "include_all": ["pelikan"],
        "include_any": [
            "hell schildpatt",
            "light tortoise",
            "light tortoiseshell",
        ],
        "exclude": [
            "m400",
            "tortoise white",
        ],
    }

    # 1. Valid match
    run_test(
        "valid Pelikan Light Tortoise",
        pelikan_entry,
        "Vintage Pelikan 400 Light Tortoise Fountain Pen",
        True,
    )

    # 2. Required term 'Pelikan' missing
    run_test(
        "missing required Pelikan",
        pelikan_entry,
        "Vintage 400 Light Tortoise Fountain Pen",
        False,
    )

    # 3. Exclusion overrides otherwise valid match
    run_test(
        "excluded modern M400",
        pelikan_entry,
        "Pelikan M400 Light Tortoise Fountain Pen",
        False,
    )

    # 4. Existing legacy syntax must still work
    legacy_entry = {
        "keywords": [
            "soennecken",
            "sönnecken",
        ]
    }

    run_test(
        "legacy Soennecken",
        legacy_entry,
        "Vintage Soennecken 111 Extra Fountain Pen",
        True,
    )


if __name__ == "__main__":
    main()
