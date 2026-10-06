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
    def _contains(text: str, term: str) -> bool:
        return term.casefold() in text.casefold()

    @classmethod
    def matches(cls, entry: dict, text: str) -> list[str]:
        """
        Match text against a watchlist entry.

        Supported rules:

        keywords:
            Legacy mode. At least one keyword must match.

        include_any:
            At least one term must match.

        include_all:
            Every term must match.

        exclude:
            If any term matches, the complete entry is rejected.
        """

        # Exclusions always take precedence.
        for term in entry.get("exclude", []):
            if cls._contains(text, term):
                return []

        include_all = entry.get("include_all", [])
        for term in include_all:
            if not cls._contains(text, term):
                return []

        include_any = entry.get("include_any", [])

        # Backwards compatibility with existing watchlists.
        legacy_keywords = entry.get("keywords", [])

        any_terms = include_any or legacy_keywords

        matched_terms = [
            term
            for term in any_terms
            if cls._contains(text, term)
        ]

        if any_terms and not matched_terms:
            return []

        # Prevent an empty rule set from matching everything.
        if not any_terms and not include_all:
            return []

        matched_all = [
            term
            for term in include_all
            if cls._contains(text, term)
        ]

        return matched_all + matched_terms
