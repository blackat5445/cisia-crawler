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
        # Telegram bot commands
        "bot_welcome": (
            "Welcome to CISIA CRAWLER!\n\n"
            "You are now subscribed.\n"
            "You will NOT receive any alerts until you choose your exams.\n\n"
            "Use /exams to select which exams you want to follow.\n\n"
            "Commands:\n"
            "/exams - Choose which exams to follow\n"
            "/status - Show your current subscription\n"
            "/stop - Unsubscribe from alerts"
        ),
        "bot_stopped": "You have been unsubscribed. Send /start to re-subscribe.",
        "bot_choose_exams": "Select the exams you want to receive alerts for. Send the numbers separated by commas (e.g. 1,3,5) or send 'all' for everything:",
        "bot_exams_updated": "Your exam preferences have been updated:\n{exams}",
        "bot_exams_invalid": "Invalid input. Send numbers separated by commas (e.g. 1,3,5) or 'all'.",
        "bot_status": "Your subscription:\nActive: {active}\nExams: {exams}",
        "bot_status_all": "all exams",
        "bot_status_none": "none (use /exams to choose)",
        "bot_not_subscribed": "You are not subscribed. Send /start to subscribe.",
        "bot_new_subscriber": "New subscriber: {name} (@{username}, ID: {user_id})",
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
        "bot_welcome": (
            "Benvenuto in CISIA CRAWLER!\n\n"
            "Sei ora iscritto.\n"
            "NON riceverai alcun avviso finche non scegli i tuoi esami.\n\n"
            "Usa /exams per selezionare quali esami vuoi seguire.\n\n"
            "Comandi:\n"
            "/exams - Scegli quali esami seguire\n"
            "/status - Mostra la tua iscrizione\n"
            "/stop - Disiscriviti dagli avvisi"
        ),
        "bot_stopped": "Sei stato disiscritto. Invia /start per re-iscriverti.",
        "bot_choose_exams": "Seleziona gli esami per cui vuoi ricevere avvisi. Invia i numeri separati da virgola (es. 1,3,5) o invia 'all' per tutti:",
        "bot_exams_updated": "Le tue preferenze esami sono state aggiornate:\n{exams}",
        "bot_exams_invalid": "Input non valido. Invia numeri separati da virgola (es. 1,3,5) o 'all'.",
        "bot_status": "La tua iscrizione:\nAttivo: {active}\nEsami: {exams}",
        "bot_status_all": "tutti gli esami",
        "bot_status_none": "nessuno (usa /exams per scegliere)",
        "bot_not_subscribed": "Non sei iscritto. Invia /start per iscriverti.",
        "bot_new_subscriber": "Nuovo iscritto: {name} (@{username}, ID: {user_id})",
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
