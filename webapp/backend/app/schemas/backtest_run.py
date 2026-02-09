from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime

class BacktestRunBase(BaseModel):
    strategy_name: str
    strategy_params: Dict[str, Any] = {}
    symbol: str = "BTC-USD"
    timeframe: str = "1d"
    initial_capital: float

class BacktestRunCreate(BacktestRunBase):
    metrics: Dict[str, Any] = {}
    equity_curve: List[Dict[str, Any]] = []
    trades: List[Dict[str, Any]] = []
    total_return: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None
    num_trades: Optional[int] = None
    final_equity: Optional[float] = None

class BacktestRun(BacktestRunCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True