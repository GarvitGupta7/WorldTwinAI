"""Domain models for Scenarios and Scenario Parsing."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ScenarioParameter(BaseModel):
    name: str
    value: Any
    unit: Optional[str] = None


class ScenarioParseRequest(BaseModel):
    world_id: str
    text: str


class ScenarioParsedOutput(BaseModel):
    action: str
    parameters: List[ScenarioParameter] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    ambiguities: List[str] = Field(default_factory=list)
    confidence: float
    reasoning: str
    valid: bool = True
    clarification_question: Optional[str] = None


class ScenarioCreate(BaseModel):
    id: Optional[str] = None
    world_id: str
    original_text: str
    action: str
    parameters: List[Dict[str, Any]] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    ambiguities: List[str] = Field(default_factory=list)
    valid: bool = True
    parser_metadata: Dict[str, Any] = Field(default_factory=dict)


class Scenario(BaseModel):
    id: str
    world_id: str
    original_text: str
    action: str
    parameters: List[Dict[str, Any]]
    assumptions: List[str]
    ambiguities: List[str]
    valid: bool
    parser_metadata: Dict[str, Any]
    created_at: Optional[str] = None
