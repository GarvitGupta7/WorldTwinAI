const BASE_URL = '';

async function handleResponse(res) {
  if (!res.ok) {
    const errorBody = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errorBody.detail || `Request failed with status ${res.status}`);
  }
  return res.json();
}

export const apiClient = {
  async getHealth() {
    const res = await fetch(`${BASE_URL}/health`);
    return handleResponse(res);
  },

  async listWorlds() {
    const res = await fetch(`${BASE_URL}/api/worlds`);
    return handleResponse(res);
  },

  async getWorld(worldId) {
    const res = await fetch(`${BASE_URL}/api/worlds/${worldId}`);
    return handleResponse(res);
  },

  async proposeWorld(description) {
    const res = await fetch(`${BASE_URL}/api/worlds/propose`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ description })
    });
    return handleResponse(res);
  },

  async confirmWorld(template, customName, customWorldId) {
    const res = await fetch(`${BASE_URL}/api/worlds/confirm`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ template, custom_name: customName, custom_world_id: customWorldId })
    });
    return handleResponse(res);
  },

  async getEntities(worldId, entityType) {
    const url = entityType
      ? `${BASE_URL}/api/worlds/${worldId}/entities?entity_type=${encodeURIComponent(entityType)}`
      : `${BASE_URL}/api/worlds/${worldId}/entities`;
    const res = await fetch(url);
    return handleResponse(res);
  },

  async getRelationships(worldId) {
    const res = await fetch(`${BASE_URL}/api/worlds/${worldId}/relationships`);
    return handleResponse(res);
  },

  async parseScenario(worldId, text) {
    const res = await fetch(`${BASE_URL}/api/worlds/${worldId}/scenarios/parse`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text })
    });
    return handleResponse(res);
  },

  async createBranch(worldId, params) {
    const res = await fetch(`${BASE_URL}/api/worlds/${worldId}/branches`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params)
    });
    return handleResponse(res);
  },

  async simulateBranch(branchId) {
    const res = await fetch(`${BASE_URL}/api/branches/${branchId}/simulate`, {
      method: 'POST'
    });
    return handleResponse(res);
  },

  async runBatchExperiments(payload) {
    const res = await fetch(`${BASE_URL}/api/branches/batch_run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse(res);
  },

  async getBranch(branchId) {
    const res = await fetch(`${BASE_URL}/api/branches/${branchId}`);
    return handleResponse(res);
  },

  async getBranchTimeline(branchId) {
    const res = await fetch(`${BASE_URL}/api/branches/${branchId}/timeline`);
    return handleResponse(res);
  },

  async listBranches(worldId) {
    const res = await fetch(`${BASE_URL}/api/worlds/${worldId}/branches`);
    return handleResponse(res);
  },

  async compareBranches(branchAId, branchBId) {
    const res = await fetch(`${BASE_URL}/api/branches/compare?branch_a_id=${encodeURIComponent(branchAId)}&branch_b_id=${encodeURIComponent(branchBId)}`);
    return handleResponse(res);
  },

  async listInterventions(worldId) {
    const res = await fetch(`${BASE_URL}/api/worlds/${worldId}/interventions`);
    return handleResponse(res);
  },

  async evaluateInterventions(worldId, payload) {
    const res = await fetch(`${BASE_URL}/api/worlds/${worldId}/interventions/evaluate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse(res);
  },

  async sendCopilotTurn(worldId, query, branchId, sessionId) {
    const res = await fetch(`${BASE_URL}/api/copilot/turn`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        world_id: worldId,
        query,
        branch_id: branchId,
        session_id: sessionId
      })
    });
    return handleResponse(res);
  },

  async searchKnowledge(worldId, q) {
    const res = await fetch(`${BASE_URL}/api/worlds/${worldId}/knowledge/search?q=${encodeURIComponent(q)}`);
    return handleResponse(res);
  },

  async listReports(worldId) {
    const res = await fetch(`${BASE_URL}/api/worlds/${worldId}/reports`);
    return handleResponse(res);
  },

  async getReport(reportId) {
    const res = await fetch(`${BASE_URL}/api/reports/${reportId}`);
    return handleResponse(res);
  },

  async generateReport(worldId, branchId, title) {
    const res = await fetch(`${BASE_URL}/api/reports/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ world_id: worldId, branch_id: branchId, title })
    });
    return handleResponse(res);
  }
};
