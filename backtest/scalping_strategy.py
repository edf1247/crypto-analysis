"""
Scalping trading strategy based on Pine Script strategy.
"""

import pandas as pd
import numpy as np
from typing import Optional

from .core import Strategy, OrderSide
from .data import DataLoader


class ScalpingStrategy(Strategy):
    """
    Scalping strategy combining SMA, EMA, Keltner Channel, Stochastic, and MACD.

    Entry conditions (from Pine Script):
    - Long: close > SMA(len) AND close < upper Keltner AND close > lower Keltner
             AND hist < 0 AND k < 50 AND close > EMA(len2)
    - Short: close < SMA(len) AND close < upper Keltner AND close > lower Keltner
             AND hist > 0 AND k > 50 AND close < EMA(len2)

    Exit logic: Fixed stop loss (2%) and take profit (5%)
    """

    def __init__(
        self,
        sma_length: int = 25,
        ema_length: int = 200,
        keltner_length: int = 10,
        keltner_multiplier: float = 2.0,
        keltner_band_style: str = "Average True Range",
        keltner_atr_length: int = 14,
        stoch_period_k: int = 10,
        stoch_smooth_k: int = 1,
        stoch_period_d: int = 1,
        macd_fast: int = 4,
        macd_slow: int = 34,
        macd_signal: int = 5,
        macd_source_ma: str = "EMA",
        macd_signal_ma: str = "EMA",
        position_size: float = 0.95,
        stop_loss_pct: float = 0.02,
        take_profit_pct: float = 0.05,
        **kwargs
    ):
        super().__init__(take_profit_pct=take_profit_pct, stop_loss_pct=stop_loss_pct, **kwargs)
        # Store all parameters
        self.sma_length = sma_length
        self.ema_length = ema_length
        self.keltner_length = keltner_length
        self.keltner_multiplier = keltner_multiplier
        self.keltner_band_style = keltner_band_style
        self.keltner_atr_length = keltner_atr_length
        self.stoch_period_k = stoch_period_k
        self.stoch_smooth_k = stoch_smooth_k
        self.stoch_period_d = stoch_period_d
        self.macd_fast = macd_fast
        self.macd_slow = macd_slow
        self.macd_signal = macd_signal
        self.macd_source_ma = macd_source_ma
        self.macd_signal_ma = macd_signal_ma
        self.position_size = position_size
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct

        # State tracking
        self.entry_price = 0.0
        self.position_direction = 0  # 0 = no position, 1 = long, -1 = short

    def next(self):
        # Need enough data for all indicators
        required_bars = max(
            self.sma_length,
            self.ema_length,
            self.keltner_length,
            self.stoch_period_k,
            self.macd_slow + self.macd_signal
        )
        if self.current_idx < required_bars:
            return

        # Get recent data (more than required for smoothing)
        data = self.get_ohlc(required_bars + 20)

        # Calculate indicators
        # SMA
        sma = data['close'].rolling(self.sma_length).mean().iloc[-1]

        # EMA
        ema = data['close'].ewm(span=self.ema_length, adjust=False).mean().iloc[-1]

        # Keltner Channel (using DataLoader method)
        data_kc = DataLoader.add_keltner_channel(
            data,
            length=self.keltner_length,
            multiplier=self.keltner_multiplier,
            band_style=self.keltner_band_style,
            atr_length=self.keltner_atr_length
        )
        keltner_upper = data_kc['keltner_upper'].iloc[-1]
        keltner_lower = data_kc['keltner_lower'].iloc[-1]

        # Stochastic
        data_stoch = DataLoader.add_stochastic(
            data,
            period_k=self.stoch_period_k,
            smooth_k=self.stoch_smooth_k,
            period_d=self.stoch_period_d
        )
        stoch_k = data_stoch['stoch_k'].iloc[-1]

        # MACD
        if self.macd_source_ma == "SMA":
            fast_ma = data['close'].rolling(self.macd_fast).mean()
            slow_ma = data['close'].rolling(self.macd_slow).mean()
        else:  # EMA
            fast_ma = data['close'].ewm(span=self.macd_fast, adjust=False).mean()
            slow_ma = data['close'].ewm(span=self.macd_slow, adjust=False).mean()

        macd_line = fast_ma - slow_ma

        if self.macd_signal_ma == "SMA":
            signal_line = macd_line.rolling(self.macd_signal).mean()
        else:  # EMA
            signal_line = macd_line.ewm(span=self.macd_signal, adjust=False).mean()

        hist = macd_line.iloc[-1] - signal_line.iloc[-1]

        # Current price and position
        current_price = self.current_price
        position_size = self.portfolio.get_position_size("BTC-USD")

        # Check exit conditions (stop loss / take profit)
        if self.position_direction != 0:
            if self._check_exit_conditions(current_price):
                # Exit position
                if position_size > 0:
                    self.sell(position_size)
                elif position_size < 0:
                    self.buy(abs(position_size))
                self.position_direction = 0
                self.entry_price = 0.0
                return

        # Entry conditions
        long_condition = (
            current_price > sma and
            current_price < keltner_upper and
            current_price > keltner_lower and
            hist < 0 and
            stoch_k < 50 and
            current_price > ema
        )

        short_condition = (
            current_price < sma and
            current_price < keltner_upper and
            current_price > keltner_lower and
            hist > 0 and
            stoch_k > 50 and
            current_price < ema
        )

        # Execute entry
        if long_condition and position_size <= 0:
            # Buy signal
            if position_size < 0:
                # Close short first
                self.buy(abs(position_size))

            size = (self.portfolio.cash * self.position_size) / current_price
            self.buy(size)
            self.position_direction = 1
            self.entry_price = current_price

        elif short_condition and position_size >= 0:
            # Sell signal
            if position_size > 0:
                # Close long first
                self.sell(position_size)

            size = (self.portfolio.cash * self.position_size) / current_price
            self.sell(size)
            self.position_direction = -1
            self.entry_price = current_price

    def _check_exit_conditions(self, current_price: float) -> bool:
        """Check if stop loss or take profit hit."""
        if self.position_direction == 1:  # Long position
            ret = (current_price / self.entry_price) - 1.0
            if ret <= -self.stop_loss_pct or ret >= self.take_profit_pct:
                return True
        elif self.position_direction == -1:  # Short position
            ret = (self.entry_price / current_price) - 1.0
            if ret <= -self.stop_loss_pct or ret >= self.take_profit_pct:
                return True
        return False