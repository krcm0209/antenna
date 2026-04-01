"""Entry point: python -m antenna.sync"""

import argparse
import asyncio
import logging

from antenna.sync.runner import run_sync

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)

parser = argparse.ArgumentParser(description="FCC data sync pipeline")
parser.add_argument(
    "--skip-am-fetch",
    action="store_true",
    help="Skip fetching new AM contours from the Entity API",
)
args = parser.parse_args()

asyncio.run(run_sync(skip_am_fetch=args.skip_am_fetch))
