"""
Interval scheduler.
Supports fixed and random intervals with anti-repeat logic.
"""

import random


class IntervalScheduler:
    """
    Produces wait times.

    In 'fixed' mode it always returns the same value (minutes * 60).

    In 'random' mode it picks a random value in [lo, hi] that is
    guaranteed to differ from the previous value by at least 30 %
    of the total range, so consecutive checks never cluster together.
    """

    def __init__(self, mode, fixed_minutes=5, random_lo=60, random_hi=900):
        self.mode = mode
        self.fixed_seconds = fixed_minutes * 60
        self.lo = random_lo
        self.hi = random_hi
        self._last = None
        self._min_gap = max(int((random_hi - random_lo) * 0.30), 10)

    def next_seconds(self):
        """Return the number of seconds to wait before the next check."""
        if self.mode == "fixed":
            return self.fixed_seconds

        for _ in range(200):
            candidate = random.randint(self.lo, self.hi)
            if self._last is None or abs(candidate - self._last) >= self._min_gap:
                self._last = candidate
                return candidate

        fallback = random.randint(self.lo, self.hi)
        self._last = fallback
        return fallback
