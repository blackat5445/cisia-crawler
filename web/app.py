"""
CISIA CRAWLER — Admin Web Panel v2
Flask app with 2FA, bot start/stop, user management, statistics, charts.
"""

import os
import sys
import json
import hmac
import time
import struct
import hashlib
import base64
import secrets
import functools
import threading
import subprocess

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, jsonify, send_from_directory,
)

from config.settings import load_settings, save_settings, get_all_exam_keys
from utils.subscribers import SubscriberManager
from utils.donators import DonatorManager
from utils.bot_stats import BotStats

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
app.config["PERMANENT_SESSION_LIFETIME"] = 86400  # 24h

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADMIN_FILE = os.path.join(BASE_DIR, "admin_auth.json")
USERS_FILE = os.path.join(BASE_DIR, "web_users.json")

bot_stats = BotStats()
_bot_process = None
_bot_lock = threading.Lock()

# ── TOTP ──────────────────────────────────────────────────────────────────

def _hotp(secret_bytes, counter):
    msg = struct.pack(">Q", counter)
    h = hmac.new(secret_bytes, msg, hashlib.sha1).digest()
    o = h[-1] & 0x0F
    code = struct.unpack(">I", h[o:o+4])[0] & 0x7FFFFFFF
    return code % 1000000

def totp_verify(secret_b32, code, window=1):
    secret_bytes = base64.b32decode(secret_b32.upper().replace(" ", ""))
    counter = int(time.time()) // 30
    for i in range(-window, window + 1):
        if hmac.compare_digest("{:06d}".format(_hotp(secret_bytes, counter + i)), code.strip()):
            return True
    return False

def generate_totp_secret():
    return base64.b32encode(secrets.token_bytes(20)).decode("ascii")

def get_totp_uri(secret, issuer="CISIA-CRAWLER", account="admin"):
    return "otpauth://totp/{i}:{a}?secret={s}&issuer={i}&digits=6&period=30".format(
        i=issuer, a=account, s=secret)

# ── Admin/User auth ──────────────────────────────────────────────────────

def load_admin():
    if os.path.exists(ADMIN_FILE):
        try:
            with open(ADMIN_FILE, "r") as f: return json.load(f)
        except: pass
    return None

def save_admin(data):
    with open(ADMIN_FILE, "w") as f: json.dump(data, f, indent=2)

def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r") as f: return json.load(f)
        except: pass
    return []

def save_users(users):
    with open(USERS_FILE, "w") as f: json.dump(users, f, indent=2)

def hash_pw(salt, password):
    return hashlib.sha256((salt + password).encode()).hexdigest()

