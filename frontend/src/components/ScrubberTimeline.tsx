import React, { useState, useEffect } from 'react';
import { TimelineStep } from '../types';

interface ScrubberTimelineProps {
  timeline: TimelineStep[];
  currentStep: number;
  onStepChange: (step: number) => void;
  isPlaying: boolean;
  onTogglePlay: () => void;
}

export const ScrubberTimeline: React.FC<ScrubberTimelineProps> = ({
  timeline,
  currentStep,
  onStepChange,
  isPlaying,
  onTogglePlay
}) => {
  const maxStep = timeline.length > 0 ? timeline[timeline.length - 1].step : 60;
  const currentSnapshot = timeline.find(t => t.step === currentStep) || timeline[0];

  return (
    <div className="scrubber-card">
      <div className="scrubber-header">
        <div className="scrubber-title">
          <span className="mono-label">TIMELINE SCRUBBER</span>
          <span className="step-badge">Step {currentStep} / {maxStep} ({currentSnapshot?.timestamp || 'T+00:00'})</span>
        </div>
        <div className="scrubber-controls">
          <button
            className="ctrl-btn"
            onClick={() => onStepChange(Math.max(0, currentStep - 1))}
            disabled={currentStep <= 0}
          >
            ⏮ Step -1
          </button>
          <button className={`ctrl-btn play-btn ${isPlaying ? 'playing' : ''}`} onClick={onTogglePlay}>
            {isPlaying ? '⏸ Pause' : '▶ Play'}
          </button>
          <button
            className="ctrl-btn"
            onClick={() => onStepChange(Math.min(maxStep, currentStep + 1))}
            disabled={currentStep >= maxStep}
          >
            Step +1 ⏭
          </button>
        </div>
      </div>

      <div className="scrubber-track-container">
        <input
          type="range"
          min={0}
          max={maxStep}
          value={currentStep}
          onChange={(e) => onStepChange(Number(e.target.value))}
          className="timeline-slider"
        />
        <div className="scrubber-ticks">
          <span>T+00:00</span>
          <span>T+15:00</span>
          <span>T+30:00</span>
          <span>T+45:00</span>
          <span>T+60:00</span>
        </div>
      </div>
    </div>
  );
};
