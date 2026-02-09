"""
Telegram notification sender — v2.
Group-based notifications, GitHub star gating, donation tracking,
and auto-expiring invite links.

Key changes from v1:
  - Bot sends notifications to EXAM-SPECIFIC GROUPS (not individual users).
  - Users must star the GitHub repo to unlock bot features.
  - /donate command shows USDT TRC20 address; /donate <tx_id> records donation.
  - /exam lets users pick an exam and receive a 1-minute invite link to the group.
  - New members in groups are verified: kicked if they haven't starred the repo.
"""

import requests
import threading
import time as _time
from collections import defaultdict

from config.settings import get_all_exam_keys
from utils.subscribers import SubscriberManager
from utils.github_stars import GitHubStarChecker, GITHUB_REPO_URL
from utils.donators import DonatorManager, USDT_TRC20_ADDRESS


# ── Exam -> Group chat_id mapping ─────────────────────────────────────────
# Fill in the actual group chat_ids after creating the groups.
# Use negative numbers for supergroups (e.g. -1001234567890).
EXAM_GROUP_IDS = {
    "CEnT-S":   "",   # fill with group chat_id
    "TOLC-AV":  "",
    "TOLC-B":   "",
    "TOLC-E":   "",
    "TOLC-F":   "",
    "TOLC-I":   "",
    "TOLC-LP":  "",
    "TOLC-PSI": "",
    "TOLC-S":   "",
    "TOLC-SPS": "",
    "TOLC-SU":  "",
}


