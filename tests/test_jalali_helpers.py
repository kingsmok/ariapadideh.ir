"""
Tests for Jalali date helpers and Persian numeral formatting.
"""
from datetime import datetime
from app.utils.helpers import (
    format_jalali,
    format_jalali_date,
    format_jalali_human,
    to_jalali,
    to_persian_digits,
    to_english_digits,
)


def test_to_jalali_conversion():
    """Verify standard Gregorian to Jalali conversion."""
    gregorian_dt = datetime(2026, 3, 21, 10, 30, 0)
    jdt = to_jalali(gregorian_dt)
    assert jdt is not None
    assert jdt.year == 1405
    assert jdt.month == 1
    assert jdt.day == 1


def test_format_jalali():
    """Verify formatted string output with Persian numerals."""
    dt = datetime(2026, 3, 21, 15, 45, 0)
    formatted = format_jalali(dt, fmt="%Y/%m/%d - %H:%M", persian_digits=True)
    assert "۱۴۰۵" in formatted
    assert "۱۵:۴۵" in formatted


def test_format_jalali_human():
    """Verify human readable month string in Persian."""
    dt = datetime(2026, 3, 21)
    human_date = format_jalali_human(dt, include_time=False, persian_digits=True)
    assert "فروردین" in human_date
    assert "۱۴۰۵" in human_date


def test_digit_conversion_helpers():
    """Verify bidirectional digit translation between Persian and English."""
    assert to_persian_digits("1234567890") == "۱۲۳۴۵۶۷۸۹۰"
    assert to_english_digits("۱۲۳۴۵۶۷۸۹۰") == "1234567890"
