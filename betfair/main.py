import asyncio
import collections
import json
import threading
import time
from collections import defaultdict
from datetime import datetime, timedelta

import pytz
import uvicorn
from betfairlightweight.filters import (streaming_market_data_filter,
                                        streaming_market_filter)
from fastapi import FastAPI, WebSocket
from pymongo import MongoClient

from betfair.config import client
from betfair.horse_racing_listener import HorseRaceListener

# constants
COUNTRIES = ['AU']
MARKET_TYPES = ['WIN']
EVENT_TYPE_IDS = ['7']  # Horse Racing event type ID

SECS_MARKET_FETCH_INTERVAL = 60

HOSTNAME = '3.24.169.161'
MONGO_USERNAME = "admin"
MONGO_PASSWROD = "sickpunt123"
MONGO_DB = "horse_racing"  # The database you want to connect to
MONGO_AUTH_DB = "admin"  # Database where the user is authenticated
connection_string = (f"mongodb://{MONGO_USERNAME}:{MONGO_PASSWROD}@{HOSTNAME}:27017/{MONGO_DB}"
                     f"?authSource={MONGO_AUTH_DB}")

mongo_client = MongoClient(connection_string)
mongo_db = mongo_client["horse_racing"]
tickdata_collection = mongo_db["tickdata"]
metadata_collection = mongo_db["metadata"]

app = FastAPI()
race_data_available = asyncio.Event()


@app.websocket("/race_updates")
async def race_updates(websocket: WebSocket):
    await websocket.accept()
    while True:
        await race_data_available.wait()
        await websocket.send_json({"race_ids": list(race_ids)})
        await asyncio.sleep(1)


@app.websocket("/ff_cache")
async def last_prices(websocket: WebSocket):
    await websocket.accept()
    while True:
        await race_data_available.wait()

        def convert_deque(data):
            if isinstance(data, collections.deque):
                return list(data)
            elif isinstance(data, dict):
                return {k: convert_deque(v) for k, v in data.items()}
            elif isinstance(data, list):
                return [convert_deque(v) for v in data]
            else:
                return data

        # Before sending the data
        converted_ff_cache = convert_deque(ff_cache)
        await websocket.send_json({"ff_cache": dict(converted_ff_cache)})
        await asyncio.sleep(.1)


def get_current_event_metadata():
    while True:  # Repeat indefinitely
        # Get the current time and the time 60 minutes from now
        now = datetime.utcnow()
        end_time = now + timedelta(days=1)
        race_datas = []

        # Define the filter for the races
        market_filter = {
            'eventTypeIds': EVENT_TYPE_IDS,  # Horse Racing event type ID
            'marketStartTime': {
                'from': (now - timedelta(minutes=10)).isoformat(),
                'to': end_time.isoformat()
            },
            'market_types': MARKET_TYPES,
            'marketCountries': COUNTRIES  # UK and IE market countries
        }

        # Retrieve the list of races
        races = client.betting.list_market_catalogue(
            filter=market_filter,
            max_results=25,
            market_projection=[
                'EVENT', 'RUNNER_DESCRIPTION', 'MARKET_START_TIME']
        )

        # Update the shared dict of market data
        # Update the shared list of market data
        for race in races:
            race_data = json.loads(race.json())
            race_datas.append(race_data)
            race_ids.add(race_data['marketId'])
            race_dict[race_data['marketId']] = {'start_time': datetime.fromisoformat(
                race_data['marketStartTime']).replace(tzinfo=pytz.utc), 'runners': race_data['runners']}

            race_data_available.set()

        print(race_datas)
        upsert_event_metadata(race_datas)
        time.sleep(SECS_MARKET_FETCH_INTERVAL)


def upsert_event_metadata(race_data):
    # upsert the market data into the MongoDB collection
    for race in race_data:
        # use upsert=True to avoid duplicates
        metadata_collection.update_one(
            {'market_id': race['marketId']},
            {
                '$set': race
            },
            upsert=True,
        )


if __name__ == '__main__':
    race_ids = set()
    race_dict = dict()
    ff_cache = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
    last_cache = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
    threading.Thread(target=get_current_event_metadata, daemon=True).start()

    betfair_socket = client.streaming.create_stream(listener=
                                                    HorseRaceListener(ff_cache, race_ids, last_cache, race_dict))

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
    uvicorn.run(app, host="127.0.0.1", port=8010)
