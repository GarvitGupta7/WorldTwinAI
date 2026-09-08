"""
World Meta-Model and Generator Engine for WorldTwin AI.
Generates fully functional, stateful digital twin worlds from structured templates.
Treats all domains (campus, hospital, airport, factory) purely as data/configuration.
"""

import json
import uuid
import random
import logging
from typing import Any, Dict, List, Optional, Tuple
from backend.app.database import Database, db
from backend.app.models.world import WorldSchemaDefinition

logger = logging.getLogger("worldtwin.generator")


class WorldGenerator:
    """Instantiates complete digital twin environments from declarative templates."""

    def __init__(self, database: Optional[Database] = None):
        self.db = database or db

    def validate_template(self, template: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate template against the World meta-model requirements."""
        errors = []
        required_keys = ["world_type", "name", "declared_entity_types", "metrics", "scenario_vocabulary"]
        for key in required_keys:
            if key not in template:
                errors.append(f"Missing required top-level template key: '{key}'")

        entity_types = [et.get("name") for et in template.get("declared_entity_types", []) if isinstance(et, dict)]
        if not entity_types:
            errors.append("Template must declare at least one entity type in declared_entity_types.")

        # Validate metrics
        for idx, m in enumerate(template.get("metrics", [])):
            if not isinstance(m, dict) or "name" not in m or "computation_type" not in m:
                errors.append(f"Metric at index {idx} must have 'name' and 'computation_type'.")

        # Validate scenario vocabulary
        for idx, sv in enumerate(template.get("scenario_vocabulary", [])):
            if not isinstance(sv, dict) or "action" not in sv:
                errors.append(f"Scenario vocabulary at index {idx} must specify 'action'.")

        return len(errors) == 0, errors

    def instantiate_world(
        self,
        template: Dict[str, Any],
        custom_world_id: Optional[str] = None,
        custom_name: Optional[str] = None,
        seed: int = 42
    ) -> Dict[str, Any]:
        """Generate and persist a complete world instance from a template."""
        is_valid, errors = self.validate_template(template)
        if not is_valid:
            raise ValueError(f"Invalid world template: {'; '.join(errors)}")

        random.seed(seed)
        world_id = custom_world_id or f"world_{template['world_type']}_{uuid.uuid4().hex[:8]}"
        world_name = custom_name or template["name"]
        world_type = template["world_type"]
        description = template.get("description", "")

        schema_def_json = json.dumps({
            "world_type": world_type,
            "version": template.get("version", "1.0.0"),
            "declared_entity_types": [et["name"] for et in template["declared_entity_types"]],
            "declared_relationship_types": template.get("declared_relationship_types", []),
            "metrics": template.get("metrics", []),
            "scenario_vocabulary": template.get("scenario_vocabulary", []),
            "spatial_bounds": template.get("spatial_bounds", {"min_x": 0, "max_x": 1000, "min_y": 0, "max_y": 1000})
        })

        # 1. Insert World
        self.db.execute(
            """
            INSERT INTO worlds (id, name, world_type, description, schema_definition)
            VALUES (?, ?, ?, ?, ?);
            """,
            (world_id, world_name, world_type, description, schema_def_json)
        )

        # 2. Register Entity Types
        for et in template["declared_entity_types"]:
            et_name = et["name"]
            display_name = et.get("display_name", et_name.capitalize())
            schema_def = json.dumps({
                "attributes_schema": et.get("attributes_schema", {}),
                "state_schema": et.get("state_schema", {})
            })
            rules_def = json.dumps(et.get("rules", {"placement": et.get("placement", "explicit")}))
            self.db.execute(
                """
                INSERT INTO entity_types (world_id, name, display_name, schema_definition, rules_definition)
                VALUES (?, ?, ?, ?, ?);
                """,
                (world_id, et_name, display_name, schema_def, rules_def)
            )

        # 3. Instantiate Entities
        entities_created: List[Dict[str, Any]] = []
        entity_id_map: Dict[str, str] = {} # maps suffix or alias -> actual entity_id
        cluster_anchor_positions: Dict[str, Dict[str, float]] = {}

        for et in template["declared_entity_types"]:
            et_name = et["name"]
            placement = et.get("placement", "explicit")
            seed_instances = et.get("seed_instances", [])

            # Explicit instances
            for inst in seed_instances:
                inst_id = f"{world_id}_{inst.get('id_suffix', uuid.uuid4().hex[:6])}"
                alias = inst.get("id_suffix")
                if alias:
                    entity_id_map[alias] = inst_id

                pos = inst.get("position", {"x": 500, "y": 500})
                if alias:
                    cluster_anchor_positions[alias] = {"x": pos.get("x", 500), "y": pos.get("y", 500)}

                ent_record = {
                    "id": inst_id,
                    "world_id": world_id,
                    "entity_type": et_name,
                    "name": inst.get("name", f"{et_name} {inst_id}"),
                    "position": json.dumps(pos),
                    "state": json.dumps(inst.get("state", {})),
                    "attributes": json.dumps(inst.get("attributes", {})),
                    "relationships": json.dumps(inst.get("relationships", []))
                }
                self.db.execute(
                    """
                    INSERT INTO entities (id, world_id, entity_type, name, position, state, attributes, relationships)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        ent_record["id"], ent_record["world_id"], ent_record["entity_type"],
                        ent_record["name"], ent_record["position"], ent_record["state"],
                        ent_record["attributes"], ent_record["relationships"]
                    )
                )
                entities_created.append(ent_record)

            # Generative procedural instances (e.g. students, patients, workers)
            count = et.get("count", 0) - len(seed_instances)
            if count > 0:
                cluster_targets = et.get("cluster_targets", [])
                for i in range(count):
                    gen_id = f"{world_id}_{et_name}_{i+1:03d}"
                    if cluster_targets and any(t in cluster_anchor_positions for t in cluster_targets):
                        target_alias = random.choice(cluster_targets)
                        anchor = cluster_anchor_positions.get(target_alias, {"x": 500, "y": 500})
                        pos_x = max(20, min(980, anchor["x"] + random.gauss(0, 45)))
                        pos_y = max(20, min(980, anchor["y"] + random.gauss(0, 45)))
                    else:
                        pos_x = random.uniform(50, 950)
                        pos_y = random.uniform(50, 950)

                    # Dynamic state and attributes based on entity type schema
                    if et_name == "student":
                        majors = ["Computer Science", "Mechanical Eng", "Biology", "Economics", "History", "Literature"]
                        transits = ["walking", "bus", "bicycle", "walking"]
                        origin_alias = random.choice(["bld_dorms", "bld_union"])
                        dest_alias = random.choice(["bld_science", "bld_library", "bld_admin"])
                        attributes = {
                            "major": random.choice(majors),
                            "year": random.randint(1, 4),
                            "preferred_transit": random.choice(transits)
                        }
                        state = {
                            "transit_mode": random.choice(transits),
                            "origin": entity_id_map.get(origin_alias, origin_alias),
                            "destination": entity_id_map.get(dest_alias, dest_alias),
                            "commute_time_minutes": round(random.uniform(8.0, 22.0), 1),
                            "stress_level": round(random.uniform(0.1, 0.45), 2)
                        }
                        relationships = [entity_id_map.get(dest_alias, dest_alias)]
                    elif et_name == "patient":
                        attributes = {"triage_acuity": random.randint(1, 5), "age": random.randint(18, 85)}
                        state = {"status": "waiting", "wait_time_minutes": round(random.uniform(10.0, 45.0), 1), "pain_score": random.randint(2, 8)}
                        relationships = []
                    else:
                        attributes = {"generated_index": i + 1}
                        state = {"active": True, "load": round(random.uniform(0.2, 0.8), 2)}
                        relationships = []

                    ent_record = {
                        "id": gen_id,
                        "world_id": world_id,
                        "entity_type": et_name,
                        "name": f"{et.get('display_name', et_name.capitalize())} #{i+1}",
                        "position": json.dumps({"x": round(pos_x, 1), "y": round(pos_y, 1)}),
                        "state": json.dumps(state),
                        "attributes": json.dumps(attributes),
                        "relationships": json.dumps(relationships)
                    }
                    self.db.execute(
                        """
                        INSERT INTO entities (id, world_id, entity_type, name, position, state, attributes, relationships)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                        """,
                        (
                            ent_record["id"], ent_record["world_id"], ent_record["entity_type"],
                            ent_record["name"], ent_record["position"], ent_record["state"],
                            ent_record["attributes"], ent_record["relationships"]
                        )
                    )
                    entities_created.append(ent_record)

        # 4. Generate Relationships
        rel_types = template.get("declared_relationship_types", [])
        for rel_spec in rel_types:
            r_type = rel_spec["relationship_type"]
            src_type = rel_spec["source_entity_type"]
            tgt_type = rel_spec["target_entity_type"]

            src_entities = self.db.fetchall(
                "SELECT id, position FROM entities WHERE world_id = ? AND entity_type = ?;",
                (world_id, src_type)
            )
            tgt_entities = self.db.fetchall(
                "SELECT id, position FROM entities WHERE world_id = ? AND entity_type = ?;",
                (world_id, tgt_type)
            )

            if src_entities and tgt_entities:
                for src in src_entities:
                    # Connect to nearest target
                    src_pos = json.loads(src["position"])
                    best_tgt = None
                    best_dist = float("inf")
                    for tgt in tgt_entities:
                        tgt_pos = json.loads(tgt["position"])
                        dx = src_pos.get("x", 0) - tgt_pos.get("x", 0)
                        dy = src_pos.get("y", 0) - tgt_pos.get("y", 0)
                        dist = (dx**2 + dy**2) ** 0.5
                        if dist < best_dist:
                            best_dist = dist
                            best_tgt = tgt

                    if best_tgt:
                        rel_id = f"rel_{uuid.uuid4().hex[:8]}"
                        self.db.execute(
                            """
                            INSERT INTO relationships (id, world_id, source_entity_id, target_entity_id, relationship_type, attributes)
                            VALUES (?, ?, ?, ?, ?, ?);
                            """,
                            (rel_id, world_id, src["id"], best_tgt["id"], r_type, json.dumps({"distance": round(best_dist, 1)}))
                        )

        # 5. Populate Initial Knowledge Base
        for doc in template.get("initial_knowledge", []):
            k_id = f"kdoc_{uuid.uuid4().hex[:8]}"
            self.db.execute(
                """
                INSERT INTO knowledge_documents (id, world_id, title, category, content, metadata)
                VALUES (?, ?, ?, ?, ?, ?);
                """,
                (k_id, world_id, doc["title"], doc.get("category", "general"), doc["content"], json.dumps({"source": "world_template"}))
            )

        # 6. Create Seed Playbook of Interventions
        if world_type == "campus":
            playbook = [
                {
                    "name": "Deploy 2 Additional Peak Shuttles",
                    "description": "Increases shuttle frequency across campus corridors to relieve student transit delay.",
                    "scenario_action": "increase_bus_frequency",
                    "parameters": [{"name": "multiplier", "value": 1.5, "unit": "factor"}],
                    "cost": 3.5,
                    "complexity": 2.0,
                    "expected_benefit": 8.0
                },
                {
                    "name": "Stagger Class Start Times by 20 Minutes",
                    "description": "Redistributes class transition surges between academic halls and dorms.",
                    "scenario_action": "shift_class_schedule",
                    "parameters": [{"name": "stagger_minutes", "value": 20, "unit": "minutes"}],
                    "cost": 1.5,
                    "complexity": 5.0,
                    "expected_benefit": 7.5
                },
                {
                    "name": "Divert Transit via Perimeter Connector",
                    "description": "Reroutes bus and service vehicles away from central campus core corridors.",
                    "scenario_action": "reroute_buses",
                    "parameters": [
                        {"name": "avoid_road_id", "value": "road_union"},
                        {"name": "alternate_road_id", "value": "road_perimeter"}
                    ],
                    "cost": 2.0,
                    "complexity": 3.0,
                    "expected_benefit": 6.5
                }
            ]
            for pb in playbook:
                int_id = f"intv_{uuid.uuid4().hex[:8]}"
                self.db.execute(
                    """
                    INSERT INTO interventions (id, world_id, name, description, scenario_action, parameters, cost, complexity, expected_benefit)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (int_id, world_id, pb["name"], pb["description"], pb["scenario_action"], json.dumps(pb["parameters"]), pb["cost"], pb["complexity"], pb["expected_benefit"])
                )

        logger.info(f"Instantiated world '{world_name}' ({world_id}) with {len(entities_created)} entities.")
        return {
            "world_id": world_id,
            "name": world_name,
            "world_type": world_type,
            "entity_count": len(entities_created),
            "declared_entity_types": [et["name"] for et in template["declared_entity_types"]],
            "metrics": [m["name"] for m in template.get("metrics", [])]
        }
