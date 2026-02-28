"""Tests for warmonitor.main module helpers."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from warmonitor.main import _calculate_defcon, _time_ago
from warmonitor.models import Event


def _make_event(severity: int, age_minutes: int = 0, url: str = "https://example.com/") -> Event:
    published = datetime.now(timezone.utc) - timedelta(minutes=age_minutes)
    return Event(
        id=f"ev-{severity}-{age_minutes}-{url}",
        title="Test event",
        summary="Summary",
        url=url,
        published=published,
        source_id="test",
        source_name="Test Source",
        credibility="HIGH",
        keywords_matched=["Iran"],
        severity=severity,
    )


# ── _time_ago ────────────────────────────────────────────────────────────────

def test_time_ago_seconds():
    dt = datetime.now(timezone.utc) - timedelta(seconds=30)
    assert _time_ago(dt) == "30s ago"


def test_time_ago_minutes():
    dt = datetime.now(timezone.utc) - timedelta(minutes=5)
    result = _time_ago(dt)
    assert result == "5m ago"


def test_time_ago_hours():
    dt = datetime.now(timezone.utc) - timedelta(hours=3)
    result = _time_ago(dt)
    assert result == "3h ago"


def test_time_ago_days():
    dt = datetime.now(timezone.utc) - timedelta(days=2)
    result = _time_ago(dt)
    assert result == "2d ago"


# ── _calculate_defcon ────────────────────────────────────────────────────────

def test_calculate_defcon_no_events():
    assert _calculate_defcon([]) == 5


def test_calculate_defcon_sev3_only():
    events = [_make_event(3)]
    assert _calculate_defcon(events) == 4


def test_calculate_defcon_single_sev4():
    events = [_make_event(4, age_minutes=60)]
    assert _calculate_defcon(events) == 3


def test_calculate_defcon_two_sev4_recent():
    events = [
        _make_event(4, age_minutes=10, url="https://a.com/"),
        _make_event(4, age_minutes=20, url="https://b.com/"),
    ]
    assert _calculate_defcon(events) == 2


def test_calculate_defcon_sev5_recent():
    events = [_make_event(5, age_minutes=5)]
    assert _calculate_defcon(events) == 1


def test_calculate_defcon_sev5_old():
    events = [_make_event(5, age_minutes=90)]
    assert _calculate_defcon(events) == 2
