"""Pydantic data models for warmonitor."""

from datetime import datetime

from pydantic import BaseModel


class Event(BaseModel):
    id: str
    title: str
    summary: str
    url: str
    published: datetime
    source_id: str
    source_name: str
    credibility: str  # HIGH / MEDIUM
    keywords_matched: list[str]
    severity: int  # 1-5, auto-calculated from keywords


class Source(BaseModel):
    id: str
    name: str
    url: str
    type: str
    keywords: list[str]
    credibility: str
    color: str
    status: str = "unknown"  # ok / error / fetching / unknown
