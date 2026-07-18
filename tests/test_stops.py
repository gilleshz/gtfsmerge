"""Tests for coordinate-based stop ID generation and deduplication."""

from __future__ import annotations

from gtfsmerge.stops import (
    coord_to_stop_id,
    fuzzy_merge_stops,
    haversine_distance_m,
    merge_stops,
    normalize_stop_name,
    remap_stop_times,
)


class TestCoordToStopId:
    def test_format(self) -> None:
        assert coord_to_stop_id(48.5839, 7.7455) == "S_48.5839_7.7455"

    def test_format_from_strings(self) -> None:
        assert coord_to_stop_id("48.5839", "7.7455") == "S_48.5839_7.7455"

    def test_same_coords_same_id(self) -> None:
        a = coord_to_stop_id(49.12, 6.18)
        b = coord_to_stop_id(49.12, 6.18)
        assert a == b

    def test_different_coords_different_id(self) -> None:
        a = coord_to_stop_id(49.12, 6.18)
        b = coord_to_stop_id(49.13, 6.19)
        assert a != b

    def test_rounding_to_4_decimals(self) -> None:
        a = coord_to_stop_id(48.58392, 7.74553)
        b = coord_to_stop_id(48.58391, 7.74552)
        assert a == b

    def test_negative_coords(self) -> None:
        result = coord_to_stop_id(-33.8651, 151.2099)
        assert result.startswith("S_-33.8651")

    def test_zero_coords(self) -> None:
        assert coord_to_stop_id(0, 0) == "S_0.0000_0.0000"


class TestRemapStopTimes:
    def test_remap_single_stop(self) -> None:
        stop_times = [
            {"trip_id": "t1", "stop_id": "old_a", "stop_sequence": "1"},
        ]
        old_to_new = {"old_a": "S_49.1200_6.1800"}
        result = remap_stop_times(stop_times, old_to_new)
        assert result[0]["stop_id"] == "S_49.1200_6.1800"

    def test_remap_preserves_other_fields(self) -> None:
        stop_times = [
            {
                "trip_id": "t1",
                "stop_id": "old_a",
                "stop_sequence": "1",
                "arrival_time": "08:00:00",
            },
        ]
        result = remap_stop_times(stop_times, {"old_a": "new_a"})
        assert result[0]["trip_id"] == "t1"
        assert result[0]["stop_sequence"] == "1"
        assert result[0]["arrival_time"] == "08:00:00"
        assert result[0]["stop_id"] == "new_a"

    def test_unmatched_stop_id_preserved(self) -> None:
        stop_times = [{"trip_id": "t1", "stop_id": "unknown", "stop_sequence": "1"}]
        result = remap_stop_times(stop_times, {"other": "new"})
        assert result[0]["stop_id"] == "unknown"

    def test_empty_stop_id(self) -> None:
        stop_times = [{"trip_id": "t1", "stop_id": "", "stop_sequence": "1"}]
        result = remap_stop_times(stop_times, {"": "new"})
        assert result[0]["stop_id"] == ""


class TestMergeStops:
    def test_new_id_inserted(self) -> None:
        stops: dict[str, dict[str, str]] = {}
        s = {"stop_id": "S_1.0000_2.0000", "stop_name": "Central"}
        merge_stops(stops, s)
        assert "S_1.0000_2.0000" in stops
        assert stops["S_1.0000_2.0000"]["stop_name"] == "Central"

    def test_first_name_wins(self) -> None:
        stops: dict[str, dict[str, str]] = {}
        merge_stops(stops, {"stop_id": "X", "stop_name": "First", "stop_lat": "1"})
        merge_stops(stops, {"stop_id": "X", "stop_name": "Second", "stop_lat": "2"})
        assert stops["X"]["stop_name"] == "First"
        assert stops["X"]["stop_lat"] == "1"

    def test_empty_stop_id_ignored(self) -> None:
        stops: dict[str, dict[str, str]] = {}
        merge_stops(stops, {"stop_id": "", "stop_name": "Empty"})
        assert "" not in stops
        assert len(stops) == 0


class TestNormalizeStopName:
    def test_lowercases(self) -> None:
        assert normalize_stop_name("ROI GEORGE") == "roi george"

    def test_strips_and_collapses_whitespace(self) -> None:
        assert normalize_stop_name("  Roi   George ") == "roi george"

    def test_title_case_preserved_as_lower(self) -> None:
        assert normalize_stop_name("Roi George") == "roi george"

    def test_mixed(self) -> None:
        assert normalize_stop_name("Gare De Metz-Ville") == "gare de metz-ville"

    def test_accented_vs_unaccented(self) -> None:
        assert normalize_stop_name("RÉPUBLIQUE") == normalize_stop_name("République")

    def test_accented_lowercase_vs_unaccented(self) -> None:
        assert normalize_stop_name("république") == normalize_stop_name("REPUBLIQUE")


