"""Market-hours guard: only act on weekdays, inside [market_open, market_close],
and not on NSE holidays. All time logic is in the configured exchange timezone."""
from __future__ import annotations
from datetime import datetime, time, timedelta
import pytz

from .config import load_holidays


def _parse_hhmm(s: str) -> time:
    h, m = s.split(":")
    return time(int(h), int(m))


class MarketCalendar:
    def __init__(self, config: dict):
        self.tz = pytz.timezone(config["timezone"])
        self.open = _parse_hhmm(config["market_open"])
        self.close = _parse_hhmm(config["market_close"])
        self.holidays = load_holidays()

    def now(self) -> datetime:
        return datetime.now(self.tz)

    def is_holiday(self, dt: datetime | None = None) -> bool:
        dt = dt or self.now()
        return dt.strftime("%Y-%m-%d") in self.holidays

    def is_weekend(self, dt: datetime | None = None) -> bool:
        dt = dt or self.now()
        return dt.weekday() >= 5  # 5=Sat, 6=Sun

    def is_trading_day(self, dt: datetime | None = None) -> bool:
        dt = dt or self.now()
        return not (self.is_weekend(dt) or self.is_holiday(dt))

    def is_open(self, dt: datetime | None = None) -> bool:
        """True only during the cash session on a valid trading day."""
        dt = dt or self.now()
        if not self.is_trading_day(dt):
            return False
        return self.open <= dt.time() <= self.close

    def session_close_dt(self, dt: datetime | None = None) -> datetime:
        dt = dt or self.now()
        return self.tz.localize(datetime.combine(dt.date(), self.close)) \
            if dt.tzinfo is None else dt.replace(hour=self.close.hour,
                                                 minute=self.close.minute,
                                                 second=0, microsecond=0)

    def status(self, dt: datetime | None = None) -> str:
        dt = dt or self.now()
        if self.is_weekend(dt):
            return "CLOSED (weekend)"
        if self.is_holiday(dt):
            return "CLOSED (holiday)"
        if dt.time() < self.open:
            return "PRE-OPEN"
        if dt.time() > self.close:
            return "CLOSED (after-hours)"
        return "OPEN"
