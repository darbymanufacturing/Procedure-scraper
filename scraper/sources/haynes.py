"""Haynes official online manual catalog (haynes.com)."""

from __future__ import annotations

import re
from typing import List
from urllib.parse import quote_plus

from bs4 import BeautifulSoup

from scraper.http import get
from scraper.models import ManualResult
from scraper.sources.base import Source


class HaynesSource(Source):
    name = "Haynes"

    _SEARCH_URL = "https://haynes.com/en-us/search?q={query}"

    def search(self, make: str, model: str, year: int) -> List[ManualResult]:
        results: List[ManualResult] = []
        try:
            query = quote_plus(f"{year} {make} {model}")
            url = self._SEARCH_URL.format(query=query)
            resp = get(self.session, url)
            if resp.status_code != 200:
                return results

            soup = BeautifulSoup(resp.text, "lxml")

            # Haynes search results appear as product cards
            cards = soup.select("div.search-result, li.product-item, div.product-card, article.product")
            if not cards:
                # Fallback: look for any <a> that contains the make/model text
                cards = soup.find_all("a", href=re.compile(r"/en-us/.*manual", re.I))

            seen: set = set()
            for card in cards[:10]:
                if hasattr(card, "find"):
                    link = card.find("a", href=True)
                    title_el = card.find(["h2", "h3", "h4", "span"], class_=re.compile(r"title|name|product", re.I))
                else:
                    link = card
                    title_el = None

                if link is None:
                    continue

                href = link.get("href", "")
                if not href.startswith("http"):
                    href = "https://haynes.com" + href

                if href in seen:
                    continue
                seen.add(href)

                title = (title_el.get_text(strip=True) if title_el else link.get_text(strip=True)) or href
                if not title:
                    continue

                # Score based on how well the title matches make/model/year
                title_lower = title.lower()
                score = 0.5
                if str(year) in title_lower:
                    score += 0.2
                if make.lower() in title_lower:
                    score += 0.15
                if model.lower() in title_lower:
                    score += 0.15

                results.append(
                    ManualResult(
                        title=title,
                        source=self.name,
                        url=href,
                        format="subscription",
                        confidence=min(score, 1.0),
                        notes="Official Haynes manual — purchase or online subscription at haynes.com",
                    )
                )

            if not results:
                # Always surface a direct search link even if parsing fails
                results.append(
                    ManualResult(
                        title=f"Haynes catalog search: {year} {make} {model}",
                        source=self.name,
                        url=f"https://haynes.com/en-us/search?q={query}",
                        format="subscription",
                        confidence=0.4,
                        notes="Official Haynes manual — purchase or online subscription at haynes.com",
                    )
                )

        except Exception:
            pass
        return results
