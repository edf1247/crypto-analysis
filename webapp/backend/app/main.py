from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import backtest_runs, backtest_jobs, strategies
import re
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Crypto Backtesting Webapp", version="0.1.0")

localhost_regex = r"^https?://localhost:\d+(?=/|$)"
localhost_regex += r"|^https?://127\.0\.0\.1:\d+(?=/|$)"
localhost_regex += r"|^https?://\[::1\]:\d+(?=/|$)"

logger.info(f"CORS regex pattern: {localhost_regex}")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    origin = request.headers.get("origin")
    if origin:
        logger.info(f"Request origin: {origin}")
    response = await call_next(request)
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=[],  # Empty since using regex
    allow_origin_regex=localhost_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(backtest_runs.router, prefix="/api/v1/backtest-runs", tags=["backtest-runs"])
app.include_router(backtest_jobs.router, prefix="/api/v1/backtest-jobs", tags=["backtest-jobs"])
app.include_router(strategies.router, prefix="/api/v1/strategies", tags=["strategies"])

@app.get("/health")
def health_check():
    return {"status": "healthy"}
