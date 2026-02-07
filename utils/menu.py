"""
Interactive CLI menu for CISIA CRAWLER.
Allows users to configure all settings, test connections, and start the bot.
"""

import sys
import os
import webbrowser

from config.settings import (
    load_settings, save_settings, validate_settings,
    get_all_exam_keys, EXAM_TYPES, FORMAT_TYPES, print_banner,
)
from utils.i18n import I18n
from utils.logger import Logger


GITHUB_URL = "https://github.com/blackat5445/cisia-crawler"


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def pause():
    input("\n  Press Enter to continue...")


def read_input(prompt, default=None):
    """Read input with optional default value."""
    if default is not None:
        raw = input("  {} [{}]: ".format(prompt, default)).strip()
        return raw if raw else str(default)
    return input("  {}: ".format(prompt)).strip()


def read_int(prompt, default=None, lo=None, hi=None):
    """Read an integer with validation."""
    while True:
        val = read_input(prompt, default)
        try:
            n = int(val)
            if lo is not None and n < lo:
                print("    Value must be >= {}".format(lo))
                continue
            if hi is not None and n > hi:
                print("    Value must be <= {}".format(hi))
                continue
            return n
        except ValueError:
            print("    Please enter a valid number.")


def read_bool(prompt, default=False):
    """Read a yes/no boolean."""
    default_str = "Y/n" if default else "y/N"
    raw = input("  {} [{}]: ".format(prompt, default_str)).strip().lower()
    if not raw:
        return default
    return raw in ("y", "yes", "1", "true")


def show_main_menu(settings):
    """Display the main menu and return the user's choice."""
    clear_screen()
    print_banner()

    lang = I18n(settings["language"])

    # Show current config summary
    exam = settings["exam_type"]
    fmt = settings["format_type"]
    mode = settings["check_mode"]
    tg = "ON" if settings["telegram"]["enabled"] else "OFF"
    em = "ON" if settings["email"]["enabled"] else "OFF"
    lng = settings["language"].upper()

    print("  Current config: exam={} | format={} | mode={} | lang={}".format(exam, fmt, mode, lng))
    print("  Telegram: {} | Email: {}".format(tg, em))
    print("")
    print("  ----------------------------------------------------------------")
    print("  1. Start the bot")
    print("  2. Settings")
    print("  3. Test Telegram connection")
    print("  4. Test Email connection")
    print("  5. About")
    print("  6. Donate")
    print("  7. Exit")
    print("  ----------------------------------------------------------------")
    print("")

    choice = input("  Select option [1-7]: ").strip()
    return choice


def settings_menu(settings):
    """Interactive settings editor. Returns updated settings dict."""
    while True:
        clear_screen()
        print_banner()
        print("  === SETTINGS ===")
        print("")
        print("  1.  Exam type          : {}".format(settings["exam_type"]))
        print("  2.  Format type        : {}".format(settings["format_type"]))
        print("  3.  Check mode         : {}".format(settings["check_mode"]))
        if settings["check_mode"] == "fixed":
            print("  4.  Check interval     : {} minutes".format(settings["check_interval_minutes"]))
        else:
            print("  4.  Random range       : {}s - {}s".format(
                settings["random_interval_from"], settings["random_interval_to"]))
        print("  5.  Language           : {}".format(settings["language"]))
        print("  6.  Page language      : {}".format(settings["page_language"]))
        print("  7.  Telegram settings")
        print("  8.  Email settings")
        print("  9.  Back to main menu")
        print("")

        choice = input("  Select option [1-9]: ").strip()

        if choice == "1":
            _set_exam_type(settings)
        elif choice == "2":
            _set_format_type(settings)
        elif choice == "3":
            _set_check_mode(settings)
        elif choice == "4":
            _set_interval(settings)
        elif choice == "5":
            _set_language(settings)
        elif choice == "6":
            _set_page_language(settings)
        elif choice == "7":
            _telegram_settings(settings)
        elif choice == "8":
            _email_settings(settings)
        elif choice == "9":
            # Validate before saving
            ok, err = validate_settings(settings)
            if not ok:
                print("\n  [ERROR] {}".format(err))
                pause()
            else:
                save_settings(settings)
                print("\n  [OK] Settings saved to config.yaml")
                pause()
            return settings
        else:
            continue

    return settings


