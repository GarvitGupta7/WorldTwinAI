/**
 * WorldTwin AI — Production Client Application
 * Features verified GenAI command layer, full-stack state synchronization,
 * interactive timeline scrubber, and dynamic digital twin rendering.
 */

// Global State
const state = {
  currentView: 'living-world',
  systemHealth: 'healthy',
  worlds: [],
  activeWorldId: '',
  activeWorld: null,
  activeBranchId: '',
  branches: [],
  entities: [],
  relationships: [],
  timeline: [],
  currentStep: 0,
  isPlaying: false,
  playTimer: null,
  selectedEntity: null,
  zoom: 1.0,
  // Interventions
  interventions: [],
  interventionRankings: [],
  weights: { benefit: 0.4, safety: 0.3, cost: 0.15, complexity: 0.15 },
  // Copilot
  copilotMessages: [],
  // Reports
  reports: [],
  selectedReport: null
};

// API Helper
async function apiCall(endpoint, options = {}) {
  try {
    const res = await fetch(endpoint, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(options.headers || {})
      }
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || 'API request failed');
    }
    return await res.json();
  } catch (e) {
    console.error(`API Error [${endpoint}]:`, e);
    throw e;
  }
}

// Router
function parseHash() {
  const hash = window.location.hash.replace(/^#\/?/, '');
  const [route, queryStr] = hash.split('?');
  const validViews = [
    'living-world', 'scenario-studio', 'future-branches',
    'experiment-lab', 'ai-copilot', 'intervention-lab',
    'knowledge-graph', 'research-reports'
  ];
  if (route && validViews.includes(route)) {
    state.currentView = route;
  }
  if (queryStr) {
    const params = new URLSearchParams(queryStr);
    const w = params.get('world');
    const b = params.get('branch');
    if (w) state.activeWorldId = w;
    if (b) state.activeBranchId = b;
  }
}

function updateRoute(view, worldId, branchId) {
  state.currentView = view || state.currentView;
  const w = worldId || state.activeWorldId;
  const b = branchId || state.activeBranchId;
  window.location.hash = `#/${state.currentView}?world=${encodeURIComponent(w)}&branch=${encodeURIComponent(b)}`;
  render();
}

window.addEventListener('hashchange', () => {
  parseHash();
  render();
});

// Initialization
async function init() {
  parseHash();
  try {
    const health = await apiCall('/health');
    state.systemHealth = health.status;

    const worlds = await apiCall('/api/worlds');
    state.worlds = worlds;
    if (worlds.length > 0) {
      if (!state.activeWorldId || !worlds.some(w => w.id === state.activeWorldId)) {
        state.activeWorldId = worlds[0].id;
      }
      await loadWorldData(state.activeWorldId);
    }
  } catch (e) {
    state.systemHealth = 'degraded';
    console.error("Init failed:", e);
  }
  render();
}

async function loadWorldData(worldId) {
  try {
    const [world, ents, rels, branches] = await Promise.all([
      apiCall(`/api/worlds/${worldId}`),
      apiCall(`/api/worlds/${worldId}/entities`),
      apiCall(`/api/worlds/${worldId}/relationships`),
      apiCall(`/api/worlds/${worldId}/branches`)
    ]);

    state.activeWorld = world;
    state.entities = ents;
    state.relationships = rels;
    state.branches = branches;

    if (branches.length > 0) {
      if (!state.activeBranchId || !branches.some(b => b.id === state.activeBranchId)) {
        state.activeBranchId = branches[0].id;
      }
      await loadTimeline(state.activeBranchId);
    } else {
      // Create baseline branch
      const b = await apiCall(`/api/worlds/${worldId}/branches`, {
        method: 'POST',
        body: JSON.stringify({ name: 'Baseline Operations', branch_type: 'baseline', seed: 42, duration: 30 })
      });
      await apiCall(`/api/branches/${b.id}/simulate`, { method: 'POST' });
      state.activeBranchId = b.id;
      await loadTimeline(b.id);
    }

    // Load initial copilot greeting
    if (state.copilotMessages.length === 0) {
      state.copilotMessages.push({
        sender: 'assistant',
        text: `WorldTwin GenAI Command Layer active for ${world.name}. Every action follows the verified loop: Intent -> Structured Plan -> Allowlist Validation -> Controlled Execution -> Independent Verification -> Evidence-Backed Response. What would you like to simulate?`
      });
    }
  } catch (e) {
    console.error("Failed loading world data:", e);
  }
}

async function loadTimeline(branchId) {
  try {
    const tl = await apiCall(`/api/branches/${branchId}/timeline`);
    state.timeline = tl;
    state.currentStep = 0;
    stopPlayback();
  } catch (e) {
    console.error("Failed loading timeline:", e);
  }
}

// Scrubber Playback
function togglePlayback() {
  if (state.isPlaying) {
    stopPlayback();
  } else {
    startPlayback();
  }
  render();
}

function startPlayback() {
  state.isPlaying = true;
  state.playTimer = setInterval(() => {
    const maxStep = state.timeline.length > 0 ? state.timeline[state.timeline.length - 1].step : 60;
    if (state.currentStep >= maxStep) {
      stopPlayback();
      render();
      return;
    }
    state.currentStep += 1;
    render();
  }, 500);
}

function stopPlayback() {
  state.isPlaying = false;
  if (state.playTimer) {
    clearInterval(state.playTimer);
    state.playTimer = null;
  }
}

function setScrubberStep(step) {
  state.currentStep = step;
  render();
}

// Global UI Actions
window.switchView = function(viewId) {
  updateRoute(viewId);
};

window.switchWorld = async function(worldId) {
  state.activeWorldId = worldId;
  state.activeBranchId = '';
  await loadWorldData(worldId);
  updateRoute(state.currentView, worldId);
};

window.scrubStep = function(step) {
  setScrubberStep(parseInt(step, 10));
};

window.togglePlay = function() {
  togglePlayback();
};

window.stepDelta = function(delta) {
  const maxStep = state.timeline.length > 0 ? state.timeline[state.timeline.length - 1].step : 60;
  const next = Math.max(0, Math.min(maxStep, state.currentStep + delta));
  setScrubberStep(next);
};

window.adjustZoom = function(delta) {
  if (delta === 0) {
    state.zoom = 1.0;
  } else {
    state.zoom = Math.max(0.6, Math.min(2.5, state.zoom + delta));
  }
  render();
};

window.inspectEntity = function(entId) {
  state.selectedEntity = state.entities.find(e => e.id === entId) || null;
  render();
};

window.closeInspector = function() {
  state.selectedEntity = null;
  render();
};

// Scenario Studio Actions
window.parseScenarioAction = async function() {
  const textarea = document.getElementById('scenario-input');
  if (!textarea) return;
  const text = textarea.value.trim();
  if (!text) return;

  const btn = document.getElementById('btn-parse-scenario');
  btn.disabled = true;
  btn.innerText = 'Parsing with GenAI...';

  try {
    const res = await apiCall(`/api/worlds/${state.activeWorldId}/scenarios/parse`, {
      method: 'POST',
      body: JSON.stringify({ text })
    });
    state.parsedScenario = res;
  } catch (e) {
    alert(e.message);
  } finally {
    btn.disabled = false;
    btn.innerText = '⚡ Parse & Validate Scenario';
    render();
  }
};

window.executeScenarioBranch = async function() {
  if (!state.parsedScenario || !state.parsedScenario.valid) return;
  const btn = document.getElementById('btn-execute-branch');
  if (btn) {
    btn.disabled = true;
    btn.innerText = 'Simulating Branch...';
  }

  try {
    const branch = await apiCall(`/api/worlds/${state.activeWorldId}/branches`, {
      method: 'POST',
      body: JSON.stringify({
        name: `What-If: ${state.parsedScenario.action}`,
        branch_type: 'what_if',
        parent_branch_id: state.activeBranchId || undefined,
        seed: 42,
        duration: 60
      })
    });

    await apiCall(`/api/branches/${branch.id}/simulate`, { method: 'POST' });
    state.activeBranchId = branch.id;
    await loadWorldData(state.activeWorldId);
    updateRoute('living-world', state.activeWorldId, branch.id);
  } catch (e) {
    alert(e.message);
  }
};

// Batch Experiment Action
window.runBatchExperiments = async function() {
  const scenariosText = document.getElementById('batch-scenarios').value;
  const seedsText = document.getElementById('batch-seeds').value;
  const duration = parseInt(document.getElementById('batch-duration').value, 10) || 30;

  const scenarios = scenariosText.split('\n').map(s => s.trim()).filter(Boolean);
  const seeds = seedsText.split(',').map(s => parseInt(s.trim(), 10)).filter(n => !isNaN(n));

  const btn = document.getElementById('btn-run-batch');
  btn.disabled = true;
  btn.innerText = 'Running Combinatorial Batch Matrix...';

  try {
    const res = await apiCall('/api/branches/batch_run', {
      method: 'POST',
      body: JSON.stringify({
        world_id: state.activeWorldId,
        parent_branch_id: state.activeBranchId || undefined,
        scenarios,
        seeds,
        duration
      })
    });
    state.batchResults = res;
    await loadWorldData(state.activeWorldId);
  } catch (e) {
    alert(e.message);
  } finally {
    btn.disabled = false;
    btn.innerText = '⚡ Launch Batch Experiment Suite';
    render();
  }
};

// Copilot Action
window.sendCopilotQuery = async function(customQuery) {
  const input = document.getElementById('copilot-input');
  const query = customQuery || (input ? input.value.trim() : '');
  if (!query) return;

  if (input) input.value = '';
  state.copilotMessages.push({ sender: 'user', text: query });
  state.isCopilotThinking = true;
  render();

  try {
    const res = await apiCall('/api/copilot/turn', {
      method: 'POST',
      body: JSON.stringify({
        world_id: state.activeWorldId,
        query,
        branch_id: state.activeBranchId || undefined
      })
    });

    state.copilotMessages.push({
      sender: 'assistant',
      text: res.response_text,
      payload: res
    });

    // If a new branch was created, reload
    if (res.executed_tools.some(t => t.tool_name === 'run_scenario' && t.success)) {
      await loadWorldData(state.activeWorldId);
    }
  } catch (e) {
    state.copilotMessages.push({
      sender: 'assistant',
      text: `Error executing command layer: ${e.message}`
    });
  } finally {
    state.isCopilotThinking = false;
    render();
  }
};

// Interventions Evaluation
window.evaluateInterventions = async function() {
  const btn = document.getElementById('btn-evaluate-interventions');
  if (btn) {
    btn.disabled = true;
    btn.innerText = 'Simulating Counterfactuals...';
  }

  try {
    const res = await apiCall(`/api/worlds/${state.activeWorldId}/interventions/evaluate`, {
      method: 'POST',
      body: JSON.stringify({
        baseline_branch_id: state.activeBranchId,
        weights: state.weights
      })
    });
    state.interventionRankings = res.rankings;
  } catch (e) {
    alert(e.message);
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerText = '⚡ Run Counterfactual Ranking';
    }
    render();
  }
};

