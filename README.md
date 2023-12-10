# How to run

There are a number of providers available, each of them is located in its own python module and has a `__main__.py`
that enables you to run them.

Each provider has two available commands, the first one `page`, will listen to a specific channel on redis pubsub
for messages on what was inserted into the database. Each of the providers will then try to fetch the page related to the 
inserted CPU and add that information directly into the database.

## Importing a CPU

TODO

## Fetching a price

In order to fetch a price, you can use the second subcomand of the provider script called `price`, this subcommand takes
the `_id` of the document you want to update in the database, and it will retrieve the current price for you

# Checkout what is in the database

TODO
