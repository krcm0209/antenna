"""Tests for /stations/* endpoints — search and listing."""


class TestSearchStations:
    def test_search_by_facility_id(self, client):
        resp = client.get("/stations/search/1001")
        assert resp.status_code == 200
        stations = resp.json()
        assert len(stations) == 1
        assert stations[0]["facility_id"] == 1001

    def test_search_by_callsign_prefix(self, client):
        resp = client.get("/stations/search/WTE")
        assert resp.status_code == 200
        callsigns = [s["callsign"] for s in resp.json()]
        assert "WTEST" in callsigns

    def test_search_by_licensee(self, client):
        resp = client.get("/stations/search/XYZ Media")
        assert resp.status_code == 200
        assert any(s["facility_id"] == 1002 for s in resp.json())

    def test_search_no_results(self, client):
        resp = client.get("/stations/search/ZZZZZ")
        assert resp.status_code == 200
        assert resp.json() == []


class TestListFmStations:
    def test_returns_fm_only(self, client):
        resp = client.get("/stations/fm")
        assert resp.status_code == 200
        for s in resp.json():
            assert s["service"] in ("FM", "FX", "FL", "FB")

    def test_state_filter(self, client):
        resp = client.get("/stations/fm", params={"state": "NJ"})
        assert resp.status_code == 200
        for s in resp.json():
            assert s["state"] == "NJ"

    def test_frequency_range(self, client):
        resp = client.get("/stations/fm", params={"freq_min": 99.0, "freq_max": 100.0})
        stations = resp.json()
        assert len(stations) == 1
        assert stations[0]["frequency"] == 99.1


class TestListAmStations:
    def test_returns_am_only(self, client):
        resp = client.get("/stations/am")
        assert resp.status_code == 200
        stations = resp.json()
        assert len(stations) >= 1
        for s in stations:
            assert s["service"] == "AM"
