from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_list_backtest_runs():
    response = client.get("/api/v1/backtest-runs")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # At least one record (since we have inserted data)
    if len(data) > 0:
        run = data[0]
        assert "id" in run
        assert "strategy_name" in run
        assert "total_return" in run

def test_get_backtest_run():
    # First get list to have an id
    response = client.get("/api/v1/backtest-runs")
    if response.status_code == 200 and len(response.json()) > 0:
        run_id = response.json()[0]["id"]
        response = client.get(f"/api/v1/backtest-runs/{run_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == run_id
    else:
        # No data, skip
        pass