"""HIMSETU — SQLite Database Connection & Schema Management."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS datasets (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    category TEXT NOT NULL,
    file_format TEXT NOT NULL,
    file_size_bytes INTEGER DEFAULT 0,
    min_lat REAL,
    max_lat REAL,
    min_lon REAL,
    max_lon REAL,
    crs TEXT,
    resolution_meters REAL,
    tags TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS processing_jobs (
    id TEXT PRIMARY KEY,
    job_type TEXT NOT NULL,
    status TEXT NOT NULL,
    parameters TEXT,
    output_path TEXT,
    error_message TEXT,
    created_at TEXT NOT NULL,
    completed_at TEXT
);
"""


class Database:
    """SQLite Database manager for HIMSETU metadata storage."""

    def __init__(self, db_path: str | Path = "data/himsetu.db") -> None:
        self.db_path = str(db_path)
        self._memory_conn: Optional[sqlite3.Connection] = None
        if self.db_path == ":memory:":
            self._memory_conn = sqlite3.connect(":memory:", check_same_thread=False)
            self._memory_conn.row_factory = sqlite3.Row
        else:
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.init_schema()

    def get_connection(self) -> sqlite3.Connection:
        """Create or return SQLite connection with dict-like row factory."""
        if self._memory_conn is not None:
            return self._memory_conn
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_schema(self) -> None:
        """Create database tables if they do not exist."""
        conn = self.get_connection()
        conn.executescript(SCHEMA_SQL)
        conn.commit()
