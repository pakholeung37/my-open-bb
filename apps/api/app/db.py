from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import duckdb


def _column_names(description: list[tuple] | None) -> list[str]:
    if not description:
        return []
    return [str(column[0]) for column in description]


def _connect(path: Path) -> duckdb.DuckDBPyConnection:
    return duckdb.connect(str(path))


@contextmanager
def get_connection(path: Path) -> Iterator[duckdb.DuckDBPyConnection]:
    conn = _connect(path)
    try:
        yield conn
    finally:
        conn.close()


def fetchall_dicts(conn: duckdb.DuckDBPyConnection, query: str, params: list | tuple | None = None) -> list[dict]:
    cursor = conn.execute(query, params or [])
    columns = _column_names(cursor.description)
    rows = cursor.fetchall()
    return [dict(zip(columns, row, strict=False)) for row in rows]


def fetchone_dict(conn: duckdb.DuckDBPyConnection, query: str, params: list | tuple | None = None) -> dict | None:
    cursor = conn.execute(query, params or [])
    columns = _column_names(cursor.description)
    row = cursor.fetchone()
    if row is None:
        return None
    return dict(zip(columns, row, strict=False))


def init_db(path: Path) -> None:
    with get_connection(path) as conn:
        conn.execute("CREATE SEQUENCE IF NOT EXISTS feed_items_id_seq START 1")
        conn.execute("CREATE SEQUENCE IF NOT EXISTS ingestion_runs_id_seq START 1")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS feed_items (
                id BIGINT PRIMARY KEY DEFAULT nextval('feed_items_id_seq'),
                source_id VARCHAR NOT NULL,
                title VARCHAR NOT NULL,
                summary VARCHAR,
                url VARCHAR NOT NULL,
                published_at TIMESTAMP,
                symbol VARCHAR,
                tags_json VARCHAR NOT NULL,
                item_hash VARCHAR NOT NULL UNIQUE,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_feed_published_at ON feed_items(published_at DESC)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_feed_symbol ON feed_items(symbol)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_feed_source_id ON feed_items(source_id)")

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS market_quotes (
                symbol VARCHAR NOT NULL,
                price DOUBLE,
                change_percent DOUBLE,
                volume DOUBLE,
                pe_ratio DOUBLE,
                market_cap DOUBLE,
                provider VARCHAR NOT NULL,
                fetched_at TIMESTAMP NOT NULL
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_market_quotes_symbol_time ON market_quotes(symbol, fetched_at DESC)")

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS asset_overviews (
                symbol VARCHAR PRIMARY KEY,
                display_name VARCHAR,
                last_price DOUBLE,
                change_percent DOUBLE,
                volume DOUBLE,
                pe_ratio DOUBLE,
                market_cap DOUBLE,
                provider VARCHAR NOT NULL,
                updated_at TIMESTAMP NOT NULL
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS market_bars (
                symbol VARCHAR NOT NULL,
                interval VARCHAR NOT NULL,
                ts TIMESTAMP NOT NULL,
                open DOUBLE,
                high DOUBLE,
                low DOUBLE,
                close DOUBLE,
                volume DOUBLE,
                provider VARCHAR NOT NULL,
                fetched_at TIMESTAMP NOT NULL,
                PRIMARY KEY(symbol, interval, ts)
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS ingestion_runs (
                id BIGINT PRIMARY KEY DEFAULT nextval('ingestion_runs_id_seq'),
                job_type VARCHAR NOT NULL,
                status VARCHAR NOT NULL,
                message VARCHAR,
                started_at TIMESTAMP NOT NULL,
                finished_at TIMESTAMP NOT NULL
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_ingestion_job_time ON ingestion_runs(job_type, finished_at DESC)")
