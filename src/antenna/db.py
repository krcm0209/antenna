import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from antenna.config import settings


def get_connection(db_path: Path, *, readonly: bool = False) -> sqlite3.Connection:
    """Open a SQLite connection with SpatiaLite loaded."""
    uri = f"file:{db_path}{'?mode=ro' if readonly else ''}"
    # check_same_thread=False is safe because each HTTP request gets its own
    # connection (created in middleware, closed after response). No connection
    # is ever shared between concurrent requests/threads.
    conn = sqlite3.connect(uri, uri=True, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.enable_load_extension(True)
    conn.load_extension(settings.spatialite_path)
    conn.enable_load_extension(False)
    return conn


@contextmanager
def get_db(db_path: Path, *, readonly: bool = False) -> Generator[sqlite3.Connection]:
    """Context manager for a SpatiaLite-enabled connection."""
    conn = get_connection(db_path, readonly=readonly)
    try:
        yield conn
    finally:
        conn.close()
