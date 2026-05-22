"""Offline tests using mock HTTP responses — no real network calls."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
import requests

from scraper.models import ManualResult
from scraper.sources.archive_org import ArchiveOrgSource
from scraper.sources.autozone import AutoZoneSource
from scraper.sources.haynes import HaynesSource
from scraper.sources.manufacturer import ManufacturerSource
from scraper.sources.web_search import WebSearchSource


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_session() -> requests.Session:
    return MagicMock(spec=requests.Session)


def _response(status: int = 200, text: str = "", json_data=None) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status
    resp.text = text
    resp.url = "https://example.com/result"
    if json_data is not None:
        resp.json.return_value = json_data
    return resp


# ---------------------------------------------------------------------------
# ManufacturerSource — purely static, no HTTP
# ---------------------------------------------------------------------------

class TestManufacturerSource:
    def test_known_make_returns_result(self):
        src = ManufacturerSource(_mock_session())
        results = src.search("Toyota", "Camry", 2018)
        assert len(results) == 1
        r = results[0]
        assert isinstance(r, ManualResult)
        assert "toyota.com" in r.url
        assert r.format == "pdf"
        assert r.confidence > 0

    def test_unknown_make_returns_empty(self):
        src = ManufacturerSource(_mock_session())
        results = src.search("Trabant", "601", 1975)
        assert results == []

    def test_case_insensitive(self):
        src = ManufacturerSource(_mock_session())
        results = src.search("FORD", "F-150", 2020)
        assert len(results) == 1
        assert "ford.com" in results[0].url

    def test_saab_discontinued(self):
        src = ManufacturerSource(_mock_session())
        results = src.search("Saab", "9-5", 2003)
        assert len(results) == 1


# ---------------------------------------------------------------------------
# ArchiveOrgSource — uses archive.org JSON API
# ---------------------------------------------------------------------------

ARCHIVE_JSON = {
    "response": {
        "docs": [
            {
                "identifier": "1989-ford-mustang-fsm",
                "title": "1989 Ford Mustang Factory Service Manual",
                "format": ["PDF", "Text"],
            },
            {
                "identifier": "ford-mustang-89-workshop",
                "title": "Ford Mustang 89 Workshop Repair Guide",
                "format": ["DjVu", "Text"],
            },
        ]
    }
}


class TestArchiveOrgSource:
    def test_returns_results_for_pdf(self):
        session = _mock_session()
        with patch("scraper.sources.archive_org.get") as mock_get:
            mock_get.return_value = _response(200, json_data=ARCHIVE_JSON)
            src = ArchiveOrgSource(session)
            results = src.search("Ford", "Mustang", 1989)

        assert len(results) == 2
        # PDF item should rank higher (has "PDF" in format list)
        pdf_results = [r for r in results if r.format == "pdf"]
        assert len(pdf_results) == 1
        assert "1989-ford-mustang-fsm" in pdf_results[0].url

    def test_empty_response(self):
        session = _mock_session()
        with patch("scraper.sources.archive_org.get") as mock_get:
            mock_get.return_value = _response(200, json_data={"response": {"docs": []}})
            src = ArchiveOrgSource(session)
            results = src.search("Bugatti", "Veyron", 2012)
        assert results == []

    def test_http_error_returns_empty(self):
        session = _mock_session()
        with patch("scraper.sources.archive_org.get") as mock_get:
            mock_get.return_value = _response(503)
            src = ArchiveOrgSource(session)
            results = src.search("Toyota", "Camry", 2018)
        assert results == []

    def test_confidence_higher_when_year_matches(self):
        session = _mock_session()
        data = {
            "response": {
                "docs": [
                    {"identifier": "with-year", "title": "2018 Toyota Camry Service Manual", "format": []},
                    {"identifier": "no-year", "title": "Toyota Camry Service Manual", "format": []},
                ]
            }
        }
        with patch("scraper.sources.archive_org.get") as mock_get:
            mock_get.return_value = _response(200, json_data=data)
            src = ArchiveOrgSource(session)
            results = src.search("Toyota", "Camry", 2018)

        # The result with the year in the title should have higher confidence
        with_year = next(r for r in results if "with-year" in r.url)
        no_year = next(r for r in results if "no-year" in r.url)
        assert with_year.confidence > no_year.confidence


# ---------------------------------------------------------------------------
# HaynesSource
# ---------------------------------------------------------------------------

HAYNES_HTML = """
<html><body>
<div class="product-card">
  <h3 class="product-title">2018 Toyota Camry Haynes Repair Manual</h3>
  <a href="/en-us/toyota/camry/2018-manual">Buy Now</a>
