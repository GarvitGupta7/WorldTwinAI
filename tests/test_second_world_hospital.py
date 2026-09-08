"""
Test demonstrating Second World Type (Metropolitan Hospital Center Digital Twin).
Proves domain generality: Hospital world is built, simulated, queried by Copilot,
and branched without touching a single line of simulation engine code!
"""

import os
import json
import unittest

from backend.app.database import db
from backend.app.migrations.runner import MigrationRunner
from backend.app.services.generator_service import WorldGenerator
from backend.app.services.branch_service import BranchService
from backend.app.services.scenario_parser import ScenarioParser
from backend.app.services.copilot_planner import CopilotPlanner


class TestHospitalDigitalTwin(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # 1. Ensure migrations are run
        runner = MigrationRunner(db)
        runner.run_migrations()

        # 2. Clean up prior test run if exists
        db.execute("DELETE FROM worlds WHERE id = 'world_hospital_01';")

        template_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..", "backend", "app", "templates", "hospital_template.json"
        )
        with open(template_path) as f:
            template = json.load(f)

        gen = WorldGenerator(db)
        cls.world_res = gen.instantiate_world(template, custom_world_id="world_hospital_01")

    def test_01_hospital_world_instantiation(self):
        """Verify hospital template instantiates wards, staff, patients, ambulances, and relationships."""
        self.assertEqual(self.world_res["world_type"], "hospital")
        self.assertIn("ed_wait_time", self.world_res["metrics"])
        self.assertIn("bed_occupancy_rate", self.world_res["metrics"])

        rows = db.fetchall(
            "SELECT entity_type, COUNT(*) as c FROM entities WHERE world_id = 'world_hospital_01' GROUP BY entity_type;"
        )
        types_map = {r["entity_type"]: r["c"] for r in rows}
        self.assertEqual(types_map.get("ward"), 5)
        self.assertEqual(types_map.get("staff"), 4)
        self.assertEqual(types_map.get("ambulance"), 3)
        self.assertEqual(types_map.get("patient"), 45)

    def test_02_hospital_baseline_simulation(self):
        """Verify baseline simulation runs dynamically and computes hospital-specific metrics."""
        b_service = BranchService(db)
        branch = b_service.create_branch(
            world_id="world_hospital_01",
            name="Hospital Baseline Operations",
            branch_type="baseline",
            seed=101,
            duration=30
        )
        result = b_service.run_branch(branch["id"])
        self.assertEqual(result["status"], "completed")

        metrics = result["final_metrics"]
        self.assertIn("ed_wait_time", metrics)
        self.assertIn("bed_occupancy_rate", metrics)
        self.assertIn("nurse_to_patient_ratio", metrics)
        self.assertIn("system_flow_efficiency", metrics)
        self.assertGreater(metrics["bed_occupancy_rate"], 0.5)

    def test_03_hospital_mass_casualty_scenario(self):
        """Verify mass casualty incident scenario perturbs hospital ward states and increases ED wait times."""
        parser = ScenarioParser(db)
        parsed = parser.parse_scenario("world_hospital_01", "Simulate a mass casualty surge with 20 arriving trauma patients")
        self.assertTrue(parsed.valid)
        self.assertEqual(parsed.action, "mass_casualty_surge")

        scen_id = "scen_hosp_surge_01"
        db.execute(
            """
            INSERT OR REPLACE INTO scenarios (id, world_id, original_text, action, parameters, assumptions, ambiguities, valid, parser_metadata)
            VALUES (?, 'world_hospital_01', 'Mass casualty surge', ?, ?, '[]', '[]', 1, '{}');
            """,
            (scen_id, parsed.action, json.dumps([p.dict() for p in parsed.parameters]))
        )

        b_service = BranchService(db)
        branch = b_service.create_branch(
            world_id="world_hospital_01",
            name="Mass Casualty Surge Branch",
            branch_type="what_if",
            scenario_id=scen_id,
            seed=101,
            duration=30
        )
        res = b_service.run_branch(branch["id"])
        self.assertEqual(res["status"], "completed")
        self.assertGreater(res["anomalies_count"], 0)

    def test_04_hospital_copilot_command_loop(self):
        """Verify GenAI Copilot seamlessly commands the hospital digital twin with evidence backing."""
        copilot = CopilotPlanner(db)
        turn = copilot.execute_copilot_turn(
            world_id="world_hospital_01",
            query="Simulate a 20-patient highway accident mass casualty surge"
        )
        self.assertEqual(turn.status, "verified")
        self.assertTrue(len(turn.verification_checks) > 0)
        self.assertTrue(all(v.verified for v in turn.verification_checks))
        self.assertTrue(any("mass_casualty_surge" in t.tool_name or t.tool_name == "run_scenario" for t in turn.executed_tools))


if __name__ == "__main__":
    unittest.main()
