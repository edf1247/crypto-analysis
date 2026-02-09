"""
Aggressive ATR breakout strategy with RSI and MACD confirmation.
"""

import pandas as pd
import numpy as np
from typing import Optional

from .core import Strategy, OrderSide
from .data import DataLoader


class ATRBreakoutStrategy(Strategy):
    """
    Aggressive strategy combining ATR volatility breakout with RSI momentum
    and MACD trend confirmation.

    Entry Logic:
    - Long: Close > prev_close + (ATR_multiplier * ATR) AND RSI < oversold
            AND MACD histogram > 0 AND MACD line > signal line
    - Short: Close < prev_close - (ATR_multiplier * ATR) AND RSI > overbought
             AND MACD histogram < 0 AND MACD line < signal line

    Exit Logic:
    - Stop loss: entry_price ± (stop_ATR_multiplier * entry_ATR)
    - Take profit: entry_price ± (tp_ATR_multiplier * entry_ATR)
    - MACD trend reversal

    Position Sizing:
    - Dynamic sizing based on ATR volatility: size = risk_per_trade / (stop_ATR_multiplier * entry_ATR)
    - Capped at max_position_size
    """

    def __init__(
        self,
        # Entry parameters
        atr_multiplier: float = 1.5,
        rsi_oversold: float = 30.0,
        rsi_overbought: float = 70.0,
        macd_fast: int = 12,
        macd_slow: int = 26,
        macd_signal: int = 9,

        # Risk management
        risk_per_trade: float = 0.02,  # 2% risk per trade
        stop_atr_multiplier: float = 1.5,
        tp_atr_multiplier: float = 3.0,
        max_position_size: float = 0.95,

        # Filters
        min_atr: float = 0.0,
        **kwargs
    ):
        super().__init__(**kwargs)
        # Entry parameters
        self.atr_multiplier = atr_multiplier
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
        self.macd_fast = macd_fast
        self.macd_slow = macd_slow
        self.macd_signal = macd_signal

        # Risk management
        self.risk_per_trade = risk_per_trade
        self.stop_atr_multiplier = stop_atr_multiplier
        self.tp_atr_multiplier = tp_atr_multiplier
        self.max_position_size = max_position_size

        # Filters
        self.min_atr = min_atr

        # State tracking
        self.entry_price = 0.0
        self.entry_atr = 0.0
        self.position_direction = 0  # 0 = no position, 1 = long, -1 = short
        self.stop_price = 0.0
        self.take_profit_price = 0.0

    def next(self):
        # Need enough data for all indicators
        required_bars = max(self.macd_slow + self.macd_signal, 20)  # ATR uses 14 periods
        if self.current_idx < required_bars:
            return

        # Get recent data with indicators
        data = self.get_ohlc(required_bars + 10)

        # Current values
        current_close = self.current_price
        current_rsi = data['rsi'].iloc[-1]
        current_atr = data['atr'].iloc[-1]

        # MACD values
        current_macd = data['macd'].iloc[-1]
        current_signal = data['macd_signal'].iloc[-1]
        current_hist = data['macd_hist'].iloc[-1]

        # Previous close for breakout calculation
        prev_close = data['close'].iloc[-2] if len(data) > 1 else current_close

        # Current position
        position_size = self.portfolio.get_position_size("BTC-USD")

        # Check exit conditions first
        if self.position_direction != 0:
            if self._check_exit_conditions(current_close, current_macd, current_signal):
                self._exit_position(position_size)
                return

        # Check if ATR meets minimum threshold
        if current_atr < self.min_atr:
            return

        # Entry conditions
        atr_breakout_level = self.atr_multiplier * current_atr

        long_condition = (
            current_close > prev_close + atr_breakout_level and
            current_rsi < self.rsi_oversold and
            current_hist > 0 and
            current_macd > current_signal
        )

        short_condition = (
            current_close < prev_close - atr_breakout_level and
            current_rsi > self.rsi_overbought and
            current_hist < 0 and
            current_macd < current_signal
        )

        # Execute entry
        if long_condition and position_size <= 0:
            self._enter_long(current_close, current_atr, position_size)
        elif short_condition and position_size >= 0:
            self._enter_short(current_close, current_atr, position_size)

    def _enter_long(self, entry_price: float, entry_atr: float, current_position: float):
        """Enter long position with dynamic sizing."""
        if current_position < 0:
            # Close short first
            self.buy(abs(current_position))

        # Calculate position size
        risk_amount = self.portfolio.cash * self.risk_per_trade
        atr_risk = self.stop_atr_multiplier * entry_atr
        base_size = risk_amount / atr_risk if atr_risk > 0 else 0

        # Convert to units and apply max size cap
        size_units = base_size
        max_units = (self.portfolio.cash * self.max_position_size) / entry_price
        size_units = min(size_units, max_units)

        if size_units > 0:
            self.buy(size_units)
            self.entry_price = entry_price
            self.entry_atr = entry_atr
            self.position_direction = 1
            self.stop_price = entry_price - (self.stop_atr_multiplier * entry_atr)
            self.take_profit_price = entry_price + (self.tp_atr_multiplier * entry_atr)

    def _enter_short(self, entry_price: float, entry_atr: float, current_position: float):
        """Enter short position with dynamic sizing."""
        if current_position > 0:
            # Close long first
            self.sell(current_position)

        # Calculate position size
        risk_amount = self.portfolio.cash * self.risk_per_trade
        atr_risk = self.stop_atr_multiplier * entry_atr
        base_size = risk_amount / atr_risk if atr_risk > 0 else 0

        # Convert to units and apply max size cap
        size_units = base_size
        max_units = (self.portfolio.cash * self.max_position_size) / entry_price
        size_units = min(size_units, max_units)

        if size_units > 0:
            self.sell(size_units)
            self.entry_price = entry_price
            self.entry_atr = entry_atr
            self.position_direction = -1
            self.stop_price = entry_price + (self.stop_atr_multiplier * entry_atr)
            self.take_profit_price = entry_price - (self.tp_atr_multiplier * entry_atr)

    def _check_exit_conditions(
        self,
        current_price: float,
        current_macd: float,
        current_signal: float
    ) -> bool:
        """Check if stop loss, take profit, or trend reversal hit."""
        # Stop loss
        if self.position_direction == 1 and current_price <= self.stop_price:
            return True
        elif self.position_direction == -1 and current_price >= self.stop_price:
            return True

        # Take profit
        if self.position_direction == 1 and current_price >= self.take_profit_price:
            return True
        elif self.position_direction == -1 and current_price <= self.take_profit_price:
            return True

        # MACD trend reversal
        if self.position_direction == 1 and current_macd < current_signal:
            return True
        elif self.position_direction == -1 and current_macd > current_signal:
            return True

        return False

    def _exit_position(self, position_size: float):
        """Exit current position."""
        if position_size > 0:
            self.sell(position_size)
        elif position_size < 0:
            self.buy(abs(position_size))

        # Reset state
        self.position_direction = 0
        self.entry_price = 0.0
        self.entry_atr = 0.0
        self.stop_price = 0.0
        self.take_profit_price = 0.0