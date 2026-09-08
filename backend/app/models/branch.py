"""Domain models for Simulation Branches, Snapshots, Events, Anomalies, Predictions."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SimulationBranchCreate(BaseModel):
    id: Optional[str] = None
    world_id: str
    parent_branch_id: Optional[str] = None
    scenario_id: Optional[str] = None
    branch_type: str = "what_if"  # baseline, what_if, counterfactual, intervention
    name: str
    seed: int = 42
    duration: int = 60  # simulation steps


class SimulationBranch(BaseModel):
    id: str
    world_id: str
    parent_branch_id: Optional[str] = None
    scenario_id: Optional[str] = None
    branch_type: str
    name: str
    seed: int
    duration: int
    status: str
    initial_state_hash: str
    created_at: Optional[str] = None
    completed_at: Optional[str] = None


class SimulationStateSnapshot(BaseModel):
    id: str
    branch_id: str
    world_id: str
    step: int
    timestamp: str
    state_snapshot: Dict[str, Any]
    state_hash: str
    created_at: Optional[str] = None


class MetricSnapshot(BaseModel):
    id: str
    branch_id: str
    world_id: str
    step: int
    timestamp: str
    metrics: Dict[str, float]
    created_at: Optional[str] = None


class SimulationEvent(BaseModel):
    id: str
    branch_id: str
    world_id: str
    step: int
    timestamp: str
    event_type: str
    description: str
    details: Dict[str, Any]
    created_at: Optional[str] = None


class Anomaly(BaseModel):
    id: str
    branch_id: str
    world_id: str
    step: int
    metric_name: str
    severity: str  # info, warning, critical
    threshold: float
    actual_value: float
    description: str
    created_at: Optional[str] = None


class Prediction(BaseModel):
    id: str
    branch_id: str
    world_id: str
    target_metric: str
    horizon_steps: int
    predicted_values: List[float]
    confidence: float
    method: str
    limitations: str
    created_at: Optional[str] = None
