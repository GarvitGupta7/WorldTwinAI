"""Application configuration settings with dynamic cross-platform path resolution."""

import os

# Dynamically resolve project root directory: .../worldtwin-ai/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

WORLDTWIN_API_KEY = os.environ.get("WORLDTWIN_API_KEY", "wt-adm-secret-2026")
DB_PATH = os.environ.get("WORLDTWIN_DB_PATH", os.path.join(BASE_DIR, "worldtwin.db"))
PORT = int(os.environ.get("PORT", 8000))
HOST = os.environ.get("HOST", "0.0.0.0")

# Support both built production frontend (dist) and developer static/public directory
_dist_dir = os.path.join(BASE_DIR, "frontend", "dist")
_public_dir = os.path.join(BASE_DIR, "frontend", "public")

if os.path.exists(_dist_dir):
    STATIC_DIR = os.environ.get("STATIC_DIR", _dist_dir)
else:
    STATIC_DIR = os.environ.get("STATIC_DIR", _public_dir)
