"""Domain models for Research Reports."""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class ReportCreate(BaseModel):
    id: Optional[str] = None
    world_id: str
    branch_id: str
    title: str
    format: str = "markdown"
    content: str
    summary: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Report(BaseModel):
    id: str
    world_id: str
    branch_id: str
    title: str
    format: str
    content: str
    summary: str
    metadata: Dict[str, Any]
    created_at: Optional[str] = None
