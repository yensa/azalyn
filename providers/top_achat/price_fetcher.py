import re

import httpx
from bs4 import BeautifulSoup

from .exceptions import JobFailure

JOB_NAME = "TOP_ACHAT_PRICE_FETCHER"

extract_price_regex = re.compile(r"(\d+\.\d+).*€")


def fetch_price(url: str, client: httpx.Client) -> float:
    try:
        response = client.get(url)
        response.raise_for_status()
    except httpx.HTTPError as e:
        raise JobFailure(JOB_NAME, "Could not load price page") from e

    document = BeautifulSoup(response.content, feature="html.parser")

    el = document.find("span", class_="offer-price__price")

    if not (result := extract_price_regex.search(el.text)):
        raise JobFailure(JOB_NAME, "Could not parse the price")

    try:
        price = float(result.group(1))
    except TypeError as e:
        raise JobFailure(JOB_NAME, "Price was not a float") from e

    return price
