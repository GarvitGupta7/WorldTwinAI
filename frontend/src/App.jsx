import React, { useState, useEffect, useRef } from 'react';
import { apiClient } from './api/client.js';
import { Navbar } from './components/Navbar.jsx';
import { WorldSwitcher } from './components/WorldSwitcher.jsx';
import { LivingWorld } from './views/LivingWorld.jsx';
import { ScenarioStudio } from './views/ScenarioStudio.jsx';
import { FutureBranches } from './views/FutureBranches.jsx';
import { ExperimentLab } from './views/ExperimentLab.jsx';
import { AICopilot } from './views/AICopilot.jsx';
import { InterventionLab } from './views/InterventionLab.jsx';
import { KnowledgeGraph } from './views/KnowledgeGraph.jsx';
import { ResearchReports } from './views/ResearchReports.jsx';

export const App = () => {
  const [currentView, setCurrentView] = useState('living-world');
  const [systemHealth, setSystemHealth] = useState('healthy');

  const [worlds, setWorlds] = useState([]);
  const [activeWorldId, setActiveWorldId] = useState('');
  const [activeBranchId, setActiveBranchId] = useState('');

  const [entities, setEntities] = useState([]);
  const [relationships, setRelationships] = useState([]);
  const [timeline, setTimeline] = useState([]);
  const [currentStep, setCurrentStep] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);

  const [isProposeModalOpen, setIsProposeModalOpen] = useState(false);
  const [proposalPrompt, setProposalPrompt] = useState('A regional hospital with trauma bays, ICU, inpatient wards, nurses, and ambulances');
  const [isProposing, setIsProposing] = useState(false);
  const [proposalResult, setProposalResult] = useState(null);

  const playTimerRef = useRef(null);

  useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash.replace(/^#\/?/, '');
      const [route, queryStr] = hash.split('?');
      if (route) setCurrentView(route);
      if (queryStr) {
        const params = new URLSearchParams(queryStr);
        const w = params.get('world');
        const b = params.get('branch');
        if (w) setActiveWorldId(w);
        if (b) setActiveBranchId(b);
      }
    };

    window.addEventListener('hashchange', handleHashChange);
    handleHashChange();
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  const updateRoute = (view, worldId, branchId) => {
    setCurrentView(view);
    const w = worldId || activeWorldId;
    const b = branchId || activeBranchId;
    window.location.hash = `#/${view}?world=${encodeURIComponent(w)}&branch=${encodeURIComponent(b)}`;
  };

  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    try {
      const h = await apiClient.getHealth();
      setSystemHealth(h.status);

      const wList = await apiClient.listWorlds();
      setWorlds(wList);
      if (wList.length > 0) {
        const initialWorld = activeWorldId && wList.some(w => w.id === activeWorldId)
          ? activeWorldId
          : wList[0].id;
        setActiveWorldId(initialWorld);
      }
    } catch (e) {
      console.error(e);
      setSystemHealth('degraded');
    }
  };

  useEffect(() => {
    if (activeWorldId) {
      loadWorldData(activeWorldId);
    }
  }, [activeWorldId]);

  const loadWorldData = async (worldId) => {
    try {
      const [ents, rels, branches] = await Promise.all([
        apiClient.getEntities(worldId),
        apiClient.getRelationships(worldId),
        apiClient.listBranches(worldId)
      ]);
      setEntities(ents);
      setRelationships(rels);

      if (branches.length > 0) {
        const b = branches[0];
        setActiveBranchId(b.id);
        loadBranchTimeline(b.id);
      } else {
        const b = await apiClient.createBranch(worldId, {
          name: 'Baseline World Operations',
          branch_type: 'baseline',
          seed: 42,
          duration: 30
        });
        await apiClient.simulateBranch(b.id);
        setActiveBranchId(b.id);
        loadBranchTimeline(b.id);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const loadBranchTimeline = async (branchId) => {
    try {
      const tl = await apiClient.getBranchTimeline(branchId);
      setTimeline(tl);
      setCurrentStep(0);
      setIsPlaying(false);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    if (isPlaying) {
      playTimerRef.current = setInterval(() => {
        setCurrentStep(prev => {
          const maxStep = timeline.length > 0 ? timeline[timeline.length - 1].step : 60;
          if (prev >= maxStep) {
            setIsPlaying(false);
            return maxStep;
          }
          return prev + 1;
        });
      }, 500);
    } else {
      if (playTimerRef.current) clearInterval(playTimerRef.current);
    }
    return () => {
      if (playTimerRef.current) clearInterval(playTimerRef.current);
    };
  }, [isPlaying, timeline]);

  const activeWorld = worlds.find(w => w.id === activeWorldId) || worlds[0];

  const handleProposeWorld = async () => {
    setIsProposing(true);
    try {
      const prop = await apiClient.proposeWorld(proposalPrompt);
      setProposalResult(prop);
    } catch (e) {
      alert(e.message || "Failed to propose world");
    } finally {
      setIsProposing(false);
    }
  };

  const handleConfirmWorld = async () => {
    if (!proposalResult) return;
    try {
      const res = await apiClient.confirmWorld(proposalResult);
      alert(`Instantiated new Digital Twin World '${res.name}' (${res.world_id}) with ${res.entity_count} entities!`);
      setIsProposeModalOpen(false);
      setProposalResult(null);
      const wList = await apiClient.listWorlds();
      setWorlds(wList);
      setActiveWorldId(res.world_id);
    } catch (e) {
      alert(e.message || "Failed to instantiate world");
    }
  };

  return (
    <div className="app-shell">
      <Navbar
        currentView={currentView}
        onSelectView={(v) => updateRoute(v)}
        systemHealth={systemHealth}
      />

      <WorldSwitcher
        worlds={worlds}
        activeWorldId={activeWorldId}
        onSelectWorld={(wId) => {
          setActiveWorldId(wId);
          updateRoute(currentView, wId);
        }}
        onOpenCreateModal={() => setIsProposeModalOpen(true)}
      />

      <main className="main-content">
        {activeWorld ? (
          <>
            {currentView === 'living-world' && (
              <LivingWorld
                world={activeWorld}
                entities={entities}
                relationships={relationships}
                timeline={timeline}
                currentStep={currentStep}
                onStepChange={setCurrentStep}
                isPlaying={isPlaying}
                onTogglePlay={() => setIsPlaying(!isPlaying)}
              />
            )}

            {currentView === 'scenario-studio' && (
              <ScenarioStudio
                world={activeWorld}
                activeBranchId={activeBranchId}
                onBranchCreated={(bId) => {
                  setActiveBranchId(bId);
                  loadBranchTimeline(bId);
                  updateRoute('living-world', activeWorld.id, bId);
                }}
              />
            )}

            {currentView === 'future-branches' && (
              <FutureBranches
                world={activeWorld}
                activeBranchId={activeBranchId}
                onSelectBranch={(bId) => {
                  setActiveBranchId(bId);
                  loadBranchTimeline(bId);
                  updateRoute(currentView, activeWorld.id, bId);
                }}
              />
            )}

            {currentView === 'experiment-lab' && (
              <ExperimentLab
                world={activeWorld}
                activeBranchId={activeBranchId}
              />
            )}

            {currentView === 'ai-copilot' && (
              <AICopilot
                world={activeWorld}
                activeBranchId={activeBranchId}
              />
            )}

            {currentView === 'intervention-lab' && (
              <InterventionLab
                world={activeWorld}
                activeBranchId={activeBranchId}
                onForkBranch={(bId) => {
                  setActiveBranchId(bId);
                  loadBranchTimeline(bId);
                  updateRoute('living-world', activeWorld.id, bId);
                }}
              />
            )}

            {currentView === 'knowledge-graph' && (
              <KnowledgeGraph
                world={activeWorld}
                relationships={relationships}
              />
            )}

            {currentView === 'research-reports' && (
              <ResearchReports
                world={activeWorld}
                activeBranchId={activeBranchId}
              />
            )}
          </>
        ) : (
          <div className="loading-screen">Loading Digital Twin Engine...</div>
        )}
      </main>

      {isProposeModalOpen && (
        <div className="modal-backdrop">
          <div className="modal-card">
            <div className="modal-header">
              <h3>GenAI-Assisted World Creation (Proposal Step)</h3>
              <button className="close-btn" onClick={() => setIsProposeModalOpen(false)}>×</button>
            </div>
            <p className="subtext">
              Describe an environment (hospital, airport, factory, smart city).
              The system synthesizes a structured meta-model template for review and confirmation.
            </p>

            <textarea
              rows={3}
              value={proposalPrompt}
              onChange={(e) => setProposalPrompt(e.target.value)}
              className="scenario-textarea"
              placeholder="e.g. A regional hospital with trauma bays, ICU, inpatient wards, nurses, and ambulances"
            />

            <div className="modal-actions">
              <button className="btn-primary" onClick={handleProposeWorld} disabled={isProposing}>
                {isProposing ? 'Synthesizing Proposal...' : '⚡ Generate Template Proposal'}
              </button>
            </div>

            {proposalResult && (
              <div className="proposal-review-box">
                <h4>Proposed World Spec: {proposalResult.name}</h4>
                <div className="badge">{proposalResult.world_type?.toUpperCase()}</div>
                <p>{proposalResult.review_message}</p>
                <div className="meta-list">
                  <div>Entity Types: <strong>{proposalResult.declared_entity_types?.map(e => e.name).join(', ')}</strong></div>
                  <div>Metrics: <strong>{proposalResult.metrics?.map(m => m.name).join(', ')}</strong></div>
                  <div>Scenario Actions: <strong>{proposalResult.scenario_vocabulary?.map(v => v.action).join(', ')}</strong></div>
                </div>

                <div className="confirm-row">
                  <button className="btn-success" onClick={handleConfirmWorld}>
                    Confirm & Instantiate World Into Relational Database
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
