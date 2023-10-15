import asyncio
import collections
import copy
import json
import logging
import queue
import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict

import pytz
import uvicorn
import websockets
from betfairlightweight.exceptions import SocketError
from betfairlightweight.filters import (streaming_market_data_filter,
                                        streaming_market_filter)
from fastapi import (FastAPI, HTTPException, Request, WebSocket,
                     WebSocketDisconnect)
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from requests import request
from tenacity import retry, wait_exponential

from betfair.config import (COUNTRIES, EVENT_TYPE_IDS, MARKET_TYPES,
                            admin_collection, client, orders_collection,
                            strategy_collection)
from betfair.helper import init_logger
from betfair.metadata import get_current_event_metadata
from betfair.strategy import StrategyHandler
from betfair.streamer import HorseRaceListener

lock = asyncio.Lock()


init_logger(screenlevel=logging.INFO, filename='default')

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You might want to be more specific in production.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
race_data_available = asyncio.Event()
betfair_socket = None
log = logging.getLogger(__name__)


@app.websocket("/race_updates")
async def race_updates(websocket: WebSocket):
    """
    Sends a JSON message containing the list of race IDs to the client
    whenever the `race_data_available` event is set.

    :param websocket: WebSocket connection object
    """
    await websocket.accept()
    while True:
        await race_data_available.wait()
        try:
            await websocket.send_json({"race_ids": list(race_ids)})
        except WebSocketDisconnect:
            log.warning("Client disconnected")
        await asyncio.sleep(1)


@app.post("/orders")
async def get_orders():
    """
    Returns the contents of the `orders_collection` in MongoDB.

    :return: List of orders
    """
    return list(orders_collection.find({}, {'_id': False}))


@app.post("/load_admin")
async def load_admin():
    return list(admin_collection.find({"Email": "default"}, {'_id': False}))[0]


@app.post("/save_admin")
async def save_admin(admin_dict: Dict):
    try:
        # Extract strategy name for the upsert filter
        admin_dict = admin_dict['admin_dict']
        email = admin_dict.get("Email")

        filter_query = {'Email': email}
        update_query = {'$set': admin_dict}

        # Assuming you're using pymongo to interact with MongoDB
        admin_collection.update_one(filter_query, update_query, upsert=True)

        return {"message": "Admin successfully saved"}

    except Exception as e:
        return {"error": str(e)}


@app.post("/load_strategy")
async def load_strategy(strategy_name: str):
    strategy_data = strategy_collection.find_one(
        {"StrategyName": strategy_name}, {"_id": 0})

    if strategy_data:
        return strategy_data
    else:
        raise HTTPException(status_code=404, detail="Strategy not found")


@app.post("/get_strategies")
async def get_strategies():
    # Finding distinct strategy names
    strategy_names = strategy_collection.distinct("StrategyName")
    return {"strategies": strategy_names}


@app.post("/open_orders")
async def open_orders():
    try:
        # Use the list_current_orders method to retrieve information about your orders
        response = client.betting.list_current_orders()
        orders = response.orders
        # Convert orders to a format suitable for JSON serialization
        orders_json = [{'bet_id': order.bet_id, 'status': order.status,
                        'price': order.price, 'size': order.size} for order in orders]
        return {"orders": orders_json}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/save_strategy")
async def save_strategy(strategy_config: Dict):
    try:
        # Extract strategy name for the upsert filter
        strategy_config = strategy_config['strategy_config']
        strategy_name = strategy_config.get("StrategyName")

        # Remove any unwanted keys like [[Prototype]], if needed
        # (it generally won't be there in parsed JSON)

        # Define the filter and update query
        filter_query = {'StrategyName': strategy_name}
        update_query = {'$set': strategy_config}

        # Assuming you're using pymongo to interact with MongoDB
        strategy_collection.update_one(filter_query, update_query, upsert=True)

        return {"message": "Strategy successfully saved"}

    except Exception as e:
        return {"error": str(e)}


@app.websocket("/ff_cache")
async def last_prices(websocket: WebSocket):
    """
    Sends a JSON message containing the last prices to the client
    whenever the `race_data_available` event is set.

    :param websocket: WebSocket connection object
    """
    await websocket.accept()
    while True:
        await race_data_available.wait()

        def convert_deque(data):
            """
            Converts deque objects to lists and recursively converts nested deques and dicts.

            :param data: Deque or dict object
            :return: Converted list or dict object
            """
            if isinstance(data, collections.deque):
                return list(data)
            elif isinstance(data, dict):
                return {k: convert_deque(v) for k, v in data.items()}
            else:
                return data

        for key in list(ff_cache.keys()):
            if key not in race_ids:
                log.info(f"Deleting {key} from ff_cache")
                del ff_cache[key]

        # Before sending the data
        converted_ff_cache = convert_deque(ff_cache)

        try:
            await websocket.send_json({"ff_cache": dict(converted_ff_cache)})
        except websockets.exceptions.ConnectionClosedOK:
            break
        except TypeError as e:
            log.error(f"TypeError: {e}")
            log.error(f"Offending data: {converted_ff_cache}")
            # Optionally, re-raise the exception if you want the error to propagate
            # raise
        await asyncio.sleep(0)


