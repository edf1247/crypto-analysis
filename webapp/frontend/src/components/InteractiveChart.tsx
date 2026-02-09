import React, { useState } from 'react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

interface ChartDataPoint {
  timestamp: string;
  equity: number;
  close?: number;
}

interface InteractiveChartProps {
  equityCurve: ChartDataPoint[];
  title?: string;
}

const InteractiveChart: React.FC<InteractiveChartProps> = ({
  equityCurve,
  title = 'Backtest Visualization'
}) => {
  const [showEquity, setShowEquity] = useState(true);
  const [showPrice, setShowPrice] = useState(true);

  const labels = equityCurve.map(point => new Date(point.timestamp).toLocaleDateString());

  const datasets = [];

  if (showEquity) {
    datasets.push({
      label: 'Portfolio Equity',
      data: equityCurve.map(point => point.equity),
      borderColor: 'rgb(75, 192, 192)',
      backgroundColor: 'rgba(75, 192, 192, 0.5)',
      yAxisID: 'y',
    });
  }

  if (showPrice && equityCurve[0]?.close !== undefined) {
    datasets.push({
      label: 'Asset Price',
      data: equityCurve.map(point => point.close),
      borderColor: 'rgb(201, 203, 207)',
      backgroundColor: 'rgba(201, 203, 207, 0.5)',
      yAxisID: 'y1',
    });
  }

  const data = { labels, datasets };

  const options = {
    responsive: true,
    interaction: {
      mode: 'index' as const,
      intersect: false,
    },
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
        text: title,
      },
    },
    scales: {
      y: {
        type: 'linear' as const,
        display: showEquity,
        position: 'left' as const,
        title: {
          display: true,
          text: 'Portfolio Equity ($)',
        },
      },
      y1: {
        type: 'linear' as const,
        display: showPrice,
        position: 'right' as const,
        grid: {
          drawOnChartArea: false,
        },
        title: {
          display: true,
          text: 'Asset Price ($)',
        },
      },
    },
  };

  return (
    <div className="interactive-chart">
      <div className="chart-controls">
        <label>
          <input
            type="checkbox"
            checked={showEquity}
            onChange={(e) => setShowEquity(e.target.checked)}
          />
          Show Equity Curve
        </label>
        <label>
          <input
            type="checkbox"
            checked={showPrice}
            onChange={(e) => setShowPrice(e.target.checked)}
            disabled={equityCurve[0]?.close === undefined}
          />
          Show Asset Price
        </label>
      </div>
      <Line options={options} data={data} />
    </div>
  );
};

export default InteractiveChart;