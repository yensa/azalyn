from urllib.parse import urljoin

import httpx
from thefuzz import fuzz

from .exceptions import JobFailure

JOB_NAME = "TOP_ACHAT_PAGE_FETCHER"
MIN_RATIO = 85

base_url = "https://www.topachat.com"
search_url = "/api/search/search.suggest.php?terms={terms}"


def prepare_search_terms(product_name: str) -> str:
    return product_name.replace(" ", "+")


def fetch_product_page(product_name: str, client: httpx.Client) -> str:
    url = urljoin(base_url, search_url).format(
        terms=prepare_search_terms(product_name))

    try:
        response = client.get(url)
        response.raise_for_status()
    except httpx.HTTPError as e:
        raise JobFailure(JOB_NAME, "Could not load price page") from e

    data = response.json()

    try:
        result = data["result"]["document"]["products"][0]
    except KeyError as e:
        raise JobFailure(JOB_NAME, "Data has wrong format") from e
    except IndexError as e:
        raise JobFailure(
            JOB_NAME, f"Could not find any product matching {product_name}"
        ) from e

    # We need to validate the name
    label = result["label"]

    ratio = fuzz.partial_ratio(product_name, label)

    if ratio < MIN_RATIO:
        raise JobFailure(
            JOB_NAME, f"Could not find any product matching {product_name}")

    return urljoin(base_url, result["url"])
