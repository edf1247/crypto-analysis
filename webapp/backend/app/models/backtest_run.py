from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Text
from sqlalchemy.sql import func
from app.core.database import Base

class BacktestRun(Base):
    __tablename__ = "backtest_runs"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    strategy_name = Column(String, nullable=False)
    strategy_params = Column(JSON, default=dict)  # JSON dict of parameters
    symbol = Column(String, default="BTC-USD")
    timeframe = Column(String, default="1d")
    initial_capital = Column(Float, nullable=False)

    # Metrics (store as JSON for flexibility)
    metrics = Column(JSON, default=dict)

    # Results data (could be large, consider compression or separate table)
    equity_curve = Column(JSON, default=list)  # list of {timestamp, equity, close}
    trades = Column(JSON, default=list)         # list of trade objects

    # Summary fields for quick display
    total_return = Column(Float)
    sharpe_ratio = Column(Float)
    max_drawdown = Column(Float)
    num_trades = Column(Integer)
    final_equity = Column(Float)