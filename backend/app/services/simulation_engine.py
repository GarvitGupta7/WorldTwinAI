"""
Deterministic, Seeded Simulation Engine for WorldTwin AI.
Simulates time-series state progression, records full timeline snapshots,
evaluates dynamic metrics via RuleRegistry, detects anomalies,
honors parent branch chaining from terminal snapshots,
and generates trend-extrapolation predictions with honest confidence bounds.
"""

import json
import uuid
import random
import hashlib
import datetime
import logging
from typing import Any, Dict, List, Optional
import numpy as np

from backend.app.database import Database, db
from backend.app.services.rule_registry import RuleRegistry

logger = logging.getLogger("worldtwin.simulation")


class SimulationEngine:
    """Executes stateful digital twin simulation branches."""

    def __init__(self, database: Optional[Database] = None):
        self.db = database or db

    def _compute_state_hash(self, entities: List[Dict[str, Any]]) -> str:
        canonical = []
        for e in sorted(entities, key=lambda x: x["id"]):
            canonical.append({
                "id": e["id"],
                "type": e.get("entity_type"),
                "state": e.get("state", {}),
                "pos": e.get("position", {})
            })
        data_str = json.dumps(canonical, sort_keys=True)
        return hashlib.sha256(data_str.encode("utf-8")).hexdigest()

    def load_initial_entities(self, world_id: str, parent_branch_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if parent_branch_id:
            terminal_state_row = self.db.fetchone(
                """
                SELECT state_snapshot FROM simulation_states
                WHERE branch_id = ?
                ORDER BY step DESC LIMIT 1;
                """,
                (parent_branch_id,)
            )
            if terminal_state_row and terminal_state_row.get("state_snapshot"):
                logger.info(f"Chaining branch from parent '{parent_branch_id}' terminal state snapshot.")
                snapshot_data = json.loads(terminal_state_row["state_snapshot"])
                return snapshot_data.get("entities", [])
            else:
                logger.warning(f"Parent branch '{parent_branch_id}' had no state snapshots. Falling back to base entities.")

        rows = self.db.fetchall(
            "SELECT id, world_id, entity_type, name, position, state, attributes, relationships FROM entities WHERE world_id = ?;",
            (world_id,)
        )
        entities = []
        for r in rows:
            entities.append({
                "id": r["id"],
                "world_id": r["world_id"],
                "entity_type": r["entity_type"],
                "name": r["name"],
                "position": json.loads(r["position"]) if isinstance(r["position"], str) else r["position"],
                "state": json.loads(r["state"]) if isinstance(r["state"], str) else r["state"],
                "attributes": json.loads(r["attributes"]) if isinstance(r["attributes"], str) else r["attributes"],
                "relationships": json.loads(r["relationships"]) if isinstance(r["relationships"], str) else r["relationships"]
            })
        return entities

    def run_branch_simulation(
        self,
        branch_id: str,
        world_id: str,
        seed: int = 42,
        duration: int = 60,
        scenario_id: Optional[str] = None,
        parent_branch_id: Optional[str] = None
    ) -> Dict[str, Any]:
        rng = random.Random(seed)

        world_row = self.db.fetchone("SELECT schema_definition, world_type FROM worlds WHERE id = ?;", (world_id,))
        if not world_row:
            raise ValueError(f"World '{world_id}' not found.")

        schema_def = json.loads(world_row["schema_definition"])
        world_type = world_row["world_type"]
        declared_metrics = schema_def.get("metrics", [])

        entities = self.load_initial_entities(world_id, parent_branch_id)
        entities_by_id = {e["id"]: e for e in entities}

        scenario_logs = []
        if scenario_id:
            scen_row = self.db.fetchone("SELECT action, parameters FROM scenarios WHERE id = ?;", (scenario_id,))
            if scen_row:
                action = scen_row["action"]
                params = json.loads(scen_row["parameters"]) if isinstance(scen_row["parameters"], str) else scen_row["parameters"]
                entities_by_id, scenario_logs = RuleRegistry.apply_scenario_perturbation(
                    entities_by_id, action, params, world_type=world_type
                )
                logger.info(f"Applied scenario '{action}' to branch '{branch_id}': {len(scenario_logs)} effects logged.")

        entities = list(entities_by_id.values())
        initial_hash = self._compute_state_hash(entities)
        self.db.execute(
            "UPDATE simulation_branches SET initial_state_hash = ?, status = 'running' WHERE id = ?;",
            (initial_hash, branch_id)
        )

        metrics_history: Dict[str, List[float]] = {m["name"]: [] for m in declared_metrics}
        timeline_snapshots = []
        anomalies_detected = []
        events_emitted = []

        if scenario_logs:
            for log_msg in scenario_logs:
                evt_id = f"evt_{uuid.uuid4().hex[:8]}"
                self.db.execute(
                    """
                    INSERT INTO simulation_events (id, branch_id, world_id, step, timestamp, event_type, description, details)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (evt_id, branch_id, world_id, 0, "T+00:00", "scenario_applied", log_msg, json.dumps({"source": "scenario"}))
                )
                events_emitted.append({"step": 0, "event_type": "scenario_applied", "description": log_msg})

        sample_interval = 1 if duration <= 60 else max(1, duration // 40)
        current_metrics: Dict[str, float] = {}

        for step in range(duration + 1):
            step_ts = f"T+{step:02d}:00"

            if step > 0:
                for e in entities:
                    etype = e.get("entity_type")
                    st = e.get("state", {})
                    if etype == "bus":
                        jitter = rng.uniform(-0.8, 0.8)
                        st["speed_mph"] = max(4.0, min(35.0, round(st.get("speed_mph", 15.0) + jitter, 1)))
                        if st.get("delay_minutes", 0) > 0.5:
                            st["delay_minutes"] = max(0.0, round(st["delay_minutes"] - rng.uniform(0.05, 0.2), 1))
                    elif etype == "road":
                        jitter = rng.uniform(-0.02, 0.02)
                        if not st.get("blocked", False):
                            st["congestion_index"] = max(0.05, min(0.99, round(st.get("congestion_index", 0.3) + jitter, 3)))
                    elif etype == "student":
                        if rng.random() < 0.08:
                            st["commute_time_minutes"] = max(5.0, round(st.get("commute_time_minutes", 15.0) + rng.uniform(-1.0, 1.0), 1))
                    elif etype == "ward":
                        if rng.random() < 0.15:
                            st["occupied_beds"] = max(5, min(e.get("attributes", {}).get("capacity_beds", 50), st.get("occupied_beds", 20) + rng.randint(-1, 1)))
                    elif etype == "patient":
                        if rng.random() < 0.1:
                            st["wait_time_minutes"] = max(2.0, round(st.get("wait_time_minutes", 15.0) + rng.uniform(-1.5, 1.5), 1))

            step_metrics = {}
            for m_def in declared_metrics:
                m_val = RuleRegistry.compute_metric(m_def, entities, world_type=world_type, prior_metrics=step_metrics)
                step_metrics[m_def["name"]] = m_val
                metrics_history[m_def["name"]].append(m_val)
            current_metrics = step_metrics

            for m_def in declared_metrics:
                m_name = m_def["name"]
                val = step_metrics.get(m_name, 0.0)
                h_min = m_def.get("healthy_min", float("-inf"))
                h_max = m_def.get("healthy_max", float("inf"))
                if val < h_min or val > h_max:
                    sev = "critical" if (val > h_max * 1.3 or val < h_min * 0.7) else "warning"
                    anom_desc = f"{m_def.get('display_name', m_name)} reached {val} {m_def.get('unit', '')} (healthy range: {h_min}-{h_max})."
                    anom_id = f"anom_{uuid.uuid4().hex[:8]}"
                    threshold_breached = h_max if val > h_max else h_min
                    self.db.execute(
                        """
                        INSERT INTO anomalies (id, branch_id, world_id, step, metric_name, severity, threshold, actual_value, description)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                        """,
                        (anom_id, branch_id, world_id, step, m_name, sev, threshold_breached, val, anom_desc)
                    )
                    anomalies_detected.append({
                        "id": anom_id, "step": step, "metric_name": m_name,
                        "severity": sev, "actual_value": val, "description": anom_desc
                    })

            if step % sample_interval == 0 or step == duration:
                snap_id = f"snap_{uuid.uuid4().hex[:8]}"
                state_hash = self._compute_state_hash(entities)
                state_snapshot_json = json.dumps({
                    "step": step,
                    "timestamp": step_ts,
                    "entities": entities,
                    "metrics": step_metrics
                })
                self.db.execute(
                    """
                    INSERT INTO simulation_states (id, branch_id, world_id, step, timestamp, state_snapshot, state_hash)
                    VALUES (?, ?, ?, ?, ?, ?, ?);
                    """,
                    (snap_id, branch_id, world_id, step, step_ts, state_snapshot_json, state_hash)
                )

                metric_snap_id = f"msnap_{uuid.uuid4().hex[:8]}"
                self.db.execute(
                    """
                    INSERT INTO metric_snapshots (id, branch_id, world_id, step, timestamp, metrics)
                    VALUES (?, ?, ?, ?, ?, ?);
                    """,
                    (metric_snap_id, branch_id, world_id, step, step_ts, json.dumps(step_metrics))
                )
                timeline_snapshots.append({"step": step, "timestamp": step_ts, "metrics": step_metrics})

        predictions = []
        for m_def in declared_metrics:
            m_name = m_def["name"]
            series = metrics_history.get(m_name, [])
            if len(series) >= 5:
                x = np.arange(len(series))
                y = np.array(series)
                poly = np.polyfit(x, y, 1)
                slope, intercept = poly[0], poly[1]
                horizon = 15
                future_x = np.arange(len(series), len(series) + horizon)
                projected = np.round(slope * future_x + intercept, 4).tolist()

                residuals = y - (slope * x + intercept)
                ss_res = np.sum(residuals**2)
                ss_tot = np.sum((y - np.mean(y))**2)
                r2 = 1.0 - (ss_res / (ss_tot + 1e-8))
                confidence = float(max(0.45, min(0.95, round(float(r2), 3) if not np.isnan(r2) else 0.65)))

                pred_id = f"pred_{uuid.uuid4().hex[:8]}"
                limitations = "Trend-extrapolation baseline using linear least-squares regression over simulation history. Assumes steady-state conditions without exogenous scenario shocks."
                self.db.execute(
                    """
                    INSERT INTO predictions (id, branch_id, world_id, target_metric, horizon_steps, predicted_values, confidence, method, limitations)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (pred_id, branch_id, world_id, m_name, horizon, json.dumps(projected), confidence, "linear_trend_extrapolation", limitations)
                )
                predictions.append({
                    "target_metric": m_name,
                    "horizon_steps": horizon,
                    "predicted_values": projected,
                    "confidence": confidence,
                    "method": "linear_trend_extrapolation",
                    "limitations": limitations
                })

        now_iso = datetime.datetime.utcnow().isoformat()
        self.db.execute(
            "UPDATE simulation_branches SET status = 'completed', completed_at = ? WHERE id = ?;",
            (now_iso, branch_id)
        )

        return {
            "branch_id": branch_id,
            "world_id": world_id,
            "status": "completed",
            "duration": duration,
            "final_metrics": current_metrics,
            "snapshots_count": len(timeline_snapshots),
            "anomalies_count": len(anomalies_detected),
            "events_count": len(events_emitted),
            "predictions": predictions
        }
