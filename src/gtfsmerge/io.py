"""CSV reading, ZIP extraction, and GTFS file writing."""

from __future__ import annotations

import csv
import io
import zipfile
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from gtfsmerge.models import (
    Agency,
    Calendar,
    CalendarDate,
    Feed,
    Route,
    ShapePoint,
    Stop,
    StopTime,
    Trip,
)

_GTFS_TABLES: list[tuple[str, type[Any]]] = [
    ("agency.txt", Agency),
    ("calendar.txt", Calendar),
    ("calendar_dates.txt", CalendarDate),
    ("routes.txt", Route),
    ("trips.txt", Trip),
    ("stops.txt", Stop),
    ("stop_times.txt", StopTime),
    ("shapes.txt", ShapePoint),
]


def read_source_rows(source_path: str | Path, filename: str) -> Iterator[dict[str, str]]:
    """Yield each row of *filename* from *source_path* as a dict of strings.

    *source_path* may be a directory of CSV files or a ``.zip`` archive. Returns
    an empty iterator when *filename* does not exist in the source.
    """
    sp = Path(source_path)
    if sp.suffix.lower() == ".zip":
        yield from _read_zip_rows(sp, filename)
    else:
        yield from _read_dir_rows(sp, filename)


def _read_dir_rows(directory: Path, filename: str) -> Iterator[dict[str, str]]:
    filepath = directory / filename
    if not filepath.is_file():
        return
    with open(filepath, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            yield {k.strip(): (v.strip() if isinstance(v, str) else v) for k, v in row.items()}


def _read_zip_rows(zip_path: Path, filename: str) -> Iterator[dict[str, str]]:
    with zipfile.ZipFile(str(zip_path), "r") as zf:
        names = zf.namelist()
        match = _find_matching_file(names, filename)
        if match is None:
            return
        with zf.open(match) as fh:
            text_wrapper = io.TextIOWrapper(fh, encoding="utf-8", newline="")
            reader = csv.DictReader(text_wrapper)
            for row in reader:
                yield {k.strip(): (v.strip() if isinstance(v, str) else v) for k, v in row.items()}


def _find_matching_file(names: list[str], filename: str) -> str | None:
    for name in names:
        if name.endswith(filename) or name == filename:
            return name
    return None


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    """Write *rows* as a CSV file at *path* with the given *fieldnames* order."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_feed(feed: Feed, output_dir: str | Path) -> None:
    """Write all GTFS tables from *feed* into *output_dir*."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    write_csv(out / "agency.txt", feed.agencies, Agency.REQUIRED_FIELDS)
    if feed.calendars:
        write_csv(out / "calendar.txt", feed.calendars, Calendar.REQUIRED_FIELDS)
    if feed.calendar_dates:
        write_csv(out / "calendar_dates.txt", feed.calendar_dates, CalendarDate.REQUIRED_FIELDS)
    write_csv(out / "routes.txt", feed.routes, Route.REQUIRED_FIELDS)
    write_csv(out / "trips.txt", feed.trips, Trip.REQUIRED_FIELDS)
    write_csv(out / "stops.txt", feed.stops, Stop.REQUIRED_FIELDS)
    write_csv(out / "stop_times.txt", feed.stop_times, StopTime.REQUIRED_FIELDS)
    if feed.shapes:
        write_csv(out / "shapes.txt", feed.shapes, ShapePoint.REQUIRED_FIELDS)


def stream_write_shapes(
    output_path: Path,
    sources: dict[str, Path],
    source_shape_ids: dict[str, set[str]],
) -> set[str]:
    """Stream shapes.txt from contributing sources into *output_path*.

    Returns the set of *shape_id* values actually written.
    """
    written: set[str] = set()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as out_fh:
        writer = csv.DictWriter(
            out_fh, fieldnames=ShapePoint.REQUIRED_FIELDS, extrasaction="ignore"
        )
        writer.writeheader()
        for source_name, shape_ids in source_shape_ids.items():
            if not shape_ids:
                continue
            source_path = sources[source_name]
            for row in read_source_rows(source_path, "shapes.txt"):
                if row.get("shape_id", "") in shape_ids:
                    writer.writerow(row)
                    written.add(row.get("shape_id", ""))
    return written
