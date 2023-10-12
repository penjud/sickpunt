import json
import logging
import re
import time
from datetime import datetime, timedelta

import pytz

from betfair.config import (COUNTRIES, EVENT_TYPE_IDS, KEEP_AFTER_RACE_START_MIN, MARKET_TYPES,
                            SECS_MARKET_FETCH_INTERVAL, client,
                            punters_com_au_collection, upsert_event_metadata)

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def get_current_event_metadata(race_ids, race_dict, race_data_available, horse_info_dict, runnerid_name_dict):
    while True:  # Repeat indefinitely
        # Get the current time and the time 60 minutes from now
        try:
            client.login_interactive()
        except:
            print("Interactive login failed. Trying again in 1min.")
            time.sleep(60)
        now = datetime.utcnow()
        end_time = now + timedelta(days=1)
        race_datas = []

        # Define the filter for the races
        market_filter = {
            'eventTypeIds': EVENT_TYPE_IDS,  # Horse Racing event type ID
            'marketStartTime': {
                'from': (now - timedelta(minutes=KEEP_AFTER_RACE_START_MIN)).isoformat(),
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
        current_races = set()
        for race in races:
            race_data = json.loads(race.json())
            race_datas.append(race_data)
            race_ids.add(race_data['marketId'])
            current_races.add(race_data['marketId'])
            race_dict[race_data['marketId']] = {'start_time': datetime.fromisoformat(
                race_data['marketStartTime']).replace(tzinfo=pytz.utc), 
                                                'runners': race_data['runners'],
                                                'event': race_data['event'],
                                                'marketName': race_data['marketName'],
                                                'totalMatched': race_data['totalMatched']}

            race_data_available.set()

        # remove all elements in race_ids that are not in current_races
        race_ids.intersection_update(current_races)
        # print('----')
        # print(datetime.now())
        # print (len(race_ids))
        # print (race_ids)
        # print(current_races)

        # print(race_datas)
        upsert_event_metadata(race_datas)

        # load all market_ids from punters_com_au_collection
        horse_names = []
        for race in race_datas:
            for horse in race['runners']:
                horse_names.append(
                    re.sub(r'^\d+\.\s+', '', horse['runnerName']))
                runnerid_name_dict[horse['selectionId']] = horse['runnerName']

        # Execute the query
        horse_infos = list(punters_com_au_collection.find(
            {"Horse Name": {"$in": horse_names}}, {'_id': 0}))
        for horse in horse_infos:
            horse_info_dict[horse['Horse Name']] = horse

        time.sleep(SECS_MARKET_FETCH_INTERVAL)
