import copy
import threading
from datetime import datetime

import numpy as np
import pandas as pd
import pytz
from betfair.config import is_prod_computer

from betfair.betting import place_order, price_adjustment
from betfair.config import orders_collection
import logging

log = logging.getLogger(__name__)


class StrategyHandler:
    def __init__(self) -> None:
        pass

    def check_execute(self, last, ff, race_dict, runnerid_name_dict, strategies) -> bool:
        lock = threading.Lock()
        with lock:
            ff_copy = copy.copy(ff)
            strategies_copy = copy.copy(strategies)
        for _, strategy in strategies_copy.items():
            strategy_name = strategy.get('StrategyName', 'Unknown')
            bet_size = strategy.get('betSize', 0)
            bet_type = strategy.get('betType', 'Lay').upper()
            max_horses_to_bet = int(strategy.get('maxHorsesToBet', 1))
            max_horses_to_bet_strategy = strategy.get(
                'maxHorsesToBetStrategy', '')
            persistent_type = 'LAPSE'
            price_strategy = strategy.get('priceStrategy', 'last')
            active = strategy.get('active', 'off')
            price_max_value = strategy.get('priceMaxValue', 1000)
            price_min_value = strategy.get('priceMinValue', 1.01)
            min_last_total_odds = strategy.get('minLastTotalOdds', 0)
            max_last_total_odds = strategy.get('maxLastTotalOdds', 1000)
            min_back_total_odds = strategy.get('minBackTotalOdds', 0)
            max_back_total_odds = strategy.get('maxBackTotalOdds', 1000)
            min_lay_total_odds = strategy.get('minLayTotalOdds', 0)
            max_lay_total_odds = strategy.get('maxLayTotalOdds', 1000)

            for market_id, race_data in ff_copy.items():
                strategy_race_order_count = len([order for order in ff_copy[market_id]['_orders'] if order.get('strategy_name') == strategy_name])
                if strategy_race_order_count>=max_horses_to_bet:
                    update_strategy_status(
                        ff, market_id, strategy_name, comment=f'Already bet on {max_horses_to_bet} horses.')
                    continue
                
                with lock:
                    race_data2 = copy.copy(race_data)
                    race_dict2 = copy.copy(race_dict)
                
                if not race_data2['_seconds_to_start']:
                    continue  # data not yet available
                
                country = race_dict2[market_id]['event']['countryCode']
                strategy_countries = strategy['selectedCountries']
                if not country in strategy_countries:
                    update_strategy_status(
                        ff, market_id, strategy_name, comment=f'Country {country} not part of strategy countries {strategy_countries}')
                    continue
                
                if not (strategy['secsToStartSlider'][0] <= -race_data2['_seconds_to_start'] <= strategy['secsToStartSlider'][1]):
                    update_strategy_status(
                        ff, market_id, strategy_name, comment='Time window not met')
                    continue
                order_found = False

                if '_orders' in race_data2:
                    del race_data2['_orders']
                df = pd.DataFrame(race_data2).T

                last_total_odds = df.loc['_last_overrun'].iloc[0]
                back_total_odds = df.loc['_back_overrun'].iloc[0]
                lay_total_odds = df.loc['_lay_overrun'].iloc[0]
                
                try:
                    if not(float(min_last_total_odds) <= last_total_odds <= float(max_last_total_odds)):
                        update_strategy_status(ff, market_id, strategy_name, comment=f'Total last odds {last_total_odds} outside of allowed window')
                        continue
                    if not(float(min_back_total_odds) <= back_total_odds <= float(max_back_total_odds)):
                        update_strategy_status(ff, market_id, strategy_name, comment=f'Total back odds {back_total_odds} outside of allowed window')
                        continue
                    if not(float(min_lay_total_odds) <= lay_total_odds <= float(max_lay_total_odds)):
                        update_strategy_status(ff, market_id, strategy_name, comment=f'Total lay odds {lay_total_odds} outside of allowed window')
                        continue
                except ValueError as err:
                    log.warning(err)
                    update_strategy_status(ff, market_id, strategy_name, comment='Value Error in min/max total odds. Check the values')
                    continue

                df = df.loc[~df.index.str.startswith('_')]

                ascending = True if max_horses_to_bet_strategy == 'lowest odds first' else False
                try:
                    df = df.sort_values(price_strategy, ascending=ascending)
                except KeyError:
                    log.warning(f"Price strategy {price_strategy} not found in data")
                    update_strategy_status(ff, market_id, strategy_name, comment='Price strategy not found in data')
                    continue
                
                df = df.head(max_horses_to_bet)

                for selection_id, horse in df.iterrows():

                    # check for selected conditions in strategy
                    condition_met = True
                    horse_info_dict = horse['_horse_info']
                    for strategy_item in strategy:   # can be limited to condition items
                        if not ('min' in strategy_item and 'max' in strategy_item):
                            continue
                        if strategy_item not in horse_info_dict:
                            if strategy['missingConditionsData'] == "risk":
                                continue
                            else:
                                condition_met = False
                                update_strategy_status(
                                    ff, market_id, strategy_name, selection_id, comment=f'{strategy_item} not found in data')
                                break
                            
                        if not (float(strategy_item['min']) <= float(horse_info_dict[strategy_item]) <= float(strategy_item['max'])):
                            condition_met = False
                            update_strategy_status(
                                ff, market_id, strategy_name, selection_id, comment=f'{strategy_item} condition not met')

                    if not condition_met:
                        continue

                    price = horse[price_strategy]
                    price = min(max(price, float(price_min_value)), float(price_max_value))
                    price = price_adjustment(price)
                    
                    try:
                        horse_name = runnerid_name_dict[int(selection_id)]
                    except KeyError:
                        horse_name = selection_id

                    if active in ['dummy', 'on']:
                        # check we have no order for that horse already
                        orders = ff[market_id]['_orders']
                        if orders:
                            for order in orders:
                                if order['selection_id'] == selection_id:
                                    # log.info(f"Already have an order for {selection_id} in {market_id}")
                                    order_found = True
                            if order_found:
                                update_strategy_status(ff, market_id, strategy_name, selection_id, comment='Order already placed')
                                continue

                        status, bet_id, average_price_matched = 'dummy', 'dummy', 'dummy'
                        if active == 'on' and is_prod_computer():
                            log.info(
                                {f"Sending to betfair: {strategy_name} {bet_type} {bet_size} {price} {selection_id} {market_id}"})
                            status, bet_id, average_price_matched = place_order(market_id, selection_id, bet_size, price,
                                                                                side=bet_type, persistence_type=persistent_type)

                        order = {'strategy_name': strategy_name,
                                 'size': bet_size,
                                 'selection_id': selection_id,
                                 'horse_name': horse_name,
                                 'price': price,
                                 'side': bet_type,
                                 'persistence_type': persistent_type,
                                 'timestamp': datetime.now().isoformat()[:19],
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

    def check_modify(self, last, ff, race_dict, runnerid_name_dict, strategies):
        pass


def update_strategy_status(ff, market_id, strategy_name, selection_id=None, comment=None):
    if selection_id:
        ff[market_id][selection_id]['_strategy_status'] = comment
    else:
        ff[market_id]['_strategy_status'][strategy_name] = comment
