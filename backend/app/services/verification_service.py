"""
Independent Verification Service for WorldTwin AI.
Re-reads resulting state directly from the database and confirms it matches
what was claimed by tool executions. Never trusts LLM narration.
"""

import logging
from typing import Any, Dict, List, Optional
from backend.app.database import Database, db
from backend.app.models.copilot import VerificationCheck, EvidenceItem

logger = logging.getLogger("worldtwin.verification")


class VerificationService:
    """Verifies claimed actions against real database source of truth."""

    def __init__(self, database: Optional[Database] = None):
        self.db = database or db

    def verify_branch_created(self, branch_id: str) -> VerificationCheck:
        row = self.db.fetchone("SELECT id, status, initial_state_hash FROM simulation_branches WHERE id = ?;", (branch_id,))
        if row:
            return VerificationCheck(
                target_resource_type="branch",
                resource_id=branch_id,
                expected_property="branch_persisted",
                observed_value=row["status"],
                verified=True,
                details=f"Branch exists with status '{row['status']}' and state hash '{row['initial_state_hash'][:12]}...'."
            )
        return VerificationCheck(
            target_resource_type="branch",
            resource_id=branch_id,
            expected_property="branch_persisted",
            observed_value=None,
            verified=False,
            details=f"Verification failed: branch '{branch_id}' not found in database."
        )

    def verify_metrics_exist(self, branch_id: str) -> VerificationCheck:
        row = self.db.fetchone("SELECT COUNT(*) as count FROM metric_snapshots WHERE branch_id = ?;", (branch_id,))
        count = row["count"] if row else 0
        return VerificationCheck(
            target_resource_type="metrics",
            resource_id=branch_id,
            expected_property="metric_snapshots_exist",
            observed_value=count,
            verified=count > 0,
            details=f"Verified {count} metric snapshots exist in database for branch '{branch_id}'." if count > 0 else "No metric snapshots found."
        )

    def verify_interventions_evaluated(self, baseline_branch_id: str) -> VerificationCheck:
        rows = self.db.fetchall("SELECT id, score, ranking FROM intervention_runs WHERE baseline_branch_id = ?;", (baseline_branch_id,))
        count = len(rows)
        return VerificationCheck(
            target_resource_type="intervention_runs",
            resource_id=baseline_branch_id,
            expected_property="counterfactual_runs_persisted",
            observed_value=count,
            verified=count > 0,
            details=f"Verified {count} counterfactual intervention runs persisted for baseline '{baseline_branch_id}'."
        )

    def verify_report_created(self, report_id: str) -> VerificationCheck:
        row = self.db.fetchone("SELECT id, title, created_at FROM reports WHERE id = ?;", (report_id,))
        if row:
            return VerificationCheck(
                target_resource_type="report",
                resource_id=report_id,
                expected_property="report_persisted",
                observed_value=row["title"],
                verified=True,
                details=f"Report '{row['title']}' verified in database."
            )
        return VerificationCheck(
            target_resource_type="report",
            resource_id=report_id,
            expected_property="report_persisted",
            observed_value=None,
            verified=False,
            details=f"Report '{report_id}' not found in database."
        )
