from __future__ import annotations

from collections.abc import Callable

from apscheduler.schedulers.background import BackgroundScheduler


class SchedulerService:
    def __init__(self, interval_minutes: int, refresh_callback: Callable[[], object]):
        self._scheduler = BackgroundScheduler(timezone="UTC")
        self._interval_minutes = interval_minutes
        self._refresh_callback = refresh_callback

    def start(self) -> None:
        if self._scheduler.running:
            return
        self._scheduler.add_job(self._refresh_callback, "interval", minutes=self._interval_minutes, id="refresh_all")
        self._scheduler.start()

    def shutdown(self) -> None:
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)

    @property
    def running(self) -> bool:
        return bool(self._scheduler.running)
