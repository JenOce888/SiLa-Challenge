"""
db.py — Database & ELO logic
SQLite persistence for players and game history.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "hangman.db"

# ELO multipliers per difficulty and hint usage
_ELO_WIN  = {"easy": 21, "medium": 30, "hard": 45}
_ELO_LOSS = {"easy": -14, "medium": -20, "hard": -30}
HINT_PENALTY = -50


def init() -> None:
    """Create tables if they don't exist."""
    with _connect() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS players (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                name         TEXT    UNIQUE NOT NULL,
                elo          INTEGER DEFAULT 1000,
                games_played INTEGER DEFAULT 0,
                games_won    INTEGER DEFAULT 0,
                created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS game_history (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                player      TEXT    NOT NULL,
                word        TEXT    NOT NULL,
                category    TEXT    NOT NULL,
                difficulty  TEXT    NOT NULL,
                won         INTEGER NOT NULL,
                elo_change  INTEGER NOT NULL,
                duration_s  INTEGER DEFAULT 0,
                played_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)


def get_or_create(name: str) -> dict:
    """Return player dict, creating a new row if needed."""
    with _connect() as conn:
        conn.execute("INSERT OR IGNORE INTO players (name) VALUES (?)", (name,))
    return fetch_player(name)


def fetch_player(name: str) -> dict:
    with _connect() as conn:
        row = conn.execute(
            "SELECT name, elo, games_played, games_won FROM players WHERE name=?",
            (name,)
        ).fetchone()
    if row is None:
        raise ValueError(f"Player '{name}' not found.")
    return {"name": row[0], "elo": row[1], "games_played": row[2], "games_won": row[3]}


def record_game(
    player: str,
    word: str,
    category: str,
    difficulty: str,
    won: bool,
    hint_used: bool,
    duration_s: int,
) -> int:
    """
    Update ELO, persist history, return the ELO delta applied.

    Timer bonus/penalty: every 10 s over 30 s costs -2 ELO on a win.
    """
    base = _ELO_WIN[difficulty] if won else _ELO_LOSS[difficulty]

    # Timer penalty on wins (no penalty on losses)
    timer_penalty = 0
    if won and duration_s > 30:
        overtime = duration_s - 30
        timer_penalty = -2 * (overtime // 10)

    delta = base + timer_penalty
    if hint_used:
        delta += HINT_PENALTY

    with _connect() as conn:
        conn.execute(
            "UPDATE players SET elo=MAX(0, elo+?), games_played=games_played+1, "
            "games_won=games_won+? WHERE name=?",
            (delta, 1 if won else 0, player),
        )
        conn.execute(
            "INSERT INTO game_history (player,word,category,difficulty,won,elo_change,duration_s) "
            "VALUES (?,?,?,?,?,?,?)",
            (player, word, category, difficulty, int(won), delta, duration_s),
        )
    return delta


def leaderboard(limit: int = 10) -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT name, elo, games_played, games_won FROM players "
            "ORDER BY elo DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [
        {"rank": i + 1, "name": r[0], "elo": r[1],
         "games_played": r[2], "games_won": r[3]}
        for i, r in enumerate(rows)
    ]


#  Internal helper functions

def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
