"""Command-line entry point for gtfsmerge."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from gtfsmerge.merge import merge


def _parse_source(value: str) -> tuple[str, Path]:
    """Parse a ``NAME=PATH`` argument into (name, path)."""
    if "=" not in value:
        raise argparse.ArgumentTypeError(f"invalid source format '{value}': expected NAME=PATH")
    name, _, path_str = value.partition("=")
    name = name.strip()
    path_str = path_str.strip()
    if not name:
        raise argparse.ArgumentTypeError("source name must not be empty")
    if not path_str:
        raise argparse.ArgumentTypeError("source path must not be empty")
    path = Path(path_str)
    if name == "osm":
        if not path.is_dir():
            raise argparse.ArgumentTypeError(f"OSM source must be a directory of CSV files: {path}")
    elif path.suffix.lower() not in (".zip",) and not path.is_dir():
        raise argparse.ArgumentTypeError(f"source path must be a directory or .zip file: {path}")
    return (name, path)


def _parse_routes(value: str) -> list[str]:
    """Parse a comma-separated list of route refs."""
    return [r.strip() for r in value.split(",") if r.strip()]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gtfsmerge",
        description="Merge multiple GTFS feeds into one, deduplicating routes and unifying stops.",
    )
    parser.add_argument("--version", action="version", version="gtfsmerge 0.1.0")

    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="output directory for merged GTFS CSV files",
    )
    parser.add_argument(
        "--source",
        type=_parse_source,
        action="append",
        dest="sources",
        required=True,
        metavar="NAME=PATH",
        help="one input source: NAME=PATH (repeat for multiple sources)",
    )
    parser.add_argument(
        "--routes",
        type=_parse_routes,
        default=None,
        help="comma-separated route refs (short_names) to include; omit to include all",
    )
    parser.add_argument(
        "--stop-merge-radius",
        type=float,
        default=50.0,
        metavar="METRES",
        help="merge nearby stops with matching name within this radius in metres (0 disables)",
    )

    return parser


def main(argv: list[str] | None = None) -> None:
    """Parse arguments and run the merge."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    sources: dict[str, Path] = {}
    for name, path in args.sources:
        if name in sources:
            sys.stderr.write(f"warning: duplicate source name '{name}', replacing\n")
        sources[name] = path

    if not sources:
        parser.error("at least one --source is required")

    route_refs = args.routes or []

    try:
        merge(sources, route_refs, args.output, args.stop_merge_radius)
    except Exception as exc:
        sys.stderr.write(f"error: {exc}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
