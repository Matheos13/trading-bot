from tradingbot.risk.manager import RiskManager


def test_position_size_basic():
    rm = RiskManager(risk_per_trade=0.02, stop_loss_pct=0.05)
    # risk $200 on a $10k account, stop is 5% of price → size = 200 / (100*0.05) = 40
    size = rm.position_size(equity=10_000, price=100)
    assert size == 40.0


def test_position_size_zero_price():
    rm = RiskManager()
    assert rm.position_size(equity=10_000, price=0) == 0.0


def test_stop_price():
    rm = RiskManager(stop_loss_pct=0.10)
    assert rm.stop_price(100) == 90.0


def test_stop_hit_true():
    rm = RiskManager(stop_loss_pct=0.10)
    assert rm.stop_hit(entry_price=100, current_price=89) is True


def test_stop_hit_false():
    rm = RiskManager(stop_loss_pct=0.10)
    assert rm.stop_hit(entry_price=100, current_price=95) is False


def test_stop_hit_exactly_at_stop():
    rm = RiskManager(stop_loss_pct=0.10)
    assert rm.stop_hit(entry_price=100, current_price=90) is True
