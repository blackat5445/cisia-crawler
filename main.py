#!/usr/bin/env python3
"""
CISIA CRAWLER v1.1.0
Author: Kasra Falahati
https://github.com/blackat5445/cisia-crawler

A web scraper to monitor CISIA test seat availability
and notify via Telegram and Email.
"""

import time
import signal
import sys

from config.settings import load_settings, validate_settings, print_banner, save_settings
from scraper.crawler import CisiaCrawler
from notifications.telegram_bot import TelegramNotifier
from notifications.email_sender import EmailNotifier
from utils.logger import Logger
from utils.i18n import I18n
from utils.scheduler import IntervalScheduler
from utils.menu import (
    show_main_menu, settings_menu, test_telegram, test_email,
    show_about, show_donate, clear_screen,
)


def signal_handler(sig, frame):
    print("\n\nCISIA CRAWLER stopped. Goodbye.")
    sys.exit(0)


def run_bot(settings):
    """Run the crawler loop with the given settings."""
    clear_screen()
    print_banner()

    ok, err = validate_settings(settings)
    if not ok:
        print("  [ERROR] {}".format(err))
        print("  Please fix your settings before starting.")
        input("\n  Press Enter to return to menu...")
        return

    lang = I18n(settings["language"])
    logger = Logger(lang)

    logger.info(lang.t("starting"))

    if settings["exam_type"] == "ALL":
        logger.info(lang.t("exam_type_all"))
    else:
        logger.info(lang.t("exam_type", exam=settings["exam_type"]))

    logger.info(lang.t("format_type", fmt=settings["format_type"]))

    if settings["check_mode"] == "fixed":
        logger.info(lang.t("interval_fixed", minutes=settings["check_interval_minutes"]))
    else:
        logger.info(lang.t("interval_random",
                           lo=settings["random_interval_from"],
                           hi=settings["random_interval_to"]))

    logger.info(lang.t("language_set", language=settings["language"]))

    scheduler = IntervalScheduler(
        mode=settings["check_mode"],
        fixed_minutes=settings["check_interval_minutes"],
        random_lo=settings["random_interval_from"],
        random_hi=settings["random_interval_to"],
    )

    # Telegram
    telegram = None
    if settings["telegram"]["enabled"]:
        telegram = TelegramNotifier(
            bot_token=settings["telegram"]["bot_token"],
            chat_id=settings["telegram"]["chat_id"],
            lang=lang,
            logger=logger,
            message_count=settings["telegram"]["message_count"],
            multi_user=settings["telegram"]["multi_user"],
        )
        logger.info(lang.t("telegram_enabled"))
        logger.info(lang.t("msg_count", count=settings["telegram"]["message_count"]))
        if settings["telegram"]["multi_user"]:
            telegram.start_polling()
    else:
        logger.warn(lang.t("telegram_disabled"))

    # Email
    email_notifier = None
    if settings["email"]["enabled"]:
        email_notifier = EmailNotifier(
            smtp_host=settings["email"]["smtp_host"],
            smtp_port=settings["email"]["smtp_port"],
            smtp_user=settings["email"]["smtp_user"],
            smtp_password=settings["email"]["smtp_password"],
            from_email=settings["email"]["from_email"],
            to_email=settings["email"]["to_email"],
            use_tls=settings["email"]["use_tls"],
            lang=lang,
            logger=logger,
        )
        logger.info(lang.t("email_enabled", email=settings["email"]["to_email"]))
    else:
        logger.warn(lang.t("email_disabled"))

    print("-" * 60)
    print("  Bot is running. Press Ctrl+C to stop and return to menu.")
    print("-" * 60)

    # IMPORTANT: Give the admin time to configure preferences (especially in
    # multi-user mode) before we start scraping.
    # This also helps reduce immediate burst traffic on Telegram.
    startup_delay_seconds = 5 * 60
    logger.info(lang.t("startup_delay", seconds=startup_delay_seconds))
    time.sleep(startup_delay_seconds)

    # In multi-user mode we need to scrape ALL exams and filter per user
    # preference when sending notifications.
    crawler_exam_type = "ALL" if settings["telegram"].get("multi_user") else settings["exam_type"]

    crawler = CisiaCrawler(
        exam_type=crawler_exam_type,
        format_type=settings["format_type"],
        language=settings["page_language"],
        logger=logger,
        lang=lang,
    )

    check_count = 0

    try:
        while True:
            check_count += 1
            logger.info(lang.t("check_number", n=check_count))

            try:
                results = crawler.check_availability()
                total_available = sum(len(seats) for seats in results.values())

                if total_available > 0:
                    logger.success(lang.t("seats_found", count=total_available))

                    for exam_key, seats in results.items():
                        for seat in seats:
                            logger.success(
                                "  [{exam}] {uni} - {city} | "
                                "{lbl_seats}: {seats} | "
                                "{lbl_date}: {date} | "
                                "{lbl_deadline}: {deadline}".format(
                                    exam=exam_key,
                                    uni=seat["university"],
                                    city=seat["city"],
                                    lbl_seats=lang.t("seats"),
                                    seats=seat["seats"],
                                    lbl_date=lang.t("date"),
                                    date=seat["date"],
                                    lbl_deadline=lang.t("deadline"),
                                    deadline=seat["deadline"],
                                )
                            )

                    if telegram:
                        telegram.send_availability_alert(results)
                        telegram.send_daily_no_spots(results)
                    if email_notifier:
                        email_notifier.send_availability_alert(results)
                else:
                    logger.info(lang.t("no_seats"))
                    if telegram:
                        telegram.send_daily_no_spots(results)

            except Exception as e:
                logger.error(lang.t("error_check", error=str(e)))

            wait = scheduler.next_seconds()

            if settings["check_mode"] == "fixed":
                logger.info(lang.t("next_check_fixed", minutes=settings["check_interval_minutes"]))
            else:
                logger.info(lang.t("next_check_random", seconds=wait))

            print("-" * 60)
            time.sleep(wait)

    except KeyboardInterrupt:
        print("\n\n  Bot stopped. Returning to menu...\n")
        return


def main():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    settings = load_settings()

    while True:
        # Re-register signal handler for menu mode (not exit on Ctrl+C from bot)
        signal.signal(signal.SIGINT, signal_handler)

        choice = show_main_menu(settings)

        if choice == "1":
            # Override signal handler so Ctrl+C returns to menu instead of exiting
            signal.signal(signal.SIGINT, signal.default_int_handler)
            run_bot(settings)
        elif choice == "2":
            settings = settings_menu(settings)
        elif choice == "3":
            test_telegram(settings)
        elif choice == "4":
            test_email(settings)
        elif choice == "5":
            show_about()
        elif choice == "6":
            show_donate()
        elif choice == "7":
            clear_screen()
            print("")
            print("  CISIA CRAWLER stopped. Goodbye.")
            print("")
            sys.exit(0)


if __name__ == "__main__":
    main()
