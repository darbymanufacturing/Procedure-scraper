"""Abstract base class for manual sources."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

import requests

from scraper.models import ManualResult


class Source(ABC):
    """A single source of repair manuals."""

    name: str = "UnknownSource"

    def __init__(self, session: requests.Session) -> None:
        self.session = session

    @abstractmethod
    def search(self, make: str, model: str, year: int) -> List[ManualResult]:
        """Search for manuals for the given vehicle.

        Returns a (possibly empty) list of ManualResult objects.
        Must not raise — catch exceptions and return [] instead.
        """
        ...
