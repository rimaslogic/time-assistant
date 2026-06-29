"""Tests for engine.timeutil — UTC → tenant-timezone conversion."""
import pytest
from engine.timeutil import to_zone


def test_z_suffix_converts_to_warsaw():
    result = to_zone("2026-06-25T04:10:00Z", "Europe/Warsaw")
    assert result.startswith("2026-06-25T06:10:00"), repr(result)
    assert "+02:00" in result, repr(result)


def test_utc_offset_input_converts_to_warsaw():
    result = to_zone("2026-06-25T04:10:00+00:00", "Europe/Warsaw")
    assert result.startswith("2026-06-25T06:10:00"), repr(result)
    assert "+02:00" in result, repr(result)


def test_naive_input_treated_as_utc():
    result = to_zone("2026-06-25T04:10:00", "Europe/Warsaw")
    assert result.startswith("2026-06-25T06:10:00"), repr(result)
    assert "+02:00" in result, repr(result)


def test_unknown_tz_falls_back_to_utc():
    result = to_zone("2026-06-25T04:10:00Z", "Mars/Phobos")
    assert "+00:00" in result, repr(result)
    # no exception raised
