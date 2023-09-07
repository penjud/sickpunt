import asyncio
import collections
import json
import threading
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta

import betfairlightweight
import numpy as np
import pytz
import uvicorn
from betfairlightweight import StreamListener
from betfairlightweight.filters import (streaming_market_data_filter,
                                        streaming_market_filter)
from fastapi import FastAPI, WebSocket
from pymongo import MongoClient

# constants
APP_KEY="mECg2P2ohk92MLXy"
PASSWORD=r"%2s8ThBv&u5#s$Wg"
USERNAME="penjud"
COUNTRIES = ['AU']
MINS_TO_START_FILTER = 180
MINS_MAX_RACE_DURATION = 60
SECS_MARKET_FETCH_INTERVAL = 60

mongo_client = MongoClient("mongodb://localhost:27017/")
mongo_db = mongo_client["horse_racing"]
tickdata_collection = mongo_db["tickdata"]
metadata_collection = mongo_db["metadata"]

SECS_TO_START_FILTER = MINS_TO_START_FILTER * 60
SECS_MAX_RACE_DURATION = MINS_MAX_RACE_DURATION * 60

client = betfairlightweight.APIClient(
    username=USERNAME, password=PASSWORD, app_key=APP_KEY)
client.login_interactive()

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


def vwap(data):
    data = np.array(data)
    prices = data[:, 0]
    volumes = data[:, 1]
    vwap = np.sum(prices * volumes) / np.sum(volumes)
    return vwap


def get_market_sum(market_id, field_name):
    total_sum = 0
    for horse_id, data in ff_cache[market_id].items():
        if horse_id[0] == '_':
            continue
        value = data[field_name]
        if value:  # prevent division by zero
            total_sum += (1 / value)
    return total_sum


