"""SQLite 状态库：记录已见/已推送指纹与每次运行的游标。"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path


class Store:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with closing(self._conn()) as conn, conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS seen_events (
                    id TEXT PRIMARY KEY,
                    source_id TEXT,
                    title TEXT,
                    url TEXT,
                    first_seen TEXT,
                    pushed INTEGER DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS source_cursor (
                    source_id TEXT PRIMARY KEY,
                    last_success TEXT
                );
                CREATE TABLE IF NOT EXISTS runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    started_at TEXT,
                    collected INTEGER,
                    after_dedup INTEGER,
                    pushed INTEGER,
                    note TEXT
                );
                """
            )

    def is_seen(self, event_id: str) -> bool:
        with closing(self._conn()) as conn:
            row = conn.execute(
                "SELECT 1 FROM seen_events WHERE id = ?", (event_id,)
            ).fetchone()
            return row is not None

    def mark_seen(self, event_id: str, source_id: str, title: str, url: str) -> None:
        with closing(self._conn()) as conn, conn:
            conn.execute(
                "INSERT OR IGNORE INTO seen_events (id, source_id, title, url, first_seen)"
                " VALUES (?, ?, ?, ?, ?)",
                (event_id, source_id, title, url, _now()),
            )

    def mark_pushed(self, event_ids: list[str]) -> None:
        if not event_ids:
            return
        with closing(self._conn()) as conn, conn:
            conn.executemany(
                "UPDATE seen_events SET pushed = 1 WHERE id = ?",
                [(eid,) for eid in event_ids],
            )

    def get_cursor(self, source_id: str) -> datetime | None:
        with closing(self._conn()) as conn:
            row = conn.execute(
                "SELECT last_success FROM source_cursor WHERE source_id = ?",
                (source_id,),
            ).fetchone()
            if row and row["last_success"]:
                return datetime.fromisoformat(row["last_success"])
            return None

    def set_cursor(self, source_id: str, ts: datetime) -> None:
        with closing(self._conn()) as conn, conn:
            conn.execute(
                "INSERT INTO source_cursor (source_id, last_success) VALUES (?, ?)"
                " ON CONFLICT(source_id) DO UPDATE SET last_success = excluded.last_success",
                (source_id, ts.isoformat()),
            )

    def record_run(self, collected: int, after_dedup: int, pushed: int, note: str = "") -> None:
        with closing(self._conn()) as conn, conn:
            conn.execute(
                "INSERT INTO runs (started_at, collected, after_dedup, pushed, note)"
                " VALUES (?, ?, ?, ?, ?)",
                (_now(), collected, after_dedup, pushed, note),
            )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
