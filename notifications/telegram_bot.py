"""
Telegram notification sender.
Supports single admin mode and multi-user subscriber mode.
Captures user profile info (name, username, id, join date) on /start.
"""

import requests
import threading
import time as _time
from collections import defaultdict

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
        # chat_id -> exam_key -> last_sent_epoch_seconds
        self._last_no_spots_sent = defaultdict(dict)

    def _call_api(self, method, payload, max_retries=3):
        """Make a Telegram Bot API call with basic rate-limit handling."""
        url = self.API_URL.format(token=self.bot_token, method=method)

        for attempt in range(max_retries):
            try:
                resp = requests.post(url, json=payload, timeout=20)

                # Handle Telegram rate-limits (HTTP 429)
                if resp.status_code == 429:
                    try:
                        data = resp.json() or {}
                    except Exception:
                        data = {}
                    retry_after = 5
                    if isinstance(data, dict):
                        retry_after = (
                            data.get("parameters", {}).get("retry_after")
                            or retry_after
                        )
                    self.logger.warn(self.lang.t("telegram_rate_limited", seconds=retry_after))
                    _time.sleep(int(retry_after) + 1)
                    continue

                # Transient server errors
                if 500 <= resp.status_code < 600:
                    _time.sleep(2)
                    continue

                resp.raise_for_status()
                return resp.json()

            except Exception as e:
                if attempt == max_retries - 1:
                    self.logger.error(self.lang.t("telegram_error", error=str(e)))
                    return None
                _time.sleep(2)

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

    def _format_exam_summary(self, exam_key, seats):
        """Format a single exam summary message (aggregated by city/region)."""
        # Group by (region, city)
        groups = {}
        for s in seats:
            key = (s.get("region", ""), s.get("city", ""))
            g = groups.setdefault(key, {"seats": 0, "dates": set()})
            # seats may be "---"; parse defensively
            try:
                g["seats"] += int(str(s.get("seats", "0")).strip())
            except Exception:
                # if we can't parse, count it as 1 "available"
                g["seats"] += 1
            d = str(s.get("date", "")).strip()
            if d:
                g["dates"].add(d)

        lines = [
            "\U0001F6A8 <b>{}</b>".format(exam_key),
            "",
        ]
        for (region, city), g in sorted(groups.items(), key=lambda x: (x[0][0], x[0][1])):
            lines.append(
                "\U0001F4CD <b>{region}</b> – {city}: {seats} {lbl_seats}, {dates} {lbl_dates}".format(
                    region=region or "-",
                    city=city or "-",
                    seats=g["seats"],
                    lbl_seats=self.lang.t("seats"),
                    dates=len(g["dates"]),
                    lbl_dates=self.lang.t("dates"),
                )
            )

        lines += [
            "",
            "\U0001F517 <a href='https://testcisia.it/studenti_tolc/login_sso.php'>\U0001F4CC {}</a>".format(
                self.lang.t("book_now")
            ),
        ]

        return "\n".join(lines)

    def _format_alert(self, seat):
        """Legacy per-seat alert formatter (kept for compatibility)."""
        return (
            "\U0001F6A8 <b>{title}</b>\n\n"
            "\U0001F4CB <b>{lbl_exam}:</b> {exam}\n"
            "\U0001F4CB <b>{lbl_fmt}:</b> {fmt}\n"
            "\U0001F3EB <b>{lbl_uni}:</b> {uni}\n"
            "\U0001F4CD <b>{lbl_city}:</b> {city}\n"
            "\U0001F5FA <b>{lbl_region}:</b> {region}\n"
            "\U0001F4BA <b>{lbl_seats}:</b> {seats}\n"
            "\U0001F4C5 <b>{lbl_date}:</b> {date}\n"
            "\u23F0 <b>{lbl_deadline}:</b> {deadline}\n\n"
            "\U0001F517 <a href='https://testcisia.it/studenti_tolc/login_sso.php'>"
            "\U0001F4CC {book}</a>"
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

    def _get_recipient_ids(self):
        """Return list of chat_ids to notify."""
        recipients = []
        if self.multi_user and self.subscribers:
            recipients = [r["chat_id"] for r in self.subscribers.get_active_subscribers()]
            if self.chat_id and str(self.chat_id) not in recipients:
                recipients.append(str(self.chat_id))
        else:
            if self.chat_id:
                recipients = [str(self.chat_id)]
        return recipients

    def _user_selected_exams(self, chat_id):
        """Return list of selected exams for a user (may include ALL)."""
        if not self.multi_user or not self.subscribers:
            return ["ALL"]

        rec = self.subscribers.get_subscriber(chat_id)
        if rec and rec.get("active"):
            return rec.get("exams", [])

        # If the admin isn't subscribed, default admin to ALL.
        if self.chat_id and str(chat_id) == str(self.chat_id):
            return ["ALL"]

        return []

    def send_availability_alert(self, results_by_exam):
        """Send ONE aggregated message per exam (per user)."""
        recipients = self._get_recipient_ids()

        for rid in recipients:
            selected = self._user_selected_exams(rid)
            if not selected:
                continue

            wants_all = "ALL" in selected

            for exam_key, seats in results_by_exam.items():
                if not seats:
                    continue
                if not wants_all and exam_key not in selected:
                    continue

                message = self._format_exam_summary(exam_key, seats)
                self._send_message(rid, message)
                _time.sleep(0.2)

    def send_daily_no_spots(self, results_by_exam, hours=24):
        """Send a daily 'still running' message per exam when no seats are found."""
        now = int(_time.time())
        interval = int(hours * 3600)
        recipients = self._get_recipient_ids()

        for rid in recipients:
            selected = self._user_selected_exams(rid)
            if not selected:
                continue

            exams_to_check = get_all_exam_keys() if "ALL" in selected else selected

            for exam_key in exams_to_check:
                seats = results_by_exam.get(exam_key, [])
                if seats:
                    continue

                last = self._last_no_spots_sent[str(rid)].get(exam_key, 0)
                if now - int(last) < interval:
                    continue

                msg = self.lang.t("daily_no_spots", exam=exam_key)
                self._send_message(rid, msg)
                self._last_no_spots_sent[str(rid)][exam_key] = now
                _time.sleep(0.2)

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

        exams = sub["exams"]
        if not exams:
            exams_str = self.lang.t("bot_status_none")
        elif "ALL" in exams:
            exams_str = self.lang.t("bot_status_all")
        else:
            exams_str = ", ".join(exams)
        msg = self.lang.t("bot_status", active="Yes", exams=exams_str)
        self._send_message(chat_id, msg)

    def _try_parse_exam_selection(self, chat_id, text):
        """Try to interpret the message as an exam selection."""
        sub = self.subscribers.get_subscriber(chat_id)
        if not sub or not sub["active"]:
            return

        all_exams = get_all_exam_keys()

        if text.lower() == "all":
            self.subscribers.set_exams(chat_id, ["ALL"])
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
