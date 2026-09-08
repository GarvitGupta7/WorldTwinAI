import React, { useState } from 'react';
import { apiClient } from '../api/client.js';



export const ScenarioStudio = ({
  world,
  activeBranchId,
  onBranchCreated
}) => {
  const [prompt, setPrompt] = useState('Close Central Academic Avenue for emergency maintenance');
  const [isParsing, setIsParsing] = useState(false);
  const [isSimulating, setIsSimulating] = useState(false);
  const [parsed, setParsed] = useState(null);
  const [error, setError] = useState(null);

  const handleParse = async () => {
    setIsParsing(true);
    setError(null);
    try {
      const res = await apiClient.parseScenario(world.id, prompt);
      setParsed(res);
    } catch (e) {
      setError(e.message || 'Failed to parse scenario');
    } finally {
      setIsParsing(false);
    }
  };

  const handleSimulate = async () => {
    if (!parsed || !parsed.valid) return;
    setIsSimulating(true);
    setError(null);
    try {
      // 1. Create branch
      const branch = await apiClient.createBranch(world.id, {
        name: `What-If: ${parsed.action}`,
        branch_type: 'what_if',
        parent_branch_id: activeBranchId,
        seed: 42,
        duration);

      // 2. Simulate branch
      await apiClient.simulateBranch(branch.id);
      onBranchCreated(branch.id);
    } catch (e) {
      setError(e.message || 'Simulation execution failed');
    } finally {
      setIsSimulating(false);
    }
  };

  return (
    <div className="view-container scenario-studio-layout">
      <div className="studio-card">
        <h3>Scenario Studio — Natural Language What-If Engine</h3>
        <p className="subtext">
          Express complex operational disruptions or infrastructure shifts in natural language.
          The engine parses intent into typed scenario vocabulary and executes a deterministic simulation branch.
        </p>

        <div className="prompt-input-area">
          <label className="mono-label">NATURAL LANGUAGE SCENARIO PROMPT</label>
          <textarea
            className="scenario-textarea"
            rows={4}
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="e.g., Close Pavilion Transit Loop for 60 minutes and double bus frequency"
          />
          <div className="action-row">
            <button className="btn-primary" onClick={handleParse} disabled={isParsing}>
              {isParsing ? 'Parsing with GenAI...' : '⚡ Parse & Validate Scenario'}
            </button>
          </div>
        </div>

        {error && <div className="error-banner">{error}</div>}

        {parsed && (
          <div className="parsed-results-card">
            <div className="parsed-header">
              <span className="mono-label">STRUCTURED PARSER TELEMETRY</span>
              <span className={`confidence-badge ${parsed.confidence > 0.8 ? 'high' : 'medium'}`}>
                Confidence)}%
              </span>
            </div>

            <div className="parsed-body">
              <div className="item-row">
                <span className="key">Resolved Action:</span>
                <span className="val bold highlight">{parsed.action}</span>
              </div>
              <div className="item-row">
                <span className="key">Extracted Parameters:</span>
                <pre className="json-pre">{JSON.stringify(parsed.parameters, null, 2)}</pre>
              </div>
              {parsed.assumptions.length > 0 && (
                <div className="item-row">
                  <span className="key">Modeling Assumptions) => <li key={i}>{a}</li>)}
                  </ul>
                </div>
              )}

              {parsed.valid ? (
                <div className="execution-action-bar">
                  <button className="btn-success" onClick={handleSimulate} disabled={isSimulating}>
                    {isSimulating ? 'Simulating Branch...' ) : (
                <div className="unsupported-box">
                  {parsed.clarification_question || 'Scenario not valid for this world vocabulary.'}
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      <div className="vocabulary-reference-card">
        <h4>Declared Scenario Vocabulary ({world.world_type.toUpperCase()})</h4>
        <div className="vocab-list">
          {world.schema_definition?.scenario_vocabulary?.map(v => (
            <div key={v.action} className="vocab-item" onClick={() => setPrompt(v.example_phrases[0] || v.action)}>
              <div className="vocab-title">{v.display_name}</div>
              <div className="vocab-action mono">action: {v.action}</div>
              <div className="vocab-desc">{v.description}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
