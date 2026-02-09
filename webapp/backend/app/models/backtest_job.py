from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Enum
from sqlalchemy.sql import func
from app.core.database import Base
import enum

class JobStatus(enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class BacktestJob(Base):
    __tablename__ = "backtest_jobs"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    status = Column(Enum(JobStatus), default=JobStatus.PENDING, nullable=False)
    error_message = Column(String, nullable=True)

    # Configuration
    strategy_name = Column(String, nullable=False)
    strategy_params = Column(JSON, default=dict)
    symbol = Column(String, default="BTCUSDT")
    interval = Column(String, default="1d")
    start_date = Column(DateTime)  # or string ISO format
    end_date = Column(DateTime)
    initial_capital = Column(Float, nullable=False)
    take_profit_pct = Column(Float)
    stop_loss_pct = Column(Float)

    # Result reference
    backtest_run_id = Column(Integer, nullable=True)  # FK to BacktestRun