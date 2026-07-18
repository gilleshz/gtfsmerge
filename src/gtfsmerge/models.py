"""GTFS entity dataclasses and field-name constants."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Agency:
    agency_id: str = ""
    agency_name: str = ""
    agency_url: str = ""
    agency_timezone: str = ""

    REQUIRED_FIELDS = ["agency_id", "agency_name", "agency_url", "agency_timezone"]


@dataclass(frozen=True)
class Calendar:
    service_id: str = ""
    monday: str = "0"
    tuesday: str = "0"
    wednesday: str = "0"
    thursday: str = "0"
    friday: str = "0"
    saturday: str = "0"
    sunday: str = "0"
    start_date: str = ""
    end_date: str = ""

    REQUIRED_FIELDS = [
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
    ]


@dataclass(frozen=True)
class CalendarDate:
    service_id: str = ""
    date: str = ""
    exception_type: str = ""

    REQUIRED_FIELDS = ["service_id", "date", "exception_type"]


@dataclass(frozen=True)
class Route:
    route_id: str = ""
    agency_id: str = ""
    route_short_name: str = ""
    route_long_name: str = ""
    route_type: str = ""
    route_color: str = ""
    route_text_color: str = ""

    REQUIRED_FIELDS = [
        "route_id",
        "agency_id",
        "route_short_name",
        "route_long_name",
        "route_type",
        "route_color",
        "route_text_color",
    ]


@dataclass(frozen=True)
class Trip:
    route_id: str = ""
    service_id: str = ""
    trip_id: str = ""
    shape_id: str = ""
    trip_headsign: str = ""
    direction_id: str = ""
    block_id: str = ""

    REQUIRED_FIELDS = [
        "route_id",
        "service_id",
        "trip_id",
        "shape_id",
        "trip_headsign",
        "direction_id",
        "block_id",
    ]


@dataclass(frozen=True)
class Stop:
    stop_id: str = ""
    stop_name: str = ""
    stop_lat: str = ""
    stop_lon: str = ""
    stop_desc: str = ""
    zone_id: str = ""
    location_type: str = ""
    parent_station: str = ""

    REQUIRED_FIELDS = ["stop_id", "stop_name", "stop_lat", "stop_lon"]


@dataclass(frozen=True)
class StopTime:
    trip_id: str = ""
    arrival_time: str = ""
    departure_time: str = ""
    stop_id: str = ""
    stop_sequence: str = ""
    shape_dist_traveled: str = ""

    REQUIRED_FIELDS = [
        "trip_id",
        "arrival_time",
        "departure_time",
        "stop_id",
        "stop_sequence",
    ]


@dataclass(frozen=True)
class ShapePoint:
    shape_id: str = ""
    shape_pt_lat: str = ""
    shape_pt_lon: str = ""
    shape_pt_sequence: str = ""
    shape_dist_traveled: str = ""

    REQUIRED_FIELDS = [
        "shape_id",
        "shape_pt_lat",
        "shape_pt_lon",
        "shape_pt_sequence",
    ]


@dataclass
class Feed:
    agencies: list[dict[str, str]] = field(default_factory=list)
    calendars: list[dict[str, str]] = field(default_factory=list)
    calendar_dates: list[dict[str, str]] = field(default_factory=list)
    routes: list[dict[str, str]] = field(default_factory=list)
    trips: list[dict[str, str]] = field(default_factory=list)
    stops: list[dict[str, str]] = field(default_factory=list)
    stop_times: list[dict[str, str]] = field(default_factory=list)
    shapes: list[dict[str, str]] = field(default_factory=list)
