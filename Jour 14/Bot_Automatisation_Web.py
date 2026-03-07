# main.py — Bot entry point

import logging

from storage import init_db
from scraper import scrape_job
from scheduler import start_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

if __name__ == "__main__":
    init_db()
    scrape_job()           # run immediately on startup
    start_scheduler(scrape_job)
