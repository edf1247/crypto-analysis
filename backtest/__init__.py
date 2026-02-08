"""
Cryptocurrency Backtesting Framework

A simple yet powerful framework for backtesting cryptocurrency trading strategies.
"""

from .core import (
    Strategy,
    BacktestEngine,
    Order,
    Trade,
    Position,
    Portfolio,
    OrderSide,
    OrderType
)

from .data import (
    DataLoader,
    generate_sample_data
)

from .strategies import (
    BuyAndHold,
    SmaCrossover,
    RSIStrategy,
    BollingerBandsStrategy,
    MACDStrategy,
    GridTradingStrategy,
    TrailingStopStrategy
)

from .scalping_strategy import ScalpingStrategy
from .atr_breakout_strategy import ATRBreakoutStrategy

from .metrics import (
    PerformanceReport,
    calculate_metrics,
    monthly_returns_table
)

from .visualization import (
    plot_equity_curve,
    plot_trades,
    plot_rolling_metrics,
    create_summary_chart
)

__version__ = "0.1.0"
__all__ = [
    'Strategy',
    'BacktestEngine',
    'Order',
    'Trade',
    'Position',
    'Portfolio',
    'OrderSide',
    'OrderType',
    'DataLoader',
    'generate_sample_data',
    'BuyAndHold',
    'SmaCrossover',
    'RSIStrategy',
    'BollingerBandsStrategy',
    'MACDStrategy',
    'GridTradingStrategy',
    'TrailingStopStrategy',
    'ScalpingStrategy',
    'ATRBreakoutStrategy',
    'PerformanceReport',
    'calculate_metrics',
    'monthly_returns_table',
    'plot_equity_curve',
    'plot_trades',
    'plot_rolling_metrics',
    'create_summary_chart'
]
