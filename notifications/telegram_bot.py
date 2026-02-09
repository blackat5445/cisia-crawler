"""
Telegram notification sender — v2.1.
Group-based notifications, GitHub star gating, donation/premium tracking,
auto-expiring invite links, and admin-only controls.

Architecture:
  - Alerts go to 11 exam-specific groups (bypasses 30 msg/min limit).
  - Users must star the GitHub repo to unlock basic bot features.
  - Verified donators become "premium" and gain access to a premium group
    with faster check intervals (30s–1min).
  - /interval is admin-only (hidden from /help).
  - /donators is admin-only: list pending donations, verify or reject.
  - Unverified users joining any exam group are kicked.
  - Non-premium users joining the premium group are kicked.
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
# Populated at startup from config.yaml via main.py
EXAM_GROUP_IDS = {
    "CEnT-S":   "",
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

# Premium group chat_id — populated at startup from config.yaml
PREMIUM_GROUP_ID = ""


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

        # Admin donator-review state: admin_chat_id -> list of pending records
        self._admin_donator_state = {}

    # ──────────────────────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────────────────────

    def _is_admin(self, chat_id):
        """Check if a chat_id is the admin."""
        return self.chat_id and str(chat_id) == str(self.chat_id)

    # ──────────────────────────────────────────────────────────────────────
    # Low-level Telegram API
    # ──────────────────────────────────────────────────────────────────────

    def _call_api(self, method, payload=None, max_retries=3):
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
                        retry_after = data.get("parameters", {}).get("retry_after") or retry_after
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
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": disable_preview,
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup
        result = self._call_api("sendMessage", payload)
        return bool(result and result.get("ok"))

    # ──────────────────────────────────────────────────────────────────────
    # Invite link management
    # ──────────────────────────────────────────────────────────────────────

    def _create_invite_link(self, group_chat_id, expire_seconds=60, member_limit=1):
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
    # Kick helper
    # ──────────────────────────────────────────────────────────────────────

    def _kick_member(self, chat_id, user_id, first_name="", reason="unverified"):
        """Ban then immediately unban so user can rejoin later."""
        self._call_api("banChatMember", {"chat_id": chat_id, "user_id": user_id})
        _time.sleep(0.5)
        self._call_api("unbanChatMember", {
            "chat_id": chat_id, "user_id": user_id, "only_if_banned": True,
        })
        self.logger.warn("Kicked {} user {} ({}) from group {}".format(
            reason, first_name, user_id, chat_id))

    # ──────────────────────────────────────────────────────────────────────
    # Message formatters
    # ──────────────────────────────────────────────────────────────────────

    def _format_exam_summary(self, exam_key, seats):
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

        lines = ["\U0001F6A8 <b>{}</b>".format(exam_key), ""]
        for (region, city), g in sorted(groups.items(), key=lambda x: (x[0][0], x[0][1])):
            lines.append(
                "\U0001F4CD <b>{region}</b> \u2013 {city}: {seats} {lbl_seats}, "
                "{dates} {lbl_dates}".format(
                    region=region or "-", city=city or "-",
                    seats=g["seats"], lbl_seats=self.lang.t("seats"),
                    dates=len(g["dates"]), lbl_dates=self.lang.t("dates"),
                ))
        lines += [
            "",
            "\U0001F517 <a href='https://testcisia.it/studenti_tolc/login_sso.php'>"
            "\U0001F4CC {}</a>".format(self.lang.t("book_now")),
        ]
        return "\n".join(lines)

    # ──────────────────────────────────────────────────────────────────────
    # Public notification methods (sends to GROUPS)
    # ──────────────────────────────────────────────────────────────────────

    def send_availability_alert(self, results_by_exam):
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
        test_msg = "<b>CISIA CRAWLER</b>\n\n{}".format(self.lang.t("test_message"))
        return self._send_message(self.chat_id, test_msg)

    # ──────────────────────────────────────────────────────────────────────
    # Polling
    # ──────────────────────────────────────────────────────────────────────

    def start_polling(self):
        if not self.multi_user:
            return
        self._polling_thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._polling_thread.start()
        self.logger.info(self.lang.t("telegram_multiuser"))

    def _poll_loop(self):
        offset = 0
        while True:
            try:
                url = self.API_URL.format(token=self.bot_token, method="getUpdates")
                resp = requests.get(url, params={
                    "offset": offset, "timeout": 30,
                    "allowed_updates": '["message","chat_member"]',
                }, timeout=35)
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
        message = update.get("message")
        if not message:
            return

        # Handle new chat members (group join verification)
        new_members = message.get("new_chat_members", [])
        if new_members and message.get("chat", {}).get("type") in ("group", "supergroup"):
            self._handle_new_chat_members(message, new_members)
            return

        if "text" not in message:
            return
        if message.get("chat", {}).get("type") != "private":
            return

        chat_id = str(message["chat"]["id"])
        text = message["text"].strip()

        user = message.get("from", {})
        user_info = {
            "user_id": user.get("id", ""),
            "username": user.get("username", ""),
            "first_name": user.get("first_name", ""),
            "last_name": user.get("last_name", ""),
        }

        # ── Check if admin is in donator-review flow ──
        if self._is_admin(chat_id) and chat_id in self._admin_donator_state:
            self._handle_donator_review_reply(chat_id, text)
            return

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

        # ── Admin-only commands (before star gate) ──

        if self._is_admin(chat_id):
            if text == "/interval":
                self._send_message(chat_id, self.lang.t("interval_info"))
                return
            if text.startswith("/interval "):
                self._cmd_set_interval(chat_id, text)
                return
            if text == "/donators":
                self._cmd_donators_list(chat_id)
                return

        # ── Star verification gate ──

        sub = self.subscribers.get_subscriber(chat_id) if self.subscribers else None
        if not sub or not sub.get("github_verified"):
            self._send_message(chat_id, self.lang.t("github_required"))
            return

        # ── Commands that require star verification ──

        if text == "/stop":
            self._cmd_stop(chat_id)
        elif text == "/exam" or text == "/exams":
            self._cmd_exam_menu(chat_id)
        elif text == "/status":
            self._cmd_status(chat_id)
        elif text == "/help":
            self._cmd_help(chat_id)
        else:
            self._try_parse_exam_selection(chat_id, text)

    # ──────────────────────────────────────────────────────────────────────
    # Group join verification
    # ──────────────────────────────────────────────────────────────────────

    def _handle_new_chat_members(self, message, new_members):
        """Verify new members joining any group.
        - Exam groups: must be github-verified
        - Premium group: must be a verified donator
        """
        group_chat_id = str(message["chat"]["id"])
        is_premium_group = PREMIUM_GROUP_ID and group_chat_id == str(PREMIUM_GROUP_ID)

        for member in new_members:
            if member.get("is_bot", False):
                continue

            user_id = member.get("id")
            first_name = member.get("first_name", "Unknown")

            # Look up subscriber record by user_id
            sub_record = None
            if self.subscribers:
                for rec in self.subscribers.get_all_subscribers():
                    if str(rec.get("user_id")) == str(user_id):
                        sub_record = rec
                        break

            if is_premium_group:
                # Premium group: must be a verified donator
                is_premium = False
                if sub_record:
                    is_premium = self.donators.is_verified_donator(sub_record.get("chat_id", ""))

                if not is_premium:
                    kick_msg = (
                        "\u274C <b>{name}</b>, this group is for <b>Premium</b> members only.\n\n"
                        "To become Premium:\n"
                        "1\uFE0F\u20E3 Send /donate in the bot DM\n"
                        "2\uFE0F\u20E3 Donate via USDT (TRC20)\n"
                        "3\uFE0F\u20E3 Submit your TX ID with /donate &lt;tx_id&gt;\n"
                        "4\uFE0F\u20E3 Wait for admin verification"
                    ).format(name=first_name)
                    self._send_message(group_chat_id, kick_msg)
                    _time.sleep(1)
                    self._kick_member(group_chat_id, user_id, first_name, "non-premium")
            else:
                # Exam groups: must be github-verified
                verified = sub_record and sub_record.get("github_verified", False)

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
                    self._kick_member(group_chat_id, user_id, first_name, "unverified")

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
            self.logger.info(self.lang.t(
                "bot_new_subscriber",
                name=name or "Unknown",
                username=user_info.get("username", "N/A"),
                user_id=user_info.get("user_id", "N/A"),
            ))

    def _cmd_stop(self, chat_id):
        self.subscribers.unsubscribe(chat_id)
        self._send_message(chat_id, self.lang.t("bot_stopped"))

    # ── Donate ──

    def _cmd_donate_info(self, chat_id):
        msg = self.lang.t("donate_info", address=USDT_TRC20_ADDRESS)
        self._send_message(chat_id, msg)

    def _cmd_donate_submit(self, chat_id, tx_id, user_info):
        self.donators.add_donation(chat_id, tx_id, user_info=user_info)
        self._send_message(chat_id, self.lang.t("donate_submitted", tx_id=tx_id))

        # Notify admin
        admin_msg = (
            "\U0001F4B0 <b>New Donation Claim</b>\n\n"
            "User: {name} (@{username})\n"
            "Chat ID: {chat_id}\n"
            "TX ID: <code>{tx_id}</code>\n\n"
            "Use /donators to review."
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

    # ── GitHub star verification ──

    def _cmd_verify_star(self, chat_id, github_username, user_info):
        github_username = github_username.strip().lstrip("@").strip("/")
        if "github.com/" in github_username:
            github_username = github_username.rstrip("/").split("/")[-1]

        if not github_username:
            self._send_message(chat_id, self.lang.t("github_usage"))
            return

        # Check if this GitHub username is already claimed by another user
        if self.subscribers and self.subscribers.is_github_username_taken(github_username, exclude_chat_id=chat_id):
            self._send_message(
                chat_id,
                "\u274C The GitHub username <b>{}</b> is already verified by another user.\n\n"
                "Each GitHub account can only be linked to one Telegram account.".format(github_username),
            )
            return

        self._send_message(chat_id, self.lang.t("github_checking", username=github_username))

        if self.github.has_starred(github_username):
            if self.subscribers:
                result = self.subscribers.set_github_verified(chat_id, github_username)
                if not result:
                    self._send_message(
                        chat_id,
                        "\u274C The GitHub username <b>{}</b> is already verified by another user.".format(github_username),
                    )
                    return
            self._send_message(chat_id, self.lang.t("github_verified", username=github_username))
            self.logger.info("GitHub verified: {} -> {}".format(chat_id, github_username))
        else:
            self._send_message(chat_id, self.lang.t(
                "github_not_starred", username=github_username, repo=GITHUB_REPO_URL))

    # ── Exam selection ──

    def _cmd_exam_menu(self, chat_id):
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
        is_premium = self.donators.is_verified_donator(chat_id)
        premium_str = "\u2B50 Premium" if is_premium else "\u274C"
        has_pending = self.donators.is_donator(chat_id) and not is_premium
        pending_str = " (pending verification)" if has_pending else ""

        msg = (
            "<b>Your Status</b>\n\n"
            "Active: {active}\n"
            "GitHub: @{gh} {verified}\n"
            "Premium: {premium}{pending}"
        ).format(
            active="Yes" if sub["active"] else "No",
            gh=gh, verified=verified,
            premium=premium_str, pending=pending_str,
        )
        self._send_message(chat_id, msg)

    def _cmd_help(self, chat_id):
        self._send_message(chat_id, self.lang.t("help_message"))

    # ── Admin-only: interval ──

    def _cmd_set_interval(self, chat_id, text):
        try:
            parts = text.split()
            minutes = int(parts[1])
            if minutes < 1 or minutes > 60:
                self._send_message(chat_id, "Interval must be between 1 and 60 minutes.")
                return
            if self.subscribers:
                self.subscribers.set_interval(chat_id, minutes)
            self._send_message(chat_id, self.lang.t("interval_set", minutes=minutes))
        except (ValueError, IndexError):
            self._send_message(chat_id, "Usage: /interval <minutes> (1-60)")

    # ── Admin-only: donators review ──

    def _cmd_donators_list(self, chat_id):
        """Show the list of unverified donators for admin to review."""
        pending = self.donators.get_unverified_donators()
        if not pending:
            self._send_message(chat_id, "\u2705 No pending donation claims.")
            return

        lines = ["\U0001F4CB <b>Pending Donation Claims</b>\n"]
        for i, rec in enumerate(pending, 1):
            name = "{} {}".format(rec.get("first_name", ""), rec.get("last_name", "")).strip()
            lines.append(
                "{idx}. {name} (@{username})\n"
                "   Chat ID: <code>{chat_id}</code>\n"
                "   TX ID: <code>{tx}</code>\n"
                "   Date: {date}".format(
                    idx=i, name=name or "Unknown",
                    username=rec.get("username", "N/A"),
                    chat_id=rec.get("chat_id", ""),
                    tx=rec.get("transaction_id", ""),
                    date=rec.get("donated_at", ""),
                ))

        lines.append("")
        lines.append(
            "Reply with the <b>number</b> to review that donation.\n"
            "Send /cancel to exit."
        )

        # Store the pending list so we can reference it by index
        self._admin_donator_state[chat_id] = {"step": "select", "pending": pending}
        self._send_message(chat_id, "\n".join(lines))

    def _handle_donator_review_reply(self, chat_id, text):
        """Handle multi-step admin donator review conversation."""
        state = self._admin_donator_state.get(chat_id)
        if not state:
            return

        if text.lower() == "/cancel":
            del self._admin_donator_state[chat_id]
            self._send_message(chat_id, "Donator review cancelled.")
            return

        step = state.get("step", "select")

        if step == "select":
            # Admin is selecting a donator by number
            try:
                idx = int(text.strip())
                pending = state["pending"]
                if idx < 1 or idx > len(pending):
                    self._send_message(chat_id, "Invalid number. Enter 1-{}.".format(len(pending)))
                    return

                selected = pending[idx - 1]
                state["selected"] = selected
                state["step"] = "action"

                name = "{} {}".format(
                    selected.get("first_name", ""),
                    selected.get("last_name", ""),
                ).strip()
                msg = (
                    "\U0001F50D <b>Reviewing donation:</b>\n\n"
                    "User: {name} (@{username})\n"
                    "Chat ID: <code>{cid}</code>\n"
                    "TX ID: <code>{tx}</code>\n"
                    "Date: {date}\n\n"
                    "Reply:\n"
                    "<b>1</b> = \u2705 Verify (make Premium)\n"
                    "<b>2</b> = \u274C Reject (remove claim)\n"
                    "/cancel = Go back"
                ).format(
                    name=name or "Unknown",
                    username=selected.get("username", "N/A"),
                    cid=selected.get("chat_id", ""),
                    tx=selected.get("transaction_id", ""),
                    date=selected.get("donated_at", ""),
                )
                self._send_message(chat_id, msg)

            except ValueError:
                self._send_message(chat_id, "Send a number or /cancel.")

        elif step == "action":
            selected = state.get("selected", {})
            target_chat_id = str(selected.get("chat_id", ""))
            name = "{} {}".format(
                selected.get("first_name", ""),
                selected.get("last_name", ""),
            ).strip() or "Unknown"

            if text.strip() == "1":
                # Verify
                self.donators.set_verified(target_chat_id, True)
                del self._admin_donator_state[chat_id]

                self._send_message(
                    chat_id,
                    "\u2705 <b>{}</b> is now Premium!".format(name),
                )

                # Notify the user
                self._send_message(
                    target_chat_id,
                    self.lang.t("donate_verified_user"),
                )

                # Send premium group invite link if configured
                if PREMIUM_GROUP_ID:
                    link = self._create_invite_link(PREMIUM_GROUP_ID, expire_seconds=60, member_limit=1)
                    if link:
                        self._send_message(
                            target_chat_id,
                            self.lang.t("premium_invite_link", link=link),
                        )

                self.logger.info("Donator verified: {} ({})".format(name, target_chat_id))

            elif text.strip() == "2":
                # Reject
                self.donators.remove_donator(target_chat_id)
                del self._admin_donator_state[chat_id]

                self._send_message(
                    chat_id,
                    "\u274C Donation claim from <b>{}</b> has been rejected and removed.".format(name),
                )

                # Notify the user
                self._send_message(
                    target_chat_id,
                    self.lang.t("donate_rejected_user"),
                )

                self.logger.info("Donator rejected: {} ({})".format(name, target_chat_id))
            else:
                self._send_message(chat_id, "Reply <b>1</b> (verify), <b>2</b> (reject), or /cancel.")

    # ── Exam selection parsing ──

    def _try_parse_exam_selection(self, chat_id, text):
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
                self._send_invite_link(chat_id, all_exams[idx - 1])
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
        group_id = EXAM_GROUP_IDS.get(exam_key)
        if not group_id:
            self._send_message(
                chat_id,
                "\u26A0\uFE0F Group for <b>{}</b> is not configured yet.".format(exam_key),
            )
            return

        self._send_message(chat_id, self.lang.t("invite_generating", exam=exam_key))

        link = self._create_invite_link(group_id, expire_seconds=60, member_limit=1)
        if link:
            self._send_message(chat_id, self.lang.t("invite_link", exam=exam_key, link=link))
            self.logger.info("Invite link sent to {} for {}".format(chat_id, exam_key))
        else:
            self._send_message(
                chat_id,
                "\u274C Failed to create invite link for <b>{}</b>. "
                "Make sure the bot is admin in the group.".format(exam_key),
            )
