"""
CLI Logger with timestamps and colored output.
"""

from datetime import datetime


class Colors:
    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    DIM = "\033[2m"


class Logger:
    def __init__(self, lang=None):
        self.lang = lang

    def _timestamp(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def info(self, message):
        print(
            "{}[{}]{} {}[INFO]{} {}".format(
                Colors.CYAN, self._timestamp(), Colors.RESET,
                Colors.BLUE, Colors.RESET, message
            )
        )

    def success(self, message):
        print(
            "{}[{}]{} {}[OK]{} {}".format(
                Colors.CYAN, self._timestamp(), Colors.RESET,
                Colors.GREEN, Colors.RESET, message
            )
        )

    def warn(self, message):
        print(
            "{}[{}]{} {}[WARN]{} {}".format(
                Colors.CYAN, self._timestamp(), Colors.RESET,
                Colors.YELLOW, Colors.RESET, message
            )
        )

    def error(self, message):
        print(
            "{}[{}]{} {}[ERROR]{} {}".format(
                Colors.CYAN, self._timestamp(), Colors.RESET,
                Colors.RED, Colors.RESET, message
            )
        )

    def debug(self, message):
        print(
            "{}[{}]{} {}[DEBUG]{} {}".format(
                Colors.CYAN, self._timestamp(), Colors.RESET,
                Colors.DIM, Colors.RESET, message
            )
        )
