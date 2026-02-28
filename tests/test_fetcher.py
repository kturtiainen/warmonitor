"""Tests for warmonitor.fetcher module."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from warmonitor.fetcher import (
    _calculate_severity,
    _make_event_id,
    _match_keywords,
    _parse_published,
    fetch_all,
)
from warmonitor.models import Event, Source


def test_calculate_severity_level5():
    assert _calculate_severity("Iran launched a nuclear strike") == 5


def test_calculate_severity_level4():
    assert _calculate_severity("Missile fired at US troops") == 4


def test_calculate_severity_level3():
    assert _calculate_severity("New sanctions imposed amid diplomatic talks with envoy") == 3


def test_calculate_severity_level2():
    assert _calculate_severity("Talks and negotiations underway in Geneva") == 2


def test_calculate_severity_level1():
    assert _calculate_severity("Weather forecast: sunny skies") == 1


def test_calculate_severity_case_insensitive():
    assert _calculate_severity("ATTACK on facility") == 5


def test_match_keywords_found():
    result = _match_keywords("Iran launches drone strike", ["Iran", "drone", "UK"])
    assert "Iran" in result
    assert "drone" in result
    assert "UK" not in result


def test_match_keywords_empty():
    assert _match_keywords("No relevant content here", ["Iran", "Israel"]) == []


def test_match_keywords_case_insensitive():
    result = _match_keywords("IRAN sanctions", ["iran"])
    assert "iran" in result


def test_parse_published_fallback():
    entry = MagicMock(spec=[])
    result = _parse_published(entry)
    # Should return a datetime close to now
    delta = abs((datetime.now(timezone.utc) - result).total_seconds())
    assert delta < 5


def test_parse_published_uses_published_parsed():
    entry = MagicMock()
    entry.published_parsed = (2025, 1, 15, 12, 0, 0, 0, 0, 0)
    result = _parse_published(entry)
    assert result == datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)


def test_parse_published_uses_updated_parsed_as_fallback():
    entry = MagicMock()
    entry.published_parsed = None
    entry.updated_parsed = (2025, 6, 1, 8, 30, 0, 0, 0, 0)
    result = _parse_published(entry)
    assert result == datetime(2025, 6, 1, 8, 30, 0, tzinfo=timezone.utc)


def test_make_event_id_same_url():
    id1 = _make_event_id("https://example.com/article/1")
    id2 = _make_event_id("https://example.com/article/1")
    assert id1 == id2


def test_make_event_id_different_urls():
    id1 = _make_event_id("https://example.com/article/1")
    id2 = _make_event_id("https://example.com/article/2")
    assert id1 != id2


def test_make_event_id_length():
    eid = _make_event_id("https://example.com/")
    assert len(eid) == 16


def _make_source(source_id: str = "test") -> Source:
    return Source(
        id=source_id,
        name="Test Source",
        url="https://example.com/rss",
        type="rss",
        keywords=["Iran", "missile"],
        credibility="HIGH",
        color="green",
    )


def _make_event(url: str, source_id: str = "test") -> Event:
    source = _make_source(source_id)
    return Event(
        id=_make_event_id(url),
        title="Test event",
        summary="Test summary",
        url=url,
        published=datetime(2025, 1, 1, tzinfo=timezone.utc),
        source_id=source.id,
        source_name=source.name,
        credibility=source.credibility,
        keywords_matched=["Iran"],
        severity=3,
    )


@pytest.mark.asyncio
async def test_fetch_all_deduplication():
    """fetch_all should deduplicate events with the same ID across sources."""
    url_shared = "https://example.com/shared"
    url_unique_a = "https://example.com/unique-a"
    url_unique_b = "https://example.com/unique-b"

    event_shared = _make_event(url_shared, "src_a")
    event_a = _make_event(url_unique_a, "src_a")
    event_b = _make_event(url_shared, "src_b")  # same URL → same ID
    event_c = _make_event(url_unique_b, "src_b")

    source_a = _make_source("src_a")
    source_b = _make_source("src_b")

    async def fake_fetch_source(client, source, source_status):
        if source.id == "src_a":
            return [event_shared, event_a]
        return [event_b, event_c]

    with patch("warmonitor.fetcher.fetch_source", side_effect=fake_fetch_source):
        status: dict[str, str] = {}
        result = await fetch_all([source_a, source_b], status)

    ids = [e.id for e in result]
    assert len(ids) == len(set(ids)), "Duplicate event IDs found in fetch_all result"
    assert len(result) == 3  # shared (once), unique_a, unique_b
