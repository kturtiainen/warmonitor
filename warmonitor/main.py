"""Warmonitor — Live Iran–USA conflict terminal dashboard.

Entry point: `warmonitor` or `uv run warmonitor`.
"""

from __future__ import annotations

import webbrowser
from datetime import datetime, timezone

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import ScrollableContainer, Vertical, Horizontal
from textual.reactive import reactive
from textual.widgets import Label, Static

from warmonitor.cache import load_cache, save_cache
from warmonitor.config import load_sources
from warmonitor.fetcher import fetch_all
from warmonitor.models import Event

SOURCES = load_sources()
REFRESH_INTERVAL = 60  # seconds

SEVERITY_EMOJI = {5: "🔴", 4: "🟠", 3: "🟡", 2: "🔵", 1: "⚪"}
SEVERITY_CLASS = {
    5: "event-severity-critical",
    4: "event-severity-high",
    3: "event-severity-medium",
    2: "event-severity-low",
    1: "event-severity-info",
}
SEVERITY_LABEL = {5: "CRITICAL", 4: "HIGH", 3: "MEDIUM", 2: "LOW", 1: "INFO"}


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


class EventRow(Static):
    """A focusable event row that can open its URL in a browser."""

    can_focus = True

    def __init__(self, event: Event, renderable="", **kwargs) -> None:
        super().__init__(renderable, **kwargs)
        self._event = event

    def on_key(self, key_event) -> None:
        if key_event.key in ("enter", "o"):
            webbrowser.open(self._event.url)
            key_event.stop()


