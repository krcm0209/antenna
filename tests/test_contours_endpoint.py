"""Tests for GET /contours/{facility_id} — contour geometry retrieval."""


class TestGetContour:
    def test_found(self, client):
        resp = client.get("/contours/1001")
        assert resp.status_code == 200
        data = resp.json()
        assert data["facility_id"] == 1001
        assert data["service_type"] == "FM"
        assert data["geometry"]["type"] == "Polygon"
        assert len(data["geometry"]["coordinates"]) >= 1

    def test_not_found(self, client):
        resp = client.get("/contours/9999")
        assert resp.status_code == 404
