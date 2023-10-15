"""Orchestration of placing and administering bets."""
import betfairlightweight
import numpy as np
from betfairlightweight import filters

from betfair.config import client, tick_sizes

# create trading instance
trading = client


def create_ladder():
    raw_ladder = np.concatenate(list(map(lambda x: np.arange(*x), tick_sizes)))
    return np.round(raw_ladder, 10)


price_ladder = create_ladder()


def price_adjustment(price):
    i = 0
    while i < len(price_ladder) and price_ladder[i] < price:
        i += 1
    if i >= len(price_ladder):
        return None  # or any suitable value to indicate that `price` is out of ladder range
    return round(price_ladder[i], 2)


async def place_order(market_id, selection_id, size, price, side='LAY', persistence_type='LAPSE'):
    # placing an order
    limit_order = filters.limit_order(
        size=size, price=price, persistence_type=persistence_type)
    instruction = filters.place_instruction(
        order_type="LIMIT",
        selection_id=selection_id,
        side=side,
        limit_order=limit_order,
    )
    place_orders = trading.betting.place_orders(
        market_id=market_id, instructions=[instruction]  # list
    )

    print(place_orders.status)
    for order in place_orders.place_instruction_reports:
        print(
            "Status: %s, BetId: %s, Average Price Matched: %s "
            % (order.status, order.bet_id, order.average_price_matched)
        )
    return order.status, order.bet_id, order.average_price_matched


def update_order(bet_id, market_id):
    # updating an order
    instruction = filters.update_instruction(
        bet_id=bet_id, new_persistence_type="PERSIST"
    )
    update_order = trading.betting.update_orders(
        market_id=market_id, instructions=[instruction]
    )

    print(update_order.status)
    for order in update_order.update_instruction_reports:
        print("Status: %s" % order.status)


def replace_order(bet_id, market_id, new_price):
    # replacing an order
    instruction = filters.replace_instruction(
        bet_id=bet_id, new_price=new_price)
    replace_order = trading.betting.replace_orders(
        market_id=market_id, instructions=[instruction]
    )

    print(replace_order.status)
    for order in replace_order.replace_instruction_reports:
        place_report = order.place_instruction_reports
        cancel_report = order.cancel_instruction_reports
        print(
            "Status: %s, New BetId: %s, Average Price Matched: %s "
            % (order.status, place_report.bet_id, place_report.average_price_matched)
        )


def cancel_order(bet_id, market_id, size_reduction):
    # cancelling an order
    instruction = filters.cancel_instruction(
        bet_id=bet_id, size_reduction=size_reduction)
    cancel_order = trading.betting.cancel_orders(
        market_id=market_id, instructions=[instruction]
    )

    print(cancel_order.status)
    for cancel in cancel_order.cancel_instruction_reports:
        print(
            "Status: %s, Size Cancelled: %s, Cancelled Date: %s"
            % (cancel.status, cancel.size_cancelled, cancel.cancelled_date)
        )
