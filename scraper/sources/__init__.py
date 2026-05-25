"""Manual sources package."""

from scraper.sources.archive_org import ArchiveOrgSource
from scraper.sources.autozone import AutoZoneSource
from scraper.sources.haynes import HaynesSource
from scraper.sources.manufacturer import ManufacturerSource
from scraper.sources.web_search import WebSearchSource

__all__ = [
    "HaynesSource",
    "AutoZoneSource",
    "ArchiveOrgSource",
    "ManufacturerSource",
    "WebSearchSource",
]