</div>
<div class="product-card">
  <h3 class="product-title">2016-2020 Toyota Camry Haynes Manual</h3>
  <a href="/en-us/toyota/camry/2016-2020-manual">Buy Now</a>
</div>
</body></html>
"""


class TestHaynesSource:
    def test_parses_results(self):
        session = _mock_session()
        with patch("scraper.sources.haynes.get") as mock_get:
            mock_get.return_value = _response(200, HAYNES_HTML)
            src = HaynesSource(session)
            results = src.search("Toyota", "Camry", 2018)

        assert len(results) >= 1
        urls = [r.url for r in results]
        assert any("haynes.com" in u for u in urls)

    def test_fallback_search_link_on_empty_html(self):
        session = _mock_session()
        with patch("scraper.sources.haynes.get") as mock_get:
            mock_get.return_value = _response(200, "<html><body>nothing</body></html>")
            src = HaynesSource(session)
            results = src.search("Saab", "9-5", 2003)

        # Must still return at least the search-link fallback
        assert len(results) >= 1
        assert all(r.format == "subscription" for r in results)

    def test_http_error_returns_empty(self):
        session = _mock_session()
        with patch("scraper.sources.haynes.get") as mock_get:
            mock_get.return_value = _response(404)
            src = HaynesSource(session)
            results = src.search("Toyota", "Camry", 2018)
        assert results == []


# ---------------------------------------------------------------------------
# AutoZoneSource
# ---------------------------------------------------------------------------

class TestAutoZoneSource:
    def test_direct_url_success(self):
        session = _mock_session()
        resp = _response(200, "<html>Repair Guide content</html>")
        resp.url = "https://www.autozone.com/repairguides/toyota/camry"
        with patch("scraper.sources.autozone.get") as mock_get:
            mock_get.return_value = resp
            src = AutoZoneSource(session)
            results = src.search("Toyota", "Camry", 2018)

        assert len(results) >= 1
        assert results[0].format == "web"

    def test_fallback_search_link(self):
        session = _mock_session()
        resp404 = _response(404)
        resp404.url = "https://www.autozone.com/diy/toyota/camry/year-2018"
        resp_empty = _response(200, "<html></html>")

        with patch("scraper.sources.autozone.get") as mock_get:
            mock_get.side_effect = [resp404, resp_empty]
            src = AutoZoneSource(session)
            results = src.search("Toyota", "Camry", 2018)

        assert len(results) >= 1
        assert any("autozone.com" in r.url for r in results)


# ---------------------------------------------------------------------------
# WebSearchSource
# ---------------------------------------------------------------------------

DDG_HTML = """
<html><body>
<div class="results">
  <a class="result__a" href="https://archive.org/details/ford-f150-1995-service-manual">
    1995 Ford F-150 Factory Service Manual PDF
  </a>
  <a class="result__a" href="https://haynes.com/en-us/ford/f-150/1992-1997-manual">
    Haynes Ford F-150 1992-1997 Manual
  </a>
  <a class="result__a" href="https://somewarez.ru/ford-f150.pdf">
    Download F150 manual warez
  </a>
</div>
</body></html>
"""


class TestWebSearchSource:
    def test_filters_blocklisted_domains(self):
        session = _mock_session()
        with patch("scraper.sources.web_search.get") as mock_get:
            mock_get.return_value = _response(200, DDG_HTML)
            src = WebSearchSource(session)
            results = src.search("Ford", "F-150", 1995)

        urls = [r.url for r in results]
        assert not any("warez" in u for u in urls)

    def test_returns_allowed_domains(self):
        session = _mock_session()
        with patch("scraper.sources.web_search.get") as mock_get:
            mock_get.return_value = _response(200, DDG_HTML)
            src = WebSearchSource(session)
            results = src.search("Ford", "F-150", 1995)

        urls = [r.url for r in results]
        assert any("archive.org" in u for u in urls)

    def test_http_error_returns_empty(self):
        session = _mock_session()
        with patch("scraper.sources.web_search.get") as mock_get:
            mock_get.return_value = _response(503)
            src = WebSearchSource(session)
            results = src.search("Ford", "F-150", 1995)
        assert results == []


# ---------------------------------------------------------------------------
# ManualResult model
# ---------------------------------------------------------------------------

class TestManualResult:
    def test_str_includes_url_and_source(self):
        r = ManualResult(
            title="Test Manual",
            source="TestSource",
            url="https://example.com/manual.pdf",
            format="pdf",
            confidence=0.9,
            notes="some note",
        )
        s = str(r)
        assert "https://example.com/manual.pdf" in s
        assert "TestSource" in s
        assert "[PDF]" in s
        assert "some note" in s
