"""Tests for GET /lookup/at-location — spatial station lookup."""


class TestLookupAtLocation:
    def test_returns_stations_inside_contour(self, client):
        resp = client.get("/lookup/at-location", params={"lat": 40.0, "lon": -74.0})
        assert resp.status_code == 200
        data = resp.json()
        assert data["latitude"] == 40.0
        assert data["longitude"] == -74.0
        ids = {s["facility_id"] for s in data["stations"]}
        assert 1001 in ids
        assert 1002 in ids

    def test_returns_empty_outside_contour(self, client):
        resp = client.get("/lookup/at-location", params={"lat": 0.0, "lon": 0.0})
        assert resp.status_code == 200
        assert resp.json()["stations"] == []

    def test_service_filter_fm(self, client):
        resp = client.get(
            "/lookup/at-location", params={"lat": 40.0, "lon": -74.0, "service": "FM"}
        )
        assert resp.status_code == 200
        for s in resp.json()["stations"]:
            assert s["service"] == "FM"

    def test_service_filter_am_at_fm_location(self, client):
        resp = client.get(
            "/lookup/at-location", params={"lat": 40.0, "lon": -74.0, "service": "AM"}
        )
        assert resp.status_code == 200
        assert resp.json()["stations"] == []

    def test_sort_by_frequency(self, client):
        resp = client.get(
            "/lookup/at-location",
            params={"lat": 40.0, "lon": -74.0, "sort_by": "frequency"},
        )
        stations = resp.json()["stations"]
        freqs = [s["frequency"] for s in stations]
        assert freqs == sorted(freqs)

    def test_sort_by_signal(self, client):
        resp = client.get(
            "/lookup/at-location",
            params={"lat": 40.0, "lon": -74.0, "sort_by": "signal"},
        )
        stations = resp.json()["stations"]
        signals = [s["estimated_signal_dbm"] for s in stations]
        non_none = [s for s in signals if s is not None]
        assert non_none == sorted(non_none, reverse=True)

    def test_invalid_lat_returns_422(self, client):
        resp = client.get("/lookup/at-location", params={"lat": 91, "lon": 0})
        assert resp.status_code == 422

    def test_missing_params_returns_422(self, client):
        resp = client.get("/lookup/at-location")
        assert resp.status_code == 422

    def test_response_fields(self, client):
        resp = client.get("/lookup/at-location", params={"lat": 40.0, "lon": -74.0})
        station = resp.json()["stations"][0]
        assert "facility_id" in station
        assert "callsign" in station
        assert "distance_km" in station
        assert "estimated_signal_dbm" in station
