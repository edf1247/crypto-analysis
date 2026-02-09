from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.models.backtest_job import BacktestJob, JobStatus
from app.schemas.backtest_job import BacktestJobCreate, BacktestJobUpdate, BacktestJob as BacktestJobSchema
from app.services.backtest_runner import run_backtest_job, STRATEGY_CLASSES

router = APIRouter()

@router.post("/", response_model=BacktestJobSchema, status_code=201)
def create_backtest_job(
    job: BacktestJobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Create a new backtest job.
    The job will be processed asynchronously in the background.
    """
    # Validate strategy name
    if job.strategy_name not in STRATEGY_CLASSES:
        raise HTTPException(status_code=400, detail=f"Unknown strategy: {job.strategy_name}")

    # Create job record
    db_job = BacktestJob(
        **job.dict(),
        status=JobStatus.PENDING,
        created_at=datetime.now(),
        updated_at=None,
        error_message=None,
        backtest_run_id=None
    )

    db.add(db_job)
    db.commit()
    db.refresh(db_job)

    # Queue job for processing
    background_tasks.add_task(run_backtest_job, db_job.id)

    return db_job

@router.get("/", response_model=List[BacktestJobSchema])
def list_backtest_jobs(
    skip: int = 0,
    limit: int = 100,
    status: Optional[JobStatus] = None,
    db: Session = Depends(get_db)
):
    """
    List backtest jobs, optionally filtered by status.
    """
    query = db.query(BacktestJob)
    if status:
        query = query.filter(BacktestJob.status == status)
    jobs = query.order_by(BacktestJob.created_at.desc()).offset(skip).limit(limit).all()
    return jobs

@router.get("/{job_id}", response_model=BacktestJobSchema)
def get_backtest_job(job_id: int, db: Session = Depends(get_db)):
    """
    Get a specific backtest job by ID.
    """
    job = db.query(BacktestJob).filter(BacktestJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Backtest job not found")
    return job

@router.get("/{job_id}/result")
def get_backtest_job_result(job_id: int, db: Session = Depends(get_db)):
    """
    Get the backtest run result for a completed job.
    Returns the BacktestRun record if job completed.
    """
    job = db.query(BacktestJob).filter(BacktestJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Backtest job not found")
    if job.status != JobStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Job not completed")
    if not job.backtest_run_id:
        raise HTTPException(status_code=404, detail="No backtest run associated with job")
    # TODO: Return BacktestRun record
    # For now, return the ID
    return {"backtest_run_id": job.backtest_run_id}