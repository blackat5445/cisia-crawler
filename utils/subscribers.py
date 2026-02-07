"""
Subscriber persistence for multi-user Telegram mode.
Stores subscribers, their exam preferences, and profile info in a JSON file.

Exam preference logic:
  - exams = []         -> user has NOT chosen yet, receives NOTHING
  - exams = ["ALL"]    -> user wants ALL exams
  - exams = ["CEnT-S"] -> user wants only those specific exams
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
        "exams": []
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
        New subscribers start with exams=[] which means they must
        use /exams to choose what they want. They receive NOTHING
        until they select exams.
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
                # Keep existing exam choices if re-subscribing, otherwise empty
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
        """
        Set exam preferences.
        exams=["ALL"] means all exams.
        exams=["CEnT-S", "TOLC-I"] means only those.
        exams=[] means nothing selected (no notifications).
        """
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
        """
        Check if subscriber wants notifications for a given exam.

        Returns True only if:
          - subscriber is active AND
          - exams contains "ALL" OR exams contains the specific exam_type

        Returns False if:
          - subscriber inactive, not found, or exams is empty
        """
        chat_id = str(chat_id)
        with self._lock:
            rec = self._data.get(chat_id)
            if not rec or not rec["active"]:
                return False
            exams = rec.get("exams", [])
            if not exams:
                return False
            if "ALL" in exams:
                return True
            return exam_type in exams
