"""Tests for FCC station line parsers and helpers."""

import pytest

from antenna.sync.lms import _parse_am_line, _parse_fm_line, _parse_frequency, _parse_lat_lon


def _make_fm_fields(**overrides) -> list[str]:
    """Build a 41-element FM field list with sane defaults."""
    fields = [""] * 41
    fields[1] = overrides.get("callsign", "WTEST-FM")
    fields[2] = overrides.get("frequency", "99.1  MHz")
    fields[3] = overrides.get("service", "FM")
    fields[4] = overrides.get("channel", "256")
    fields[7] = overrides.get("station_class", "C1")
    fields[9] = overrides.get("status", "LIC")
    fields[10] = overrides.get("city", "TESTVILLE")
    fields[11] = overrides.get("state", "NJ")
    fields[13] = overrides.get("application_id", "12345")
    fields[14] = overrides.get("erp_h", "50.0  kW")
    fields[15] = overrides.get("erp_v", "")
    fields[16] = overrides.get("haat_h", "300.0  m")
    fields[17] = overrides.get("haat_v", "")
    fields[18] = overrides.get("facility_id", "91001")
    fields[19] = overrides.get("lat_dir", "N")
    fields[20] = overrides.get("lat_deg", "40")
    fields[21] = overrides.get("lat_min", "44")
    fields[22] = overrides.get("lat_sec", "54.36")
    fields[23] = overrides.get("lon_dir", "W")
    fields[24] = overrides.get("lon_deg", "74")
    fields[25] = overrides.get("lon_min", "0")
    fields[26] = overrides.get("lon_sec", "21.48")
    fields[27] = overrides.get("licensee", "Test Broadcasting Inc")
    fields[31] = overrides.get("rcamsl", "415.0  m")
    fields[38] = overrides.get("lms_uuid", "abc-123")
    return fields


def _make_am_fields(**overrides) -> list[str]:
    """Build a 35-element AM field list with sane defaults."""
    fields = [""] * 35
    fields[1] = overrides.get("callsign", "KTEST")
    fields[2] = overrides.get("frequency", "710   kHz")
    fields[3] = overrides.get("service", "AM")
    fields[4] = overrides.get("channel", "")
    fields[7] = overrides.get("station_class", "B")
    fields[9] = overrides.get("status", "LIC")
    fields[10] = overrides.get("city", "LOS ANGELES")
    fields[11] = overrides.get("state", "CA")
    fields[13] = overrides.get("application_id", "67890")
    fields[14] = overrides.get("erp", "5.0   kW")
    fields[18] = overrides.get("facility_id", "92001")
    fields[19] = overrides.get("lat_dir", "N")
    fields[20] = overrides.get("lat_deg", "34")
    fields[21] = overrides.get("lat_min", "3")
    fields[22] = overrides.get("lat_sec", "8.04")
    fields[23] = overrides.get("lon_dir", "W")
    fields[24] = overrides.get("lon_deg", "118")
    fields[25] = overrides.get("lon_min", "14")
    fields[26] = overrides.get("lon_sec", "37.26")
    fields[27] = overrides.get("licensee", "AM Test Corp")
    return fields


class TestParseFmLine:
    def test_valid(self):
        station = _parse_fm_line(_make_fm_fields())
        assert station is not None
        assert station.facility_id == 91001
        assert station.callsign == "WTEST-FM"
        assert station.service == "FM"
        assert station.frequency == pytest.approx(99.1)
        assert station.erp_kw == pytest.approx(50.0)
        assert station.antenna_lat == pytest.approx(40.7484, abs=1e-3)
        assert station.antenna_lon == pytest.approx(-74.006, abs=1e-3)
        assert station.state == "NJ"

    def test_missing_facility_id(self):
        assert _parse_fm_line(_make_fm_fields(facility_id="")) is None

    def test_missing_coordinates(self):
        assert _parse_fm_line(_make_fm_fields(lat_deg="")) is None


class TestParseAmLine:
    def test_valid(self):
        station = _parse_am_line(_make_am_fields())
        assert station is not None
        assert station.facility_id == 92001
        assert station.callsign == "KTEST"
        assert station.service == "AM"
        assert station.erp_kw == pytest.approx(5.0)
        assert station.antenna_lat == pytest.approx(34.0522, abs=1e-3)
        assert station.antenna_lon == pytest.approx(-118.2437, abs=1e-3)

    def test_missing_facility_id(self):
        assert _parse_am_line(_make_am_fields(facility_id="")) is None


class TestParseFrequency:
    def test_mhz(self):
        assert _parse_frequency("88.1  MHz") == pytest.approx(88.1)

    def test_khz_converted_to_mhz(self):
        assert _parse_frequency("710   kHz") == pytest.approx(0.71)

    def test_plain_number(self):
        assert _parse_frequency("99.1") == pytest.approx(99.1)

    def test_empty(self):
        assert _parse_frequency("") is None


class TestParseLatLon:
    def test_north_east_positive(self):
        fields = [""] * 27
        fields[19] = "N"
        fields[20] = "40"
        fields[21] = "44"
        fields[22] = "54.36"
        fields[23] = "E"
        fields[24] = "74"
        fields[25] = "0"
        fields[26] = "21.48"
        lat = _parse_lat_lon(fields, lat_dir=19, lat_deg=20, lat_min=21, lat_sec=22)
        lon = _parse_lat_lon(fields, lat_dir=23, lat_deg=24, lat_min=25, lat_sec=26)
        assert lat is not None and lat > 0
        assert lon is not None and lon > 0

    def test_south_west_negative(self):
        fields = [""] * 27
        fields[19] = "S"
        fields[20] = "33"
        fields[21] = "52"
        fields[22] = "0.0"
        fields[23] = "W"
        fields[24] = "118"
        fields[25] = "14"
        fields[26] = "37.26"
        lat = _parse_lat_lon(fields, lat_dir=19, lat_deg=20, lat_min=21, lat_sec=22)
        lon = _parse_lat_lon(fields, lat_dir=23, lat_deg=24, lat_min=25, lat_sec=26)
        assert lat is not None and lat < 0
        assert lon is not None and lon < 0

    def test_missing_field(self):
        fields = [""] * 27
        fields[19] = "N"
        fields[20] = ""
        fields[21] = "44"
        fields[22] = "54.36"
        assert _parse_lat_lon(fields, lat_dir=19, lat_deg=20, lat_min=21, lat_sec=22) is None
