# storage.py — Data persistence with SQLite and pandas

import sqlite3
import logging
import pandas as pd

from config import DB_PATH

log = logging.getLogger(__name__)


def init_db(db_path: str = DB_PATH) -> None:
    """Create the books table if it does not already exist."""
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS books (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                title      TEXT,
                price      TEXT,
                rating     TEXT,
                available  TEXT,
                scraped_at TEXT
            )
        """)
    log.info("Database initialised.")


def save_to_db(records: list[dict], db_path: str = DB_PATH) -> None:
    """Insert a list of book records into the SQLite database."""
    if not records:
        log.warning("No records to save.")
        return
    df = pd.DataFrame(records)
    with sqlite3.connect(db_path) as conn:
        df.to_sql("books", conn, if_exists="append", index=False)
    log.info(f"{len(records)} record(s) saved to '{db_path}'.")
