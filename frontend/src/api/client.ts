import {
  World, Entity, Relationship, ScenarioParsedOutput, SimulationBranch,
  TimelineStep, Intervention, InterventionRun, MultiObjectiveWeights,
  CopilotTurnResponse, ResearchReport
} from '../types';

const BASE_URL = '';

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const errorBody = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errorBody.detail || `Request failed with status ${res.status}`);
  }
  return res.json();
}

export const apiClient = {
  // Health
  async getHealth(): Promise<any> {
    const res = await fetch(`${BASE_URL}/health`);
    return handleResponse(res);
  },

  // Worlds
  async listWorlds(): Promise<World[]> {
    const res = await fetch(`${BASE_URL}/api/worlds`);
    return handleResponse(res);
  },

  async getWorld(worldId: string): Promise<World> {
    const res = await fetch(`${BASE_URL}/api/worlds/${worldId}`);
    return handleResponse(res);
  },

  async proposeWorld(description: string): Promise<any> {
    const res = await fetch(`${BASE_URL}/api/worlds/propose`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ description })
    });
    return handleResponse(res);
  },

  async confirmWorld(template: any, customName?: string, customWorldId?: string): Promise<any> {
    const res = await fetch(`${BASE_URL}/api/worlds/confirm`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ template, custom_name: customName, custom_world_id: customWorldId })
    });
    return handleResponse(res);
  },

  async getEntities(worldId: string, entityType?: string): Promise<Entity[]> {
    const url = entityType
      ? `${BASE_URL}/api/worlds/${worldId}/entities?entity_type=${encodeURIComponent(entityType)}`
      : `${BASE_URL}/api/worlds/${worldId}/entities`;
    const res = await fetch(url);
    return handleResponse(res);
  },

  async getRelationships(worldId: string): Promise<Relationship[]> {
    const res = await fetch(`${BASE_URL}/api/worlds/${worldId}/relationships`);
    return handleResponse(res);
  },

  // Scenarios & Branches
  async parseScenario(worldId: string, text: string): Promise<ScenarioParsedOutput> {
    const res = await fetch(`${BASE_URL}/api/worlds/${worldId}/scenarios/parse`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text })
    });
    return handleResponse(res);
  },

  async createBranch(worldId: string, params: {
    name: string;
    branch_type?: string;
    parent_branch_id?: string;
    scenario_id?: string;
    seed?: number;
    duration?: number;
  }): Promise<SimulationBranch> {
    const res = await fetch(`${BASE_URL}/api/worlds/${worldId}/branches`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params)
    });
    return handleResponse(res);
  },

  async simulateBranch(branchId: string): Promise<any> {
    const res = await fetch(`${BASE_URL}/api/branches/${branchId}/simulate`, {
      method: 'POST'
    });
    return handleResponse(res);
  },

  async runBatchExperiments(payload: {
    world_id: string;
    parent_branch_id?: string;
    scenarios: string[];
    seeds?: number[];
    duration?: number;
  }): Promise<any> {
    const res = await fetch(`${BASE_URL}/api/branches/batch_run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse(res);
  },

  async getBranch(branchId: string): Promise<SimulationBranch> {
    const res = await fetch(`${BASE_URL}/api/branches/${branchId}`);
    return handleResponse(res);
  },

  async getBranchTimeline(branchId: string): Promise<TimelineStep[]> {
    const res = await fetch(`${BASE_URL}/api/branches/${branchId}/timeline`);
    return handleResponse(res);
  },

  async listBranches(worldId: string): Promise<SimulationBranch[]> {
    const res = await fetch(`${BASE_URL}/api/worlds/${worldId}/branches`);
    return handleResponse(res);
  },

  async compareBranches(branchAId: string, branchBId: string): Promise<any> {
    const res = await fetch(`${BASE_URL}/api/branches/compare?branch_a_id=${encodeURIComponent(branchAId)}&branch_b_id=${encodeURIComponent(branchBId)}`);
    return handleResponse(res);
  },

  // Interventions
  async listInterventions(worldId: string): Promise<Intervention[]> {
    const res = await fetch(`${BASE_URL}/api/worlds/${worldId}/interventions`);
    return handleResponse(res);
  },

  async evaluateInterventions(worldId: string, payload: {
    baseline_branch_id: string;
    candidate_intervention_ids?: string[];
    weights?: MultiObjectiveWeights;
  }): Promise<{ world_id: string; baseline_branch_id: string; evaluated_count: number; rankings: InterventionRun[] }> {
    const res = await fetch(`${BASE_URL}/api/worlds/${worldId}/interventions/evaluate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse(res);
  },

  // Copilot Command Layer
  async sendCopilotTurn(worldId: string, query: string, branchId?: string, sessionId?: string): Promise<CopilotTurnResponse> {
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

  // Knowledge & Reports
  async searchKnowledge(worldId: string, q: string): Promise<any[]> {
    const res = await fetch(`${BASE_URL}/api/worlds/${worldId}/knowledge/search?q=${encodeURIComponent(q)}`);
    return handleResponse(res);
  },

  async listReports(worldId: string): Promise<ResearchReport[]> {
    const res = await fetch(`${BASE_URL}/api/worlds/${worldId}/reports`);
    return handleResponse(res);
  },

  async getReport(reportId: string): Promise<ResearchReport> {
    const res = await fetch(`${BASE_URL}/api/reports/${reportId}`);
    return handleResponse(res);
  },

  async generateReport(worldId: string, branchId: string, title?: string): Promise<ResearchReport> {
    const res = await fetch(`${BASE_URL}/api/reports/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ world_id: worldId, branch_id: branchId, title })
    });
    return handleResponse(res);
  }
};
