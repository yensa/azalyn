import logging
import pprint
import time

import click
import httpx
import redis
from bson.objectid import ObjectId
from pymongo import MongoClient
from pymongo.collection import Collection

from . import fetch_price, fetch_product_page
from .exceptions import JobFailure

REDIS_URI = "127.0.0.1"
MONGO_URI = "mongodb://127.0.0.1"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("top_achat")


def save_to_object(
    _id: str,
    fieldname: str,
    field_value: str,
    collection: Collection,
) -> None:
    collection.update_one(
        {"_id": ObjectId(_id)},
        {
            "$set": {
                fieldname: field_value,
            }
        },
    )


@click.group()
def cli():
    pass


@click.command()
@click.argument(
    "channel",
    default="processor",
)
@click.argument(
    "collection_name",
    default="cpu",
)
@click.argument(
    "mongo_db_name",
    default="providers",
)
@click.option("--redis-url", help="The url to connect to redis")
@click.option("--mongo-url", help="The url to connect to mongo")
def page(
    channel: str,
    collection_name: str,
    mongo_db_name: str,
    redis_url: str | None = None,
    mongo_url: str | None = None,
) -> None:
    redis_client = redis.Redis(redis_url or REDIS_URI)
    mongo_client = MongoClient(mongo_url or MONGO_URI)
    http_client = httpx.Client()
    pubsub_client = redis_client.pubsub()

    db = mongo_client[mongo_db_name]
    collection = db[collection_name]

    pubsub_client.subscribe(channel)

    # Pull out the subscription confirmation
    while pubsub_client.get_message() is None:
        time.sleep(0.01)

    logger.info(f"Successfully subscribed to {channel}, waiting for message")

    while True:
        message = pubsub_client.get_message()

        if message and (data := message.get("data")):
            _id, name = data.decode("utf-8").split(";")

            logger.info(f"Received message with {_id=}, processing ...")

            try:
                product_page = fetch_product_page(name, http_client)
            except JobFailure as e:
                logger.exception("Could not process the message", exc_info=e)
                continue

            save_to_object(_id, "top_achat", product_page, collection)

            logger.info("Saved page to object")

        time.sleep(0.01)


@click.command()
@click.argument(
    "object_id",
)
@click.argument(
    "collection_name",
    default="cpu",
)
@click.argument(
    "mongo_db_name",
    default="providers",
)
@click.option("--mongo-url", help="The url to connect to mongo")
def price(
    object_id: str,
    collection_name: str,
    mongo_db_name: str,
    mongo_url: str | None = None,
) -> None:
    mongo_client = MongoClient(mongo_url or MONGO_URI)
    http_client = httpx.Client()

    db = mongo_client[mongo_db_name]
    collection = db[collection_name]

    obj = collection.find_one(
        {"_id": ObjectId(object_id)},
    )

    logger.info(f"{object_id=} successfully loaded")

    url: str | None = obj.get("top_achat")

    if url is None:
        raise ValueError(f"Couldn't find any top_achat url on {object_id=}")

    logger.info("Fetching price")

    try:
        price = fetch_price(url, http_client)
    except JobFailure as e:
        logger.exception(
            f"Couldn't fetch the price for {object_id=}", exc_info=e)
        return

    logger.info("Saving price")

    save_to_object(object_id, "top_achat_price", price, collection)

    logger.info(f"Price ({price} €) saved")


@click.command()
@click.argument(
    "collection_name",
    default="cpu",
)
@click.argument(
    "mongo_db_name",
    default="providers",
)
@click.option("--mongo-url", help="The url to connect to mongo")
@click.option("-n")
def first(
    collection_name: str,
    mongo_db_name: str,
    mongo_url: str | None = None,
    n: str | int = 1,
):
    mongo_client = MongoClient(mongo_url or MONGO_URI)
    db = mongo_client[mongo_db_name]
    collection = db[collection_name]

    cur = collection.find()

    for _ in range(int(n)):
        obj = cur.next()

    pprint.pprint(obj)


cli.add_command(page)
cli.add_command(price)
cli.add_command(first)


if __name__ == "__main__":
    cli()
