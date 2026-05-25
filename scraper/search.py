"""Search orchestrator — queries all sources concurrently and returns ranked results."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Type

from scraper.http import build_session
from scraper.models import ManualResult
from scraper.sources.archive_org import ArchiveOrgSource
from scraper.sources.autozone import AutoZoneSource
from scraper.sources.base import Source
from scraper.sources.haynes import HaynesSource
from scraper.sources.manufacturer import ManufacturerSource
from scraper.sources.web_search import WebSearchSource

# Ordered by preference; web_search is last (broadest but least precise)
_SOURCE_CLASSES: List[Type[Source]] = [
    HaynesSource,
    AutoZoneSource,
    ArchiveOrgSource,
    ManufacturerSource,
    WebSearchSource,
]


def search_manuals(
    make: str,
    model: str,
    year: int,
    task: str = "",
    top_n: int = 5,
    all_results: bool = False,
) -> List[ManualResult]:
    """Query all sources concurrently and return the best matches.

    Args:
        make: Vehicle make, e.g. "Toyota"
        model: Vehicle model, e.g. "Camry"
        year: Four-digit model year, e.g. 2018
        task: Optional repair task, e.g. "clutch replacement". Used to refine
              source queries and demote results that won't cover the task.
        top_n: Maximum results to return (ignored when all_results=True)
        all_results: If True, return every result from every source.

    Returns:
        List of ManualResult sorted by confidence (highest first).
    """
    session = build_session()
    sources = [cls(session) for cls in _SOURCE_CLASSES]

    all_found: List[ManualResult] = []

    def _run(source: Source) -> List[ManualResult]:
        return source.search(make, model, year, task)

    with ThreadPoolExecutor(max_workers=len(sources)) as pool:
        futures = {pool.submit(_run, s): s for s in sources}
        for future in as_completed(futures):
            try:
                all_found.extend(future.result())
            except Exception:
                pass

    # De-duplicate by URL
    seen_urls: set = set()
    unique: List[ManualResult] = []
    for result in all_found:
        if result.url not in seen_urls:
            seen_urls.add(result.url)
            unique.append(result)

    # Sort by confidence desc, then prefer PDF over web over subscription
    format_rank = {"pdf": 0, "web": 1, "subscription": 2, "unknown": 3}
    unique.sort(key=lambda r: (-r.confidence, format_rank.get(r.format, 99)))

    if all_results:
        return unique
    return unique[:top_n]