class StreamWithReconnect:
    def __init__(self, client, listener, market_filter, market_data_filter):
        self.client = client
        self.listener = listener
        self.market_filter = market_filter
        self.market_data_filter = market_data_filter
        self.stream = None
        self.output_queue = asyncio.Queue()

    @retry(wait=wait_exponential(multiplier=1, min=2, max=30))
    async def run(self):
        log.info("Starting StreamWithReconnect")
        loop = asyncio.get_event_loop()

        try:
            # If the create_stream method is synchronous
            self.stream = await loop.run_in_executor(None, lambda: self.client.streaming.create_stream(listener=self.listener))

            # If the subscribe_to_markets method is synchronous
            await loop.run_in_executor(None, lambda: self.stream.subscribe_to_markets(market_filter=self.market_filter, market_data_filter=self.market_data_filter))

            # If the start method is synchronous
            await loop.run_in_executor(None, self.stream.start)

        except Exception as e:  # Adjust the exception types as needed
            log.critical(f"Unhandled exception: {e}")
            raise


async def connect_to_stream():
    # Assuming 'client' and all filter variables are already defined
    listener = HorseRaceListener(
        ff_cache, race_ids, last_cache, race_dict,
        punters_com_au, horse_info_dict, runnerid_name_dict
    )
    market_filter = streaming_market_filter(
        event_type_ids=EVENT_TYPE_IDS,
        country_codes=COUNTRIES,
        market_types=MARKET_TYPES,
    )
    market_data_filter = streaming_market_data_filter(
        fields=['EX_MARKET_DEF', 'EX_ALL_OFFERS', 'EX_TRADED'],
        ladder_levels=3
    )

    stream_with_reconnect = StreamWithReconnect(
        client, listener, market_filter, market_data_filter
    )
    await stream_with_reconnect.run()


async def check_strategy(last_cache, ff_cache, race_dict, runnerid_name_dict, strategies):
    while True:
        await strategy_handler.check_execute(
            last_cache, ff_cache, race_dict, runnerid_name_dict, strategies)
        await strategy_handler.check_modify(
            last_cache, ff_cache, race_dict, runnerid_name_dict, strategies)
        await asyncio.sleep(0)


async def load_strategies(strategies):
    while True:
        loaded_strategies = strategy_collection.find(
            {"active": {"$in": ["dummy", "on"]}}, {"_id": 0}
        )
        for strategy in loaded_strategies:
            strategies[strategy["StrategyName"]] = strategy
        await asyncio.sleep(10)


async def update_remaining_time(ff_cache):
    while True:
        async with lock:
            ff_copy = copy.copy(ff_cache)
        for market_id, race_data in ff_copy.items():
            ff = ff_cache
            try:
                iso_format_string = ff[market_id]['_race_start_time']
                race_start_time = datetime.fromisoformat(iso_format_string)
                race_data['_seconds_to_start'] = (
                    race_start_time - datetime.utcnow().replace(tzinfo=pytz.utc)).total_seconds()
                ff[market_id]['_seconds_to_start'] = race_data['_seconds_to_start']
            except TypeError:
                log.error(
                    "TypeError in update_remaining_time, no starttime")
        await asyncio.sleep(.5)


@app.on_event("startup")
async def startup_event():
    loop = asyncio.get_event_loop()
    try:
        loop.create_task(get_current_event_metadata(
            race_ids, race_dict, race_data_available, horse_info_dict, runnerid_name_dict))
        loop.create_task(load_strategies(strategies))
        loop.create_task(check_strategy(last_cache, ff_cache,
                         race_dict, runnerid_name_dict, strategies))
        loop.create_task(update_remaining_time(ff_cache))
        loop.create_task(connect_to_stream())
    except Exception as e:
        log.critical(f"Error during startup: {e}")

if __name__ == '__main__':
    strategy_handler = StrategyHandler()
    race_ids = set()
    race_dict = dict()
    punters_com_au = dict()
    horse_info_dict = dict()
    runnerid_name_dict = dict()
    orders = dict()
    strategies = dict()
    ff_cache = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
    last_cache = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))

    uvicorn.run(app, host="0.0.0.0", port=7777)
