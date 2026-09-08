"""World Management API Routes."""

import json
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from backend.app.database import db
from backend.app.services.generator_service import WorldGenerator
from backend.app.services.world_creator_agent import WorldCreatorAgent
from backend.app.auth import verify_api_access

router = APIRouter(prefix="/api/worlds", tags=["worlds"])
generator = WorldGenerator(db)
creator = WorldCreatorAgent()


class ProposeWorldRequest(BaseModel):
    description: str


class ConfirmWorldRequest(BaseModel):
    template: Dict[str, Any]
    custom_name: Optional[str] = None
    custom_world_id: Optional[str] = None


@router.get("")
def list_worlds(_: bool = Depends(verify_api_access)):
    rows = db.fetchall("SELECT id, name, world_type, description, current_timestamp, created_at FROM worlds ORDER BY created_at ASC;")
    return rows


@router.get("/{world_id}")
def get_world(world_id: str, _: bool = Depends(verify_api_access)):
    row = db.fetchone("SELECT * FROM worlds WHERE id = ?;", (world_id,))
    if not row:
        raise HTTPException(status_code=404, detail=f"World '{world_id}' not found.")
    schema_def = json.loads(row["schema_definition"]) if isinstance(row["schema_definition"], str) else row["schema_definition"]
    return {
        **row,
        "schema_definition": schema_def
    }


@router.get("/{world_id}/entities")
def get_world_entities(world_id: str, entity_type: Optional[str] = None, _: bool = Depends(verify_api_access)):
    if entity_type:
        rows = db.fetchall("SELECT * FROM entities WHERE world_id = ? AND entity_type = ?;", (world_id, entity_type))
    else:
        rows = db.fetchall("SELECT * FROM entities WHERE world_id = ?;", (world_id,))

    entities = []
    for r in rows:
        entities.append({
            "id": r["id"],
            "world_id": r["world_id"],
            "entity_type": r["entity_type"],
            "name": r["name"],
            "position": json.loads(r["position"]) if isinstance(r["position"], str) else r["position"],
            "state": json.loads(r["state"]) if isinstance(r["state"], str) else r["state"],
            "attributes": json.loads(r["attributes"]) if isinstance(r["attributes"], str) else r["attributes"],
            "relationships": json.loads(r["relationships"]) if isinstance(r["relationships"], str) else r["relationships"]
        })
    return entities


@router.get("/{world_id}/relationships")
def get_world_relationships(world_id: str, _: bool = Depends(verify_api_access)):
    rows = db.fetchall("SELECT * FROM relationships WHERE world_id = ?;", (world_id,))
    rels = []
    for r in rows:
        rels.append({
            **r,
            "attributes": json.loads(r["attributes"]) if isinstance(r["attributes"], str) else r["attributes"]
        })
    return rels


@router.post("/propose")
def propose_world(req: ProposeWorldRequest, _: bool = Depends(verify_api_access)):
    """GenAI proposes structured world template without persisting (human review step)."""
    proposal = creator.propose_world_template(req.description)
    return proposal


@router.post("/confirm")
def confirm_and_instantiate_world(req: ConfirmWorldRequest, _: bool = Depends(verify_api_access)):
    """Instantiate a confirmed world template."""
    try:
        res = generator.instantiate_world(
            template=req.template,
            custom_world_id=req.custom_world_id,
            custom_name=req.custom_name
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
