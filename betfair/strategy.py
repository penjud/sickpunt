from datetime import datetime

import pandas as pd

from betfair.betting import place_order, price_adjustment
from betfair.config import orders_collection


class Strateegy1:
    def __init__(self) -> None:
        pass

    def check_execute(self, last, ff, orders) -> bool:

        for market_id, race_data in ff.items():
            df = pd.DataFrame(race_data).T

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
            price = highest_odds_lay_price

            if race_data['_seconds_to_start'] == 60:
                execute = True
            else:
                execute = False

            price = price_adjustment(price)

            if execute:
                order = {'size': size,
                         'selection_id': selection_id,
                         'price': price,
                         'side': side,
                         'persistence_type': persistent_type,
                         'timestamp': datetime.now(),
                         'seconds_to_start': race_data['_seconds_to_start'],
                         }
                orders[market_id] = order
                if isinstance(ff[market_id]['_orders'], list):
                    ff[market_id]['_orders'].append(order)
                else:
                    ff[market_id]['_orders'] = [order]
                orders_collection.insert_one(order)
                # place_order(market_id, selection_id, size, price,
                #             side=side, persistence_type=persistent_type)

    def check_modify(self, last, ff, orders):
        pass