window.updateWeight = function(key, val) {
  state.weights[key] = parseFloat(val);
  const label = document.getElementById(`weight-val-${key}`);
  if (label) label.innerText = state.weights[key].toFixed(2);
};

// Reports Action
window.generateReport = async function() {
  try {
    const rep = await apiCall('/api/reports/generate', {
      method: 'POST',
      body: JSON.stringify({
        world_id: state.activeWorldId,
        branch_id: state.activeBranchId
      })
    });
    state.reports.unshift(rep);
    state.selectedReport = rep;
    render();
  } catch (e) {
    alert(e.message);
  }
};

window.selectReport = async function(repId) {
  try {
    const rep = await apiCall(`/api/reports/${repId}`);
    state.selectedReport = rep;
    render();
  } catch (e) {
    console.error(e);
  }
};

// Propose & Confirm World
window.openProposeModal = function() {
  state.isProposeModalOpen = true;
  state.proposalResult = null;
  render();
};

window.closeProposeModal = function() {
  state.isProposeModalOpen = false;
  render();
};

window.submitProposeWorld = async function() {
  const text = document.getElementById('proposal-text').value;
  if (!text) return;
  const btn = document.getElementById('btn-propose');
  btn.disabled = true;
  btn.innerText = 'Synthesizing Proposal...';

  try {
    const res = await apiCall('/api/worlds/propose', {
      method: 'POST',
      body: JSON.stringify({ description: text })
    });
    state.proposalResult = res;
  } catch (e) {
    alert(e.message);
  } finally {
    btn.disabled = false;
    btn.innerText = '⚡ Generate Template Proposal';
    render();
  }
};

