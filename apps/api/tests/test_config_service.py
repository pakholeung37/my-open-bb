from pathlib import Path

from app.services.config_service import load_feeds, load_watchlist


def test_load_watchlist_from_default_config():
    path = Path(__file__).resolve().parents[3] / "configs" / "watchlist.yaml"
    watchlist = load_watchlist(path)
    assert len(watchlist) >= 1
    assert watchlist[0].symbol


def test_load_feeds_from_default_config():
    path = Path(__file__).resolve().parents[3] / "configs" / "feeds.yaml"
    feeds = load_feeds(path)
    assert len(feeds) >= 1
    assert feeds[0].url.startswith("http")
