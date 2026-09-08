"""
GenAI-Assisted World Creator Service for WorldTwin AI.
Synthesizes structured World Templates from natural language descriptions.
Generates candidate entity types, spatial distributions, metric definitions,
and scenario vocabularies for human review and approval.
"""

import json
import logging
from typing import Any, Dict, List, Optional
from backend.app.services.generator_service import WorldGenerator

logger = logging.getLogger("worldtwin.creator")


class WorldCreatorAgent:
    """Generates structured digital twin proposals from natural language specs."""

    def __init__(self):
        self.generator = WorldGenerator()

    def propose_world_template(self, prompt: str) -> Dict[str, Any]:
        """Propose a valid World Template spec from a natural language prompt."""
        p_lower = prompt.lower()

        if any(w in p_lower for w in ["hospital", "clinic", "healthcare", "icu", "patient", "doctor", "triage"]):
            world_type = "hospital"
            default_name = "Metropolitan Hospital Center Digital Twin"
            description = "High-fidelity digital twin of a hospital system simulating triage, bed allocation, emergency surges, and patient flow."
            entity_types = [
                {
                    "name": "ward",
                    "display_name": "Hospital Ward / Department",
                    "count": 4,
                    "attributes_schema": { "capacity_beds": "integer", "specialty": "string" },
                    "state_schema": { "occupied_beds": "integer", "staff_on_duty": "integer", "status": "string" },
                    "placement": "explicit",
                    "seed_instances": [
                        {
                            "id_suffix": "ward_ed",
                            "name": "Emergency Department",
                            "position": { "x": 300, "y": 300, "topology": { "node_id": "dept_ed", "level": 1 } },
                            "attributes": { "capacity_beds": 35, "specialty": "Emergency" },
                            "state": { "occupied_beds": 28, "staff_on_duty": 12, "status": "nominal" }
                        },
                        {
                            "id_suffix": "ward_icu",
                            "name": "Intensive Care Unit (ICU)",
                            "position": { "x": 300, "y": 700, "topology": { "node_id": "dept_icu", "level": 2 } },
                            "attributes": { "capacity_beds": 20, "specialty": "Critical Care" },
                            "state": { "occupied_beds": 16, "staff_on_duty": 10, "status": "nominal" }
                        },
                        {
                            "id_suffix": "ward_surg",
                            "name": "Surgical Inpatient Ward",
                            "position": { "x": 700, "y": 300, "topology": { "node_id": "dept_surg", "level": 3 } },
                            "attributes": { "capacity_beds": 50, "specialty": "Surgery" },
                            "state": { "occupied_beds": 34, "staff_on_duty": 8, "status": "nominal" }
                        },
                        {
                            "id_suffix": "ward_gen",
                            "name": "General Medicine Ward",
                            "position": { "x": 700, "y": 700, "topology": { "node_id": "dept_gen", "level": 2 } },
                            "attributes": { "capacity_beds": 60, "specialty": "Internal Medicine" },
                            "state": { "occupied_beds": 42, "staff_on_duty": 9, "status": "nominal" }
                        }
                    ]
                },
                {
                    "name": "staff",
                    "display_name": "Medical Staff / Care Team",
                    "count": 4,
                    "attributes_schema": { "role": "string", "shift": "string" },
                    "state_schema": { "assigned_ward": "string", "fatigue_index": "number", "status": "string" },
                    "placement": "explicit",
                    "seed_instances": [
                        {
                            "id_suffix": "staff_trauma1",
                            "name": "Trauma Team Alpha",
                            "position": { "x": 320, "y": 320, "topology": { "node_id": "dept_ed" } },
                            "attributes": { "role": "Emergency Medicine", "shift": "day" },
                            "state": { "assigned_ward": "ward_ed", "fatigue_index": 0.35, "status": "active" }
                        },
                        {
                            "id_suffix": "staff_icu1",
                            "name": "ICU Intensivist Team",
                            "position": { "x": 320, "y": 680, "topology": { "node_id": "dept_icu" } },
                            "attributes": { "role": "Critical Care", "shift": "day" },
                            "state": { "assigned_ward": "ward_icu", "fatigue_index": 0.42, "status": "active" }
                        }
                    ]
                },
                {
                    "name": "patient",
                    "display_name": "Inpatient / Triage Patient",
                    "count": 40,
                    "attributes_schema": { "triage_acuity": "integer", "age": "integer" },
                    "state_schema": { "status": "string", "wait_time_minutes": "number", "pain_score": "number" },
                    "placement": "cluster_around",
                    "cluster_targets": ["ward_ed", "ward_surg", "ward_gen"]
                },
                {
                    "name": "ambulance",
                    "display_name": "Emergency Medical Transport",
                    "count": 2,
                    "attributes_schema": { "vehicle_id": "string", "equipment_level": "string" },
                    "state_schema": { "status": "string", "eta_minutes": "number", "patient_onboard": "boolean" },
                    "placement": "explicit",
                    "seed_instances": [
                        {
                            "id_suffix": "amb_01",
                            "name": "Paramedic Unit 1",
                            "position": { "x": 150, "y": 300 },
                            "attributes": { "vehicle_id": "EMS-101", "equipment_level": "ALS" },
                            "state": { "status": "in_transit", "eta_minutes": 4.5, "patient_onboard": True }
                        }
                    ]
                }
            ]
            relationships = [
                { "relationship_type": "admitted_to", "source_entity_type": "patient", "target_entity_type": "ward" },
                { "relationship_type": "assigned_to_ward", "source_entity_type": "staff", "target_entity_type": "ward" },
                { "relationship_type": "transporting_to", "source_entity_type": "ambulance", "target_entity_type": "ward" }
            ]
            metrics = [
                {
                    "name": "ed_wait_time",
                    "display_name": "ED Average Triage Wait Time",
                    "description": "Mean waiting duration for triage assessment in the Emergency Department.",
                    "unit": "minutes",
                    "healthy_min": 5.0,
                    "healthy_max": 30.0,
                    "computation_type": "avg_state_field",
                    "target_entity_type": "patient",
                    "target_field": "wait_time_minutes"
                },
                {
                    "name": "bed_occupancy_rate",
                    "display_name": "Hospital Bed Occupancy Rate",
                    "description": "Ratio of occupied beds to total licensed capacity across all departments.",
                    "unit": "ratio",
                    "healthy_min": 0.60,
                    "healthy_max": 0.85,
                    "computation_type": "ratio_state_attribute",
                    "target_entity_type": "ward",
                    "state_field": "occupied_beds",
                    "attr_field": "capacity_beds"
                },
                {
                    "name": "nurse_to_patient_ratio",
                    "display_name": "Staff Fatigue Index",
                    "description": "Mean clinician workload and fatigue index.",
                    "unit": "ratio",
                    "healthy_min": 0.15,
                    "healthy_max": 0.55,
                    "computation_type": "avg_state_field",
                    "target_entity_type": "staff",
                    "target_field": "fatigue_index"
                }
            ]
            scenario_vocab = [
                {
                    "action": "mass_casualty_surge",
                    "display_name": "Mass Casualty Incident",
                    "description": "Simulates a sudden arrival of multiple high-acuity trauma patients in the Emergency Department.",
                    "target_entity_types": ["ward", "patient", "ambulance"],
                    "allowed_parameters": [
                        { "name": "surge_patient_count", "type": "integer", "description": "Number of acute patients arriving", "default": 20 }
                    ],
                    "example_phrases": [
                        "Simulate a 20-patient highway accident mass casualty surge",
                        "Trigger an emergency code orange surge in ED"
                    ]
                },
                {
                    "action": "divert_ambulances",
                    "display_name": "Emergency Divert Status",
                    "description": "Diverts incoming ambulance transports to neighboring regional medical facilities.",
                    "target_entity_types": ["ambulance", "ward"],
                    "allowed_parameters": [
                        { "name": "divert_percentage", "type": "number", "description": "Fraction of transport volume diverted", "default": 0.5 }
                    ],
                    "example_phrases": [
                        "Place Emergency Department on divert for 2 hours",
                        "Divert 50% of incoming non-trauma ambulances"
                    ]
                },
                {
                    "action": "call_in_backup_staff",
                    "display_name": "Mobilize On-Call Medical Staff",
                    "description": "Activates reserve nursing and surgical teams to expand clinical throughput.",
                    "target_entity_types": ["staff", "ward"],
                    "allowed_parameters": [
                        { "name": "additional_nurses", "type": "integer", "description": "Number of backup clinicians deployed", "default": 8 }
                    ],
                    "example_phrases": [
                        "Call in 8 backup emergency nurses to handle the surge",
                        "Deploy reserve critical care teams"
                    ]
                }
            ]
            knowledge = [
                {
                    "title": "Hospital Emergency Escalation and Divert Protocols",
                    "category": "clinical_operations",
                    "content": "When ED bed occupancy exceeds 90% or average triage wait time exceeds 45 minutes, hospital command enters Phase 2 Surge. Low-acuity ambulance transports are diverted to partner facilities, and reserve nursing staff are deployed."
                }
            ]
        else:
            world_type = "facility"
            default_name = f"Smart Facility Digital Twin ({prompt[:24]}...)"
            description = f"Configurable digital twin generated from: '{prompt}'."
            entity_types = [
                {
                    "name": "zone",
                    "display_name": "Operational Zone",
                    "count": 2,
                    "attributes_schema": { "area_sqft": "number" },
                    "state_schema": { "utilization": "number", "active": "boolean" },
                    "placement": "explicit",
                    "seed_instances": [
                        { "id_suffix": "z1", "name": "Main Operation Zone A", "position": { "x": 300, "y": 300 }, "attributes": { "area_sqft": 5000 }, "state": { "utilization": 0.65, "active": True } },
                        { "id_suffix": "z2", "name": "Logistics Zone B", "position": { "x": 700, "y": 700 }, "attributes": { "area_sqft": 8000 }, "state": { "utilization": 0.40, "active": True } }
                    ]
                }
            ]
            relationships = []
            metrics = [
                { "name": "facility_utilization", "display_name": "Facility Utilization", "description": "Mean utilization index.", "unit": "ratio", "healthy_min": 0.3, "healthy_max": 0.8, "computation_type": "avg_state_field", "target_entity_type": "zone", "target_field": "utilization" }
            ]
            scenario_vocab = [
                { "action": "reallocate_capacity", "display_name": "Reallocate Zone Capacity", "description": "Adjusts load balancing across zones.", "target_entity_types": ["zone"], "allowed_parameters": [{"name": "factor", "type": "number", "default": 1.2}], "example_phrases": ["Reallocate load to Zone B"] }
            ]
            knowledge = [
                { "title": "Facility Operational Operating Standards", "category": "standards", "content": "Operating utilization should remain between 40% and 80% to ensure sustainable asset wear and team safety." }
            ]

        proposal = {
            "world_type": world_type,
            "name": default_name,
            "description": description,
            "source_prompt": prompt,
            "declared_entity_types": entity_types,
            "declared_relationship_types": relationships,
            "metrics": metrics,
            "scenario_vocabulary": scenario_vocab,
            "initial_knowledge": knowledge,
            "status": "proposal_pending_confirmation",
            "review_message": f"Proposed {world_type.capitalize()} Digital Twin template with {len(entity_types)} entity types ({', '.join(e['name'] for e in entity_types)}), {len(relationships)} relationship types, and {len(metrics)} live metrics. Requires human confirmation to instantiate."
        }

        valid, errs = self.generator.validate_template(proposal)
        proposal["template_valid"] = valid
        proposal["validation_errors"] = errs
        return proposal
