"""
Donator persistence module.
Tracks users who claim to have donated via USDT TRC20 and stores their transaction details.
"""

import json
import os
import threading
from datetime import datetime

DONATORS_FILE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "donators.json"
)

USDT_TRC20_ADDRESS = "TJaPMJJekVuBbQKbtp8w69m7GrojSaiRRm"


class DonatorManager:
    """
    Thread-safe donator storage.

    Each donator record:
    {
        "chat_id": "123456",
        "user_id": 123456,
        "username": "john_doe",
        "first_name": "John",
        "last_name": "Doe",
        "transaction_id": "abc123...",
        "donated_at": "2026-02-09 15:30:00",
        "verified": false
    }
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._data = {}  # chat_id (str) -> record
        self._load()

    def _load(self):
        if os.path.exists(DONATORS_FILE):
            try:
                with open(DONATORS_FILE, "r", encoding="utf-8") as f:
                    records = json.load(f)
                for rec in records:
                    self._data[str(rec["chat_id"])] = rec
            except (json.JSONDecodeError, KeyError):
                self._data = {}

    def _save(self):
        with open(DONATORS_FILE, "w", encoding="utf-8") as f:
            json.dump(list(self._data.values()), f, indent=2, ensure_ascii=False)

    def add_donation(self, chat_id, transaction_id, user_info=None):
        """Record a donation claim with transaction ID."""
        chat_id = str(chat_id)
        info = user_info or {}
        with self._lock:
            self._data[chat_id] = {
                "chat_id": chat_id,
                "user_id": info.get("user_id", ""),
                "username": info.get("username", ""),
                "first_name": info.get("first_name", ""),
                "last_name": info.get("last_name", ""),
                "transaction_id": transaction_id,
                "donated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "verified": False,
            }
            self._save()

    def is_donator(self, chat_id):
        """Check if a user has submitted a donation."""
        chat_id = str(chat_id)
        with self._lock:
            return chat_id in self._data

    def get_donator(self, chat_id):
        """Get donator record."""
        chat_id = str(chat_id)
        with self._lock:
            return self._data.get(chat_id)

    def get_all_donators(self):
        """Return all donator records."""
        with self._lock:
            return list(self._data.values())

    def set_verified(self, chat_id, verified=True):
        """Mark a donation as verified (by admin)."""
        chat_id = str(chat_id)
        with self._lock:
            if chat_id in self._data:
                self._data[chat_id]["verified"] = verified
                self._save()
                return True
            return False

    def remove_donator(self, chat_id):
        """Remove a donator record entirely (rejected by admin)."""
        chat_id = str(chat_id)
        with self._lock:
            if chat_id in self._data:
                del self._data[chat_id]
                self._save()
                return True
            return False

    def get_unverified_donators(self):
        """Return list of donators whose transactions have not been verified yet."""
        with self._lock:
            return [r for r in self._data.values() if not r.get("verified")]

    def get_verified_donators(self):
        """Return list of donators whose transactions have been verified."""
        with self._lock:
            return [r for r in self._data.values() if r.get("verified")]

    def is_verified_donator(self, chat_id):
        """Check if a user is a verified (premium) donator."""
        chat_id = str(chat_id)
        with self._lock:
            rec = self._data.get(chat_id)
            return rec is not None and rec.get("verified", False)
