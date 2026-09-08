import React, { useState, useEffect } from 'react';
import { World, Intervention, InterventionRun, MultiObjectiveWeights } from '../types';
import { apiClient } from '../api/client';

interface InterventionLabProps {
  world: World;
  activeBranchId?: string;
  onForkBranch?: (branchId: string) => void;
}

export const InterventionLab: React.FC<InterventionLabProps> = ({
  world,
  activeBranchId,
  onForkBranch
}) => {
  const [interventions, setInterventions] = useState<Intervention[]>([]);
  const [rankings, setRankings] = useState<InterventionRun[]>([]);
  const [isEvaluating, setIsEvaluating] = useState<boolean>(false);
  const [weights, setWeights] = useState<MultiObjectiveWeights>({
    benefit: 0.4,
    safety: 0.3,
    cost: 0.15,
    complexity: 0.15
  });

  useEffect(() => {
    loadInterventions();
  }, [world.id]);

  const loadInterventions = async () => {
    try {
      const list = await apiClient.listInterventions(world.id);
      setInterventions(list);
    } catch (e) {
      console.error(e);
    }
  };

  const handleEvaluate = async () => {
    if (!activeBranchId) {
      alert("Please select an active baseline branch first.");
      return;
    }
    setIsEvaluating(true);
    try {
      const res = await apiClient.evaluateInterventions(world.id, {
        baseline_branch_id: activeBranchId,
        weights: weights
      });
      setRankings(res.rankings);
    } catch (e: any) {
      alert(e.message || "Failed to evaluate interventions");
    } finally {
      setIsEvaluating(false);
    }
  };

  return (
    <div className="view-container intervention-lab-layout">
      <div className="weights-sidebar-card">
        <h3>Multi-Objective Weights</h3>
        <p className="subtext">
          Adjust priorities. Sliders are directly wired to the backend counterfactual scoring engine.
        </p>

        <div className="slider-group">
          <div className="slider-header">
            <span>Observed Benefit</span>
            <span className="mono">{weights.benefit.toFixed(2)}</span>
          </div>
          <input
            type="range"
            min={0}
            max={1}
            step={0.05}
            value={weights.benefit}
            onChange={(e) => setWeights({ ...weights, benefit: Number(e.target.value) })}
          />
        </div>

        <div className="slider-group">
          <div className="slider-header">
            <span>Safety / Anomaly Reduction</span>
            <span className="mono">{weights.safety.toFixed(2)}</span>
          </div>
          <input
            type="range"
            min={0}
            max={1}
            step={0.05}
            value={weights.safety}
            onChange={(e) => setWeights({ ...weights, safety: Number(e.target.value) })}
          />
        </div>

        <div className="slider-group">
          <div className="slider-header">
            <span>Capital Cost Penalty</span>
            <span className="mono">{weights.cost.toFixed(2)}</span>
          </div>
          <input
            type="range"
            min={0}
            max={1}
            step={0.05}
            value={weights.cost}
            onChange={(e) => setWeights({ ...weights, cost: Number(e.target.value) })}
          />
        </div>

        <div className="slider-group">
          <div className="slider-header">
            <span>Operational Complexity Penalty</span>
            <span className="mono">{weights.complexity.toFixed(2)}</span>
          </div>
          <input
            type="range"
            min={0}
            max={1}
            step={0.05}
            value={weights.complexity}
            onChange={(e) => setWeights({ ...weights, complexity: Number(e.target.value) })}
          />
        </div>

        <button className="btn-primary full-width" onClick={handleEvaluate} disabled={isEvaluating}>
          {isEvaluating ? 'Simulating Counterfactuals...' : '⚡ Run Counterfactual Ranking'}
        </button>
      </div>

      <div className="intervention-results-card">
        <h3>Counterfactual Intervention Rankings</h3>
        <p className="subtext">
          Candidate interventions are simulated as isolated counterfactual branches and ranked by empirical performance deltas.
        </p>

        {rankings.length > 0 ? (
          <div className="rankings-list">
            {rankings.map(run => (
              <div key={run.run_id} className={`ranking-card rank-${run.ranking}`}>
                <div className="rank-badge">#{run.ranking}</div>
                <div className="rank-content">
                  <div className="rank-header-row">
                    <h4 className="rank-title">{run.intervention_name}</h4>
                    <span className="composite-score-badge">Score: {run.score.toFixed(3)}</span>
                  </div>
                  <div className="rank-metrics-row">
                    <span>Observed Benefit: <strong>{run.observed_benefit.toFixed(2)}/10</strong></span>
                    <span>Cost: <strong>{run.cost.toFixed(1)}/10</strong></span>
                    <span>Complexity: <strong>{run.complexity.toFixed(1)}/10</strong></span>
                    <span>Anomaly Delta: <strong>{run.outcome_metrics?.anomaly_delta}</strong></span>
                  </div>
                  <div className="branch-link-row">
                    <span>Counterfactual Branch: <code>{run.counterfactual_branch_id}</code></span>
                    {onForkBranch && (
                      <button className="btn-secondary small" onClick={() => onForkBranch(run.counterfactual_branch_id)}>
                        Inspect Branch
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="placeholder-box">
            Click 'Run Counterfactual Ranking' to simulate each candidate intervention as an independent branch and compute empirical trade-off scores.
          </div>
        )}
      </div>
    </div>
  );
};
