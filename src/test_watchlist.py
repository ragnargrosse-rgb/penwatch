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

    # ---------------------------------------------------------
    # Soennecken 111 / 222 fountain pens and 11 / 22 pencils
    # ---------------------------------------------------------

    soennecken_entry = {
        "include_all": ["soennecken"],
        "include_groups": [
            [
                {"exact": "111"},
                {"exact": "222"},
                {"exact": "11"},
                {"exact": "22"},
            ]
        ],
    }

    run_test(
        "Soennecken 111",
        soennecken_entry,
        "Vintage Soennecken 111 fountain pen",
        True,
    )

    run_test(
        "Soennecken 222",
        soennecken_entry,
        "Soennecken 222 Kolbenfueller",
        True,
    )

    run_test(
        "Soennecken pencil 11",
        soennecken_entry,
        "Vintage Soennecken 11 mechanical pencil",
        True,
    )

    run_test(
        "Soennecken pencil 22",
        soennecken_entry,
        "Soennecken Bleistift Modell 22",
        True,
    )

    # 11 must not match 111 accidentally
    matches = Watchlist.matches(
        soennecken_entry,
        "Soennecken 111 fountain pen",
    )

    exact_test = (
        "111" in matches
        and "11" not in matches
    )

    print(
        f"{'PASS' if exact_test else 'FAIL'}: "
        f"111 does not also match 11 | matches={matches}"
    )

    # 22 must not match 222 accidentally
    matches = Watchlist.matches(
        soennecken_entry,
        "Soennecken 222 fountain pen",
    )

    exact_test = (
        "222" in matches
        and "22" not in matches
    )

    print(
        f"{'PASS' if exact_test else 'FAIL'}: "
        f"222 does not also match 22 | matches={matches}"
    )

    run_test(
        "wrong Soennecken model",
        soennecken_entry,
        "Vintage Soennecken 333 fountain pen",
        False,
    )

    run_test(
        "model without Soennecken",
        soennecken_entry,
        "Vintage fountain pen model 111",
        False,
    )

    # ---------------------------------------------------------
    # Multiple AND/OR groups
    # ---------------------------------------------------------

    pelikan_entry = {
        "include_all": ["pelikan"],
        "include_groups": [
            [
                {"exact": "140"},
                {"exact": "400"},
                {"exact": "400N"},
                {"exact": "400NN"},
            ],
            [
                "hell schildpatt",
                "light tortoise",
                "light tortoiseshell",
            ],
        ],
    }

    run_test(
        "Pelikan with model and colour",
        pelikan_entry,
        "Pelikan 400NN Light Tortoise fountain pen",
        True,
    )

    run_test(
        "Pelikan colour but no model",
        pelikan_entry,
        "Pelikan Light Tortoise fountain pen",
        False,
    )

    run_test(
        "Pelikan model but no colour",
        pelikan_entry,
        "Pelikan 400NN vintage fountain pen",
        False,
    )

    run_test(
        "model and colour but no Pelikan",
        pelikan_entry,
        "400NN Light Tortoise fountain pen",
        False,
    )

    # ---------------------------------------------------------
    # Legacy compatibility
    # ---------------------------------------------------------

    legacy_entry = {
        "keywords": [
            "soennecken",
            "sönnecken",
        ]
    }

    run_test(
        "legacy keyword syntax",
        legacy_entry,
        "Vintage Soennecken fountain pen",
        True,
    )


if __name__ == "__main__":
    main()
