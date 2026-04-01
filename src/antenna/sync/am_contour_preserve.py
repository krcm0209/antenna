"""Preserve AM contour data across database rebuilds."""

import logging
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from sqlmodel import Session

from antenna.db import get_connection
from antenna.models.contours import Contour

logger = logging.getLogger(__name__)


@dataclass
class PreservedContour:
    facility_id: int
    application_id: int | None
    service_type: str
    field_strength: float | None
    erp_kw: float | None
    contour_data: str | None
    geom_wkb: bytes | None


def extract_am_contours(old_db_path: Path) -> list[PreservedContour]:
    """Read all AM contours (metadata + geometry WKB) from an existing DB."""
    if not old_db_path.exists():
        logger.info("No previous DB at %s — nothing to preserve", old_db_path)
        return []

    conn = get_connection(old_db_path, readonly=True)
    try:
        rows = conn.execute(
            """SELECT facility_id, application_id, service_type,
                      field_strength, erp_kw, contour_data,
                      AsBinary(geom) AS geom_wkb
               FROM contours
               WHERE service_type = 'AM'"""
        ).fetchall()
        logger.info("Extracted %d AM contours from previous DB", len(rows))
        return [
            PreservedContour(
                facility_id=r["facility_id"],
                application_id=r["application_id"],
                service_type=r["service_type"],
                field_strength=r["field_strength"],
                erp_kw=r["erp_kw"],
                contour_data=r["contour_data"],
                geom_wkb=r["geom_wkb"],
            )
            for r in rows
        ]
    finally:
        conn.close()


def reinsert_am_contours(
    session: Session,
    raw_conn: sqlite3.Connection,
    preserved: list[PreservedContour],
    valid_facility_ids: set[int],
) -> int:
    """Re-insert preserved AM contours into the new DB.

    Only re-inserts contours whose facility_id still exists in the
    freshly-loaded station data (handles station deletions).
    """
    count = 0
    for p in preserved:
        if p.facility_id not in valid_facility_ids:
            continue

        contour = Contour(
            facility_id=p.facility_id,
            application_id=p.application_id,
            service_type=p.service_type,
            field_strength=p.field_strength,
            erp_kw=p.erp_kw,
            contour_data=p.contour_data,
        )
        session.add(contour)
        session.flush()

        if contour.id is not None and p.geom_wkb is not None:
            raw_conn.execute(
                "UPDATE contours SET geom = GeomFromWKB(?, 4326) WHERE id = ?",
                (p.geom_wkb, contour.id),
            )

        count += 1
        if count % 1000 == 0:
            session.commit()
            raw_conn.commit()
            logger.info("Re-inserted %d AM contours", count)

    session.commit()
    raw_conn.commit()
    logger.info("Re-inserted %d AM contours total (of %d preserved)", count, len(preserved))
    return count
