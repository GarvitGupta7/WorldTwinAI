"""
Relational Database Abstraction Layer for WorldTwin AI.
Provides thread-safe connection management, transaction handling,
schema migration tracking, and dictionary row mapping.
"""

import os
import sqlite3
import json
import logging
from typing import Any, Dict, List, Optional, Tuple
from contextlib import contextmanager

from backend.app.config import DB_PATH

logger = logging.getLogger("worldtwin.database")


def dict_factory(cursor: sqlite3.Cursor, row: Tuple) -> Dict[str, Any]:
    """Convert sqlite3 row to dictionary."""
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


class Database:
    """Relational Database Manager with SQLite/Postgres-compatible abstraction."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or DB_PATH
        # Ensure parent directory exists for database file
        parent_dir = os.path.dirname(os.path.abspath(self.db_path))
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)

    @contextmanager
    def get_connection(self):
        """Context manager yielding a connection with foreign keys enabled."""
        conn = sqlite3.connect(self.db_path, timeout=30.0, check_same_thread=False)
        conn.row_factory = dict_factory
        conn.execute("PRAGMA foreign_keys = ON;")
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database transaction rolled back due to error: {e}")
            raise
        finally:
            conn.close()

    def execute(self, query: str, params: Optional[Tuple[Any, ...]] = None) -> Any:
        """Execute a single write statement and return the lastrowid or affected rows."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            return cursor.lastrowid

    def fetchone(self, query: str, params: Optional[Tuple[Any, ...]] = None) -> Optional[Dict[str, Any]]:
        """Fetch a single row as a dictionary."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            return cursor.fetchone()

    def fetchall(self, query: str, params: Optional[Tuple[Any, ...]] = None) -> List[Dict[str, Any]]:
        """Fetch all rows as dictionaries."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            return cursor.fetchall()

    def executescript(self, script: str):
        """Execute a raw SQL script."""
        with self.get_connection() as conn:
            conn.executescript(script)

    def ping(self) -> bool:
        """Health-check probe: verify database accessibility."""
        try:
            res = self.fetchone("SELECT 1 as alive;")
            return res is not None and res.get("alive") == 1
        except Exception as e:
            logger.error(f"Database ping failed: {e}")
            return False

    def dump_sql(self, target_filepath: str):
        """Dump entire SQL database to a target file for backup."""
        with self.get_connection() as conn:
            with open(target_filepath, "w") as f:
                for line in conn.iterdump():
                    f.write(f"{line}\n")


db = Database()
