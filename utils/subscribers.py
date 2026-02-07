"""
Subscriber persistence for multi-user Telegram mode.
Stores subscribers, their exam preferences, and profile info in a JSON file.
"""

import json
import os
import threading
from datetime import datetime

SUBSCRIBERS_FILE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "subscribers.json"
)


class SubscriberManager:
    """
    Thread-safe subscriber storage.

    Each subscriber record:
    {
        "chat_id": "123456",
        "user_id": 123456,
        "username": "john_doe",
        "first_name": "John",
        "last_name": "Doe",
        "joined_at": "2026-02-07 15:30:00",
        "active": true,
        "exams": ["CEnT-S", "TOLC-I"]   // empty list = all exams
    }
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._data = {}  # chat_id (str) -> record
        self._load()

    def _load(self):
        if os.path.exists(SUBSCRIBERS_FILE):
            try:
                with open(SUBSCRIBERS_FILE, "r", encoding="utf-8") as f:
                    records = json.load(f)
                for rec in records:
                    self._data[str(rec["chat_id"])] = rec
            except (json.JSONDecodeError, KeyError):
                self._data = {}

    def _save(self):
        with open(SUBSCRIBERS_FILE, "w", encoding="utf-8") as f:
            json.dump(list(self._data.values()), f, indent=2, ensure_ascii=False)

    def subscribe(self, chat_id, user_info=None):
        """
        Add or reactivate a subscriber.
        user_info is a dict with keys: user_id, username, first_name, last_name
        Returns True if this is a new subscriber.
        """
        chat_id = str(chat_id)
        with self._lock:
            is_new = chat_id not in self._data or not self._data[chat_id]["active"]

            existing = self._data.get(chat_id, {})
            info = user_info or {}

            self._data[chat_id] = {
                "chat_id": chat_id,
                "user_id": info.get("user_id", existing.get("user_id", "")),
                "username": info.get("username", existing.get("username", "")),
                "first_name": info.get("first_name", existing.get("first_name", "")),
                "last_name": info.get("last_name", existing.get("last_name", "")),
                "joined_at": existing.get("joined_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                "active": True,
                "exams": existing.get("exams", []),
            }
            self._save()
            return is_new

    def unsubscribe(self, chat_id):
        chat_id = str(chat_id)
        with self._lock:
            if chat_id in self._data:
                self._data[chat_id]["active"] = False
                self._save()

    def set_exams(self, chat_id, exams):
        """Set exam preferences. Empty list means all exams."""
        chat_id = str(chat_id)
        with self._lock:
            if chat_id in self._data:
                self._data[chat_id]["exams"] = exams
                self._save()

    def get_subscriber(self, chat_id):
        chat_id = str(chat_id)
        return self._data.get(chat_id)

    def get_active_subscribers(self):
        """Return list of active subscriber records."""
        with self._lock:
            return [r for r in self._data.values() if r["active"]]

    def get_all_subscribers(self):
        """Return all subscriber records."""
        with self._lock:
            return list(self._data.values())

    def wants_exam(self, chat_id, exam_type):
        """Check if subscriber wants notifications for a given exam."""
        chat_id = str(chat_id)
        rec = self._data.get(chat_id)
        if not rec or not rec["active"]:
            return False
        if not rec["exams"]:
            return True
        return exam_type in rec["exams"]
