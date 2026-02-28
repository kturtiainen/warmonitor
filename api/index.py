"""Flask backend for Warmonitor — Vercel serverless entry point."""

from __future__ import annotations

import asyncio
import sys
import os

# Ensure the project root is on the path so warmonitor package can be imported
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import datetime, timezone

from flask import Flask, render_template

from warmonitor.fetcher import fetch_all
from warmonitor.models import Event
from warmonitor.sources import SOURCES

SEVERITY_LABEL = {5: "CRITICAL", 4: "HIGH", 3: "MEDIUM", 2: "LOW", 1: "INFO"}


def _calculate_defcon(events: list[Event]) -> int:
    now = datetime.now(timezone.utc)

    def recent(minutes: int) -> list[Event]:
        cutoff = now.timestamp() - minutes * 60
        return [e for e in events if e.published.timestamp() >= cutoff]

    last_30 = recent(30)
    last_120 = recent(120)

    sev5_30 = any(e.severity == 5 for e in last_30)
    sev5_120 = any(e.severity == 5 for e in last_120)
    sev4_30_count = sum(1 for e in last_30 if e.severity == 4)
    has_sev4 = any(e.severity == 4 for e in events)
    has_sev3 = any(e.severity == 3 for e in events)

    if sev5_30:
        return 1
    if sev5_120 or sev4_30_count >= 2:
        return 2
    if has_sev4:
        return 3
    if has_sev3:
        return 4
    return 5

_TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "..", "templates")
app = Flask(__name__, template_folder=_TEMPLATES_DIR)

SEVERITY_COLOR = {
    5: "critical",
    4: "high",
    3: "medium",
    2: "low",
    1: "info",
}


def _time_ago(dt: datetime) -> str:
    delta = datetime.now(timezone.utc) - dt
    total_seconds = int(delta.total_seconds())
    if total_seconds < 60:
        return f"{total_seconds}s ago"
    elif total_seconds < 3600:
        return f"{total_seconds // 60}m ago"
    elif total_seconds < 86400:
        return f"{total_seconds // 3600}h ago"
    else:
        return f"{total_seconds // 86400}d ago"


@app.route("/")
def index():
    source_status: dict[str, str] = {}
    events = asyncio.run(fetch_all(SOURCES, source_status))

    defcon = _calculate_defcon(events)
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    enriched_events = [
        {
            "title": e.title,
            "url": e.url,
            "source_name": e.source_name,
            "severity": e.severity,
            "severity_label": SEVERITY_LABEL[e.severity],
            "severity_color": SEVERITY_COLOR[e.severity],
            "age": _time_ago(e.published),
        }
        for e in events
    ]

    sources_info = [
        {
            "name": s.name,
            "status": source_status.get(s.id, "unknown"),
        }
        for s in SOURCES
    ]

    return render_template(
        "index.html",
        defcon=defcon,
        events=enriched_events,
        sources=sources_info,
        now=now_str,
    )
