from pathlib import Path

import yaml


class Watchlist:
    def __init__(self, path: str = "config/watchlist.yaml") -> None:
        self.path = Path(path)
        self.entries = self._load()

    def _load(self) -> list[dict]:
        if not self.path.exists():
            raise FileNotFoundError(
                f"Watchlist configuration not found: {self.path}"
            )

        with self.path.open("r", encoding="utf-8") as file:
            config = yaml.safe_load(file) or {}

        entries = config.get("watchlists", [])

        if not isinstance(entries, list):
            raise ValueError("'watchlists' must be a list.")

        return entries

    def enabled(self) -> list[dict]:
        return [
            entry
            for entry in self.entries
            if entry.get("enabled", False)
        ]

    @staticmethod
    def matches(entry: dict, text: str) -> list[str]:
        text_normalized = text.casefold()

        matches = []

        for keyword in entry.get("keywords", []):
            if keyword.casefold() in text_normalized:
                matches.append(keyword)

        return matches
