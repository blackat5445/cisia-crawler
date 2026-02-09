# CISIA CRAWLER v1.2.1

**Author:** Kasra Falahati
**GitHub:** https://github.com/blackat5445/cisia-crawler

A Python bot that monitors the CISIA (https://testcisia.it) test calendar for
available seats and sends instant notifications via Telegram and Email.

---

## What's New in v1.2.1

- **Group-based notifications** -- alerts are now sent to 11 exam-specific
  Telegram groups instead of individual users, bypassing the 30 msg/min
  Telegram broadcast limit
- **GitHub star verification** -- users must star this repository and verify
  with `/github <username>` before accessing bot features
- **Donation system** -- USDT TRC20 donations with transaction tracking;
  donators get early access to new versions
- **Invite link system** -- verified users pick an exam via `/exam` and
  receive a unique invite link that expires in 1 minute (single-use)
- **Group member verification** -- unverified users who join a group are
  automatically kicked and instructed to verify first
- **User-controlled check interval** -- verified users can set their
  preferred check interval via `/interval`

---

## Features

- Interactive CLI menu -- configure everything without editing files
- Multi-exam support: TOLC-I, TOLC-E, TOLC-S, TOLC-F, TOLC-SU, TOLC-B,
  TOLC-AV, TOLC-PSI, TOLC-SPS, TOLC-LP, CEnT-S
- "ALL" mode: monitor every exam type at once
- Format filter: monitor @HOME (online) or @UNI (in-person) exams
- **Group-based Telegram alerts** -- one group per exam, no broadcast limits
- **GitHub star gating** -- only verified stargazers can use the bot
- **USDT TRC20 donation tracking** with admin notifications
- **Auto-expiring invite links** -- unique per user, 1-minute TTL
- **Auto-kick unverified group members** on join
- Multi-user Telegram mode with per-user exam filtering
- Captures subscriber name, username, numeric ID, GitHub username, and join date
- Email alerts: HTML-formatted email with all seat details
- Random interval scheduling with anti-clustering
- Bilingual: full English and Italian support
- Colored CLI logging with timestamps
- Built-in Telegram and Email connection tests

---

## Project Structure

```
cisia-crawler/
|-- main.py                  # Entry point (menu + bot)
|-- config.yaml              # Configuration (auto-created, editable via menu)
|-- requirements.txt         # Python dependencies
|-- README.md
|-- subscribers.json         # Auto-created in multi-user mode
|-- donators.json            # Auto-created when donations are submitted
|-- config/
|   |-- __init__.py
|   |-- settings.py          # Config loader, validation, save
|-- scraper/
|   |-- __init__.py
|   |-- crawler.py           # Web scraper (single + ALL exams)
|-- notifications/
|   |-- __init__.py
|   |-- telegram_bot.py      # Telegram notifier + groups + verification
|   |-- email_sender.py      # Email notifier
|-- utils/
    |-- __init__.py
    |-- menu.py               # Interactive CLI menu system
    |-- logger.py             # CLI logger
    |-- i18n.py               # English / Italian translations
    |-- scheduler.py          # Fixed + random interval scheduler
    |-- subscribers.py        # Subscriber persistence (JSON)
    |-- github_stars.py       # GitHub star verification (API)
    |-- donators.py           # Donation tracking (JSON)
```

---

## Installation

### Prerequisites

- Python 3.8 or later
- pip (Python package manager)

### Step 1: Download

```bash
git clone https://github.com/blackat5445/cisia-crawler.git
cd cisia-crawler
```

### Step 2: Install dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Run

```bash
python main.py
```

The interactive menu will appear. You can configure everything from there.

---

## Main Menu

When you run `python main.py`, you see:

```
  ================================================================
   CISIA CRAWLER v1.2.1
   Author: Kasra Falahati
   https://github.com/blackat5445/cisia-crawler
  ================================================================

  Current config: exam=CEnT-S | format=@HOME | mode=fixed | lang=EN
  Telegram: OFF | Email: OFF

  ----------------------------------------------------------------
  1. Start the bot
  2. Settings
  3. Test Telegram connection
  4. Test Email connection
  5. About
  6. Donate
  7. Exit
  ----------------------------------------------------------------
```

### Option 1: Start the bot

Starts the crawler loop. It will check for available seats at the
configured interval and send notifications when seats are found.
Press Ctrl+C to stop and return to the menu.

### Option 2: Settings

Opens the settings editor where you can configure:

- Exam type (single exam or ALL)
- Format type (@HOME or @UNI)
- Check mode (fixed or random interval)
- Interval settings (minutes for fixed, seconds range for random)
- Language (en/it) and page language (inglese/italiano)
- Telegram settings (token, chat ID, message count, multi-user, GitHub token)
- Email settings (SMTP host/port, credentials, sender/receiver)

All changes are saved to `config.yaml` when you exit the settings menu.

### Option 3: Test Telegram connection

Sends a test message to your Telegram admin chat to verify the bot
is properly configured.

### Option 4: Test Email connection

Sends a test email to the configured receiver address to verify
SMTP credentials work.

### Option 5: About

Shows project information.

### Option 6: Donate

Opens the GitHub repository page.

### Option 7: Exit

Quits the application.

---

## Configuration Reference

You can configure everything via the menu (option 2), or edit
`config.yaml` directly.

### exam_type

Set to any single exam name, or "ALL" to monitor every exam.

Available: TOLC-I, TOLC-E, TOLC-S, TOLC-F, TOLC-SU, TOLC-B,
TOLC-AV, TOLC-PSI, TOLC-SPS, TOLC-LP, CEnT-S, ALL

### format_type

- `@HOME` -- online at home
- `@UNI` -- in-person at university

### check_mode and intervals

Fixed mode: checks every N minutes.

```yaml
check_mode: fixed
check_interval_minutes: 5
```

Random mode: checks at random intervals within a range (seconds).
Consecutive waits are guaranteed to differ by at least 30% of the
range, preventing clustered checks.

```yaml
check_mode: random
random_interval_from: 60
random_interval_to: 900
```

### telegram.message_count

How many repeated messages to send per alert (1-50). Set this in
the menu under Settings > Telegram settings.

### telegram.multi_user

When true, the bot listens for commands from any Telegram user and
manages a subscriber list. Each subscriber can choose which exams
to follow.

### telegram.github_token

Optional GitHub personal access token. Without it, the GitHub API
allows 60 requests per hour (per IP). With a token, the limit
increases to 5,000 requests per hour. Recommended if you expect
many users verifying their stars.

Generate one at: https://github.com/settings/tokens
No special scopes are needed (public repo access only).

### exam_group_ids

Maps each exam type to a Telegram group chat ID. The bot sends
availability alerts directly to these groups instead of broadcasting
to individual users.

```yaml
exam_group_ids:
  CEnT-S: '-1001234567890'
  TOLC-AV: '-1001234567891'
  TOLC-B: '-1001234567892'
  # ... etc
```

See "Exam Groups Setup" below for how to get the group chat IDs.

---

## Telegram Setup

### Step 1: Create a Telegram Bot

1. Open Telegram and search for @BotFather
2. Send `/newbot`
3. Pick a name (e.g. "CISIA Seat Alert")
4. Pick a username ending in `bot` (e.g. `cisia_seat_alert_bot`)
5. BotFather replies with your bot token:
   `123456789:ABCdefGhIjKlMnOpQrStUvWxYz`
6. Save this token

### Step 2: Get Your Chat ID

1. Open Telegram, find your new bot, and send `/start`
2. Send any message, e.g. "hello"
3. Open this URL in your browser (replace YOUR_BOT_TOKEN):
   `https://api.telegram.org/botYOUR_BOT_TOKEN/getUpdates`
4. In the JSON response, find `"chat":{"id": 123456789}`
5. That number is your chat_id

### Step 3: Configure via Menu

1. Run `python main.py`
2. Select option 2 (Settings)
3. Select option 7 (Telegram settings)
4. Enable Telegram, enter your bot token and chat ID
5. Go back and select option 3 from the main menu to test

### Step 4: Test

Select option 3 from the main menu. If successful, you will
receive a test message in Telegram.

---

## Exam Groups Setup

The bot now sends alerts to exam-specific Telegram groups. You need
to create 11 groups and configure their chat IDs.

### Step 1: Create the groups

Create these 11 private groups in Telegram:

1. CEnT-S
2. TOLC-AV
3. TOLC-B
4. TOLC-E
5. TOLC-F
6. TOLC-I
7. TOLC-LP
8. TOLC-PSI
9. TOLC-S
10. TOLC-SPS
11. TOLC-SU

### Step 2: Add the bot as admin

In each group:

1. Go to group settings > Administrators > Add Administrator
2. Search for your bot username
3. Grant **all permissions** (especially "Invite Users via Link"
   and "Ban Users")

### Step 3: Get group chat IDs

After adding the bot to each group, send any message in the group.
Then check:

```
https://api.telegram.org/botYOUR_BOT_TOKEN/getUpdates
```

Look for `"chat":{"id": -1001234567890}` — the negative number is
the group chat ID.

### Step 4: Configure in config.yaml

```yaml
exam_group_ids:
  CEnT-S: '-1001234567890'
  TOLC-AV: '-1001234567891'
  TOLC-B: '-1001234567892'
  TOLC-E: '-1001234567893'
  TOLC-F: '-1001234567894'
  TOLC-I: '-1001234567895'
  TOLC-LP: '-1001234567896'
  TOLC-PSI: '-1001234567897'
  TOLC-S: '-1001234567898'
  TOLC-SPS: '-1001234567899'
  TOLC-SU: '-1001234567900'
```

### How it works

- Availability alerts go directly to the exam group (one message
  per exam, no broadcast limit issues)
- Users get invite links via `/exam` in the bot's DM
- Each invite link is unique, single-use, and expires in 1 minute
- Multiple users can request links for the same group simultaneously
  (each gets their own unique link)
- Unverified users who join a group are automatically kicked

---

## Making the Bot Public (Multi-User)

If you want other people to subscribe to your bot:

### 1. Set up bot commands via BotFather

Send `/setcommands` to @BotFather, select your bot, then paste:

```
start - Subscribe to seat alerts
github - Verify your GitHub star
exam - Get invite link to an exam group
status - Show your subscription info
interval - Set check interval (1-60 min)
donate - Support the project (USDT)
help - Show all commands
stop - Unsubscribe from alerts
```

### 2. Set a bot description

Send `/setdescription` to @BotFather:

> Monitors CISIA test calendars and sends you a notification when
> seats become available. Star the GitHub repo and send /start to
> get started.

### 3. Enable multi-user mode

In the menu: Settings > Telegram settings > Multi-user > ON

Or in config.yaml:

```yaml
exam_type: "ALL"
telegram:
  enabled: true
  bot_token: "YOUR_TOKEN"
  chat_id: "YOUR_ADMIN_CHAT_ID"
  message_count: 3
  multi_user: true
  github_token: ""  # optional, for higher API rate limit
```

### 4. Deploy and run

Run `python main.py`, select option 1 to start.

### 5. Share the bot

Give people the link: `https://t.me/YOUR_BOT_USERNAME`

### How it works for users

1. User sends `/start` → subscribed, but features are locked
2. User stars the GitHub repo: https://github.com/blackat5445/cisia-crawler
3. User sends `/github their_username` → bot verifies the star
4. Once verified, user sends `/exam` → sees numbered exam list
5. User sends a number (e.g. `6` for TOLC-I) → receives a unique
   invite link to the group (expires in 1 minute, single-use)
6. User joins the group and receives exam-specific alerts
7. User can send `/interval 3` to set preferred check interval
8. User can send `/status` to see their subscription info
9. User sends `/stop` → unsubscribed

### Donation flow

1. User sends `/donate` → sees USDT TRC20 address and instructions
2. User sends USDT (min $1) to the displayed address
3. User sends `/donate <transaction_id>` → donation is recorded
4. Admin receives a notification with user details and TX ID
5. Admin manually verifies the transaction and adds the user to
   an early-access group

Donator details are saved in `donators.json`.

### Group member verification

When someone joins an exam group, the bot automatically:

1. Checks if the user's Telegram ID matches a verified subscriber
2. If not verified → sends a warning message in the group explaining
   what to do, then kicks the user
3. The user is unbanned immediately so they can rejoin after
   verifying their GitHub star

This ensures only verified users remain in the groups.

### What the bot captures about subscribers

When a user sends /start, the bot records:

- Telegram numeric user ID
- Username (if set)
- First name and last name
- GitHub username (after verification)
- GitHub verification status
- Preferred check interval
- Date and time of subscription

This data is stored in `subscribers.json` on your server. No
message history is recorded.

---

## Email Setup

### Gmail

1. Enable 2-Step Verification on your Google account
2. Go to App passwords: https://myaccount.google.com/apppasswords
3. Generate a password for "Mail"
4. Configure via menu: Settings > Email settings

Or in config.yaml:

```yaml
email:
  enabled: true
  smtp_host: smtp.gmail.com
  smtp_port: 587
  smtp_user: your.email@gmail.com
  smtp_password: abcd efgh ijkl mnop
  from_email: your.email@gmail.com
  to_email: receiver@example.com
  use_tls: true
```

### Other providers

| Provider | SMTP Host             | Port |
|----------|-----------------------|------|
| Gmail    | smtp.gmail.com        | 587  |
| Outlook  | smtp.office365.com    | 587  |
| Yahoo    | smtp.mail.yahoo.com   | 587  |

---

## Deployment

### Option 1: screen (simple)

```bash
sudo apt install screen
screen -S cisia
python main.py
# Select 1 to start the bot
# Detach: Ctrl+A then D
# Reattach: screen -r cisia
```

### Option 2: systemd (recommended)

Create `/etc/systemd/system/cisia-crawler.service`:

```ini
[Unit]
Description=CISIA CRAWLER - Test Seat Monitor
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/cisia-crawler
ExecStart=/usr/bin/python3 /path/to/cisia-crawler/main.py
Restart=always
RestartSec=10
StandardInput=tty

[Install]
WantedBy=multi-user.target
```

Note: for headless/server use where the interactive menu is not
practical, you can configure everything in config.yaml beforehand
and the bot will start with option 1 automatically. Alternatively,
you can pass `--start` as a command line argument (see below).

```bash
sudo systemctl daemon-reload
sudo systemctl enable cisia-crawler
sudo systemctl start cisia-crawler
journalctl -u cisia-crawler -f
```

### Option 3: nohup

```bash
nohup python main.py > cisia.log 2>&1 &
tail -f cisia.log
```

### Option 4: Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
CMD ["python", "main.py"]
```

```bash
docker build -t cisia-crawler .
docker run -d --name cisia-crawler --restart unless-stopped \
  -v $(pwd)/config.yaml:/app/config.yaml \
  -v $(pwd)/subscribers.json:/app/subscribers.json \
  -v $(pwd)/donators.json:/app/donators.json \
  cisia-crawler
```

---

## About

| Field   | Value                                        |
|---------|----------------------------------------------|
| Name    | CISIA CRAWLER                                |
| Version | 1.2.1                                        |
| Author  | Kasra Falahati                               |
| License | Attribution-NonCommercial 4.0 International  |
| GitHub  | https://github.com/blackat5445/cisia-crawler |

---

## FAQ

**How often should I set the check interval?**
3-5 minutes for fixed mode. For random mode, a range of 60-900
seconds works well.

**Can I monitor multiple exams?**
Yes. Set exam_type to ALL via the menu or config.yaml.

**The bot says no seats but I see them on the website?**
Make sure your format_type (@HOME or @UNI) matches what you see.

**Telegram messages not arriving?**
Use option 3 from the main menu to test the connection. Make sure
you sent /start to your bot first.

**Why do users need to star the GitHub repo?**
This is a lightweight verification step that helps track genuine
users and supports the project's visibility. The bot checks the
GitHub stargazers API to verify.

**What if the GitHub API rate limit is hit?**
Without a token, the limit is 60 requests/hour. Set a personal
access token in `telegram.github_token` to increase it to
5,000 requests/hour. No special scopes are needed.

**How do invite links work?**
Each `/exam` selection generates a unique link via Telegram's
`createChatInviteLink` API. Links expire in 1 minute and allow
exactly 1 join. Multiple users requesting links simultaneously
each get their own unique link.

**What happens if an unverified user joins a group?**
The bot detects the join event, sends a warning message explaining
what to do, kicks the user, then immediately unbans them so they
can rejoin after completing verification.

**How do donations work?**
Users send USDT (TRC20) to the displayed address and submit their
transaction ID via `/donate <tx_id>`. The admin receives a
notification and manually verifies the transaction. Donator details
are stored in `donators.json`.

**How does random anti-clustering work?**
If you set 60-900, the range is 840s. 30% of that is 252s. So if
the bot waits 100s, the next wait will differ by at least 252s
(e.g. 352s or more). This prevents checking twice in quick
succession.

**WARNING! DO NOT SET THE INTERVAL CHECKING TIME BELOW 3 MINUTES, THIS MAY RESULT SERVER IP BLOCK!**
