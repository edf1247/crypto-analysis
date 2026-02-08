"""
Basic example of using the backtesting framework.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from backtest import (
    BacktestEngine,
    DataLoader,
    generate_sample_data,
    SmaCrossover,
    RSIStrategy,
    MACDStrategy,
    plot_equity_curve,
    calculate_metrics
)


def main():
    print("=" * 60)
    print("CRYPTOCURRENCY BACKTEST FRAMEWORK - EXAMPLE")
    print("=" * 60)

    # Generate sample data (or load from file/API)
    print("\n1. Generating sample data...")
    data = generate_sample_data(
        periods=365,
        start_price=50000,
        volatility=0.03,
        trend=0.0005
    )
    print(f"   Data range: {data.index[0].date()} to {data.index[-1].date()}")
    print(f"   Price range: ${data['close'].min():.2f} - ${data['close'].max():.2f}")

    # Add indicators to data
    data = DataLoader.add_indicators(data)

    # Strategy 1: SMA Crossover
    print("\n2. Running SMA Crossover Strategy...")
    strategy1 = SmaCrossover(fast=10, slow=30, position_size=0.95)
    engine1 = BacktestEngine(
        data=data,
        strategy=strategy1,
        initial_capital=10000,
        commission=0.001,  # 0.1%
        slippage=0.0001    # 0.01%
    )
    results1 = engine1.run()

    print(f"   Final Equity: ${results1['final_equity']:,.2f}")
    print(f"   Total Return: {results1['total_return']:.2%}")
    print(f"   Sharpe Ratio: {results1['sharpe_ratio']:.2f}")
    print(f"   Max Drawdown: {results1['max_drawdown']:.2%}")
    print(f"   Trades: {results1['num_trades']}")

    # Strategy 2: RSI Mean Reversion
    print("\n3. Running RSI Strategy...")
    strategy2 = RSIStrategy(period=14, oversold=30, overbought=70, position_size=0.2)
    engine2 = BacktestEngine(
        data=data,
        strategy=strategy2,
        initial_capital=10000,
        commission=0.001,
        slippage=0.0001
    )
    results2 = engine2.run()

    print(f"   Final Equity: ${results2['final_equity']:,.2f}")
    print(f"   Total Return: {results2['total_return']:.2%}")
    print(f"   Sharpe Ratio: {results2['sharpe_ratio']:.2f}")
    print(f"   Max Drawdown: {results2['max_drawdown']:.2%}")
    print(f"   Trades: {results2['num_trades']}")

    # Strategy 3: MACD Trend Following
    print("\n4. Running MACD Strategy...")
    strategy3 = MACDStrategy(fast=12, slow=26, signal=9, position_size=0.9)
    engine3 = BacktestEngine(
        data=data,
        strategy=strategy3,
        initial_capital=10000,
        commission=0.001,
        slippage=0.0001
    )
    results3 = engine3.run()

    print(f"   Final Equity: ${results3['final_equity']:,.2f}")
    print(f"   Total Return: {results3['total_return']:.2%}")
    print(f"   Sharpe Ratio: {results3['sharpe_ratio']:.2f}")
    print(f"   Max Drawdown: {results3['max_drawdown']:.2%}")
    print(f"   Trades: {results3['num_trades']}")

    # Buy and Hold comparison
    print("\n5. Buy and Hold Benchmark...")
    initial_price = data['close'].iloc[0]
    final_price = data['close'].iloc[-1]
    shares = 10000 / initial_price
    final_value = shares * final_price
    buyhold_return = (final_value / 10000) - 1

    print(f"   Final Equity: ${final_value:,.2f}")
    print(f"   Total Return: {buyhold_return:.2%}")

    # Comparison
    print("\n6. Strategy Comparison")
    print("-" * 60)
    print(f"{'Metric':<20} {'SMA Cross':>12} {'RSI':>12} {'MACD':>12} {'Buy&Hold':>12}")
    print("-" * 60)
    print(f"{'Total Return':<20} {results1['total_return']:>11.2%} {results2['total_return']:>11.2%} {results3['total_return']:>11.2%} {buyhold_return:>11.2%}")
    print(f"{'Sharpe Ratio':<20} {results1['sharpe_ratio']:>12.2f} {results2['sharpe_ratio']:>12.2f} {results3['sharpe_ratio']:>12.2f} {'N/A':>12}")
    print(f"{'Max Drawdown':<20} {results1['max_drawdown']:>11.2%} {results2['max_drawdown']:>11.2%} {results3['max_drawdown']:>11.2%} {'N/A':>12}")
    print(f"{'Num Trades':<20} {results1['num_trades']:>12} {results2['num_trades']:>12} {results3['num_trades']:>12} {0:>12}")
    print("-" * 60)

    # Try to plot if matplotlib is available
    try:
        print("\n7. Generating plots...")
        fig = plot_equity_curve(results1, title="SMA Crossover Strategy")
        fig.savefig('/home/edf1247/projects/crypto/examples/sma_equity.png')
        print("   Saved: examples/sma_equity.png")

        fig = plot_equity_curve(results2, title="RSI Strategy")
        fig.savefig('/home/edf1247/projects/crypto/examples/rsi_equity.png')
        print("   Saved: examples/rsi_equity.png")

        fig = plot_equity_curve(results3, title="MACD Strategy")
        fig.savefig('/home/edf1247/projects/crypto/examples/macd_equity.png')
        print("   Saved: examples/macd_equity.png")
    except Exception as e:
        print(f"   Plotting skipped: {e}")

    print("\n" + "=" * 60)
    print("Backtest complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
