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
    def search(self, make: str, model: str, year: int, task: str = "") -> List[ManualResult]:
        """Search for manuals for the given vehicle.

        Args:
            make: Vehicle make, e.g. "Toyota"
            model: Vehicle model, e.g. "Civic"
            year: Four-digit model year
            task: Optional repair task description, e.g. "clutch replacement".
                  Sources use this to refine queries and rank results.

        Returns a (possibly empty) list of ManualResult objects.
        Must not raise — catch exceptions and return [] instead.
        """
        ...
