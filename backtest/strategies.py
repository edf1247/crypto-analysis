"""
Example trading strategies for the backtesting framework.
"""

import pandas as pd
import numpy as np
from typing import Optional

from .core import Strategy, OrderSide


class BuyAndHold(Strategy):
    """Simple buy and hold strategy."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bought = False

    def next(self):
        if not self.bought:
            # Invest all capital
            size = self.portfolio.cash / self.current_price
            self.buy(size)
            self.bought = True


class SmaCrossover(Strategy):
    """Simple Moving Average crossover strategy."""

    def __init__(self, fast: int = 20, slow: int = 50, position_size: float = 0.95, **kwargs):
        super().__init__(**kwargs)
        self.fast = fast
        self.slow = slow
        self.position_size = position_size
        self.prev_signal = 0

    def next(self):
        if self.current_idx < self.slow:
            return

        # Calculate moving averages
        data = self.get_ohlc(self.slow + 5)
        sma_fast = data['close'].rolling(self.fast).mean().iloc[-1]
        sma_slow = data['close'].rolling(self.slow).mean().iloc[-1]

        # Current position
        position_size = self.portfolio.get_position_size("BTC-USD")

        # Generate signal
        signal = 1 if sma_fast > sma_slow else -1

        # Trading logic
        if signal == 1 and position_size <= 0:
            # Buy signal - close any short and go long
            if position_size < 0:
                self.buy(abs(position_size) * 2)  # Close short and open long
            else:
                size = (self.portfolio.cash * self.position_size) / self.current_price
                self.buy(size)

        elif signal == -1 and position_size >= 0:
            # Sell signal - close any long and go short (if allowed)
            if position_size > 0:
                self.sell(position_size * 2)  # Close long and open short

        self.prev_signal = signal


class RSIStrategy(Strategy):
    """RSI-based mean reversion strategy."""

    def __init__(
        self,
        period: int = 14,
        oversold: float = 30,
        overbought: float = 70,
        position_size: float = 0.2,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
        self.position_size = position_size
        self.in_position = False

    def next(self):
        if self.current_idx < self.period + 1:
            return

        # Calculate RSI
        data = self.get_ohlc(self.period + 10)
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1]

        position_size = self.portfolio.get_position_size("BTC-USD")

        # Buy when oversold
        if current_rsi < self.oversold and position_size <= 0:
            if position_size < 0:
                self.buy(abs(position_size))  # Close short
            size = (self.portfolio.cash * self.position_size) / self.current_price
            self.buy(size)
            self.in_position = True

        # Sell when overbought
        elif current_rsi > self.overbought and position_size >= 0:
            if position_size > 0:
                self.sell(position_size)
            self.in_position = False


class BollingerBandsStrategy(Strategy):
    """Bollinger Bands mean reversion strategy."""

    def __init__(
        self,
        period: int = 20,
        std_dev: float = 2.0,
        position_size: float = 0.25,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.period = period
        self.std_dev = std_dev
        self.position_size = position_size

    def next(self):
        if self.current_idx < self.period:
            return

        # Calculate Bollinger Bands
        data = self.get_ohlc(self.period + 5)
        sma = data['close'].rolling(self.period).mean()
        std = data['close'].rolling(self.period).std()
        upper = sma + (std * self.std_dev)
        lower = sma - (std * self.std_dev)

        current_price = self.current_price
        current_upper = upper.iloc[-1]
        current_lower = lower.iloc[-1]
        current_sma = sma.iloc[-1]

        position_size = self.portfolio.get_position_size("BTC-USD")

        # Buy when price touches lower band
        if current_price <= current_lower and position_size <= 0:
            if position_size < 0:
                self.buy(abs(position_size))
            size = (self.portfolio.cash * self.position_size) / current_price
            self.buy(size)

        # Sell when price touches upper band
        elif current_price >= current_upper and position_size >= 0:
            if position_size > 0:
                self.sell(position_size)

        # Exit at middle band if in profit
        elif position_size != 0:
            if position_size > 0 and current_price >= current_sma:
                self.sell(position_size)
            elif position_size < 0 and current_price <= current_sma:
                self.buy(abs(position_size))


class MACDStrategy(Strategy):
    """MACD trend following strategy."""

    def __init__(
        self,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9,
        position_size: float = 0.9,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.fast = fast
        self.slow = slow
        self.signal = signal
        self.position_size = position_size
        self.prev_macd = None
        self.prev_signal_line = None

    def next(self):
        if self.current_idx < self.slow + self.signal:
            return

        # Calculate MACD
        data = self.get_ohlc(self.slow + self.signal + 10)
        ema_fast = data['close'].ewm(span=self.fast, adjust=False).mean()
        ema_slow = data['close'].ewm(span=self.slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=self.signal, adjust=False).mean()

        current_macd = macd_line.iloc[-1]
        current_signal = signal_line.iloc[-1]
        prev_macd = macd_line.iloc[-2]
        prev_signal = signal_line.iloc[-2]

        position_size = self.portfolio.get_position_size("BTC-USD")

        # Bullish crossover
        if prev_macd < prev_signal and current_macd > current_signal and position_size <= 0:
            if position_size < 0:
                self.buy(abs(position_size))
            size = (self.portfolio.cash * self.position_size) / self.current_price
            self.buy(size)

        # Bearish crossover
        elif prev_macd > prev_signal and current_macd < current_signal and position_size >= 0:
            if position_size > 0:
                self.sell(position_size)


class GridTradingStrategy(Strategy):
    """Grid trading strategy for sideways markets."""

    def __init__(
        self,
        grid_levels: int = 10,
        grid_spacing: float = 0.02,  # 2% between grids
        position_per_grid: float = 0.1,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.grid_levels = grid_levels
        self.grid_spacing = grid_spacing
        self.position_per_grid = position_per_grid
        self.grids: list = []
        self.initialized = False

    def next(self):
        if not self.initialized and self.current_idx >= 20:
            # Initialize grid around current price
            current_price = self.current_price
            self.grids = []

            for i in range(-self.grid_levels // 2, self.grid_levels // 2 + 1):
                grid_price = current_price * (1 + i * self.grid_spacing)
                self.grids.append({
                    'price': grid_price,
                    'bought': False,
                    'sold': False
                })
            self.initialized = True

        if not self.initialized:
            return

        current_price = self.current_price

        for grid in self.grids:
            # Buy when price drops to grid level
            if not grid['bought'] and current_price <= grid['price'] * 1.005:
                size = (self.portfolio.cash * self.position_per_grid) / current_price
                if size > 0:
                    self.buy(size)
                    grid['bought'] = True
                    grid['sold'] = False

            # Sell when price rises above grid level
            elif grid['bought'] and not grid['sold'] and current_price >= grid['price'] * 1.01:
                position = self.portfolio.get_position_size("BTC-USD")
                sell_size = (self.initial_capital * self.position_per_grid) / grid['price']
                if position >= sell_size > 0:
                    self.sell(sell_size)
                    grid['sold'] = True
                    grid['bought'] = False


class TrailingStopStrategy(Strategy):
    """Strategy with trailing stop loss."""

    def __init__(
        self,
        entry_sma_fast: int = 10,
        entry_sma_slow: int = 30,
        trailing_pct: float = 0.05,
        position_size: float = 0.9,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.entry_sma_fast = entry_sma_fast
        self.entry_sma_slow = entry_sma_slow
        self.trailing_pct = trailing_pct
        self.position_size = position_size
        self.highest_price: Optional[float] = None
        self.stop_price: Optional[float] = None

    def next(self):
        if self.current_idx < self.entry_sma_slow:
            return

        data = self.get_ohlc(self.entry_sma_slow + 5)
        sma_fast = data['close'].rolling(self.entry_sma_fast).mean().iloc[-1]
        sma_slow = data['close'].rolling(self.entry_sma_slow).mean().iloc[-1]

        position_size = self.portfolio.get_position_size("BTC-USD")
        current_price = self.current_price

        # Entry logic
        if position_size <= 0 and sma_fast > sma_slow:
            if position_size < 0:
                self.buy(abs(position_size))
            size = (self.portfolio.cash * self.position_size) / current_price
            self.buy(size)
            self.highest_price = current_price
            self.stop_price = current_price * (1 - self.trailing_pct)

        # Update trailing stop if in position
        elif position_size > 0:
            if self.highest_price is None:
                self.highest_price = current_price
            else:
                self.highest_price = max(self.highest_price, current_price)

            new_stop = self.highest_price * (1 - self.trailing_pct)
            self.stop_price = max(self.stop_price or 0, new_stop)

            # Check stop loss
            if current_price <= self.stop_price:
                self.sell(position_size)
                self.highest_price = None
                self.stop_price = None

        # Exit on trend reversal
        elif position_size > 0 and sma_fast < sma_slow:
            self.sell(position_size)
            self.highest_price = None
            self.stop_price = None
