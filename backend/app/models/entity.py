"""Domain models for Entities and Relationships."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class GeoCoordinate(BaseModel):
    lat: float
    lng: float


class GraphTopology(BaseModel):
    node_id: str
    level: Optional[int] = 1
    zone: Optional[str] = None


class Position(BaseModel):
    x: float = 0.0
    y: float = 0.0
    geo: Optional[GeoCoordinate] = None
    topology: Optional[GraphTopology] = None


class EntityCreate(BaseModel):
    id: Optional[str] = None
    world_id: str
    entity_type: str
    name: str
    position: Position
    state: Dict[str, Any] = Field(default_factory=dict)
    attributes: Dict[str, Any] = Field(default_factory=dict)
    relationships: List[str] = Field(default_factory=list)


class Entity(BaseModel):
    id: str
    world_id: str
    entity_type: str
    name: str
    position: Dict[str, Any]
    state: Dict[str, Any]
    attributes: Dict[str, Any]
    relationships: List[str]
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class RelationshipCreate(BaseModel):
    id: Optional[str] = None
    world_id: str
    source_entity_id: str
    target_entity_id: str
    relationship_type: str
    attributes: Dict[str, Any] = Field(default_factory=dict)


class Relationship(BaseModel):
    id: str
    world_id: str
    source_entity_id: str
    target_entity_id: str
    relationship_type: str
    attributes: Dict[str, Any]
    created_at: Optional[str] = None
