from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.backtest_run import BacktestRun
from app.schemas.backtest_run import BacktestRun as BacktestRunSchema

router = APIRouter()

@router.get("/", response_model=List[BacktestRunSchema])
def list_backtest_runs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    runs = db.query(BacktestRun).order_by(BacktestRun.created_at.desc()).offset(skip).limit(limit).all()
    return runs

@router.get("/{run_id}", response_model=BacktestRunSchema)
def get_backtest_run(run_id: int, db: Session = Depends(get_db)):
    run = db.query(BacktestRun).filter(BacktestRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Backtest run not found")
    return run