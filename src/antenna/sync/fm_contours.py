"""Download and parse FM bulk contour data from FCC."""

import io
import logging
import sqlite3
import zipfile

import httpx
from sqlmodel import Session

from antenna.config import settings
from antenna.models.contours import Contour
from antenna.sync.db_builder import insert_contour_geometry
from antenna.sync.parsers import parse_pipe_int

logger = logging.getLogger(__name__)


def download_fm_contour_zip() -> bytes:
    """Download the FM contour bulk data ZIP from FCC."""
    logger.info("Downloading FM contour bulk data from %s", settings.fcc_fm_contour_bulk_url)
    response = httpx.get(settings.fcc_fm_contour_bulk_url, timeout=120.0)
    response.raise_for_status()
    logger.info("Downloaded %d bytes", len(response.content))
    return response.content


def parse_and_insert_fm_contours(
    session: Session,
    raw_conn: sqlite3.Connection,
    zip_data: bytes,
    lms_app_to_facility: dict[str, int],
) -> int:
    """Parse FM contour bulk data and insert into the database.

    The bulk file (FM_service_contour_current.txt) is pipe-delimited:
    - Field 0: application_id (integer, FCC application number)
    - Field 1: service (e.g., "FM")
    - Field 2: lms_application_id (UUID hex — matches LMS dump app IDs)
    - Field 3: dts_site_number
    - Field 4: transmitter site as "lat,lon"
    - Fields 5-364: 360 contour points as "lat,lon" per field (0-359 degrees azimuth)

    Returns the number of contours inserted.
    """
    with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
        names = zf.namelist()
        if not names:
            logger.warning("FM contour ZIP is empty")
            return 0

        data_file = names[0]
        logger.info("Parsing %s", data_file)
        content = zf.read(data_file).decode("utf-8", errors="replace")

    # First pass: collect all contours, keeping only the latest application
    # (highest application_id) per facility.
    best: dict[int, tuple[int, str, list[tuple[float, float]]]] = {}  # facility_id → (app_id, service, points)
    skipped = 0

    for i, line in enumerate(content.strip().split("\n")):
        if i == 0:
            continue

        fields = line.split("|")
        if len(fields) < 6:
            continue

        application_id_int = parse_pipe_int(fields[0])
        service = fields[1].strip()
        lms_app_id = fields[2].strip()

        facility_id = lms_app_to_facility.get(lms_app_id)
        if facility_id is None:
            skipped += 1
            continue

        # Skip if we already have a newer application for this facility
        if facility_id in best and application_id_int is not None and application_id_int <= best[facility_id][0]:
            continue

        contour_points: list[tuple[float, float]] = []
        for j in range(5, min(len(fields), 365)):
            pair = fields[j].strip()
            if not pair:
                continue
            parts = pair.split(",")
            if len(parts) != 2:
                continue
            try:
                lat = float(parts[0].strip())
                lon = float(parts[1].strip())
                if lat != 0.0 and lon != 0.0:
                    contour_points.append((lon, lat))
            except ValueError:
                continue

        if len(contour_points) < 3:
            continue

        best[facility_id] = (application_id_int or 0, service, contour_points)

    logger.info("Parsed %d unique facility contours (skipped %d unmatched)", len(best), skipped)

    # Second pass: insert the deduplicated contours
    count = 0
    for facility_id, (app_id, service, contour_points) in best.items():
        contour = Contour(
            facility_id=facility_id,
            application_id=app_id or None,
            service_type=service,
        )
        session.add(contour)
        session.flush()

        if contour.id is not None:
            insert_contour_geometry(
                raw_conn,
                contour_id=contour.id,
                contour_points=contour_points,
            )

        count += 1
        if count % 1000 == 0:
            session.commit()
            raw_conn.commit()
            logger.info("Inserted %d FM contours", count)

    session.commit()
    raw_conn.commit()
    logger.info("Finished: inserted %d FM contours total", count)
    return count
