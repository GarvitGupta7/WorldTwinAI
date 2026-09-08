"""Domain models for Worlds and EntityType definitions."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MetricDefinition(BaseModel):
    name: str
    display_name: str
    description: str
    unit: str
    healthy_min: float
    healthy_max: float
    computation_type: str  # e.g., 'avg_attribute', 'ratio', 'count_state', 'weighted_sum'
    target_entity_type: Optional[str] = None
    target_field: Optional[str] = None


class ScenarioVocabularyItem(BaseModel):
    action: str
    display_name: str
    description: str
    target_entity_types: List[str]
    allowed_parameters: List[Dict[str, Any]]
    example_phrases: List[str]


class WorldSchemaDefinition(BaseModel):
    world_type: str
    version: str = "1.0.0"
    declared_entity_types: List[str]
    declared_relationship_types: List[str]
    metrics: List[MetricDefinition]
    scenario_vocabulary: List[ScenarioVocabularyItem]


class WorldCreate(BaseModel):
    id: Optional[str] = None
    name: str
    world_type: str
    description: Optional[str] = ""
    schema_definition: WorldSchemaDefinition


class World(BaseModel):
    id: str
    name: str
    world_type: str
    description: Optional[str] = ""
    schema_definition: Dict[str, Any]
    current_timestamp: str
    created_at: Optional[str] = None


class EntityTypeCreate(BaseModel):
    world_id: str
    name: str
    display_name: str
    schema_definition: Dict[str, Any]
    rules_definition: Dict[str, Any]


class EntityType(BaseModel):
    world_id: str
    name: str
    display_name: str
    schema_definition: Dict[str, Any]
    rules_definition: Dict[str, Any]
    created_at: Optional[str] = None
