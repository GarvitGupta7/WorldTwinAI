"""Domain models for Interventions and Counterfactual Evaluation."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MultiObjectiveWeights(BaseModel):
    benefit: float = 0.4
    safety: float = 0.3
    cost: float = 0.15
    complexity: float = 0.15


class InterventionCreate(BaseModel):
    id: Optional[str] = None
    world_id: str
    name: str
    description: str
    scenario_action: str
    parameters: List[Dict[str, Any]] = Field(default_factory=list)
    cost: float = 1.0        # 1-10
    complexity: float = 1.0  # 1-10
    expected_benefit: float = 1.0 # 1-10


class Intervention(BaseModel):
    id: str
    world_id: str
    name: str
    description: str
    scenario_action: str
    parameters: List[Dict[str, Any]]
    cost: float
    complexity: float
    expected_benefit: float
    created_at: Optional[str] = None


class InterventionRun(BaseModel):
    id: str
    world_id: str
    intervention_id: str
    baseline_branch_id: str
    counterfactual_branch_id: str
    outcome_metrics: Dict[str, Any]
    score: float
    weights_used: Dict[str, float]
    ranking: Optional[int] = None
    status: str = "completed"
    created_at: Optional[str] = None
