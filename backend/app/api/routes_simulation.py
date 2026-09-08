"""Simulation, Scenarios, and Branching API Routes."""

import json
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from backend.app.database import db
from backend.app.services.branch_service import BranchService
from backend.app.services.scenario_parser import ScenarioParser
from backend.app.auth import verify_api_access

router = APIRouter(tags=["simulation"])
branch_service = BranchService(db)
scenario_parser = ScenarioParser(db)


class ParseScenarioRequest(BaseModel):
    text: str


class CreateBranchRequest(BaseModel):
    name: str
    branch_type: str = "what_if"
    parent_branch_id: Optional[str] = None
    scenario_id: Optional[str] = None
    seed: int = 42
    duration: int = 60


class BatchRunRequest(BaseModel):
    world_id: str
    parent_branch_id: Optional[str] = None
    scenarios: List[str]
    seeds: List[int] = [42, 101, 2024]
    duration: int = 30


@router.post("/api/worlds/{world_id}/scenarios/parse")
def parse_scenario(world_id: str, req: ParseScenarioRequest, _: bool = Depends(verify_api_access)):
    parsed = scenario_parser.parse_scenario(world_id, req.text)
    return parsed


@router.post("/api/worlds/{world_id}/branches")
def create_branch(world_id: str, req: CreateBranchRequest, _: bool = Depends(verify_api_access)):
    branch = branch_service.create_branch(
        world_id=world_id,
        name=req.name,
        branch_type=req.branch_type,
        parent_branch_id=req.parent_branch_id,
        scenario_id=req.scenario_id,
        seed=req.seed,
        duration=req.duration
    )
    return branch


@router.post("/api/branches/{branch_id}/simulate")
def run_branch_simulation(branch_id: str, _: bool = Depends(verify_api_access)):
    try:
        result = branch_service.run_branch(branch_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/api/branches/batch_run")
def run_batch_simulation(req: BatchRunRequest, _: bool = Depends(verify_api_access)):
    """Batch experiment runner across multiple scenarios and seeds."""
    results = []
    for scen_text in req.scenarios:
        # Parse scenario
        parsed = scenario_parser.parse_scenario(req.world_id, scen_text)
        scen_id = None
        if parsed.valid:
            scen_id = f"scen_batch_{len(results)}"
            db.execute(
                """
                INSERT INTO scenarios (id, world_id, original_text, action, parameters, assumptions, ambiguities, valid, parser_metadata)
                VALUES (?, ?, ?, ?, ?, '[]', '[]', 1, '{}');
                """,
                (scen_id, req.world_id, scen_text, parsed.action, json.dumps([p.dict() for p in parsed.parameters]))
            )

        for s in req.seeds:
            b_name = f"Batch: {parsed.action} (seed {s})"
            branch = branch_service.create_branch(
                world_id=req.world_id,
                name=b_name,
                branch_type="what_if",
                parent_branch_id=req.parent_branch_id,
                scenario_id=scen_id,
                seed=s,
                duration=req.duration
            )
            sim_res = branch_service.run_branch(branch["id"])
            results.append({
                "scenario": scen_text,
                "action": parsed.action,
                "seed": s,
                "branch_id": branch["id"],
                "final_metrics": sim_res["final_metrics"],
                "anomalies_count": sim_res["anomalies_count"]
            })

    return {
        "world_id": req.world_id,
        "batch_count": len(results),
        "experiments": results
    }


@router.get("/api/branches/{branch_id}")
def get_branch(branch_id: str, _: bool = Depends(verify_api_access)):
    details = branch_service.get_branch_details(branch_id)
    if not details:
        raise HTTPException(status_code=404, detail=f"Branch '{branch_id}' not found.")
    return details


@router.get("/api/branches/{branch_id}/timeline")
def get_branch_timeline(branch_id: str, _: bool = Depends(verify_api_access)):
    timeline = branch_service.get_branch_timeline(branch_id)
    return timeline


@router.get("/api/worlds/{world_id}/branches")
def list_branches(world_id: str, _: bool = Depends(verify_api_access)):
    branches = branch_service.list_branches_for_world(world_id)
    return branches


@router.get("/api/branches/compare")
def compare_branches(branch_a_id: str, branch_b_id: str, _: bool = Depends(verify_api_access)):
    try:
        diff = branch_service.compare_branches(branch_a_id, branch_b_id)
        return diff
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
