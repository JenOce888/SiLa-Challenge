# extractor.py — HTML data extraction with BeautifulSoup

import logging
from datetime import datetime
from bs4 import BeautifulSoup

log = logging.getLogger(__name__)


def extract_books(page_source: str) -> list[dict]:
    """Parse the page HTML and return a list of book records."""
    soup  = BeautifulSoup(page_source, "html.parser")
    books = []

    for article in soup.select("article.product_pod"):
        title  = article.select_one("h3 a")["title"]
        price  = article.select_one("p.price_color").text.strip()
        rating = article.select_one("p.star-rating")["class"][1]  # e.g. "Three"
        avail  = article.select_one("p.availability").text.strip()

        books.append({
            "title"     : title,
            "price"     : price,
            "rating"    : rating,
            "available" : avail,
            "scraped_at": datetime.now().isoformat(timespec="seconds"),
        })

    log.info(f"Extracted {len(books)} book(s) from current page.")
    return books
