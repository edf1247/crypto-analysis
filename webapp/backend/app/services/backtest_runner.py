import sys
import pandas as pd
from pathlib import Path
from datetime import datetime
from enum import Enum

# Add project root to Python path to allow importing backtest module
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from backtest import BacktestEngine, DataLoader, generate_sample_data
from backtest.strategies import (
    BuyAndHold, SmaCrossover, RSIStrategy, BollingerBandsStrategy,
    MACDStrategy, GridTradingStrategy, TrailingStopStrategy
)
from backtest.scalping_strategy import ScalpingStrategy
from backtest.atr_breakout_strategy import ATRBreakoutStrategy
from app.models.backtest_run import BacktestRun
from app.models.backtest_job import BacktestJob, JobStatus
from app.core.database import SessionLocal

class DataSource(Enum):
    BINANCE = "binance"
    CSV = "csv"
    SYNTHETIC = "synthetic"

# Mapping from strategy name to class
STRATEGY_CLASSES = {
    "BuyAndHold": BuyAndHold,
    "SmaCrossover": SmaCrossover,
    "RSIStrategy": RSIStrategy,
    "BollingerBandsStrategy": BollingerBandsStrategy,
    "MACDStrategy": MACDStrategy,
    "GridTradingStrategy": GridTradingStrategy,
    "TrailingStopStrategy": TrailingStopStrategy,
    "ScalpingStrategy": ScalpingStrategy,
    "ATRBreakoutStrategy": ATRBreakoutStrategy,
}

def fetch_binance_paginated(symbol, interval, start_date=None, end_date=None):
    """
    Fetch Binance data with pagination for date ranges > 1000 candles.
    """
    import time
    all_data = []
    limit = 1000  # Binance max per request
    current_start = start_date
    while True:
        start_ms = int(current_start.timestamp() * 1000) if current_start else None
        end_ms = int(end_date.timestamp() * 1000) if end_date else None
        chunk = DataLoader.fetch_binance(
            symbol=symbol,
            interval=interval,
            limit=limit,
            start_time=start_ms,
            end_time=end_ms
        )
        if chunk.empty:
            break
        all_data.append(chunk)
        # Update current_start to last timestamp + interval
        last_timestamp = chunk.index[-1]
        # If we've reached end_date or beyond, break
        if end_date and last_timestamp >= end_date:
            break
        # Move start to next interval (add 1 ms? actually we need next candle start)
        # Use pandas date offset based on interval
        if interval.endswith('m'):
            minutes = int(interval[:-1])
            next_start = last_timestamp + pd.Timedelta(minutes=minutes)
        elif interval.endswith('h'):
            hours = int(interval[:-1])
            next_start = last_timestamp + pd.Timedelta(hours=hours)
        elif interval.endswith('d'):
            days = int(interval[:-1])
            next_start = last_timestamp + pd.Timedelta(days=days)
        elif interval.endswith('w'):
            weeks = int(interval[:-1])
            next_start = last_timestamp + pd.Timedelta(weeks=weeks)
        else:
            # default 1 day
            next_start = last_timestamp + pd.Timedelta(days=1)
        current_start = next_start
        # Rate limiting
        time.sleep(0.1)
    if not all_data:
        return pd.DataFrame()
    combined = pd.concat(all_data).drop_duplicates().sort_index()
    if start_date:
        combined = combined[combined.index >= start_date]
    if end_date:
        combined = combined[combined.index <= end_date]
    return combined


