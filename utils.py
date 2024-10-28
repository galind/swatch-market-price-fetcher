import csv
import logging
from os import path
from typing import List, Optional


def setup_console_logger(level: int = logging.INFO) -> logging.Logger:
    """Sets up and returns a logger with console output only."""
    logger = logging.getLogger("watch_reference_logger")
    logger.setLevel(level)

    # Avoid adding handlers if they already exist (for cases of repeated imports)
    if not logger.handlers:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        formatter = logging.Formatter(
            "%(asctime)s | %(name)s | %(levelname)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger


def read_csv(file_path: str, header: bool = False) -> Optional[List[List[str]]]:
    """Reads a CSV file and returns its content as a list of lists."""
    data = []
    if not path.exists(file_path):
        logging.error(f"File not found: {file_path}")
        return None

    try:
        with open(file_path, "r", newline="") as file:
            reader = csv.reader(file)
            if header:
                next(reader, None)  # Skip the header row if it exists
            data = [row for row in reader]
    except Exception as e:
        logging.error(f"Failed to read CSV file at {file_path}: {e}")
        return None

    return data


def format_watch_reference(reference: str) -> str:
    """Formats the watch reference by stripping leading whitespace and encoding spaces."""
    return reference.strip().replace(" ", "", 1).replace(" ", "%20")


def any_word_in_strings(words: List[str], strings: List) -> bool:
    """Checks if any of the words appear in any of the given strings."""
    return any(word in string.text.lower() for string in strings for word in words)
