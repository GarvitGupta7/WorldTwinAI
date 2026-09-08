"""GenAI Copilot Command Layer API Routes."""

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from backend.app.database import db
from backend.app.services.copilot_planner import CopilotPlanner
from backend.app.models.copilot import CopilotTurnRequest
from backend.app.auth import verify_api_access

router = APIRouter(prefix="/api/copilot", tags=["copilot"])
copilot = CopilotPlanner(db)


@router.post("/turn")
def copilot_turn(req: CopilotTurnRequest, _: bool = Depends(verify_api_access)):
    try:
        response = copilot.execute_copilot_turn(
            world_id=req.world_id,
            query=req.query,
            branch_id=req.branch_id,
            session_id=req.session_id
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
