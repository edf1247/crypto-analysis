import { useState, useEffect } from 'react';
import type { BacktestRun } from '../services/api';
import { fetchBacktestRuns } from '../services/api';

const useBacktestRuns = () => {
  const [runs, setRuns] = useState<BacktestRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadRuns = async () => {
      try {
        const data = await fetchBacktestRuns();
        setRuns(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };
    loadRuns();
  }, []);

  return { runs, loading, error };
};

export default useBacktestRuns;