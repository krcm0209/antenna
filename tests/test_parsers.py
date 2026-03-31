"""Tests for antenna.sync.parsers — FCC data format parsing utilities."""

import pytest

from antenna.sync.parsers import dms_to_decimal, parse_pipe_float, parse_pipe_int


class TestDmsToDecimal:
    def test_basic(self):
        assert dms_to_decimal(40, 44, 54.36) == pytest.approx(40.7484, abs=1e-4)

    def test_zero_minutes_seconds(self):
        assert dms_to_decimal(90, 0, 0.0) == 90.0

    def test_zero_degrees(self):
        assert dms_to_decimal(0, 30, 0.0) == pytest.approx(0.5)


class TestParsePipeFloat:
    def test_plain_number(self):
        assert parse_pipe_float("5.2") == 5.2

    def test_with_trailing_unit(self):
        assert parse_pipe_float("5.2    kW") == 5.2

    def test_with_whitespace(self):
        assert parse_pipe_float("  415.0   ") == 415.0

    def test_empty_string(self):
        assert parse_pipe_float("") is None

    def test_whitespace_only(self):
        assert parse_pipe_float("   ") is None

    def test_garbage(self):
        assert parse_pipe_float("N/A") is None


class TestParsePipeInt:
    def test_normal(self):
        assert parse_pipe_int("12345") == 12345

    def test_with_whitespace(self):
        assert parse_pipe_int("  67890  ") == 67890

    def test_empty_string(self):
        assert parse_pipe_int("") is None

    def test_garbage(self):
        assert parse_pipe_int("abc") is None

    def test_float_string(self):
        # int("5.2") raises ValueError — should return None
        assert parse_pipe_int("5.2") is None
