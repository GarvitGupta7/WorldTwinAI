"""RAG Knowledge Base API Routes."""

from fastapi import APIRouter, HTTPException, Depends
from backend.app.database import db
from backend.app.services.knowledge_service import KnowledgeService
from backend.app.auth import verify_api_access

router = APIRouter(prefix="/api/worlds/{world_id}/knowledge", tags=["knowledge"])
knowledge_service = KnowledgeService(db)


@router.get("/search")
def search_knowledge(world_id: str, q: str, top_k: int = 5, _: bool = Depends(verify_api_access)):
    results = knowledge_service.search(world_id, q, top_k=top_k)
    return results


@router.get("/documents")
def list_knowledge_documents(world_id: str, _: bool = Depends(verify_api_access)):
    rows = db.fetchall("SELECT id, title, category, content FROM knowledge_documents WHERE world_id = ?;", (world_id,))
    return rows
