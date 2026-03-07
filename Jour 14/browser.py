# browser.py — Dynamic form & AJAX interaction

import logging

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from utils import random_delay

log = logging.getLogger(__name__)


def interact_with_dynamic_form(driver: webdriver.Chrome) -> None:
    """
    Click a category filter and wait for the AJAX content to reload.
    Adapt the CSS selectors to your real target site.
    """
    wait = WebDriverWait(driver, 10)
    try:
        category_link = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "ul.nav-list li a"))
        )
        log.info(f"Clicking category: {category_link.text.strip()}")
        category_link.click()

        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "article.product_pod")))
        random_delay()
        log.info("AJAX content loaded successfully.")

    except TimeoutException:
        log.warning("AJAX interaction timed out — skipping.")
    except NoSuchElementException:
        log.warning("Element not found — skipping form interaction.")
