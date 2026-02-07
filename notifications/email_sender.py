"""
Email notification sender.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class EmailNotifier:
    def __init__(
        self, smtp_host, smtp_port, smtp_user, smtp_password,
        from_email, to_email, use_tls, lang, logger
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.from_email = from_email
        self.to_email = to_email
        self.use_tls = use_tls
        self.lang = lang
        self.logger = logger

    def _send_email(self, subject, html_body):
        """Send an HTML email."""
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.from_email
            msg["To"] = self.to_email
            msg.attach(MIMEText(html_body, "html", "utf-8"))

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.from_email, self.to_email, msg.as_string())

            self.logger.info(self.lang.t("email_sent", email=self.to_email))
            return True
        except Exception as e:
            self.logger.error(self.lang.t("email_error", error=str(e)))
            return False

    def send_test(self):
        """Send a test email to verify connection."""
        subject = "CISIA CRAWLER - Test Email"
        body = """
        <html><body style="font-family:Arial,sans-serif;text-align:center;padding:40px;">
            <h2>CISIA CRAWLER</h2>
            <p>{}</p>
            <p style="color:#666;font-size:12px;">v1.1.0 - Author: Kasra Falahati</p>
        </body></html>
        """.format(self.lang.t("test_message"))
        return self._send_email(subject, body)

    def send_availability_alert(self, results_by_exam):
        """Send an email alert with all available seats."""
        all_seats = []
        for exam_key, seats in results_by_exam.items():
            all_seats.extend(seats)

        if not all_seats:
            return False

        subject = "CISIA CRAWLER - {}".format(self.lang.t("alert_title"))

        rows_html = ""
        for seat in all_seats:
            rows_html += (
                "<tr>"
                "<td style='padding:8px;border:1px solid #ddd;'>{exam}</td>"
                "<td style='padding:8px;border:1px solid #ddd;'>{fmt}</td>"
                "<td style='padding:8px;border:1px solid #ddd;'>{uni}</td>"
                "<td style='padding:8px;border:1px solid #ddd;'>{city}</td>"
                "<td style='padding:8px;border:1px solid #ddd;'>{region}</td>"
                "<td style='padding:8px;border:1px solid #ddd;'>{seats}</td>"
                "<td style='padding:8px;border:1px solid #ddd;'>{date}</td>"
                "<td style='padding:8px;border:1px solid #ddd;'>{deadline}</td>"
                "</tr>"
            ).format(
                exam=seat.get("exam", ""),
                fmt=seat["format"],
                uni=seat["university"],
                city=seat["city"],
                region=seat["region"],
                seats=seat["seats"],
                date=seat["date"],
                deadline=seat["deadline"],
            )

        html_body = """
        <html>
        <body style="font-family:Arial,sans-serif;max-width:900px;margin:0 auto;">
            <div style="background:#004d8a;color:white;padding:20px;text-align:center;">
                <h1>CISIA CRAWLER</h1>
                <h2>{title}</h2>
            </div>
            <div style="padding:20px;">
                <table style="width:100%;border-collapse:collapse;margin:20px 0;">
                    <thead>
                        <tr style="background:#f4f4f4;">
                            <th style="padding:8px;border:1px solid #ddd;">{lbl_exam}</th>
                            <th style="padding:8px;border:1px solid #ddd;">{lbl_fmt}</th>
                            <th style="padding:8px;border:1px solid #ddd;">{lbl_uni}</th>
                            <th style="padding:8px;border:1px solid #ddd;">{lbl_city}</th>
                            <th style="padding:8px;border:1px solid #ddd;">{lbl_region}</th>
                            <th style="padding:8px;border:1px solid #ddd;">{lbl_seats}</th>
                            <th style="padding:8px;border:1px solid #ddd;">{lbl_date}</th>
                            <th style="padding:8px;border:1px solid #ddd;">{lbl_deadline}</th>
                        </tr>
                    </thead>
                    <tbody>{rows}</tbody>
                </table>
                <p style="text-align:center;">
                    <a href="https://testcisia.it/studenti_tolc/login_sso.php"
                       style="background:#004d8a;color:white;padding:12px 24px;
                              text-decoration:none;border-radius:5px;display:inline-block;">
                        {book}
                    </a>
                </p>
            </div>
            <div style="background:#f4f4f4;padding:10px;text-align:center;font-size:12px;color:#666;">
                CISIA CRAWLER v1.1.0 - Author: Kasra Falahati
            </div>
        </body>
        </html>
        """.format(
            title=self.lang.t("alert_title"),
            lbl_exam=self.lang.t("exam"),
            lbl_fmt=self.lang.t("format"),
            lbl_uni=self.lang.t("university"),
            lbl_city=self.lang.t("city"),
            lbl_region=self.lang.t("region"),
            lbl_seats=self.lang.t("seats"),
            lbl_date=self.lang.t("date"),
            lbl_deadline=self.lang.t("deadline"),
            rows=rows_html,
            book=self.lang.t("book_now"),
        )

        return self._send_email(subject, html_body)
