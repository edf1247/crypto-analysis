# Crypto Backtesting Webapp

A modular web application to display recent backtesting results from the cryptocurrency backtesting framework.

## Features

- Backend FastAPI server with SQLite database
- REST API endpoints for backtest runs
- React frontend with TypeScript
- Charts for equity curves using Chart.js
- Automated backtest runner script

## Project Structure

```
webapp/
├── backend/           # FastAPI backend
│   ├── app/           # Application code
│   ├── alembic/       # Database migrations
│   ├── scripts/       # Utility scripts
│   └── requirements.txt
└── frontend/          # React frontend
    ├── src/
    │   ├── components/ # React components
    │   ├── hooks/      # Custom hooks
    │   └── services/   # API client
    └── package.json
```

## Quick Start

### Backend Setup

1. Install Python dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. Set up database:
   ```bash
   alembic upgrade head
   ```

3. Run backtest runner to populate data:
   ```bash
   python scripts/run_backtests.py
   ```

4. Start FastAPI server:
   ```bash
   uvicorn app.main:app --reload
   ```

### Frontend Setup

1. Install Node.js dependencies:
   ```bash
   cd frontend
   npm install
   ```

2. Start development server:
   ```bash
   npm run dev
   ```

3. Open browser at `http://localhost:3000`

## API Documentation

Once the backend server is running, visit `http://localhost:8000/docs` for interactive API documentation.

## Development

- Backend tests: `pytest`
- Frontend build: `npm run build`

## Future Enhancements

- User authentication
- Real-time backtest execution via UI
- Additional technical indicators
- Multi-asset support