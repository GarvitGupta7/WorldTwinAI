"""
Branch Management Service for WorldTwin AI.
Creates, chains, runs, compares, and retrieves simulation branches.
"""

import uuid
import json
import logging
from typing import Any, Dict, List, Optional
from backend.app.database import Database, db
from backend.app.services.simulation_engine import SimulationEngine

logger = logging.getLogger("worldtwin.branches")


class BranchService:
    def __init__(self, database: Optional[Database] = None):
        self.db = database or db
        self.engine = SimulationEngine(self.db)

    def create_branch(
        self,
        world_id: str,
        name: str,
        branch_type: str = "what_if",
        parent_branch_id: Optional[str] = None,
        scenario_id: Optional[str] = None,
        seed: int = 42,
        duration: int = 60
    ) -> Dict[str, Any]:
        branch_id = f"branch_{uuid.uuid4().hex[:8]}"
        self.db.execute(
            """
            INSERT INTO simulation_branches (id, world_id, parent_branch_id, scenario_id, branch_type, name, seed, duration, status, initial_state_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', 'pending');
            """,
            (branch_id, world_id, parent_branch_id, scenario_id, branch_type, name, seed, duration)
        )
        return {
            "id": branch_id,
            "world_id": world_id,
            "parent_branch_id": parent_branch_id,
            "scenario_id": scenario_id,
            "branch_type": branch_type,
            "name": name,
            "seed": seed,
            "duration": duration,
            "status": "pending"
        }

    def run_branch(self, branch_id: str) -> Dict[str, Any]:
        branch_row = self.db.fetchone("SELECT * FROM simulation_branches WHERE id = ?;", (branch_id,))
        if not branch_row:
            raise ValueError(f"Branch '{branch_id}' not found.")

        result = self.engine.run_branch_simulation(
            branch_id=branch_id,
            world_id=branch_row["world_id"],
            seed=branch_row["seed"],
            duration=branch_row["duration"],
            scenario_id=branch_row["scenario_id"],
            parent_branch_id=branch_row["parent_branch_id"]
        )
        return result

    def get_branch_details(self, branch_id: str) -> Optional[Dict[str, Any]]:
        row = self.db.fetchone("SELECT * FROM simulation_branches WHERE id = ?;", (branch_id,))
        if not row:
            return None

        # Fetch latest metrics
        latest_metric_row = self.db.fetchone(
            "SELECT metrics, step, timestamp FROM metric_snapshots WHERE branch_id = ? ORDER BY step DESC LIMIT 1;",
            (branch_id,)
        )
        latest_metrics = json.loads(latest_metric_row["metrics"]) if latest_metric_row else {}

        # Fetch anomalies
        anomalies = self.db.fetchall(
            "SELECT id, step, metric_name, severity, threshold, actual_value, description FROM anomalies WHERE branch_id = ? ORDER BY step ASC;",
            (branch_id,)
        )

        # Fetch predictions
        predictions = self.db.fetchall(
            "SELECT target_metric, horizon_steps, predicted_values, confidence, method, limitations FROM predictions WHERE branch_id = ?;",
            (branch_id,)
        )
        parsed_predictions = []
        for p in predictions:
            parsed_predictions.append({
                "target_metric": p["target_metric"],
                "horizon_steps": p["horizon_steps"],
                "predicted_values": json.loads(p["predicted_values"]),
                "confidence": p["confidence"],
                "method": p["method"],
                "limitations": p["limitations"]
            })

        # Fetch events
        events = self.db.fetchall(
            "SELECT step, timestamp, event_type, description FROM simulation_events WHERE branch_id = ? ORDER BY step ASC;",
            (branch_id,)
        )

        return {
            **row,
            "latest_metrics": latest_metrics,
            "anomalies": anomalies,
            "predictions": parsed_predictions,
            "events": events
        }

    def get_branch_timeline(self, branch_id: str) -> List[Dict[str, Any]]:
        rows = self.db.fetchall(
            """
            SELECT s.step, s.timestamp, s.state_snapshot, m.metrics
            FROM simulation_states s
            LEFT JOIN metric_snapshots m ON s.branch_id = m.branch_id AND s.step = m.step
            WHERE s.branch_id = ?
            ORDER BY s.step ASC;
            """,
            (branch_id,)
        )
        timeline = []
        for r in rows:
            snapshot_data = json.loads(r["state_snapshot"]) if r["state_snapshot"] else {}
            metrics_data = json.loads(r["metrics"]) if r["metrics"] else {}
            timeline.append({
                "step": r["step"],
                "timestamp": r["timestamp"],
                "entities": snapshot_data.get("entities", []),
                "metrics": metrics_data
            })
        return timeline

    def list_branches_for_world(self, world_id: str) -> List[Dict[str, Any]]:
        rows = self.db.fetchall(
            """
            SELECT b.*, s.action as scenario_action, s.original_text as scenario_text
            FROM simulation_branches b
            LEFT JOIN scenarios s ON b.scenario_id = s.id
            WHERE b.world_id = ?
            ORDER BY b.created_at DESC;
            """,
            (world_id,)
        )
        return rows

    def compare_branches(self, branch_a_id: str, branch_b_id: str) -> Dict[str, Any]:
        details_a = self.get_branch_details(branch_a_id)
        details_b = self.get_branch_details(branch_b_id)
        if not details_a or not details_b:
            raise ValueError("One or both branches could not be found.")

        metrics_a = details_a.get("latest_metrics", {})
        metrics_b = details_b.get("latest_metrics", {})

        diffs = {}
        all_metric_keys = set(metrics_a.keys()).union(set(metrics_b.keys()))
        for k in all_metric_keys:
            val_a = metrics_a.get(k, 0.0)
            val_b = metrics_b.get(k, 0.0)
            diff = round(val_b - val_a, 4)
            pct_change = round((diff / max(abs(val_a), 1e-4)) * 100.0, 2)
            diffs[k] = {
                "branch_a": val_a,
                "branch_b": val_b,
                "absolute_diff": diff,
                "percent_change": pct_change
            }

        return {
            "branch_a": {"id": branch_a_id, "name": details_a["name"], "type": details_a["branch_type"]},
            "branch_b": {"id": branch_b_id, "name": details_b["name"], "type": details_b["branch_type"]},
            "metric_comparisons": diffs,
            "anomalies_a_count": len(details_a.get("anomalies", [])),
            "anomalies_b_count": len(details_b.get("anomalies", []))
        }
