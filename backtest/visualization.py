"""
Visualization utilities for backtest results.
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
from typing import Optional, Dict, Any


def plot_equity_curve(
    results: Dict[str, Any],
    title: str = "Backtest Results",
    figsize: tuple = (14, 10),
    save_path: Optional[str] = None
):
    """
    Plot comprehensive backtest visualization.

    Args:
        results: Results dictionary from backtest
        title: Plot title
        figsize: Figure size tuple
        save_path: Optional path to save figure
    """
    fig, axes = plt.subplots(3, 1, figsize=figsize, gridspec_kw={'height_ratios': [3, 1, 1]})

    equity_df = results['equity_curve']
    equity = equity_df['equity']
    close = equity_df['close']

    # Plot 1: Equity curve and price
    ax1 = axes[0]
    ax1_twin = ax1.twinx()

    ax1.plot(equity.index, equity, label='Portfolio Value', color='blue', linewidth=1.5)
    ax1_twin.plot(close.index, close, label='Asset Price', color='gray', alpha=0.5, linewidth=1)

    ax1.set_ylabel('Portfolio Value ($)', color='blue')
    ax1_twin.set_ylabel('Price ($)', color='gray')
    ax1.set_title(title)
    ax1.legend(loc='upper left')
    ax1_twin.legend(loc='upper right')
    ax1.grid(True, alpha=0.3)

    # Plot 2: Drawdown
    ax2 = axes[1]
    rolling_max = equity.cummax()
    drawdown = (equity - rolling_max) / rolling_max * 100

    ax2.fill_between(drawdown.index, drawdown, 0, color='red', alpha=0.3)
    ax2.plot(drawdown.index, drawdown, color='red', linewidth=0.5)
    ax2.set_ylabel('Drawdown (%)')
    ax2.set_title('Drawdown')
    ax2.grid(True, alpha=0.3)

    # Plot 3: Returns distribution
    ax3 = axes[2]
    returns = equity.pct_change().dropna() * 100

    ax3.hist(returns, bins=50, color='steelblue', edgecolor='black', alpha=0.7)
    ax3.axvline(returns.mean(), color='red', linestyle='--', label=f'Mean: {returns.mean():.2f}%')
    ax3.set_xlabel('Daily Return (%)')
    ax3.set_ylabel('Frequency')
    ax3.set_title('Returns Distribution')
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')

    return fig


def plot_trades(
    results: Dict[str, Any],
    price_data: pd.DataFrame,
    figsize: tuple = (14, 8),
    save_path: Optional[str] = None
):
    """
    Plot price chart with entry/exit points.

    Args:
        results: Results dictionary with trades
        price_data: OHLCV DataFrame
        figsize: Figure size
        save_path: Optional path to save figure
    """
    fig, ax = plt.subplots(figsize=figsize)

    # Plot price
    ax.plot(price_data.index, price_data['close'], label='Price', color='black', linewidth=1)

    # Plot trades
    trades = results.get('trades', [])
    buy_times = []
    buy_prices = []
    sell_times = []
    sell_prices = []

    for trade in trades:
        if trade.side.value == 'buy':
            buy_times.append(trade.timestamp)
            buy_prices.append(trade.price)
        else:
            sell_times.append(trade.timestamp)
            sell_prices.append(trade.price)

    ax.scatter(buy_times, buy_prices, marker='^', color='green', s=100, label='Buy', zorder=5)
    ax.scatter(sell_times, sell_prices, marker='v', color='red', s=100, label='Sell', zorder=5)

    ax.set_xlabel('Date')
    ax.set_ylabel('Price ($)')
    ax.set_title('Trades')
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')

    return fig


def plot_rolling_metrics(
    results: Dict[str, Any],
    window: int = 30,
    figsize: tuple = (14, 8)
):
    """
    Plot rolling performance metrics.

    Args:
        results: Results dictionary
        window: Rolling window size
        figsize: Figure size
    """
    equity_df = results['equity_curve']
    returns = equity_df['equity'].pct_change()

    fig, axes = plt.subplots(2, 2, figsize=figsize)

    # Rolling Sharpe
    ax1 = axes[0, 0]
    rolling_sharpe = (returns.rolling(window).mean() * 365) / (returns.rolling(window).std() * np.sqrt(365))
    ax1.plot(rolling_sharpe.index, rolling_sharpe, color='blue')
    ax1.axhline(0, color='black', linestyle='--', alpha=0.5)
    ax1.set_title(f'Rolling Sharpe Ratio ({window}d)')
    ax1.grid(True, alpha=0.3)

    # Rolling Volatility
    ax2 = axes[0, 1]
    rolling_vol = returns.rolling(window).std() * np.sqrt(365)
    ax2.plot(rolling_vol.index, rolling_vol, color='orange')
    ax2.set_title(f'Rolling Volatility ({window}d)')
    ax2.grid(True, alpha=0.3)

    # Rolling Returns
    ax3 = axes[1, 0]
    rolling_return = returns.rolling(window).sum()
    ax3.fill_between(rolling_return.index, rolling_return, 0, alpha=0.3, color='green')
    ax3.plot(rolling_return.index, rolling_return, color='green')
    ax3.axhline(0, color='black', linestyle='--', alpha=0.5)
    ax3.set_title(f'Rolling Returns ({window}d)')
    ax3.grid(True, alpha=0.3)

    # Underwater plot
    ax4 = axes[1, 1]
    equity = equity_df['equity']
    rolling_max = equity.cummax()
    underwater = (equity - rolling_max) / rolling_max
    ax4.fill_between(underwater.index, underwater, 0, color='red', alpha=0.3)
    ax4.plot(underwater.index, underwater, color='red')
    ax4.set_title('Underwater Plot')
    ax4.grid(True, alpha=0.3)

    plt.tight_layout()
    return fig


def create_summary_chart(
    results_list: list,
    labels: list,
    figsize: tuple = (12, 8)
):
    """
    Compare multiple backtest results.

    Args:
        results_list: List of results dictionaries
        labels: List of labels for each result
        figsize: Figure size
    """
    fig, axes = plt.subplots(2, 2, figsize=figsize)

    metrics = ['total_return', 'sharpe_ratio', 'max_drawdown', 'volatility']
    metric_names = ['Total Return', 'Sharpe Ratio', 'Max Drawdown', 'Volatility']

    for ax, metric, name in zip(axes.flat, metrics, metric_names):
        values = [r[metric] for r in results_list]
        colors = plt.cm.Set3(np.linspace(0, 1, len(labels)))

        bars = ax.bar(labels, values, color=colors, edgecolor='black')
        ax.set_title(name)
        ax.axhline(0, color='black', linewidth=0.5)

        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.2%}' if metric in ['total_return', 'max_drawdown', 'volatility'] else f'{height:.2f}',
                   ha='center', va='bottom', fontsize=8)

    plt.tight_layout()
    return fig
