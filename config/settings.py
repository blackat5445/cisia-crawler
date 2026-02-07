"""
Configuration loader for CISIA CRAWLER.
Reads settings from config.yaml and provides defaults.
Supports saving settings back to config.yaml from the interactive menu.
"""

import os
import sys
import yaml

CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.yaml")

EXAM_TYPES = {
    "TOLC-I": {"param": "ingegneria", "prefix": "TOLC"},
    "TOLC-E": {"param": "economia", "prefix": "TOLC"},
    "TOLC-S": {"param": "scienze", "prefix": "TOLC"},
    "TOLC-F": {"param": "farmacia", "prefix": "TOLC"},
    "TOLC-SU": {"param": "umanistica", "prefix": "TOLC"},
    "TOLC-B": {"param": "biologia", "prefix": "TOLC"},
    "TOLC-AV": {"param": "agraria", "prefix": "TOLC"},
    "TOLC-PSI": {"param": "psicologia", "prefix": "TOLC"},
    "TOLC-SPS": {"param": "scienze_politiche", "prefix": "TOLC"},
    "TOLC-LP": {"param": "lauree_professionalizzanti", "prefix": "TOLC"},
    "CEnT-S": {"param": "cents", "prefix": "CENT"},
}

FORMAT_TYPES = ["@HOME", "@UNI"]

DEFAULT_CONFIG = {
    "exam_type": "CEnT-S",
    "format_type": "@HOME",
    "check_mode": "fixed",
    "check_interval_minutes": 5,
    "random_interval_from": 60,
    "random_interval_to": 900,
    "language": "en",
    "page_language": "inglese",
    "telegram": {
        "enabled": False,
        "bot_token": "",
        "chat_id": "",
        "message_count": 5,
        "multi_user": False,
    },
    "email": {
        "enabled": False,
        "smtp_host": "smtp.gmail.com",
        "smtp_port": 587,
        "smtp_user": "",
        "smtp_password": "",
        "from_email": "",
        "to_email": "",
        "use_tls": True,
    },
}


def load_settings():
    """Load settings from config.yaml, falling back to defaults."""
    if not os.path.exists(CONFIG_FILE):
        save_settings(DEFAULT_CONFIG)
        return {**DEFAULT_CONFIG, "telegram": {**DEFAULT_CONFIG["telegram"]}, "email": {**DEFAULT_CONFIG["email"]}}

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        user_config = yaml.safe_load(f) or {}

    settings = {}
    for key, default in DEFAULT_CONFIG.items():
        if isinstance(default, dict):
            settings[key] = {**default, **user_config.get(key, {})}
        else:
            settings[key] = user_config.get(key, default)

    return settings


def save_settings(settings):
    """Write settings dict back to config.yaml preserving comments structure."""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        yaml.dump(settings, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


def validate_settings(settings):
    """Validate settings. Returns (ok, error_message)."""
    exam = settings["exam_type"]
    if exam != "ALL" and exam not in EXAM_TYPES:
        return False, "Invalid exam_type: {}. Available: ALL, {}".format(exam, ", ".join(EXAM_TYPES.keys()))

    if settings["format_type"] not in FORMAT_TYPES:
        return False, "Invalid format_type: {}".format(settings["format_type"])

    if settings["language"] not in ["en", "it"]:
        return False, "Invalid language. Use 'en' or 'it'."

    if settings["check_mode"] not in ["fixed", "random"]:
        return False, "Invalid check_mode. Use 'fixed' or 'random'."

    if settings["check_mode"] == "random":
        lo = settings["random_interval_from"]
        hi = settings["random_interval_to"]
        if lo >= hi:
            return False, "random_interval_from ({}) must be < random_interval_to ({}).".format(lo, hi)
        if hi - lo < 30:
            return False, "Random interval range must be at least 30 seconds wide."

    mc = settings["telegram"].get("message_count", 5)
    if not isinstance(mc, int) or mc < 1 or mc > 50:
        return False, "telegram.message_count must be 1-50."

    return True, ""


def get_all_exam_keys():
    """Return a sorted list of all exam type keys."""
    return sorted(EXAM_TYPES.keys())


def print_banner():
    """Print the application banner."""
    print("")
    print("  ================================================================")
    print("   CISIA CRAWLER v1.1.0")
    print("   Author: Kasra Falahati")
    print("   https://github.com/blackat5445/cisia-crawler")
    print("  ================================================================")
    print("")
