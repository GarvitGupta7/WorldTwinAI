import React, { useState } from 'react';
import { World } from '../types';
import { apiClient } from '../api/client';

interface ExperimentLabProps {
  world: World;
  activeBranchId?: string;
}

export const ExperimentLab: React.FC<ExperimentLabProps> = ({ world, activeBranchId }) => {
  const [scenariosText, setScenariosText] = useState<string>(
    "Close Central Academic Avenue\nDouble bus frequency across campus\nStagger class start times by 20 minutes"
  );
  const [seeds, setSeeds] = useState<string>("42, 101, 2024");
  const [duration, setDuration] = useState<number>(30);
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [results, setResults] = useState<any>(null);

  const handleRunBatch = async () => {
    setIsRunning(true);
    try {
      const scenarioList = scenariosText.split('\n').map(s => s.trim()).filter(Boolean);
      const seedList = seeds.split(',').map(s => parseInt(s.trim(), 10)).filter(n => !isNaN(n));
      const res = await apiClient.runBatchExperiments({
        world_id: world.id,
        parent_branch_id: activeBranchId,
        scenarios: scenarioList,
        seeds: seedList,
        duration: Number(duration)
      });
      setResults(res);
    } catch (e: any) {
      alert(e.message || 'Batch experiment failed');
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="view-container experiment-lab-layout">
      <div className="lab-config-card">
        <h3>Batch Resilience Experiment Runner</h3>
        <p className="subtext">
          Executes combinatorial simulation runs across multiple scenario perturbations and stochastic seeds.
          Backed by the high-throughput batch backend API.
        </p>

        <div className="form-group">
          <label className="mono-label">DISRUPTION SCENARIOS (ONE PER LINE)</label>
          <textarea
            rows={4}
            value={scenariosText}
            onChange={(e) => setScenariosText(e.target.value)}
            className="scenario-textarea"
          />
        </div>

        <div className="form-row">
          <div className="form-group">
            <label className="mono-label">RANDOM SEEDS (COMMA-SEPARATED)</label>
            <input
              type="text"
              value={seeds}
              onChange={(e) => setSeeds(e.target.value)}
              className="text-input"
            />
          </div>
          <div className="form-group">
            <label className="mono-label">SIMULATION STEPS</label>
            <input
              type="number"
              value={duration}
              onChange={(e) => setDuration(Number(e.target.value))}
              className="text-input"
            />
          </div>
        </div>

        <button className="btn-primary" onClick={handleRunBatch} disabled={isRunning}>
          {isRunning ? 'Running Combinatorial Batch Matrix...' : '⚡ Launch Batch Experiment Suite'}
        </button>
      </div>

      <div className="lab-results-card">
        <h3>Experiment Execution Matrix</h3>
        {results ? (
          <div className="matrix-table-wrapper">
            <table className="diff-table">
              <thead>
                <tr>
                  <th>Action</th>
                  <th>Scenario</th>
                  <th>Seed</th>
                  <th>Branch ID</th>
                  <th>Anomalies</th>
                  <th>Terminal Congestion</th>
                  <th>Flow Efficiency</th>
                </tr>
              </thead>
              <tbody>
                {results.experiments.map((exp: any, i: number) => (
                  <tr key={i}>
                    <td className="bold">{exp.action}</td>
                    <td>{exp.scenario}</td>
                    <td><code>{exp.seed}</code></td>
                    <td><code>{exp.branch_id}</code></td>
                    <td>
                      <span className={`pill ${exp.anomalies_count > 0 ? 'pill-red' : 'pill-green'}`}>
                        {exp.anomalies_count}
                      </span>
                    </td>
                    <td>{exp.final_metrics?.road_congestion ?? 'N/A'}</td>
                    <td>{exp.final_metrics?.system_flow_efficiency ?? 'N/A'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="placeholder-box">
            Configure parameters and launch the batch experiment runner to view empirical stress-testing metrics.
          </div>
        )}
      </div>
    </div>
  );
};
