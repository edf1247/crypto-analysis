import React from 'react';
import type { BacktestRun } from '../services/api';

interface BacktestTableProps {
  runs: BacktestRun[];
}

const BacktestTable: React.FC<BacktestTableProps> = ({ runs }) => {
  return (
    <table>
      <thead>
        <tr>
          <th>ID</th>
          <th>Strategy</th>
          <th>Symbol</th>
          <th>Total Return</th>
          <th>Sharpe Ratio</th>
          <th>Max Drawdown</th>
          <th>Num Trades</th>
          <th>Final Equity</th>
        </tr>
      </thead>
      <tbody>
        {runs.map((run) => (
          <tr key={run.id}>
            <td>{run.id}</td>
            <td>{run.strategy_name}</td>
            <td>{run.symbol}</td>
            <td>{run.total_return.toFixed(2)}</td>
            <td>{run.sharpe_ratio.toFixed(2)}</td>
            <td>{run.max_drawdown.toFixed(2)}</td>
            <td>{run.num_trades}</td>
            <td>{run.final_equity.toFixed(2)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
};

export default BacktestTable;