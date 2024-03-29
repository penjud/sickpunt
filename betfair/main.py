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

import numpy as np
import pandas as pd
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
                            STREAM_RESTART_MINUTES, admin_collection, client,
                            orders_collection, strategy_collection, winner_collection)

from betfair.mongo_manager import (get_orders_without_estimated_winner, get_strategies_for_play, insert_winner,
                                   update_estimated_profit, get_data_for_hypothetical_payoff)

from betfair.helper import init_logger
from betfair.metadata import get_current_event_metadata
from betfair.strategy import StrategyHandler
from betfair.streamer import HorseRaceListener
from betfair.api import app

lock = asyncio.Lock()

init_logger(screenlevel=logging.INFO, filename='default')

race_data_available = asyncio.Event()
betfair_socket = None
log = logging.getLogger(__name__)


@app.post("/orders")
async def orders():

    bot_orders_json = list(orders_collection.find({}, {'_id': False}))

    # Use the list_current_orders method to retrieve information about your orders
    response = client.betting.list_cleared_orders()
    orders = response.orders
    # Convert orders to a format suitable for JSON serialization
    elements = [x for x in dir(orders[0]) if x[0] != '_' and x != 'get']
    betfair_orders_json = [
        {element: getattr(order, element) for element in elements} for order in orders]

    betfair_df = pd.DataFrame(betfair_orders_json)
    bot_df = pd.DataFrame(bot_orders_json)
    bot_df['bet_id'] = bot_df['bet_id'].astype(str)
    betfair_df['bet_id'] = betfair_df['bet_id'].astype(str)

    df = pd.merge(betfair_df, bot_df, on=['bet_id'], how='outer')
    df = df.drop(['handicap', 'price_reduced',  'customer_order_ref',
                  'customer_strategy_ref', 'persistence_type_x', 'persistence_type_y',
                   'side_y', 'oder_type', 'size-cancelled', 'item_description', 'event_type_id',
                  'comission', 'average_price_matched', 'bet_count', 'settled_date', 
                  'bet_id', 'commission', 'event_id', 'size_cancelled', 'placed_date', 'last_matched_date', 'price_requested', 'total_matched',
                  'user', 'event_id',
                  'order_type', 'size_settled', 'last_traded', 'price', 'last_lay', 'last_back', 'seconds_to_start', 'size'


                  ], axis=1, errors='ignore')
    df = df.fillna(0)
    floats = ['profit', 'last_back', 'last_lay',
              'last_traded', 'price', 'price_matched', 'size']

    for fl in floats:
        try:
            df[fl] = df[fl].astype(float)
        except Exception as e:
            pass

    return json.loads(df.to_json(orient='records'))


@app.post("/balance")
async def balance():
    resp = client.account.get_account_funds()
    return {'Available Funds': resp.available_to_bet_balance,
            'Current exposure': -resp.exposure,
            'Total Funds':  resp.available_to_bet_balance-resp.exposure}


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
        admin_collection.update_one(filter_query, admin_dict, upsert=True)

        return {"message": "Admin successfully saved"}

    except Exception as e:
        return {"error": str(e)}


@app.post("/load_strategy")
async def load_strategy(strategy_name: str):
    # log.info(race_ids)
    strategy_data = strategy_collection.find_one(
        {"StrategyName": strategy_name}, {"_id": 0})

    if strategy_data:
        return strategy_data
    else:
        raise HTTPException(status_code=404, detail="Strategy not found")


@app.post("/delete_strategy")
async def delete_strategy(strategy_name: str):
    # log.info(race_ids)
    res = strategy_collection.delete_one(
        {"StrategyName": strategy_name})


@app.post("/get_strategies")
async def get_strategies():
    # Finding distinct strategy names
    strategy_names = strategy_collection.distinct("StrategyName")
    return {"strategies": strategy_names}


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

        # Assuming you're using pymongo to interact with MongoDB
        existing_doc = strategy_collection.find_one(filter_query)

        if existing_doc:
            # Replace the existing document
            strategy_collection.replace_one(filter_query, strategy_config)
        else:
            # Insert new document
            strategy_collection.insert_one(strategy_config)

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
        await asyncio.sleep(1)


class StreamWithReconnect:
    def __init__(self, client, listener, market_filter, market_data_filter):
        self.client = client
        self.listener = listener
        self.market_filter = market_filter
        self.market_data_filter = market_data_filter

    def update_market_filter(self, new_market_filter):
        self.market_filter = new_market_filter

    def update_market_data_filter(self, new_market_data_filter):
        self.market_data_filter = new_market_data_filter

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

    def stop(self):
        if self.stream is not None:
            # Add logic here to stop the stream. This depends on how your streaming client is implemented.
            self.stream.stop()


async def connect_to_stream(stream_with_reconnect):
    # log.info(f"Current race_ids: {race_ids}")  # Add debug log
    market_filter = streaming_market_filter(
        market_ids=list(race_ids)
    )
    market_data_filter = streaming_market_data_filter(
        fields=['EX_MARKET_DEF', 'EX_ALL_OFFERS', 'EX_TRADED'],
        ladder_levels=3
    )

    stream_with_reconnect.update_market_filter(market_filter)
    stream_with_reconnect.update_market_data_filter(market_data_filter)
    await stream_with_reconnect.run()


