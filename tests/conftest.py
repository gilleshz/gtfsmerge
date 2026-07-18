"""Shared fixtures for gtfsmerge tests."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

import pytest


def _write_csv(path: Path, header: list[str], rows: list[list[Any]]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)


def build_gtfs_dir(root: Path, spec: dict[str, tuple[list[str], list[list[Any]]]]) -> None:
    """Write GTFS CSV files into *root* from a *spec* dict.

    *spec* maps filename to ``(header, rows)`` where *rows* is a list of lists.
    """
    root.mkdir(parents=True, exist_ok=True)
    for filename, (header, rows) in spec.items():
        _write_csv(root / filename, header, rows)


@pytest.fixture
def metz_feed(tmp_path: Path) -> Path:
    """A synthetic Metz GTFS feed (directory) with two bus routes."""
    spec: dict[str, tuple[list[str], list[list[Any]]]] = {
        "agency.txt": (
            ["agency_id", "agency_name", "agency_url", "agency_timezone"],
            [["metz_agency", "Le Met'", "https://lemet.fr", "Europe/Paris"]],
        ),
        "routes.txt": (
            [
                "route_id",
                "agency_id",
                "route_short_name",
                "route_long_name",
                "route_type",
                "route_color",
                "route_text_color",
            ],
            [
                ["metz_L1", "metz_agency", "L1", "Ligne 1", "3", "FF0000", "FFFFFF"],
                ["metz_MA", "metz_agency", "MA", "Mettis A", "0", "00AA00", "FFFFFF"],
            ],
        ),
        "trips.txt": (
            ["route_id", "service_id", "trip_id", "shape_id"],
            [
                ["metz_L1", "WEEK", "trip_L1_out", "shape_L1"],
                ["metz_MA", "WEEK", "trip_MA_out", "shape_MA"],
            ],
        ),
        "stops.txt": (
            ["stop_id", "stop_name", "stop_lat", "stop_lon"],
            [
                ["stop_a", "Station A", "49.1200", "6.1800"],
                ["stop_b", "Station B", "49.1250", "6.1850"],
                ["stop_c", "Station C", "49.1300", "6.1900"],
                ["stop_d", "Station D", "49.1350", "6.1950"],
            ],
        ),
        "stop_times.txt": (
            ["trip_id", "arrival_time", "departure_time", "stop_id", "stop_sequence"],
            [
                ["trip_L1_out", "08:00:00", "08:00:00", "stop_a", "1"],
                ["trip_L1_out", "08:15:00", "08:15:00", "stop_b", "2"],
                ["trip_MA_out", "09:00:00", "09:00:00", "stop_c", "1"],
                ["trip_MA_out", "09:10:00", "09:10:00", "stop_d", "2"],
            ],
        ),
        "shapes.txt": (
            ["shape_id", "shape_pt_lat", "shape_pt_lon", "shape_pt_sequence"],
            [
                ["shape_L1", "49.1200", "6.1800", "1"],
                ["shape_L1", "49.1250", "6.1850", "2"],
                ["shape_MA", "49.1300", "6.1900", "1"],
                ["shape_MA", "49.1350", "6.1950", "2"],
            ],
        ),
        "calendar.txt": (
            [
                "service_id",
                "monday",
                "tuesday",
                "wednesday",
                "thursday",
                "friday",
                "saturday",
                "sunday",
                "start_date",
                "end_date",
            ],
            [["WEEK", "1", "1", "1", "1", "1", "0", "0", "20260101", "20261231"]],
        ),
    }
    path = tmp_path / "metz"
    build_gtfs_dir(path, spec)
    return path


@pytest.fixture
def osm_feed(tmp_path: Path) -> Path:
    """A synthetic OSM-derived feed with an overlapping L1 route and an extra MB route."""
    spec: dict[str, tuple[list[str], list[list[Any]]]] = {
        "agency.txt": (
            ["agency_id", "agency_name", "agency_url", "agency_timezone"],
            [["osm_agency", "OpenStreetMap", "https://osm.org", "Europe/Paris"]],
        ),
        "routes.txt": (
            [
                "route_id",
                "agency_id",
                "route_short_name",
                "route_long_name",
                "route_type",
                "route_color",
                "route_text_color",
            ],
            [
                ["osm_L1", "osm_agency", "L1", "Ligne 1 (OSM)", "3", "DD0000", "FFFFFF"],
                ["osm_MB", "osm_agency", "MB", "Mettis B", "0", "0000DD", "FFFFFF"],
            ],
        ),
        "trips.txt": (
            ["route_id", "service_id", "trip_id", "shape_id"],
            [
                ["osm_L1", "WEEK", "osm_trip_L1", "osm_shape_L1"],
                ["osm_MB", "WEEK", "osm_trip_MB", "osm_shape_MB"],
            ],
        ),
        "stops.txt": (
            ["stop_id", "stop_name", "stop_lat", "stop_lon"],
            [
                ["osm_stop_a", "A OSM", "49.1200", "6.1800"],
                ["osm_stop_b", "B OSM", "49.1250", "6.1850"],
                ["osm_stop_e", "Station E", "49.1400", "6.2000"],
                ["osm_stop_f", "Station F", "49.1450", "6.2050"],
            ],
        ),
        "stop_times.txt": (
            ["trip_id", "arrival_time", "departure_time", "stop_id", "stop_sequence"],
            [
                ["osm_trip_L1", "08:00:00", "08:00:00", "osm_stop_a", "1"],
                ["osm_trip_L1", "08:10:00", "08:10:00", "osm_stop_b", "2"],
                ["osm_trip_MB", "10:00:00", "10:00:00", "osm_stop_e", "1"],
                ["osm_trip_MB", "10:12:00", "10:12:00", "osm_stop_f", "2"],
            ],
        ),
        "shapes.txt": (
            ["shape_id", "shape_pt_lat", "shape_pt_lon", "shape_pt_sequence"],
            [
                ["osm_shape_L1", "49.1200", "6.1800", "1"],
                ["osm_shape_L1", "49.1250", "6.1850", "2"],
                ["osm_shape_MB", "49.1400", "6.2000", "1"],
                ["osm_shape_MB", "49.1450", "6.2050", "2"],
            ],
        ),
        "calendar.txt": (
            [
                "service_id",
                "monday",
                "tuesday",
                "wednesday",
                "thursday",
                "friday",
                "saturday",
                "sunday",
                "start_date",
                "end_date",
            ],
            [["WEEK", "1", "1", "1", "1", "1", "0", "0", "20260101", "20261231"]],
        ),
    }
    path = tmp_path / "osm"
    build_gtfs_dir(path, spec)
    return path


@pytest.fixture
def metz_zip(tmp_path: Path) -> Path:
    """Same as metz_feed but packaged as a .zip file."""
    import zipfile

    feed_dir = tmp_path / "metz"
    spec: dict[str, tuple[list[str], list[list[Any]]]] = {
        "agency.txt": (
            ["agency_id", "agency_name", "agency_url", "agency_timezone"],
            [["metz_agency", "Le Met'", "https://lemet.fr", "Europe/Paris"]],
        ),
        "routes.txt": (
            [
                "route_id",
                "agency_id",
                "route_short_name",
                "route_long_name",
                "route_type",
                "route_color",
                "route_text_color",
            ],
            [
                ["metz_L1", "metz_agency", "L1", "Ligne 1", "3", "FF0000", "FFFFFF"],
            ],
        ),
        "trips.txt": (
            ["route_id", "service_id", "trip_id", "shape_id"],
            [["metz_L1", "WEEK", "trip_L1_out", "shape_L1"]],
        ),
        "stops.txt": (
            ["stop_id", "stop_name", "stop_lat", "stop_lon"],
            [
                ["stop_a", "Station A", "49.1200", "6.1800"],
                ["stop_b", "Station B", "49.1250", "6.1850"],
            ],
        ),
        "stop_times.txt": (
            ["trip_id", "arrival_time", "departure_time", "stop_id", "stop_sequence"],
            [
                ["trip_L1_out", "08:00:00", "08:00:00", "stop_a", "1"],
                ["trip_L1_out", "08:15:00", "08:15:00", "stop_b", "2"],
            ],
        ),
        "calendar.txt": (
            [
                "service_id",
                "monday",
                "tuesday",
                "wednesday",
                "thursday",
                "friday",
                "saturday",
                "sunday",
                "start_date",
                "end_date",
            ],
            [["WEEK", "1", "1", "1", "1", "1", "0", "0", "20260101", "20261231"]],
        ),
    }
    build_gtfs_dir(feed_dir, spec)
    zip_path = tmp_path / "metz.zip"
    with zipfile.ZipFile(str(zip_path), "w", zipfile.ZIP_DEFLATED) as zf:
        for txt_file in sorted(feed_dir.glob("*.txt")):
            zf.write(txt_file, txt_file.name)
    return zip_path
