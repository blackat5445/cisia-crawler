"""
Subscriber persistence for multi-user Telegram mode.
Stores subscribers, their exam preferences, profile info,
GitHub verification status, and preferred check interval.
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
        "exams": [],
        "github_verified": false,
        "github_username": "",
        "preferred_interval_minutes": 5
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
        New subscribers start with github_verified=False.
        They must verify via /github before using the bot.
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
                "github_verified": existing.get("github_verified", False),
                "github_username": existing.get("github_username", ""),
                "preferred_interval_minutes": existing.get("preferred_interval_minutes", 5),
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
        chat_id = str(chat_id)
        with self._lock:
            if chat_id in self._data:
                self._data[chat_id]["exams"] = exams
                self._save()

    def set_github_verified(self, chat_id, github_username):
        """Mark a subscriber as GitHub-verified.
        Returns False if the GitHub username is already used by another subscriber.
        """
        chat_id = str(chat_id)
        with self._lock:
            # Check if this GitHub username is already claimed by another user
            gh_lower = github_username.lower().strip()
            for cid, rec in self._data.items():
                if cid != chat_id and rec.get("github_verified") and rec.get("github_username", "").lower().strip() == gh_lower:
                    return False  # Already taken

            if chat_id in self._data:
                self._data[chat_id]["github_verified"] = True
                self._data[chat_id]["github_username"] = github_username
                self._save()
                return True
            return False

    def is_github_username_taken(self, github_username, exclude_chat_id=None):
        """Check if a GitHub username is already verified by another user."""
        gh_lower = github_username.lower().strip()
        with self._lock:
            for cid, rec in self._data.items():
                if exclude_chat_id and str(cid) == str(exclude_chat_id):
                    continue
                if rec.get("github_verified") and rec.get("github_username", "").lower().strip() == gh_lower:
                    return True
            return False

    def set_interval(self, chat_id, minutes):
        """Store a user's preferred check interval."""
        chat_id = str(chat_id)
        with self._lock:
            if chat_id in self._data:
                self._data[chat_id]["preferred_interval_minutes"] = minutes
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
