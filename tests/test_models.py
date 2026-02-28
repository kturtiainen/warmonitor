"""Tests for warmonitor.models module."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from warmonitor.models import Event, Source


def test_event_model_valid():
    event = Event(
        id="abc123",
        title="Test Event",
        summary="A test summary",
        url="https://example.com/article",
        published=datetime(2025, 1, 1, tzinfo=timezone.utc),
        source_id="test_source",
        source_name="Test Source",
        credibility="HIGH",
        keywords_matched=["Iran"],
        severity=3,
    )
    assert event.id == "abc123"
    assert event.severity == 3
    assert event.credibility == "HIGH"
    assert event.keywords_matched == ["Iran"]


def test_event_model_missing_required_field():
    with pytest.raises(ValidationError):
        Event(
            id="abc123",
            # title missing
            summary="summary",
            url="https://example.com",
            published=datetime(2025, 1, 1, tzinfo=timezone.utc),
            source_id="src",
            source_name="Source",
            credibility="HIGH",
            keywords_matched=[],
            severity=1,
        )


def test_source_model_valid():
    source = Source(
        id="bbc_world",
        name="BBC News",
        url="https://feeds.bbci.co.uk/news/world/rss.xml",
        type="rss",
        keywords=["Iran", "Israel"],
        credibility="HIGH",
        color="green",
    )
    assert source.id == "bbc_world"
    assert source.status == "unknown"  # default value


def test_source_model_custom_status():
    source = Source(
        id="reuters",
        name="Reuters",
        url="https://feeds.reuters.com/reuters/worldNews",
        type="rss",
        keywords=["Iran"],
        credibility="HIGH",
        color="green",
        status="ok",
    )
    assert source.status == "ok"


def test_source_model_missing_required_field():
    with pytest.raises(ValidationError):
        Source(
            id="test",
            name="Test",
            # url missing
            type="rss",
            keywords=[],
            credibility="HIGH",
            color="green",
        )
