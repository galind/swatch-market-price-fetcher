import logging
from typing import Optional

import requests
from bs4 import BeautifulSoup

from utils import setup_console_logger, format_watch_reference, read_csv, any_word_in_strings

logger = setup_console_logger(logging.INFO)


def search_in_ebay(watch_reference: str, check_sold: bool) -> Optional[list]:
    session = requests.Session()
    advanced_search_endpoint = f"https://www.ebay.es/sch/i.html?_nkw={watch_reference}&_in_kw=3&_sacat=281"
    if check_sold:
        advanced_search_endpoint += "&LH_Sold=1&LH_Complete=1"
    logger.debug(f"{watch_reference} | URL: {advanced_search_endpoint}")

    response = session.get(advanced_search_endpoint, allow_redirects=True)
    if response.status_code != 200:
        logger.error(f"{watch_reference} | Request failed, status code: {response.status_code}")
        return

    soup = BeautifulSoup(response.text, "html.parser")
    watch_posts = soup.find_all("div", {"class": "s-item__info clearfix"})
    if len(watch_posts) == 0:
        logger.error(f"{watch_reference} | No posts found")
        return

    logger.debug(f"{watch_reference} | {len(watch_posts)} posts found")

    price_list = []
    for post in watch_posts:
        post_soup = BeautifulSoup(str(post), "html.parser")

        heading_list = post_soup.find_all("span", {"role": "heading"})
        if not any_word_in_strings(["swatch", "reloj watch", "reloj reloj"], heading_list):
            logger.debug(f"{watch_reference} | The item doesn't seem to be a watch")
            continue
        italic_list = post_soup.find_all("span", {"class": "ITALIC"})
        if len(italic_list) == 0:
            continue

        clean_price = float(italic_list[0].text.split()[0].replace(".", "").replace(",", "."))
        price_list.append(clean_price)

    logger.debug(f"{watch_reference} | {price_list}")
    return price_list


def run() -> None:
    amount_total = 0
    found_watches = 0
    content = read_csv("watches.csv")
    for year, reference, name, quantity in content:
        formated_reference = format_watch_reference(reference)
        not_sold_results = search_in_ebay(formated_reference, check_sold=False)
        sold_results = search_in_ebay(formated_reference, check_sold=True)

        if not not_sold_results and not sold_results:
            logger.error(f"{formated_reference} | Watch not found, skipping...")
            continue

        if not_sold_results:
            not_sold_price_average = round(sum(not_sold_results) / len(not_sold_results), 2)
            logger.debug(f"{formated_reference} | Not sold average: {not_sold_price_average}")
        else:
            not_sold_price_average = None

        if sold_results:
            sold_price_average = round(sum(sold_results) / len(sold_results), 2)
            logger.debug(f"{formated_reference} | Sold average: {sold_price_average}")
        else:
            sold_price_average = None

        if not_sold_price_average and sold_price_average:
            total_average = round((not_sold_price_average + sold_price_average) / 2, 2)
        elif sold_price_average:
            total_average = sold_price_average
        elif not_sold_price_average:
            total_average = not_sold_price_average
        else:
            continue
        logger.debug(f"{formated_reference} | Total average: {total_average}")

        amount_total += total_average * int(quantity)
        found_watches += 1

        qty_text = f"{quantity} units" if int(quantity) > 1 else f"{quantity} unit"
        logger.info(
            f"{formated_reference} | {found_watches}/{len(content)} | Watch price: {total_average} ({qty_text})"
        )

    logger.info(
        f"Estimate total value of the collection ({found_watches}/{len(content)} watches found): "
        f"{round(amount_total, 2)}"
    )


if __name__ == "__main__":
    run()