def _set_exam_type(settings):
    """Let user choose exam type."""
    print("")
    all_exams = get_all_exam_keys()
    print("  Available exam types:")
    for i, exam in enumerate(all_exams, 1):
        print("    {}. {}".format(i, exam))
    print("    {}. ALL (monitor every exam)".format(len(all_exams) + 1))
    print("")

    idx = read_int("Enter number", lo=1, hi=len(all_exams) + 1)
    if idx == len(all_exams) + 1:
        settings["exam_type"] = "ALL"
    else:
        settings["exam_type"] = all_exams[idx - 1]

    print("  -> Exam type set to: {}".format(settings["exam_type"]))
    pause()


def _set_format_type(settings):
    """Let user choose @HOME or @UNI."""
    print("")
    for i, fmt in enumerate(FORMAT_TYPES, 1):
        label = "online at home" if fmt == "@HOME" else "in-person at university"
        print("    {}. {} ({})".format(i, fmt, label))
    print("")

    idx = read_int("Enter number", lo=1, hi=len(FORMAT_TYPES))
    settings["format_type"] = FORMAT_TYPES[idx - 1]
    print("  -> Format set to: {}".format(settings["format_type"]))
    pause()


def _set_check_mode(settings):
    """Let user choose fixed or random."""
    print("")
    print("    1. fixed  - check every N minutes")
    print("    2. random - check at random intervals within a range")
    print("")

    idx = read_int("Enter number", lo=1, hi=2)
    settings["check_mode"] = "fixed" if idx == 1 else "random"
    print("  -> Check mode set to: {}".format(settings["check_mode"]))
    pause()


def _set_interval(settings):
    """Set fixed interval or random range."""
    print("")
    if settings["check_mode"] == "fixed":
        val = read_int("Check interval in minutes", default=settings["check_interval_minutes"], lo=1, hi=1440)
        settings["check_interval_minutes"] = val
        print("  -> Interval set to: {} minutes".format(val))
    else:
        print("  Set the random interval range in seconds.")
        print("  The bot will pick a random wait time between these two values.")
        print("  Consecutive waits are guaranteed to differ significantly.")
        print("")
        lo = read_int("From (seconds)", default=settings["random_interval_from"], lo=10)
        hi = read_int("To (seconds)", default=settings["random_interval_to"], lo=lo + 30)
        settings["random_interval_from"] = lo
        settings["random_interval_to"] = hi
        print("  -> Random interval set to: {}s - {}s".format(lo, hi))
    pause()


def _set_language(settings):
    """Set bot/CLI language."""
    print("")
    print("    1. en - English")
    print("    2. it - Italian")
    print("")
    idx = read_int("Enter number", lo=1, hi=2)
    settings["language"] = "en" if idx == 1 else "it"
    print("  -> Language set to: {}".format(settings["language"]))
    pause()


def _set_page_language(settings):
    """Set CISIA page language."""
    print("")
    print("    1. inglese  - English page")
    print("    2. italiano - Italian page")
    print("")
    idx = read_int("Enter number", lo=1, hi=2)
    settings["page_language"] = "inglese" if idx == 1 else "italiano"
    print("  -> Page language set to: {}".format(settings["page_language"]))
    pause()


