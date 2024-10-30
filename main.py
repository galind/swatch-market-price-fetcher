import logging
import time
from typing import Optional, List, Dict, Tuple

import requests
from bs4 import BeautifulSoup

from utils import setup_console_logger, format_watch_reference, read_csv, any_word_in_strings, save_to_json

logger = setup_console_logger(logging.DEBUG)
keyword_list = ["swatch", "watch", "reloj"]


def get_ebay_results(session, watch_reference: str, check_active: bool) -> Tuple[Optional[List[float]], int]:
    """Fetches eBay search results and returns a list of prices and the count of posts found."""
    logger.debug(f"Fetching eBay results (active={check_active})", extra={"reference": watch_reference})
    endpoint = f"https://www.ebay.es/sch/i.html?_nkw={format_watch_reference(watch_reference)}&_in_kw=3&_sacat=281"
    if check_active:
        endpoint += "&LH_Sold=1&LH_Complete=1"
    logger.debug(f"URL: {endpoint}", extra={"reference": watch_reference})

    response = session.get(endpoint, allow_redirects=True)
    if response.status_code != 200:
        logger.error(f"Request failed with status code {response.status_code}", extra={"reference": watch_reference})
        return None, 0

    prices, post_count = parse_ebay_results(response.text, watch_reference)
    logger.info(
        f"Found {post_count} {'active' if check_active else 'sold'} posts", extra={"reference": watch_reference}
    )
    return prices, post_count


def parse_ebay_results(html: str, watch_reference: str) -> Tuple[List[float], int]:
    """Parses the HTML from eBay, extracts prices if available, and returns prices with post count."""
    soup = BeautifulSoup(html, "html.parser")
    watch_posts = soup.find_all("div", {"class": "s-item__info clearfix"})
    post_count = len(watch_posts)

    if post_count == 0:
        logger.warning("No posts found", extra={"reference": watch_reference})
        return [], 0

    logger.debug(f"Parsing {post_count} posts for prices", extra={"reference": watch_reference})
    price_list = [parse_price(post, watch_reference) for post in watch_posts]
    return [price for price in price_list if price is not None], post_count


def parse_price(post, watch_reference: str) -> Optional[float]:
    """Extracts and cleans price information from a post."""
    post_soup = BeautifulSoup(str(post), "html.parser")
    heading_list = post_soup.find_all("span", {"role": "heading"})
    if not any_word_in_strings(keyword_list, heading_list):
        logger.debug("Item skipped: does not match keywords", extra={"reference": watch_reference})
        return None

    price_span = post_soup.find("span", {"class": "ITALIC"})
    if price_span and price_span.text:
        try:
            clean_price = float(price_span.text.split()[0].replace(".", "").replace(",", "."))
            logger.debug(f"Extracted price: {clean_price}", extra={"reference": watch_reference})
            return round(clean_price, 2)
        except ValueError:
            logger.warning(f"Price conversion failed for text: {price_span.text}", extra={"reference": watch_reference})
    return None


def calculate_average(prices: List[float], reference: str) -> Optional[float]:
    """Calculates the average price from a list of prices, rounded to 2 decimal places."""
    if prices:
        average = round(sum(prices) / len(prices), 2)
        logger.debug(f"Calculated average price: {average}", extra={"reference": reference})
        return average
    logger.debug("Empty price list encountered in average calculation", extra={"reference": reference})
    return None


def load_data(file_path: str) -> List:
    """Loads and returns watch data from the CSV file."""
    logger.info(f"Loading data from {file_path}", extra={"reference": "global"})
    data = read_csv(file_path)
    if data is None:
        logger.error("Failed to load data. Exiting program.", extra={"reference": "global"})
        exit(1)
    logger.info(f"Loaded {len(data)} items from {file_path}", extra={"reference": "global"})
    return data


def process_watch(session, watch_data) -> Dict:
    """Processes each watch reference, calculates prices, and returns structured data."""
    year, reference, name, quantity = watch_data

    logger.info(f"Processing watch {reference}", extra={"reference": reference})
    active_results, active_posts = get_ebay_results(session, reference, check_active=True)
    sold_results, sold_posts = get_ebay_results(session, reference, check_active=False)

    avg_active = calculate_average(active_results, reference) if active_results else None
    avg_sold = calculate_average(sold_results, reference) if sold_results else None

    if avg_active and avg_sold:
        total_avg = round((avg_active + avg_sold) / 2, 2)
    else:
        total_avg = avg_sold or avg_active

    watch_info = {
        "year": year,
        "reference": reference,
        "name": name,
        "quantity": quantity,
        "avg_active": avg_active,
        "avg_sold": avg_sold,
        "total_avg": total_avg,
        "total_value": round(total_avg * int(quantity), 2) if total_avg else None,
        "active_posts_found": active_posts,
        "sold_posts_found": sold_posts,
    }

    logger.info(
        f"Summary: Active Avg: {avg_active}, Sold Avg: {avg_sold}, Total Avg: {total_avg}, Quantity: {quantity}",
        extra={"reference": reference},
    )

    return watch_info


def calculate_collection_value(session, data: List) -> List[Dict]:
    """Calculates the total collection value and returns all processed watch data for JSON storage."""
    results = []
    start_time = time.time()

    for watch_data in data:
        watch_info = process_watch(session, watch_data)
        results.append(watch_info)

    elapsed_time = time.time() - start_time
    logger.info(f"Processed {len(data)} watches in {elapsed_time:.2f} seconds", extra={"reference": "global"})
    return results


def get_watch_data() -> None:
    """
    Fetches watch data from eBay, calculates prices, and saves the results to a JSON file.
    """
    session = requests.Session()
    data = load_data("watches.csv")
    processed_data = calculate_collection_value(session, data)
    save_to_json(processed_data, "results.json")
    logger.info("Data processing complete. Results saved to results.json")


if __name__ == "__main__":
    print("1. Get collection data\n2. Display existent data\n")
    try:
        selected_option = int(input("What do you want to do? "))
        match selected_option:
            case 1:
                get_watch_data()
            case 2:
                # Add any specific functionality if needed
                pass
            case _:
                print("Invalid option")
    except ValueError:
        print("Please enter a valid number.")
