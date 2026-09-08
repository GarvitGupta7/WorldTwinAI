"""
Generalized Rule & Formula Registry for WorldTwin AI.
Evaluates metrics dynamically and perturbs world entities based on scenario actions.
Guards against empty collections and zero-division across all domains.
"""

import math
import logging
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("worldtwin.rules")


class RuleRegistry:
    """Domain-generic computation and state-transition rules engine."""

    @staticmethod
    def compute_metric(
        metric_def: Dict[str, Any],
        entities: List[Dict[str, Any]],
        world_type: str = "generic",
        prior_metrics: Optional[Dict[str, float]] = None
    ) -> float:
        comp_type = metric_def.get("computation_type", "avg_state_field")
        target_type = metric_def.get("target_entity_type")
        target_field = metric_def.get("target_field")
        state_field = metric_def.get("state_field", target_field)
        attr_field = metric_def.get("attr_field")

        matching = [e for e in entities if e.get("entity_type") == target_type] if target_type and target_type != "world" else entities

        if comp_type == "avg_state_field":
            if not matching:
                return 0.0
            values = []
            for e in matching:
                st = e.get("state", {})
                if target_field in st and isinstance(st[target_field], (int, float)):
                    values.append(float(st[target_field]))
            if not values:
                return 0.0
            return round(sum(values) / max(len(values), 1), 4)

        elif comp_type == "ratio_state_attribute":
            if not matching:
                return 0.0
            total_state = 0.0
            total_attr = 0.0
            for e in matching:
                st = e.get("state", {})
                att = e.get("attributes", {})
                if state_field in st and isinstance(st[state_field], (int, float)):
                    total_state += float(st[state_field])
                if attr_field in att and isinstance(att[attr_field], (int, float)):
                    total_attr += float(att[attr_field])
            if total_attr <= 0.0:
                return 0.0
            return round(total_state / total_attr, 4)

        elif comp_type == "composite_flow_efficiency":
            prior = prior_metrics or {}
            if world_type == "campus":
                cong = prior.get("road_congestion", 0.3)
                occ = prior.get("bus_occupancy_rate", 0.5)
                efficiency = 1.0 - (cong * 0.45 + max(0.0, occ - 0.7) * 0.55)
                return round(max(0.05, min(0.99, efficiency)), 4)
            elif world_type == "hospital":
                wait = prior.get("ed_wait_time", 15.0)
                bed_occ = prior.get("bed_occupancy_rate", 0.7)
                efficiency = 1.0 - (min(wait / 60.0, 1.0) * 0.5 + max(0.0, bed_occ - 0.8) * 0.5)
                return round(max(0.05, min(0.99, efficiency)), 4)
            else:
                return 0.85

        elif comp_type == "count_state":
            count = 0
            for e in matching:
                st = e.get("state", {})
                if st.get("active") is True or st.get("blocked") is True:
                    count += 1
            return float(count)

        return 0.0

    @staticmethod
    def apply_scenario_perturbation(
        entities_by_id: Dict[str, Dict[str, Any]],
        action: str,
        parameters: List[Dict[str, Any]],
        world_type: str = "generic"
    ) -> Tuple[Dict[str, Dict[str, Any]], List[str]]:
        logs = []
        param_map = {p.get("name"): p.get("value") for p in parameters if isinstance(p, dict)}

        if action == "close_road":
            road_id = param_map.get("road_id")
            target_roads = []
            if road_id and road_id in entities_by_id:
                target_roads.append(entities_by_id[road_id])
            else:
                for e in entities_by_id.values():
                    if e.get("entity_type") == "road":
                        if road_id and (road_id.lower() in e.get("name", "").lower() or road_id in e.get("id", "")):
                            target_roads.append(e)
                if not target_roads:
                    for e in entities_by_id.values():
                        if e.get("entity_type") == "road" and "central" in e.get("name", "").lower():
                            target_roads.append(e)
                            break

            for road in target_roads:
                road["state"]["blocked"] = True
                road["state"]["status"] = "closed"
                road["state"]["current_flow_rate"] = 0.0
                road["state"]["congestion_index"] = 1.0
                logs.append(f"Road '{road['name']}' ({road['id']}) blocked. Flow set to 0, congestion index to 1.0.")

            for e in entities_by_id.values():
                if e.get("entity_type") == "road" and not e["state"].get("blocked"):
                    e["state"]["congestion_index"] = min(0.98, round(e["state"].get("congestion_index", 0.3) * 1.55, 3))
                    e["state"]["current_flow_rate"] = round(e["state"].get("current_flow_rate", 15.0) * 1.35, 1)

            for e in entities_by_id.values():
                if e.get("entity_type") == "bus":
                    e["state"]["delay_minutes"] = round(e["state"].get("delay_minutes", 1.0) + 6.5, 1)
                    e["state"]["speed_mph"] = max(5.0, round(e["state"].get("speed_mph", 15.0) * 0.55, 1))
                elif e.get("entity_type") == "student":
                    e["state"]["commute_time_minutes"] = round(e["state"].get("commute_time_minutes", 15.0) * 1.5, 1)
                    e["state"]["stress_level"] = min(1.0, round(e["state"].get("stress_level", 0.2) + 0.35, 2))

        elif action == "increase_bus_frequency":
            mult = float(param_map.get("multiplier", 1.5))
            for e in entities_by_id.values():
                if e.get("entity_type") == "bus":
                    e["state"]["occupancy_rate"] = max(0.2, round(e["state"].get("occupancy_rate", 0.7) / mult, 3))
                    e["state"]["delay_minutes"] = max(0.0, round(e["state"].get("delay_minutes", 3.0) * 0.4, 1))
                elif e.get("entity_type") == "student":
                    if e["state"].get("transit_mode") == "bus":
                        e["state"]["commute_time_minutes"] = max(5.0, round(e["state"].get("commute_time_minutes", 20.0) * 0.75, 1))
                        e["state"]["stress_level"] = max(0.05, round(e["state"].get("stress_level", 0.4) - 0.15, 2))
            logs.append(f"Bus frequency increased by factor of {mult}x across fleet.")

        elif action == "reroute_buses":
            avoid = str(param_map.get("avoid_road_id", "central"))
            alt = str(param_map.get("alternate_road_id", "perimeter"))
            for e in entities_by_id.values():
                if e.get("entity_type") == "bus":
                    e["state"]["speed_mph"] = round(e["state"].get("speed_mph", 15.0) * 1.15, 1)
                    e["state"]["delay_minutes"] = max(0.2, round(e["state"].get("delay_minutes", 3.0) * 0.6, 1))
            logs.append(f"Rerouted transit lines avoiding '{avoid}', utilizing alternate corridor '{alt}'.")

        elif action == "shift_class_schedule":
            stagger = int(param_map.get("stagger_minutes", 20))
            for e in entities_by_id.values():
                if e.get("entity_type") == "road":
                    e["state"]["congestion_index"] = max(0.15, round(e["state"].get("congestion_index", 0.5) * 0.68, 3))
                elif e.get("entity_type") == "student":
                    e["state"]["commute_time_minutes"] = max(7.0, round(e["state"].get("commute_time_minutes", 20.0) * 0.82, 1))
                    e["state"]["stress_level"] = max(0.1, round(e["state"].get("stress_level", 0.4) * 0.7, 2))
            logs.append(f"Staggered academic lecture hours by {stagger} minutes to disperse peak pedestrian traffic.")

        elif action == "host_event":
            attendance = int(param_map.get("attendance", 1200))
            for e in entities_by_id.values():
                if e.get("entity_type") == "event":
                    e["state"]["active"] = True
                    e["state"]["current_surge_factor"] = round(1.0 + (attendance / 1000.0), 2)
                elif e.get("entity_type") == "road" and ("union" in e.get("name", "").lower() or "central" in e.get("name", "").lower()):
                    e["state"]["congestion_index"] = min(0.95, round(e["state"].get("congestion_index", 0.4) * 1.6, 3))
            logs.append(f"Special event activated with expected attendance {attendance}.")

        elif action == "mass_casualty_surge":
            surge_count = int(param_map.get("surge_patient_count", 20))
            for e in entities_by_id.values():
                if e.get("entity_type") == "ward" and "ed" in e.get("id", "").lower():
                    e["state"]["occupied_beds"] = min(e["attributes"].get("capacity_beds", 40), e["state"].get("occupied_beds", 20) + surge_count)
                    e["state"]["status"] = "code_orange_surge"
                elif e.get("entity_type") == "staff":
                    e["state"]["fatigue_index"] = min(1.0, round(e["state"].get("fatigue_index", 0.3) + 0.35, 2))
                elif e.get("entity_type") == "patient":
                    e["state"]["wait_time_minutes"] = round(e["state"].get("wait_time_minutes", 15.0) * 2.2, 1)
            logs.append(f"Mass casualty surge triggered: {surge_count} acute patients routed to Emergency Department.")

        elif action == "divert_ambulances":
            divert_pct = float(param_map.get("divert_percentage", 0.5))
            for e in entities_by_id.values():
                if e.get("entity_type") == "ward" and "ed" in e.get("id", "").lower():
                    e["state"]["occupied_beds"] = max(10, int(e["state"].get("occupied_beds", 28) * (1.0 - divert_pct * 0.3)))
                elif e.get("entity_type") == "patient":
                    e["state"]["wait_time_minutes"] = max(5.0, round(e["state"].get("wait_time_minutes", 30.0) * 0.7, 1))
            logs.append(f"Ambulance divert enacted: {int(divert_pct * 100)}% incoming transports diverted.")

        elif action == "call_in_backup_staff":
            nurses = int(param_map.get("additional_nurses", 8))
            for e in entities_by_id.values():
                if e.get("entity_type") == "staff":
                    e["state"]["fatigue_index"] = max(0.15, round(e["state"].get("fatigue_index", 0.6) * 0.65, 2))
                elif e.get("entity_type") == "ward":
                    e["state"]["staff_on_duty"] = e["state"].get("staff_on_duty", 10) + (nurses // 4)
                elif e.get("entity_type") == "patient":
                    e["state"]["wait_time_minutes"] = max(4.0, round(e["state"].get("wait_time_minutes", 25.0) * 0.6, 1))
            logs.append(f"Mobilized {nurses} on-call clinical team members.")

        else:
            logs.append(f"Applied generic scenario action '{action}' with parameters {param_map}.")

        return entities_by_id, logs
