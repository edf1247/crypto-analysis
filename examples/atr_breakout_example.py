"""
Example usage of ATRBreakoutStrategy aggressive trading.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import matplotlib.pyplot as plt
from backtest import ATRBreakoutStrategy, BacktestEngine, DataLoader
from backtest.data import generate_sample_data
from backtest.visualization import plot_equity_curve, plot_trades, plot_rolling_metrics


def run_backtest(params: dict, data: pd.DataFrame):
    """Run backtest with given parameters."""
    strategy = ATRBreakoutStrategy(**params)

    engine = BacktestEngine(
        data=data,
        strategy=strategy,
        initial_capital=10000,
        commission=0.001,
        slippage=0.0001
    )

    return engine.run()


def main():
    print("=" * 70)
    print("ATR BREAKOUT AGGRESSIVE STRATEGY EXAMPLE")
    print("=" * 70)

    # Generate sample data with volatility
    data = generate_sample_data(periods=2000, volatility=0.025, trend=0.0001)
    data = DataLoader.add_indicators(data)

    # Define parameter sets to test
    param_sets = {
        "Very Aggressive": {
            "atr_multiplier": 1.0,
            "risk_per_trade": 0.03,  # 3% risk per trade
            "stop_atr_multiplier": 1.0,  # Tight stop
            "tp_atr_multiplier": 2.0,    # 2:1 reward:risk
            "max_position_size": 0.95,
        },
        "Moderately Aggressive": {
            "atr_multiplier": 1.5,
            "risk_per_trade": 0.02,  # 2% risk per trade
            "stop_atr_multiplier": 1.5,
            "tp_atr_multiplier": 3.0,    # 2:1 reward:risk
            "max_position_size": 0.90,
        },
        "Conservative Aggressive": {
            "atr_multiplier": 2.0,
            "risk_per_trade": 0.01,  # 1% risk per trade
            "stop_atr_multiplier": 2.0,
            "tp_atr_multiplier": 4.0,    # 2:1 reward:risk
            "max_position_size": 0.80,
        }
    }

    results = {}
    for name, params in param_sets.items():
        print(f"\nRunning {name} configuration...")
        results[name] = run_backtest(params, data)

        # Print summary
        r = results[name]
        print(f"  Final Equity: ${r['final_equity']:,.2f}")
        print(f"  Total Return: {r['total_return']:+.2%}")
        print(f"  CAGR: {r['cagr']:+.2%}")
        print(f"  Sharpe Ratio: {r['sharpe_ratio']:.2f}")
        print(f"  Max Drawdown: {r['max_drawdown']:.2%}")
        print(f"  Number of Trades: {r['num_trades']}")

    # Compare results
    print("\n" + "=" * 70)
    print("PERFORMANCE COMPARISON")
    print("=" * 70)

    comparison = pd.DataFrame([
        {
            "Strategy": name,
            "Total Return": r["total_return"],
            "CAGR": r["cagr"],
            "Sharpe": r["sharpe_ratio"],
            "Max DD": r["max_drawdown"],
            "Trades": r["num_trades"],
            "Win Rate": r.get("win_rate", 0)
        }
        for name, r in results.items()
    ])

    print(comparison.to_string(index=False))

    # Plot results for the most aggressive strategy
    most_aggressive = max(results.items(), key=lambda x: x[1]['total_return'])
    strategy_name, best_result = most_aggressive

    if len(best_result.get('trades', [])) > 0:
        fig, axes = plt.subplots(3, 1, figsize=(14, 10))

        # Equity curve
        plot_equity_curve(data, best_result['equity_curve'], ax=axes[0])
        axes[0].set_title(f"{strategy_name} - Equity Curve")

        # Trades
        plot_trades(data, best_result['trades'], ax=axes[1])
        axes[1].set_title(f"{strategy_name} - Trade Entries/Exits")

        # Rolling metrics
        plot_rolling_metrics(best_result['equity_curve'], ax=axes[2])
        axes[2].set_title(f"{strategy_name} - Rolling Performance Metrics")

        plt.tight_layout()
        plt.savefig(f"atr_breakout_{strategy_name.lower().replace(' ', '_')}.png")
        print(f"\nPlot saved to: atr_breakout_{strategy_name.lower().replace(' ', '_')}.png")

    print("\n" + "=" * 70)
    print("AGGRESSIVE STRATEGY ANALYSIS COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
