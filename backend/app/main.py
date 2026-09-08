"""
WorldTwin AI — Main Application Server
Full-stack research-grade Generative AI Digital Twin platform.
"""

import os
import json
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from backend.app.config import STATIC_DIR, BASE_DIR
from backend.app.database import db
from backend.app.migrations.runner import MigrationRunner
from backend.app.services.generator_service import WorldGenerator
from backend.app.api.routes_world import router as world_router
from backend.app.api.routes_simulation import router as sim_router
from backend.app.api.routes_intervention import router as intv_router
from backend.app.api.routes_copilot import router as copilot_router
from backend.app.api.routes_knowledge import router as know_router
from backend.app.api.routes_reports import router as rep_router
from backend.app.api.routes_health import router as health_router

# Structured Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
)
logger = logging.getLogger("worldtwin.main")

app = FastAPI(
    title="WorldTwin AI",
    description="Research-Grade Generative AI Digital Twin Platform with Verified Command Layer",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(health_router)
app.include_router(world_router)
app.include_router(sim_router)
app.include_router(intv_router)
app.include_router(copilot_router)
app.include_router(know_router)
app.include_router(rep_router)


@app.on_event("startup")
def startup_event():
    """Run database migrations and ensure default seed worlds are initialized."""
    logger.info("Initializing database migrations...")
    runner = MigrationRunner(db)
    runner.run_migrations()

    # Check if worlds exist
    worlds = db.fetchall("SELECT id FROM worlds;")
    if not worlds:
        logger.info("No worlds found. Instantiating default Campus World Template...")
        template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates", "campus_template.json")
        if os.path.exists(template_path):
            with open(template_path) as f:
                template = json.load(f)
            generator = WorldGenerator(db)
            res = generator.instantiate_world(template, custom_world_id="world_campus_01")
            logger.info(f"Initialized default world '{res['world_id']}'.")


# Mount static assets if directory exists
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
# Also mount public if different
public_fallback = os.path.join(BASE_DIR, "frontend", "public")
if os.path.exists(public_fallback) and public_fallback != STATIC_DIR:
    app.mount("/public", StaticFiles(directory=public_fallback), name="public")


@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    """Serve frontend single-page application and route index.html."""
    if full_path.startswith("api/") or full_path.startswith("health"):
        return JSONResponse(status_code=404, content={"detail": "Not Found"})

    candidates = [
        os.path.join(STATIC_DIR, "index.html"),
        os.path.join(BASE_DIR, "frontend", "dist", "index.html"),
        os.path.join(BASE_DIR, "frontend", "public", "index.html"),
        os.path.join(BASE_DIR, "frontend", "index.html"),
    ]
    for cand in candidates:
        if os.path.exists(cand):
            return FileResponse(cand)

    return JSONResponse(
        status_code=200,
        content={"message": "WorldTwin AI API operational. Frontend loading."}
    )
