"""
CISIA website scraper.
Fetches the calendar page and parses available seats.
Supports single exam or ALL exams mode.
"""

import requests
from bs4 import BeautifulSoup

from config.settings import EXAM_TYPES

BASE_URL = "https://testcisia.it/calendario.php"


class CisiaCrawler:
    def __init__(self, exam_type, format_type, language, logger, lang):
        self.exam_type = exam_type
        self.format_type = format_type
        self.language = language
        self.logger = logger
        self.lang = lang

    def _build_url(self, exam_key):
        """Build the CISIA calendar URL for a given exam."""
        info = EXAM_TYPES[exam_key]
        url = "{}?tolc={}".format(BASE_URL, info["param"])
        if info["prefix"] == "CENT":
            url += "&lingua={}".format(self.language)
        if self.language == "inglese":
            url += "&l=gb"
        else:
            url += "&l=it"
        return url

    def _get_target_format(self, exam_key):
        """Return the target format string, e.g. CENT@HOME or TOLC@UNI."""
        prefix = EXAM_TYPES[exam_key]["prefix"]
        return "{}{}".format(prefix, self.format_type)

    def _fetch_page(self, url):
        """Fetch page HTML."""
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        self.logger.info(self.lang.t("page_fetched", status=response.status_code))
        return response.text

    def _parse_table(self, html, target_format, exam_key):
        """Parse the calendar table and return available seats."""
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table", {"id": "calendario"})

        if not table:
            self.logger.error(self.lang.t("table_not_found"))
            return []

        tbody = table.find("tbody")
        if not tbody:
            self.logger.error(self.lang.t("tbody_not_found"))
            return []

        rows = tbody.find_all("tr")
        self.logger.info(self.lang.t("rows_found", count=len(rows)))

        available = []

        for row in rows:
            cells = row.find_all("td")
            if len(cells) < 8:
                continue

            format_text = cells[0].get_text(strip=True)
            university = cells[1].get_text(strip=True)
            region = cells[2].get_text(strip=True)
            city = cells[3].get_text(strip=True)
            deadline = cells[4].get_text(strip=True)
            seats_text = cells[5].get_text(strip=True)
            state_cell = cells[6]
            date = cells[7].get_text(strip=True)

            if format_text != target_format:
                continue

            has_available_span = state_cell.find(
                "span", style=lambda s: s and "LimeGreen" in s
            )
            is_number = seats_text.replace("---", "").strip() != "" and seats_text != "---"

            if has_available_span or is_number:
                available.append({
                    "exam": exam_key,
                    "format": format_text,
                    "university": university,
                    "region": region,
                    "city": city,
                    "deadline": deadline,
                    "seats": seats_text,
                    "date": date,
                })

        return available

    def check_availability(self):
        """
        Check seat availability.
        Returns dict: {exam_key: [available_seats]}
        """
        if self.exam_type == "ALL":
            return self._check_all_exams()
        else:
            return self._check_single_exam(self.exam_type)

    def _check_single_exam(self, exam_key):
        """Check a single exam type."""
        url = self._build_url(exam_key)
        target = self._get_target_format(exam_key)
        self.logger.info(self.lang.t("fetching_exam", exam=exam_key))
        self.logger.info(self.lang.t("fetching_url", url=url))
        html = self._fetch_page(url)
        seats = self._parse_table(html, target, exam_key)
        return {exam_key: seats}

    def _check_all_exams(self):
        """Check every exam type."""
        all_results = {}
        for exam_key in EXAM_TYPES:
            try:
                result = self._check_single_exam(exam_key)
                all_results.update(result)
            except Exception as e:
                self.logger.error(
                    self.lang.t("error_check", error="{}: {}".format(exam_key, str(e)))
                )
                all_results[exam_key] = []
        return all_results
