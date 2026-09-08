export interface GeoCoordinate {
  lat: number;
  lng: number;
}

export interface GraphTopology {
  node_id: string;
  level?: number;
  zone?: string;
}

export interface Position {
  x: number;
  y: number;
  geo?: GeoCoordinate;
  topology?: GraphTopology;
}

export interface MetricDefinition {
  name: string;
  display_name: string;
  description: string;
  unit: string;
  healthy_min: number;
  healthy_max: number;
  computation_type: string;
  target_entity_type?: string;
  target_field?: string;
}

export interface ScenarioVocabularyItem {
  action: string;
  display_name: string;
  description: string;
  target_entity_types: string[];
  allowed_parameters: Array<{
    name: string;
    type: string;
    description: string;
    default?: any;
  }>;
  example_phrases: string[];
}

export interface WorldSchemaDefinition {
  world_type: string;
  version: string;
  declared_entity_types: string[];
  declared_relationship_types: Array<{
    relationship_type: string;
    source_entity_type: string;
    target_entity_type: string;
  }>;
  metrics: MetricDefinition[];
  scenario_vocabulary: ScenarioVocabularyItem[];
  spatial_bounds?: {
    min_x: number;
    max_x: number;
    min_y: number;
    max_y: number;
  };
}

export interface World {
  id: string;
  name: string;
  world_type: string;
  description: string;
  schema_definition: WorldSchemaDefinition;
  current_timestamp: string;
  created_at?: string;
}

export interface Entity {
  id: string;
  world_id: string;
  entity_type: string;
  name: string;
  position: Position;
  state: Record<string, any>;
  attributes: Record<string, any>;
  relationships: string[];
}

export interface Relationship {
  id: string;
  world_id: string;
  source_entity_id: string;
  target_entity_id: string;
  relationship_type: string;
  attributes: Record<string, any>;
}

export interface ScenarioParsedParameter {
  name: string;
  value: any;
  unit?: string;
}

export interface ScenarioParsedOutput {
  action: string;
  parameters: ScenarioParsedParameter[];
  assumptions: string[];
  ambiguities: string[];
  confidence: number;
  reasoning: string;
  valid: boolean;
  clarification_question?: string;
}

export interface SimulationBranch {
  id: string;
  world_id: string;
  parent_branch_id?: string;
  scenario_id?: string;
  branch_type: 'baseline' | 'what_if' | 'counterfactual' | 'intervention';
  name: string;
  seed: number;
  duration: number;
  status: 'pending' | 'running' | 'completed' | 'failed';
  initial_state_hash: string;
  created_at?: string;
  completed_at?: string;
  latest_metrics?: Record<string, number>;
  anomalies?: Anomaly[];
  predictions?: Prediction[];
  events?: SimulationEvent[];
}

export interface TimelineStep {
  step: number;
  timestamp: string;
  entities: Entity[];
  metrics: Record<string, number>;
}

export interface Anomaly {
  id: string;
  step: number;
  metric_name: string;
  severity: 'info' | 'warning' | 'critical';
  threshold: number;
  actual_value: number;
  description: string;
}

export interface Prediction {
  target_metric: string;
  horizon_steps: number;
  predicted_values: number[];
  confidence: number;
  method: string;
  limitations: string;
}

export interface SimulationEvent {
  step: number;
  timestamp: string;
  event_type: string;
  description: string;
}

export interface MultiObjectiveWeights {
  benefit: number;
  safety: number;
  cost: number;
  complexity: number;
}

export interface Intervention {
  id: string;
  world_id: string;
  name: string;
  description: string;
  scenario_action: string;
  parameters: Array<{ name: string; value: any; unit?: string }>;
  cost: number;
  complexity: number;
  expected_benefit: number;
}

export interface InterventionRun {
  run_id: string;
  intervention_id: string;
  intervention_name: string;
  counterfactual_branch_id: string;
  score: number;
  observed_benefit: number;
  cost: number;
  complexity: number;
  ranking?: number;
  outcome_metrics: {
    baseline_metrics: Record<string, number>;
    counterfactual_metrics: Record<string, number>;
    metric_deltas: Record<string, number>;
    observed_benefit: number;
    safety_gain: number;
    anomaly_delta: number;
  };
}

export interface ToolCall {
  tool_name: string;
  arguments: Record<string, any>;
}

export interface VerificationCheck {
  target_resource_type: string;
  resource_id: string;
  expected_property: string;
  observed_value: any;
  verified: boolean;
  details: string;
}

export interface EvidenceItem {
  source: string;
  resource_id?: string;
  metric_or_field?: string;
  verified_data: any;
  timestamp: string;
}

export interface CopilotTurnResponse {
  response_text: string;
  structured_plan: {
    intent: string;
    reasoning: string;
    tool_calls: ToolCall[];
  };
  executed_tools: Array<{
    tool_name: string;
    arguments: Record<string, any>;
    success: boolean;
    data: any;
    error?: string;
  }>;
  verification_checks: VerificationCheck[];
  evidence: EvidenceItem[];
  citations: string[];
  confidence: number;
  status: 'verified' | 'partially_verified' | 'unverified_failure' | 'refusal';
  session_id: string;
}

export interface ResearchReport {
  id: string;
  world_id: string;
  branch_id: string;
  title: string;
  format: string;
  content: string;
  summary: string;
  created_at?: string;
}
