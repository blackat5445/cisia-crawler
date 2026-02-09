"""
GitHub star verification module.
Checks if a GitHub user has starred the repository.
Caches the stargazers list to avoid hitting API rate limits.
"""

import requests
import threading
import time

GITHUB_REPO_OWNER = "blackat5445"
GITHUB_REPO_NAME = "cisia-crawler"
GITHUB_REPO_URL = "https://github.com/{}/{}".format(GITHUB_REPO_OWNER, GITHUB_REPO_NAME)

# Cache duration in seconds (5 minutes)
CACHE_TTL = 300


class GitHubStarChecker:
    """Check if a GitHub user has starred the repository."""

    API_URL = "https://api.github.com/repos/{owner}/{repo}/stargazers"

    def __init__(self, github_token=None):
        self._lock = threading.Lock()
        self._stargazers = set()
        self._last_fetch = 0
        self._github_token = github_token

    def _fetch_stargazers(self):
        """Fetch all stargazers from GitHub API (paginated)."""
        now = time.time()
        if now - self._last_fetch < CACHE_TTL and self._stargazers:
            return

        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self._github_token:
            headers["Authorization"] = "Bearer {}".format(self._github_token)

        all_stargazers = set()
        page = 1
        per_page = 100

        while True:
            url = self.API_URL.format(owner=GITHUB_REPO_OWNER, repo=GITHUB_REPO_NAME)
            try:
                resp = requests.get(
                    url,
                    headers=headers,
                    params={"per_page": per_page, "page": page},
                    timeout=15,
                )
                if resp.status_code != 200:
                    break

                data = resp.json()
                if not data:
                    break

                for user in data:
                    login = user.get("login", "").lower()
                    if login:
                        all_stargazers.add(login)

                if len(data) < per_page:
                    break
                page += 1

            except Exception:
                break

        with self._lock:
            self._stargazers = all_stargazers
            self._last_fetch = now

    def has_starred(self, github_username):
        """Check if a GitHub username has starred the repo."""
        if not github_username:
            return False

        self._fetch_stargazers()

        with self._lock:
            return github_username.lower().strip().lstrip("@") in self._stargazers

    def get_stargazer_count(self):
        """Return the number of cached stargazers."""
        self._fetch_stargazers()
        with self._lock:
            return len(self._stargazers)
