import asyncio
import collections
import json
import logging
import threading
import time
from collections import defaultdict
from datetime import datetime, timedelta

import pytz
import uvicorn
import websockets
from betfairlightweight.filters import (streaming_market_data_filter,
                                        streaming_market_filter)
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from betfair.metadata import get_current_event_metadata
from betfair.config import COUNTRIES, EVENT_TYPE_IDS, MARKET_TYPES, client
from betfair.streamer import HorseRaceListener

app = FastAPI()
race_data_available = asyncio.Event()

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
        await asyncio.sleep(.1)


if __name__ == '__main__':
    race_ids = set()
    race_dict = dict()
    punters_com_au = dict()
    horse_info_dict = dict()
    runnerid_name_dict = dict()
    ff_cache = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
    last_cache = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
    threading.Thread(target=lambda: get_current_event_metadata(race_ids, race_dict, race_data_available, horse_info_dict, runnerid_name_dict),
                     daemon=True).start()
    time.sleep(10)
    betfair_socket = client.streaming.create_stream(
        listener=HorseRaceListener(
            ff_cache, race_ids, last_cache, race_dict, punters_com_au, horse_info_dict, runnerid_name_dict)
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
    uvicorn.run(app, host="0.0.0.0", port=7777)