async def schedule_stream_restart(interval_minutes=STREAM_RESTART_MINUTES):
    listener = HorseRaceListener(
        ff_cache, race_ids, last_cache, race_dict,
        punters_com_au, horse_info_dict, runnerid_name_dict
    )
    stream_with_reconnect = StreamWithReconnect(client, listener, None, None)

    while True:
        log.info("Starting new streaming session")
        stream_task = asyncio.create_task(
            connect_to_stream(stream_with_reconnect))
        # Convert minutes to seconds
        await asyncio.sleep(interval_minutes * 60)
        log.info("Stopping current streaming session")

        # Stop the old stream
        stream_with_reconnect.stop()

        stream_task.cancel()
        try:
            await stream_task
        except asyncio.CancelledError:
            pass


async def check_strategy(last_cache, ff_cache, race_dict, runnerid_name_dict, strategies):
    while True:
        await strategy_handler.check_execute(
            last_cache, ff_cache, race_dict, runnerid_name_dict, strategies)
        await strategy_handler.check_modify(
            last_cache, ff_cache, race_dict, runnerid_name_dict, strategies)
        await asyncio.sleep(.01)


async def load_strategies(strategies):
    while True:
        log.debug('Loading strategies')
        loaded_strategies = await get_strategies_for_play()
        log.debug('Done')

        # Populate the strategies dictionary with loaded strategies
        loaded_strategy_names = set()
        for strategy in loaded_strategies:
            strategy_name = strategy["StrategyName"]
            strategies[strategy_name] = strategy
            loaded_strategy_names.add(strategy_name)

        # Remove strategies not present in loaded_strategies
        strategy_names_to_remove = [
            name for name in strategies.keys() if name not in loaded_strategy_names]
        for name_to_remove in strategy_names_to_remove:
            del strategies[name_to_remove]

        for race_id in list(ff_cache.keys()):
            if race_id not in race_ids:
                winner = get_winner(race_id)
                if not winner:
                    log.debug("No winner found")
                    continue
                winner_collection.insert_one(
                    {'market_id': race_id, 'winner': winner, 'timestamp': datetime.utcnow()})
                
                del ff_cache[race_id]

        await asyncio.sleep(15)


async def hypothetical_payoff_calc():
    """add payoffs to each bet that has been placed"""
    while True:
        
        # add winners to winner collection
        race_ids = await get_orders_without_estimated_winner(hours=12)
        for race_id in race_ids:
            winner = get_winner(race_id)
            if not winner:
                log.warning("No winner found")
                continue
            log.debug(f'Winner: {winner}')
            await insert_winner(
                {'market_id': race_id, 'winner': winner, 'timestamp': datetime.utcnow()},
                {'market_id': race_id}
                )
        
        # calculate hypothetical payoff
        winners_df, orders_list = await get_data_for_hypothetical_payoff()

        # calculate hypothetical payoffs, depending on oder type lay or back and whether the horse won or not
        for order in orders_list:
            if len(orders_list) > 100:
                log.warning(f'Large number of orders to process estimated profit: {len(orders_list)}')
            try:
                log.debug(f"Processing historical order: {order['market_id']}")
                winners = winners_df[winners_df['market_id']
                                    == order['market_id']]['winner'].values[0]
            except (IndexError, KeyError):
                log.debug(f"No winner found for {order['market_id']}")
                continue   # nothing in the database
            if int(order['selection_id']) in winners:
                if order['side'] == 'BACK':
                    order['profit_estimate'] = order['size'] * \
                        order['price'] - 1
                    order['outcome_estimate'] = 'WON'
                elif order['side'] == 'LAY':
                    order['profit_estimate'] = - \
                        order['size'] * order['price'] + 1
                    order['outcome_estimate'] = 'LOST'
            else:  # loser
                if order['side'] == 'BACK':
                    order['profit_estimate'] = -order['size']
                    order['outcome_estimate'] = 'LOST'
                elif order['side'] == 'LAY':
                    order['profit_estimate'] = order['size']
                    order['outcome_estimate'] = 'WON'

            # save hypothetical payoffs to mongodb
            log.debug(f'Updating estimates profits in orders database')
            await update_estimated_profit(order)

        await asyncio.sleep(234)


def get_winner(market_id):
    """use betfairleightweight to get the winner of a market"""
    market_book = client.betting.list_market_book(
        market_ids=[market_id], price_projection={"priceData": ["EX_BEST_OFFERS"]}
    )
    if not market_book:
        log.warning(f"Market book not found for {market_id}")
        return
    if market_book[0]['status'] == 'OPEN':
        pass # market is still open
    elif market_book[0]['status'] == 'CLOSED':
        winners = [runner.selection_id for runner in market_book[0]['runners'] if runner['status'] == 'WINNER']
        # log.info(f"The winning selection is:  {winners}")
        return winners


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
        loop.create_task(schedule_stream_restart())
        loop.create_task(hypothetical_payoff_calc())
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

    uvicorn.run(app, host="0.0.0.0", port=7779)