def login_required(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("authenticated"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("authenticated"):
            return redirect(url_for("login"))
        if session.get("role") != "admin":
            flash("Admin access required.", "error")
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    return decorated

# ── Favicon ───────────────────────────────────────────────────────────────

@app.route("/favicon.ico")
def favicon():
    return send_from_directory(os.path.join(app.root_path, "static"),
                               "favicon.ico", mimetype="image/x-icon")

# ── Auth Routes ───────────────────────────────────────────────────────────

@app.route("/")
def index():
    if not session.get("authenticated"):
        return redirect(url_for("login"))
    return redirect(url_for("dashboard"))

@app.route("/setup", methods=["GET", "POST"])
def setup():
    admin = load_admin()
    if admin:
        return redirect(url_for("login"))
    if request.method == "POST":
        pw = request.form.get("password", "")
        confirm = request.form.get("confirm", "")
        totp_code = request.form.get("totp_code", "")
        totp_secret = request.form.get("totp_secret", "")
        if len(pw) < 6:
            flash("Password must be at least 6 characters.", "error")
            return render_template("setup.html", totp_secret=totp_secret, totp_uri=get_totp_uri(totp_secret))
        if pw != confirm:
            flash("Passwords do not match.", "error")
            return render_template("setup.html", totp_secret=totp_secret, totp_uri=get_totp_uri(totp_secret))
        if not totp_verify(totp_secret, totp_code):
            flash("Invalid 2FA code.", "error")
            return render_template("setup.html", totp_secret=totp_secret, totp_uri=get_totp_uri(totp_secret))
        salt = secrets.token_hex(16)
        save_admin({"password_hash": hash_pw(salt, pw), "salt": salt, "totp_secret": totp_secret})
        flash("Admin account created! Please log in.", "success")
        return redirect(url_for("login"))
    ts = generate_totp_secret()
    return render_template("setup.html", totp_secret=ts, totp_uri=get_totp_uri(ts))

@app.route("/login", methods=["GET", "POST"])
def login():
    admin = load_admin()
    if not admin:
        return redirect(url_for("setup"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        pw = request.form.get("password", "")
        totp_code = request.form.get("totp_code", "")
        # Try admin login
        if username == "" or username.lower() == "admin":
            if hmac.compare_digest(hash_pw(admin["salt"], pw), admin["password_hash"]):
                if totp_verify(admin["totp_secret"], totp_code):
                    session["authenticated"] = True
                    session["role"] = "admin"
                    session["username"] = "admin"
                    session.permanent = True
                    return redirect(url_for("dashboard"))
                flash("Invalid 2FA code.", "error")
                return render_template("login.html")
        # Try user login
        users = load_users()
        for u in users:
            if u["username"].lower() == username.lower():
                if hmac.compare_digest(hash_pw(u["salt"], pw), u["password_hash"]):
                    if totp_verify(u["totp_secret"], totp_code):
                        session["authenticated"] = True
                        session["role"] = u.get("role", "user")
                        session["username"] = u["username"]
                        session.permanent = True
                        return redirect(url_for("dashboard"))
                    flash("Invalid 2FA code.", "error")
                    return render_template("login.html")
        flash("Invalid credentials.", "error")
        return render_template("login.html")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ── Dashboard ─────────────────────────────────────────────────────────────

@app.route("/dashboard")
@login_required
def dashboard():
    subs = SubscriberManager()
    donators = DonatorManager()
    settings = load_settings()
    stats = bot_stats.get_stats()
    daily = bot_stats.get_daily_data(14)

    all_subs = subs.get_all_subscribers()
    active_count = sum(1 for s in all_subs if s.get("active"))
    verified_count = sum(1 for s in all_subs if s.get("github_verified"))
    pending_donations = len(donators.get_unverified_donators())
    premium_count = len(donators.get_verified_donators())

    return render_template("dashboard.html",
        total_subs=len(all_subs), active_count=active_count,
        verified_count=verified_count, pending_donations=pending_donations,
        premium_count=premium_count, settings=settings, stats=stats,
        daily_data=json.dumps(daily), is_admin=session.get("role") == "admin")

# ── Bot Control ───────────────────────────────────────────────────────────

@app.route("/api/bot/start", methods=["POST"])
@admin_required
def bot_start():
    global _bot_process
    with _bot_lock:
        if bot_stats.is_running():
            return jsonify({"ok": False, "message": "Bot is already running."})
        try:
            bot_stats.set_running(True)
            _bot_process = subprocess.Popen(
                [sys.executable, os.path.join(BASE_DIR, "bot_runner.py")],
                cwd=BASE_DIR,
            )
            return jsonify({"ok": True, "message": "Bot started."})
        except Exception as e:
            bot_stats.set_running(False)
            return jsonify({"ok": False, "message": str(e)})

@app.route("/api/bot/stop", methods=["POST"])
@admin_required
def bot_stop():
    global _bot_process
    with _bot_lock:
        bot_stats.set_running(False)
        if _bot_process:
            try:
                _bot_process.terminate()
            except: pass
            _bot_process = None
        return jsonify({"ok": True, "message": "Bot stop signal sent."})

@app.route("/api/bot/status")
@login_required
def bot_status():
    return jsonify({"running": bot_stats.is_running()})

# ── Members ───────────────────────────────────────────────────────────────

@app.route("/members")
@login_required
def members():
    subs = SubscriberManager()
    donators = DonatorManager()
    all_subs = subs.get_all_subscribers()
    for s in all_subs:
        s["is_premium"] = donators.is_verified_donator(s.get("chat_id", ""))
    return render_template("members.html", members=all_subs, is_admin=session.get("role") == "admin")

# ── Donations ─────────────────────────────────────────────────────────────

@app.route("/donations")
@login_required
def donations():
    donators = DonatorManager()
    return render_template("donations.html", donations=donators.get_all_donators(),
                           is_admin=session.get("role") == "admin")

@app.route("/api/donation/<chat_id>/verify", methods=["POST"])
@admin_required
def verify_donation(chat_id):
    d = DonatorManager()
    if d.set_verified(chat_id, True):
        return jsonify({"ok": True, "message": "Verified."})
    return jsonify({"ok": False, "message": "Not found."}), 404

@app.route("/api/donation/<chat_id>/reject", methods=["POST"])
@admin_required
def reject_donation(chat_id):
    d = DonatorManager()
    if d.remove_donator(chat_id):
        return jsonify({"ok": True, "message": "Rejected."})
    return jsonify({"ok": False, "message": "Not found."}), 404

# ── Statistics ────────────────────────────────────────────────────────────

@app.route("/statistics")
@login_required
def statistics():
    subs = SubscriberManager()
    donators = DonatorManager()
    settings = load_settings()
    stats = bot_stats.get_stats()
    daily = bot_stats.get_daily_data(30)
    all_subs = subs.get_all_subscribers()

    # Group membership counts
    group_ids = settings.get("exam_group_ids", {})
    exams = get_all_exam_keys()
    group_stats = []
    for exam in exams:
        gid = group_ids.get(exam, "")
        # Count subs who have this exam in their preferences or all
        count = sum(1 for s in all_subs if s.get("active") and s.get("github_verified"))
        group_stats.append({"exam": exam, "configured": bool(gid), "members": count})

    # Donation stats
    all_don = donators.get_all_donators()
    verified_don = [d for d in all_don if d.get("verified")]
    pending_don = [d for d in all_don if not d.get("verified")]

    return render_template("statistics.html",
        stats=stats, daily_data=json.dumps(daily),
        group_stats=group_stats, all_subs=all_subs,
        total_donations=len(all_don), verified_donations=len(verified_don),
        pending_donations=len(pending_don),
        is_admin=session.get("role") == "admin")

# ── Settings ──────────────────────────────────────────────────────────────

@app.route("/settings", methods=["GET", "POST"])
@admin_required
def settings_page():
    settings = load_settings()
    if request.method == "POST":
        settings["exam_type"] = request.form.get("exam_type", settings["exam_type"])
        settings["format_type"] = request.form.get("format_type", settings["format_type"])
        settings["check_mode"] = request.form.get("check_mode", settings["check_mode"])
        for k in ["check_interval_minutes", "random_interval_from", "random_interval_to", "startup_delay_seconds"]:
            try: settings[k] = int(request.form.get(k, settings.get(k, 0)))
            except: pass
        settings["language"] = request.form.get("language", settings["language"])
        settings["page_language"] = request.form.get("page_language", settings["page_language"])
        tg = settings["telegram"]
        tg["enabled"] = request.form.get("tg_enabled") == "on"
        tg["bot_token"] = request.form.get("tg_bot_token", tg["bot_token"])
        tg["chat_id"] = request.form.get("tg_chat_id", tg["chat_id"])
        tg["multi_user"] = request.form.get("tg_multi_user") == "on"
        tg["github_token"] = request.form.get("tg_github_token", tg.get("github_token", ""))
        try: tg["message_count"] = int(request.form.get("tg_message_count", 5))
        except: pass
        groups = settings.setdefault("exam_group_ids", {})
        for exam in get_all_exam_keys():
            groups[exam] = request.form.get("group_{}".format(exam.replace("-", "_")), "").strip()
        settings["premium_group_id"] = request.form.get("premium_group_id", "").strip()
        save_settings(settings)
        flash("Settings saved. Restart the bot for changes to take effect.", "success")
        return redirect(url_for("settings_page"))
    return render_template("settings.html", settings=settings, all_exams=get_all_exam_keys(),
                           is_admin=session.get("role") == "admin")

# ── User Management ──────────────────────────────────────────────────────

@app.route("/users")
@admin_required
def users_page():
    users = load_users()
    return render_template("users.html", users=users, is_admin=True)

@app.route("/users/create", methods=["GET", "POST"])
@admin_required
def create_user():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        pw = request.form.get("password", "")
        confirm = request.form.get("confirm", "")
        role = request.form.get("role", "user")
        totp_code = request.form.get("totp_code", "")
        totp_secret = request.form.get("totp_secret", "")
        if not username or len(username) < 3:
            flash("Username must be at least 3 characters.", "error")
            return render_template("create_user.html", totp_secret=totp_secret,
                                   totp_uri=get_totp_uri(totp_secret, account=username or "user"), is_admin=True)
        if username.lower() == "admin":
            flash("Cannot use 'admin' as username.", "error")
            return render_template("create_user.html", totp_secret=totp_secret,
                                   totp_uri=get_totp_uri(totp_secret, account=username), is_admin=True)
        if len(pw) < 6:
            flash("Password must be at least 6 characters.", "error")
            return render_template("create_user.html", totp_secret=totp_secret,
                                   totp_uri=get_totp_uri(totp_secret, account=username), is_admin=True)
        if pw != confirm:
            flash("Passwords do not match.", "error")
            return render_template("create_user.html", totp_secret=totp_secret,
                                   totp_uri=get_totp_uri(totp_secret, account=username), is_admin=True)
        if not totp_verify(totp_secret, totp_code):
            flash("Invalid 2FA code. Have the user scan the QR code and enter the code.", "error")
            return render_template("create_user.html", totp_secret=totp_secret,
                                   totp_uri=get_totp_uri(totp_secret, account=username), is_admin=True)
        users = load_users()
        for u in users:
            if u["username"].lower() == username.lower():
                flash("Username already exists.", "error")
                return render_template("create_user.html", totp_secret=totp_secret,
                                       totp_uri=get_totp_uri(totp_secret, account=username), is_admin=True)
        salt = secrets.token_hex(16)
        users.append({
            "username": username, "password_hash": hash_pw(salt, pw),
            "salt": salt, "totp_secret": totp_secret, "role": role,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        })
        save_users(users)
        flash("User '{}' created.".format(username), "success")
        return redirect(url_for("users_page"))
    ts = generate_totp_secret()
    return render_template("create_user.html", totp_secret=ts,
                           totp_uri=get_totp_uri(ts, account="new_user"), is_admin=True)

@app.route("/api/users/<username>/delete", methods=["POST"])
@admin_required
def delete_user(username):
    users = load_users()
    users = [u for u in users if u["username"].lower() != username.lower()]
    save_users(users)
    return jsonify({"ok": True})

# ── Run ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
