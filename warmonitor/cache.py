"""Persistent event cache for warmonitor.

Cache file: ``~/.warmonitor_cache.json``
Stores up to 500 events across restarts.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from warmonitor.models import Event

_CACHE_PATH = Path.home() / ".warmonitor_cache.json"
_CACHE_LIMIT = 500


def load_cache() -> list[Event]:
    """Load cached events from disk. Returns an empty list on any error."""
    if not _CACHE_PATH.exists():
        return []
    try:
        raw = _CACHE_PATH.read_text(encoding="utf-8")
        data = json.loads(raw)
        return [Event.model_validate(item) for item in data]
    except Exception as exc:
        print(f"warmonitor: warning: could not load cache {_CACHE_PATH}: {exc}", file=sys.stderr)
        return []


def save_cache(events: list[Event]) -> None:
    """Save events to the cache file, trimmed to the cache limit."""
    try:
        limited = events[:_CACHE_LIMIT]
        payload = json.dumps([e.model_dump(mode="json") for e in limited], indent=None)
        _CACHE_PATH.write_text(payload, encoding="utf-8")
    except Exception as exc:
        print(f"warmonitor: warning: could not save cache {_CACHE_PATH}: {exc}", file=sys.stderr)
