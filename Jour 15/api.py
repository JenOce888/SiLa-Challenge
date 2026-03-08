"""
api.py — Minimal Flask REST API
Runs in a daemon thread on localhost:5050.

Endpoints:
    GET /health
    GET /leaderboard
    GET /player/<name>
"""

import threading
import db


def start() -> None:
    """Launch the Flask server in a background daemon thread."""
    t = threading.Thread(target=_run, daemon=True, name="flask-api")
    t.start()


def _run() -> None:
    try:
        from flask import Flask, jsonify

        app = Flask(__name__)
        app.logger.disabled = True
        import logging
        log = logging.getLogger("werkzeug")
        log.setLevel(logging.ERROR)

        @app.get("/health")
        def health():
            return jsonify({"status": "ok", "service": "hangman-elo"})

        @app.get("/leaderboard")
        def leaderboard():
            return jsonify(db.leaderboard())

        @app.get("/player/<name>")
        def player(name: str):
            try:
                return jsonify(db.fetch_player(name))
            except ValueError:
                return jsonify({"error": "Player not found"}), 404

        print("[api] Flask API running on http://localhost:5050")
        app.run(host="127.0.0.1", port=5050, debug=False, use_reloader=False)

    except ImportError:
        print("[api] Flask not installed — API disabled.")
    except OSError:
        print("[api] Port 5050 already in use — API skipped.")
    except Exception as e:
        print(f"[api] Error: {e}")
