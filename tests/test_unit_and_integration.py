"""
Comprehensive Unit & Integration Test Suite for WorldTwin AI.
Covers migrations, world generation, deterministic simulation, true branch chaining,
scenario parsing, counterfactual interventions, copilot verification loop,
and adversarial safety boundaries.
"""

import os
import json
import unittest

from backend.app.database import db
from backend.app.migrations.runner import MigrationRunner
from backend.app.services.generator_service import WorldGenerator
from backend.app.services.rule_registry import RuleRegistry
from backend.app.services.simulation_engine import SimulationEngine
from backend.app.services.scenario_parser import ScenarioParser
from backend.app.services.branch_service import BranchService
from backend.app.services.intervention_service import InterventionService
from backend.app.services.knowledge_service import KnowledgeService
from backend.app.services.report_service import ReportService
from backend.app.services.verification_service import VerificationService
from backend.app.services.copilot_planner import CopilotPlanner
from backend.app.models.copilot import StructuredPlan, ToolCall


class TestWorldTwinCore(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # 1. Run migrations
        runner = MigrationRunner(db)
        runner.run_migrations()

        # 2. Ensure default campus world exists
        w_row = db.fetchone("SELECT id FROM worlds WHERE id = 'world_campus_01';")
        if not w_row:
            template_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "..", "backend", "app", "templates", "campus_template.json"
            )
            with open(template_path) as f:
                template = json.load(f)
            gen = WorldGenerator(db)
            gen.instantiate_world(template, custom_world_id="world_campus_01")

    def test_01_migrations_and_tables(self):
        """Verify incremental migrations created all required relational tables."""
        tables = db.fetchall("SELECT name FROM sqlite_master WHERE type='table';")
        table_names = set(t["name"] for t in tables)
        expected = {
            "worlds", "entity_types", "entities", "relationships",
            "scenarios", "simulation_branches", "simulation_states",
            "metric_snapshots", "simulation_events", "anomalies", "predictions",
            "interventions", "intervention_runs", "knowledge_documents",
            "reports", "copilot_sessions", "schema_migrations"
        }
        for exp in expected:
            self.assertIn(exp, table_names, f"Table '{exp}' missing from database schema")

    def test_02_world_generator_and_zero_division_guard(self):
        """Verify world generator validation and ensure aggregate metrics are protected against zero-division."""
        generator = WorldGenerator(db)

        # Invalid template rejected
        is_valid, errs = generator.validate_template({"world_type": "invalid"})
        self.assertFalse(is_valid)

        # Test RuleRegistry zero-division defense with empty entities
        m_def = {
            "name": "test_metric",
            "computation_type": "avg_state_field",
            "target_entity_type": "nonexistent",
            "target_field": "val"
        }
        res = RuleRegistry.compute_metric(m_def, entities=[])
        self.assertEqual(res, 0.0)

        m_ratio = {
            "name": "test_ratio",
            "computation_type": "ratio_state_attribute",
            "target_entity_type": "nonexistent",
            "state_field": "a",
            "attr_field": "b"
        }
        res_ratio = RuleRegistry.compute_metric(m_ratio, entities=[])
        self.assertEqual(res_ratio, 0.0)

    def test_03_deterministic_simulation_reproducibility(self):
        """Verify identical seed produces identical state hash and timeline metrics."""
        engine = SimulationEngine(db)
        b_service = BranchService(db)

        # Create two separate branches with identical seed 42
        b1 = b_service.create_branch("world_campus_01", "Sim Run A", seed=42, duration=20)
        res1 = b_service.run_branch(b1["id"])

        b2 = b_service.create_branch("world_campus_01", "Sim Run B", seed=42, duration=20)
        res2 = b_service.run_branch(b2["id"])

        # Compare terminal metrics
        self.assertEqual(res1["final_metrics"], res2["final_metrics"], "Deterministic simulation diverged on identical seed!")

        # Verify predictions were generated with honest limitations
        self.assertTrue(len(res1["predictions"]) > 0)
        for p in res1["predictions"]:
            self.assertIn("Trend-extrapolation baseline", p["limitations"])
            self.assertGreaterEqual(p["confidence"], 0.4)

    def test_04_true_branch_chaining_from_parent_terminal_state(self):
        """Verify that child branch starts from parent branch terminal snapshot, not world seed."""
        b_service = BranchService(db)

        # 1. Create parent branch with a road closure scenario
        scen_id = "scen_test_chain_parent"
        db.execute(
            """
            INSERT OR REPLACE INTO scenarios (id, world_id, original_text, action, parameters, assumptions, ambiguities, valid, parser_metadata)
            VALUES (?, 'world_campus_01', 'Close Central Academic Avenue', 'close_road', '[]', '[]', '[]', 1, '{}');
            """,
            (scen_id,)
        )

        parent_b = b_service.create_branch(
            "world_campus_01", "Parent Road Closure",
            scenario_id=scen_id, seed=42, duration=25
        )
        b_service.run_branch(parent_b["id"])

        # Fetch parent terminal state snapshot
        parent_terminal = db.fetchone(
            "SELECT state_snapshot FROM simulation_states WHERE branch_id = ? ORDER BY step DESC LIMIT 1;",
            (parent_b["id"],)
        )
        self.assertIsNotNone(parent_terminal)
        parent_snapshot_data = json.loads(parent_terminal["state_snapshot"])
        parent_terminal_entities = {e["id"]: e for e in parent_snapshot_data["entities"]}

        # 2. Create child branch chained off parent
        child_b = b_service.create_branch(
            "world_campus_01", "Child Chained Branch",
            parent_branch_id=parent_b["id"], seed=42, duration=10
        )
        b_service.run_branch(child_b["id"])

        # Fetch step 0 of child branch
        child_initial = db.fetchone(
            "SELECT state_snapshot FROM simulation_states WHERE branch_id = ? AND step = 0;",
            (child_b["id"],)
        )
        self.assertIsNotNone(child_initial)
        child_initial_data = json.loads(child_initial["state_snapshot"])
        child_initial_entities = {e["id"]: e for e in child_initial_data["entities"]}

        # Verify child initial entities match parent terminal entities (e.g. road blocked status)
        for eid, p_ent in parent_terminal_entities.items():
            if p_ent.get("entity_type") == "road" and p_ent["state"].get("blocked"):
                self.assertTrue(
                    child_initial_entities[eid]["state"].get("blocked"),
                    f"Child branch failed to inherit blocked state from parent terminal snapshot for entity {eid}!"
                )

    def test_05_scenario_parsing_and_confidence_calibration(self):
        """Verify scenario parser maps actions, estimates calibrated confidence, and asks clarifying questions for ambiguous inputs."""
        parser = ScenarioParser(db)

        # Clear query
        res = parser.parse_scenario("world_campus_01", "Close North Campus Parkway for maintenance")
        self.assertTrue(res.valid)
        self.assertEqual(res.action, "close_road")
        self.assertGreater(res.confidence, 0.85)

        # Unsupported / ambiguous query
        res_ambig = parser.parse_scenario("world_campus_01", "Fly a spaceship over the galaxy")
        self.assertFalse(res_ambig.valid)
        self.assertEqual(res_ambig.action, "unsupported")
        self.assertIsNotNone(res_ambig.clarification_question)

    def test_06_counterfactual_interventions_evaluation(self):
        """Verify interventions are actually simulated as counterfactual branches and ranked from observed outcomes."""
        b_service = BranchService(db)
        intv_service = InterventionService(db)

        base_b = b_service.create_branch("world_campus_01", "Base For Interventions", seed=42, duration=20)
        b_service.run_branch(base_b["id"])

        rankings = intv_service.evaluate_interventions("world_campus_01", base_b["id"])
        self.assertTrue(len(rankings) > 0)

        # Verify ranking order
        for i in range(len(rankings) - 1):
            self.assertGreaterEqual(rankings[i]["score"], rankings[i+1]["score"])

        # Verify counterfactual branches exist in database
        for r in rankings:
            cf_branch_id = r["counterfactual_branch_id"]
            row = db.fetchone("SELECT status FROM simulation_branches WHERE id = ?;", (cf_branch_id,))
            self.assertIsNotNone(row)
            self.assertEqual(row["status"], "completed")

    def test_07_copilot_verification_loop_and_evidence(self):
        """Verify Copilot command loop executes plan, checks DB independently, and returns evidence."""
        copilot = CopilotPlanner(db)
        res = copilot.execute_copilot_turn("world_campus_01", "What if we close Central Academic Avenue?")

        self.assertEqual(res.status, "verified")
        self.assertTrue(len(res.executed_tools) > 0)
        self.assertTrue(len(res.verification_checks) > 0)
        self.assertTrue(all(v.verified for v in res.verification_checks))
        self.assertTrue(len(res.evidence) > 0)

    def test_08_adversarial_tool_refusal(self):
        """Adversarial test: Copilot must refuse unapproved tools or direct SQL execution attempts."""
        copilot = CopilotPlanner(db)

        # Forge plan with disallowed tool
        adversarial_plan = StructuredPlan(
            intent="malicious_injection",
            reasoning="Attempting raw DB drop",
            tool_calls=[ToolCall(tool_name="drop_database", arguments={"target": "all"})]
        )

        validation = copilot.validate_plan(adversarial_plan, "world_campus_01")
        self.assertFalse(validation.is_valid)
        self.assertIn("Disallowed tool call", validation.errors[0])

    def test_09_anti_hallucination_unverified_fallback(self):
        """Proves that if an entity or branch cannot be verified against DB, system reports unverified failure, never faking success."""
        verif_service = VerificationService(db)

        # Non-existent branch verification
        fake_id = "branch_completely_fabricated_999"
        check = verif_service.verify_branch_created(fake_id)
        self.assertFalse(check.verified)
        self.assertEqual(check.observed_value, None)
        self.assertIn("Verification failed", check.details)


if __name__ == "__main__":
    unittest.main()