window.confirmWorldCreation = async function() {
  if (!state.proposalResult) return;
  try {
    const res = await apiCall('/api/worlds/confirm', {
      method: 'POST',
      body: JSON.stringify({ template: state.proposalResult })
    });
    alert(`Instantiated new Digital Twin World '${res.name}' (${res.world_id}) with ${res.entity_count} entities!`);
    state.isProposeModalOpen = false;
    const worlds = await apiCall('/api/worlds');
    state.worlds = worlds;
    await window.switchWorld(res.world_id);
  } catch (e) {
    alert(e.message);
  }
};

// RENDER FUNCTION
function render() {
  const root = document.getElementById('root');
  if (!root) return;

  const currentSnapshot = state.timeline.find(t => t.step === state.currentStep) || state.timeline[0];
  const activeEntities = currentSnapshot?.entities || state.entities;
  const currentMetrics = currentSnapshot?.metrics || {};
  const maxStep = state.timeline.length > 0 ? state.timeline[state.timeline.length - 1].step : 60;

  const navTabs = [
    { id: 'living-world', label: 'Living World' },
    { id: 'scenario-studio', label: 'Scenario Studio' },
    { id: 'future-branches', label: 'Future Branches' },
    { id: 'experiment-lab', label: 'Experiment Lab' },
    { id: 'ai-copilot', label: 'AI Copilot' },
    { id: 'intervention-lab', label: 'Intervention Lab' },
    { id: 'knowledge-graph', label: 'Knowledge Graph' },
    { id: 'research-reports', label: 'Research Reports' },
  ];

  // SVG Elements
  const roads = activeEntities.filter(e => e.entity_type === 'road' || e.entity_type === 'corridor');
  const buildings = activeEntities.filter(e => ['building', 'ward', 'terminal', 'zone'].includes(e.entity_type));
  const dynamicEntities = activeEntities.filter(e => ['bus', 'student', 'staff', 'ambulance', 'patient', 'flight'].includes(e.entity_type));

  function getEntityColor(type, st) {
    if (st?.blocked) return '#ef4444';
    if (['building', 'ward', 'terminal', 'zone'].includes(type)) return '#3b82f6';
    if (type === 'road') {
      const ci = st?.congestion_index || 0.2;
      return ci > 0.7 ? '#ef4444' : ci > 0.45 ? '#f59e0b' : '#10b981';
    }
    if (['bus', 'ambulance'].includes(type)) return '#f97316';
    if (['student', 'patient'].includes(type)) return '#06b6d4';
    return '#8b5cf6';
  }

  root.innerHTML = `
    <div class="app-shell">
      <!-- Navbar -->
      <header class="navbar-container">
        <div class="navbar-brand">
          <div class="brand-logo-badge">WT</div>
          <div class="brand-titles">
            <span class="brand-name">WorldTwin AI</span>
            <span class="brand-sub">Generative Digital Twin Platform</span>
          </div>
        </div>

        <nav class="navbar-links">
          ${navTabs.map(t => `
            <button
              class="nav-tab-btn ${state.currentView === t.id ? 'active' : ''}"
              onclick="switchView('${t.id}')"
            >
              ${t.label}
            </button>
          `).join('')}
        </nav>

        <div class="navbar-status">
          <span class="status-indicator ${state.systemHealth === 'healthy' ? 'online' : 'warn'}"></span>
          <span class="status-text">${state.systemHealth.toUpperCase()}</span>
        </div>
      </header>

      <!-- World Switcher -->
      <div class="world-switcher-bar">
        <div class="switcher-left">
          <span class="mono-tag">CURRENT TWIN WORLD</span>
          <select class="world-select" onchange="switchWorld(this.value)">
            ${state.worlds.map(w => `
              <option value="${w.id}" ${w.id === state.activeWorldId ? 'selected' : ''}>
                ${w.name} (${w.world_type.toUpperCase()})
              </option>
            `).join('')}
          </select>
          ${state.activeWorld ? `
            <span class="world-meta">
              Entities: ${state.entities.length} | Declared Types: ${state.activeWorld.schema_definition?.declared_entity_types?.join(', ') || 'N/A'}
            </span>
          ` : ''}
        </div>
        <div class="switcher-right">
          <button class="btn-secondary" onclick="openProposeModal()">+ Propose New World (GenAI)</button>
        </div>
      </div>

      <!-- Main Content -->
      <main class="main-content">
        ${state.currentView === 'living-world' ? `
          <div class="view-container living-world-grid">
            <div class="main-viewport-column">
              <div class="canvas-wrapper">
                <div class="canvas-toolbar">
                  <span class="mono-label">SPATIAL TOPOLOGY & TWIN MAP</span>
                  <div class="zoom-controls">
                    <button onclick="adjustZoom(-0.2)">-</button>
                    <span>${Math.round(state.zoom * 100)}%</span>
                    <button onclick="adjustZoom(0.2)">+</button>
                    <button onclick="adjustZoom(0)">Reset</button>
                  </div>
                </div>

                <svg class="twin-svg-canvas" viewBox="0 0 1000 1000" style="transform: scale(${state.zoom});">
                  <defs>
                    <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
                      <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#1f2937" stroke-width="0.8" />
                    </pattern>
                  </defs>
                  <rect width="1000" height="1000" fill="url(#grid)" />

                  <!-- Relationships -->
                  ${state.relationships.map(rel => {
                    const src = activeEntities.find(e => e.id === rel.source_entity_id);
                    const tgt = activeEntities.find(e => e.id === rel.target_entity_id);
                    if (!src || !tgt) return '';
                    return `
                      <line
                        x1="${src.position.x}" y1="${src.position.y}"
                        x2="${tgt.position.x}" y2="${tgt.position.y}"
                        stroke="#374151" stroke-width="1.2" stroke-dasharray="4 3"
                      />
                    `;
                  }).join('')}

                  <!-- Roads / Corridors -->
                  ${roads.map(r => {
                    const col = getEntityColor(r.entity_type, r.state);
                    const isSel = state.selectedEntity?.id === r.id;
                    return `
                      <g class="map-node-interactive" onclick="inspectEntity('${r.id}')">
                        <circle cx="${r.position.x}" cy="${r.position.y}" r="${isSel ? 16 : 12}" fill="${col}" stroke="${isSel ? '#fff' : '#111827'}" stroke-width="${isSel ? 3 : 1.5}" opacity="0.9" />
                        <text x="${r.position.x + 16}" y="${r.position.y + 4}" fill="#9ca3af" font-size="11" font-family="monospace">${r.name}</text>
                      </g>
                    `;
                  }).join('')}

                  <!-- Buildings / Wards -->
                  ${buildings.map(b => {
                    const isSel = state.selectedEntity?.id === b.id;
                    return `
                      <g class="map-node-interactive" onclick="inspectEntity('${b.id}')">
                        <rect x="${b.position.x - 30}" y="${b.position.y - 20}" width="60" height="40" rx="6" fill="#1e3a8a" stroke="${isSel ? '#60a5fa' : '#3b82f6'}" stroke-width="${isSel ? 3 : 1.5}" opacity="0.9" />
                        <text x="${b.position.x}" y="${b.position.y + 4}" fill="#e5e7eb" font-size="10" font-weight="bold" text-anchor="middle">
                          ${b.name.length > 12 ? b.name.substring(0, 10) + '..' : b.name}
                        </text>
                      </g>
                    `;
                  }).join('')}

                  <!-- Dynamic Entities -->
                  ${dynamicEntities.map(e => {
                    const isSel = state.selectedEntity?.id === e.id;
                    const col = getEntityColor(e.entity_type, e.state);
                    return `
                      <g class="map-node-interactive" onclick="inspectEntity('${e.id}')">
                        <circle cx="${e.position.x}" cy="${e.position.y}" r="${isSel ? 9 : 5}" fill="${col}" stroke="#111827" stroke-width="1" />
                      </g>
                    `;
                  }).join('')}
                </svg>
              </div>

              <!-- Scrubber Timeline -->
              <div class="scrubber-card">
                <div class="scrubber-header">
                  <div class="scrubber-title">
                    <span class="mono-label">TIMELINE SCRUBBER</span>
                    <span class="step-badge">Step ${state.currentStep} / ${maxStep} (${currentSnapshot?.timestamp || 'T+00:00'})</span>
                  </div>
                  <div class="scrubber-controls">
                    <button class="ctrl-btn" onclick="stepDelta(-1)" ${state.currentStep <= 0 ? 'disabled' : ''}>⏮ Step -1</button>
                    <button class="ctrl-btn play-btn ${state.isPlaying ? 'playing' : ''}" onclick="togglePlay()">
                      ${state.isPlaying ? '⏸ Pause' : '▶ Play'}
                    </button>
                    <button class="ctrl-btn" onclick="stepDelta(1)" ${state.currentStep >= maxStep ? 'disabled' : ''}>Step +1 ⏭</button>
                  </div>
                </div>
                <div class="scrubber-track-container">
                  <input
                    type="range" min="0" max="${maxStep}" value="${state.currentStep}"
                    class="timeline-slider" oninput="scrubStep(this.value)"
                  />
                  <div class="scrubber-ticks">
                    <span>T+00:00</span>
                    <span>T+15:00</span>
                    <span>T+30:00</span>
                    <span>T+45:00</span>
                    <span>T+60:00</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Sidebar Metrics Column -->
            <div class="sidebar-metrics-column">
              <div class="section-title">
                <span class="mono-label">LIVE METRICS TELEMETRY</span>
              </div>

              <div class="metrics-list">
                ${state.activeWorld?.schema_definition?.metrics?.map(m => {
                  const val = currentMetrics[m.name] ?? 0.0;
                  const isHealthy = val >= m.healthy_min && val <= m.healthy_max;
                  const pct = Math.min(100, Math.max(0, ((val - (m.healthy_min * 0.5)) / (Math.max(m.healthy_max * 1.5, 1) - (m.healthy_min * 0.5))) * 100));
                  return `
                    <div class="metric-card ${isHealthy ? 'healthy' : 'anomaly'}">
                      <div class="metric-header">
                        <span class="metric-title">${m.display_name}</span>
                        <span class="metric-status-pill ${isHealthy ? 'pill-green' : 'pill-red'}">
                          ${isHealthy ? 'HEALTHY' : 'ANOMALY'}
                        </span>
                      </div>
                      <div class="metric-value-row">
                        <span class="metric-number">${val.toFixed(2)}</span>
                        <span class="metric-unit">${m.unit}</span>
                      </div>
                      <div class="metric-range-bar">
                        <div class="range-track"><div class="range-fill" style="width: ${pct}%;"></div></div>
                        <div class="range-labels">
                          <span>Safe: ${m.healthy_min}</span>
                          <span>Max: ${m.healthy_max}</span>
                        </div>
                      </div>
                    </div>
                  `;
                }).join('')}
              </div>

              ${state.selectedEntity ? `
                <div class="inspector-card">
                  <div class="inspector-header">
                    <span class="mono-tag">ENTITY INSPECTOR</span>
                    <button class="close-btn" onclick="closeInspector()">×</button>
                  </div>
                  <h4>${state.selectedEntity.name}</h4>
                  <div class="inspector-row">
                    <span class="key">Type:</span> <span class="val badge">${state.selectedEntity.entity_type}</span>
                  </div>
                  <div class="inspector-row">
                    <span class="key">ID:</span> <span class="val mono">${state.selectedEntity.id}</span>
                  </div>
                  <div class="inspector-sub">State:</div>
                  <pre class="json-pre">${JSON.stringify(state.selectedEntity.state, null, 2)}</pre>
                  <div class="inspector-sub">Attributes:</div>
                  <pre class="json-pre">${JSON.stringify(state.selectedEntity.attributes, null, 2)}</pre>
                </div>
              ` : ''}
            </div>
          </div>
        ` : ''}

        ${state.currentView === 'scenario-studio' ? `
          <div class="view-container scenario-studio-layout">
            <div class="studio-card">
              <h3>Scenario Studio — Natural Language What-If Engine</h3>
              <p class="subtext">
                Express complex operational disruptions or infrastructure shifts in natural language.
                The GenAI parser resolves intent against the world's declared scenario vocabulary and executes a deterministic simulation branch.
              </p>

              <div class="prompt-input-area">
                <label class="mono-label">NATURAL LANGUAGE SCENARIO PROMPT</label>
                <textarea
                  id="scenario-input"
                  class="scenario-textarea"
                  rows="4"
                  placeholder="e.g. Close Central Academic Avenue for utility repairs"
                >Close Central Academic Avenue for emergency maintenance</textarea>
                <div class="action-row" style="margin-top: 10px;">
                  <button id="btn-parse-scenario" class="btn-primary" onclick="parseScenarioAction()">
                    ⚡ Parse & Validate Scenario
                  </button>
                </div>
              </div>

              ${state.parsedScenario ? `
                <div class="parsed-results-card" style="margin-top: 16px;">
                  <div class="parsed-header">
                    <span class="mono-label">STRUCTURED PARSER TELEMETRY</span>
                    <span class="confidence-badge ${state.parsedScenario.confidence > 0.8 ? 'high' : 'medium'}">
                      Confidence: ${Math.round(state.parsedScenario.confidence * 100)}%
                    </span>
                  </div>
                  <div class="parsed-body">
                    <div class="item-row" style="margin: 8px 0;">
                      <span class="key">Resolved Action:</span>
                      <span class="val bold highlight">${state.parsedScenario.action}</span>
                    </div>
                    <div class="item-row">
                      <span class="key">Extracted Parameters:</span>
                      <pre class="json-pre">${JSON.stringify(state.parsedScenario.parameters, null, 2)}</pre>
                    </div>
                    ${state.parsedScenario.assumptions?.length > 0 ? `
                      <div class="item-row" style="margin-top: 8px;">
                        <span class="key">Modeling Assumptions:</span>
                        <ul class="bullet-list">${state.parsedScenario.assumptions.map(a => `<li>${a}</li>`).join('')}</ul>
                      </div>
                    ` : ''}

                    ${state.parsedScenario.valid ? `
                      <div class="execution-action-bar" style="margin-top: 16px;">
                        <button id="btn-execute-branch" class="btn-success" onclick="executeScenarioBranch()">
                          🚀 Execute Counterfactual Branch Now
                        </button>
                      </div>
                    ` : `
                      <div class="unsupported-box" style="margin-top: 12px; color: #f87171;">
                        ${state.parsedScenario.clarification_question || 'Scenario unsupported.'}
                      </div>
                    `}
                  </div>
                </div>
              ` : ''}
            </div>

            <div class="vocabulary-reference-card">
              <h4>Declared Scenario Vocabulary (${state.activeWorld?.world_type?.toUpperCase()})</h4>
              <div class="vocab-list">
                ${state.activeWorld?.schema_definition?.scenario_vocabulary?.map(v => `
                  <div class="vocab-item" onclick="document.getElementById('scenario-input').value = '${v.example_phrases[0] || v.action}'">
                    <div class="vocab-title">${v.display_name}</div>
                    <div class="vocab-action mono">action: ${v.action}</div>
                    <div class="vocab-desc">${v.description}</div>
                  </div>
                `).join('')}
              </div>
            </div>
          </div>
        ` : ''}

        ${state.currentView === 'future-branches' ? `
          <div class="view-container branches-layout" style="display: grid; grid-template-columns: 360px 1fr; gap: 20px;">
            <div class="branches-list-card">
              <div class="branches-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <h3>Simulation Branches (${state.branches.length})</h3>
                <button class="btn-secondary" onclick="loadWorldData(state.activeWorldId)">Refresh</button>
              </div>
              <div class="branch-items-scroll">
                ${state.branches.map(b => `
                  <div class="branch-card ${b.id === state.activeBranchId ? 'active' : ''}" style="background: #1f2937; padding: 12px; border-radius: 6px; margin-bottom: 10px; cursor: pointer;" onclick="loadTimeline('${b.id}'); state.activeBranchId = '${b.id}'; render();">
                    <div class="b-card-top" style="display: flex; justify-content: space-between;">
                      <span class="mono-id" style="color: #60a5fa;">${b.id}</span>
                      <span class="b-status ${b.status}">${b.status}</span>
                    </div>
                    <h4 style="margin: 4px 0;">${b.name}</h4>
                    <div style="font-size: 11px; color: #9ca3af;">Seed: ${b.seed} | Duration: ${b.duration} steps</div>
                    ${b.parent_branch_id ? `<div style="font-size: 10px; color: #f59e0b; margin-top: 4px;">Chained from: ${b.parent_branch_id}</div>` : ''}
                  </div>
                `).join('')}
              </div>
            </div>

            <div class="branch-comparison-card">
              <h3>Active Branch Inspector: <code>${state.activeBranchId}</code></h3>
              <p class="subtext">Examine terminal metrics, detected threshold anomalies, and trend predictions.</p>

              <div style="margin-top: 16px;">
                <h4>Timeline Snapshots Available: ${state.timeline.length}</h4>
                <p style="color: #9ca3af; font-size: 12px;">Use the Timeline Scrubber on Living World view to inspect dynamic spatial states at any historical simulation step.</p>
              </div>
            </div>
          </div>
        ` : ''}

        ${state.currentView === 'experiment-lab' ? `
          <div class="view-container experiment-lab-layout" style="display: grid; grid-template-columns: 400px 1fr; gap: 20px;">
            <div class="lab-config-card">
              <h3>Batch Resilience Experiment Runner</h3>
              <p class="subtext">
                Executes combinatorial simulation runs across multiple scenario perturbations and stochastic seeds.
                Directly calls the batch execution backend endpoint.
              </p>
              <div class="form-group" style="margin: 12px 0;">
                <label class="mono-label">DISRUPTION SCENARIOS (ONE PER LINE)</label>
                <textarea id="batch-scenarios" class="scenario-textarea" rows="4">Close Central Academic Avenue
Double bus frequency across campus
Stagger class start times by 20 minutes</textarea>
              </div>
              <div class="form-row" style="display: flex; gap: 10px; margin-bottom: 12px;">
                <div class="form-group" style="flex: 1;">
                  <label class="mono-label">RANDOM SEEDS</label>
                  <input type="text" id="batch-seeds" class="text-input" value="42, 101, 2024" />
                </div>
                <div class="form-group" style="flex: 1;">
                  <label class="mono-label">STEPS</label>
                  <input type="number" id="batch-duration" class="text-input" value="30" />
                </div>
              </div>
              <button id="btn-run-batch" class="btn-primary" onclick="runBatchExperiments()">
                ⚡ Launch Batch Experiment Suite
              </button>
            </div>

            <div class="lab-results-card">
              <h3>Combinatorial Stress Matrix</h3>
              ${state.batchResults ? `
                <div class="matrix-table-wrapper" style="margin-top: 14px;">
                  <table class="diff-table">
                    <thead>
                      <tr>
                        <th>Action</th>
                        <th>Seed</th>
                        <th>Branch ID</th>
                        <th>Anomalies</th>
                        <th>Congestion</th>
                        <th>Flow Efficiency</th>
                      </tr>
                    </thead>
                    <tbody>
                      ${state.batchResults.experiments.map(exp => `
                        <tr>
                          <td class="bold">${exp.action}</td>
                          <td><code>${exp.seed}</code></td>
                          <td><code>${exp.branch_id}</code></td>
                          <td><span class="pill ${exp.anomalies_count > 0 ? 'pill-red' : 'pill-green'}">${exp.anomalies_count}</span></td>
                          <td>${exp.final_metrics?.road_congestion ?? 'N/A'}</td>
                          <td>${exp.final_metrics?.system_flow_efficiency ?? 'N/A'}</td>
                        </tr>
                      `).join('')}
                    </tbody>
                  </table>
                </div>
              ` : `
                <div class="placeholder-box" style="margin-top: 20px; color: #6b7280;">
                  Click 'Launch Batch Experiment Suite' to execute parallel counterfactual tests across scenarios and seeds.
                </div>
              `}
            </div>
          </div>
        ` : ''}

        ${state.currentView === 'ai-copilot' ? `
          <div class="view-container copilot-chat-layout">
            <div class="chat-messages-container">
              ${state.copilotMessages.map(m => `
                <div class="chat-bubble ${m.sender}">
                  <div class="bubble-sender mono-tag">
                    ${m.sender === 'user' ? 'OPERATOR' : 'GENAI COMMAND LAYER (VERIFIED)'}
                  </div>
                  <div class="bubble-text" style="margin: 6px 0;">${m.text}</div>

                  ${m.payload ? `
                    <div class="verification-card">
                      <div class="card-header">
                        <span class="mono-label">VERIFIED EXECUTION ARTIFACTS</span>
                        <span class="status-pill pill-${m.payload.status === 'verified' ? 'green' : 'red'}">
                          ${m.payload.status.toUpperCase()}
                        </span>
                      </div>

                      <div class="plan-section">
                        <div class="mono-intent" style="color: #93c5fd; font-family: monospace;">Intent: ${m.payload.structured_plan?.intent}</div>
                        <div class="tool-chips">
                          ${m.payload.structured_plan?.tool_calls?.map(t => `
                            <span class="tool-badge">🔧 ${t.tool_name}</span>
                          `).join('')}
                        </div>
                      </div>

                      ${m.payload.verification_checks?.length > 0 ? `
                        <div class="verif-section" style="margin-top: 10px;">
                          <div class="sub-label mono-label">Independent DB Verification:</div>
                          ${m.payload.verification_checks.map(v => `
                            <div class="verif-row" style="font-size: 11px; margin-top: 4px;">
                              <span>${v.verified ? '✅' : '❌'}</span>
                              <span>${v.details}</span>
                            </div>
                          `).join('')}
                        </div>
                      ` : ''}

                      ${m.payload.citations?.length > 0 ? `
                        <div class="citation-section" style="margin-top: 10px;">
                          <div class="sub-label mono-label">Knowledge Base Citations:</div>
                          <ul class="cite-list" style="margin-left: 16px; font-size: 11px; color: #a5b4fc;">
                            ${m.payload.citations.map(c => `<li>📖 ${c}</li>`).join('')}
                          </ul>
                        </div>
                      ` : ''}
                    </div>
                  ` : ''}
                </div>
              `).join('')}

              ${state.isCopilotThinking ? `
                <div class="chat-bubble assistant loading">
                  Executing verified command loop (Intent → Structured Plan → Validation → Execution → DB Verification)...
                </div>
              ` : ''}
            </div>

            <div class="chat-input-bar">
              <div class="quick-prompts">
                <button onclick="sendCopilotQuery('What if we close Central Academic Avenue?')">"What if we close Central Academic Avenue?"</button>
                <button onclick="sendCopilotQuery('Evaluate interventions to mitigate this congestion')">"Evaluate interventions to mitigate this congestion"</button>
                <button onclick="sendCopilotQuery('Generate a research audit report')">"Generate a research audit report"</button>
                <button onclick="sendCopilotQuery('Explain the campus transportation master plan')">"Explain campus mobility guidelines"</button>
              </div>
              <div class="input-row">
                <input
                  type="text"
                  id="copilot-input"
                  class="chat-text-input"
                  placeholder="Issue a verified natural language digital twin command..."
                  onkeydown="if (event.key === 'Enter') sendCopilotQuery()"
                />
                <button class="btn-primary" onclick="sendCopilotQuery()">Send</button>
              </div>
            </div>
          </div>
        ` : ''}

        ${state.currentView === 'intervention-lab' ? `
          <div class="view-container intervention-lab-layout" style="display: grid; grid-template-columns: 360px 1fr; gap: 20px;">
            <div class="weights-sidebar-card">
              <h3>Multi-Objective Weights</h3>
              <p class="subtext">
                Adjust trade-off priorities. Sliders are wired directly to the backend counterfactual evaluation call.
              </p>

              <div class="slider-group" style="margin: 14px 0;">
                <div class="slider-header" style="display: flex; justify-content: space-between;">
                  <span>Observed Benefit</span>
                  <span id="weight-val-benefit" class="mono">${state.weights.benefit.toFixed(2)}</span>
                </div>
                <input type="range" min="0" max="1" step="0.05" value="${state.weights.benefit}" oninput="updateWeight('benefit', this.value)" style="width: 100%;" />
              </div>

              <div class="slider-group" style="margin: 14px 0;">
                <div class="slider-header" style="display: flex; justify-content: space-between;">
                  <span>Safety / Anomaly Gain</span>
                  <span id="weight-val-safety" class="mono">${state.weights.safety.toFixed(2)}</span>
                </div>
                <input type="range" min="0" max="1" step="0.05" value="${state.weights.safety}" oninput="updateWeight('safety', this.value)" style="width: 100%;" />
              </div>

              <div class="slider-group" style="margin: 14px 0;">
                <div class="slider-header" style="display: flex; justify-content: space-between;">
                  <span>Capital Cost Penalty</span>
                  <span id="weight-val-cost" class="mono">${state.weights.cost.toFixed(2)}</span>
                </div>
                <input type="range" min="0" max="1" step="0.05" value="${state.weights.cost}" oninput="updateWeight('cost', this.value)" style="width: 100%;" />
              </div>

              <div class="slider-group" style="margin: 14px 0;">
                <div class="slider-header" style="display: flex; justify-content: space-between;">
                  <span>Operational Complexity Penalty</span>
                  <span id="weight-val-complexity" class="mono">${state.weights.complexity.toFixed(2)}</span>
                </div>
                <input type="range" min="0" max="1" step="0.05" value="${state.weights.complexity}" oninput="updateWeight('complexity', this.value)" style="width: 100%;" />
              </div>

              <button id="btn-evaluate-interventions" class="btn-primary full-width" style="width: 100%; margin-top: 10px;" onclick="evaluateInterventions()">
                ⚡ Run Counterfactual Ranking
              </button>
            </div>

            <div class="intervention-results-card">
              <h3>Empirical Counterfactual Intervention Rankings</h3>
              <p class="subtext">
                Candidate interventions are actually executed as isolated simulation branches and ranked strictly by observed outcome metrics.
              </p>

              <div class="rankings-list" style="margin-top: 16px;">
                ${state.interventionRankings.length > 0 ? state.interventionRankings.map(run => `
                  <div class="ranking-card" style="background: #1f2937; border: 1px solid var(--border-color); padding: 14px; border-radius: 8px; margin-bottom: 12px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                      <h4 style="color: #60a5fa;">#${run.ranking}: ${run.intervention_name}</h4>
                      <span class="composite-score-badge" style="background: #1e3a8a; padding: 2px 8px; border-radius: 4px; font-family: monospace;">Score: ${run.score.toFixed(3)}</span>
                    </div>
                    <div style="display: flex; gap: 16px; margin: 8px 0; font-size: 12px; color: #d1d5db;">
                      <span>Benefit: <strong>${run.observed_benefit.toFixed(2)}/10</strong></span>
                      <span>Cost: <strong>${run.cost.toFixed(1)}/10</strong></span>
                      <span>Complexity: <strong>${run.complexity.toFixed(1)}/10</strong></span>
                      <span>Anomaly Delta: <strong>${run.outcome_metrics?.anomaly_delta}</strong></span>
                    </div>
                    <div style="font-size: 11px; color: #9ca3af;">
                      Simulated Counterfactual Branch: <code>${run.counterfactual_branch_id}</code>
                    </div>
                  </div>
                `).join('') : `
                  <div class="placeholder-box" style="color: #6b7280; padding: 20px 0;">
                    Click 'Run Counterfactual Ranking' to execute counterfactual runs against baseline branch <code>${state.activeBranchId}</code>.
                  </div>
                `}
              </div>
            </div>
          </div>
        ` : ''}

        ${state.currentView === 'knowledge-graph' ? `
          <div class="view-container knowledge-layout" style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
            <div class="knowledge-search-card">
              <h3>Domain Knowledge Base (RAG)</h3>
              <p class="subtext">Operational procedures and safety regulations for ${state.activeWorld?.name}.</p>
              <div style="margin-top: 14px;">
                <button class="btn-secondary" onclick="apiCall('/api/worlds/' + state.activeWorldId + '/knowledge/search?q=mobility').then(docs => { alert('Found ' + docs.length + ' operational guidelines.'); })">
                  Query Mobility Guidelines
                </button>
              </div>
            </div>

            <div class="topology-relations-card">
              <h3>Declared Relationship Graph</h3>
              <div class="rel-list" style="margin-top: 14px;">
                ${state.activeWorld?.schema_definition?.declared_relationship_types?.map(r => `
                  <div class="rel-type-item" style="padding: 8px 0; border-bottom: 1px solid #1f2937;">
                    <span class="mono bold" style="color: #60a5fa;">${r.source_entity_type}</span>
                    <span style="color: #6b7280; margin: 0 8px;">──[${r.relationship_type}]──▶</span>
                    <span class="mono bold" style="color: #34d399;">${r.target_entity_type}</span>
                  </div>
                `).join('')}
              </div>
            </div>
          </div>
        ` : ''}

        ${state.currentView === 'research-reports' ? `
          <div class="view-container reports-layout" style="display: grid; grid-template-columns: 360px 1fr; gap: 20px;">
            <div class="reports-sidebar-card">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px;">
                <h3>Audits & Reports</h3>
                <button class="btn-primary" onclick="generateReport()">+ New Report</button>
              </div>
              <div class="reports-scroll-list">
                ${state.reports.map(r => `
                  <div class="report-item-card ${state.selectedReport?.id === r.id ? 'active' : ''}" style="background: #1f2937; padding: 10px; border-radius: 6px; margin-bottom: 8px; cursor: pointer;" onclick="selectReport('${r.id}')">
                    <h4>${r.title}</h4>
                    <p style="font-size: 11px; color: #9ca3af; margin: 4px 0;">${r.summary}</p>
                  </div>
                `).join('')}
              </div>
            </div>

            <div class="report-viewer-card">
              ${state.selectedReport ? `
                <pre class="report-markdown-pre">${state.selectedReport.content}</pre>
              ` : `
                <div class="placeholder-box" style="color: #6b7280;">Click '+ New Report' to generate a research audit for the active branch.</div>
              `}
            </div>
          </div>
        ` : ''}
      </main>

      <!-- Propose World Modal -->
      ${state.isProposeModalOpen ? `
        <div class="modal-backdrop">
          <div class="modal-card">
            <div class="modal-header">
              <h3>GenAI-Assisted World Creation (Proposal Step)</h3>
              <button class="close-btn" onclick="closeProposeModal()">×</button>
            </div>
            <p class="subtext">
              Describe an environment (hospital, airport, factory, smart city).
              The system synthesizes a structured meta-model template for your review and explicit approval.
            </p>
            <textarea
              id="proposal-text"
              class="scenario-textarea"
              rows="3"
              placeholder="e.g. A regional hospital with trauma bays, ICU, inpatient wards, nurses, and ambulances"
            >A regional hospital with trauma bays, ICU, inpatient wards, nurses, and ambulances</textarea>
            <div style="margin-top: 10px;">
              <button id="btn-propose" class="btn-primary" onclick="submitProposeWorld()">⚡ Generate Template Proposal</button>
            </div>

            ${state.proposalResult ? `
              <div class="proposal-review-box" style="background: #1f2937; padding: 14px; border-radius: 6px; margin-top: 14px;">
                <h4>Proposed Spec: ${state.proposalResult.name}</h4>
                <div class="badge" style="margin: 6px 0;">${state.proposalResult.world_type.toUpperCase()}</div>
                <p style="font-size: 12px; color: #d1d5db;">${state.proposalResult.review_message}</p>
                <div style="margin: 10px 0; font-size: 11px;">
                  <div>Entities: <strong>${state.proposalResult.declared_entity_types?.map(e => e.name).join(', ')}</strong></div>
                  <div>Metrics: <strong>${state.proposalResult.metrics?.map(m => m.name).join(', ')}</strong></div>
                </div>
                <button class="btn-success" onclick="confirmWorldCreation()">
                  Confirm & Instantiate World Into Relational Database
                </button>
              </div>
            ` : ''}
          </div>
        </div>
      ` : ''}
    </div>
  `;
}

// Start app on DOM ready
document.addEventListener('DOMContentLoaded', init);
