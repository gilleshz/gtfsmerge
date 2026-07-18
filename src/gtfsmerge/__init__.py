"""gtfsmerge -- Merge multiple GTFS feeds into one."""

from __future__ import annotations

from gtfsmerge.cli import main
from gtfsmerge.merge import merge

__all__ = ["main", "merge"]
