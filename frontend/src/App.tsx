import React, { useState, useEffect, useRef } from 'react';
import { World, Entity, Relationship, TimelineStep } from './types';
import { apiClient } from './api/client';
import { Navbar } from './components/Navbar';
import { WorldSwitcher } from './components/WorldSwitcher';
import { LivingWorld } from './views/LivingWorld';
import { ScenarioStudio } from './views/ScenarioStudio';
import { FutureBranches } from './views/FutureBranches';
import { ExperimentLab } from './views/ExperimentLab';
import { AICopilot } from './views/AICopilot';
import { InterventionLab } from './views/InterventionLab';
import { KnowledgeGraph } from './views/KnowledgeGraph';
import { ResearchReports } from './views/ResearchReports';

export const App: React.FC = () => {
  // Navigation & routing
  const [currentView, setCurrentView] = useState<string>('living-world');
  const [systemHealth, setSystemHealth] = useState<string>('healthy');

  // Worlds & active state
  const [worlds, setWorlds] = useState<World[]>([]);
  const [activeWorldId, setActiveWorldId] = useState<string>('');
  const [activeBranchId, setActiveBranchId] = useState<string>('');

  // World entities & telemetry
  const [entities, setEntities] = useState<Entity[]>([]);
  const [relationships, setRelationships] = useState<Relationship[]>([]);
  const [timeline, setTimeline] = useState<TimelineStep[]>([]);
  const [currentStep, setCurrentStep] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);

  // Proposal modal
  const [isProposeModalOpen, setIsProposeModalOpen] = useState<boolean>(false);
  const [proposalPrompt, setProposalPrompt] = useState<string>('A regional hospital with trauma bays, ICU, inpatient wards, nurses, and ambulances');
  const [isProposing, setIsProposing] = useState<boolean>(false);
  const [proposalResult, setProposalResult] = useState<any>(null);

  // Interval timer for playback
  const playTimerRef = useRef<any>(null);

  // Read initial route from URL Hash
  useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash.replace(/^#\/?/, '');
      const [route, queryStr] = hash.split('?');
      if (route) {
        setCurrentView(route);
      }
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

  // Sync state to URL hash
  const updateRoute = (view: string, worldId?: string, branchId?: string) => {
    setCurrentView(view);
    const w = worldId || activeWorldId;
    const b = branchId || activeBranchId;
    const hash = `#/${view}?world=${encodeURIComponent(w)}&branch=${encodeURIComponent(b)}`;
    window.location.hash = hash;
  };

  // Initial load
  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    try {
      // Check health
      const h = await apiClient.getHealth();
      setSystemHealth(h.status);

      // List worlds
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

  // When active world changes, load entities & branches
  useEffect(() => {
    if (activeWorldId) {
      loadWorldData(activeWorldId);
    }
  }, [activeWorldId]);

  const loadWorldData = async (worldId: string) => {
    try {
      const [ents, rels, branches] = await Promise.all([
        apiClient.getEntities(worldId),
        apiClient.getRelationships(worldId),
        apiClient.listBranches(worldId)
      ]);
      setEntities(ents);
      setRelationships(rels);

      // Select or create branch
      if (branches.length > 0) {
        const b = branches[0];
        setActiveBranchId(b.id);
        loadBranchTimeline(b.id);
      } else {
        // Auto create baseline branch if none exists
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

  const loadBranchTimeline = async (branchId: string) => {
    try {
      const tl = await apiClient.getBranchTimeline(branchId);
      setTimeline(tl);
      setCurrentStep(0);
      setIsPlaying(false);
    } catch (e) {
      console.error(e);
    }
  };

  // Scrubber playback effect
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
    } catch (e: any) {
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
      // Reload worlds
      const wList = await apiClient.listWorlds();
      setWorlds(wList);
      setActiveWorldId(res.world_id);
    } catch (e: any) {
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

      {/* Propose World Modal */}
      {isProposeModalOpen && (
        <div className="modal-backdrop">
          <div className="modal-card">
            <div className="modal-header">
              <h3>GenAI-Assisted World Creation (Proposal Step)</h3>
              <button className="close-btn" onClick={() => setIsProposeModalOpen(false)}>×</button>
            </div>
            <p className="subtext">
              Describe an environment (hospital, airport, factory, smart city).
              The system synthesizes a structured meta-model template for your review and explicit approval.
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
                <div className="badge">{proposalResult.world_type.toUpperCase()}</div>
                <p>{proposalResult.review_message}</p>
                <div className="meta-list">
                  <div>Entity Types: <strong>{proposalResult.declared_entity_types?.map((e: any) => e.name).join(', ')}</strong></div>
                  <div>Metrics: <strong>{proposalResult.metrics?.map((m: any) => m.name).join(', ')}</strong></div>
                  <div>Scenario Actions: <strong>{proposalResult.scenario_vocabulary?.map((v: any) => v.action).join(', ')}</strong></div>
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
