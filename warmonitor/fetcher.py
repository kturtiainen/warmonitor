"""Async RSS feed fetcher for warmonitor."""

import asyncio
import hashlib
from datetime import datetime, timezone

import feedparser
import httpx

from warmonitor.models import Event, Source

MAX_EVENTS = 200

SEVERITY_KEYWORDS: list[tuple[int, list[str]]] = [
    (5, ["strike", "attack", "nuclear", "war", "explosion", "killed", "casualties"]),
    (4, ["missile", "drone", "retaliation", "military", "troops"]),
    (3, ["sanctions", "diplomacy", "threat", "warning"]),
    (2, ["talks", "negotiations", "meeting"]),
]


def _calculate_severity(text: str) -> int:
    lower = text.lower()
    for severity, keywords in SEVERITY_KEYWORDS:
        if any(kw.lower() in lower for kw in keywords):
            return severity
    return 1


def _match_keywords(text: str, keywords: list[str]) -> list[str]:
    lower = text.lower()
    return [kw for kw in keywords if kw.lower() in lower]


def _parse_published(entry: feedparser.FeedParserDict) -> datetime:
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        return datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
    if hasattr(entry, "updated_parsed") and entry.updated_parsed:
        return datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
    return datetime.now(timezone.utc)


def _make_event_id(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()[:16]


async def fetch_source(
    client: httpx.AsyncClient,
    source: Source,
    source_status: dict[str, str],
) -> list[Event]:
    source_status[source.id] = "fetching"
    try:
        response = await client.get(source.url, timeout=20.0, follow_redirects=True)
        response.raise_for_status()
        feed = feedparser.parse(response.text)
        events: list[Event] = []
        for entry in feed.entries:
            title = getattr(entry, "title", "") or ""
            summary = getattr(entry, "summary", "") or ""
            url = getattr(entry, "link", "") or ""
            if not url:
                continue
            combined = f"{title} {summary}"
            matched = _match_keywords(combined, source.keywords)
            if not matched:
                continue
            events.append(
                Event(
                    id=_make_event_id(url),
                    title=title,
                    summary=summary,
                    url=url,
                    published=_parse_published(entry),
                    source_id=source.id,
                    source_name=source.name,
                    credibility=source.credibility,
                    keywords_matched=matched,
                    severity=_calculate_severity(combined),
                )
            )
        source_status[source.id] = "ok"
        return events
    except Exception:
        source_status[source.id] = "error"
        return []


async def fetch_all(
    sources: list[Source],
    source_status: dict[str, str],
) -> list[Event]:
    async with httpx.AsyncClient(
        headers={"User-Agent": "warmonitor/0.1 (conflict-monitor)"}
    ) as client:
        results = await asyncio.gather(
            *[fetch_source(client, source, source_status) for source in sources],
            return_exceptions=False,
        )
    all_events: list[Event] = []
    seen: set[str] = set()
    for batch in results:
        for event in batch:
            if event.id not in seen:
                seen.add(event.id)
                all_events.append(event)
    all_events.sort(key=lambda e: e.published, reverse=True)
    return all_events[:MAX_EVENTS]
