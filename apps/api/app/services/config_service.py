from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class WatchlistItem:
    symbol: str
    display_name: str
    enabled: bool
    priority: int


@dataclass
class FeedSource:
    source_id: str
    name: str
    url: str
    category: str
    enabled: bool
    poll_interval_override: int | None = None


def _read_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fp:
        raw = yaml.safe_load(fp) or {}
    if not isinstance(raw, dict):
        raise ValueError(f"Invalid YAML format in {path}")
    return raw


def load_watchlist(path: Path) -> list[WatchlistItem]:
    raw = _read_yaml(path)
    rows = raw.get("watchlist", [])
    output: list[WatchlistItem] = []
    for row in rows:
        output.append(
            WatchlistItem(
                symbol=str(row["symbol"]).upper(),
                display_name=str(row.get("display_name") or row["symbol"]).strip(),
                enabled=bool(row.get("enabled", True)),
                priority=int(row.get("priority", 100)),
            )
        )
    output.sort(key=lambda item: item.priority)
    return [item for item in output if item.enabled]


def load_feeds(path: Path) -> list[FeedSource]:
    raw = _read_yaml(path)
    rows = raw.get("feeds", [])
    output: list[FeedSource] = []
    for row in rows:
        output.append(
            FeedSource(
                source_id=str(row["source_id"]).strip(),
                name=str(row.get("name") or row["source_id"]).strip(),
                url=str(row["url"]).strip(),
                category=str(row.get("category", "general")).strip(),
                enabled=bool(row.get("enabled", True)),
                poll_interval_override=(
                    int(row["poll_interval_override"]) if row.get("poll_interval_override") is not None else None
                ),
            )
        )
    return [source for source in output if source.enabled]
