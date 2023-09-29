"""Orchestration of placing and administering bets."""
import betfairlightweight
from betfairlightweight import filters
import numpy as np
from betfair.config import client

# create trading instance
trading = client

tick_sizes = [(1.01, 2, 0.01),
              (2.02, 3, 0.02),
              (3.05, 4, 0.05),
              (4.1, 6, 0.1),
              (6.2, 10, 0.2),
              (10.5, 20, 0.5),
              (21, 30, 1.),
              (32, 50, 2.),
              (55, 100, 5.),
              (110, 1000, 10.)]

def create_ladder():
    return np.concatenate(list(map(lambda x: np.arange(*x), tick_sizes)))

price_ladder = create_ladder()

def price_adjustment(price):
    i = 0
    while price_ladder[i] < price:
        i += 1
    return float(str(round(price_ladder[i], 2)))


def place_order(market_id, selection_id, size, price, side='LAY', persistence_type='LAPSE'):
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
