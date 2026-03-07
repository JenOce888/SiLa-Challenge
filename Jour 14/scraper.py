# scraper.py — Main scraping job

import logging
import pandas as pd

from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from config import TARGET_URL, MAX_PAGES
from driver import build_driver, save_cookies, load_cookies
from browser import interact_with_dynamic_form
from extractor import extract_books
from storage import save_to_db
from utils import random_delay

log = logging.getLogger(__name__)


def scrape_job() -> None:
    """Run a full scraping cycle: navigate, extract, store."""
    log.info("═══ Scraping job started ═══")
    driver    = build_driver()
    all_books: list[dict] = []

    try:
        driver.get(TARGET_URL)
        random_delay()

        load_cookies(driver)
        driver.refresh()
        random_delay()

        interact_with_dynamic_form(driver)

        for page_num in range(1, MAX_PAGES + 1):
            log.info(f"Scraping page {page_num}…")
            books = extract_books(driver.page_source)
            all_books.extend(books)

            try:
                next_btn = driver.find_element(By.CSS_SELECTOR, "li.next a")
                next_url = next_btn.get_attribute("href")
                if not next_url.startswith("http"):
                    base     = driver.current_url.rsplit("/", 1)[0]
                    next_url = f"{base}/{next_url}"
                random_delay()
                driver.get(next_url)
            except NoSuchElementException:
                log.info("Last page reached.")
                break

        save_cookies(driver)

    except Exception as exc:
        log.error(f"Scraping error: {exc}", exc_info=True)

    finally:
        driver.quit()

    save_to_db(all_books)

    if all_books:
        df = pd.DataFrame(all_books)
        log.info("\n" + df[["title", "price", "rating"]].head(10).to_string(index=False))

    log.info(f"═══ Job done — {len(all_books)} book(s) collected ═══\n")
