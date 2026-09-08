"""Domain models for RAG Knowledge Documents and Search."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class KnowledgeDocumentCreate(BaseModel):
    id: Optional[str] = None
    world_id: str
    title: str
    category: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class KnowledgeDocument(BaseModel):
    id: str
    world_id: str
    title: str
    category: str
    content: str
    metadata: Dict[str, Any]
    created_at: Optional[str] = None


class KnowledgeSearchResult(BaseModel):
    document_id: str
    title: str
    category: str
    snippet: str
    score: float
    metadata: Dict[str, Any]
