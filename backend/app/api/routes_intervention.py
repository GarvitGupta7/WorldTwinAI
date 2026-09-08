"""Intervention and Counterfactual Evaluation API Routes."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from backend.app.database import db
from backend.app.services.intervention_service import InterventionService
from backend.app.models.intervention import MultiObjectiveWeights
from backend.app.auth import verify_api_access

router = APIRouter(prefix="/api/worlds/{world_id}/interventions", tags=["interventions"])
intervention_service = InterventionService(db)


class EvaluateInterventionsRequest(BaseModel):
    baseline_branch_id: str
    candidate_intervention_ids: Optional[List[str]] = None
    weights: Optional[MultiObjectiveWeights] = None


@router.get("")
def list_interventions(world_id: str, _: bool = Depends(verify_api_access)):
    return intervention_service.get_candidate_interventions(world_id)


@router.post("/evaluate")
def evaluate_interventions(world_id: str, req: EvaluateInterventionsRequest, _: bool = Depends(verify_api_access)):
    try:
        runs = intervention_service.evaluate_interventions(
            world_id=world_id,
            baseline_branch_id=req.baseline_branch_id,
            candidate_intervention_ids=req.candidate_intervention_ids,
            weights=req.weights
        )
        return {
            "world_id": world_id,
            "baseline_branch_id": req.baseline_branch_id,
            "evaluated_count": len(runs),
            "rankings": runs
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
