from datetime import datetime
from zoneinfo import ZoneInfo

from utils.dates import generate_run_id, now_in_timezone


def test_generate_run_id_is_stable_for_fixed_datetime() -> None:
    fixed_now = datetime(2026, 6, 27, 20, 30, 1, tzinfo=ZoneInfo("America/Sao_Paulo"))

    assert generate_run_id(now=fixed_now) == "20260627T203001-0300"


def test_now_in_timezone_uses_requested_timezone() -> None:
    current = now_in_timezone("America/Sao_Paulo")

    assert current.tzinfo is not None
    assert current.utcoffset() is not None

