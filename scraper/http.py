"""Shared HTTP session with retries, rate limiting, and a realistic User-Agent."""

from __future__ import annotations

import time
import threading
from typing import Dict
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

# Per-host last-request timestamps for polite rate limiting (1 req/sec per host)
_last_request: Dict[str, float] = {}
_rate_lock = threading.Lock()

_RATE_LIMIT_SECONDS = 1.0


def _polite_sleep(url: str) -> None:
    host = urlparse(url).netloc
    with _rate_lock:
        last = _last_request.get(host, 0.0)
        wait = _RATE_LIMIT_SECONDS - (time.monotonic() - last)
        if wait > 0:
            time.sleep(wait)
        _last_request[host] = time.monotonic()


def build_session() -> requests.Session:
    """Return a requests.Session with retry logic and a real browser UA."""
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "HEAD"],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update(
        {
            "User-Agent": _USER_AGENT,
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
    )
    return session


def get(session: requests.Session, url: str, **kwargs) -> requests.Response:
    """Rate-limited GET with timeout defaults."""
    _polite_sleep(url)
    kwargs.setdefault("timeout", 15)
    return session.get(url, **kwargs)