def serialize_for_json(obj):
    """Recursively convert pandas objects to JSON-serializable types."""
    import numpy as np
    import pandas as pd
    from datetime import datetime, date
    import dataclasses

    if isinstance(obj, pd.DataFrame):
        return obj.reset_index().to_dict('records')
    if isinstance(obj, pd.Series):
        return obj.tolist()
    if isinstance(obj, dict):
        return {k: serialize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [serialize_for_json(v) for v in obj]
    if isinstance(obj, (int, float, str, bool, type(None))):
        return obj
    # Handle numpy scalar types
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    # Handle pandas Timestamp and datetime
    if isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    # Handle dataclasses
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return serialize_for_json(dataclasses.asdict(obj))
    # Handle objects with __dict__ (normal classes)
    if hasattr(obj, '__dict__'):
        return serialize_for_json(obj.__dict__)
    # Fallback: convert to string
    return str(obj)

def run_backtest(strategy_class, strategy_params, symbol="BTC-USD", initial_capital=10000,
                 data_source=DataSource.SYNTHETIC, interval="1d",
                 start_date=None, end_date=None,
                 take_profit_pct=None, stop_loss_pct=None):
    """
    Run a backtest with configurable data source and TP/SL parameters.
    """
    # Load data based on source
    if data_source == DataSource.BINANCE:
        if not start_date or not end_date:
            raise ValueError("Both start_date and end_date required for Binance data source")
        data = fetch_binance_paginated(
            symbol=symbol,
            interval=interval,
            start_date=start_date,
            end_date=end_date
        )
    elif data_source == DataSource.CSV:
        # TODO: Implement CSV loading
        raise NotImplementedError("CSV data source not yet implemented")
    else:  # synthetic
        data = generate_sample_data(periods=365)

    data = DataLoader.add_indicators(data)

    # Merge TP/SL parameters into strategy params
    strategy_params_with_tp_sl = strategy_params.copy()
    if take_profit_pct is not None:
        strategy_params_with_tp_sl['take_profit_pct'] = take_profit_pct
    if stop_loss_pct is not None:
        strategy_params_with_tp_sl['stop_loss_pct'] = stop_loss_pct

    strategy = strategy_class(**strategy_params_with_tp_sl)
    engine = BacktestEngine(
        data=data,
        strategy=strategy,
        initial_capital=initial_capital,
        commission=0.001,
        slippage=0.0001
    )

    results = engine.run()

    # Extract equity curve from results
    equity_curve = []
    if 'equity_curve' in results and hasattr(results['equity_curve'], 'reset_index'):
        equity_df = results['equity_curve']
        equity_curve = equity_df.reset_index().to_dict('records')
    elif isinstance(results.get('equity_curve'), list):
        equity_curve = results['equity_curve']

    # Create BacktestRun record
    db = SessionLocal()
    try:
        run = BacktestRun(
            strategy_name=strategy_class.__name__,
            strategy_params=strategy_params,
            symbol=symbol,
            initial_capital=initial_capital,
            metrics=serialize_for_json(results.get('metrics', {})),
            equity_curve=serialize_for_json(equity_curve),
            trades=serialize_for_json(results.get('trades', [])),
            total_return=serialize_for_json(results.get('total_return')),
            sharpe_ratio=serialize_for_json(results.get('sharpe_ratio')),
            max_drawdown=serialize_for_json(results.get('max_drawdown')),
            num_trades=serialize_for_json(results.get('num_trades')),
            final_equity=serialize_for_json(results.get('final_equity'))
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        return run
    finally:
        db.close()


def run_backtest_job(job_id: int):
    """
    Execute a backtest job by ID.
    Loads job configuration, runs backtest, updates job status and result.
    """
    db = SessionLocal()
    try:
        job = db.query(BacktestJob).filter(BacktestJob.id == job_id).first()
        if not job:
            raise ValueError(f"Backtest job {job_id} not found")

        # Update status to running
        job.status = JobStatus.RUNNING
        job.updated_at = datetime.now()
        db.commit()

        # Determine data source based on start_date/end_date
        if job.start_date and job.end_date:
            data_source = DataSource.BINANCE
        else:
            data_source = DataSource.SYNTHETIC

        # Determine strategy class
        strategy_class = STRATEGY_CLASSES.get(job.strategy_name)
        if not strategy_class:
            raise ValueError(f"Unknown strategy: {job.strategy_name}")

        # Run backtest
        run = run_backtest(
            strategy_class=strategy_class,
            strategy_params=job.strategy_params,
            symbol=job.symbol,
            initial_capital=job.initial_capital,
            data_source=data_source,
            interval=job.interval,
            start_date=job.start_date,
            end_date=job.end_date,
            take_profit_pct=job.take_profit_pct,
            stop_loss_pct=job.stop_loss_pct,
        )

        # Update job with result
        job.status = JobStatus.COMPLETED
        job.backtest_run_id = run.id
        job.updated_at = datetime.now()
        db.commit()

        return run
    except Exception as e:
        # Mark job as failed
        if 'job' in locals():
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            job.updated_at = datetime.now()
            db.commit()
        raise
    finally:
        db.close()
