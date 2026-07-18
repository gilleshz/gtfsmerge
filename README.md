# gtfsmerge

Merge multiple GTFS feeds into one, deduplicating routes by short name and
unifying stops by geographic coordinates.

## Installation

```bash
pip install git+https://github.com/gilleshz/gtfsmerge.git
```

Or from a local checkout:

```bash
git clone https://github.com/gilleshz/gtfsmerge.git
cd gtfsmerge
pip install -e .
```

## Quick start

Merge an OSM-derived GTFS directory with a user-provided GTFS zip, selecting
specific route short names:

```bash
gtfsmerge --output /tmp/merged/ \
  --source osm=/tmp/osm-gtfs-output/ \
  --source metz=/tmp/metz-gtfs.zip \
  --routes L1,L2,MA,MB
```

Only a user GTFS feed (no OSM source):

```bash
gtfsmerge --output /tmp/merged/ \
  --source dublin=/tmp/dublin-bus.zip \
  --routes 41,16,145
```

Omit `--routes` to include all routes from all sources (with deduplication):

```bash
gtfsmerge --output /tmp/merged/ \
  --source osm=/tmp/osm-gtfs-output/ \
  --source metz=/tmp/metz-gtfs.zip
```

## Options

| Flag | Description |
|---|---|
| `--output DIR` | Output directory for merged GTFS CSV files (required) |
| `--source NAME=PATH` | Input source: a label and path to a directory or `.zip` (repeatable) |
| `--routes REFS` | Comma-separated route short names to include (omit for all) |
| `--version` | Print version and exit |

## How it works

For each requested route short name:

1. The tool checks GTFS sources first, then OSM sources (the first match wins).
2. It collects the matching route, its trips, stop times, stops, and shape
   points from the winning source.
3. Stop IDs are regenerated from coordinates (`S_{lat:.4f}_{lon:.4f}`), so
   the same physical station gets the same ID across sources.
4. Agencies and calendars from contributing sources are preserved as-is.

The output is a directory of standard GTFS CSV files ready for any GTFS consumer.

## Development

```bash
pip install -e ".[dev]"
ruff format src/ tests/
ruff check src/ tests/
mypy src/
pytest
```

## License

MIT
