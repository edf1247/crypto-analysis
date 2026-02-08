"""
Performance metrics and reporting for backtests.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class PerformanceReport:
    """Comprehensive performance report."""
    total_return: float
    cagr: float
    volatility: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    max_drawdown_duration: int
    calmar_ratio: float
    win_rate: float
    profit_factor: float
    avg_trade: float
    avg_win: float
    avg_loss: float
    num_trades: int
    num_winning_trades: int
    num_losing_trades: int
    expectancy: float
    final_equity: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'Total Return': f"{self.total_return:.2%}",
            'CAGR': f"{self.cagr:.2%}",
            'Volatility': f"{self.volatility:.2%}",
            'Sharpe Ratio': f"{self.sharpe_ratio:.2f}",
            'Sortino Ratio': f"{self.sortino_ratio:.2f}",
            'Max Drawdown': f"{self.max_drawdown:.2%}",
            'Max DD Duration': f"{self.max_drawdown_duration} days",
            'Calmar Ratio': f"{self.calmar_ratio:.2f}",
            'Win Rate': f"{self.win_rate:.2%}",
            'Profit Factor': f"{self.profit_factor:.2f}",
            'Avg Trade': f"{self.avg_trade:.2%}",
            'Avg Win': f"{self.avg_win:.2%}",
            'Avg Loss': f"{self.avg_loss:.2%}",
            'Num Trades': self.num_trades,
            'Winning Trades': self.num_winning_trades,
            'Losing Trades': self.num_losing_trades,
            'Expectancy': f"{self.expectancy:.4f}",
            'Final Equity': f"${self.final_equity:,.2f}"
        }

    def print_report(self):
        """Print formatted report."""
        print("=" * 50)
        print("BACKTEST PERFORMANCE REPORT")
        print("=" * 50)
        for key, value in self.to_dict().items():
            print(f"{key:20}: {value:>15}")
        print("=" * 50)


def calculate_metrics(
    equity_curve: pd.DataFrame,
    trades: List[Any],
    initial_capital: float,
    risk_free_rate: float = 0.0
) -> PerformanceReport:
    """
    Calculate comprehensive performance metrics.

    Args:
        equity_curve: DataFrame with 'equity' column
        trades: List of trade objects
        initial_capital: Starting capital
        risk_free_rate: Annual risk-free rate
    """
    equity = equity_curve['equity']
    returns = equity.pct_change().dropna()

    # Basic return metrics
    total_return = (equity.iloc[-1] / initial_capital) - 1
    periods = len(returns)
    years = periods / 365

    cagr = (1 + total_return) ** (1 / max(years, 0.001)) - 1

    # Risk metrics
    volatility = returns.std() * np.sqrt(365)

    # Sharpe ratio
    excess_returns = returns.mean() * 365 - risk_free_rate
    sharpe_ratio = excess_returns / (returns.std() * np.sqrt(365)) if returns.std() > 0 else 0

    # Sortino ratio (downside deviation)
    downside_returns = returns[returns < 0]
    downside_std = downside_returns.std() * np.sqrt(365) if len(downside_returns) > 0 else 0
    sortino_ratio = excess_returns / downside_std if downside_std > 0 else 0

    # Drawdown
    rolling_max = equity.cummax()
    drawdown = (equity - rolling_max) / rolling_max
    max_drawdown = drawdown.min()

    # Drawdown duration
    is_drawdown = drawdown < 0
    drawdown_duration = 0
    max_duration = 0
    for in_dd in is_drawdown:
        if in_dd:
            drawdown_duration += 1
            max_duration = max(max_duration, drawdown_duration)
        else:
            drawdown_duration = 0

    # Calmar ratio
    calmar_ratio = cagr / abs(max_drawdown) if max_drawdown != 0 else 0

    # Trade metrics
    if trades:
        trade_returns = []
        for i in range(0, len(trades) - 1, 2):
            if i + 1 < len(trades):
                entry = trades[i]
                exit_trade = trades[i + 1]
                if entry.side.value == 'buy' and exit_trade.side.value == 'sell':
                    pnl = (exit_trade.price - entry.price) / entry.price
                    trade_returns.append(pnl)

        num_trades = len(trade_returns)
        winning_trades = [r for r in trade_returns if r > 0]
        losing_trades = [r for r in trade_returns if r <= 0]

        win_rate = len(winning_trades) / num_trades if num_trades > 0 else 0

        gross_profit = sum(winning_trades) if winning_trades else 0
        gross_loss = abs(sum(losing_trades)) if losing_trades else 0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')

        avg_trade = np.mean(trade_returns) if trade_returns else 0
        avg_win = np.mean(winning_trades) if winning_trades else 0
        avg_loss = np.mean(losing_trades) if losing_trades else 0

        # Expectancy
        expectancy = (win_rate * avg_win) - ((1 - win_rate) * abs(avg_loss)) if num_trades > 0 else 0
    else:
        num_trades = 0
        winning_trades = []
        losing_trades = []
        win_rate = 0
        profit_factor = 0
        avg_trade = 0
        avg_win = 0
        avg_loss = 0
        expectancy = 0

    return PerformanceReport(
        total_return=total_return,
        cagr=cagr,
        volatility=volatility,
        sharpe_ratio=sharpe_ratio,
        sortino_ratio=sortino_ratio,
        max_drawdown=max_drawdown,
        max_drawdown_duration=max_duration,
        calmar_ratio=calmar_ratio,
        win_rate=win_rate,
        profit_factor=profit_factor,
        avg_trade=avg_trade,
        avg_win=avg_win,
        avg_loss=avg_loss,
        num_trades=num_trades,
        num_winning_trades=len(winning_trades),
        num_losing_trades=len(losing_trades),
        expectancy=expectancy,
        final_equity=equity.iloc[-1]
    )


def monthly_returns_table(equity_curve: pd.DataFrame) -> pd.DataFrame:
    """Generate monthly returns table."""
    equity = equity_curve['equity']
    monthly = equity.resample('ME').last()
    monthly_returns = monthly.pct_change().dropna()

    # Create pivot table
    monthly_returns.index = pd.to_datetime(monthly_returns.index)
    df = pd.DataFrame({
        'Year': monthly_returns.index.year,
        'Month': monthly_returns.index.month,
        'Return': monthly_returns.values
    })

    pivot = df.pivot(index='Year', columns='Month', values='Return')
    pivot.columns = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                     'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    # Add annual returns
    pivot['YTD'] = pivot.apply(lambda row: (1 + row.dropna()).prod() - 1, axis=1)

    return pivot
