import asyncio
import copy
import logging
import re
import threading
from datetime import datetime

import numpy as np
import pandas as pd
import pytz

from betfair.betting import place_order, price_adjustment
from betfair.config import is_prod_computer, orders_collection
from betfair.mongo_manager import insert_order

log = logging.getLogger(__name__)
lock = asyncio.Lock()

def extract_real(value):
    # If value is already a float or int, return it
    if isinstance(value, (float, int)):
        return value
    
    # Extract only the digits and a single dot using regex
    num_str = ''.join(re.findall(r'[0-9.]', value))
    
    # Handle cases with multiple dots by keeping only the first one
    parts = num_str.split('.')
    if len(parts) > 2:
        num_str = parts[0] + '.' + ''.join(parts[1:])
    
    return float(num_str)

class StrategyHandler:
    def __init__(self) -> None:
        pass

    async def check_execute(self, last, ff, race_dict, runnerid_name_dict, strategies) -> bool:
        async with lock:
            ff_copy = copy.copy(ff)
            strategies_copy = copy.copy(strategies)

        users = ['default']
        for user in users:                
            for _, strategy in strategies_copy.items():
                user = strategy.get('user', 'default')
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
                strategy_market_type = strategy.get('market_type', 'WIN')
                harness_selection = strategy.get('harnessSelection', 'any')
                strategy_event_type = strategy.get('selectedSportType', 'Horse Racing').lower()

                for market_id, race_data in ff_copy.items():
                    update_strategy_status(
                        ff, market_id, strategy_name, comment='Processing...')
                    race_market_type = race_dict[market_id]['market_type']
                    async with lock:
                        race_data2 = copy.copy(race_data)
                        race_dict2 = copy.copy(race_dict)
                        
                    strategy_race_order_count = len(
                        [order for order in ff[market_id]['_orders'] if order.get('strategy_name') == strategy_name])
                    if strategy_race_order_count >= max_horses_to_bet:
                        update_strategy_status(
                            ff, market_id, strategy_name, comment=f'Already bet on {max_horses_to_bet} horses.')
                        continue
                    
                    if not race_data2['_seconds_to_start']:
                        continue  # data not yet available

                    country = race_dict2[market_id]['event']['countryCode']
                    strategy_countries = strategy['selectedCountries']
                    venue =  race_dict2[market_id]['event']['venue']
                    market_name =  race_dict2[market_id]['marketName']
                    full_title =  race_dict2[market_id]['fullTitle']
                    total_matched =  race_dict2[market_id]['totalMatched']
                    total_horses_num = len(race_dict2[market_id]['runners'])
                    event_type = race_dict2[market_id]['event_type']['name'].lower()
                    
                    if event_type!=strategy_event_type:
                        update_strategy_status(ff, market_id, strategy_name, comment=f'Strategy only for {strategy_event_type}.')
                        continue
                    
                    if strategy_market_type!=race_market_type:
                        update_strategy_status(ff, market_id, strategy_name, comment=f'Strategy only for {strategy_market_type}.')
                        continue
                                    
                    def is_harness(name):
                        name = name.lower()
                        return ('trot' in name.lower()) or ('pace' in name.lower())
                    is_harness = is_harness(full_title)
                    if harness_selection=='Harness only' and not is_harness:
                        update_strategy_status(ff, market_id, strategy_name, comment=f'Market {full_title} is not harness')
                        continue
                    elif harness_selection=='Non harness only' and is_harness:
                        update_strategy_status(ff, market_id, strategy_name, comment=f'Market {full_title} is harness')
                        continue
                    
                    if not country in strategy_countries:
                        update_strategy_status(
                            ff, market_id, strategy_name, comment=f'Country {country} not part of strategy countries {strategy_countries}')
                        continue

                    if not (strategy['secsToStartSlider'][0] <= -race_data2['_seconds_to_start'] <= strategy['secsToStartSlider'][1]):
                        update_strategy_status(
                            ff, market_id, strategy_name, comment='Time window not met')
                        continue

                    if '_orders' in race_data2:
                        del race_data2['_orders']
                    df = pd.DataFrame(race_data2).T

                    last_total_odds = df.loc['_last_overrun'].iloc[0]
                    back_total_odds = df.loc['_back_overrun'].iloc[0]
                    lay_total_odds = df.loc['_lay_overrun'].iloc[0]

                    df = df.loc[~df.index.str.startswith('_')]

                    ascending = True if max_horses_to_bet_strategy == 'highest odds first' else False
                    try:
                        df = df.sort_values(price_strategy, ascending=ascending)
                    except KeyError:
                        log.warning(f"Price strategy {price_strategy} not found in data")
                        update_strategy_status(ff, market_id, strategy_name, comment='Price strategy not found in data')
                        continue
                    
                    for selection_id, horse in df.iterrows():

                        # check for selected conditions in strategy
                        order_found = False
                        condition_met = True
                        horse_info_dict = horse['_horse_info'] if horse['_horse_info'] else {}
                        horse_info_dict['Horses per race'] = total_horses_num
                        horse_info_dict['Last Traded price'] = horse['last']
                        horse_info_dict['Current lay price'] = horse['lay']
                        horse_info_dict['Current back price'] = horse['back']
                        
                        horse_info_dict['Last total odds'] = last_total_odds
                        horse_info_dict['Back total odds'] = back_total_odds
                        horse_info_dict['Lay total odds'] = lay_total_odds
                        
                        try:
                            horse_name = runnerid_name_dict[int(selection_id)]
                        except KeyError:
                            horse_name = selection_id
                            
                        # max horses to bet per race restriction
                        strategy_race_order_count = len(
                            [order for order in ff[market_id]['_orders'] if order.get('strategy_name') == strategy_name])
                        if strategy_race_order_count >= max_horses_to_bet:
                            update_strategy_status(
                                ff, market_id, strategy_name, comment=f'Already bet on {max_horses_to_bet} horses.')
                            break
                        
                        # Check conditions
                        for item_name, item_value in strategy.items():
                            if not isinstance(item_value, dict): # can be limited to condition items
                                continue
                            if (not horse_info_dict) or (item_name not in horse_info_dict.keys()):
                                if strategy['missingConditionsData'] == "risk":
                                    continue
                                else:
                                    condition_met = False
                                    update_strategy_status(
                                        ff, market_id, strategy_name, selection_id, comment=f'{item_name} not found in data')
                                    break
                            
                            try:
                                
                                item_as_num = extract_real(horse_info_dict[item_name])
                                if not (float(item_value['min']) <= item_as_num <= float(item_value['max'])):
                                    condition_met = False
                                    update_strategy_status(
                                        ff, market_id, strategy_name, selection_id, comment=f'{item_name} condition not met {item_value["min"]} <= {round(item_as_num,2)} <= {item_value["max"]}')
                            except Exception as e:
                                log.warning(f"Error {item_name} not a number: {e}")
                                condition_met = False
                                update_strategy_status(
                                    ff, market_id, strategy_name, selection_id, comment=f'{item_name} not a number')
                            
                        if not condition_met:
                            continue

                        # check we have no order for that horse already
                        orders = ff[market_id]['_orders']
                        if orders:
                            for order in orders:
                                if order['selection_id'] == selection_id:
                                    order_found = True
                            if order_found:
                                update_strategy_status(
                                    ff, market_id, strategy_name, selection_id, comment='Order already placed')
                                update_strategy_status(
                                    ff, market_id, strategy_name, comment='Bets placed')
                                continue
                            
                        if active in ['dummy', 'on']:
                            price = horse[price_strategy]
                            price = min(max(price, float(price_min_value)),
                                    float(price_max_value))
                            price = price_adjustment(price)
                            status, bet_id, average_price_matched = 'dummy', 'dummy', 'dummy'
                            if active == 'on' and is_prod_computer():
                                log.debug(
                                    {f"Sending to betfair: {strategy_name} {bet_type} {bet_size} {price} {selection_id} {market_id}"})
                                status, bet_id, average_price_matched = place_order(market_id, selection_id, bet_size, price,
                                                                                    side=bet_type, persistence_type=persistent_type)

                            order = {'strategy_name': strategy_name,
                                    'event_type': event_type,
                                    'venue': venue,
                                    'market_type': strategy_market_type,
                                    'is_harness': is_harness,
                                    'country': country,
                                    'total_matched': total_matched,
                                    'market_id': market_id,
                                    'size': bet_size,
                                    'selection_id': selection_id,
                                    'horse_name': horse_name,
                                    'price': price,
                                    'last_traded': horse['last'],
                                    'last_lay': horse['lay'],
                                    'last_back': horse['back'],
                                    'side': bet_type,
                                    'persistence_type': persistent_type,
                                    'timestamp':  datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
                                    'seconds_to_start': -race_data2['_seconds_to_start'],
                                    'status': status,
                                    'bet_id': bet_id,
                                    'average_price_matched': average_price_matched,
                                    'market_name': market_name,
                                    'user': user
                                    }
                            log.debug(f"Placed order: {order}")
                            if isinstance(ff[market_id]['_orders'], list):
                                ff[market_id]['_orders'].append(order)
                            else:
                                ff[market_id]['_orders'] = [order]
                            await insert_order(copy.copy(order))

    async def check_modify(self, last, ff, race_dict, runnerid_name_dict, strategies):
        pass


def update_strategy_status(ff, market_id, strategy_name, selection_id=None, comment=None):
    if selection_id:
        ff[market_id][selection_id]['_strategy_status'] = comment
    else:
        ff[market_id]['_strategy_status'][strategy_name] = comment