class TestHaversineDistance:
    def test_same_point(self) -> None:
        assert haversine_distance_m(49.12, 6.18, 49.12, 6.18) == 0.0

    def test_roughly_111km_per_degree(self) -> None:
        d = haversine_distance_m(49.0, 6.0, 50.0, 6.0)
        assert 110_000 < d < 112_000

    def test_short_distance(self) -> None:
        d = haversine_distance_m(49.1200, 6.1800, 49.1204, 6.1804)
        assert 40 < d < 60


class TestFuzzyMergeStops:
    def test_no_merge_when_different_names(self) -> None:
        stops = {
            "A": {
                "stop_id": "A",
                "stop_name": "Central",
                "stop_lat": "49.1200",
                "stop_lon": "6.1800",
            },
            "B": {
                "stop_id": "B",
                "stop_name": "North",
                "stop_lat": "49.1204",
                "stop_lon": "6.1804",
            },
        }
        merged, remap = fuzzy_merge_stops(stops, 50.0)
        assert len(merged) == 2
        assert remap == {}

    def test_no_merge_when_too_far(self) -> None:
        stops = {
            "A": {
                "stop_id": "A",
                "stop_name": "Central",
                "stop_lat": "49.1200",
                "stop_lon": "6.1800",
            },
            "B": {
                "stop_id": "B",
                "stop_name": "Central",
                "stop_lat": "49.1300",
                "stop_lon": "6.1900",
            },
        }
        merged, remap = fuzzy_merge_stops(stops, 50.0)
        assert len(merged) == 2
        assert remap == {}

    def test_merges_same_name_within_radius(self) -> None:
        stops = {
            "A": {
                "stop_id": "A",
                "stop_name": "Central",
                "stop_lat": "49.1200",
                "stop_lon": "6.1800",
            },
            "B": {
                "stop_id": "B",
                "stop_name": "Central",
                "stop_lat": "49.1202",
                "stop_lon": "6.1802",
            },
        }
        merged, remap = fuzzy_merge_stops(stops, 50.0)
        assert len(merged) == 1
        assert remap == {"B": "A"}

    def test_merges_case_insensitive(self) -> None:
        stops = {
            "A": {
                "stop_id": "A",
                "stop_name": "Roi George",
                "stop_lat": "49.1200",
                "stop_lon": "6.1800",
            },
            "B": {
                "stop_id": "B",
                "stop_name": "ROI GEORGE",
                "stop_lat": "49.1202",
                "stop_lon": "6.1802",
            },
        }
        merged, remap = fuzzy_merge_stops(stops, 50.0)
        assert len(merged) == 1
        assert remap == {"B": "A"}

    def test_merges_with_extra_whitespace(self) -> None:
        stops = {
            "A": {
                "stop_id": "A",
                "stop_name": "  Roi  George ",
                "stop_lat": "49.1200",
                "stop_lon": "6.1800",
            },
            "B": {
                "stop_id": "B",
                "stop_name": "Roi George",
                "stop_lat": "49.1202",
                "stop_lon": "6.1802",
            },
        }
        merged, remap = fuzzy_merge_stops(stops, 50.0)
        assert len(merged) == 1

    def test_zero_radius_disables_merge(self) -> None:
        stops = {
            "A": {
                "stop_id": "A",
                "stop_name": "Central",
                "stop_lat": "49.1200",
                "stop_lon": "6.1800",
            },
            "B": {
                "stop_id": "B",
                "stop_name": "Central",
                "stop_lat": "49.1202",
                "stop_lon": "6.1802",
            },
        }
        merged, remap = fuzzy_merge_stops(stops, 0.0)
        assert len(merged) == 2
        assert remap == {}

    def test_three_way_merge(self) -> None:
        stops = {
            "A": {
                "stop_id": "A",
                "stop_name": "Central",
                "stop_lat": "49.1200",
                "stop_lon": "6.1800",
            },
            "B": {
                "stop_id": "B",
                "stop_name": "Central",
                "stop_lat": "49.1202",
                "stop_lon": "6.1802",
            },
            "C": {
                "stop_id": "C",
                "stop_name": "Central",
                "stop_lat": "49.1201",
                "stop_lon": "6.1801",
            },
        }
        merged, remap = fuzzy_merge_stops(stops, 50.0)
        assert len(merged) == 1

    def test_empty_name_stops_not_merged(self) -> None:
        stops = {
            "A": {"stop_id": "A", "stop_name": "", "stop_lat": "49.1200", "stop_lon": "6.1800"},
            "B": {"stop_id": "B", "stop_name": "", "stop_lat": "49.1202", "stop_lon": "6.1802"},
        }
        merged, remap = fuzzy_merge_stops(stops, 50.0)
        assert len(merged) == 2
