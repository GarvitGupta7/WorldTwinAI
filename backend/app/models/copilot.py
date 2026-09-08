"""Domain models for GenAI Command Layer, Tool Schemas, Verification, and Evidence."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ToolCall(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]


class StructuredPlan(BaseModel):
    intent: str
    reasoning: str
    tool_calls: List[ToolCall] = Field(default_factory=list)


class PlanValidationResult(BaseModel):
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    sanitized_plan: Optional[StructuredPlan] = None


class ToolExecutionResult(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]
    success: bool
    data: Any
    error: Optional[str] = None


class VerificationCheck(BaseModel):
    target_resource_type: str  # e.g., 'branch', 'metrics', 'intervention_run', 'world'
    resource_id: str
    expected_property: str
    observed_value: Any
    verified: bool
    details: str


class EvidenceItem(BaseModel):
    source: str  # 'database_read', 'knowledge_base', 'simulation_engine'
    resource_id: Optional[str] = None
    metric_or_field: Optional[str] = None
    verified_data: Any
    timestamp: str


class CopilotTurnRequest(BaseModel):
    world_id: str
    branch_id: Optional[str] = None
    query: str
    session_id: Optional[str] = None


class CopilotTurnResponse(BaseModel):
    response_text: str
    structured_plan: StructuredPlan
    executed_tools: List[ToolExecutionResult]
    verification_checks: List[VerificationCheck]
    evidence: List[EvidenceItem]
    citations: List[str] = Field(default_factory=list)
    confidence: float
    status: str  # 'verified', 'partially_verified', 'unverified_failure', 'refusal'
    session_id: str
