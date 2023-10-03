import asyncio
import collections
import copy
import json
import logging
import threading
import time
from collections import defaultdict
from datetime import datetime, timedelta

import pytz
import uvicorn
import websockets
from betfairlightweight.exceptions import SocketError
from betfairlightweight.filters import (streaming_market_data_filter,
                                        streaming_market_filter)
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from betfair.config import (COUNTRIES, EVENT_TYPE_IDS, MARKET_TYPES, client,
                            orders_collection, strategy_collection)
from betfair.metadata import get_current_event_metadata
from betfair.strategy import Strateegy1
from betfair.streamer import HorseRaceListener

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


class StrategyName(BaseModel):
    name: str


@app.post("/load_strategy/")
async def load_strategy(strategy: StrategyName):
    # Finding the strategy by name
    strategy_data = strategy_collection.find_one({"name": strategy.name})

    if strategy_data:
        # If found, return the data without the internal _id field
        return {key: value for key, value in strategy_data.items() if key != "_id"}
    else:
        raise HTTPException(status_code=404, detail="Strategy not found")


@app.post("/get_strategies/")
async def get_strategies():
    # Finding distinct strategy names
    strategy_names = strategy_collection.distinct("strategy_name")  # changed from "name" to "strategy_name"
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


class StrategyConfig(BaseModel):
    strategyName: str
    attributesConfig: dict = Field(..., alias='attributesConfig')


@app.post("/save_strategy")
async def save_strategy(strategy_config: StrategyConfig):
    try:
        # Extract strategy name and attributes from the request body
        strategy_name = strategy_config.strategyName
        attributes_config = strategy_config.attributesConfig

        # Define the filter and update query
        filter_query = {'strategy_name': strategy_name}
        update_query = {
            '$set': {
                'strategy_name': strategy_name,
                'attributesConfig': attributes_config
            }
        }

        # Perform upsert operation (Replace 'strategy_collection' with your MongoDB collection)
        strategy_collection.update_one(filter_query, update_query, upsert=True)

        return {"message": "Strategy successfully upserted"}

    except Exception as e:
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


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
                print(f"Deleting {key} from ff_cache")
                del ff_cache[key]

        # Before sending the data
        converted_ff_cache = convert_deque(ff_cache)

        try:
            await websocket.send_json({"ff_cache": dict(converted_ff_cache)})
        except websockets.exceptions.ConnectionClosedOK:
            break
        except TypeError as e:
            print(f"TypeError: {e}")
            print(f"Offending data: {converted_ff_cache}")
            # Optionally, re-raise the exception if you want the error to propagate
            # raise
        await asyncio.sleep(.2)


def connect_to_stream():
    global betfair_socket  # Declare betfair_socket as global inside the function
    try:
        betfair_socket = client.streaming.create_stream(
            listener=HorseRaceListener(
                ff_cache, race_ids, last_cache, race_dict,
                punters_com_au, horse_info_dict, runnerid_name_dict
            )
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

        betfair_socket.subscribe_to_markets(
            market_filter=market_filter,
            market_data_filter=market_data_filter
        )

        threading.Thread(target=betfair_socket.start).start()
    except SocketError as err:
        print(f"SocketError occurred. Reconnecting... {err}")
        # Optionally, you might want to wait for a bit before reconnecting
        time.sleep(5)
        connect_to_stream()


if __name__ == '__main__':
    strategy = Strateegy1()
    race_ids = set()
    race_dict = dict()
    punters_com_au = dict()
    horse_info_dict = dict()
    runnerid_name_dict = dict()
    orders = dict()
    ff_cache = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
    last_cache = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
    threading.Thread(target=lambda: get_current_event_metadata(race_ids, race_dict, race_data_available, horse_info_dict, runnerid_name_dict),
                     daemon=True).start()

    def check_strategy(last_cache, ff_cache):
        while True:
            strategy.check_modify(last_cache, ff_cache)
            strategy.check_execute(last_cache, ff_cache)
            # time.sleep(1)

    def update_remaining_time(last_cache, ff_cache):
        while True:
            lock = threading.Lock()
            with lock:
                ff_copy = copy.copy(ff_cache)
            for market_id, race_data in ff_copy.items():
                ff = ff_cache
                iso_format_string = ff[market_id]['_race_start_time']
                race_start_time = datetime.fromisoformat(iso_format_string)
                race_data['_seconds_to_start'] = (
                    race_start_time - datetime.utcnow().replace(tzinfo=pytz.utc)).total_seconds()
                ff[market_id]['_seconds_to_start'] = race_data['_seconds_to_start']
            time.sleep(1)

    # create a new thread and start it
    t = threading.Thread(target=check_strategy, args=(
        last_cache, ff_cache))
    t.start()

    t = threading.Thread(target=update_remaining_time, args=(
        last_cache, ff_cache))
    t.start()

    time.sleep(10)
    connect_to_stream()

    uvicorn.run(app, host="0.0.0.0", port=7777)
