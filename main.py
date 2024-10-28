import logging
from typing import Optional, List

import requests
from bs4 import BeautifulSoup

from utils import setup_console_logger, format_watch_reference, read_csv, any_word_in_strings

logger = setup_console_logger(logging.DEBUG)
keyword_list = ["swatch", "watch", "reloj"]


def get_ebay_results(session, watch_reference: str, check_sold: bool) -> Optional[List[float]]:
    """Fetches eBay search results and returns list of prices."""
    endpoint = f"https://www.ebay.es/sch/i.html?_nkw={watch_reference}&_in_kw=3&_sacat=281"
    if check_sold:
        endpoint += "&LH_Sold=1&LH_Complete=1"
    logger.debug(f"{watch_reference} | URL: {endpoint}")

    response = session.get(endpoint, allow_redirects=True)
    if response.status_code != 200:
        logger.error(f"{watch_reference} | Request failed, status code: {response.status_code}")
        return None

    return parse_ebay_results(response.text, watch_reference)


def parse_ebay_results(html: str, watch_reference: str) -> List[float]:
    """Parses the HTML from eBay and extracts prices if available."""
    soup = BeautifulSoup(html, "html.parser")
    watch_posts = soup.find_all("div", {"class": "s-item__info clearfix"})
    if not watch_posts:
        logger.error(f"{watch_reference} | No posts found")
        return []

    logger.debug(f"{watch_reference} | {len(watch_posts)} posts found")
    price_list = [parse_price(post, watch_reference) for post in watch_posts]
    return [price for price in price_list if price is not None]


def parse_price(post, watch_reference: str) -> Optional[float]:
    """Extracts and cleans price information from a post."""
    post_soup = BeautifulSoup(str(post), "html.parser")
    heading_list = post_soup.find_all("span", {"role": "heading"})
    if not any_word_in_strings(keyword_list, heading_list):
        logger.debug(f"{watch_reference} | The item doesn't seem to be a watch")
        return None

    price_span = post_soup.find("span", {"class": "ITALIC"})
    if price_span and price_span.text:
        try:
            clean_price = float(price_span.text.split()[0].replace(".", "").replace(",", "."))
            return clean_price
        except ValueError:
            logger.warning(f"{watch_reference} | Price conversion failed")
    return None


def calculate_average(prices: List[float]) -> Optional[float]:
    """Calculates the average price from a list of prices."""
    if prices:
        return round(sum(prices) / len(prices), 2)
    logger.debug("Empty price list encountered in average calculation")
    return None


def load_data(file_path: str) -> List:
    """Loads and returns watch data from the CSV file."""
    data = read_csv(file_path)
    if data is None:
        logger.error("Failed to load data. Exiting program.")
        exit(1)  # Exit if data loading fails
    return data


def process_watch(session, watch_data) -> Optional[float]:
    """Processes each watch reference and calculates the average price."""
    year, reference, name, quantity = watch_data
    formatted_reference = format_watch_reference(reference)

    not_sold_results = get_ebay_results(session, formatted_reference, check_sold=False)
    sold_results = get_ebay_results(session, formatted_reference, check_sold=True)

    if not not_sold_results and not sold_results:
        logger.error(f"{formatted_reference} | Watch not found, skipping...")
        return None

    avg_not_sold = calculate_average(not_sold_results)
    avg_sold = calculate_average(sold_results)

    if avg_not_sold and avg_sold:
        total_avg = round((avg_not_sold + avg_sold) / 2, 2)
    else:
        total_avg = avg_sold or avg_not_sold

    if total_avg:
        logger.info(f"{formatted_reference} | Average price: {total_avg} | Quantity: {quantity}")
    return total_avg * int(quantity) if total_avg else None


def calculate_collection_value(session, data: List) -> float:
    """Calculates the total value of the watch collection."""
    total_value = 0
    found_watches = 0

    for watch_data in data:
        watch_value = process_watch(session, watch_data)
        if watch_value:
            total_value += watch_value
            found_watches += 1

    logger.info(f"Total collection value for {found_watches}/{len(data)} watches: {round(total_value, 2)}")
    return total_value


def run() -> None:
    """Main function to execute the workflow."""
    session = requests.Session()
    data = load_data("watches.csv")
    calculate_collection_value(session, data)


if __name__ == "__main__":
    run()
