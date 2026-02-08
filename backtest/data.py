"""
Data loading and handling utilities for backtesting.
"""

import pandas as pd
import numpy as np
from typing import Optional, List
from pathlib import Path
import requests


class DataLoader:
    """Loads and preprocesses OHLCV data for backtesting."""

    @staticmethod
    def from_csv(filepath: str) -> pd.DataFrame:
        """Load data from CSV file."""
        df = pd.read_csv(filepath)
        return DataLoader._standardize(df)

    @staticmethod
    def from_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """Standardize an existing DataFrame."""
        return DataLoader._standardize(df.copy())

    @staticmethod
    def fetch_binance(
        symbol: str = "BTCUSDT",
        interval: str = "1d",
        limit: int = 1000,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Fetch historical data from Binance API.

        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            interval: Time interval (1m, 5m, 15m, 1h, 4h, 1d, 1w, 1M)
            limit: Number of candles (max 1000)
            start_time: Start time in milliseconds
            end_time: End time in milliseconds
        """
        url = "https://api.binance.com/api/v3/klines"
        params = {
            "symbol": symbol.upper(),
            "interval": interval,
            "limit": limit
        }
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time

        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        df = pd.DataFrame(data, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'trades', 'taker_buy_volume',
            'taker_buy_quote_volume', 'ignore'
        ])

        return DataLoader._standardize(df)

    @staticmethod
    def _standardize(df: pd.DataFrame) -> pd.DataFrame:
        """Standardize DataFrame format."""
        # Convert timestamp to datetime index
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms' if df['timestamp'].dtype == np.int64 else None)
            df.set_index('timestamp', inplace=True)
        elif not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)

        # Ensure required columns exist
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in required_cols:
            if col not in df.columns:
                if col.capitalize() in df.columns:
                    df[col] = df[col.capitalize()]
                else:
                    raise ValueError(f"Missing required column: {col}")

        # Convert to numeric
        for col in required_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # Select only required columns
        df = df[required_cols].copy()

        # Remove any NaN values
        df.dropna(inplace=True)

        return df.sort_index()

    @staticmethod
    def resample(df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
        """
        Resample data to a different timeframe.

        Args:
            df: OHLCV DataFrame
            timeframe: Pandas offset string (e.g., '1H', '4H', '1D')
        """
        resampled = df.resample(timeframe).agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        })
        return resampled.dropna()

    @staticmethod
    def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """Add common technical indicators."""
        df = df.copy()

        # Simple Moving Averages
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['sma_50'] = df['close'].rolling(window=50).mean()
        df['sma_200'] = df['close'].rolling(window=200).mean()

        # Exponential Moving Averages
        df['ema_12'] = df['close'].ewm(span=12, adjust=False).mean()
        df['ema_26'] = df['close'].ewm(span=26, adjust=False).mean()

        # MACD
        df['macd'] = df['ema_12'] - df['ema_26']
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']

        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))

        # Bollinger Bands
        df['bb_middle'] = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
        df['bb_lower'] = df['bb_middle'] - (bb_std * 2)

        # ATR (Average True Range)
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        df['atr'] = true_range.rolling(14).mean()

        # Keltner Channel (default parameters)
        df = DataLoader.add_keltner_channel(df, length=10, multiplier=2.0,
                                      band_style='Average True Range', atr_length=14)

        # Stochastic (default parameters)
        df = DataLoader.add_stochastic(df, period_k=10, smooth_k=1, period_d=1)

        return df

    @staticmethod
    def add_keltner_channel(
        df: pd.DataFrame,
        length: int = 10,
        multiplier: float = 2.0,
        source_col: str = 'close',
        band_style: str = 'Average True Range',
        atr_length: int = 14
    ) -> pd.DataFrame:
        """
        Add Keltner Channel indicators to DataFrame.

        Args:
            df: OHLCV DataFrame
            length: Period for moving average
            multiplier: Band multiplier
            source_col: Price source column
            band_style: 'Average True Range', 'True Range', or 'Range'
            atr_length: ATR period if band_style is 'Average True Range'

        Returns:
            DataFrame with keltner_middle, keltner_upper, keltner_lower columns
        """
        df = df.copy()
        # Middle line: SMA of source
        df['keltner_middle'] = df[source_col].rolling(window=length).mean()

        # Calculate range based on band_style
        if band_style == 'True Range':
            high_low = df['high'] - df['low']
            high_close = np.abs(df['high'] - df['close'].shift())
            low_close = np.abs(df['low'] - df['close'].shift())
            ranges = pd.concat([high_low, high_close, low_close], axis=1)
            rangema = np.max(ranges, axis=1).rolling(length).mean()
        elif band_style == 'Average True Range':
            # Use existing ATR calculation or compute
            if 'atr' not in df.columns:
                high_low = df['high'] - df['low']
                high_close = np.abs(df['high'] - df['close'].shift())
                low_close = np.abs(df['low'] - df['close'].shift())
                ranges = pd.concat([high_low, high_close, low_close], axis=1)
                true_range = np.max(ranges, axis=1)
                atr = true_range.rolling(atr_length).mean()
                rangema = atr
            else:
                rangema = df['atr']
        else:  # 'Range'
            rangema = (df['high'] - df['low']).rolling(length).mean()

        df['keltner_upper'] = df['keltner_middle'] + (rangema * multiplier)
        df['keltner_lower'] = df['keltner_middle'] - (rangema * multiplier)
        return df

    @staticmethod
    def add_stochastic(
        df: pd.DataFrame,
        period_k: int = 10,
        smooth_k: int = 1,
        period_d: int = 1
    ) -> pd.DataFrame:
        """
        Add Stochastic oscillator to DataFrame.

        Args:
            df: OHLCV DataFrame
            period_k: %K period
            smooth_k: %K smoothing
            period_d: %D smoothing

        Returns:
            DataFrame with stoch_k and stoch_d columns
        """
        df = df.copy()
        # Calculate %K
        low_min = df['low'].rolling(window=period_k).min()
        high_max = df['high'].rolling(window=period_k).max()
        k_raw = 100 * ((df['close'] - low_min) / (high_max - low_min))

        # Smooth %K
        k_smoothed = k_raw.rolling(window=smooth_k).mean()
        df['stoch_k'] = k_smoothed

        # %D line (signal)
        df['stoch_d'] = k_smoothed.rolling(window=period_d).mean()
        return df


def generate_sample_data(
    periods: int = 1000,
    start_price: float = 50000,
    volatility: float = 0.02,
    trend: float = 0.0001,
    start_date: str = "2023-01-01"
) -> pd.DataFrame:
    """
    Generate synthetic OHLCV data for testing.

    Args:
        periods: Number of periods to generate
        start_price: Starting price
        volatility: Daily volatility
        trend: Daily trend (drift)
        start_date: Start date string
    """
    np.random.seed(42)
    dates = pd.date_range(start=start_date, periods=periods, freq='D')

    # Generate random walk with trend
    returns = np.random.normal(trend, volatility, periods)
    prices = start_price * np.exp(np.cumsum(returns))

    # Generate OHLC from close prices
    df = pd.DataFrame(index=dates)
    df['close'] = prices
    df['open'] = df['close'].shift(1) * (1 + np.random.normal(0, volatility/3, periods))
    df.loc[df.index[0], 'open'] = start_price

    # High and low based on volatility
    daily_range = prices * volatility * np.random.uniform(0.5, 2.0, periods)
    df['high'] = np.maximum(df['open'], df['close']) + daily_range * np.random.uniform(0, 0.5, periods)
    df['low'] = np.minimum(df['open'], df['close']) - daily_range * np.random.uniform(0, 0.5, periods)

    # Volume
    df['volume'] = np.random.lognormal(20, 1, periods)

    return df
