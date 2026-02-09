import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1';

export interface BacktestRun {
  id: number;
  created_at: string;
  strategy_name: string;
  strategy_params: Record<string, unknown>;
  symbol: string;
  timeframe: string;
  initial_capital: number;
  total_return: number;
  sharpe_ratio: number;
  max_drawdown: number;
  num_trades: number;
  final_equity: number;
  metrics: Record<string, unknown>;
  equity_curve: Array<{ timestamp: string; equity: number; close?: number }>;
  trades: unknown[];
}

export const fetchBacktestRuns = async (): Promise<BacktestRun[]> => {
  const response = await axios.get(`${API_BASE_URL}/backtest-runs/`);
  return response.data;
};

// Backtest Job interfaces
export interface BacktestJob {
  id: number;
  created_at: string;
  updated_at?: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  error_message?: string;
  strategy_name: string;
  strategy_params: Record<string, unknown>;
  symbol: string;
  interval: string;
  start_date?: string;
  end_date?: string;
  initial_capital: number;
  take_profit_pct?: number;
  stop_loss_pct?: number;
  backtest_run_id?: number;
}

export interface BacktestJobCreate {
  strategy_name: string;
  strategy_params: Record<string, unknown>;
  symbol: string;
  interval: string;
  start_date?: string;
  end_date?: string;
  initial_capital: number;
  take_profit_pct?: number;
  stop_loss_pct?: number;
}

export interface StrategyInfo {
  name: string;
  description?: string;
  parameters: Array<{
    name: string;
    type: string;
    default?: any;
    description?: string;
  }>;
}

// Fetch available strategies
export const fetchStrategies = async (): Promise<StrategyInfo[]> => {
  const response = await axios.get(`${API_BASE_URL}/strategies/`);
  return response.data;
};

// Create a new backtest job
export const createBacktestJob = async (job: BacktestJobCreate): Promise<BacktestJob> => {
  const response = await axios.post(`${API_BASE_URL}/backtest-jobs/`, job);
  return response.data;
};

// Get a specific backtest job
export const fetchBacktestJob = async (jobId: number): Promise<BacktestJob> => {
  const response = await axios.get(`${API_BASE_URL}/backtest-jobs/${jobId}`);
  return response.data;
};

// List backtest jobs, optionally filtered by status
export const fetchBacktestJobs = async (status?: string): Promise<BacktestJob[]> => {
  const params = status ? { status } : {};
  const response = await axios.get(`${API_BASE_URL}/backtest-jobs/`, { params });
  return response.data;
};

// Poll job status until completion
export const pollJobStatus = async (jobId: number, interval = 2000): Promise<BacktestJob> => {
  return new Promise((resolve, reject) => {
    const checkStatus = async () => {
      try {
        const job = await fetchBacktestJob(jobId);
        if (job.status === 'completed' || job.status === 'failed') {
          resolve(job);
        } else {
          setTimeout(checkStatus, interval);
        }
      } catch (error) {
        reject(error);
      }
    };
    checkStatus();
  });
};
