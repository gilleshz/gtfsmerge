"""Tests for the merge algorithm."""

from __future__ import annotations

from pathlib import Path

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
