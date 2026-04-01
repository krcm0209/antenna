"""Orchestrate the full data sync pipeline."""

import logging

from sqlmodel import select

from antenna.clients.base import FCCClient
from antenna.config import settings
from antenna.models.stations import Station
from antenna.sync.am_contour_preserve import extract_am_contours, reinsert_am_contours
from antenna.sync.am_contours import fetch_and_insert_am_contours
from antenna.sync.db_builder import create_db, finalize_db
from antenna.sync.fm_contours import download_fm_contour_zip, parse_and_insert_fm_contours
from antenna.sync.lms import download_station_data, parse_and_insert_stations

logger = logging.getLogger(__name__)


async def run_sync(*, skip_am_fetch: bool = False) -> None:
    """Run the full sync pipeline: download FCC data, build fresh DB.

    Args:
        skip_am_fetch: If True, skip fetching new AM contours from the
            Entity API (used during initial seed batching).
    """
    db_path = settings.db_path
    logger.info("Starting sync — building %s", db_path)

    # Step 0: Extract AM contours from previous DB (if exists)
    preserved_am = extract_am_contours(db_path)

    # Step 1: Create fresh database (deletes existing)
    session, raw_conn = create_db(db_path)

    # Step 2: Download and insert station metadata from FCC query APIs
    lms_app_to_facility: dict[str, int] = {}
    try:
        fm_text, am_text = download_station_data()
        station_count, lms_app_to_facility = parse_and_insert_stations(
            session, fm_text, am_text
        )
        logger.info("Inserted %d stations", station_count)
        del fm_text, am_text
    except Exception:
        logger.exception("Failed to download/parse station data")
        finalize_db(session, raw_conn)
        return

    # Step 3: Download and insert FM contours from bulk data
    try:
        fm_zip = download_fm_contour_zip()
        fm_count = parse_and_insert_fm_contours(
            session, raw_conn, fm_zip, lms_app_to_facility
        )
        logger.info("Inserted %d FM contours from bulk data", fm_count)
        del fm_zip
        del lms_app_to_facility
    except Exception:
        logger.exception("Failed to download/parse FM contour bulk data")

    # Step 3.5: Re-insert preserved AM contours
    if preserved_am:
        am_facility_ids = set(
            session.exec(select(Station.facility_id).where(Station.service == "AM")).all()
        )
        reinsert_am_contours(session, raw_conn, preserved_am, am_facility_ids)
        del preserved_am

    # Step 4: Fetch AM contours for NEW stations only
    if not skip_am_fetch:
        client = FCCClient()
        try:
            am_count = await fetch_and_insert_am_contours(session, raw_conn, client)
            logger.info("Inserted %d AM contours from Entity API", am_count)
        except Exception:
            logger.exception("Failed to fetch AM contours")
        finally:
            await client.close()

    # Step 5: Finalize
    finalize_db(session, raw_conn)
    logger.info("Sync complete — database saved to %s", db_path)