def _telegram_settings(settings):
    """Telegram sub-menu."""
    tg = settings["telegram"]
    while True:
        clear_screen()
        print_banner()
        print("  === TELEGRAM SETTINGS ===")
        print("")
        print("  1. Enabled        : {}".format("ON" if tg["enabled"] else "OFF"))
        print("  2. Bot token      : {}".format(tg["bot_token"][:15] + "..." if tg["bot_token"] else "(not set)"))
        print("  3. Admin chat ID  : {}".format(tg["chat_id"] or "(not set)"))
        print("  4. Message count  : {}".format(tg["message_count"]))
        print("  5. Multi-user     : {}".format("ON" if tg["multi_user"] else "OFF"))
        print("  6. Back")
        print("")

        choice = input("  Select option [1-6]: ").strip()

        if choice == "1":
            tg["enabled"] = not tg["enabled"]
            print("  -> Telegram {}".format("ENABLED" if tg["enabled"] else "DISABLED"))
            pause()
        elif choice == "2":
            token = read_input("Bot token")
            if token:
                tg["bot_token"] = token
                print("  -> Token set.")
            pause()
        elif choice == "3":
            cid = read_input("Admin chat ID")
            if cid:
                tg["chat_id"] = cid
                print("  -> Chat ID set.")
            pause()
        elif choice == "4":
            mc = read_int("Messages per alert", default=tg["message_count"], lo=1, hi=50)
            tg["message_count"] = mc
            print("  -> Message count set to: {}".format(mc))
            pause()
        elif choice == "5":
            tg["multi_user"] = not tg["multi_user"]
            print("  -> Multi-user {}".format("ENABLED" if tg["multi_user"] else "DISABLED"))
            pause()
        elif choice == "6":
            break


def _email_settings(settings):
    """Email sub-menu."""
    em = settings["email"]
    while True:
        clear_screen()
        print_banner()
        print("  === EMAIL SETTINGS ===")
        print("")
        print("  1. Enabled       : {}".format("ON" if em["enabled"] else "OFF"))
        print("  2. SMTP host     : {}".format(em["smtp_host"]))
        print("  3. SMTP port     : {}".format(em["smtp_port"]))
        print("  4. SMTP user     : {}".format(em["smtp_user"] or "(not set)"))
        print("  5. SMTP password : {}".format("****" if em["smtp_password"] else "(not set)"))
        print("  6. From email    : {}".format(em["from_email"] or "(not set)"))
        print("  7. To email      : {}".format(em["to_email"] or "(not set)"))
        print("  8. Use TLS       : {}".format("ON" if em["use_tls"] else "OFF"))
        print("  9. Back")
        print("")

        choice = input("  Select option [1-9]: ").strip()

        if choice == "1":
            em["enabled"] = not em["enabled"]
            print("  -> Email {}".format("ENABLED" if em["enabled"] else "DISABLED"))
            pause()
        elif choice == "2":
            val = read_input("SMTP host", default=em["smtp_host"])
            em["smtp_host"] = val
            pause()
        elif choice == "3":
            val = read_int("SMTP port", default=em["smtp_port"], lo=1, hi=65535)
            em["smtp_port"] = val
            pause()
        elif choice == "4":
            val = read_input("SMTP user (email)")
            if val:
                em["smtp_user"] = val
            pause()
        elif choice == "5":
            val = read_input("SMTP password (app password)")
            if val:
                em["smtp_password"] = val
            pause()
        elif choice == "6":
            val = read_input("From email")
            if val:
                em["from_email"] = val
            pause()
        elif choice == "7":
            val = read_input("To email (receiver)")
            if val:
                em["to_email"] = val
            pause()
        elif choice == "8":
            em["use_tls"] = not em["use_tls"]
            print("  -> TLS {}".format("ENABLED" if em["use_tls"] else "DISABLED"))
            pause()
        elif choice == "9":
            break


