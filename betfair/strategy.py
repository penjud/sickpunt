import copy
from datetime import datetime
import threading

import pandas as pd
import numpy as np
import pytz

from betfair.betting import place_order, price_adjustment
from betfair.config import orders_collection


class Strateegy1:
    def __init__(self) -> None:
        pass

    def check_execute(self, last, ff) -> bool:
        lock = threading.Lock()
        with lock:
            ff_copy = copy.copy(ff)
        for market_id, race_data in ff_copy.items():

            order_found = False
            # print (f"Checking {market_id} at timestamp {datetime.now().isoformat()}")
            # update seconds
            # create dataframe for further manipulation
            with lock:
                race_data2 = copy.copy(race_data)
            if '_orders' in race_data2:
                del race_data2['_orders']
            df = pd.DataFrame(race_data2).T

            try:
                last_overrun = df.loc['_last_overrun'].iloc[0]
                back_overrun = df.loc['_back_overrun'].iloc[0]
                lay_overrun = df.loc['_lay_overrun'].iloc[0]
            except:
                pass
            df = df.loc[~df.index.str.startswith('_')]

            size = 1
            side = 'BACK'
            persistent_type = 'LAPSE'

            df = df.sort_values('lay')
            highest_odds_selection_id = df.index[0]
            highest_odds_back_price = df.lay.iloc[0]
            highest_odds_lay_price = df.back.iloc[0]

            selection_id = highest_odds_selection_id
            price = np.mean([highest_odds_lay_price,highest_odds_back_price])

            if race_data['_seconds_to_start'] < -60:
                execute = True
            else:
                execute = False

            price = price_adjustment(price)

            if execute:
                # check we have no order for that horse already
                orders = ff[market_id]['_orders']
                if orders:
                    for order in orders:
                        if order['selection_id'] == selection_id:
                            # print(f"Already have an order for {selection_id} in {market_id}")
                            order_found = True

                    if order_found:
                        continue
                
                
                order = {'size': size,
                         'selection_id': selection_id,
                         'price': price,
                         'side': side,
                         'persistence_type': persistent_type,
                         'timestamp': datetime.now().isoformat(),
                         'seconds_to_start': race_data['_seconds_to_start'],
                         }
                print(f"Placing order: {order}")
                if isinstance(ff[market_id]['_orders'], list):
                    ff[market_id]['_orders'].append(order)
                else:
                    ff[market_id]['_orders'] = [order]
                orders_collection.insert_one(copy.copy(order))
                # place_order(market_id, selection_id, size, price,
                #             side=side, persistence_type=persistent_type)

    def check_modify(self, last, ff):
        pass
