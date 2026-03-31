"""Shared test fixtures — session-scoped SpatiaLite DB and FastAPI TestClient."""

import os
from pathlib import Path

import pytest

# Set DB path env var before any antenna imports so the Settings singleton picks it up.
_TEST_DB = Path(__file__).parent / "_test.db"
os.environ["FCC_API_DB_PATH"] = str(_TEST_DB)


@pytest.fixture(scope="session", autouse=True)
def test_db():
    """Build a minimal SpatiaLite database with known fixture data."""
    from antenna.models.contours import Contour
    from antenna.models.stations import Station
    from antenna.sync.db_builder import create_db, finalize_db, insert_contour_geometry

    session, raw_conn = create_db(_TEST_DB)

    # --- Fixture stations ---
    session.add(
        Station(
            facility_id=1001,
            callsign="WTEST",
            service="FM",
            frequency=99.1,
            station_class="C1",
            erp_kw=50.0,
            haat_m=300.0,
            antenna_lat=40.0,
            antenna_lon=-74.0,
            city="TESTVILLE",
            state="NJ",
            licensee="Test Broadcasting Inc",
        )
    )
    session.add(
        Station(
            facility_id=1002,
            callsign="WXYZ",
            service="FM",
            frequency=101.5,
            station_class="B",
            erp_kw=10.0,
            haat_m=150.0,
            antenna_lat=40.01,
            antenna_lon=-74.01,
            city="TESTVILLE",
            state="NJ",
            licensee="XYZ Media LLC",
        )
    )
    session.add(
        Station(
            facility_id=2001,
            callsign="KTEST",
            service="AM",
            frequency=0.71,
            station_class="B",
            erp_kw=5.0,
            antenna_lat=34.0,
            antenna_lon=-118.0,
            city="LOS ANGELES",
            state="CA",
            licensee="AM Test Corp",
        )
    )
    session.commit()

    # --- Contours for FM stations (simple rectangles) ---
    # Station 1001: box around (40.0, -74.0) ± 0.5 degrees
    session.add(Contour(id=1, facility_id=1001, service_type="FM"))
    # Station 1002: overlapping box around (40.01, -74.01)
    session.add(Contour(id=2, facility_id=1002, service_type="FM"))
    session.commit()

    insert_contour_geometry(
        raw_conn,
        contour_id=1,
        contour_points=[
            (-74.5, 39.5),
            (-73.5, 39.5),
            (-73.5, 40.5),
            (-74.5, 40.5),
        ],
    )
    insert_contour_geometry(
        raw_conn,
        contour_id=2,
        contour_points=[
            (-74.51, 39.51),
            (-73.51, 39.51),
            (-73.51, 40.51),
            (-74.51, 40.51),
        ],
    )
    raw_conn.commit()

    finalize_db(session, raw_conn)
    yield
    _TEST_DB.unlink(missing_ok=True)


@pytest.fixture(scope="session")
def client(test_db):
    """FastAPI TestClient backed by the fixture database."""
    from fastapi.testclient import TestClient

    from antenna.main import app

    with TestClient(app) as c:
        yield c