class TelegramNotifier:
    API_URL = "https://api.telegram.org/bot{token}/{method}"

    def __init__(self, bot_token, chat_id, lang, logger,
                 message_count=5, multi_user=False, github_token=None):
        self.bot_token = bot_token
        self.chat_id = chat_id            # admin chat_id
        self.lang = lang
        self.logger = logger
        self.message_count = message_count
        self.multi_user = multi_user

        # Managers
        self.subscribers = SubscriberManager() if multi_user else None
        self.github = GitHubStarChecker(github_token=github_token)
        self.donators = DonatorManager()

        self._polling_thread = None
        self._last_no_spots_sent = defaultdict(dict)

    # ──────────────────────────────────────────────────────────────────────
    # Low-level Telegram helpers
    # ──────────────────────────────────────────────────────────────────────

    def _call_api(self, method, payload=None, max_retries=3):
        """Make a Telegram Bot API call with rate-limit handling."""
        url = self.API_URL.format(token=self.bot_token, method=method)

        for attempt in range(max_retries):
            try:
                resp = requests.post(url, json=payload or {}, timeout=20)

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

    def _send_message(self, chat_id, text, parse_mode="HTML",
                      disable_preview=True, reply_markup=None):
        """Send a single message to a specific chat_id."""
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": disable_preview,
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup
        result = self._call_api("sendMessage", payload)
        if result and result.get("ok"):
            return True
        return False

    # ──────────────────────────────────────────────────────────────────────
    # Invite link management
    # ──────────────────────────────────────────────────────────────────────

    def _create_invite_link(self, group_chat_id, expire_seconds=60, member_limit=1):
        """Create an invite link that expires after `expire_seconds`.

        Uses createChatInviteLink which produces a UNIQUE link per call.
        Safe for concurrent requests — each user gets their own link.
        """
        expire_date = int(_time.time()) + expire_seconds
        payload = {
            "chat_id": group_chat_id,
            "expire_date": expire_date,
            "member_limit": member_limit,
        }
        result = self._call_api("createChatInviteLink", payload)
        if result and result.get("ok"):
            return result["result"].get("invite_link")
        return None

    # ──────────────────────────────────────────────────────────────────────
    # Group member verification
    # ──────────────────────────────────────────────────────────────────────

    def _kick_unverified_member(self, chat_id, user_id, first_name=""):
        """Remove a user from a group if they haven't starred the repo."""
        payload = {"chat_id": chat_id, "user_id": user_id}
        self._call_api("banChatMember", payload)
        _time.sleep(0.5)
        # Immediately unban so they can re-join later with a valid invite
        payload_unban = {
            "chat_id": chat_id,
            "user_id": user_id,
            "only_if_banned": True,
        }
        self._call_api("unbanChatMember", payload_unban)
        self.logger.warn(
            "Kicked unverified user {} ({}) from group {}".format(
                first_name, user_id, chat_id
            )
        )

    # ──────────────────────────────────────────────────────────────────────
    # Message formatters
    # ──────────────────────────────────────────────────────────────────────

    def _format_exam_summary(self, exam_key, seats):
        """Format a single exam summary message (aggregated by city/region)."""
        groups = {}
        for s in seats:
            key = (s.get("region", ""), s.get("city", ""))
            g = groups.setdefault(key, {"seats": 0, "dates": set()})
            try:
                g["seats"] += int(str(s.get("seats", "0")).strip())
            except Exception:
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
                "\U0001F4CD <b>{region}</b> \u2013 {city}: {seats} {lbl_seats}, {dates} {lbl_dates}".format(
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

    # ──────────────────────────────────────────────────────────────────────
    # Public notification methods (sends to GROUPS now)
    # ──────────────────────────────────────────────────────────────────────

    def send_availability_alert(self, results_by_exam):
        """Send ONE aggregated message per exam to the corresponding GROUP."""
        for exam_key, seats in results_by_exam.items():
            if not seats:
                continue

            group_id = EXAM_GROUP_IDS.get(exam_key)
            if not group_id:
                continue

            message = self._format_exam_summary(exam_key, seats)
            self._send_message(group_id, message)
            _time.sleep(0.5)

    def send_daily_no_spots(self, results_by_exam, hours=24):
        """Send a daily 'still running' message per exam to the group."""
        now = int(_time.time())
        interval = int(hours * 3600)

        for exam_key in get_all_exam_keys():
            group_id = EXAM_GROUP_IDS.get(exam_key)
            if not group_id:
                continue

            seats = results_by_exam.get(exam_key, [])
            if seats:
                continue

            last = self._last_no_spots_sent.get(group_id, {}).get(exam_key, 0)
            if now - int(last) < interval:
                continue

            msg = self.lang.t("daily_no_spots", exam=exam_key)
            self._send_message(group_id, msg)
            self._last_no_spots_sent.setdefault(group_id, {})[exam_key] = now
            _time.sleep(0.5)

    def test_connection(self):
        """Send a test message to the admin to verify the bot works."""
        test_msg = "<b>CISIA CRAWLER</b>\n\n{}".format(self.lang.t("test_message"))
        return self._send_message(self.chat_id, test_msg)

    # ──────────────────────────────────────────────────────────────────────
    # Polling
    # ──────────────────────────────────────────────────────────────────────

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
                    params={
                        "offset": offset,
                        "timeout": 30,
                        "allowed_updates": '["message","chat_member"]',
                    },
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

    # ──────────────────────────────────────────────────────────────────────
    # Update router
    # ──────────────────────────────────────────────────────────────────────

    def _handle_update(self, update):
        """Route an incoming Telegram update to the right handler."""

        message = update.get("message")
        if not message:
            return

        # Handle new chat members (group join verification)
        new_members = message.get("new_chat_members", [])
        if new_members and message.get("chat", {}).get("type") in ("group", "supergroup"):
            self._handle_new_chat_members(message, new_members)
            return

        # Only handle private text messages for commands
        if "text" not in message:
            return
        if message.get("chat", {}).get("type") != "private":
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

        # ── Commands that work WITHOUT star verification ──

        if text == "/start":
            self._cmd_start(chat_id, user_info)
            return

        if text == "/donate":
            self._cmd_donate_info(chat_id)
            return

        if text.startswith("/donate "):
            tx_id = text[len("/donate "):].strip()
            if tx_id:
                self._cmd_donate_submit(chat_id, tx_id, user_info)
            else:
                self._cmd_donate_info(chat_id)
            return

        if text.startswith("/github ") or text.startswith("/star "):
            parts = text.split(None, 1)
            if len(parts) == 2:
                self._cmd_verify_star(chat_id, parts[1].strip(), user_info)
            else:
                self._send_message(chat_id, self.lang.t("github_usage"))
            return

        # ── Commands that REQUIRE star verification ──

        sub = self.subscribers.get_subscriber(chat_id) if self.subscribers else None
        if not sub or not sub.get("github_verified"):
            self._send_message(chat_id, self.lang.t("github_required"))
            return

        if text == "/stop":
            self._cmd_stop(chat_id)
        elif text == "/exam" or text == "/exams":
            self._cmd_exam_menu(chat_id)
        elif text == "/status":
            self._cmd_status(chat_id)
        elif text == "/help":
            self._cmd_help(chat_id)
        elif text == "/interval":
            self._send_message(chat_id, self.lang.t("interval_info"))
        elif text.startswith("/interval "):
            self._cmd_set_interval(chat_id, text)
        else:
            self._try_parse_exam_selection(chat_id, text)

    # ──────────────────────────────────────────────────────────────────────
    # Group join verification
    # ──────────────────────────────────────────────────────────────────────

    def _handle_new_chat_members(self, message, new_members):
        """Check every new member that joins a group.
        Kick them if they haven't starred the GitHub repo.
        """
        group_chat_id = str(message["chat"]["id"])

        for member in new_members:
            if member.get("is_bot", False):
                continue

            user_id = member.get("id")
            first_name = member.get("first_name", "Unknown")

            # Check if this user is a verified subscriber (lookup by user_id)
            verified = False
            if self.subscribers:
                for rec in self.subscribers.get_all_subscribers():
                    if str(rec.get("user_id")) == str(user_id) and rec.get("github_verified"):
                        verified = True
                        break

            if not verified:
                kick_msg = (
                    "\u274C <b>{name}</b>, you must verify your GitHub star before "
                    "joining this group.\n\n"
                    "1\uFE0F\u20E3 Star the repo: {repo}\n"
                    "2\uFE0F\u20E3 Open the bot in DM and send:\n"
                    "    <code>/github your_github_username</code>\n"
                    "3\uFE0F\u20E3 Then use /exam to get a new invite link."
                ).format(name=first_name, repo=GITHUB_REPO_URL)
                self._send_message(group_chat_id, kick_msg)
                _time.sleep(1)
                self._kick_unverified_member(group_chat_id, user_id, first_name)

    # ──────────────────────────────────────────────────────────────────────
    # Bot commands
    # ──────────────────────────────────────────────────────────────────────

    def _cmd_start(self, chat_id, user_info):
        is_new = self.subscribers.subscribe(chat_id, user_info=user_info)
        self._send_message(chat_id, self.lang.t("bot_welcome_v2"))
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

    def _cmd_donate_info(self, chat_id):
        """Show the USDT TRC20 donation address."""
        msg = self.lang.t("donate_info", address=USDT_TRC20_ADDRESS)
        self._send_message(chat_id, msg)

    def _cmd_donate_submit(self, chat_id, tx_id, user_info):
        """Record a donation transaction ID."""
        self.donators.add_donation(chat_id, tx_id, user_info=user_info)
        self._send_message(chat_id, self.lang.t("donate_submitted", tx_id=tx_id))

        # Notify admin
        admin_msg = (
            "\U0001F4B0 <b>New Donation Claim</b>\n\n"
            "User: {name} (@{username})\n"
            "Chat ID: {chat_id}\n"
            "TX ID: <code>{tx_id}</code>"
        ).format(
            name="{} {}".format(
                user_info.get("first_name", ""),
                user_info.get("last_name", ""),
            ).strip(),
            username=user_info.get("username", "N/A"),
            chat_id=chat_id,
            tx_id=tx_id,
        )
        if self.chat_id:
            self._send_message(self.chat_id, admin_msg)

        self.logger.info("Donation claim from {} (TX: {})".format(chat_id, tx_id))

    def _cmd_verify_star(self, chat_id, github_username, user_info):
        """Verify that a GitHub user has starred the repo."""
        github_username = github_username.strip().lstrip("@").strip("/")
        # Handle URLs like https://github.com/username
        if "github.com/" in github_username:
            github_username = github_username.rstrip("/").split("/")[-1]

        if not github_username:
            self._send_message(chat_id, self.lang.t("github_usage"))
            return

        self._send_message(chat_id, self.lang.t("github_checking", username=github_username))

        if self.github.has_starred(github_username):
            if self.subscribers:
                self.subscribers.set_github_verified(chat_id, github_username)
            self._send_message(chat_id, self.lang.t("github_verified", username=github_username))
            self.logger.info("GitHub verified: {} -> {}".format(chat_id, github_username))
        else:
            self._send_message(
                chat_id,
                self.lang.t("github_not_starred",
                            username=github_username, repo=GITHUB_REPO_URL),
            )

    def _cmd_exam_menu(self, chat_id):
        """Show the exam list so user can request an invite link."""
        all_exams = get_all_exam_keys()
        lines = []
        for i, exam in enumerate(all_exams, 1):
            lines.append("{}. {}".format(i, exam))

        prompt = self.lang.t("exam_select_prompt") + "\n\n" + "\n".join(lines)
        self._send_message(chat_id, prompt)

    def _cmd_status(self, chat_id):
        sub = self.subscribers.get_subscriber(chat_id)
        if not sub or not sub["active"]:
            self._send_message(chat_id, self.lang.t("bot_not_subscribed"))
            return

        gh = sub.get("github_username", "N/A")
        verified = "\u2705" if sub.get("github_verified") else "\u274C"
        is_donator = "\u2705" if self.donators.is_donator(chat_id) else "\u274C"

        msg = (
            "<b>Your Status</b>\n\n"
            "Active: {active}\n"
            "GitHub: @{gh} {verified}\n"
            "Donator: {donator}"
        ).format(
            active="Yes" if sub["active"] else "No",
            gh=gh,
            verified=verified,
            donator=is_donator,
        )
        self._send_message(chat_id, msg)

    def _cmd_help(self, chat_id):
        """Show all available commands."""
        self._send_message(chat_id, self.lang.t("help_message"))

    def _cmd_set_interval(self, chat_id, text):
        """Allow verified users to store a preferred check interval."""
        try:
            parts = text.split()
            minutes = int(parts[1])
            if minutes < 1 or minutes > 60:
                self._send_message(chat_id, "Interval must be between 1 and 60 minutes.")
                return
            if self.subscribers:
                self.subscribers.set_interval(chat_id, minutes)
            self._send_message(
                chat_id,
                self.lang.t("interval_set", minutes=minutes),
            )
        except (ValueError, IndexError):
            self._send_message(chat_id, "Usage: /interval <minutes> (1-60)")

    def _try_parse_exam_selection(self, chat_id, text):
        """Interpret the message as an exam selection for invite link."""
        sub = self.subscribers.get_subscriber(chat_id) if self.subscribers else None
        if not sub or not sub.get("active"):
            return

        if not sub.get("github_verified"):
            self._send_message(chat_id, self.lang.t("github_required"))
            return

        all_exams = get_all_exam_keys()

        # Try number
        try:
            idx = int(text.strip())
            if 1 <= idx <= len(all_exams):
                exam_key = all_exams[idx - 1]
                self._send_invite_link(chat_id, exam_key)
                return
        except ValueError:
            pass

        # Try exact exam name
        text_upper = text.strip().upper()
        for exam in all_exams:
            if text_upper == exam.upper():
                self._send_invite_link(chat_id, exam)
                return

    def _send_invite_link(self, chat_id, exam_key):
        """Generate a 1-minute invite link for the exam group and send it."""
        group_id = EXAM_GROUP_IDS.get(exam_key)
        if not group_id:
            self._send_message(
                chat_id,
                "\u26A0\uFE0F Group for <b>{}</b> is not configured yet.".format(exam_key),
            )
            return

        self._send_message(
            chat_id,
            self.lang.t("invite_generating", exam=exam_key),
        )

        # createChatInviteLink produces a unique link per call,
        # so concurrent requests for the same group each get their own link.
        link = self._create_invite_link(group_id, expire_seconds=60, member_limit=1)

        if link:
            self._send_message(
                chat_id,
                self.lang.t("invite_link", exam=exam_key, link=link),
            )
            self.logger.info("Invite link sent to {} for {}".format(chat_id, exam_key))
        else:
            self._send_message(
                chat_id,
                "\u274C Failed to create invite link for <b>{}</b>. "
                "Make sure the bot is an admin in the group.".format(exam_key),
            )
