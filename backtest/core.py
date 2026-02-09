"""
Core backtesting engine for cryptocurrency trading strategies.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Callable, Any
from enum import Enum
from datetime import datetime
import pandas as pd
import numpy as np


class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"


@dataclass
class Order:
    """Represents a trading order."""
    side: OrderSide
    size: float
    price: Optional[float] = None
    order_type: OrderType = OrderType.MARKET
    timestamp: Optional[datetime] = None
    symbol: str = "BTC-USD"


@dataclass
class Trade:
    """Represents an executed trade."""
    side: OrderSide
    size: float
    price: float
    timestamp: datetime
    symbol: str
    fee: float = 0.0


@dataclass
class Position:
    """Tracks an open position."""
    symbol: str
    side: OrderSide
    size: float
    entry_price: float
    entry_time: datetime

    @property
    def unrealized_pnl(self, current_price: float) -> float:
        """Calculate unrealized P&L at current price."""
        if self.side == OrderSide.BUY:
            return (current_price - self.entry_price) * self.size
        else:
            return (self.entry_price - current_price) * self.size


@dataclass
class Portfolio:
    """Manages cash and positions."""
    initial_capital: float
    cash: float = field(init=False)
    positions: Dict[str, Position] = field(default_factory=dict)
    trades: List[Trade] = field(default_factory=list)

    def __post_init__(self):
        self.cash = self.initial_capital

    def get_position_size(self, symbol: str) -> float:
        """Get current position size for a symbol."""
        if symbol in self.positions:
            pos = self.positions[symbol]
            return pos.size if pos.side == OrderSide.BUY else -pos.size
        return 0.0

    def get_total_value(self, prices: Dict[str, float]) -> float:
        """Calculate total portfolio value including positions."""
        total = self.cash
        for symbol, position in self.positions.items():
            if symbol in prices:
                total += position.size * prices[symbol]
        return total


class Strategy:
    """Base class for trading strategies."""

    def __init__(self, take_profit_pct=None, stop_loss_pct=None, **kwargs):
        self.data: Optional[pd.DataFrame] = None
        self.current_idx: int = 0
        self.orders: List[Order] = []
        self.take_profit_pct = take_profit_pct
        self.stop_loss_pct = stop_loss_pct
        # Ignore extra kwargs

    def check_exit_signals(self):
        """Check take profit and stop loss signals for all positions."""
        if not hasattr(self, 'portfolio') or self.portfolio is None:
            return

        current_price = self.current_price
        for symbol, position in self.portfolio.positions.items():
            entry_price = position.entry_price
            # Calculate percentage change
            pct_change = (current_price - entry_price) / entry_price * 100
            if position.side == OrderSide.SELL:
                pct_change = -pct_change  # For short positions, price decrease is profit

            # Check take profit
            if self.take_profit_pct is not None and pct_change >= self.take_profit_pct:
                self.close_position(symbol)
            # Check stop loss
            elif self.stop_loss_pct is not None and pct_change <= -self.stop_loss_pct:
                self.close_position(symbol)

    def set_data(self, data: pd.DataFrame):
        """Set the historical data for the strategy."""
        self.data = data

    @property
    def current_price(self) -> float:
        """Get the current closing price."""
        return self.data.iloc[self.current_idx]['close']

    @property
    def current_timestamp(self) -> datetime:
        """Get the current timestamp."""
        return self.data.index[self.current_idx]

    def next(self):
        """Called for each new data point. Override in subclass."""
        raise NotImplementedError

    def buy(self, size: float, price: Optional[float] = None):
        """Place a buy order."""
        order_type = OrderType.LIMIT if price else OrderType.MARKET
        self.orders.append(Order(
            side=OrderSide.BUY,
            size=size,
            price=price,
            order_type=order_type,
            timestamp=self.current_timestamp
        ))

    def sell(self, size: float, price: Optional[float] = None):
        """Place a sell order."""
        order_type = OrderType.LIMIT if price else OrderType.MARKET
        self.orders.append(Order(
            side=OrderSide.SELL,
            size=size,
            price=price,
            order_type=order_type,
            timestamp=self.current_timestamp
        ))

    def close_position(self, symbol: str = "BTC-USD"):
        """Close all positions for a symbol."""
        if not hasattr(self, 'portfolio') or self.portfolio is None:
            return
        if symbol not in self.portfolio.positions:
            return
        position = self.portfolio.positions[symbol]
        if position.side == OrderSide.BUY:
            self.sell(position.size)
        else:
            self.buy(position.size)

    def get_ohlc(self, lookback: int = 20) -> pd.DataFrame:
        """Get OHLC data for the last N periods."""
        start_idx = max(0, self.current_idx - lookback + 1)
        return self.data.iloc[start_idx:self.current_idx + 1]


class BacktestEngine:
    """
    Main backtesting engine that runs strategies on historical data.
    """

    def __init__(
        self,
        data: pd.DataFrame,
        strategy: Strategy,
        initial_capital: float = 10000.0,
        commission: float = 0.001,
        slippage: float = 0.0
    ):
        """
        Initialize the backtest engine.

        Args:
            data: DataFrame with columns [open, high, low, close, volume]
            strategy: Strategy instance to backtest
            initial_capital: Starting capital
            commission: Commission rate per trade (e.g., 0.001 = 0.1%)
            slippage: Slippage per trade (e.g., 0.0001 = 0.01%)
        """
        self.data = data
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        self.portfolio = Portfolio(initial_capital=initial_capital)
        self.equity_curve: List[Dict] = []

    def _execute_order(self, order: Order, bar: pd.Series) -> Optional[Trade]:
        """Execute an order and return a Trade if filled."""
        symbol = order.symbol

        if order.order_type == OrderType.MARKET:
            # Market orders fill at open of next bar (current bar's open)
            fill_price = bar['open'] * (1 + self.slippage if order.side == OrderSide.BUY else 1 - self.slippage)
        else:
            # Limit orders - check if price was touched
            if order.side == OrderSide.BUY and order.price >= bar['low']:
                fill_price = min(order.price, bar['open'])
            elif order.side == OrderSide.SELL and order.price <= bar['high']:
                fill_price = max(order.price, bar['open'])
            else:
                return None  # Limit order not filled

        # Calculate fee
        order_value = order.size * fill_price
        fee = order_value * self.commission

        # Update portfolio
        if order.side == OrderSide.BUY:
            cost = order_value + fee
            if cost > self.portfolio.cash:
                return None  # Insufficient funds

            self.portfolio.cash -= cost

            if symbol in self.portfolio.positions:
                pos = self.portfolio.positions[symbol]
                if pos.side == OrderSide.BUY:
                    # Add to existing long position
                    total_size = pos.size + order.size
                    pos.entry_price = (pos.entry_price * pos.size + fill_price * order.size) / total_size
                    pos.size = total_size
                else:
                    # Close short position or reduce it
                    if order.size >= pos.size:
                        # Fully close short and potentially flip to long
                        remaining = order.size - pos.size
                        del self.portfolio.positions[symbol]
                        if remaining > 0:
                            self.portfolio.positions[symbol] = Position(
                                symbol=symbol,
                                side=OrderSide.BUY,
                                size=remaining,
                                entry_price=fill_price,
                                entry_time=order.timestamp
                            )
                    else:
                        # Partially close short
                        pos.size -= order.size
            else:
                # New long position
                self.portfolio.positions[symbol] = Position(
                    symbol=symbol,
                    side=OrderSide.BUY,
                    size=order.size,
                    entry_price=fill_price,
                    entry_time=order.timestamp
                )

        else:  # SELL
            proceeds = order_value - fee
            self.portfolio.cash += proceeds

            if symbol in self.portfolio.positions:
                pos = self.portfolio.positions[symbol]
                if pos.side == OrderSide.SELL:
                    # Add to existing short position
                    total_size = pos.size + order.size
                    pos.entry_price = (pos.entry_price * pos.size + fill_price * order.size) / total_size
                    pos.size = total_size
                else:
                    # Close long position or reduce it
                    if order.size >= pos.size:
                        # Fully close long and potentially flip to short
                        remaining = order.size - pos.size
                        del self.portfolio.positions[symbol]
                        if remaining > 0:
                            self.portfolio.positions[symbol] = Position(
                                symbol=symbol,
                                side=OrderSide.SELL,
                                size=remaining,
                                entry_price=fill_price,
                                entry_time=order.timestamp
                            )
                    else:
                        # Partially close long
                        pos.size -= order.size
            else:
                # New short position
                self.portfolio.positions[symbol] = Position(
                    symbol=symbol,
                    side=OrderSide.SELL,
                    size=order.size,
                    entry_price=fill_price,
                    entry_time=order.timestamp
                )

        return Trade(
            side=order.side,
            size=order.size,
            price=fill_price,
            timestamp=order.timestamp,
            symbol=symbol,
            fee=fee
        )

    def run(self) -> Dict[str, Any]:
        """Run the backtest and return results."""
        self.strategy.set_data(self.data)
        self.strategy.portfolio = self.portfolio
        self.strategy.initial_capital = self.initial_capital

        for i in range(len(self.data)):
            self.strategy.current_idx = i
            bar = self.data.iloc[i]

            # Execute any pending orders from previous step
            for order in self.strategy.orders:
                trade = self._execute_order(order, bar)
                if trade:
                    self.portfolio.trades.append(trade)

            # Clear orders after execution attempt
            self.strategy.orders = []

            # Check TP/SL exit signals
            self.strategy.check_exit_signals()

            # Run strategy logic
            self.strategy.next()

            # Record equity
            prices = {"BTC-USD": bar['close']}
            equity = self.portfolio.get_total_value(prices)
            self.equity_curve.append({
                'timestamp': self.data.index[i],
                'equity': equity,
                'cash': self.portfolio.cash,
                'close': bar['close']
            })

        return self._calculate_metrics()

    def _calculate_metrics(self) -> Dict[str, Any]:
        """Calculate performance metrics."""
        equity_df = pd.DataFrame(self.equity_curve).set_index('timestamp')
        returns = equity_df['equity'].pct_change().dropna()

        total_return = (equity_df['equity'].iloc[-1] / self.initial_capital) - 1

        # Annualized metrics (assuming crypto trades 365 days/year)
        periods = len(returns)
        years = periods / 365 if periods > 0 else 1

        cagr = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0

        # Volatility
        volatility = returns.std() * np.sqrt(365)

        # Sharpe ratio (assuming 0% risk-free rate for simplicity)
        sharpe_ratio = (returns.mean() * 365) / (returns.std() * np.sqrt(365)) if returns.std() > 0 else 0

        # Maximum drawdown
        rolling_max = equity_df['equity'].cummax()
        drawdown = (equity_df['equity'] - rolling_max) / rolling_max
        max_drawdown = drawdown.min()

        # Win rate
        trades = self.portfolio.trades
        if trades:
            # Group trades by symbol and side to calculate individual trade P&L
            trade_pnls = []
            for trade in trades:
                # Simplified P&L calculation
                if trade.side == OrderSide.SELL:
                    # Find corresponding buy to calculate profit
                    cost_basis = trade.size * trade.price
                    trade_pnls.append(cost_basis)  # Placeholder - full P&L tracking would need position tracking

            profitable_trades = sum(1 for t in trades if t.side == OrderSide.SELL)
            win_rate = profitable_trades / len(trades) if trades else 0
        else:
            win_rate = 0

        return {
            'total_return': total_return,
            'cagr': cagr,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'num_trades': len(trades),
            'final_equity': equity_df['equity'].iloc[-1],
            'equity_curve': equity_df,
            'trades': trades
        }