class CustomListener(StreamListener):
    def __init__(self):
        super().__init__()

    def on_data(self, raw_data):
        data = json.loads(raw_data)
        for market_change in data.get('mc', []):
            market_id = market_change.get('id')
            if market_id in race_ids:
                race_start_time = race_dict[market_id]['start_time']
                secs_to_start = (race_start_time -
                                 datetime.utcnow().replace(tzinfo=pytz.utc)).total_seconds()
                for runner_change in market_change.get('rc', []):
                    runner_id = str(runner_change.get('id'))

                   # Initialize deques if they don't exist
                    if not '_back_values' in ff_cache[market_id][runner_id]:
                        ff_cache[market_id][runner_id]['_back_values'] = deque(
                            maxlen=1000)
                    if not '_lay_values' in ff_cache[market_id][runner_id]:
                        ff_cache[market_id][runner_id]['_lay_values'] = deque(
                            maxlen=1000)
                    if not '_last_values' in ff_cache[market_id][runner_id]:
                        ff_cache[market_id][runner_id]['_last_values'] = deque(
                            maxlen=1000)

                    # Update values and moving averages
                    new_back = runner_change.get('atb')[0][0] if runner_change.get(
                        'atb') else ff_cache[market_id][runner_id]['back']
                    ff_cache[market_id][runner_id]['_back_values'].append(
                        new_back)
                    ff_cache[market_id][runner_id]['_back_moving_avg'] = sum(
                        ff_cache[market_id][runner_id]['_back_values']) / len(ff_cache[market_id][runner_id]['_back_values'])

                    new_lay = runner_change.get('atl')[0][0] if runner_change.get(
                        'atl') else ff_cache[market_id][runner_id]['lay']
                    ff_cache[market_id][runner_id]['_lay_values'].append(
                        new_lay)
                    ff_cache[market_id][runner_id]['_lay_moving_avg'] = sum(
                        ff_cache[market_id][runner_id]['_lay_values']) / len(ff_cache[market_id][runner_id]['_lay_values'])

                    new_last = runner_change.get('trd')[0][0] if runner_change.get(
                        'trd') else ff_cache[market_id][runner_id]['last']
                    ff_cache[market_id][runner_id]['_last_values'].append(
                        new_last)
                    ff_cache[market_id][runner_id]['_last_moving_avg'] = sum(
                        ff_cache[market_id][runner_id]['_last_values']) / len(ff_cache[market_id][runner_id]['_last_values'])

                    ff_cache[market_id][runner_id]['_back_min'] = min(
                        ff_cache[market_id][runner_id]['_back_values'])
                    ff_cache[market_id][runner_id]['_back_max'] = max(
                        ff_cache[market_id][runner_id]['_back_values'])

                    ff_cache[market_id][runner_id]['_lay_min'] = min(
                        ff_cache[market_id][runner_id]['_lay_values'])
                    ff_cache[market_id][runner_id]['_lay_max'] = max(
                        ff_cache[market_id][runner_id]['_lay_values'])

                    ff_cache[market_id][runner_id]['_last_min'] = min(
                        ff_cache[market_id][runner_id]['_last_values'])
                    ff_cache[market_id][runner_id]['_last_max'] = max(
                        ff_cache[market_id][runner_id]['_last_values'])

                    ff_cache[market_id][runner_id]['back'] = runner_change.get(
                        'atb')[0][0] if runner_change.get('atb') else ff_cache[market_id][runner_id]['back']
                    ff_cache[market_id][runner_id]['lay'] = runner_change.get(
                        'atl')[0][0] if runner_change.get('atl') else ff_cache[market_id][runner_id]['lay']
                    ff_cache[market_id][runner_id]['last'] = runner_change.get(
                        'trd')[0][0] if runner_change.get('trd') else ff_cache[market_id][runner_id]['last']
                    trd_value = runner_change.get('trd')
                    if trd_value is not None:
                        ff_cache[market_id][runner_id]['volume'] = trd_value[0][1] + \
                            ff_cache[market_id][runner_id]['last']
                    else:
                        ff_cache[market_id][runner_id]['volume'] = ff_cache[market_id][runner_id]['last']

                    last_cache[market_id][runner_id]['back'] = runner_change.get(
                        'atb')[0][0] if runner_change.get('atb') else None
                    last_cache[market_id][runner_id]['lay'] = runner_change.get(
                        'atl')[0][0] if runner_change.get('atl') else None
                    last_cache[market_id][runner_id]['last'] = runner_change.get(
                        'trd')[0][0] if runner_change.get('trd') else None

                    ff_cache[market_id]['_lay_overrun'] = overrun_lay = get_market_sum(
                        market_id, 'lay')
                    ff_cache[market_id]['_back_overrun'] = overrun_back = get_market_sum(
                        market_id, 'back')
                    ff_cache[market_id]['_last_overrun'] = overrun_last = get_market_sum(
                        market_id, 'last')
                    ff_cache[market_id]['_seconds_to_start'] = secs_to_start

                    flattened_data = {
                        # divide by 1000 to convert from milliseconds to seconds
                        'pt': datetime.fromtimestamp(data.get('pt')/1000) if data.get('pt') else None,
                        'meta': {
                            'market_id': market_id,
                            'runner_id': runner_id,
                            'secs_to_start': -secs_to_start
                        },
                        'back_odds': runner_change.get('atb')[0][0] if runner_change.get('atb') else None,
                        'back_vol': runner_change.get('atb')[0][1] if runner_change.get('atb') else None,
                        'lay_odds': runner_change.get('atl')[0][0] if runner_change.get('atl') else None,
                        'lay_vol': runner_change.get('atl')[0][1] if runner_change.get('atl') else None,
                        'traded_odds': runner_change.get('trd')[0][0] if runner_change.get('trd') else None,
                        'traded_vol': runner_change.get('trd')[0][1] if runner_change.get('trd') else None,
                        'back_vwap': vwap(runner_change.get('atb')) if runner_change.get('atb') else None,
                        'lay_vwap': vwap(runner_change.get('atl')) if runner_change.get('atl') else None,
                        'overrun_back': overrun_back if overrun_back else None,
                        'overrun_lay': overrun_lay if overrun_lay else None,
                        'overrun_last': overrun_last if overrun_last else None,
                        'cumulative_volume': ff_cache[market_id][runner_id]['volume'] if ff_cache[market_id][runner_id]['volume'] else None,
                        # 'forward_fills': ff_cache[market_id],
                    }
                    # print (flattened_data)
                    if data.get('clk') != 'AAAAAAAA' and SECS_MAX_RACE_DURATION > flattened_data['meta']['secs_to_start'] > -SECS_TO_START_FILTER:
                        print(flattened_data)
                        tickdata_collection.insert_one(flattened_data)


def get_current_races():
    while True:  # Repeat indefinitely
        # Get the current time and the time 60 minutes from now
        now = datetime.utcnow()
        end_time = now + timedelta(days=1)
        race_datas = []

        # Define the filter for the races
        market_filter = {
            'eventTypeIds': ['7'],  # Horse Racing event type ID
            'marketStartTime': {
                'from': (now - timedelta(minutes=10)).isoformat(),
                'to': end_time.isoformat()
            },
            'market_types': ['WIN'],
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
                race_data['marketStartTime']).replace(tzinfo=pytz.utc)}

            race_data_available.set()

        print(race_datas)
        upsert_market_data(race_datas)
        time.sleep(SECS_MARKET_FETCH_INTERVAL)


def upsert_market_data(race_data):
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
    threading.Thread(target=get_current_races, daemon=True).start()

    betfair_socket = client.streaming.create_stream(
        listener=CustomListener())

    market_filter = streaming_market_filter(
        event_type_ids=['7'],  # Racing
        country_codes=COUNTRIES,
        market_types=['WIN'],
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
