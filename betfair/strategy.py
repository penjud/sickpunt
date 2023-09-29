from betfair.betting import place_order


class Strateegy1:
    def __init__(self) -> None:
        pass

    def check_execute(self, last, ff) -> bool:
        execute = False
        market_id = None
        selection_id = None
        size = None
        price = None

        if execute:
            place_order(market_id, selection_id, size, price,
                        side='LAY', persistence_type='LAPSE')

    def check_modify(self, last, ff):
        pass
