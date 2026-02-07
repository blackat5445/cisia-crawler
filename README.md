# CISIA CRAWLER v1.1.0

**Author:** Kasra Falahati
**GitHub:** https://github.com/blackat5445/cisia-crawler

A Python bot that monitors the CISIA (https://testcisia.it) test calendar for
available seats and sends instant notifications via Telegram and Email.

---

## Features

- Interactive CLI menu -- configure everything without editing files
- Multi-exam support: TOLC-I, TOLC-E, TOLC-S, TOLC-F, TOLC-SU, TOLC-B,
  TOLC-AV, TOLC-PSI, TOLC-SPS, TOLC-LP, CEnT-S
- "ALL" mode: monitor every exam type at once
- Format filter: monitor @HOME (online) or @UNI (in-person) exams
- Telegram alerts with configurable repeat count (1-50 messages per alert)
- Multi-user Telegram mode with per-user exam filtering
- Captures subscriber name, username, numeric ID, and join date
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
|-- config/
|   |-- __init__.py
|   |-- settings.py          # Config loader, validation, save
|-- scraper/
|   |-- __init__.py
|   |-- crawler.py           # Web scraper (single + ALL exams)
|-- notifications/
|   |-- __init__.py
|   |-- telegram_bot.py      # Telegram notifier + multi-user polling
|   |-- email_sender.py      # Email notifier
|-- utils/
    |-- __init__.py
    |-- menu.py               # Interactive CLI menu system
    |-- logger.py             # CLI logger
    |-- i18n.py               # English / Italian translations
    |-- scheduler.py          # Fixed + random interval scheduler
    |-- subscribers.py        # Subscriber persistence (JSON)
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
   CISIA CRAWLER v1.1.0
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
- Telegram settings (token, chat ID, message count, multi-user)
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

## Making the Bot Public (Multi-User)

If you want other people to subscribe to your bot:

### 1. Set up bot commands via BotFather

Send `/setcommands` to @BotFather, select your bot, then paste:

```
start - Subscribe to seat alerts
stop - Unsubscribe from alerts
exams - Choose which exams to follow
status - Show your current subscription
```

### 2. Set a bot description

Send `/setdescription` to @BotFather:

> Monitors CISIA test calendars and sends you a notification when
> seats become available. Send /start to subscribe.

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
```

### 4. Deploy and run

Run `python main.py`, select option 1 to start.

### 5. Share the bot

Give people the link: `https://t.me/YOUR_BOT_USERNAME`

### How it works for subscribers

1. User sends /start -> subscribed to all exams by default
2. User sends /exams -> bot shows numbered list of all exams
3. User replies with numbers (e.g. "1,5,11") -> gets alerts only
   for those exams
4. User sends "all" -> gets alerts for everything again
5. User sends /status -> shows current subscription info
6. User sends /stop -> unsubscribed

### What the bot captures about subscribers

When a user sends /start, the bot records:

- Telegram numeric user ID
- Username (if set)
- First name and last name
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
  cisia-crawler
```

---

## About

| Field   | Value                                        |
|---------|----------------------------------------------|
| Name    | CISIA CRAWLER                                |
| Version | 1.1.0                                        |
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

**How does random anti-clustering work?**
If you set 60-900, the range is 840s. 30% of that is 252s. So if
the bot waits 100s, the next wait will differ by at least 252s
(e.g. 352s or more). This prevents checking twice in quick
succession.

**WARNING! DO NOT SET THE INTERVAL CHECKING TIME BELOW 3 MINUTES, THIS MAY RESULT SERVER IP BLOCK!**
