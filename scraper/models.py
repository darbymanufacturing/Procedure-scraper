"""Data models for manual search results."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


FormatType = Literal["pdf", "web", "subscription", "unknown"]


@dataclass
class ManualResult:
    """A single repair manual search result."""

    title: str
    source: str          # e.g. "Haynes", "AutoZone", "archive.org"
    url: str
    format: FormatType   # "pdf", "web", "subscription", "unknown"
    confidence: float    # 0.0 – 1.0; higher = better match
    notes: str = ""      # extra human-readable detail (e.g. "free with library card")

    def __str__(self) -> str:
        badge = {
            "pdf": "[PDF]",
            "web": "[WEB]",
            "subscription": "[PAID/SUBSCRIPTION]",
            "unknown": "[?]",
        }.get(self.format, "[?]")
        lines = [f"{badge} {self.title}", f"    Source : {self.source}", f"    URL    : {self.url}"]
        if self.notes:
            lines.append(f"    Note   : {self.notes}")
        return "\n".join(lines)
