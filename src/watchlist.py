import re
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

    @staticmethod
    def _contains_exact(text: str, term: str) -> bool:
        """
        Match a term as a standalone token.

        This prevents model '11' from matching '111',
        while still allowing punctuation around the model number.
        """
        pattern = rf"(?<!\w){re.escape(term)}(?!\w)"
        return re.search(pattern, text, flags=re.IGNORECASE) is not None

    @classmethod
    def _term_matches(cls, text: str, rule) -> bool:
        """
        A rule may be either a plain string or a dictionary:

        - "soennecken"
        - exact: "11"
        """
        if isinstance(rule, str):
            return cls._contains(text, rule)

        if isinstance(rule, dict) and "exact" in rule:
            return cls._contains_exact(text, str(rule["exact"]))

        raise ValueError(f"Invalid watchlist rule: {rule!r}")

    @staticmethod
    def _rule_label(rule) -> str:
        if isinstance(rule, str):
            return rule

        if isinstance(rule, dict) and "exact" in rule:
            return str(rule["exact"])

        return str(rule)

    @classmethod
    def matches(cls, entry: dict, text: str) -> list[str]:
        """
        Supported rules:

        keywords:
            Legacy mode. At least one keyword must match.

        include_any:
            At least one term must match.

        include_all:
            Every term must match.

        include_groups:
            Each group must produce at least one match.
            This enables:
            A AND (B OR C) AND (D OR E)

        exclude:
            Any matching exclusion rejects the complete entry.

        Rules can be plain strings or exact-token rules:
            - "pelikan"
            - exact: "400"
        """

        # Exclusions always take precedence.
        for rule in entry.get("exclude", []):
            if cls._term_matches(text, rule):
                return []

        matched_terms = []

        # Every include_all rule is mandatory.
        for rule in entry.get("include_all", []):
            if not cls._term_matches(text, rule):
                return []
            matched_terms.append(cls._rule_label(rule))

        # Every include_group must contain at least one match.
        include_groups = entry.get("include_groups", [])

        for group in include_groups:
            group_matches = [
                rule
                for rule in group
                if cls._term_matches(text, rule)
            ]

            if not group_matches:
                return []

            matched_terms.extend(
                cls._rule_label(rule)
                for rule in group_matches
            )

        # include_any or legacy keywords.
        include_any = entry.get("include_any", [])
        legacy_keywords = entry.get("keywords", [])
        any_rules = include_any or legacy_keywords

        if any_rules:
            any_matches = [
                rule
                for rule in any_rules
                if cls._term_matches(text, rule)
            ]

            if not any_matches:
                return []

            matched_terms.extend(
                cls._rule_label(rule)
                for rule in any_matches
            )

        # Empty rules must never match everything.
        if (
            not entry.get("include_all")
            and not include_groups
            and not any_rules
        ):
            return []

        # Remove duplicates while preserving order.
        return list(dict.fromkeys(matched_terms))
