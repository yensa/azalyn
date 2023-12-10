from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup
from thefuzz import fuzz

from .exceptions import JobFailure

JOB_NAME = "LDLC_PAGE_FETCHER"
MIN_RATIO = 85

base_url = "https://www.ldlc.com"
# search_url = "/v4/fr-be/search/autocomplete/{terms}"
search_url = "/fr-be/recherche/{terms}"


def prepare_search_terms(product_name: str) -> str:
    # return quote(quote(product_name))
    return product_name


def fetch_product_page(product_name: str, client: httpx.Client) -> str:
    url = urljoin(base_url, search_url).format(
        terms=prepare_search_terms(product_name))

    try:
        response = client.get(url)
        response.raise_for_status()
    except httpx.HTTPError as e:
        raise JobFailure(JOB_NAME, "Could not load price page") from e

    data = response.content

    document = BeautifulSoup(data, features="html.parser")
    try:
        el = document.find("div", class_="wrap-list").find("ul").find_all("li")[0].find("h3").find("a")
    except IndexError as e:
        raise JobFailure(
            JOB_NAME, f"Could not find any product matching {product_name}"
        ) from e

    # We need to validate the name
    label = el.text

    ratio = fuzz.partial_ratio(product_name, label)

    if ratio < MIN_RATIO:
        raise JobFailure(
            JOB_NAME, f"Could not find any product matching {product_name}")

    return urljoin(base_url, el["href"])
