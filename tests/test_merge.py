"""Tests for the merge algorithm."""

from __future__ import annotations

from pathlib import Path

from conftest import build_gtfs_dir

from gtfsmerge.merge import merge


class TestBasicMerge:
    def test_metz_only_all_routes(self, metz_feed: Path, tmp_path: Path) -> None:
        output = tmp_path / "out"
        summary = merge({"metz": metz_feed}, [], output)
        assert summary["routes"] == 2
        assert summary["trips"] == 2
        assert summary["stops"] == 4
        assert summary["shape_points"] == 4

    def test_osm_only_all_routes(self, osm_feed: Path, tmp_path: Path) -> None:
        output = tmp_path / "out"
        summary = merge({"osm": osm_feed}, [], output)
        assert summary["routes"] == 2
        assert summary["trips"] == 2
        assert summary["stops"] == 4
        assert summary["shape_points"] == 4


class TestRouteFiltering:
    def test_select_single_route(self, metz_feed: Path, tmp_path: Path) -> None:
        output = tmp_path / "out"
        summary = merge({"metz": metz_feed}, ["L1"], output)
        assert summary["routes"] == 1
        assert summary["trips"] == 1

    def test_select_nonexistent_route(self, metz_feed: Path, tmp_path: Path) -> None:
        output = tmp_path / "out"
        summary = merge({"metz": metz_feed}, ["XX"], output)
        assert summary["routes"] == 0

    def test_select_multiple_routes(self, osm_feed: Path, tmp_path: Path) -> None:
        output = tmp_path / "out"
        summary = merge({"osm": osm_feed}, ["L1", "MB"], output)
        assert summary["routes"] == 2
        assert summary["trips"] == 2


class TestDeduplication:
    def test_gtfs_wins_over_osm(self, metz_feed: Path, osm_feed: Path, tmp_path: Path) -> None:
        """L1 appears in both feeds; the GTFS (metz) version should be selected."""
        output = tmp_path / "out"
        summary = merge({"metz": metz_feed, "osm": osm_feed}, ["L1"], output)
        routes_file = output / "routes.txt"
        content = routes_file.read_text()
        assert "metz_L1" in content
        assert "osm_L1" not in content
        assert summary["routes"] == 1

    def test_osm_only_for_unique_route(
        self, metz_feed: Path, osm_feed: Path, tmp_path: Path
    ) -> None:
        """MB only exists in the OSM feed, should be included."""
        output = tmp_path / "out"
        summary = merge({"metz": metz_feed, "osm": osm_feed}, ["MB"], output)
        assert summary["routes"] == 1
        routes_file = output / "routes.txt"
        content = routes_file.read_text()
        assert "osm_MB" in content
        assert "MB" in content

    def test_mixed_sources(self, metz_feed: Path, osm_feed: Path, tmp_path: Path) -> None:
        """Select L1 (GTFS wins) and MB (OSM only), both should be present."""
        output = tmp_path / "out"
        summary = merge({"metz": metz_feed, "osm": osm_feed}, ["L1", "MB"], output)
        assert summary["routes"] == 2
        routes_file = output / "routes.txt"
        content = routes_file.read_text()
        assert "metz_L1" in content
        assert "osm_MB" in content


class TestStopCoordinateRemapping:
    def test_stop_ids_are_coordinate_based(self, metz_feed: Path, tmp_path: Path) -> None:
        output = tmp_path / "out"
        merge({"metz": metz_feed}, ["L1"], output)
        stops = (output / "stops.txt").read_text()
        assert "S_49.1200_6.1800" in stops
        assert "S_49.1250_6.1850" in stops

    def test_stop_times_reference_new_ids(self, metz_feed: Path, tmp_path: Path) -> None:
        output = tmp_path / "out"
        merge({"metz": metz_feed}, ["L1"], output)
        stop_times = (output / "stop_times.txt").read_text()
        assert "stop_a" not in stop_times
        assert "S_49.1200_6.1800" in stop_times

    def test_same_physical_stop_same_id(
        self, metz_feed: Path, osm_feed: Path, tmp_path: Path
    ) -> None:
        """stop_a in metz and osm_stop_a in osm are at the same coordinates, should merge."""
        output = tmp_path / "out"
        merge({"metz": metz_feed, "osm": osm_feed}, ["L1"], output)
        stops_content = (output / "stops.txt").read_text()
        count = stops_content.count("S_49.1200_6.1800")
        assert count == 1


