from __future__ import annotations

import json
from pathlib import Path

from app.db import get_connection
from app.services.feed_service import NormalizedFeedItem


class FeedRepository:
    def __init__(self, database_path: Path):
        self.database_path = database_path

    def save_items(self, items: list[NormalizedFeedItem]) -> int:
        if not items:
            return 0

        inserted = 0
        with get_connection(self.database_path) as conn:
            for item in items:
                cursor = conn.execute(
                    """
                    INSERT OR IGNORE INTO feed_items
                    (source_id, title, summary, url, published_at, symbol, tags_json, item_hash)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        item.source_id,
                        item.title,
                        item.summary,
                        item.url,
                        item.published_at,
                        item.symbol,
                        json.dumps(item.tags, ensure_ascii=True),
                        item.item_hash,
                    ),
                )
                inserted += cursor.rowcount
        return inserted

    def list_items(
        self,
        source_id: str | None,
        symbol: str | None,
        tag: str | None,
        limit: int,
        offset: int,
    ) -> list[dict]:
        params: list = []
        where_clauses: list[str] = []

        if source_id:
            where_clauses.append("source_id = ?")
            params.append(source_id)

        if symbol:
            where_clauses.append("symbol = ?")
            params.append(symbol.upper())

        if tag:
            where_clauses.append("LOWER(tags_json) LIKE ?")
            params.append(f"%{tag.lower()}%")

        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        with get_connection(self.database_path) as conn:
            rows = conn.execute(
                f"""
                SELECT id, source_id, title, summary, url, published_at, symbol, tags_json
                FROM feed_items
                {where_sql}
                ORDER BY COALESCE(published_at, created_at) DESC
                LIMIT ? OFFSET ?
                """,
                [*params, limit, offset],
            ).fetchall()

        output = []
        for row in rows:
            item = dict(row)
            item["tags"] = json.loads(item.pop("tags_json") or "[]")
            output.append(item)
        return output

    def newest_published_at(self) -> str | None:
        with get_connection(self.database_path) as conn:
            row = conn.execute(
                """
                SELECT COALESCE(MAX(published_at), MAX(created_at)) AS newest
                FROM feed_items
                """
            ).fetchone()
        return row["newest"] if row else None
