from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from learning_ops.config import DomainError


def utc(value: datetime | str) -> datetime:
    value = (
        datetime.fromisoformat(value.replace("Z", "+00:00")) if isinstance(value, str) else value
    )
    if value.tzinfo is None:
        raise DomainError("Time must include an explicit UTC offset.")
    return value.astimezone(UTC).replace(microsecond=0)


def stamp(value: datetime | str) -> str:
    return utc(value).strftime("%Y-%m-%dT%H:%M:%SZ")


class SystemClock:
    def now(self):
        return datetime.now(UTC).replace(microsecond=0)


@dataclass
class FixedClock:
    value: datetime

    def now(self):
        return utc(self.value)


def local_to_utc(value: datetime, timezone: str, fold: int | None = None) -> datetime:
    if value.tzinfo is not None:
        raise DomainError("Enter a local time without an offset, and select the timezone.")
    zone = ZoneInfo(timezone)
    candidates = {}
    for choice in (0, 1):
        candidate = value.replace(tzinfo=zone, fold=choice).astimezone(UTC)
        if candidate.astimezone(zone).replace(tzinfo=None) == value:
            candidates[choice] = candidate
    if not candidates:
        raise DomainError("This local time does not exist due to daylight saving time.")
    if len(set(candidates.values())) > 1 and fold is None:
        raise DomainError("Ambiguous daylight saving time: choose first or second occurrence.")
    if fold not in (None, 0, 1):
        raise DomainError("Occurrence must be first (0) or second (1).")
    return candidates[0 if fold is None else fold]


def date_bounds(start: date, end: date, timezone: str):
    if end < start:
        raise DomainError("End date must not precede start date.")
    return (
        stamp(local_to_utc(datetime.combine(start, time.min), timezone)),
        stamp(local_to_utc(datetime.combine(end + timedelta(days=1), time.min), timezone)),
    )
