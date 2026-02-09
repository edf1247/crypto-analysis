import { useState } from 'react';
import useBacktestRuns from './hooks/useBacktestRuns';
import BacktestTable from './components/BacktestTable';
import InteractiveChart from './components/InteractiveChart';
import MetricCard from './components/MetricCard';
import BacktestConfigForm from './components/BacktestConfigForm';
import BacktestJobStatus from './components/BacktestJobStatus';
import './App.css';

function App() {
  const { runs, loading, error } = useBacktestRuns();
  const [selectedRunId, setSelectedRunId] = useState<number | null>(null);
  const [showConfigForm, setShowConfigForm] = useState(false);

  if (loading) return <div>Loading backtest runs...</div>;
  if (error) return <div>Error: {error}</div>;

  // Determine which run to display
  const selectedRun = selectedRunId
    ? runs.find(run => run.id === selectedRunId)
    : runs[0] || null;

  const equityCurve = selectedRun?.equity_curve || [];

  return (
    <div className="App">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1>Crypto Backtesting Results</h1>
        <button onClick={() => setShowConfigForm(!showConfigForm)}>
          {showConfigForm ? 'Hide Config Form' : 'New Backtest'}
        </button>
      </div>
      {showConfigForm && (
        <BacktestConfigForm onSuccess={() => setShowConfigForm(false)} />
      )}
      <BacktestJobStatus refreshInterval={5000} showCompleted={false} />

      {/* Run Selection Dropdown */}
      {runs.length > 1 && (
        <div className="run-selector">
          <label htmlFor="run-select">Select Backtest Run: </label>
          <select
            id="run-select"
            value={selectedRunId || runs[0]?.id || ''}
            onChange={(e) => setSelectedRunId(Number(e.target.value))}
          >
            {runs.map(run => (
              <option key={run.id} value={run.id}>
                {run.strategy_name} - {run.symbol} ({run.timeframe}) - {new Date(run.created_at).toLocaleDateString()}
              </option>
            ))}
          </select>
        </div>
      )}

      <div className="metrics-grid">
        {selectedRun && (
          <>
            <MetricCard title="Strategy" value={selectedRun.strategy_name} />
            <MetricCard title="Symbol" value={selectedRun.symbol} />
            <MetricCard title="Timeframe" value={selectedRun.timeframe} />
            <MetricCard title="Total Return" value={`${selectedRun.total_return.toFixed(2)}%`} />
            <MetricCard title="Sharpe Ratio" value={selectedRun.sharpe_ratio.toFixed(2)} />
            <MetricCard title="Max Drawdown" value={`${selectedRun.max_drawdown.toFixed(2)}%`} />
            <MetricCard title="Num Trades" value={selectedRun.num_trades} />
          </>
        )}
      </div>

      <div className="chart-section">
        <h2>Backtest Visualization</h2>
        {equityCurve.length > 0 ? (
          <InteractiveChart equityCurve={equityCurve} />
        ) : (
          <p>No equity curve data available.</p>
        )}
      </div>

      <div className="table-section">
        <h2>Recent Backtest Runs</h2>
        <BacktestTable runs={runs} />
      </div>
    </div>
  );
}

export default App;
