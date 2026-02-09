import React from 'react';
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

interface EquityChartProps {
  equityCurve: Array<{ timestamp: string; equity: number }>;
}

const EquityChart: React.FC<EquityChartProps> = ({ equityCurve }) => {
  const data = {
    labels: equityCurve.map(point => new Date(point.timestamp).toLocaleDateString()),
    datasets: [
      {
        label: 'Equity',
        data: equityCurve.map(point => point.equity),
        borderColor: 'rgb(75, 192, 192)',
        backgroundColor: 'rgba(75, 192, 192, 0.5)',
      },
    ],
  };

  const options = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
        text: 'Equity Curve',
      },
    },
  };

  return <Line options={options} data={data} />;
};

export default EquityChart;