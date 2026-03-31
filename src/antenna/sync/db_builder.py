"""Build a fresh SpatiaLite database from parsed FCC data."""

import sqlite3
from pathlib import Path

from shapely.geometry import Polygon
from sqlmodel import Session, SQLModel, create_engine

from antenna.db import get_connection
from antenna.models import Contour as Contour  # registers table on SQLModel.metadata
from antenna.models import Station as Station  # registers table on SQLModel.metadata


def create_db(db_path: Path) -> tuple[Session, sqlite3.Connection]:
    """Create a fresh SpatiaLite database.

    Returns a SQLModel Session and a raw sqlite3 connection that share the
    same underlying database connection, avoiding SQLite write-lock conflicts.
    """
    if db_path.exists():
        db_path.unlink()

    # Single raw connection with SpatiaLite loaded — shared by both
    # SQLModel/SQLAlchemy and raw geometry operations.
    raw_conn = get_connection(db_path)
    raw_conn.execute("SELECT InitSpatialMetaData(1)")
    raw_conn.commit()

    # Create SQLAlchemy engine that reuses the same raw_conn
    from sqlalchemy.pool import StaticPool

    engine = create_engine(
        "sqlite://",
        creator=lambda: raw_conn,
        poolclass=StaticPool,
    )

    SQLModel.metadata.create_all(engine)
    session = Session(engine)

    # Add geometry column and spatial index (raw SQL — not expressible in SQLModel)
    raw_conn.execute("SELECT AddGeometryColumn('contours', 'geom', 4326, 'POLYGON', 'XY')")
    raw_conn.execute("SELECT CreateSpatialIndex('contours', 'geom')")
    raw_conn.commit()

    return session, raw_conn


def insert_contour_geometry(
    conn: sqlite3.Connection,
    *,
    contour_id: int,
    contour_points: list[tuple[float, float]],
) -> None:
    """Set the geometry for a contour row.

    contour_points: list of (longitude, latitude) tuples forming the polygon ring.
    """
    if len(contour_points) < 3:
        return

    # Ensure the ring is closed
    if contour_points[0] != contour_points[-1]:
        contour_points = [*contour_points, contour_points[0]]

    polygon = Polygon(contour_points)
    if not polygon.is_valid:
        polygon = polygon.buffer(0)

    conn.execute(
        "UPDATE contours SET geom = GeomFromWKB(?, 4326) WHERE id = ?",
        (polygon.wkb, contour_id),
    )


def finalize_db(session: Session, conn: sqlite3.Connection) -> None:
    """Commit and analyze the database."""
    session.commit()
    session.close()
    conn.commit()
    conn.execute("ANALYZE")
    conn.close()
