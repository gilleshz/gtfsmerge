"""Coordinate-based stop ID generation and stop deduplication."""

from __future__ import annotations

from typing import Any


def coord_to_stop_id(lat: Any, lon: Any) -> str:
    """Generate a coordinate-based stop ID from latitude and longitude.

    Rounds to 4 decimal places (roughly 11 m precision) so that two sources
    describing the same physical station receive the same ``stop_id``.

    >>> coord_to_stop_id(48.58392, 7.74553)
    'S_48.5839_7.7455'
    """
    lat_f = float(lat) if not isinstance(lat, float) else lat
    lon_f = float(lon) if not isinstance(lon, float) else lon
    return f"S_{lat_f:.4f}_{lon_f:.4f}"


def remap_stop_times(
    stop_times: list[dict[str, str]], old_to_new: dict[str, str]
) -> list[dict[str, str]]:
    """Return *stop_times* with ``stop_id`` fields replaced via *old_to_new*."""
    result: list[dict[str, str]] = []
    for st in stop_times:
        old = st.get("stop_id", "")
        if old and old in old_to_new:
            row = dict(st)
            row["stop_id"] = old_to_new[old]
            result.append(row)
        else:
            result.append(st)
    return result


def merge_stops(
    stops_by_new_id: dict[str, dict[str, str]],
    new_stop: dict[str, str],
) -> dict[str, dict[str, str]]:
    """Insert *new_stop* into *stops_by_new_id*, keyed by ``stop_id``.

    If a stop with the same key already exists the existing entry is kept
    (first name wins).
    """
    key = new_stop.get("stop_id", "")
    if not key:
        return stops_by_new_id
    if key not in stops_by_new_id:
        stops_by_new_id[key] = dict(new_stop)
    return stops_by_new_id
