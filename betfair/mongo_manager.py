from datetime import datetime, timedelta
import logging
import pandas as pd
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient as MongoClient

from betfair.config import (HOSTNAME, MONGO_AUTH_DB, MONGO_DB, MONGO_PASSWROD,
                            MONGO_USERNAME)


log = logging.getLogger(__name__)

connection_string = (f"mongodb://{MONGO_USERNAME}:{MONGO_PASSWROD}@{HOSTNAME}:27017/{MONGO_DB}"
                     f"?authSource={MONGO_AUTH_DB}")


mongo_client = MongoClient(connection_string)

mongo_db = mongo_client["horse_racing"]
metadata_collection = mongo_db["metadata"]
punters_com_au_collection = mongo_db["punters_com_au"]
tickdata_collection = mongo_db["tickdata"]
orders_collection = mongo_db["orders"]
strategy_collection = mongo_db["strategies"]
winner_collection = mongo_db["winner"]


async def insert_order(order):
    await orders_collection.insert_one(order)


async def get_strategies_for_play():
    cursor = strategy_collection.find(
        {"active": {"$in": ["dummy", "on"]}}, {"_id": 0}
    )
    loaded_strategies = await cursor.to_list(length=None)
    return loaded_strategies


async def update_estimated_profit(order):
    await orders_collection.update_one({'timestamp': order['timestamp'],
                                        'market_id': order['market_id'],
                                        'selection_id': order['selection_id'],
                                        'strategy_name': order['strategy_name']},
                                       {'$set': {'profit_estimate': order['profit_estimate'],
                                                 'outcome_estimate': order['outcome_estimate']}})


async def insert_order(order):
    await orders_collection.insert_one(order)


async def get_strategies_for_play():
    cursor = strategy_collection.find(
        {"active": {"$in": ["dummy", "on"]}}, {"_id": 0}
    )
    loaded_strategies = await cursor.to_list(length=None)
    return loaded_strategies


async def get_data_for_hypothetical_payoff():
    # Async function to load winners where timestamp is greater than 24 hours ago
    cursor = winner_collection.find(
        {'timestamp': {'$gte': datetime.utcnow() - timedelta(hours=24)}},
        {'_id': False}
    )
    winners = await cursor.to_list(length=None)
    winners_df = pd.DataFrame(winners)

    try:
        available_market_ids = list(winners_df['market_id'].unique())
    except KeyError:
        available_market_ids = []

    # Async function to load placed bets that contains available_market_ids
    # TODO: only load the ones that have no estimated_profit or estimated_outcome
    cursor = orders_collection.find(
        {'market_id': {'$in': available_market_ids}},
        {'_id': False}
    )
    orders_list = await cursor.to_list(length=None)

    return winners_df, orders_list


async def get_orders_without_estimated_winner(hours):
    # Async function to load placed bets that contains market_ids but has no estimated_profit or estimated_outcome
    # also filter to only get orders in the last hours based on _id

    delta = datetime.utcnow() - timedelta(hours=hours)
    hexSeconds = format(int(delta.timestamp()), 'x')
    constructedObjectId = ObjectId(hexSeconds + "0000000000000000")

    cursor = orders_collection.find(
        {
            'outcome_estimate': {'$exists': False},
            '_id': {'$gte': constructedObjectId}
        },
        {'market_id': True}
    )

    # get distinct market_ids
    market_ids = await cursor.distinct('market_id')
    log.debug(f"market_ids to check winner: {market_ids}")
    return market_ids


async def insert_winner(data):
    await winner_collection.insert_one(data)
