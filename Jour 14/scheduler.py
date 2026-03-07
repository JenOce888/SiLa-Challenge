# scheduler.py — Periodic scheduling with APScheduler

import logging
from apscheduler.schedulers.blocking import BlockingScheduler
from config import SCHEDULE_INTERVAL_MINUTES, TIMEZONE

log = logging.getLogger(__name__)


def start_scheduler(job_func) -> None:
    """Start the scheduler and run job_func every N minutes."""
    scheduler = BlockingScheduler(timezone=TIMEZONE)
    scheduler.add_job(
        job_func,
        trigger="interval",
        minutes=SCHEDULE_INTERVAL_MINUTES,
        id="web_scraper",
        max_instances=1,
        misfire_grace_time=60,
    )
    log.info(f"Scheduler started — next run in {SCHEDULE_INTERVAL_MINUTES} min. (Ctrl+C to stop)")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        log.info("Scheduler stopped cleanly.")
