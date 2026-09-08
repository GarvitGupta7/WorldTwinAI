"""
Incremental Database Migration Runner for WorldTwin AI.
Tracks applied versions in the `schema_migrations` table and applies
pending migrations in strict sequential order.
"""

import os
import importlib.util
import logging
from typing import List
from backend.app.database import Database

logger = logging.getLogger("worldtwin.migrations")

MIGRATIONS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "versions")


class MigrationRunner:
    def __init__(self, db: Database):
        self.db = db
        self._ensure_migration_table()

    def _ensure_migration_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        self.db.execute(query)

    def get_applied_versions(self) -> List[int]:
        rows = self.db.fetchall("SELECT version FROM schema_migrations ORDER BY version ASC;")
        return [r["version"] for r in rows]

    def run_migrations(self):
        applied = set(self.get_applied_versions())
        files = sorted(os.listdir(MIGRATIONS_DIR))
        py_files = [f for f in files if f.endswith(".py") and not f.startswith("__")]

        for f in py_files:
            parts = f.split("_", 1)
            try:
                version = int(parts[0])
            except ValueError:
                continue

            if version not in applied:
                logger.info(f"Applying migration {version}: {f}")
                file_path = os.path.join(MIGRATIONS_DIR, f)
                spec = importlib.util.spec_from_file_location(f"migration_{version}", file_path)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    if hasattr(module, "upgrade"):
                        module.upgrade(self.db)
                        self.db.execute(
                            "INSERT INTO schema_migrations (version, name) VALUES (?, ?);",
                            (version, f),
                        )
                        logger.info(f"Successfully applied migration {version}: {f}")
                    else:
                        raise RuntimeError(f"Migration {f} missing upgrade() function")

    def rollback_latest(self):
        rows = self.db.fetchall("SELECT version, name FROM schema_migrations ORDER BY version DESC LIMIT 1;")
        if not rows:
            logger.info("No migrations to rollback.")
            return
        version = rows[0]["version"]
        name = rows[0]["name"]
        file_path = os.path.join(MIGRATIONS_DIR, name)
        spec = importlib.util.spec_from_file_location(f"migration_{version}", file_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if hasattr(module, "downgrade"):
                module.downgrade(self.db)
                self.db.execute("DELETE FROM schema_migrations WHERE version = ?;", (version,))
                logger.info(f"Rolled back migration {version}: {name}")
