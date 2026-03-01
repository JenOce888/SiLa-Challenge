"""
Main.py
───────
Entry point. Runs one fetch immediately, renders the live dashboard,
then auto-refreshes every REFRESH_INTERVAL seconds.

Press Ctrl+C to exit cleanly.
"""

import asyncio
import logging
import time

import aiohttp
from rich.live import Live
from rich.console import Console

from config import config
from fetchers import fetch_all, get_circuit_breakers
from dashboard import build_layout, console

# Logging setup
logging.basicConfig(
    filename="async_client.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# Main loop 
async def run():
    console.rule("[bold cyan] Client API REST Asynchrone [/bold cyan]")

    # Warn if API keys are missing
    if not config.owm_api_key:
        console.print("[yellow]⚠  OWM_API_KEY not set — weather will be unavailable[/yellow]")
    if not config.news_api_key:
        console.print("[yellow]⚠  NEWS_API_KEY not set — news will be unavailable[/yellow]")

    breakers = get_circuit_breakers()

    # Initial empty result while first fetch runs
    results: dict = {
        "github":  {"user": None, "repos": []},
        "weather": None,
        "news":    None,
    }

    async with aiohttp.ClientSession() as session:
        with Live(
            build_layout(results, breakers, config.news_query),
            console=console,
            refresh_per_second=1,
            screen=True,
        ) as live:

            while True:
                t0 = time.perf_counter()
                logger.info("Starting parallel fetch of all APIs")

                try:
                    results = await fetch_all(session)
                except Exception as e:
                    logger.error(f"Unexpected error during fetch: {e}")

                elapsed = time.perf_counter() - t0
                logger.info(f"Fetch completed in {elapsed:.2f}s")

                # Update the live dashboard
                live.update(build_layout(results, breakers, config.news_query))

                # Wait until next refresh cycle
                await asyncio.sleep(config.refresh_interval)


def main():
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        console.print("\n[dim]Dashboard stopped. See you next time! [/dim]")


if __name__ == "__main__":
    main()