class WarmonitorApp(App):
    """Live Iran–USA conflict dashboard."""

    CSS_PATH = "app.tcss"

    BINDINGS = [
        Binding("r", "refresh", "Refresh", show=True),
        Binding("q", "quit", "Quit", show=True),
        Binding("f", "filter", "Filter ≥3", show=True),
        Binding("s", "sort_toggle", "Sort", show=True),
        Binding("o", "open_url", "Open URL", show=True),
    ]

    events_data: reactive[list[Event]] = reactive([], layout=True)
    source_status: dict[str, str] = {}
    filter_active: reactive[bool] = reactive(False)
    sort_by_severity: reactive[bool] = reactive(False)
    fetching: reactive[bool] = reactive(False)

    def compose(self) -> ComposeResult:
        # Header
        with Horizontal(id="header"):
            yield Label("🔴 WARMONITOR", id="header-title")
            yield Label("  Iran–USA Conflict Dashboard", id="header-subtitle")
            yield Label("", id="header-timestamp")
            yield Label(f"  AUTO-REFRESH: {REFRESH_INTERVAL}s", id="header-refresh")

        # Body
        with Horizontal(id="body"):
            # Left — Status
            with Vertical(id="status-panel"):
                yield Label("STATUS", id="status-panel-title")
                yield Label("DEFCON: 5", id="defcon-label")
                yield Label("Last event:\n—", id="last-event-label")
                yield Label("Events/hr:\n—", id="events-per-hour")
                yield Label("", id="severity-breakdown")

            # Center — Live Feed
            with Vertical(id="feed-panel"):
                yield Label("⚡ LIVE FEED", id="feed-panel-title")
                with ScrollableContainer(id="feed-container"):
                    yield Static(
                        "No matching events yet — waiting for feed update…",
                        id="no-events-msg",
                    )

            # Right — Sources
            with Vertical(id="sources-panel"):
                yield Label("SOURCES", id="sources-panel-title")
                for source in SOURCES:
                    self.source_status[source.id] = "unknown"
                    yield Label(f"🟡 {source.name}", id=f"src-{source.id}", classes="source-item")
                yield Static(
                    "\n[R] Refresh\n[Q] Quit\n[F] Filter\n[S] Sort",
                    id="keybindings",
                )

    async def on_mount(self) -> None:
        self.events_data = load_cache()
        self._update_timestamp()
        self.set_interval(1, self._update_timestamp)
        self.set_interval(REFRESH_INTERVAL, self.action_refresh)
        await self._do_fetch()

    def _update_timestamp(self) -> None:
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        try:
            self.query_one("#header-timestamp", Label).update(ts)
        except Exception:
            pass

    async def action_refresh(self) -> None:
        if not self.fetching:
            await self._do_fetch()

    async def _do_fetch(self) -> None:
        self.fetching = True
        self._set_all_sources_fetching()
        try:
            new_events = await fetch_all(SOURCES, self.source_status)
            # Merge with existing, keeping up to MAX_EVENTS
            new_ids = {e.id for e in new_events}
            merged = new_events + [e for e in self.events_data if e.id not in new_ids]
            merged.sort(key=lambda e: e.published, reverse=True)
            self.events_data = merged[:200]
            save_cache(self.events_data)
        finally:
            self.fetching = False
            self._update_source_indicators()
            self._refresh_feed()
            self._refresh_status()

    def _set_all_sources_fetching(self) -> None:
        for source in SOURCES:
            self.source_status[source.id] = "fetching"
            self._update_source_label(source.id)

    def _update_source_indicators(self) -> None:
        for source in SOURCES:
            self._update_source_label(source.id)

    def _update_source_label(self, source_id: str) -> None:
        status = self.source_status.get(source_id, "unknown")
        indicator = {"ok": "🟢", "error": "🔴", "fetching": "🟡", "unknown": "⚪"}.get(
            status, "⚪"
        )
        source = next((s for s in SOURCES if s.id == source_id), None)
        if source:
            try:
                self.query_one(f"#src-{source_id}", Label).update(
                    f"{indicator} {source.name}"
                )
            except Exception:
                pass

    def _get_display_events(self) -> list[Event]:
        events = self.events_data
        if self.filter_active:
            events = [e for e in events if e.severity >= 3]
        if self.sort_by_severity:
            events = sorted(events, key=lambda e: (-e.severity, -e.published.timestamp()))
        return events

    def _refresh_feed(self) -> None:
        container = self.query_one("#feed-container", ScrollableContainer)
        container.remove_children()

        display = self._get_display_events()
        if not display:
            container.mount(
                Static(
                    "No matching events yet — waiting for feed update…",
                    id="no-events-msg",
                )
            )
            return

        filter_note = " [FILTER ≥3 ACTIVE]" if self.filter_active else ""
        sort_note = " [SORTED BY SEVERITY]" if self.sort_by_severity else ""
        if filter_note or sort_note:
            container.mount(Static(f"{filter_note}{sort_note}", classes="event-severity-medium"))

        for event in display:
            emoji = SEVERITY_EMOJI[event.severity]
            sev_class = SEVERITY_CLASS[event.severity]
            age = _time_ago(event.published)
            text = f"{emoji} [{age}] {event.title}\n    ↳ {event.source_name}"
            container.mount(EventRow(event, text, classes=f"event-row {sev_class}"))

    def _refresh_status(self) -> None:
        events = self.events_data
        defcon = _calculate_defcon(events)

        # DEFCON label with color via CSS class (keep ID stable)
        defcon_label = self.query_one("#defcon-label", Label)
        for i in range(1, 6):
            defcon_label.remove_class(f"defcon-{i}")
        defcon_label.add_class(f"defcon-{defcon}")
        defcon_label.update(f"DEFCON: {defcon}")

        # Last event
        last_event_label = self.query_one("#last-event-label", Label)
        if events:
            last_event_label.update(f"Last event:\n{_time_ago(events[0].published)}")
        else:
            last_event_label.update("Last event:\n—")

        # Events per hour
        now = datetime.now(timezone.utc)
        last_hour = [e for e in events if (now.timestamp() - e.published.timestamp()) <= 3600]
        self.query_one("#events-per-hour", Label).update(
            f"Events/hr:\n{len(last_hour)}"
        )

        # Severity breakdown
        counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for e in events:
            counts[e.severity] += 1
        breakdown = "Severity:\n"
        breakdown += f"🔴 {counts[5]}\n"
        breakdown += f"🟠 {counts[4]}\n"
        breakdown += f"🟡 {counts[3]}\n"
        breakdown += f"🔵 {counts[2]}\n"
        breakdown += f"⚪ {counts[1]}"
        self.query_one("#severity-breakdown", Label).update(breakdown)

    def action_open_url(self) -> None:
        focused = self.focused
        if isinstance(focused, EventRow):
            webbrowser.open(focused._event.url)

    def action_filter(self) -> None:
        self.filter_active = not self.filter_active
        self._refresh_feed()

    def action_sort_toggle(self) -> None:
        self.sort_by_severity = not self.sort_by_severity
        self._refresh_feed()

    def action_quit(self) -> None:
        self.exit()


def main() -> None:
    app = WarmonitorApp()
    app.run()


if __name__ == "__main__":
    main()
