"""Tests for haversine distance and signal strength estimation."""

import pytest

from antenna.routers.lookup import _estimate_signal_dbm, _haversine_km


class TestHaversineKm:
    def test_nyc_to_london(self):
        # Well-known reference distance ~5570 km
        d = _haversine_km(40.7128, -74.0060, 51.5074, -0.1278)
        assert d == pytest.approx(5570, abs=10)

    def test_same_point(self):
        assert _haversine_km(40.0, -74.0, 40.0, -74.0) == 0.0

    def test_antipodal(self):
        # Half Earth circumference ~20015 km
        d = _haversine_km(0, 0, 0, 180)
        assert d == pytest.approx(20015, abs=10)

    def test_short_distance(self):
        # ~1 degree of latitude ≈ 111 km
        d = _haversine_km(40.0, -74.0, 41.0, -74.0)
        assert d == pytest.approx(111.2, abs=1)


class TestEstimateSignalDbm:
    def test_known_values(self):
        # 50 kW at 99.1 MHz, 10 km away
        # ERP_dBm = 10*log10(50) + 60 = 16.99 + 60 = 76.99
        # FSPL = 20*log10(10) + 20*log10(99.1) + 32.45 = 20 + 39.92 + 32.45 = 92.37
        # Signal = 76.99 - 92.37 = -15.38 → rounded to -15.4
        result = _estimate_signal_dbm(50.0, 99.1, 10.0)
        assert result == pytest.approx(-15.4, abs=0.1)

    def test_none_erp(self):
        assert _estimate_signal_dbm(None, 99.1, 10.0) is None

    def test_zero_erp(self):
        assert _estimate_signal_dbm(0.0, 99.1, 10.0) is None

    def test_negative_erp(self):
        assert _estimate_signal_dbm(-1.0, 99.1, 10.0) is None

    def test_zero_distance(self):
        assert _estimate_signal_dbm(50.0, 99.1, 0.0) is None

    def test_zero_frequency(self):
        assert _estimate_signal_dbm(50.0, 0.0, 10.0) is None
