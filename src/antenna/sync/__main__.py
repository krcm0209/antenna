"""Entry point: python -m antenna.sync"""

import asyncio
import logging

from antenna.sync.runner import run_sync

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)

asyncio.run(run_sync())
