"""AutoZone Repair Guides — free web-based technician guides (autozone.com)."""

from __future__ import annotations

import re
from typing import List
from urllib.parse import quote_plus

from bs4 import BeautifulSoup

from scraper.http import get
from scraper.models import ManualResult
from scraper.sources.base import Source


class AutoZoneSource(Source):
    name = "AutoZone"

    # AutoZone's DIY repair guide search
    _SEARCH_URL = "https://www.autozone.com/diy/{make}/{model}/year-{year}"
    _ALT_SEARCH = "https://www.autozone.com/repairguides/search?year={year}&make={make}&model={model}"

    def search(self, make: str, model: str, year: int) -> List[ManualResult]:
        results: List[ManualResult] = []
        try:
            make_slug = make.lower().replace(" ", "-")
            model_slug = model.lower().replace(" ", "-")

            url = self._SEARCH_URL.format(make=make_slug, model=model_slug, year=year)
            resp = get(self.session, url)

            if resp.status_code == 200 and "repair" in resp.url.lower():
                results.append(
                    ManualResult(
                        title=f"AutoZone Repair Guide: {year} {make} {model}",
                        source=self.name,
                        url=resp.url,
                        format="web",
                        confidence=0.85,
                        notes="Free technician-grade repair guides — no account needed",
                    )
                )
                return results

            # Try the search fallback
            alt_url = self._ALT_SEARCH.format(
                year=year,
                make=quote_plus(make),
                model=quote_plus(model),
            )
            resp2 = get(self.session, alt_url)
            if resp2.status_code == 200:
                soup = BeautifulSoup(resp2.text, "lxml")
                links = soup.find_all("a", href=re.compile(r"repairguide|diy", re.I))
                seen: set = set()
                for link in links[:5]:
                    href = link.get("href", "")
                    if not href.startswith("http"):
                        href = "https://www.autozone.com" + href
                    if href in seen:
                        continue
                    seen.add(href)
                    title = link.get_text(strip=True) or f"AutoZone Repair Guide: {year} {make} {model}"
                    results.append(
                        ManualResult(
                            title=title,
                            source=self.name,
                            url=href,
                            format="web",
                            confidence=0.75,
                            notes="Free technician-grade repair guides — no account needed",
                        )
                    )

            if not results:
                # Guarantee a search link
                search_link = (
                    f"https://www.autozone.com/repairguides/search?"
                    f"year={year}&make={quote_plus(make)}&model={quote_plus(model)}"
                )
                results.append(
                    ManualResult(
                        title=f"AutoZone Repair Guides search: {year} {make} {model}",
                        source=self.name,
                        url=search_link,
                        format="web",
                        confidence=0.5,
                        notes="Free technician-grade repair guides — no account needed",
                    )
                )

        except Exception:
            pass
        return results
