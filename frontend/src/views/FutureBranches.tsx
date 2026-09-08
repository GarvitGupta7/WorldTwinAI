import React, { useState, useEffect } from 'react';
import { World, SimulationBranch } from '../types';
import { apiClient } from '../api/client';

interface FutureBranchesProps {
  world: World;
  activeBranchId?: string;
  onSelectBranch: (branchId: string) => void;
}

export const FutureBranches: React.FC<FutureBranchesProps> = ({
  world,
  activeBranchId,
  onSelectBranch
}) => {
  const [branches, setBranches] = useState<SimulationBranch[]>([]);
  const [compareA, setCompareA] = useState<string>('');
  const [compareB, setCompareB] = useState<string>('');
  const [comparisonResult, setComparisonResult] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    loadBranches();
  }, [world.id]);

  const loadBranches = async () => {
    setLoading(true);
    try {
      const list = await apiClient.listBranches(world.id);
      setBranches(list);
      if (list.length >= 2) {
        setCompareA(list[1].id);
        setCompareB(list[0].id);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleCompare = async () => {
    if (!compareA || !compareB) return;
    try {
      const res = await apiClient.compareBranches(compareA, compareB);
      setComparisonResult(res);
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="view-container branches-layout">
      <div className="branches-list-card">
        <div className="branches-header">
          <h3>Simulation Branches ({branches.length})</h3>
          <button className="btn-secondary" onClick={loadBranches}>Refresh</button>
        </div>

        <div className="branch-items-scroll">
          {branches.map(b => (
            <div
              key={b.id}
              className={`branch-card ${b.id === activeBranchId ? 'active' : ''}`}
              onClick={() => onSelectBranch(b.id)}
            >
              <div className="b-card-top">
                <span className={`branch-badge ${b.branch_type}`}>{b.branch_type.toUpperCase()}</span>
                <span className="mono-id">{b.id}</span>
              </div>
              <h4 className="b-name">{b.name}</h4>
              <div className="b-meta">
                <span>Seed: {b.seed}</span>
                <span>Duration: {b.duration} steps</span>
                <span className={`b-status ${b.status}`}>{b.status}</span>
              </div>
              {b.parent_branch_id && (
                <div className="b-chain-info">
                  Chained from terminal state of: <code>{b.parent_branch_id}</code>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      <div className="branch-comparison-card">
        <h3>Comparative Branch Diff Analyzer</h3>
        <p className="subtext">Compare terminal metrics and anomaly deltas between any two simulation futures.</p>

        <div className="compare-selectors">
          <div className="sel-group">
            <label>Branch A (Baseline / Reference):</label>
            <select value={compareA} onChange={(e) => setCompareA(e.target.value)}>
              {branches.map(b => <option key={b.id} value={b.id}>{b.name} ({b.id})</option>)}
            </select>
          </div>
          <div className="sel-group">
            <label>Branch B (Counterfactual):</label>
            <select value={compareB} onChange={(e) => setCompareB(e.target.value)}>
              {branches.map(b => <option key={b.id} value={b.id}>{b.name} ({b.id})</option>)}
            </select>
          </div>
          <button className="btn-primary" onClick={handleCompare}>Compare</button>
        </div>

        {comparisonResult && (
          <div className="diff-table-wrapper">
            <table className="diff-table">
              <thead>
                <tr>
                  <th>Metric</th>
                  <th>Branch A ({comparisonResult.branch_a.name})</th>
                  <th>Branch B ({comparisonResult.branch_b.name})</th>
                  <th>Delta</th>
                  <th>% Change</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(comparisonResult.metric_comparisons).map(([metricName, comp]: [string, any]) => {
                  const isPositive = comp.absolute_diff >= 0;
                  return (
                    <tr key={metricName}>
                      <td className="mono">{metricName}</td>
                      <td>{comp.branch_a.toFixed(3)}</td>
                      <td>{comp.branch_b.toFixed(3)}</td>
                      <td className={isPositive ? 'text-red' : 'text-green'}>
                        {isPositive ? '+' : ''}{comp.absolute_diff.toFixed(3)}
                      </td>
                      <td className={isPositive ? 'text-red' : 'text-green'}>
                        {comp.percent_change.toFixed(1)}%
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
