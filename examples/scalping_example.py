"""
Example usage of ScalpingStrategy.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backtest import ScalpingStrategy, BacktestEngine, generate_sample_data, DataLoader


def main():
    print("=" * 60)
    print("SCALPING STRATEGY EXAMPLE")
    print("=" * 60)

    # Generate sample data
    data = generate_sample_data(periods=500, volatility=0.02)
    data = DataLoader.add_indicators(data)

    # Create strategy with Pine Script defaults
    strategy = ScalpingStrategy(
        sma_length=25,
        ema_length=200,
        keltner_length=10,
        keltner_multiplier=2.0,
        keltner_band_style="Average True Range",
        keltner_atr_length=14,
        stoch_period_k=10,
        stoch_smooth_k=1,
        stoch_period_d=1,
        macd_fast=4,
        macd_slow=34,
        macd_signal=5,
        macd_source_ma="EMA",
        macd_signal_ma="EMA",
        position_size=0.95,
        stop_loss_pct=0.02,
        take_profit_pct=0.05
    )

    # Create and run backtest
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

    # Optional: Plot results
    if 'trades' in results and len(results['trades']) > 0:
        try:
            from backtest.visualization import plot_equity_curve, plot_trades
            import matplotlib.pyplot as plt

            # Plot equity curve
            plot_equity_curve(results)
            plt.show()

            # Plot trades
            plot_trades(results, data)
            plt.show()
        except Exception as e:
            print(f"Plotting failed: {e}")


if __name__ == "__main__":
    main()