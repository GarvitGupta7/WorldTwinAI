"""
RAG / Knowledge Grounding Service for WorldTwin AI.
Performs scoped search over world-specific operational documentation,
returning scored passages and citations for Copilot grounding.
"""

import math
import logging
from typing import Any, Dict, List, Optional
from backend.app.database import Database, db
from backend.app.models.knowledge import KnowledgeSearchResult

logger = logging.getLogger("worldtwin.knowledge")


class KnowledgeService:
    def __init__(self, database: Optional[Database] = None):
        self.db = database or db

    def search(self, world_id: str, query: str, top_k: int = 3) -> List[KnowledgeSearchResult]:
        rows = self.db.fetchall("SELECT id, title, category, content, metadata FROM knowledge_documents WHERE world_id = ?;", (world_id,))
        if not rows:
            return []

        q_terms = set(re_term for re_term in query.lower().split() if len(re_term) > 2)
        scored_docs = []

        for r in rows:
            text = f"{r['title']} {r['category']} {r['content']}".lower()
            tokens = text.split()
            score = 0.0
            for term in q_terms:
                term_count = tokens.count(term)
                if term_count > 0:
                    tf = term_count / max(len(tokens), 1)
                    score += tf * 5.0 + (1.0 if term in r["title"].lower() else 0.0)

            if score > 0.0:
                # Generate snippet
                idx = -1
                for term in q_terms:
                    idx = r["content"].lower().find(term)
                    if idx != -1:
                        break
                start = max(0, idx - 40) if idx != -1 else 0
                end = min(len(r["content"]), start + 240)
                snippet = r["content"][start:end] + ("..." if end < len(r["content"]) else "")

                scored_docs.append(KnowledgeSearchResult(
                    document_id=r["id"],
                    title=r["title"],
                    category=r["category"],
                    snippet=snippet,
                    score=round(score, 3),
                    metadata={"source": "world_knowledge_base"}
                ))

        scored_docs.sort(key=lambda x: x.score, reverse=True)
        return scored_docs[:top_k]
