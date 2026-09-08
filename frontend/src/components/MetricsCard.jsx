import React from 'react';

export const MetricsCard = ({ definition, name, value = 0 }) => {
  const hMin = definition?.healthy_min ?? 0;
  const hMax = definition?.healthy_max ?? 1;
  const isHealthy = value >= hMin && value <= hMax;
  const displayName = definition?.display_name || name;
  const unit = definition?.unit || '';

  const pct = Math.min(100, Math.max(0, ((value - (hMin * 0.5)) / (Math.max(hMax * 1.5, 1) - (hMin * 0.5))) * 100));

  return (
    <div className={`metric-card ${isHealthy ? 'healthy' : 'anomaly'}`}>
      <div className="metric-header">
        <span className="metric-title">{displayName}</span>
        <span className={`metric-status-pill ${isHealthy ? 'pill-green' : 'pill-red'}`}>
          {isHealthy ? 'HEALTHY' : 'ANOMALY'}
        </span>
      </div>

      <div className="metric-value-row">
        <span className="metric-number">{Number(value).toFixed(2)}</span>
        <span className="metric-unit">{unit}</span>
      </div>

      <div className="metric-range-bar">
        <div className="range-track">
          <div className="range-fill" style={{ width: `${pct}%` }} />
        </div>
        <div className="range-labels">
          <span>Safe: {hMin}</span>
          <span>Max: {hMax}</span>
        </div>
      </div>
    </div>
  );
};
