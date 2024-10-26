import csv
import logging
from os import path


def setup_console_logger(level: int) -> logging.Logger:
    # Create a custom logger
    logger = logging.getLogger(__name__)
    logger.setLevel(level)  # Set the lowest level you want to capture

    # Create console handler
    console_handler = logging.StreamHandler()  # For console output only
    console_handler.setLevel(logging.DEBUG)  # Console will capture all levels from DEBUG up

    # Create formatter and add it to console handler
    formatter = logging.Formatter("%(asctime)s | %(name)s | %(levelname)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    console_handler.setFormatter(formatter)

    # Add console handler to the logger
    logger.addHandler(console_handler)

    return logger


def read_csv(file_path: str) -> list[list[str]]:
    data = []
    if path.exists(file_path):
        with open(file_path, "r", newline="") as file:
            reader = csv.reader(file)
            data = [row for row in reader]
    return data


def format_watch_reference(reference: str) -> str:
    return reference.strip().replace(" ", "", 1).replace(" ", "%20")


def any_word_in_strings(words: list, strings: list) -> bool:
    return any(word in string.text.lower() for string in strings for word in words)
