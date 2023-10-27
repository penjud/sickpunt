import asyncio
import json
import logging
import re
import time
from datetime import datetime, timedelta

import pytz

from betfair.config import (COUNTRIES, EVENT_TYPE_IDS, HOURS_TO_FETCH,
                            KEEP_AFTER_RACE_START_MIN, MARKET_TYPES,
                            MAX_RACE_STREAMS, SECS_MARKET_FETCH_INTERVAL,
                            client, punters_com_au_collection,
                            upsert_event_metadata)

log = logging.getLogger(__name__)


async def get_current_event_metadata(race_ids, race_dict, race_data_available, horse_info_dict, runnerid_name_dict):
    while True:  # Repeat indefinitely
        # Get the current time and the time 60 minutes from now
        try:
            client.login_interactive()
        except:
            log.critical("Interactive login failed. Trying again in 1min.")
            await asyncio.sleep(60)
        now = datetime.utcnow()
        end_time = now + timedelta(hours=HOURS_TO_FETCH)
        race_datas = []
        current_races = set()
        horse_names = []
        # Define the filter for the races

        for market_type in MARKET_TYPES:

            market_filter = {
                'eventTypeIds': EVENT_TYPE_IDS,  # Horse Racing event type ID
                'marketStartTime': {
                    'from': (now - timedelta(minutes=KEEP_AFTER_RACE_START_MIN)).isoformat(),
                    'to': end_time.isoformat()
                },
                'marketTypeCodes': [market_type],
                'marketCountries': COUNTRIES,  # UK and IE market countries
                # 'raceTypes': ['Flat','Harness','Steepe','Hurdle']
            }

            # Retrieve the list of races
            races = client.betting.list_market_catalogue(
                filter=market_filter,
                max_results=MAX_RACE_STREAMS,
                sort="FIRST_TO_START",
                market_projection=[
                    'EVENT', 'EVENT_TYPE', 'COMPETITION', 'RUNNER_DESCRIPTION', 'MARKET_START_TIME', 'RUNNER_METADATA']
            )

            # Update the shared dict of market data

            for race in races:
                race_data = json.loads(race.json())
                # if race_data['marketId'] in race_ids:
                #     log.warning("Metadata tries to override previous market type")
                #     continue
                
                current_races.add(race_data['marketId'])
                race_datas.append(race_data)
                race_ids.add(race_data['marketId'])
                race_dict[race_data['marketId']] = {'start_time': datetime.fromisoformat(
                    race_data['marketStartTime']).replace(tzinfo=pytz.utc),
                    'runners': race_data['runners'],
                    'event': race_data['event'],
                    'fullTitle': race_data['eventType']['name'] +' '+ race_data['marketName'] + ' ' + race_data['event']['name']+ ' ' + race_data['event']['countryCode'],
                    'marketName': race_data['marketName'],
                    'market_type': market_type,
                    'event_type': race_data['eventType'],
                    'totalMatched': race_data['totalMatched']}

                race_data_available.set()

            # remove all elements in race_ids that are not in current_races
            race_ids.intersection_update(current_races)

            # print(race_datas)
            upsert_event_metadata(race_datas)

            # load all market_ids from punters_com_au_collection
            horse_names = []
            for race in race_datas:
                for horse in race['runners']:
                    horse_names.append(
                        re.sub(r'^\d+\.\s+', '', horse['runnerName']))
                    runnerid_name_dict[horse['selectionId']
                                       ] = horse['runnerName']

            # Execute the query
            horse_infos = list(punters_com_au_collection.find(
                {"Horse Name": {"$in": horse_names}}, {'_id': 0}))
            for horse in horse_infos:
                horse_info_dict[horse['Horse Name']] = horse

        await asyncio.sleep(SECS_MARKET_FETCH_INTERVAL)
