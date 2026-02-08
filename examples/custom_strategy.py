"""
Example of creating a custom strategy.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backtest import Strategy, BacktestEngine, generate_sample_data, DataLoader


class MyCustomStrategy(Strategy):
    """
    Example custom strategy that combines multiple indicators.

    Strategy logic:
    - Enter long when price > SMA20 AND RSI < 70 AND MACD > Signal
    - Exit when RSI > 80 or price < SMA20
    """

    def __init__(
        self,
        sma_period: int = 20,
        rsi_period: int = 14,
        macd_fast: int = 12,
        macd_slow: int = 26,
        macd_signal: int = 9,
        rsi_overbought: float = 80,
        position_size: float = 0.8
    ):
        super().__init__()
        self.sma_period = sma_period
        self.rsi_period = rsi_period
        self.macd_fast = macd_fast
        self.macd_slow = macd_slow
        self.macd_signal = macd_signal
        self.rsi_overbought = rsi_overbought
        self.position_size = position_size

    def next(self):
        # Need enough data for all indicators
        required_bars = max(self.sma_period, self.macd_slow + self.macd_signal)
        if self.current_idx < required_bars:
            return

        # Get recent data
        data = self.get_ohlc(required_bars + 10)

        # Calculate SMA
        sma = data['close'].rolling(self.sma_period).mean().iloc[-1]

        # Calculate RSI
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1]

        # Calculate MACD
        ema_fast = data['close'].ewm(span=self.macd_fast, adjust=False).mean()
        ema_slow = data['close'].ewm(span=self.macd_slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=self.macd_signal, adjust=False).mean()

        current_macd = macd_line.iloc[-1]
        current_signal = signal_line.iloc[-1]

        # Current state
        current_price = self.current_price
        position_size = self.portfolio.get_position_size("BTC-USD")

        # Entry conditions
        long_condition = (
            current_price > sma and
            current_rsi < 70 and
            current_macd > current_signal
        )

        # Exit conditions
        exit_condition = (
            current_rsi > self.rsi_overbought or
            current_price < sma
        )

        # Execute trades
        if long_condition and position_size <= 0:
            # Buy signal
            if position_size < 0:
                # Close short first
                self.buy(abs(position_size))

            size = (self.portfolio.cash * self.position_size) / current_price
            self.buy(size)
            print(f"[{self.current_timestamp}] BUY @ ${current_price:,.2f} - RSI: {current_rsi:.1f}, MACD: {current_macd:.2f}")

        elif exit_condition and position_size > 0:
            # Sell signal
            self.sell(position_size)
            print(f"[{self.current_timestamp}] SELL @ ${current_price:,.2f} - RSI: {current_rsi:.1f}")


def main():
    print("=" * 60)
    print("CUSTOM STRATEGY EXAMPLE")
    print("=" * 60)

    # Generate data
    data = generate_sample_data(periods=200, volatility=0.025)
    data = DataLoader.add_indicators(data)

    # Create and run backtest
    strategy = MyCustomStrategy(
        sma_period=20,
        rsi_overbought=80,
        position_size=0.8
    )

    engine = BacktestEngine(
        data=data,
        strategy=strategy,
        initial_capital=10000,
        commission=0.001,
        slippage=0.0001
    )

    print("\nRunning backtest...\n")
    results = engine.run()

    # Print results
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"Initial Capital:  $10,000.00")
    print(f"Final Equity:     ${results['final_equity']:,.2f}")
    print(f"Total Return:     {results['total_return']:+.2%}")
    print(f"CAGR:             {results['cagr']:+.2%}")
    print(f"Sharpe Ratio:     {results['sharpe_ratio']:.2f}")
    print(f"Max Drawdown:     {results['max_drawdown']:.2%}")
    print(f"Volatility:       {results['volatility']:.2%}")
    print(f"Number of Trades: {results['num_trades']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
