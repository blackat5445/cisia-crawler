"""
Telegram notification sender.
Supports single admin mode and multi-user subscriber mode.
Captures user profile info (name, username, id, join date) on /start.
"""

import requests
import threading
import time as _time

from config.settings import get_all_exam_keys
from utils.subscribers import SubscriberManager


class TelegramNotifier:
    API_URL = "https://api.telegram.org/bot{token}/{method}"

    def __init__(self, bot_token, chat_id, lang, logger, message_count=5, multi_user=False):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.lang = lang
        self.logger = logger
        self.message_count = message_count
        self.multi_user = multi_user
        self.subscribers = SubscriberManager() if multi_user else None
        self._polling_thread = None

    def _call_api(self, method, payload):
        """Make a Telegram Bot API call."""
        url = self.API_URL.format(token=self.bot_token, method=method)
        try:
            resp = requests.post(url, json=payload, timeout=15)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            self.logger.error(self.lang.t("telegram_error", error=str(e)))
            return None

    def _send_message(self, chat_id, text):
        """Send a single message to a specific chat_id."""
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        result = self._call_api("sendMessage", payload)
        if result and result.get("ok"):
            return True
        return False

    def _format_alert(self, seat):
        """Format a single seat alert message (Telegram only - emojis here)."""
        return (
            "\xf0\x9f\x9a\xa8 <b>{title}</b>\n\n"
            "\xf0\x9f\x93\x8b <b>{lbl_exam}:</b> {exam}\n"
            "\xf0\x9f\x93\x8b <b>{lbl_fmt}:</b> {fmt}\n"
            "\xf0\x9f\x8f\xab <b>{lbl_uni}:</b> {uni}\n"
            "\xf0\x9f\x93\x8d <b>{lbl_city}:</b> {city}\n"
            "\xf0\x9f\x97\xba <b>{lbl_region}:</b> {region}\n"
            "\xf0\x9f\x92\xba <b>{lbl_seats}:</b> {seats}\n"
            "\xf0\x9f\x93\x85 <b>{lbl_date}:</b> {date}\n"
            "\xe2\x8f\xb0 <b>{lbl_deadline}:</b> {deadline}\n\n"
            "\xf0\x9f\x94\x97 <a href='https://testcisia.it/studenti_tolc/login_sso.php'>"
            "\xf0\x9f\x93\x8c {book}</a>"
        ).format(
            title=self.lang.t("alert_title"),
            lbl_exam=self.lang.t("exam"),
            exam=seat.get("exam", ""),
            lbl_fmt=self.lang.t("format"),
            fmt=seat["format"],
            lbl_uni=self.lang.t("university"),
            uni=seat["university"],
            lbl_city=self.lang.t("city"),
            city=seat["city"],
            lbl_region=self.lang.t("region"),
            region=seat["region"],
            lbl_seats=self.lang.t("seats"),
            seats=seat["seats"],
            lbl_date=self.lang.t("date"),
            date=seat["date"],
            lbl_deadline=self.lang.t("deadline"),
            deadline=seat["deadline"],
            book=self.lang.t("book_now"),
        )

    def send_availability_alert(self, results_by_exam):
        """Send alerts for all available seats."""
        for exam_key, seats in results_by_exam.items():
            if not seats:
                continue

            for seat in seats:
                message = self._format_alert(seat)

                # Always notify admin
                if self.chat_id:
                    for i in range(self.message_count):
                        self._send_message(self.chat_id, message)
                        self.logger.info(
                            self.lang.t("telegram_repeat", current=i + 1, total=self.message_count)
                        )

                # Notify subscribers in multi-user mode
                if self.multi_user and self.subscribers:
                    for sub in self.subscribers.get_active_subscribers():
                        sub_id = sub["chat_id"]
                        if sub_id == str(self.chat_id):
                            continue

                        if not self.subscribers.wants_exam(sub_id, exam_key):
                            self.logger.debug(
                                self.lang.t("telegram_subscriber_skip",
                                            chat_id=sub_id, exam=exam_key)
                            )
                            continue

                        for i in range(self.message_count):
                            self._send_message(sub_id, message)
                        self.logger.info(
                            self.lang.t("telegram_subscriber_sent", chat_id=sub_id)
                        )

    def test_connection(self):
        """Send a test message to the admin to verify the bot works."""
        test_msg = "<b>CISIA CRAWLER</b>\n\n{}".format(self.lang.t("test_message"))
        return self._send_message(self.chat_id, test_msg)

    # ------------------------------------------------------------------
    # Multi-user polling
    # ------------------------------------------------------------------

    def start_polling(self):
        """Start a background thread that polls for Telegram updates."""
        if not self.multi_user:
            return
        self._polling_thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._polling_thread.start()
        self.logger.info(self.lang.t("telegram_multiuser"))

    def _poll_loop(self):
        """Long-poll for Telegram updates and handle commands."""
        offset = 0
        while True:
            try:
                url = self.API_URL.format(token=self.bot_token, method="getUpdates")
                resp = requests.get(
                    url,
                    params={"offset": offset, "timeout": 30},
                    timeout=35,
                )
                data = resp.json()
                if not data.get("ok"):
                    _time.sleep(5)
                    continue

                for update in data.get("result", []):
                    offset = update["update_id"] + 1
                    self._handle_update(update)

            except Exception:
                _time.sleep(5)

    def _handle_update(self, update):
        """Route an incoming Telegram update to the right handler."""
        message = update.get("message")
        if not message or "text" not in message:
            return

        chat_id = str(message["chat"]["id"])
        text = message["text"].strip()

        # Extract user profile info
        user = message.get("from", {})
        user_info = {
            "user_id": user.get("id", ""),
            "username": user.get("username", ""),
            "first_name": user.get("first_name", ""),
            "last_name": user.get("last_name", ""),
        }

        if text == "/start":
            self._cmd_start(chat_id, user_info)
        elif text == "/stop":
            self._cmd_stop(chat_id)
        elif text == "/exams":
            self._cmd_exams(chat_id)
        elif text == "/status":
            self._cmd_status(chat_id)
        else:
            self._try_parse_exam_selection(chat_id, text)

    def _cmd_start(self, chat_id, user_info):
        is_new = self.subscribers.subscribe(chat_id, user_info=user_info)
        self._send_message(chat_id, self.lang.t("bot_welcome"))
        if is_new:
            name = "{} {}".format(
                user_info.get("first_name", ""),
                user_info.get("last_name", ""),
            ).strip()
            self.logger.info(
                self.lang.t("bot_new_subscriber",
                            name=name or "Unknown",
                            username=user_info.get("username", "N/A"),
                            user_id=user_info.get("user_id", "N/A"))
            )

    def _cmd_stop(self, chat_id):
        self.subscribers.unsubscribe(chat_id)
        self._send_message(chat_id, self.lang.t("bot_stopped"))

    def _cmd_exams(self, chat_id):
        sub = self.subscribers.get_subscriber(chat_id)
        if not sub or not sub["active"]:
            self._send_message(chat_id, self.lang.t("bot_not_subscribed"))
            return

        all_exams = get_all_exam_keys()
        lines = []
        for i, exam in enumerate(all_exams, 1):
            lines.append("{}. {}".format(i, exam))
        prompt = self.lang.t("bot_choose_exams") + "\n\n" + "\n".join(lines)
        self._send_message(chat_id, prompt)

    def _cmd_status(self, chat_id):
        sub = self.subscribers.get_subscriber(chat_id)
        if not sub or not sub["active"]:
            self._send_message(chat_id, self.lang.t("bot_not_subscribed"))
            return

        exams_str = ", ".join(sub["exams"]) if sub["exams"] else self.lang.t("bot_status_all")
        msg = self.lang.t("bot_status", active="Yes", exams=exams_str)
        self._send_message(chat_id, msg)

    def _try_parse_exam_selection(self, chat_id, text):
        """Try to interpret the message as an exam selection."""
        sub = self.subscribers.get_subscriber(chat_id)
        if not sub or not sub["active"]:
            return

        all_exams = get_all_exam_keys()

        if text.lower() == "all":
            self.subscribers.set_exams(chat_id, [])
            self._send_message(
                chat_id,
                self.lang.t("bot_exams_updated", exams=self.lang.t("bot_status_all")),
            )
            return

        try:
            indices = [int(x.strip()) for x in text.split(",")]
            selected = []
            for idx in indices:
                if 1 <= idx <= len(all_exams):
                    selected.append(all_exams[idx - 1])
            if selected:
                self.subscribers.set_exams(chat_id, selected)
                self._send_message(
                    chat_id,
                    self.lang.t("bot_exams_updated", exams=", ".join(selected)),
                )
            else:
                self._send_message(chat_id, self.lang.t("bot_exams_invalid"))
        except ValueError:
            pass
