from datetime import UTC, datetime, timedelta, timezone

from utils.clock import ensure_utc, utc_now


def test_utc_now_is_timezone_aware() -> None:
    assert utc_now().tzinfo is UTC


def test_ensure_utc_assumes_utc_for_naive_values() -> None:
    naive = datetime(2026, 9, 11, 14, 30)

    assert ensure_utc(naive) == datetime(2026, 9, 11, 14, 30, tzinfo=UTC)


def test_ensure_utc_converts_other_offsets() -> None:
    bogota = timezone(timedelta(hours=-5))
    aware = datetime(2026, 9, 11, 9, 30, tzinfo=bogota)

    assert ensure_utc(aware) == datetime(2026, 9, 11, 14, 30, tzinfo=UTC)
