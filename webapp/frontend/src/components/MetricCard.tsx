import React from 'react';

interface MetricCardProps {
  title: string;
  value: string | number;
  description?: string;
}

const MetricCard: React.FC<MetricCardProps> = ({ title, value, description }) => {
  return (
    <div style={{
      border: '1px solid var(--border-color)',
      padding: '1rem',
      borderRadius: '8px',
      backgroundColor: 'var(--bg-secondary)',
      color: 'var(--text-primary)'
    }}>
      <h3>{title}</h3>
      <div style={{ fontSize: '2rem', fontWeight: 'bold' }}>{value}</div>
      {description && <p>{description}</p>}
    </div>
  );
};

export default MetricCard;