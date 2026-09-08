"""Research Reports API Routes."""

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from backend.app.database import db
from backend.app.services.report_service import ReportService
from backend.app.auth import verify_api_access

router = APIRouter(tags=["reports"])
report_service = ReportService(db)


class GenerateReportRequest(BaseModel):
    world_id: str
    branch_id: str
    title: Optional[str] = None


@router.get("/api/worlds/{world_id}/reports")
def list_reports(world_id: str, _: bool = Depends(verify_api_access)):
    return report_service.list_reports_for_world(world_id)


@router.get("/api/reports/{report_id}")
def get_report(report_id: str, _: bool = Depends(verify_api_access)):
    rep = report_service.get_report(report_id)
    if not rep:
        raise HTTPException(status_code=404, detail="Report not found.")
    return rep


@router.post("/api/reports/generate")
def generate_report(req: GenerateReportRequest, _: bool = Depends(verify_api_access)):
    try:
        rep = report_service.generate_report(req.world_id, req.branch_id, title=req.title)
        return rep
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