def test_telegram(settings):
    """Test Telegram bot connection from the menu."""
    clear_screen()
    print_banner()
    print("  === TEST TELEGRAM CONNECTION ===")
    print("")

    tg = settings["telegram"]
    lang = I18n(settings["language"])
    logger = Logger(lang)

    if not tg["enabled"]:
        print("  [WARN] Telegram is disabled. Enable it in Settings first.")
        pause()
        return

    if not tg["bot_token"]:
        print("  [ERROR] Bot token is not set. Configure it in Settings > Telegram.")
        pause()
        return

    if not tg["chat_id"]:
        print("  [ERROR] Chat ID is not set. Configure it in Settings > Telegram.")
        pause()
        return

    print("  Bot token : {}...".format(tg["bot_token"][:15]))
    print("  Chat ID   : {}".format(tg["chat_id"]))
    print("")
    print("  Sending test message...")

    from notifications.telegram_bot import TelegramNotifier
    notifier = TelegramNotifier(
        bot_token=tg["bot_token"],
        chat_id=tg["chat_id"],
        lang=lang,
        logger=logger,
        message_count=tg["message_count"],
    )

    success = notifier.test_connection()

    if success:
        print("\n  [OK] Test message sent. Check your Telegram.")
    else:
        print("\n  [FAIL] Could not send message. Check your token and chat ID.")
        print("         Make sure you sent /start to your bot.")

    pause()


def test_email(settings):
    """Test email connection from the menu."""
    clear_screen()
    print_banner()
    print("  === TEST EMAIL CONNECTION ===")
    print("")

    em = settings["email"]
    lang = I18n(settings["language"])
    logger = Logger(lang)

    if not em["enabled"]:
        print("  [WARN] Email is disabled. Enable it in Settings first.")
        pause()
        return

    missing = []
    if not em["smtp_user"]:
        missing.append("smtp_user")
    if not em["smtp_password"]:
        missing.append("smtp_password")
    if not em["from_email"]:
        missing.append("from_email")
    if not em["to_email"]:
        missing.append("to_email")

    if missing:
        print("  [ERROR] Missing fields: {}".format(", ".join(missing)))
        print("          Configure them in Settings > Email.")
        pause()
        return

    print("  SMTP      : {}:{}".format(em["smtp_host"], em["smtp_port"]))
    print("  From      : {}".format(em["from_email"]))
    print("  To        : {}".format(em["to_email"]))
    print("")
    print("  Sending test email...")

    from notifications.email_sender import EmailNotifier
    notifier = EmailNotifier(
        smtp_host=em["smtp_host"],
        smtp_port=em["smtp_port"],
        smtp_user=em["smtp_user"],
        smtp_password=em["smtp_password"],
        from_email=em["from_email"],
        to_email=em["to_email"],
        use_tls=em["use_tls"],
        lang=lang,
        logger=logger,
    )

    success = notifier.send_test()

    if success:
        print("\n  [OK] Test email sent to {}".format(em["to_email"]))
    else:
        print("\n  [FAIL] Could not send email. Check your SMTP settings and credentials.")

    pause()


def show_about():
    """Display about information."""
    clear_screen()
    print_banner()
    print("  === ABOUT ===")
    print("")
    print("  Name      : CISIA CRAWLER")
    print("  Version   : 1.1.0")
    print("  Author    : Kasra Falahati")
    print("  License   : MIT")
    print("  GitHub    : {}".format(GITHUB_URL))
    print("")
    print("  A web scraper that monitors CISIA test calendars for")
    print("  available seats and sends instant notifications via")
    print("  Telegram and Email.")
    print("")
    print("  Supported exams:")
    all_exams = get_all_exam_keys()
    print("  {}".format(", ".join(all_exams)))
    print("")
    pause()


def show_donate():
    """Open the GitHub donate/sponsor page."""
    clear_screen()
    print_banner()
    print("  === DONATE ===")
    print("")
    print("  Thank you for considering a donation!")
    print("  Visit the GitHub repository to support the project:")
    print("")
    print("  {}".format(GITHUB_URL))
    print("")

    try:
        webbrowser.open(GITHUB_URL)
        print("  (Opening in your browser...)")
    except Exception:
        print("  (Could not open browser. Please visit the URL manually.)")

    pause()
