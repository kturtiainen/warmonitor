"""Configurable sources loader for warmonitor.

Loads user-defined sources from ``~/.warmonitor.toml`` and merges them with
(or replaces) the built-in ``SOURCES`` list.
"""

from __future__ import annotations

import sys
from pathlib import Path

from warmonitor.models import Source
from warmonitor.sources import SOURCES as DEFAULT_SOURCES

_CONFIG_PATH = Path.home() / ".warmonitor.toml"


def load_sources() -> list[Source]:
    """Return the active source list, merging config file if present."""
    if not _CONFIG_PATH.exists():
        return list(DEFAULT_SOURCES)

    try:
        if sys.version_info >= (3, 11):
            import tomllib
        else:
            import tomli as tomllib  # type: ignore[no-redef]

        with open(_CONFIG_PATH, "rb") as fh:
            config = tomllib.load(fh)
    except Exception as exc:
        print(f"warmonitor: warning: could not load {_CONFIG_PATH}: {exc}", file=sys.stderr)
        return list(DEFAULT_SOURCES)

    replace_defaults = config.get("replace_defaults", False)
    raw_sources: list[dict] = config.get("sources", [])

    custom: list[Source] = []
    for raw in raw_sources:
        try:
            custom.append(Source(**raw))
        except Exception as exc:
            print(f"warmonitor: warning: skipping invalid source {raw!r}: {exc}", file=sys.stderr)

    if replace_defaults:
        return custom if custom else list(DEFAULT_SOURCES)

    # Merge: custom sources take priority (by id); then append defaults not overridden
    custom_ids = {s.id for s in custom}
    merged = custom + [s for s in DEFAULT_SOURCES if s.id not in custom_ids]
    return merged
