import copy
from datetime import datetime

import pandas as pd
import numpy as np
import pytz

from betfair.betting import place_order, price_adjustment
from betfair.config import orders_collection


class Strateegy1:
    def __init__(self) -> None:
        pass

    def check_execute(self, last, ff, orders) -> bool:

        for market_id, race_data in ff.items():

            # update seconds
            iso_format_string = ff[market_id]['_race_start_time']
            race_start_time = datetime.fromisoformat(iso_format_string)
            race_data['_seconds_to_start'] = (
                race_start_time - datetime.utcnow().replace(tzinfo=pytz.utc)).total_seconds()
            ff[market_id]['_seconds_to_start'] = race_data['_seconds_to_start']

            # create dataframe for further manipulation
            race_data2 = copy.deepcopy(race_data)
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
                if market_id in orders:
                    if orders[market_id]['selection_id'] == selection_id:
                        # print('already have an order for this horse')
                        continue

                order = {'size': size,
                         'selection_id': selection_id,
                         'price': price,
                         'side': side,
                         'persistence_type': persistent_type,
                         'timestamp': datetime.now(),
                         'seconds_to_start': race_data['_seconds_to_start'],
                         }
                orders[market_id] = order
                orders[market_id]['timestamp'] = datetime.now().isoformat()
                print(f"Placing order: {order}")
                if isinstance(ff[market_id]['_orders'], list):
                    ff[market_id]['_orders'].append(order)
                else:
                    ff[market_id]['_orders'] = [order]
                orders_collection.insert_one(order)
                place_order(market_id, selection_id, size, price,
                            side=side, persistence_type=persistent_type)

    def check_modify(self, last, ff, orders):
        pass
