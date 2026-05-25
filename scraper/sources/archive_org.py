"""Internet Archive (archive.org) — free public-domain/CC service manuals.

Runs multiple queries to maximise coverage:
  1. Unquoted year+make+model search (broader, picks up most FSMs)
  2. "factory service manual" variant (targets OEM FSMs)
  3. "workshop manual" variant (European/older terminology)
  4. Task-specific query if --task is provided
"""

from __future__ import annotations

import re
from typing import Dict, List
from urllib.parse import quote_plus

from scraper.http import get
from scraper.models import ManualResult
from scraper.sources.base import Source


class ArchiveOrgSource(Source):
    name = "Internet Archive"

    _SEARCH_API = (
        "https://archive.org/advancedsearch.php?"
        "q={query}&fl[]=identifier&fl[]=title&fl[]=format&output=json"
        "&rows=10&page=1&mediatype=texts"
    )
    _ITEM_URL = "https://archive.org/details/{identifier}"
    _PDF_URL = "https://archive.org/download/{identifier}/{identifier}.pdf"

    def search(self, make: str, model: str, year: int, task: str = "") -> List[ManualResult]:
        results: List[ManualResult] = []
        seen_ids: Dict[str, bool] = {}

        # Build a list of queries to try — broader first, more specific after.
        # Unquoted terms give archive.org more flexibility to match.
        queries = [
            f"{year} {make} {model} service manual",
            f"{make} {model} factory service manual",
            f"{make} {model} workshop manual repair",
        ]
        if task.strip():
            queries.append(f"{make} {model} {year} {task}")

        try:
            for query_str in queries:
                query = quote_plus(query_str)
                api_url = self._SEARCH_API.format(query=query)

                resp = get(self.session, api_url)
                if resp.status_code != 200:
                    continue

                data = resp.json()
                docs = data.get("response", {}).get("docs", [])

                for doc in docs:
                    identifier = doc.get("identifier", "")
                    title = doc.get("title", identifier)
                    if not identifier or identifier in seen_ids:
                        continue
                    seen_ids[identifier] = True

                    title_lower = title.lower()
                    score = 0.45

                    if str(year) in title_lower:
                        score += 0.25
                    if make.lower() in title_lower:
                        score += 0.15
                    if model.lower() in title_lower:
                        score += 0.15
                    if any(
                        kw in title_lower
                        for kw in (
                            "service manual", "repair manual", "workshop manual",
                            "factory service", "fsm", "haynes", "chilton",
                        )
                    ):
                        score += 0.1
                    if task and any(
                        kw in title_lower for kw in task.lower().split()
                    ):
                        score += 0.05

                    # Check if a direct PDF download is available
                    fmt = doc.get("format", [])
                    has_pdf = isinstance(fmt, list) and any("PDF" in f for f in fmt)
                    if has_pdf:
                        result_url = self._PDF_URL.format(identifier=identifier)
                        result_format = "pdf"
                        score = min(score + 0.05, 1.0)
                    else:
                        result_url = self._ITEM_URL.format(identifier=identifier)
                        result_format = "web"

                    results.append(
                        ManualResult(
                            title=title,
                            source=self.name,
                            url=result_url,
                            format=result_format,
                            confidence=min(score, 1.0),
                            notes="Free via Internet Archive — may be scanned print manual",
                        )
                    )

            results.sort(key=lambda r: r.confidence, reverse=True)

        except Exception:
            pass
        return results
