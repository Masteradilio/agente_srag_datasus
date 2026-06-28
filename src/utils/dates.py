from datetime import datetime
from zoneinfo import ZoneInfo

DEFAULT_TIMEZONE = "America/Sao_Paulo"


def utc_now() -> datetime:
    return datetime.now(tz=ZoneInfo("UTC"))


def now_in_timezone(timezone: str = DEFAULT_TIMEZONE) -> datetime:
    return datetime.now(tz=ZoneInfo(timezone))


def generate_run_id(timezone: str = DEFAULT_TIMEZONE, now: datetime | None = None) -> str:
    timestamp = now.astimezone(ZoneInfo(timezone)) if now else now_in_timezone(timezone)
    return timestamp.strftime("%Y%m%dT%H%M%S%z")
