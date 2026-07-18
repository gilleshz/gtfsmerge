"""Tests for the CLI argument parser."""

from __future__ import annotations

from pathlib import Path

import pytest

from gtfsmerge.cli import _parse_routes, _parse_source


class TestParseSource:
    def test_valid_directory(self, tmp_path: Path) -> None:
        name, path = _parse_source(f"metz={tmp_path}")
        assert name == "metz"
        assert path == tmp_path

    def test_valid_zip(self, tmp_path: Path) -> None:
        zip_path = tmp_path / "feed.zip"
        zip_path.write_text("fake")
        name, path = _parse_source(f"metz={zip_path}")
        assert name == "metz"

    def test_missing_equals(self) -> None:
        with pytest.raises(Exception, match="invalid source format"):
            _parse_source("metz")

    def test_empty_name(self) -> None:
        with pytest.raises(Exception, match="source name must not be empty"):
            _parse_source("=/tmp/foo")

    def test_empty_path(self) -> None:
        with pytest.raises(Exception, match="source path must not be empty"):
            _parse_source("metz=")


class TestParseRoutes:
    def test_single(self) -> None:
        assert _parse_routes("L1") == ["L1"]

    def test_multiple(self) -> None:
        assert _parse_routes("L1,MA,MB") == ["L1", "MA", "MB"]

    def test_with_spaces(self) -> None:
        assert _parse_routes("L1, MA , MB") == ["L1", "MA", "MB"]

    def test_empty(self) -> None:
        assert _parse_routes("") == []

    def test_empty_with_commas(self) -> None:
        assert _parse_routes(",,") == []
