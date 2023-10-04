import copy
import threading
from datetime import datetime

import numpy as np
import pandas as pd
import pytz

from betfair.betting import place_order, price_adjustment
from betfair.config import orders_collection
import logging

log = logging.getLogger(__name__)

class StrategyHandler:
    def __init__(self) -> None:
        pass

    def check_execute(self, last, ff, strategies) -> bool:
        lock = threading.Lock()
        with lock:
            ff_copy = copy.copy(ff)

        for _, strategy in strategies.items():
            strategy_name = strategy.get('StrategyName', 'Unknown')
            bet_size = strategy.get('betSize', 0)
            bet_type = strategy.get('betType', 'Lay').upper()
            max_horses_to_bet = strategy.get('maxHorsesToBet', 1)
            max_horses_to_bet_strategy = strategy.get(
                'maxHorsesToBetStrategy', '')
            persistent_type = 'LAPSE'
            price_strategy = strategy.get('priceStrategy', 'last')
            active = strategy.get('active', 'off')
            price_max_value = strategy.get('priceMaxValue', 1000)
            price_min_value = strategy.get('priceMinValue', 1.01)
            min_last_total_odds = strategy.get('minLastTotalOdds', 1.01)
            max_last_total_odds = strategy.get('maxLastTotalOdds', 1000)
            min_back_total_odds = strategy.get('minBackTotalOdds', 1.01)
            max_back_total_odds = strategy.get('maxBackTotalOdds', 1000)
            min_lay_total_odds = strategy.get('minLayTotalOdds', 1.01)
            max_lay_total_odds = strategy.get('maxLayTotalOdds', 1000)

            for market_id, race_data in ff_copy.items():
                with lock:
                    race_data2 = copy.copy(race_data)
                if (strategy['secsToStartSlider'][0] > -race_data2['_seconds_to_start'] > strategy['secsToStartSlider'][1]):
                    continue
                order_found = False
                # log.info (f"Checking {market_id} at timestamp {datetime.now().isoformat()}")
                # update seconds
                # create dataframe for further manipulation

                if '_orders' in race_data2:
                    del race_data2['_orders']
                df = pd.DataFrame(race_data2).T

                # try:
                last_total_odds = df.loc['_last_overrun'].iloc[0]
                back_total_odds = df.loc['_back_overrun'].iloc[0]
                lay_total_odds = df.loc['_lay_overrun'].iloc[0]
                # except:
                #     last_total_odds = np.nan
                #     back_total_odds = np.nan
                #     lay_total_odds = np.nan

                if min_last_total_odds > last_total_odds > max_last_total_odds:
                    continue
                if min_back_total_odds > back_total_odds > max_back_total_odds:
                    continue
                if min_lay_total_odds > lay_total_odds > max_lay_total_odds:
                    continue

                df = df.loc[~df.index.str.startswith('_')]

                ascending = True if max_horses_to_bet_strategy == 'lowest odds first' else False
                df = df.sort_values(price_strategy, ascending=ascending)
                df = df.head(int(max_horses_to_bet))

                for selection_id, horse in df.iterrows():

                    # check for selected conditions in strategy
                    condition_met = True
                    horse_info_dict = horse['_horse_info']
                    for strategy_item in strategy:   # can be limited to condition items
                        if not ('min' in strategy_item and 'max' in strategy_item):
                            continue
                        if strategy_item not in horse_info_dict:
                            continue
                        if float(strategy_item['min']) > float(horse_info_dict[strategy_item]) > float(strategy_item['max']):
                            condition_met = False

                    if not condition_met:
                        continue

                    price = horse[price_strategy]
                    price = min(max(price, float(price_min_value)),
                                float(price_max_value))
                    price = price_adjustment(price)

                    if active in ['dummy', 'on']:
                        # check we have no order for that horse already
                        orders = ff[market_id]['_orders']
                        if orders:
                            for order in orders:
                                if order['selection_id'] == selection_id:
                                    # log.info(f"Already have an order for {selection_id} in {market_id}")
                                    order_found = True
                            if order_found:
                                continue
                        
                        status, bet_id, average_price_matched = 'dummy', 'dummy', 'dummy'
                        if active == 'on':
                            log.info({f"Sending to betfair: {strategy_name} {bet_type} {bet_size} {price} {selection_id} {market_id}"})
                            status, bet_id, average_price_matched = place_order(market_id, selection_id, bet_size, price,
                                        side=bet_type, persistence_type=persistent_type)
                            
                        order = {'strategy_name': strategy_name,
                                 'size': bet_size,
                                 'selection_id': selection_id,
                                 'price': price,
                                 'side': bet_type,
                                 'persistence_type': persistent_type,
                                 'timestamp': datetime.now().isoformat(),
                                 'seconds_to_start': -race_data2['_seconds_to_start'],
                                 'status': status,
                                 'bet_id': bet_id,
                                 'average_price_matched': average_price_matched,
                                 }
                        log.info(f"Placed order: {order}")
                        if isinstance(ff[market_id]['_orders'], list):
                            ff[market_id]['_orders'].append(order)
                        else:
                            ff[market_id]['_orders'] = [order]
                        orders_collection.insert_one(copy.copy(order))

    def check_modify(self, last, ff, strategies):
        pass
