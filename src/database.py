import sqlite3
from pathlib import Path


class Database:
    def __init__(self, path: str = "data/penwatch.db") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS seen_items (
                    source TEXT NOT NULL,
                    item_id TEXT NOT NULL,
                    watchlist_id TEXT NOT NULL,
                    title TEXT,
                    url TEXT,
                    first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (source, item_id, watchlist_id)
                )
                """
            )

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS source_items (
                    source TEXT NOT NULL,
                    item_id TEXT NOT NULL,
                    title TEXT,
                    url TEXT,
                    first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (source, item_id)
                )
                """
            )

    def has_seen(
        self,
        source: str,
        item_id: str,
        watchlist_id: str,
    ) -> bool:
        with self._connect() as connection:
            result = connection.execute(
                """
                SELECT 1
                FROM seen_items
                WHERE source = ?
                  AND item_id = ?
                  AND watchlist_id = ?
                LIMIT 1
                """,
                (source, item_id, watchlist_id),
            ).fetchone()

        return result is not None

    def mark_seen(
        self,
        source: str,
        item_id: str,
        watchlist_id: str,
        title: str,
        url: str,
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO seen_items
                    (source, item_id, watchlist_id, title, url)
                VALUES (?, ?, ?, ?, ?)
                """,
                (source, item_id, watchlist_id, title, url),
            )
    def has_source_item(
        self,
        source: str,
        item_id: str,
    ) -> bool:
        with self._connect() as connection:
            result = connection.execute(
                """
                SELECT 1
                FROM source_items
                WHERE source = ?
                  AND item_id = ?
                LIMIT 1
                """,
                (source, item_id),
            ).fetchone()

        return result is not None

    def mark_source_item(
        self,
        source: str,
        item_id: str,
        title: str,
        url: str,
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO source_items (
                    source,
                    item_id,
                    title,
                    url
                )
                VALUES (?, ?, ?, ?)
                ON CONFLICT(source, item_id)
                DO UPDATE SET
                    title = excluded.title,
                    url = excluded.url,
                    last_seen_at = CURRENT_TIMESTAMP
                """,
                (source, item_id, title, url),
            )
