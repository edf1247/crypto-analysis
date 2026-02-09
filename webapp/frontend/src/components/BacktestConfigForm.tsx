import { useState, useEffect } from 'react';
import { fetchStrategies, createBacktestJob } from '../services/api';
import type { BacktestJobCreate, StrategyInfo } from '../services/api';

interface BacktestConfigFormProps {
  onSuccess?: () => void;
}

const BacktestConfigForm = ({ onSuccess }: BacktestConfigFormProps) => {
  const [strategies, setStrategies] = useState<StrategyInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // Form fields
  const [strategyName, setStrategyName] = useState('');
  const [strategyParams, setStrategyParams] = useState<Record<string, unknown>>({});
  const [symbol, setSymbol] = useState('BTCUSDT');
  const [interval, setInterval] = useState('1d');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [initialCapital, setInitialCapital] = useState(10000);
  const [takeProfitPct, setTakeProfitPct] = useState<number | undefined>(5);
  const [stopLossPct, setStopLossPct] = useState<number | undefined>(3);

  useEffect(() => {
    const loadStrategies = async () => {
      try {
        const data = await fetchStrategies();
        setStrategies(data);
        if (data.length > 0) {
          setStrategyName(data[0].name);
          // Initialize default params from first strategy
          const defaultParams: Record<string, unknown> = {};
          data[0].parameters.forEach(param => {
            if (param.default !== undefined) {
              defaultParams[param.name] = param.default;
            }
          });
          setStrategyParams(defaultParams);
        }
      } catch (err) {
        setError('Failed to load strategies');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    loadStrategies();
  }, []);

  const handleStrategyChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const name = e.target.value;
    setStrategyName(name);
    const selected = strategies.find(s => s.name === name);
    if (selected) {
      const defaultParams: Record<string, unknown> = {};
      selected.parameters.forEach(param => {
        if (param.default !== undefined) {
          defaultParams[param.name] = param.default;
        }
      });
      setStrategyParams(defaultParams);
    }
  };

  const handleParamChange = (paramName: string, value: string) => {
    setStrategyParams(prev => ({
      ...prev,
      [paramName]: value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const job: BacktestJobCreate = {
        strategy_name: strategyName,
        strategy_params: strategyParams,
        symbol,
        interval,
        start_date: startDate || undefined,
        end_date: endDate || undefined,
        initial_capital: initialCapital,
        take_profit_pct: takeProfitPct,
        stop_loss_pct: stopLossPct,
      };
      await createBacktestJob(job);
      if (onSuccess) onSuccess();
      // Reset form?
      alert('Backtest job created! It will run in the background.');
    } catch (err) {
      setError('Failed to create backtest job');
      console.error(err);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <div>Loading strategies...</div>;

  const selectedStrategy = strategies.find(s => s.name === strategyName);

  return (
    <div className="backtest-config-form">
      <h2>Create New Backtest</h2>
      {error && <div className="error">{error}</div>}
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Strategy</label>
          <select value={strategyName} onChange={handleStrategyChange}>
            {strategies.map(strategy => (
              <option key={strategy.name} value={strategy.name}>
                {strategy.name}
              </option>
            ))}
          </select>
        </div>

        {selectedStrategy && selectedStrategy.parameters.map(param => (
          <div key={param.name} className="form-group">
            <label>{param.name}</label>
            <input
              type="text"
              value={String(strategyParams[param.name] || '')}
              onChange={e => handleParamChange(param.name, e.target.value)}
              placeholder={`Default: ${param.default}`}
            />
          </div>
        ))}

        <div className="form-group">
          <label>Symbol</label>
          <input
            type="text"
            value={symbol}
            onChange={e => setSymbol(e.target.value)}
          />
        </div>

        <div className="form-group">
          <label>Interval</label>
          <select value={interval} onChange={e => setInterval(e.target.value)}>
            <option value="1m">1 minute</option>
            <option value="5m">5 minutes</option>
            <option value="15m">15 minutes</option>
            <option value="1h">1 hour</option>
            <option value="4h">4 hours</option>
            <option value="1d">1 day</option>
            <option value="1w">1 week</option>
          </select>
        </div>

        <div className="form-group">
          <label>Start Date (optional)</label>
          <input
            type="date"
            value={startDate}
            onChange={e => setStartDate(e.target.value)}
          />
        </div>

        <div className="form-group">
          <label>End Date (optional)</label>
          <input
            type="date"
            value={endDate}
            onChange={e => setEndDate(e.target.value)}
          />
        </div>

        <div className="form-group">
          <label>Initial Capital</label>
          <input
            type="number"
            value={initialCapital}
            onChange={e => setInitialCapital(Number(e.target.value))}
          />
        </div>

        <div className="form-group">
          <label>Take Profit % (optional)</label>
          <input
            type="number"
            step="0.1"
            value={takeProfitPct || ''}
            onChange={e => setTakeProfitPct(e.target.value ? Number(e.target.value) : undefined)}
          />
        </div>

        <div className="form-group">
          <label>Stop Loss % (optional)</label>
          <input
            type="number"
            step="0.1"
            value={stopLossPct || ''}
            onChange={e => setStopLossPct(e.target.value ? Number(e.target.value) : undefined)}
          />
        </div>

        <button type="submit" disabled={submitting}>
          {submitting ? 'Creating...' : 'Start Backtest'}
        </button>
      </form>
    </div>
  );
};

export default BacktestConfigForm;