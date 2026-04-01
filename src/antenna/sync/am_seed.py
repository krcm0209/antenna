"""Seed a batch of AM contours into an existing fcc.db.

Usage: python -m antenna.sync.am_seed --offset 0 --limit 1800
"""

import argparse
import asyncio
import logging

from antenna.clients.base import FCCClient
from antenna.config import settings
from antenna.sync.am_contours import fetch_and_insert_am_contours
from antenna.sync.db_builder import finalize_db, open_existing_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)

logger = logging.getLogger(__name__)


async def main(offset: int, limit: int) -> None:
    db_path = settings.db_path
    logger.info("Opening existing DB at %s for AM contour seed (offset=%d, limit=%d)", db_path, offset, limit)

    session, raw_conn = open_existing_db(db_path)
    client = FCCClient()
    try:
        count = await fetch_and_insert_am_contours(
            session, raw_conn, client, offset=offset, limit=limit
        )
        logger.info("Seeded %d AM contours", count)
    finally:
        await client.close()
        finalize_db(session, raw_conn)


parser = argparse.ArgumentParser(description="Seed a batch of AM contours")
parser.add_argument("--offset", type=int, required=True, help="Start index in missing stations list")
parser.add_argument("--limit", type=int, required=True, help="Number of stations to process")
args = parser.parse_args()

asyncio.run(main(args.offset, args.limit))
