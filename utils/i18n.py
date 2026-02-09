"""
Internationalization (i18n) module.
Supports English and Italian translations.
"""

TRANSLATIONS = {
    "en": {
        # General
        "starting": "Starting CISIA CRAWLER...",
        "exam_type": "Exam type: {exam}",
        "exam_type_all": "Exam type: ALL (monitoring every exam)",
        "format_type": "Format: {fmt}",
        "interval_fixed": "Check interval: every {minutes} minutes (fixed)",
        "interval_random": "Check interval: random between {lo}s and {hi}s",
        "language_set": "Language: {language}",
        "check_number": "=== Check #{n} ===",
        "fetching_url": "Fetching: {url}",
        "fetching_exam": "Checking exam: {exam}",
        "page_fetched": "Page fetched (HTTP {status})",
        "table_not_found": "Calendar table not found on page.",
        "tbody_not_found": "Table body not found.",
        "rows_found": "Found {count} rows in calendar",
        "seats_found": "FOUND {count} AVAILABLE SEAT(S)!",
        "no_seats": "No available seats found. Will check again...",
        "next_check_fixed": "Next check in {minutes} minutes...",
        "next_check_random": "Next check in {seconds} seconds...",
        "error_check": "Error during check: {error}",
        "msg_count": "Telegram message count per alert: {count}",
        "startup_delay": "Startup delay: waiting {seconds}s before starting scraping...",
        # Notifications
        "telegram_enabled": "Telegram notifications: ENABLED",
        "telegram_disabled": "Telegram notifications: DISABLED",
        "telegram_multiuser": "Telegram multi-user mode: ENABLED",
        "email_enabled": "Email notifications: ENABLED (to: {email})",
        "email_disabled": "Email notifications: DISABLED",
        "telegram_sent": "Telegram message sent",
        "telegram_error": "Telegram error: {error}",
        "telegram_rate_limited": "Telegram rate limit hit (HTTP 429). Sleeping {seconds}s...",
        "telegram_repeat": "Telegram message {current}/{total} sent",
        "telegram_subscriber_sent": "Notified subscriber {chat_id}",
        "telegram_subscriber_skip": "Subscriber {chat_id} not subscribed to {exam}, skipping",
        "email_sent": "Email sent to {email}",
        "email_error": "Email error: {error}",
        "test_message": "Connection test successful. CISIA CRAWLER is connected and ready.",
        "test_email_ok": "Test email sent successfully to {email}.",
        "test_email_fail": "Test email failed: {error}",
        # Table headers / labels
        "alert_title": "Available Seats Found!",
        "format": "Format",
        "university": "University",
        "city": "City",
        "region": "Region",
        "seats": "Seats",
        "date": "Date",
        "deadline": "Deadline",
        "exam": "Exam",
        "book_now": "Book Now!",
        "dates": "dates",
        "daily_no_spots": "\u2705 Bot is running: no available spots found for <b>{exam}</b> in the last 24 hours.",

        # ── v2: New bot commands ──

        "bot_welcome_v2": (
            "\U0001F680 <b>Welcome to CISIA CRAWLER!</b>\n\n"
            "To use this bot you must first <b>star</b> our GitHub repository:\n"
            "\U0001F517 https://github.com/blackat5445/cisia-crawler\n\n"
            "After starring, send:\n"
            "<code>/github your_github_username</code>\n\n"
            "Once verified you can:\n"
            "\u2022 /exam \u2013 Join an exam notification group\n"
            "\u2022 /status \u2013 Check your subscription\n"
            "\u2022 /interval \u2013 Set check interval (1-60 min)\n"
            "\u2022 /donate \u2013 Support the project\n"
            "\u2022 /help \u2013 Show all commands\n"
            "\u2022 /stop \u2013 Unsubscribe"
        ),

        "bot_stopped": "You have been unsubscribed. Send /start to re-subscribe.",
        "bot_not_subscribed": "You are not subscribed. Send /start to subscribe.",
        "bot_new_subscriber": "New subscriber: {name} (@{username}, ID: {user_id})",

        # GitHub verification
        "github_required": (
            "\U0001F512 You must verify your GitHub star first.\n\n"
            "1. Star the repo: https://github.com/blackat5445/cisia-crawler\n"
            "2. Send: <code>/github your_github_username</code>"
        ),
        "github_usage": "Usage: <code>/github your_github_username</code>",
        "github_checking": "\U0001F50D Checking if <b>{username}</b> has starred the repo...",
        "github_verified": (
            "\u2705 <b>Verified!</b> GitHub user <b>{username}</b> has starred the repo.\n\n"
            "You now have full access to the bot.\n"
            "Use /exam to join an exam notification group."
        ),
        "github_not_starred": (
            "\u274C GitHub user <b>{username}</b> has <b>not</b> starred the repository.\n\n"
            "Please star it first:\n"
            "\U0001F517 {repo}\n\n"
            "Then try again with:\n"
            "<code>/github {username}</code>"
        ),

        # Donation
        "donate_info": (
            "\U0001F4B0 <b>Support CISIA CRAWLER</b>\n\n"
            "Donate any amount (min $1) via <b>USDT (TRC20)</b>:\n\n"
            "<code>{address}</code>\n\n"
            "Donating makes you a <b>\u2B50 Premium</b> member!\n\n"
            "\u2022 Access to a <b>private Premium channel &amp; group</b>\n"
            "\u2022 <b>Faster check intervals</b> (30s \u2013 1 min)\n"
            "\u2022 <b>Early access</b> to new versions\n\n"
            "After sending, submit your transaction:\n"
            "<code>/donate your_transaction_id</code>"
        ),
        "donate_submitted": (
            "\u2705 <b>Thank you!</b>\n\n"
            "Your donation has been recorded.\n"
            "TX ID: <code>{tx_id}</code>\n\n"
            "The admin will verify your transaction.\n"
            "Once verified you will become <b>\u2B50 Premium</b> and receive "
            "an invite link to the Premium group."
        ),
        "donate_verified_user": (
            "\U0001F389 <b>Congratulations!</b>\n\n"
            "Your donation has been verified. You are now a <b>\u2B50 Premium</b> member!\n\n"
            "Benefits:\n"
            "\u2022 Private Premium channel &amp; group\n"
            "\u2022 Faster check intervals (30s \u2013 1 min)\n"
            "\u2022 Early access to new versions"
        ),
        "donate_rejected_user": (
            "\u274C Your donation claim could not be verified.\n\n"
            "If you believe this is a mistake, please contact the admin "
            "or submit a new transaction with /donate."
        ),
        "premium_invite_link": (
            "\U0001F517 <b>Premium Group Invite</b>\n\n"
            "{link}\n\n"
            "\u26A0\uFE0F This link expires in <b>1 minute</b> and can only be used once."
        ),

        # Exam selection & invite links
        "exam_select_prompt": (
            "\U0001F4DA <b>Select an exam</b>\n\n"
            "Send the number to get an invite link to the notification group.\n"
            "The link expires in <b>1 minute</b>."
        ),
        "invite_generating": "\u23F3 Generating invite link for <b>{exam}</b>...",
        "invite_link": (
            "\U0001F517 <b>{exam}</b> \u2013 Group Invite Link\n\n"
            "{link}\n\n"
            "\u26A0\uFE0F This link expires in <b>1 minute</b> and can only be used once."
        ),

        # Interval
        "interval_info": (
            "Set your preferred check interval:\n"
            "<code>/interval 5</code> (minutes, 1-60)\n\n"
            "This controls how often the bot checks for available seats."
        ),
        "interval_set": "\u2705 Check interval set to <b>{minutes}</b> minutes.",

        # Help
        "help_message": (
            "\U0001F4CB <b>CISIA CRAWLER \u2013 Commands</b>\n\n"
            "/start \u2013 Subscribe to the bot\n"
            "/github &lt;username&gt; \u2013 Verify your GitHub star\n"
            "/exam \u2013 Get invite link to an exam group\n"
            "/status \u2013 Show your subscription info\n"
            "/donate \u2013 Support the project &amp; become Premium\n"
            "/donate &lt;tx_id&gt; \u2013 Submit donation transaction\n"
            "/stop \u2013 Unsubscribe\n"
            "/help \u2013 Show this message"
        ),

        # Legacy (kept for compatibility)
        "bot_welcome": "Welcome! Send /start to begin.",
        "bot_choose_exams": "Select the exams you want to receive alerts for.",
        "bot_exams_updated": "Your exam preferences have been updated:\n{exams}",
        "bot_exams_invalid": "Invalid input.",
        "bot_status": "Your subscription:\nActive: {active}\nExams: {exams}",
        "bot_status_all": "all exams",
        "bot_status_none": "none (use /exams to choose)",
    },
    "it": {
        "starting": "Avvio di CISIA CRAWLER...",
        "exam_type": "Tipo di esame: {exam}",
        "exam_type_all": "Tipo di esame: TUTTI (monitoraggio di ogni esame)",
        "format_type": "Formato: {fmt}",
        "interval_fixed": "Intervallo controllo: ogni {minutes} minuti (fisso)",
        "interval_random": "Intervallo controllo: casuale tra {lo}s e {hi}s",
        "language_set": "Lingua: {language}",
        "check_number": "=== Controllo #{n} ===",
        "fetching_url": "Recupero: {url}",
        "fetching_exam": "Controllo esame: {exam}",
        "page_fetched": "Pagina recuperata (HTTP {status})",
        "table_not_found": "Tabella calendario non trovata.",
        "tbody_not_found": "Corpo tabella non trovato.",
        "rows_found": "Trovate {count} righe nel calendario",
        "seats_found": "TROVATI {count} POSTO/I DISPONIBILE/I!",
        "no_seats": "Nessun posto disponibile. Ricontrollo in corso...",
        "next_check_fixed": "Prossimo controllo tra {minutes} minuti...",
        "next_check_random": "Prossimo controllo tra {seconds} secondi...",
        "error_check": "Errore durante il controllo: {error}",
        "msg_count": "Messaggi Telegram per avviso: {count}",
        "startup_delay": "Ritardo avvio: attendo {seconds}s prima di iniziare lo scraping...",
        "telegram_enabled": "Notifiche Telegram: ATTIVE",
        "telegram_disabled": "Notifiche Telegram: DISATTIVATE",
        "telegram_multiuser": "Modalita multi-utente Telegram: ATTIVA",
        "email_enabled": "Notifiche email: ATTIVE (a: {email})",
        "email_disabled": "Notifiche email: DISATTIVATE",
        "telegram_sent": "Messaggio Telegram inviato",
        "telegram_error": "Errore Telegram: {error}",
        "telegram_rate_limited": "Limite Telegram raggiunto (HTTP 429). Attendo {seconds}s...",
        "telegram_repeat": "Messaggio Telegram {current}/{total} inviato",
        "telegram_subscriber_sent": "Notificato abbonato {chat_id}",
        "telegram_subscriber_skip": "Abbonato {chat_id} non iscritto a {exam}, salto",
        "email_sent": "Email inviata a {email}",
        "email_error": "Errore email: {error}",
        "test_message": "Test connessione riuscito. CISIA CRAWLER e' connesso e pronto.",
        "test_email_ok": "Email di test inviata con successo a {email}.",
        "test_email_fail": "Email di test fallita: {error}",
        "alert_title": "Posti Disponibili Trovati!",
        "format": "Formato",
        "university": "Universita",
        "city": "Citta",
        "region": "Regione",
        "seats": "Posti",
        "date": "Data",
        "deadline": "Scadenza",
        "exam": "Esame",
        "book_now": "Prenota Ora!",
        "dates": "date",
        "daily_no_spots": "\u2705 Il bot e' attivo: nessun posto disponibile trovato per <b>{exam}</b> nelle ultime 24 ore.",

        # ── v2: Nuovi comandi bot ──

        "bot_welcome_v2": (
            "\U0001F680 <b>Benvenuto in CISIA CRAWLER!</b>\n\n"
            "Per usare questo bot devi prima dare una <b>stella</b> al nostro repository GitHub:\n"
            "\U0001F517 https://github.com/blackat5445/cisia-crawler\n\n"
            "Dopo aver dato la stella, invia:\n"
            "<code>/github tuo_username_github</code>\n\n"
            "Una volta verificato puoi:\n"
            "\u2022 /exam \u2013 Entra in un gruppo notifiche esame\n"
            "\u2022 /status \u2013 Controlla la tua iscrizione\n"
            "\u2022 /interval \u2013 Imposta intervallo controllo (1-60 min)\n"
            "\u2022 /donate \u2013 Supporta il progetto\n"
            "\u2022 /help \u2013 Mostra tutti i comandi\n"
            "\u2022 /stop \u2013 Disiscriviti"
        ),

        "bot_stopped": "Sei stato disiscritto. Invia /start per re-iscriverti.",
        "bot_not_subscribed": "Non sei iscritto. Invia /start per iscriverti.",
        "bot_new_subscriber": "Nuovo iscritto: {name} (@{username}, ID: {user_id})",

        "github_required": (
            "\U0001F512 Devi prima verificare la tua stella su GitHub.\n\n"
            "1. Dai la stella: https://github.com/blackat5445/cisia-crawler\n"
            "2. Invia: <code>/github tuo_username_github</code>"
        ),
        "github_usage": "Uso: <code>/github tuo_username_github</code>",
        "github_checking": "\U0001F50D Verifico se <b>{username}</b> ha dato la stella...",
        "github_verified": (
            "\u2705 <b>Verificato!</b> L'utente GitHub <b>{username}</b> ha dato la stella.\n\n"
            "Ora hai accesso completo al bot.\n"
            "Usa /exam per entrare in un gruppo notifiche esame."
        ),
        "github_not_starred": (
            "\u274C L'utente GitHub <b>{username}</b> <b>non</b> ha dato la stella al repository.\n\n"
            "Per favore dai la stella prima:\n"
            "\U0001F517 {repo}\n\n"
            "Poi riprova con:\n"
            "<code>/github {username}</code>"
        ),

        "donate_info": (
            "\U0001F4B0 <b>Supporta CISIA CRAWLER</b>\n\n"
            "Dona qualsiasi importo (min $1) tramite <b>USDT (TRC20)</b>:\n\n"
            "<code>{address}</code>\n\n"
            "Donando diventi un membro <b>\u2B50 Premium</b>!\n\n"
            "\u2022 Accesso a <b>canale e gruppo Premium privato</b>\n"
            "\u2022 <b>Intervalli di controllo piu' rapidi</b> (30s \u2013 1 min)\n"
            "\u2022 <b>Accesso anticipato</b> alle nuove versioni\n\n"
            "Dopo aver inviato, registra la tua transazione:\n"
            "<code>/donate tuo_id_transazione</code>"
        ),
        "donate_submitted": (
            "\u2705 <b>Grazie!</b>\n\n"
            "La tua donazione e' stata registrata.\n"
            "TX ID: <code>{tx_id}</code>\n\n"
            "L'admin verifichera' la tua transazione.\n"
            "Una volta verificata diventerai <b>\u2B50 Premium</b> e riceverai "
            "un link d'invito al gruppo Premium."
        ),
        "donate_verified_user": (
            "\U0001F389 <b>Congratulazioni!</b>\n\n"
            "La tua donazione e' stata verificata. Sei ora un membro <b>\u2B50 Premium</b>!\n\n"
            "Vantaggi:\n"
            "\u2022 Canale e gruppo Premium privato\n"
            "\u2022 Intervalli di controllo piu' rapidi (30s \u2013 1 min)\n"
            "\u2022 Accesso anticipato alle nuove versioni"
        ),
        "donate_rejected_user": (
            "\u274C La tua donazione non ha potuto essere verificata.\n\n"
            "Se ritieni sia un errore, contatta l'admin "
            "o invia una nuova transazione con /donate."
        ),
        "premium_invite_link": (
            "\U0001F517 <b>Invito Gruppo Premium</b>\n\n"
            "{link}\n\n"
            "\u26A0\uFE0F Questo link scade in <b>1 minuto</b> e puo' essere usato una sola volta."
        ),

        "exam_select_prompt": (
            "\U0001F4DA <b>Seleziona un esame</b>\n\n"
            "Invia il numero per ottenere un link d'invito al gruppo notifiche.\n"
            "Il link scade in <b>1 minuto</b>."
        ),
        "invite_generating": "\u23F3 Generazione link d'invito per <b>{exam}</b>...",
        "invite_link": (
            "\U0001F517 <b>{exam}</b> \u2013 Link Invito Gruppo\n\n"
            "{link}\n\n"
            "\u26A0\uFE0F Questo link scade in <b>1 minuto</b> e puo' essere usato una sola volta."
        ),

        "interval_info": (
            "Imposta il tuo intervallo di controllo preferito:\n"
            "<code>/interval 5</code> (minuti, 1-60)\n\n"
            "Questo controlla quanto spesso il bot cerca posti disponibili."
        ),
        "interval_set": "\u2705 Intervallo di controllo impostato a <b>{minutes}</b> minuti.",

        "help_message": (
            "\U0001F4CB <b>CISIA CRAWLER \u2013 Comandi</b>\n\n"
            "/start \u2013 Iscriviti al bot\n"
            "/github &lt;username&gt; \u2013 Verifica la tua stella GitHub\n"
            "/exam \u2013 Ottieni link invito a un gruppo esame\n"
            "/status \u2013 Mostra info iscrizione\n"
            "/donate \u2013 Supporta il progetto e diventa Premium\n"
            "/donate &lt;tx_id&gt; \u2013 Invia transazione donazione\n"
            "/stop \u2013 Disiscriviti\n"
            "/help \u2013 Mostra questo messaggio"
        ),

        "bot_welcome": "Benvenuto! Invia /start per iniziare.",
        "bot_choose_exams": "Seleziona gli esami per cui vuoi ricevere avvisi.",
        "bot_exams_updated": "Le tue preferenze esami sono state aggiornate:\n{exams}",
        "bot_exams_invalid": "Input non valido.",
        "bot_status": "La tua iscrizione:\nAttivo: {active}\nEsami: {exams}",
        "bot_status_all": "tutti gli esami",
        "bot_status_none": "nessuno (usa /exams per scegliere)",
    },
}


class I18n:
    def __init__(self, language="en"):
        self.language = language
        self.strings = TRANSLATIONS.get(language, TRANSLATIONS["en"])

    def t(self, key, **kwargs):
        """Get translated string with optional formatting."""
        text = self.strings.get(key, key)
        if kwargs:
            try:
                return text.format(**kwargs)
            except (KeyError, IndexError):
                return text
        return text
