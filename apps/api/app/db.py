from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


def _connect(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


@contextmanager
def get_connection(path: Path) -> Iterator[sqlite3.Connection]:
    conn = _connect(path)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db(path: Path) -> None:
    with get_connection(path) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS feed_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id TEXT NOT NULL,
                title TEXT NOT NULL,
                summary TEXT,
                url TEXT NOT NULL,
                published_at TEXT,
                symbol TEXT,
                tags_json TEXT NOT NULL,
                item_hash TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE INDEX IF NOT EXISTS idx_feed_published_at ON feed_items(published_at DESC);
            CREATE INDEX IF NOT EXISTS idx_feed_symbol ON feed_items(symbol);
            CREATE INDEX IF NOT EXISTS idx_feed_source_id ON feed_items(source_id);

            CREATE TABLE IF NOT EXISTS market_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                price REAL,
                change_percent REAL,
                volume REAL,
                fetched_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_market_symbol_time ON market_snapshots(symbol, fetched_at DESC);

            CREATE TABLE IF NOT EXISTS asset_overviews (
                symbol TEXT PRIMARY KEY,
                display_name TEXT,
                last_price REAL,
                change_percent REAL,
                volume REAL,
                pe_ratio REAL,
                market_cap REAL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS ingestion_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_type TEXT NOT NULL,
                status TEXT NOT NULL,
                message TEXT,
                started_at TEXT NOT NULL,
                finished_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_ingestion_job_time ON ingestion_runs(job_type, finished_at DESC);
            """
        )
