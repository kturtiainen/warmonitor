"""Verified source definitions for warmonitor."""

from warmonitor.models import Source

SOURCES: list[Source] = [
    Source(
        id="isw_iran",
        name="ISW — Iran Updates",
        url="https://www.understandingwar.org/feeds/all",
        type="rss",
        keywords=["Iran", "IRGC", "Middle East", "Israel", "nuclear"],
        credibility="HIGH",
        color="red",
    ),
    Source(
        id="critical_threats",
        name="Critical Threats (AEI)",
        url="https://www.criticalthreats.org/feed",
        type="rss",
        keywords=["Iran", "IRGC", "strike", "missile"],
        credibility="HIGH",
        color="red",
    ),
    Source(
        id="soufan",
        name="Soufan Center IntelBrief",
        url="https://thesoufancenter.org/feed/",
        type="rss",
        keywords=["Iran", "US", "Israel", "Middle East"],
        credibility="HIGH",
        color="yellow",
    ),
    Source(
        id="reuters",
        name="Reuters World News",
        url="https://feeds.reuters.com/reuters/worldNews",
        type="rss",
        keywords=["Iran", "Israel", "US military", "Middle East", "strike", "missile"],
        credibility="HIGH",
        color="green",
    ),
    Source(
        id="bbc_world",
        name="BBC News — World",
        url="https://feeds.bbci.co.uk/news/world/rss.xml",
        type="rss",
        keywords=["Iran", "Israel", "US military", "Middle East"],
        credibility="HIGH",
        color="green",
    ),
    Source(
        id="crisiswatch",
        name="Crisis Group CrisisWatch",
        url="https://www.crisisgroup.org/rss.xml",
        type="rss",
        keywords=["Iran", "Middle East"],
        credibility="HIGH",
        color="yellow",
    ),
]
