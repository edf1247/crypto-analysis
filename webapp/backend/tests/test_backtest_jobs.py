import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.backtest_job import BacktestJob, JobStatus
from app.core.database import SessionLocal
import json

client = TestClient(app)

def test_create_backtest_job():
    """Test creating a new backtest job."""
    payload = {
        "strategy_name": "SmaCrossover",
        "strategy_params": {"fast": 10, "slow": 30, "position_size": 1.0},
        "symbol": "BTCUSDT",
        "interval": "1d",
        "initial_capital": 10000,
        "take_profit_pct": 5.0,
        "stop_loss_pct": 3.0
    }
    response = client.post("/api/v1/backtest-jobs/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["strategy_name"] == "SmaCrossover"
    assert data["status"] == "pending"
    assert data["symbol"] == "BTCUSDT"
    assert data["initial_capital"] == 10000
    # Clean up: delete the created job
    job_id = data["id"]
    db = SessionLocal()
    try:
        job = db.query(BacktestJob).filter(BacktestJob.id == job_id).first()
        if job:
            db.delete(job)
            db.commit()
    finally:
        db.close()

def test_list_backtest_jobs():
    """Test listing backtest jobs."""
    response = client.get("/api/v1/backtest-jobs/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # Optionally, we could create a job first and verify it appears
    # but we'll just ensure the endpoint works.

def test_get_backtest_job():
    """Test retrieving a specific backtest job."""
    # First create a job to have an ID
    payload = {
        "strategy_name": "BuyAndHold",
        "strategy_params": {},
        "symbol": "ETHUSDT",
        "interval": "1d",
        "initial_capital": 5000
    }
    create_resp = client.post("/api/v1/backtest-jobs/", json=payload)
    if create_resp.status_code != 201:
        pytest.skip("Cannot create job for get test")
    job_id = create_resp.json()["id"]

    response = client.get(f"/api/v1/backtest-jobs/{job_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == job_id
    assert data["strategy_name"] == "BuyAndHold"

    # Clean up
    db = SessionLocal()
    try:
        job = db.query(BacktestJob).filter(BacktestJob.id == job_id).first()
        if job:
            db.delete(job)
            db.commit()
    finally:
        db.close()

def test_get_backtest_job_not_found():
    """Test retrieving a non-existent job returns 404."""
    response = client.get("/api/v1/backtest-jobs/999999")
    assert response.status_code == 404

def test_list_backtest_jobs_filter_by_status():
    """Test filtering jobs by status."""
    # Create a job
    payload = {
        "strategy_name": "RSIStrategy",
        "strategy_params": {"period": 14, "oversold": 30, "overbought": 70},
        "symbol": "BTCUSDT",
        "interval": "1h",
        "initial_capital": 1000
    }
    create_resp = client.post("/api/v1/backtest-jobs/", json=payload)
    if create_resp.status_code != 201:
        pytest.skip("Cannot create job for filter test")
    job_id = create_resp.json()["id"]

    # Get the job to see its current status
    job_resp = client.get(f"/api/v1/backtest-jobs/{job_id}")
    job_data = job_resp.json()
    current_status = job_data["status"]
    print(f"Created job status: {current_status}")

    # Filter by current status
    response = client.get(f"/api/v1/backtest-jobs/?status={current_status}")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # Our job should be in the filtered list
    filtered_ids = [job["id"] for job in data if job["status"] == current_status]
    assert job_id in filtered_ids

    # Clean up
    db = SessionLocal()
    try:
        job = db.query(BacktestJob).filter(BacktestJob.id == job_id).first()
        if job:
            db.delete(job)
            db.commit()
    finally:
        db.close()

def test_get_backtest_job_result_not_completed():
    """Test getting result for a job that is not completed."""
    payload = {
        "strategy_name": "SmaCrossover",
        "strategy_params": {"fast": 5, "slow": 20},
        "symbol": "BTCUSDT",
        "interval": "1d",
        "initial_capital": 10000
    }
    create_resp = client.post("/api/v1/backtest-jobs/", json=payload)
    if create_resp.status_code != 201:
        pytest.skip("Cannot create job for result test")
    job_id = create_resp.json()["id"]

    # Get current job status
    job_resp = client.get(f"/api/v1/backtest-jobs/{job_id}")
    job_data = job_resp.json()
    current_status = job_data["status"]
    print(f"Job status: {current_status}")

    response = client.get(f"/api/v1/backtest-jobs/{job_id}/result")
    if current_status == "completed":
        # If job completed, result endpoint should return 200 with backtest_run_id
        assert response.status_code == 200
        data = response.json()
        assert "backtest_run_id" in data
    else:
        # Job not completed, expect 400
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data

    # Clean up
    db = SessionLocal()
    try:
        job = db.query(BacktestJob).filter(BacktestJob.id == job_id).first()
        if job:
            db.delete(job)
            db.commit()
    finally:
        db.close()

# Note: Testing actual job processing (status transitions) would require
# running the background worker, which is beyond unit test scope.
# Integration tests can cover that.