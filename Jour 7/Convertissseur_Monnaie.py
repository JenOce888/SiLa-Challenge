#!/usr/bin/env python3
"""
DAY 7 - Currency Conversion API with Cache
Features:
  - Fetches exchange rates from exchangerate.host (external API)
  - Stores rates in SQLite with a 10-minute TTL
  - Exponential retry on API failure
  - 30-day conversion history + ASCII graph
  - Interactive CLI interface
"""

import requests
import sqlite3
import time
import sys
from datetime import datetime

#  Configuration

DB_PATH      = "currency_cache.db"
API_URL      = "https://api.exchangerate.host/live"
API_KEY      = ""          # Optional API key (leave empty if not required)
TTL_SECONDS  = 600         # 10 minutes
MAX_RETRIES  = 5
HISTORY_DAYS = 30

#  Database

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS rates (
            base       TEXT NOT NULL,
            currency   TEXT NOT NULL,
            rate       REAL NOT NULL,
            fetched_at INTEGER NOT NULL,
            PRIMARY KEY (base, currency)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            from_cur     TEXT NOT NULL,
            to_cur       TEXT NOT NULL,
            amount       REAL NOT NULL,
            result       REAL NOT NULL,
            rate         REAL NOT NULL,
            converted_at INTEGER NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def get_cached_rate(base: str, currency: str):
    """Return cached rate if still valid (within TTL), otherwise None."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT rate, fetched_at FROM rates WHERE base=? AND currency=?",
        (base.upper(), currency.upper())
    )
    row = c.fetchone()
    conn.close()
    if row:
        rate, fetched_at = row
        if time.time() - fetched_at < TTL_SECONDS:
            return rate
    return None


def save_rates(base: str, rates: dict):
    """Persist rates to the SQLite cache."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = int(time.time())
    for currency, rate in rates.items():
        c.execute(
            "INSERT OR REPLACE INTO rates (base, currency, rate, fetched_at) VALUES (?,?,?,?)",
            (base.upper(), currency.upper(), rate, now)
        )
    conn.commit()
    conn.close()


def save_history(from_cur, to_cur, amount, result, rate):
    """Record a conversion to the history table."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO history (from_cur,to_cur,amount,result,rate,converted_at) VALUES (?,?,?,?,?,?)",
        (from_cur.upper(), to_cur.upper(), amount, result, rate, int(time.time()))
    )
    conn.commit()
    conn.close()


def get_history(from_cur=None, to_cur=None, days=HISTORY_DAYS):
    """Retrieve conversion history for the past `days` days."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    since = int(time.time()) - days * 86400
    if from_cur and to_cur:
        c.execute(
            "SELECT * FROM history WHERE from_cur=? AND to_cur=? AND converted_at>=? ORDER BY converted_at",
            (from_cur.upper(), to_cur.upper(), since)
        )
    else:
        c.execute(
            "SELECT * FROM history WHERE converted_at>=? ORDER BY converted_at DESC LIMIT 50",
            (since,)
        )
    rows = c.fetchall()
    conn.close()
    return rows


#  API with exponential retry


def fetch_rates_from_api(base: str) -> dict:
    """
    Fetch live rates from the external API using exponential backoff retry.
    Returns a dict {CURRENCY: rate}.
    """
    params = {"base": base.upper()}
    if API_KEY:
        params["access_key"] = API_KEY

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f"  [API] Attempt {attempt}/{MAX_RETRIES} for {base.upper()}...", end=" ", flush=True)
            resp = requests.get(API_URL, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            if "rates" in data:
                print("OK")
                return data["rates"]
            elif "quotes" in data:
                # Strip the base prefix (e.g. "USDEUR" -> "EUR")
                prefix = base.upper()
                rates = {k[len(prefix):]: v for k, v in data["quotes"].items()}
                print("OK")
                return rates
            else:
                print(f"Unexpected format: {list(data.keys())}")

        except requests.exceptions.RequestException as e:
            wait = 2 ** attempt
            print(f"Error: {e}. Retrying in {wait}s...")
            time.sleep(wait)

    raise RuntimeError(f"Failed to fetch rates after {MAX_RETRIES} attempts.")


def get_rate(from_cur: str, to_cur: str) -> float:
    """Return the exchange rate, using cache when available."""
    from_cur = from_cur.upper()
    to_cur   = to_cur.upper()

    # Direct cache hit
    rate = get_cached_rate(from_cur, to_cur)
    if rate is not None:
        return rate

    # Inverse cache hit
    inv = get_cached_rate(to_cur, from_cur)
    if inv is not None and inv != 0:
        return 1.0 / inv

    # Fetch from API
    print("\n  [Cache miss / expired] Fetching rates from API...")
    rates = fetch_rates_from_api(from_cur)
    save_rates(from_cur, rates)

    if to_cur in rates:
        return rates[to_cur]

    # Cross-rate via USD
    if from_cur != "USD" and to_cur != "USD":
        usd_rates = fetch_rates_from_api("USD")
        save_rates("USD", usd_rates)
        if from_cur in usd_rates and to_cur in usd_rates:
            return usd_rates[to_cur] / usd_rates[from_cur]

    raise ValueError(f"Rate not found for {from_cur} -> {to_cur}")


#  ASCII Graph

def draw_ascii_graph(rows, from_cur, to_cur):
    """Render an ASCII bar chart of the exchange rate evolution."""
    if not rows:
        print("  No history available for this pair.")
        return

    rates = [r[5] for r in rows]
    dates = [datetime.fromtimestamp(r[6]).strftime("%d/%m") for r in rows]

    min_r  = min(rates)
    max_r  = max(rates)
    height = 10
    width  = min(len(rates), 60)
    step   = max(1, len(rates) // width)
    sampled_rates = rates[::step][:width]
    sampled_dates = dates[::step][:width]

    print(f"\n  Rate evolution {from_cur}/{to_cur} (last {HISTORY_DAYS} days)\n")
    r_range = max_r - min_r or 1

    for row_i in range(height, -1, -1):
        label = f"{min_r + (row_i / height) * r_range:8.4f} |"
        bars  = "".join(
            "#" if round((r - min_r) / r_range * height) >= row_i else " "
            for r in sampled_rates
        )
        print(f"  {label}{bars}")

    print("  " + " " * 10 + "+" + "-" * len(sampled_rates))
    step_label = max(1, len(sampled_dates) // 5)
    date_line  = "  " + " " * 11
    for i, d in enumerate(sampled_dates):
        date_line += d[:5] if i % step_label == 0 else " " * 5
    print(date_line + "\n")


#  CLI Interface

BANNER = """
+------------------------------------------------+
|   Currency Converter                           |
|   SQLite Cache (TTL 10min) | Retry Backoff     |
+------------------------------------------------+
"""

MENU = """
  [1] Convert a currency
  [2] View conversion history
  [3] Show rate evolution graph
  [4] Clear rate cache
  [5] Quit
"""


def convert_interactive():
    from_cur = input("  Source currency (e.g. USD): ").strip().upper()
    to_cur   = input("  Target currency (e.g. EUR): ").strip().upper()
    try:
        amount = float(input("  Amount: ").strip())
    except ValueError:
        print("  Invalid amount. Please enter a number.\n")
        return

    try:
        rate   = get_rate(from_cur, to_cur)
        result = amount * rate
        print(f"\n  {amount:.2f} {from_cur}  =  {result:.4f} {to_cur}")
        print(f"  (Rate: 1 {from_cur} = {rate:.6f} {to_cur})\n")
        save_history(from_cur, to_cur, amount, result, rate)
    except Exception as e:
        print(f"\n  Error: {e}\n")


def show_history():
    rows = get_history()
    if not rows:
        print("\n  No conversions recorded in the last 30 days.\n")
        return
    print(f"\n  {'#':<4} {'Date':<18} {'From':<6} {'To':<6} {'Amount':>12} {'Result':>14} {'Rate':>12}")
    print("  " + "-" * 78)
    for i, r in enumerate(rows, 1):
        _id, fc, tc, amt, res, rate, ts = r
        dt = datetime.fromtimestamp(ts).strftime("%d/%m/%Y %H:%M")
        print(f"  {i:<4} {dt:<18} {fc:<6} {tc:<6} {amt:>12.2f} {res:>14.4f} {rate:>12.6f}")
    print()


def show_graph():
    from_cur = input("  Source currency (e.g. XAF): ").strip().upper()
    to_cur   = input("  Target currency (e.g. YEN): ").strip().upper()
    rows = get_history(from_cur, to_cur)
    draw_ascii_graph(rows, from_cur, to_cur)


def clear_cache():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM rates")
    conn.commit()
    conn.close()
    print("\n  Rate cache cleared successfully.\n")


def main():
    init_db()
    print(BANNER)

    actions = {
        "1": convert_interactive,
        "2": show_history,
        "3": show_graph,
        "4": clear_cache,
    }

    while True:
        print(MENU)
        choice = input("  Your choice: ").strip()

        if choice in actions:
            actions[choice]()
        elif choice == "5":
            print("\n  Goodbye!\n")
            sys.exit(0)
        else:
            print("  Invalid choice. Please enter 1-5.\n")


if __name__ == "__main__":
    main()