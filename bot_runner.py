#!/usr/bin/env python3
"""
Headless bot runner — started by the web panel.
Runs the crawler loop without the CLI menu.
Checks bot_stats.is_running() to know when to stop.
"""

import sys
import time
import os

from config.settings import load_settings, validate_settings
from scraper.crawler import CisiaCrawler
from notifications.telegram_bot import TelegramNotifier
from notifications.email_sender import EmailNotifier
from utils.logger import Logger
from utils.i18n import I18n
from utils.scheduler import IntervalScheduler
from utils.bot_stats import BotStats

bot_stats = BotStats()


def run():
    settings = load_settings()
    ok, err = validate_settings(settings)
    if not ok:
        print("[ERROR] {}".format(err))
        bot_stats.set_running(False)
        sys.exit(1)

    lang = I18n(settings["language"])
    logger = Logger(lang)
    logger.info(lang.t("starting"))

    bot_stats.set_running(True, pid=os.getpid())

    scheduler = IntervalScheduler(
        mode=settings["check_mode"],
        fixed_minutes=settings["check_interval_minutes"],
        random_lo=settings["random_interval_from"],
        random_hi=settings["random_interval_to"],
    )

    # Telegram
    telegram = None
    if settings["telegram"]["enabled"]:
        from notifications.telegram_bot import EXAM_GROUP_IDS
        import notifications.telegram_bot as _tg_mod
        for k, v in settings.get("exam_group_ids", {}).items():
            if v:
                EXAM_GROUP_IDS[k] = v
        _tg_mod.PREMIUM_GROUP_ID = settings.get("premium_group_id", "")

        telegram = TelegramNotifier(
            bot_token=settings["telegram"]["bot_token"],
            chat_id=settings["telegram"]["chat_id"],
            lang=lang, logger=logger,
            message_count=settings["telegram"]["message_count"],
            multi_user=settings["telegram"]["multi_user"],
            github_token=settings["telegram"].get("github_token", ""),
        )
        if settings["telegram"]["multi_user"]:
            telegram.start_polling()

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
            lang=lang, logger=logger,
        )

    # Startup delay
    delay = settings.get("startup_delay_seconds", 300)
    if delay > 0:
        logger.info("Startup delay: {}s".format(delay))
        for _ in range(delay):
            if not bot_stats.is_running():
                return
            time.sleep(1)

    crawler_exam_type = "ALL" if settings["telegram"].get("multi_user") else settings["exam_type"]
    crawler = CisiaCrawler(
        exam_type=crawler_exam_type,
        format_type=settings["format_type"],
        language=settings["page_language"],
        logger=logger, lang=lang,
    )

    check_count = 0
    try:
        while bot_stats.is_running():
            check_count += 1
            logger.info(lang.t("check_number", n=check_count))
            try:
                results = crawler.check_availability()
                total = sum(len(s) for s in results.values())
                bot_stats.record_crawl(seats_found=total, exams_checked=len(results))

                if total > 0:
                    logger.success(lang.t("seats_found", count=total))
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
                bot_stats.record_error(str(e))

            wait = scheduler.next_seconds()
            for _ in range(int(wait)):
                if not bot_stats.is_running():
                    break
                time.sleep(1)
    finally:
        bot_stats.set_running(False)


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        bot_stats.set_running(False)
    except Exception as e:
        bot_stats.set_running(False)
        bot_stats.record_error("Fatal: {}".format(str(e)))
