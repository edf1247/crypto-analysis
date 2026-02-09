from typing import Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime
from enum import Enum

class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class BacktestJobBase(BaseModel):
    strategy_name: str
    strategy_params: Dict[str, Any] = {}
    symbol: str = "BTCUSDT"
    interval: str = "1d"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    initial_capital: float
    take_profit_pct: Optional[float] = None
    stop_loss_pct: Optional[float] = None

class BacktestJobCreate(BacktestJobBase):
    pass

class BacktestJobUpdate(BaseModel):
    status: Optional[JobStatus] = None
    error_message: Optional[str] = None
    backtest_run_id: Optional[int] = None

class BacktestJob(BacktestJobBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    status: JobStatus
    error_message: Optional[str] = None
    backtest_run_id: Optional[int] = None

    class Config:
        from_attributes = True