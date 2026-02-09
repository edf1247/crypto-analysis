"""
Unit tests for Take Profit / Stop Loss functionality in backtest engine.
"""
import sys
from pathlib import Path
# Add project root to Python path to allow importing backtest module
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))
print(f"Project root: {project_root}")
print(f"sys.path[0]: {sys.path[0]}")

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from backtest.core import BacktestEngine, Strategy, OrderSide

class DummyStrategy(Strategy):
    """Simple strategy that opens a long position on first bar."""
    def next(self):
        if self.current_idx == 0:
            # Buy 1 unit at current price
            self.buy(1.0)

def generate_test_data(start_price=100, periods=10, price_changes=None):
    """Generate synthetic OHLC data."""
    if price_changes is not None:
        prices = [start_price]
        for change in price_changes:
            prices.append(prices[-1] * (1 + change/100))
    else:
        prices = [start_price * (1 + i * 0.01) for i in range(periods)]  # 1% increase each period

    dates = [datetime.now() + timedelta(minutes=5*i) for i in range(len(prices))]
    data = pd.DataFrame({
        'open': prices,
        'high': [p * 1.01 for p in prices],
        'low': [p * 0.99 for p in prices],
        'close': prices,
        'volume': [1000] * len(prices)
    }, index=dates)
    return data

def test_take_profit_triggers():
    """Test that take profit closes position when price reaches target."""
    # Four bars: price 100, 100, 105, 105 (5% increase after position opened)
    data = generate_test_data(start_price=100, periods=4, price_changes=[0, 5, 0])

    strategy = DummyStrategy(take_profit_pct=5.0, stop_loss_pct=None)
    engine = BacktestEngine(data=data, strategy=strategy, initial_capital=10000)
    results = engine.run()

    trades = results['trades']
    assert len(trades) == 2, f"Expected 2 trades, got {len(trades)}: {trades}"
    assert trades[0].side == OrderSide.BUY
    assert trades[1].side == OrderSide.SELL
    # Entry price should be 100 (filled at second bar), exit price ~105
    entry_price = trades[0].price
    exit_price = trades[1].price
    # TP triggered, exit price should be higher than entry
    assert exit_price > entry_price
    # Percentage increase approximately 5%
    pct_increase = (exit_price - entry_price) / entry_price * 100
    assert abs(pct_increase - 5.0) < 0.1  # within 0.1% tolerance

def test_stop_loss_triggers():
    """Test that stop loss closes position when price drops below threshold."""
    # Four bars: price 100, 100, 97, 97 (3% decrease after position opened)
    data = generate_test_data(start_price=100, periods=4, price_changes=[0, -3, 0])

    strategy = DummyStrategy(take_profit_pct=None, stop_loss_pct=3.0)
    engine = BacktestEngine(data=data, strategy=strategy, initial_capital=10000)
    results = engine.run()

    trades = results['trades']
    assert len(trades) == 2, f"Expected 2 trades, got {len(trades)}: {trades}"
    assert trades[0].side == OrderSide.BUY
    assert trades[1].side == OrderSide.SELL
    entry_price = trades[0].price
    exit_price = trades[1].price
    # SL triggered, exit price should be lower than entry
    assert exit_price < entry_price
    pct_decrease = (entry_price - exit_price) / entry_price * 100
    assert abs(pct_decrease - 3.0) < 0.1

def test_tp_sl_disabled():
    """Test that TP/SL can be disabled (None)."""
    data = generate_test_data(start_price=100, periods=5)
    strategy = DummyStrategy(take_profit_pct=None, stop_loss_pct=None)
    engine = BacktestEngine(data=data, strategy=strategy, initial_capital=10000)
    results = engine.run()
    # Since dummy strategy only buys on first bar, position should stay open
    # No sell trade because no TP/SL and strategy doesn't sell
    trades = results['trades']
    assert len(trades) == 1  # only buy
    assert trades[0].side == OrderSide.BUY

def test_tp_sl_both_set():
    """Test that whichever triggers first closes position."""
    # Price goes up 2% then down 4%: TP 5% not reached, SL 3% should trigger on second down?
    # Actually we need more granular test.
    pass