from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_repo_root() -> Path:
    current = Path(__file__).resolve()
    for candidate in [current] + list(current.parents):
        if (candidate / "configs").exists():
            return candidate
    return Path.cwd()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="APP_", env_file=".env", extra="ignore")

    app_name: str = "OpenBB Personal Information Platform API"
    environment: str = "development"
    refresh_interval_minutes: int = 5
    manual_refresh_cooldown_seconds: int = 60
    frontend_origin: str = "http://localhost:5173"

    database_path: Path = Field(default_factory=lambda: _default_repo_root() / "data" / "openbb_platform.db")
    watchlist_path: Path = Field(default_factory=lambda: _default_repo_root() / "configs" / "watchlist.yaml")
    feeds_path: Path = Field(default_factory=lambda: _default_repo_root() / "configs" / "feeds.yaml")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.database_path.parent.mkdir(parents=True, exist_ok=True)
    return settings
