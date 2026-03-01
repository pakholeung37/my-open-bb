from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable

import feedparser
from dateutil import parser as date_parser

from app.services.config_service import FeedSource, WatchlistItem

logger = logging.getLogger(__name__)


@dataclass
class NormalizedFeedItem:
    source_id: str
    title: str
    summary: str | None
    url: str
    published_at: str | None
    symbol: str | None
    tags: list[str]
    item_hash: str


def _parse_published(entry: dict) -> str | None:
    raw = entry.get("published") or entry.get("updated")
    if not raw:
        return None
    try:
        return date_parser.parse(raw).astimezone(timezone.utc).isoformat()
    except (TypeError, ValueError, OverflowError):
        return None


def _extract_symbol(text: str, watchlist_symbols: set[str]) -> str | None:
    for symbol in watchlist_symbols:
        if re.search(rf"\\b{re.escape(symbol)}\\b", text):
            return symbol
    return None


def _extract_tags(entry: dict, default_category: str) -> list[str]:
    tags: list[str] = []
    for tag in entry.get("tags", []):
        term = tag.get("term") if isinstance(tag, dict) else None
        if term:
            tags.append(str(term).lower())
    if default_category:
        tags.append(default_category.lower())
    deduped = sorted({tag.strip() for tag in tags if tag and tag.strip()})
    return deduped


def _hash_item(source_id: str, title: str, url: str, published_at: str | None) -> str:
    payload = f"{source_id}|{title}|{url}|{published_at or ''}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def fetch_and_normalize(sources: Iterable[FeedSource], watchlist: list[WatchlistItem]) -> list[NormalizedFeedItem]:
    output: list[NormalizedFeedItem] = []
    watchlist_symbols = {item.symbol for item in watchlist}

    for source in sources:
        parsed = feedparser.parse(source.url)
        if parsed.bozo:
            logger.warning("Feed parse warning for %s", source.source_id)

        for entry in parsed.entries[:50]:
            title = str(entry.get("title", "")).strip()
            if not title:
                continue

            summary = str(entry.get("summary", "")).strip() or None
            url = str(entry.get("link", "")).strip()
            if not url:
                continue

            published_at = _parse_published(entry)
            searchable_text = f"{title} {summary or ''}"
            symbol = _extract_symbol(searchable_text.upper(), watchlist_symbols)
            tags = _extract_tags(entry, source.category)
            item_hash = _hash_item(source.source_id, title, url, published_at)

            output.append(
                NormalizedFeedItem(
                    source_id=source.source_id,
                    title=title,
                    summary=summary,
                    url=url,
                    published_at=published_at,
                    symbol=symbol,
                    tags=tags,
                    item_hash=item_hash,
                )
            )

    output.sort(key=lambda item: item.published_at or datetime.now(timezone.utc).isoformat(), reverse=True)
    return output
