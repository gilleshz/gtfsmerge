"""Core merge logic: resolve routes, collect and remap data, validate and write."""

from __future__ import annotations

import csv
import math
import sys
from pathlib import Path

from gtfsmerge.io import read_source_rows, stream_write_shapes, write_feed
from gtfsmerge.models import Feed
from gtfsmerge.stops import coord_to_stop_id, fuzzy_merge_stops, merge_stops, remap_stop_times


def merge(
    sources: dict[str, Path],
    route_refs: list[str],
    output_dir: str | Path,
    stop_merge_radius: float = 50.0,
) -> dict[str, int]:
    """Merge GTFS feeds from *sources*, selecting the requested *route_refs*.

    Returns a summary dict with counts for routes, trips, stops, and shape_points.
    """
    out = Path(output_dir)

    source_routes = _parse_all_routes(sources)
    winners = _resolve_winners(source_routes, route_refs, sources)

    if not winners:
        sys.stderr.write("warning: no matching routes found\n")
        return {"routes": 0, "trips": 0, "stops": 0, "shape_points": 0}

    by_source: dict[str, list[tuple[str, dict[str, str]]]] = {}
    for ref, source_name, route_row in winners:
        by_source.setdefault(source_name, []).append((ref, route_row))

    feed = Feed()
    global_stops: dict[str, dict[str, str]] = {}
    source_shape_ids: dict[str, set[str]] = {}

    for source_name, route_entries in by_source.items():
        source_path = sources[source_name]
        route_ids = {r["route_id"] for _, r in route_entries}

        feed.routes.extend(r for _, r in route_entries)

        trips, trip_ids = _collect_trips(
            source_path,
            route_ids,
            existing_ids={t["trip_id"] for t in feed.trips if t.get("trip_id")},
        )
        feed.trips.extend(trips)

        shape_ids = {t.get("shape_id", "") for t in trips if t.get("shape_id", "")}
        service_ids = {t.get("service_id", "") for t in trips if t.get("service_id", "")}

        stop_times, old_stop_ids = _collect_stop_times(source_path, trip_ids)
        old_to_new = _build_stop_remap(source_path, old_stop_ids, global_stops)
        feed.stop_times.extend(remap_stop_times(list(stop_times), old_to_new))

        _collect_agencies(source_path, feed)
        _collect_calendars(source_path, service_ids, feed)

        if shape_ids:
            source_shape_ids[source_name] = shape_ids

    merged_stops, fuzzy_remap = fuzzy_merge_stops(global_stops, stop_merge_radius)
    if fuzzy_remap:
        feed.stop_times = remap_stop_times(feed.stop_times, fuzzy_remap)
    feed.stops = list(merged_stops.values())

    if source_shape_ids:
        shape_path = out / "shapes.txt"
        written_shapes = stream_write_shapes(shape_path, sources, source_shape_ids)
        shape_points = _count_shape_points(shape_path)
        feed.shapes = [{"shape_id": s} for s in sorted(written_shapes)]
    else:
        shape_points = 0

    _validate(feed)

    feed.shapes = []
    write_feed(feed, out)

    summary = {
        "routes": len(feed.routes),
        "trips": len(feed.trips),
        "stops": len(feed.stops),
        "shape_points": shape_points,
    }
    sys.stderr.write(
        f"{summary['routes']} routes, {summary['trips']} trips, "
        f"{summary['stops']} stops, {summary['shape_points']} shape points\n"
    )
    return summary


def _parse_all_routes(
    sources: dict[str, Path],
) -> dict[str, dict[str, list[dict[str, str]]]]:
    """Return ``{source_name: {route_short_name: [route_rows]}}``."""
    result: dict[str, dict[str, list[dict[str, str]]]] = {}
    for name, path in sources.items():
        route_map: dict[str, list[dict[str, str]]] = {}
        for row in read_source_rows(path, "routes.txt"):
            ref = row.get("route_short_name", "").strip()
            if ref:
                route_map.setdefault(ref, []).append(row)
            elif row.get("route_long_name", "").strip():
                fallback = row["route_long_name"].strip()
                route_map.setdefault(fallback, []).append(row)
        result[name] = route_map
    return result


def _resolve_winners(
    source_routes: dict[str, dict[str, list[dict[str, str]]]],
    route_refs: list[str],
    sources: dict[str, Path],
) -> list[tuple[str, str, dict[str, str]]]:
    """Resolve each ref in *route_refs* to a winning (ref, source_name, route_row)."""
    if not route_refs:
        all_refs: set[str] = set()
        for refs in source_routes.values():
            all_refs.update(refs.keys())
        route_refs = sorted(all_refs)

    gtfs_names = [n for n in sources if n != "osm"]
    osm_names = [n for n in sources if n == "osm"]
    ordered = gtfs_names + osm_names

    winners: list[tuple[str, str, dict[str, str]]] = []
    for ref in route_refs:
        for name in ordered:
            routes = source_routes.get(name, {})
            if ref in routes:
                winners.append((ref, name, routes[ref][0]))
                break
    return winners