class TestOutputFiles:
    def test_all_required_files_present(self, metz_feed: Path, tmp_path: Path) -> None:
        output = tmp_path / "out"
        merge({"metz": metz_feed}, [], output)
        required = [
            "agency.txt",
            "routes.txt",
            "trips.txt",
            "stops.txt",
            "stop_times.txt",
        ]
        for fname in required:
            assert (output / fname).is_file(), f"missing {fname}"

    def test_shapes_written_when_present(self, metz_feed: Path, tmp_path: Path) -> None:
        output = tmp_path / "out"
        merge({"metz": metz_feed}, [], output)
        assert (output / "shapes.txt").is_file()

    def test_calendar_written(self, metz_feed: Path, tmp_path: Path) -> None:
        output = tmp_path / "out"
        merge({"metz": metz_feed}, [], output)
        assert (output / "calendar.txt").is_file()


class TestZIPSource:
    def test_zip_source_read(self, metz_zip: Path, tmp_path: Path) -> None:
        output = tmp_path / "out"
        summary = merge({"metz": metz_zip}, ["L1"], output)
        assert summary["routes"] == 1
        assert summary["trips"] == 1
        assert (output / "routes.txt").is_file()


class TestParentStationRemap:
    def test_parent_station_remapped_after_fuzzy_merge(self, tmp_path: Path) -> None:
        feed_a = tmp_path / "feed_a"
        build_gtfs_dir(
            feed_a,
            {
                "agency.txt": (
                    ["agency_id", "agency_name", "agency_url", "agency_timezone"],
                    [["a", "Agency A", "https://a.example", "Europe/Paris"]],
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
                    [["r_L1", "a", "L1", "Line 1", "3", "FF0000", "FFFFFF"]],
                ),
                "trips.txt": (
                    ["route_id", "service_id", "trip_id"],
                    [["r_L1", "WEEK", "t_L1"]],
                ),
                "stops.txt": (
                    ["stop_id", "stop_name", "stop_lat", "stop_lon", "parent_station"],
                    [
                        ["par_A", "Parent A", "49.1200", "6.1800", ""],
                        ["child_A1", "Child A1", "49.1190", "6.1790", "par_A"],
                    ],
                ),
                "stop_times.txt": (
                    ["trip_id", "arrival_time", "departure_time", "stop_id", "stop_sequence"],
                    [
                        ["t_L1", "08:00:00", "08:00:00", "par_A", "1"],
                        ["t_L1", "08:10:00", "08:10:00", "child_A1", "2"],
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
            },
        )

        feed_b = tmp_path / "feed_b"
        build_gtfs_dir(
            feed_b,
            {
                "agency.txt": (
                    ["agency_id", "agency_name", "agency_url", "agency_timezone"],
                    [["b", "Agency B", "https://b.example", "Europe/Paris"]],
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
                    [["r_MA", "b", "MA", "Line MA", "3", "00FF00", "FFFFFF"]],
                ),
                "trips.txt": (
                    ["route_id", "service_id", "trip_id"],
                    [["r_MA", "WEEK", "t_MA"]],
                ),
                "stops.txt": (
                    ["stop_id", "stop_name", "stop_lat", "stop_lon", "parent_station"],
                    [
                        ["par_A_gtfs", "Parent A", "49.1202", "6.1802", ""],
                        ["child_A2", "Child A2", "49.1192", "6.1792", "par_A_gtfs"],
                    ],
                ),
                "stop_times.txt": (
                    ["trip_id", "arrival_time", "departure_time", "stop_id", "stop_sequence"],
                    [
                        ["t_MA", "09:00:00", "09:00:00", "par_A_gtfs", "1"],
                        ["t_MA", "09:10:00", "09:10:00", "child_A2", "2"],
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
            },
        )

        output = tmp_path / "out"
        merge(
            {"feed_a": feed_a, "feed_b": feed_b},
            ["L1", "MA"],
            output,
            stop_merge_radius=50.0,
        )

        stops_content = (output / "stops.txt").read_text()
        parent_a_count = stops_content.count("Parent A")
        assert parent_a_count == 1, f"Expected 1 'Parent A' stop, got {parent_a_count}"
        assert "Parent A" in stops_content
