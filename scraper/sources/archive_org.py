"""Internet Archive (archive.org) — free public-domain/CC service manuals."""

from __future__ import annotations

import re
from typing import List
from urllib.parse import quote_plus

from bs4 import BeautifulSoup

from scraper.http import get
from scraper.models import ManualResult
from scraper.sources.base import Source


class ArchiveOrgSource(Source):
    name = "Internet Archive"

    # archive.org full-text search
    _SEARCH_API = (
        "https://archive.org/advancedsearch.php?"
        "q={query}&fl[]=identifier&fl[]=title&fl[]=format&output=json"
        "&rows=8&page=1&mediatype=texts"
    )
    _ITEM_URL = "https://archive.org/details/{identifier}"
    _PDF_URL = "https://archive.org/download/{identifier}/{identifier}.pdf"

    def search(self, make: str, model: str, year: int) -> List[ManualResult]:
        results: List[ManualResult] = []
        try:
            query_str = f'"{make} {model}" service manual'
            query = quote_plus(query_str)
            api_url = self._SEARCH_API.format(query=query)

            resp = get(self.session, api_url)
            if resp.status_code != 200:
                return results

            data = resp.json()
            docs = data.get("response", {}).get("docs", [])

            for doc in docs:
                identifier = doc.get("identifier", "")
                title = doc.get("title", identifier)
                if not identifier:
                    continue

                title_lower = title.lower()
                score = 0.45

                if str(year) in title_lower:
                    score += 0.25
                if make.lower() in title_lower:
                    score += 0.15
                if model.lower() in title_lower:
                    score += 0.15
                if any(kw in title_lower for kw in ("service manual", "repair manual", "workshop manual", "haynes", "chilton")):
                    score += 0.1

                item_url = self._ITEM_URL.format(identifier=identifier)

                # Check if a direct PDF download is available
                fmt = doc.get("format", [])
                has_pdf = isinstance(fmt, list) and any("PDF" in f for f in fmt)
                if has_pdf:
                    pdf_url = self._PDF_URL.format(identifier=identifier)
                    result_url = pdf_url
                    result_format = "pdf"
                    score = min(score + 0.05, 1.0)
                else:
                    result_url = item_url
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

            # Sort by confidence so callers get best matches first
            results.sort(key=lambda r: r.confidence, reverse=True)

        except Exception:
            pass
        return results
