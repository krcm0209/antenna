"""Fetch AM station contours from FCC Entity API (no bulk data available)."""

import json
import logging
import sqlite3

from sqlmodel import Session, select

from antenna.clients.base import FCCClient
from antenna.clients.contours import fetch_entity_contour
from antenna.models.contours import Contour
from antenna.models.stations import Station
from antenna.sync.db_builder import insert_contour_geometry

logger = logging.getLogger(__name__)


async def fetch_and_insert_am_contours(
    session: Session,
    raw_conn: sqlite3.Connection,
    client: FCCClient,
    *,
    offset: int = 0,
    limit: int | None = None,
) -> int:
    """Fetch contours for AM stations that don't have one yet.

    Args:
        offset: Skip this many missing stations (for batched seed jobs).
        limit: Only fetch this many stations (for batched seed jobs).

    Returns the number of contours inserted.
    """
    existing_contours = session.exec(select(Contour).where(Contour.service_type == "AM")).all()
    existing_ids = {c.facility_id for c in existing_contours}

    am_stations = session.exec(select(Station).where(Station.service == "AM")).all()
    missing = [s for s in am_stations if s.facility_id not in existing_ids]

    if not missing:
        logger.info("All AM stations already have contours")
        return 0

    # Apply offset/limit for batched seed jobs
    missing = missing[offset:]
    if limit is not None:
        missing = missing[:limit]

    logger.info("Fetching contours for %d AM stations", len(missing))
    count = 0

    for station in missing:
        try:
            response = await fetch_entity_contour(
                client, callsign=station.callsign, service_type="am"
            )
        except Exception:
            logger.warning(
                "Failed to fetch contour for AM station %s", station.callsign, exc_info=True
            )
            continue

        for feature in response.features:
            props = feature.properties
            contour_points = [(point.x, point.y) for point in props.contourData]

            contour_data_json = json.dumps(
                [
                    {
                        "azimuth": p.azimuth,
                        "distance": p.distance,
                        "haat": p.haat,
                        "erp": p.erp,
                        "latitude": p.y,
                        "longitude": p.x,
                    }
                    for p in props.contourData
                ]
            )

            # Insert metadata via SQLModel
            contour = Contour(
                facility_id=station.facility_id,
                application_id=props.application_id,
                service_type="AM",
                field_strength=props.field,
                erp_kw=props.erp,
                contour_data=contour_data_json,
            )
            session.add(contour)
            session.flush()  # Get the auto-generated id

            # Insert geometry via raw SpatiaLite SQL
            if contour.id is not None:
                insert_contour_geometry(
                    raw_conn,
                    contour_id=contour.id,
                    contour_points=contour_points,
                )

            count += 1

        if count % 10 == 0:
            session.commit()
            raw_conn.commit()
            logger.info("Inserted %d AM contours", count)

    session.commit()
    raw_conn.commit()
    logger.info("Finished: inserted %d AM contours total", count)
    return count
