import json
import re
from collections import deque
from datetime import datetime

import numpy as np
import pytz
from betfairlightweight import StreamListener

from betfair.config import tickdata_collection

MINS_TO_START_FILTER = 60
MINS_MAX_RACE_DURATION = 60
SECS_TO_START_FILTER = MINS_TO_START_FILTER * 60
SECS_MAX_RACE_DURATION = MINS_MAX_RACE_DURATION * 60


SAVE_TICKDATA_TO_MONGO = False


class HorseRaceListener(StreamListener):
    def __init__(self, ff_cache, race_ids, last_cache, race_dict, punters_com_au, horse_info_dict, runnerid_name_dict):
        super().__init__()
        self.ff_cache = ff_cache
        self.race_ids = race_ids
        self.last_cache = last_cache
        self.race_dict = race_dict
        self.punters_com_au = punters_com_au
        self.horse_info_dict = horse_info_dict
        self.runnerid_name_dict = runnerid_name_dict

    def on_data(self, raw_data):
        data = json.loads(raw_data)
        for market_change in data.get('mc', []):
            market_id = market_change.get('id')
            if market_id in self.race_ids:
                race_start_time = self.race_dict[market_id]['start_time']
                secs_to_start = (race_start_time -
                                 datetime.utcnow().replace(tzinfo=pytz.utc)).total_seconds()
                for runner_change in market_change.get('rc', []):
                    runner_id = str(runner_change.get('id'))
                    runner_name = self.runnerid_name_dict.get(int(runner_id))
                    if runner_name:
                        runner_name = re.sub(r'^\d+\.\s+', '', runner_name)
                   # Initialize deques if they don't exist
                    if not '_back_values' in self.ff_cache[market_id][runner_id]:
                        self.ff_cache[market_id][runner_id]['_back_values'] = deque(
                            maxlen=1000)
                    if not '_lay_values' in self.ff_cache[market_id][runner_id]:
                        self.ff_cache[market_id][runner_id]['_lay_values'] = deque(
                            maxlen=1000)
                    if not '_last_values' in self.ff_cache[market_id][runner_id]:
                        self.ff_cache[market_id][runner_id]['_last_values'] = deque(
                            maxlen=1000)

                    # Update values and moving averages
                    new_back = runner_change.get('atb')[0][0] if runner_change.get(
                        'atb') else self.ff_cache[market_id][runner_id]['back']
                    self.ff_cache[market_id][runner_id]['_back_values'].append(
                        new_back)
                    self.ff_cache[market_id][runner_id]['_runner_name'] = runner_name
                    self.ff_cache[market_id][runner_id]['_back_moving_avg'] = sum(
                        self.ff_cache[market_id][runner_id]['_back_values']) / len(self.ff_cache[market_id][runner_id]['_back_values'])

                    new_lay = runner_change.get('atl')[0][0] if runner_change.get(
                        'atl') else self.ff_cache[market_id][runner_id]['lay']
                    self.ff_cache[market_id][runner_id]['_lay_values'].append(
                        new_lay)
                    self.ff_cache[market_id][runner_id]['_lay_moving_avg'] = sum(
                        self.ff_cache[market_id][runner_id]['_lay_values']) / len(self.ff_cache[market_id][runner_id]['_lay_values'])

                    new_last = runner_change.get('trd')[0][0] if runner_change.get(
                        'trd') else self.ff_cache[market_id][runner_id]['last']
                    self.ff_cache[market_id][runner_id]['_last_values'].append(
                        new_last)
                    self.ff_cache[market_id][runner_id]['_last_moving_avg'] = sum(
                        self.ff_cache[market_id][runner_id]['_last_values']) / len(self.ff_cache[market_id][runner_id]['_last_values'])

                    self.ff_cache[market_id][runner_id]['_back_min'] = min(
                        self.ff_cache[market_id][runner_id]['_back_values'])
                    self.ff_cache[market_id][runner_id]['_back_max'] = max(
                        self.ff_cache[market_id][runner_id]['_back_values'])

                    self.ff_cache[market_id][runner_id]['_lay_min'] = min(
                        self.ff_cache[market_id][runner_id]['_lay_values'])
                    self.ff_cache[market_id][runner_id]['_lay_max'] = max(
                        self.ff_cache[market_id][runner_id]['_lay_values'])

                    self.ff_cache[market_id][runner_id]['_last_min'] = min(
                        self.ff_cache[market_id][runner_id]['_last_values'])
                    self.ff_cache[market_id][runner_id]['_last_max'] = max(
                        self.ff_cache[market_id][runner_id]['_last_values'])

                    self.ff_cache[market_id][runner_id]['back'] = runner_change.get(
                        'atb')[0][0] if runner_change.get('atb') else self.ff_cache[market_id][runner_id]['back']
                    self.ff_cache[market_id][runner_id]['lay'] = runner_change.get(
                        'atl')[0][0] if runner_change.get('atl') else self.ff_cache[market_id][runner_id]['lay']
                    self.ff_cache[market_id][runner_id]['last'] = runner_change.get(
                        'trd')[0][0] if runner_change.get('trd') else self.ff_cache[market_id][runner_id]['last']
                    trd_value = runner_change.get('trd')
                    if trd_value is not None:
                        self.ff_cache[market_id][runner_id]['volume'] = trd_value[0][1] + \
                            self.ff_cache[market_id][runner_id]['last']
                    else:
                        self.ff_cache[market_id][runner_id]['volume'] = self.ff_cache[market_id][runner_id]['last']

                    self.last_cache[market_id][runner_id]['back'] = runner_change.get(
                        'atb')[0][0] if runner_change.get('atb') else None
                    self.last_cache[market_id][runner_id]['lay'] = runner_change.get(
                        'atl')[0][0] if runner_change.get('atl') else None
                    self.last_cache[market_id][runner_id]['last'] = runner_change.get(
                        'trd')[0][0] if runner_change.get('trd') else None

                    self.ff_cache[market_id][runner_id]['_horse_info'] = self.horse_info_dict.get(
                        runner_name)

                    self.ff_cache[market_id]['_lay_overrun'] = overrun_lay = self.get_market_sum(
                        market_id, 'lay')
                    self.ff_cache[market_id]['_back_overrun'] = overrun_back = self.get_market_sum(
                        market_id, 'back')
                    self.ff_cache[market_id]['_last_overrun'] = overrun_last = self.get_market_sum(
                        market_id, 'last')
                    self.ff_cache[market_id]['_seconds_to_start'] = secs_to_start

                    flattened_data = {
                        # divide by 1000 to convert from milliseconds to seconds
                        'pt': datetime.fromtimestamp(data.get('pt')/1000) if data.get('pt') else None,
                        'meta': {
                            'market_id': market_id,
                            'runner_id': runner_id,
                            'runner_name': runner_name,
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
                        'cumulative_volume': self.ff_cache[market_id][runner_id]['volume'] if self.ff_cache[market_id][runner_id]['volume'] else None,
                        # 'forward_fills': self.ff_cache[market_id],
                    }
                    print (flattened_data)
                    # if data.get('clk') != 'AAAAAAAA' and SECS_MAX_RACE_DURATION > flattened_data['meta']['secs_to_start'] > -SECS_TO_START_FILTER:
                    #     print(flattened_data)
                    if SAVE_TICKDATA_TO_MONGO:
                        tickdata_collection.insert_one(flattened_data)

    def get_market_sum(self, market_id, field_name):
        total_sum = 0
        for horse_id, data in self.ff_cache[market_id].items():
            if horse_id[0] == '_':
                continue
            value = data[field_name]
            if value:  # prevent division by zero
                total_sum += (1 / value)
        return total_sum


def vwap(data):
    """
    Calculates the Volume Weighted Average Price (VWAP) of a given set of data.

    Args:
        data (list): A list of tuples containing price and volume data.

    Returns:
        float: The VWAP of the given data.
    """
    data = np.array(data)
    prices = data[:, 0]
    volumes = data[:, 1]
    total_volume = np.sum(volumes)
    if total_volume == 0:
        return np.nan
    res = np.sum(prices * volumes) / total_volume
    return res
