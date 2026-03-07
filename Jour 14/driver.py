# driver.py — Browser initialisation & anti-bot bypass

import random
import pickle
import os
import logging

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from config import USER_AGENTS, COOKIE_PATH

log = logging.getLogger(__name__)


def build_driver() -> webdriver.Chrome:
    """Build a stealthy Chrome driver with a random user-agent."""
    ua = random.choice(USER_AGENTS)
    log.info(f"Selected User-Agent: {ua[:60]}…")

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument(f"user-agent={ua}")
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=options)

    # Remove the navigator.webdriver flag
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"},
    )
    return driver


def save_cookies(driver: webdriver.Chrome, path: str = COOKIE_PATH) -> None:
    """Persist session cookies to disk."""
    with open(path, "wb") as f:
        pickle.dump(driver.get_cookies(), f)
    log.info(f"Cookies saved → {path}")


def load_cookies(driver: webdriver.Chrome, path: str = COOKIE_PATH) -> None:
    """Load cookies from a previous session."""
    if not os.path.exists(path):
        log.info("No saved cookies found.")
        return
    with open(path, "rb") as f:
        cookies = pickle.load(f)
    for cookie in cookies:
        try:
            driver.add_cookie(cookie)
        except Exception:
            pass
    log.info(f"Cookies loaded from {path}")
