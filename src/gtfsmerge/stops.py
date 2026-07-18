"""Coordinate-based stop ID generation and stop deduplication."""

from __future__ import annotations

import math
from typing import Any

_EARTH_RADIUS_M = 6_378_137.0


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


def normalize_stop_name(name: str) -> str:
    """Normalize a stop name for fuzzy comparison.

    Lowercases, strips, and collapses whitespace so that
    ``"  ROI  GEORGE "`` and ``"Roi George"`` compare equal.
    """
    return " ".join(name.lower().split())


def haversine_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Compute the great-circle distance in metres between two points."""
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2.0) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2.0) ** 2
    )
    return 2.0 * _EARTH_RADIUS_M * math.asin(math.sqrt(a))


def fuzzy_merge_stops(
    stops_by_id: dict[str, dict[str, str]],
    radius_m: float = 50.0,
) -> tuple[dict[str, dict[str, str]], dict[str, str]]:
    """Merge nearby stops that share the same normalized name.

    Applied as a second pass after coordinate-based dedup. Two stops that
    landed on different coordinate IDs (e.g. because OSM and GTFS placed
    the same station 20 m apart) are merged when their normalized names
    match and the distance between them is ≤ *radius_m*.

    Returns ``(merged_stops, old_id_to_new_id)`` where *merged_stops* is
    the deduplicated stop map and *old_id_to_new_id* maps removed stop IDs
    to the canonical ID they should be replaced with.
    """
    if radius_m <= 0.0:
        return dict(stops_by_id), {}

    stops_list = list(stops_by_id.items())
    remap: dict[str, str] = {}

    for i, (id_a, stop_a) in enumerate(stops_list):
        if id_a in remap:
            continue
        name_a = normalize_stop_name(stop_a.get("stop_name", ""))
        if not name_a:
            continue
        try:
            lat_a = float(stop_a.get("stop_lat", 0))
            lon_a = float(stop_a.get("stop_lon", 0))
        except (ValueError, TypeError):
            continue

        for j in range(i + 1, len(stops_list)):
            id_b, stop_b = stops_list[j]
            if id_b in remap:
                continue
            name_b = normalize_stop_name(stop_b.get("stop_name", ""))
            if name_a != name_b:
                continue
            try:
                lat_b = float(stop_b.get("stop_lat", 0))
                lon_b = float(stop_b.get("stop_lon", 0))
            except (ValueError, TypeError):
                continue
            if haversine_distance_m(lat_a, lon_a, lat_b, lon_b) <= radius_m:
                remap[id_b] = id_a

    if not remap:
        return dict(stops_by_id), remap

    merged: dict[str, dict[str, str]] = {}
    for sid, stop in stops_by_id.items():
        if sid not in remap:
            merged[sid] = stop

    return merged, remap
