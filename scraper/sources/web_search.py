"""DuckDuckGo HTML search fallback — no API key required.

Searches for PDF service/repair manuals from reputable domains.
Filters out piracy/torrent sites and only surfaces links from
recognized legitimate automotive resource domains.
"""

from __future__ import annotations

import re
from typing import List
from urllib.parse import quote_plus, urlparse

from bs4 import BeautifulSoup

from scraper.http import get
from scraper.models import ManualResult
from scraper.sources.base import Source

# Allow-listed domains: official OEM portals, reputable reference sites
_ALLOWLIST_DOMAINS = {
    "haynes.com",
    "chilton.cengage.com",
    "autozone.com",
    "alldata.com",
    "mitchellrepair.com",
    "repairpal.com",
    "archive.org",
    "manualslib.com",
    "owner.ford.com",
    "toyota.com",
    "honda.com",
    "chevrolet.com",
    "nissan.com",
    "hyundaiusa.com",
    "kia.com",
    "vw.com",
    "audiusa.com",
    "bmwusa.com",
    "mercedes-benz.com",
    "subaru.com",
    "mazda.com",
    "factory-manuals.com",
    "eautorepair.net",
    "justanswer.com",
    "carmanualshub.com",
    "carloanmanual.com",
    "car-manuals.net",
    "vehiclemanuals.info",
}

# Block-listed patterns (piracy/torrent sites)
_BLOCKLIST_PATTERNS = [
    r"torrent",
    r"pirate",
    r"crack",
    r"warez",
    r"4shared",
    r"rapidshare",
    r"megaupload",
    r"filesharing",
]


def _is_allowed(url: str) -> bool:
    try:
        host = urlparse(url).netloc.lower()
        host = host.lstrip("www.")
        # Check block-list first
        for pattern in _BLOCKLIST_PATTERNS:
            if re.search(pattern, url, re.I):
                return False
        # Accept if on allow-list
        for domain in _ALLOWLIST_DOMAINS:
            if host == domain or host.endswith("." + domain):
                return True
    except Exception:
        pass
    return False


class WebSearchSource(Source):
    name = "Web Search"

    _DDG_URL = "https://html.duckduckgo.com/html/?q={query}"

    def search(self, make: str, model: str, year: int, task: str = "") -> List[ManualResult]:
        results: List[ManualResult] = []
        try:
            task_part = f" {task}" if task.strip() else " service manual repair guide"
            raw_query = f'{year} {make} {model}{task_part} filetype:pdf'
            query = quote_plus(raw_query)
            url = self._DDG_URL.format(query=query)

            resp = get(self.session, url)
            if resp.status_code != 200:
                return results

            soup = BeautifulSoup(resp.text, "lxml")

            # DuckDuckGo HTML results are in <a class="result__a"> elements
            links = soup.select("a.result__a")
            if not links:
                # Fallback selector
                links = soup.find_all("a", href=re.compile(r"^https?://"))

            seen: set = set()
            for link in links:
                href = link.get("href", "")
                if not href.startswith("http"):
                    continue
                # DDG sometimes wraps links in a redirect — extract the real URL
                if "duckduckgo.com" in href:
                    match = re.search(r"uddg=([^&]+)", href)
                    if match:
                        from urllib.parse import unquote
                        href = unquote(match.group(1))

                if href in seen:
                    continue
                seen.add(href)

                if not _is_allowed(href):
                    continue

                title = link.get_text(strip=True) or href
                title_lower = title.lower()
                score = 0.4

                if str(year) in title_lower or str(year) in href:
                    score += 0.15
                if make.lower() in title_lower or make.lower() in href.lower():
                    score += 0.1
                if model.lower() in title_lower or model.lower() in href.lower():
                    score += 0.1
                if href.endswith(".pdf") or "filetype:pdf" in href.lower():
                    score += 0.15

                fmt = "pdf" if href.lower().endswith(".pdf") else "web"

                results.append(
                    ManualResult(
                        title=title,
                        source=self.name,
                        url=href,
                        format=fmt,
                        confidence=min(score, 1.0),
                        notes="Found via web search — verify this is a legitimate source before using",
                    )
                )

            results.sort(key=lambda r: r.confidence, reverse=True)

        except Exception:
            pass
        return results
