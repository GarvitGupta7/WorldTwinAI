import React, { useState } from 'react';
import { GraphViewer } from '../components/GraphViewer.jsx';
import { MetricsCard } from '../components/MetricsCard.jsx';
import { ScrubberTimeline } from '../components/ScrubberTimeline.jsx';



export const LivingWorld = ({
  world,
  entities,
  relationships,
  timeline,
  currentStep,
  onStepChange,
  isPlaying,
  onTogglePlay
}) => {
  const [selectedEntity, setSelectedEntity] = useState(null);
  const currentSnapshot = timeline.find(t => t.step === currentStep) || timeline[0];
  const currentMetrics = currentSnapshot?.metrics || {};

  return (
    <div className="view-container living-world-grid">
      <div className="main-viewport-column">
        <GraphViewer
          entities={currentSnapshot?.entities || entities}
          relationships={relationships}
          onSelectEntity={setSelectedEntity}
          selectedEntityId={selectedEntity?.id}
        />

        <ScrubberTimeline
          timeline={timeline}
          currentStep={currentStep}
          onStepChange={onStepChange}
          isPlaying={isPlaying}
          onTogglePlay={onTogglePlay}
        />
      </div>

      <div className="sidebar-metrics-column">
        <div className="section-title">
          <span className="mono-label">LIVE METRICS TELEMETRY</span>
        </div>

        <div className="metrics-list">
          {world.schema_definition?.metrics?.map(m => (
            <MetricsCard
              key={m.name}
              definition={m}
              name={m.name}
              value={currentMetrics[m.name] ?? 0.0}
            />
          ))}
        </div>

        {selectedEntity && (
          <div className="inspector-card">
            <div className="inspector-header">
              <span className="mono-tag">ENTITY INSPECTOR</span>
              <button className="close-btn" onClick={() => setSelectedEntity(null)}>×</button>
            </div>
            <h4>{selectedEntity.name}</h4>
            <div className="inspector-row">
              <span className="key">Type:</span>
              <span className="val badge">{selectedEntity.entity_type}</span>
            </div>
            <div className="inspector-row">
              <span className="key">ID:</span>
              <span className="val mono">{selectedEntity.id}</span>
            </div>
            <div className="inspector-sub">State:</div>
            <pre className="json-pre">{JSON.stringify(selectedEntity.state, null, 2)}</pre>
            <div className="inspector-sub">Attributes:</div>
            <pre className="json-pre">{JSON.stringify(selectedEntity.attributes, null, 2)}</pre>
          </div>
        )}
      </div>
    </div>
  );
};
