"""Merge AM contour batches into the base fcc.db.

Each batch DB (fcc-batch-N.db) contains the base stations + FM contours
plus a slice of AM contours. This script extracts AM contours from each
batch and inserts them into the base fcc.db.

Usage: python -m antenna.sync.am_merge --batches 7
"""

import argparse
import logging
from pathlib import Path

from antenna.config import settings
from antenna.sync.am_contour_preserve import extract_am_contours, reinsert_am_contours
from antenna.sync.db_builder import finalize_db, open_existing_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)

logger = logging.getLogger(__name__)


def main(batches: int) -> None:
    db_path = settings.db_path
    session, raw_conn = open_existing_db(db_path)

    # Collect all valid AM facility IDs from the base DB
    from sqlmodel import select

    from antenna.models.stations import Station

    valid_ids = set(
        session.exec(select(Station.facility_id).where(Station.service == "AM")).all()
    )

    total = 0
    seen_facilities: set[int] = set()

    for i in range(batches):
        batch_path = Path(f"fcc-batch-{i}.db")
        if not batch_path.exists():
            logger.warning("Batch file %s not found, skipping", batch_path)
            continue

        preserved = extract_am_contours(batch_path)
        # Deduplicate — only insert contours not already in the base DB
        new = [p for p in preserved if p.facility_id not in seen_facilities]
        seen_facilities.update(p.facility_id for p in new)

        count = reinsert_am_contours(session, raw_conn, new, valid_ids)
        total += count
        logger.info("Merged %d AM contours from batch %d", count, i)

    finalize_db(session, raw_conn)
    logger.info("Merge complete — %d AM contours total", total)


parser = argparse.ArgumentParser(description="Merge AM contour batch DBs")
parser.add_argument("--batches", type=int, default=7, help="Number of batch files to merge")
args = parser.parse_args()

main(args.batches)
