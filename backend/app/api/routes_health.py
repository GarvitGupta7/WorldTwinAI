"""Health and Observability Status API Routes."""

import os
import shutil
import time
from fastapi import APIRouter
from backend.app.database import db

router = APIRouter(tags=["health"])
START_TIME = time.time()


@router.get("/health")
def health_check():
    """
    Real health check probe:
    Pings the database with a live SQL query, inspects table counts,
    calculates storage usage, and computes system uptime.
    """
    db_alive = db.ping()

    stats = {}
    if db_alive:
        try:
            worlds_count = db.fetchone("SELECT COUNT(*) as c FROM worlds;")["c"]
            branches_count = db.fetchone("SELECT COUNT(*) as c FROM simulation_branches;")["c"]
            entities_count = db.fetchone("SELECT COUNT(*) as c FROM entities;")["c"]
            stats = {
                "active_worlds": worlds_count,
                "total_branches": branches_count,
                "total_entities": entities_count
            }
        except Exception as e:
            stats = {"error": str(e)}

    # Disk usage
    disk = shutil.disk_usage(os.path.abspath(os.path.dirname(__file__)))
    disk_free_mb = round(disk.free / (1024 * 1024), 1)

    status_str = "healthy" if db_alive else "degraded"

    return {
        "status": status_str,
        "database_connected": db_alive,
        "database_probe": "SELECT 1 as alive passed" if db_alive else "failed",
        "uptime_seconds": round(time.time() - START_TIME, 2),
        "disk_free_mb": disk_free_mb,
        "telemetry": stats
    }
