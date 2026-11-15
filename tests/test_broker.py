import pytest
from tradingbot.broker.paper import PaperBroker


def test_buy_reduces_cash():
    b = PaperBroker(cash=10_000, fee=0.0)
    b.buy(price=100, qty=10)
    assert b.cash == 9_000.0
    assert b.position.qty == 10.0
    assert b.position.entry_price == 100.0


def test_sell_restores_cash():
    b = PaperBroker(cash=10_000, fee=0.0)
    b.buy(price=100, qty=10)
    b.sell(price=110, qty=10)
    assert b.cash == 10_100.0
    assert b.position.qty == 0.0
    assert b.position.is_open is False


def test_fee_applied_on_buy():
    b = PaperBroker(cash=10_000, fee=0.01)
    b.buy(price=100, qty=10)
    # cost = 1000, fee = 10 → cash = 8990
    assert b.cash == pytest.approx(8_990.0)


def test_fee_applied_on_sell():
    b = PaperBroker(cash=10_000, fee=0.01)
    b.buy(price=100, qty=10)
    cash_after_buy = b.cash
    b.sell(price=100, qty=10)
    # proceeds = 1000, fee = 10 → gains back 990
    assert b.cash == pytest.approx(cash_after_buy + 990.0)


def test_buy_more_than_cash_is_ignored():
    b = PaperBroker(cash=100, fee=0.0)
    b.buy(price=200, qty=10)
    assert b.position.qty == 0.0
    assert b.cash == 100.0


def test_sell_more_than_held_caps_at_held():
    b = PaperBroker(cash=10_000, fee=0.0)
    b.buy(price=100, qty=5)
    b.sell(price=100, qty=99)
    assert b.position.qty == 0.0


def test_equity_includes_position():
    b = PaperBroker(cash=5_000, fee=0.0)
    b.buy(price=100, qty=10)
    # cash = 5000 - 1000 = 4000, position = 10 * 150 = 1500 → equity = 5500
    assert b.equity(price=150) == pytest.approx(5_500.0)


def test_average_entry_price_on_multiple_buys():
    b = PaperBroker(cash=10_000, fee=0.0)
    b.buy(price=100, qty=5)
    b.buy(price=200, qty=5)
    # avg = (500 + 1000) / 10 = 150
    assert b.position.entry_price == pytest.approx(150.0)
    assert b.position.qty == 10.0