def _collect_trips(
    source_path: Path,
    route_ids: set[str],
    existing_ids: set[str] | None = None,
) -> tuple[list[dict[str, str]], set[str]]:
    trips: list[dict[str, str]] = []
    trip_ids: set[str] = set()
    skip_ids = existing_ids or set()
    for t in read_source_rows(source_path, "trips.txt"):
        tid = t.get("trip_id", "")
        if tid in skip_ids:
            continue
        if t.get("route_id", "") in route_ids:
            trips.append(t)
            if tid:
                trip_ids.add(tid)
    return trips, trip_ids


def _collect_stop_times(
    source_path: Path, trip_ids: set[str]
) -> tuple[list[dict[str, str]], set[str]]:
    stop_times: list[dict[str, str]] = []
    stop_ids: set[str] = set()
    for st in read_source_rows(source_path, "stop_times.txt"):
        if st.get("trip_id", "") in trip_ids:
            stop_times.append(st)
            sid = st.get("stop_id", "")
            if sid:
                stop_ids.add(sid)
    return stop_times, stop_ids


def _build_stop_remap(
    source_path: Path,
    old_stop_ids: set[str],
    global_stops: dict[str, dict[str, str]],
) -> dict[str, str]:
    old_to_new: dict[str, str] = {}
    for s in read_source_rows(source_path, "stops.txt"):
        if s.get("stop_id", "") not in old_stop_ids:
            continue
        old_id = s["stop_id"]
        try:
            lat = float(s.get("stop_lat", 0))
            lon = float(s.get("stop_lon", 0))
        except (ValueError, TypeError):
            continue
        if math.isnan(lat) or math.isnan(lon):
            continue
        new_id = coord_to_stop_id(lat, lon)
        old_to_new[old_id] = new_id
        new_stop = dict(s)
        new_stop["stop_id"] = new_id
        new_stop["stop_lat"] = f"{lat:.7f}"
        new_stop["stop_lon"] = f"{lon:.7f}"
        merge_stops(global_stops, new_stop)
    return old_to_new


def _collect_agencies(source_path: Path, feed: Feed) -> None:
    existing_ids = {a.get("agency_id", "") for a in feed.agencies}
    for a in read_source_rows(source_path, "agency.txt"):
        aid = a.get("agency_id", "")
        if aid in existing_ids:
            continue
        if not aid and existing_ids:
            continue
        feed.agencies.append(a)
        existing_ids.add(aid)


def _collect_calendars(source_path: Path, service_ids: set[str], feed: Feed) -> None:
    existing_services = {c.get("service_id", "") for c in feed.calendars}
    for c in read_source_rows(source_path, "calendar.txt"):
        sid = c.get("service_id", "")
        if sid in service_ids and sid not in existing_services:
            feed.calendars.append(c)
            existing_services.add(sid)
    existing_dates = {(cd.get("service_id", ""), cd.get("date", "")) for cd in feed.calendar_dates}
    for cd in read_source_rows(source_path, "calendar_dates.txt"):
        sid = cd.get("service_id", "")
        date = cd.get("date", "")
        if sid in service_ids and (sid, date) not in existing_dates:
            feed.calendar_dates.append(cd)
            existing_dates.add((sid, date))


def _count_shape_points(shape_path: Path) -> int:
    if not shape_path.is_file():
        return 0
    count = 0
    with open(shape_path, newline="", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        next(reader, None)  # skip header
        for _ in reader:
            count += 1
    return count


def _validate(feed: Feed) -> None:
    issues: list[str] = []

    if not feed.routes:
        issues.append("routes.txt: at least one route is required")
    if not feed.trips:
        issues.append("trips.txt: at least one trip is required")
    if not feed.stops:
        issues.append("stops.txt: at least one stop is required")
    if not feed.stop_times:
        issues.append("stop_times.txt: at least one stop_time is required")

    route_ids = {r["route_id"] for r in feed.routes}
    trip_ids = {t["trip_id"] for t in feed.trips}
    service_ids = {c["service_id"] for c in feed.calendars}
    service_ids.update(cd["service_id"] for cd in feed.calendar_dates)
    stop_ids = {s["stop_id"] for s in feed.stops}
    shape_ids = {s["shape_id"] for s in feed.shapes if s.get("shape_id")}

    for t in feed.trips:
        if t["route_id"] and t["route_id"] not in route_ids:
            issues.append(
                f"trips.txt: trip {t['trip_id']} references missing route {t['route_id']}"
            )
        if t["service_id"] and service_ids and t["service_id"] not in service_ids:
            issues.append(
                f"trips.txt: trip {t['trip_id']} references missing service {t['service_id']}"
            )
        shape_id = t.get("shape_id", "")
        if shape_id and shape_ids and shape_id not in shape_ids:
            issues.append(f"trips.txt: trip {t['trip_id']} references missing shape {shape_id}")

    for st in feed.stop_times:
        if st["trip_id"] not in trip_ids:
            issues.append(f"stop_times.txt: references missing trip {st['trip_id']}")
        if st["stop_id"] not in stop_ids:
            issues.append(f"stop_times.txt: references missing stop {st['stop_id']}")

    if len(stop_ids) != len(feed.stops):
        issues.append("stops.txt: duplicate stop_ids detected")

    for issue in issues:
        sys.stderr.write(f"validation: {issue}\n")
