"""
Bot statistics and state tracker.
Records crawl events, errors, and bot running state.
Persists to bot_stats.json.
"""

import json
import os
import threading
import time
from datetime import datetime

STATS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "bot_stats.json")


class BotStats:
    """Thread-safe bot statistics storage."""

    def __init__(self):
        self._lock = threading.Lock()
        self._data = {
            "bot_running": False,
            "bot_pid": None,
            "total_crawls": 0,
            "total_errors": 0,
            "total_seats_found": 0,
            "last_crawl_at": None,
            "last_error_at": None,
            "last_error_msg": "",
            "started_at": None,
            "crawl_history": [],    # [{time, seats_found, exams_checked}] last 200
            "error_history": [],    # [{time, message}] last 100
            "daily_crawls": {},     # {"2026-02-09": 15, ...}
            "daily_errors": {},     # {"2026-02-09": 2, ...}
        }
        self._load()

    def _load(self):
        if os.path.exists(STATS_FILE):
            try:
                with open(STATS_FILE, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                self._data.update(saved)
            except Exception:
                pass

    def _save(self):
        with open(STATS_FILE, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)

    def set_running(self, running, pid=None):
        with self._lock:
            self._data["bot_running"] = running
            self._data["bot_pid"] = pid
            if running:
                self._data["started_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self._save()

    def is_running(self):
        with self._lock:
            return self._data.get("bot_running", False)

    def record_crawl(self, seats_found=0, exams_checked=0):
        now = datetime.now()
        day = now.strftime("%Y-%m-%d")
        ts = now.strftime("%Y-%m-%d %H:%M:%S")
        with self._lock:
            self._data["total_crawls"] += 1
            self._data["total_seats_found"] += seats_found
            self._data["last_crawl_at"] = ts
            self._data["crawl_history"].append({
                "time": ts, "seats_found": seats_found, "exams_checked": exams_checked,
            })
            # Keep last 200
            self._data["crawl_history"] = self._data["crawl_history"][-200:]
            # Daily
            self._data["daily_crawls"][day] = self._data["daily_crawls"].get(day, 0) + 1
            self._save()

    def record_error(self, message):
        now = datetime.now()
        day = now.strftime("%Y-%m-%d")
        ts = now.strftime("%Y-%m-%d %H:%M:%S")
        with self._lock:
            self._data["total_errors"] += 1
            self._data["last_error_at"] = ts
            self._data["last_error_msg"] = str(message)[:500]
            self._data["error_history"].append({"time": ts, "message": str(message)[:200]})
            self._data["error_history"] = self._data["error_history"][-100:]
            self._data["daily_errors"][day] = self._data["daily_errors"].get(day, 0) + 1
            self._save()

    def get_stats(self):
        with self._lock:
            return dict(self._data)

    def get_daily_data(self, days=14):
        """Return last N days of crawl/error counts for charts."""
        with self._lock:
            from datetime import timedelta
            today = datetime.now().date()
            result = []
            for i in range(days - 1, -1, -1):
                d = (today - timedelta(days=i)).strftime("%Y-%m-%d")
                result.append({
                    "date": d,
                    "crawls": self._data["daily_crawls"].get(d, 0),
                    "errors": self._data["daily_errors"].get(d, 0),
                })
            return result
