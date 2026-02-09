## Read Me

### Implementation Plan

- Backtesting Logic - done
- Web interface
    - First, just to see backtest results
    - Add routes to execute a backtest
    - Add routes to add technical indicators
    - Add routes to change crypto asset
    - Update frontend to support
        - Add support for semantic analysis

### CORS Configuration

The web application backend (FastAPI) is configured to allow cross-origin requests from the frontend development server. By default, origins `http://localhost:3000` and `http://localhost:5173` are allowed.

To modify CORS settings:
1. Edit `webapp/backend/app/core/config.py` to change the `CORS_ORIGINS` default list.
2. Or set environment variable `CORS_ORIGINS` in a `.env` file (see `.env.example` for format).
