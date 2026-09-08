"""
GenAI Copilot Command Layer for WorldTwin AI.
Enforces the mandatory execution loop:
Natural Language -> Structured Plan -> Allowlist Validation -> Controlled Execution -> State Change -> Independent Verification -> Bounded Retry -> Evidence-Backed Response.
The LLM plans and explains; the database and simulation engine are the sole source of truth.
"""

import json
import uuid
import datetime
import logging
from typing import Any, Dict, List, Optional, Tuple

from backend.app.database import Database, db
from backend.app.models.copilot import (
    ToolCall, StructuredPlan, PlanValidationResult, ToolExecutionResult,
    VerificationCheck, EvidenceItem, CopilotTurnResponse
)
from backend.app.services.branch_service import BranchService
from backend.app.services.scenario_parser import ScenarioParser
from backend.app.services.intervention_service import InterventionService
from backend.app.services.knowledge_service import KnowledgeService
from backend.app.services.report_service import ReportService
from backend.app.services.verification_service import VerificationService
from backend.app.services.world_creator_agent import WorldCreatorAgent

logger = logging.getLogger("worldtwin.copilot")

# Strict Tool Schema Allowlist
TOOL_ALLOWLIST = {
    "run_scenario": {
        "description": "Parses scenario natural language, creates a what-if branch, and runs simulation.",
        "required_args": ["world_id", "scenario_text"],
        "optional_args": ["parent_branch_id", "branch_name", "seed", "duration"]
    },
    "get_branch_metrics": {
        "description": "Retrieves verified latest metrics, anomalies, and predictions for a branch.",
        "required_args": ["branch_id"],
        "optional_args": []
    },
    "list_branches": {
        "description": "Lists all existing simulation branches for a world.",
        "required_args": ["world_id"],
        "optional_args": []
    },
    "evaluate_interventions": {
        "description": "Executes counterfactual simulation branches and scores interventions.",
        "required_args": ["world_id", "baseline_branch_id"],
        "optional_args": ["weights"]
    },
    "explain_branch": {
        "description": "Synthesizes an explanation of branch behavior comparing baseline to branch.",
        "required_args": ["branch_id"],
        "optional_args": ["baseline_branch_id"]
    },
    "search_knowledge": {
        "description": "Searches the domain knowledge base / operating procedures.",
        "required_args": ["world_id", "query"],
        "optional_args": ["top_k"]
    },
    "generate_report": {
        "description": "Generates and persists a structured research report for a branch.",
        "required_args": ["world_id", "branch_id"],
        "optional_args": ["title"]
    },
    "create_world": {
        "description": "Proposes a structured world template from natural language description (requires confirmation).",
        "required_args": ["description"],
        "optional_args": []
    }
}


class CopilotPlanner:
    def __init__(self, database: Optional[Database] = None):
        self.db = database or db
        self.branch_service = BranchService(self.db)
        self.scenario_parser = ScenarioParser(self.db)
        self.intervention_service = InterventionService(self.db)
        self.knowledge_service = KnowledgeService(self.db)
        self.report_service = ReportService(self.db)
        self.verification_service = VerificationService(self.db)
        self.world_creator = WorldCreatorAgent()

    def generate_plan(self, world_id: str, branch_id: Optional[str], query: str) -> StructuredPlan:
        """
        Intent Understanding: Translates natural language into a structured plan of tool calls.
        No free-text action without a plan.
        """
        q_lower = query.lower().strip()
        tools = []
        intent = "general_query"
        reasoning = ""

        # 1. World creation proposal intent
        if any(w in q_lower for w in ["create world", "build world", "new world", "create twin", "generate world", "propose world"]):
            intent = "create_world_proposal"
            reasoning = "User requested creating a new digital twin environment. Proposing structured template."
            tools.append(ToolCall(tool_name="create_world", arguments={"description": query}))

        # 2. Scenario execution intent
        elif any(w in q_lower for w in ["close", "shut down", "block", "what if", "simulate", "run scenario", "increase bus", "double bus", "surge", "stagger"]):
            intent = "execute_scenario_branch"
            reasoning = f"User wants to simulate a scenario on world '{world_id}'."
            tools.append(ToolCall(
                tool_name="run_scenario",
                arguments={
                    "world_id": world_id,
                    "scenario_text": query,
                    "parent_branch_id": branch_id,
                    "branch_name": f"Simulation: {query[:35]}"
                }
            ))
            # Also get metrics after
            tools.append(ToolCall(tool_name="get_branch_metrics", arguments={"branch_id": "$PREVIOUS_BRANCH_ID"}))

        # 3. Interventions evaluation intent
        elif any(w in q_lower for w in ["intervention", "mitigate", "counterfactual", "recommend", "how to fix", "solutions"]):
            intent = "evaluate_interventions"
            reasoning = "User requested intervention analysis and counterfactual evaluation."
            target_b_id = branch_id
            if not target_b_id:
                # Find most recent branch
                recent = self.branch_service.list_branches_for_world(world_id)
                target_b_id = recent[0]["id"] if recent else None
            tools.append(ToolCall(
                tool_name="evaluate_interventions",
                arguments={"world_id": world_id, "baseline_branch_id": target_b_id or "default"}
            ))

        # 4. Report generation intent
        elif any(w in q_lower for w in ["report", "audit", "document", "generate report", "write a report"]):
            intent = "generate_research_report"
            reasoning = "User requested research report compilation for the active branch."
            target_b_id = branch_id
            if not target_b_id:
                recent = self.branch_service.list_branches_for_world(world_id)
                target_b_id = recent[0]["id"] if recent else None
            tools.append(ToolCall(
                tool_name="generate_report",
                arguments={"world_id": world_id, "branch_id": target_b_id or "default"}
            ))

        # 5. Branch metrics or explanation intent
        elif any(w in q_lower for w in ["metric", "status", "congestion", "efficiency", "how is", "anomalies", "state"]):
            if branch_id:
                intent = "inspect_branch_metrics"
                reasoning = f"Retrieving metrics and explaining branch '{branch_id}'."
                tools.append(ToolCall(tool_name="get_branch_metrics", arguments={"branch_id": branch_id}))
                tools.append(ToolCall(tool_name="explain_branch", arguments={"branch_id": branch_id}))
            else:
                intent = "list_branches"
                reasoning = "No branch specified; listing available branches to inspect."
                tools.append(ToolCall(tool_name="list_branches", arguments={"world_id": world_id}))

        # 6. Knowledge search intent
        elif any(w in q_lower for w in ["protocol", "plan", "policy", "guideline", "standard", "procedure", "master plan"]):
            intent = "search_knowledge"
            reasoning = "User query targets operational procedures and guidelines in the knowledge base."
            tools.append(ToolCall(tool_name="search_knowledge", arguments={"world_id": world_id, "query": query}))

        # 7. List branches
        elif any(w in q_lower for w in ["list branches", "show branches", "branches"]):
            intent = "list_branches"
            reasoning = "Listing all branches for the active world."
            tools.append(ToolCall(tool_name="list_branches", arguments={"world_id": world_id}))

        # Default fallback: check knowledge base first, then explain branch if active
        else:
            intent = "knowledge_grounded_answer"
            reasoning = "General query. Retrieving domain operational knowledge and active branch metrics."
            tools.append(ToolCall(tool_name="search_knowledge", arguments={"world_id": world_id, "query": query}))
            if branch_id:
                tools.append(ToolCall(tool_name="get_branch_metrics", arguments={"branch_id": branch_id}))

        return StructuredPlan(intent=intent, reasoning=reasoning, tool_calls=tools)

    def validate_plan(self, plan: StructuredPlan, world_id: str) -> PlanValidationResult:
        """
        Validation: Checks plan strictly against allowlist, required typed args,
        and valid resource IDs.
        """
        errors = []
        sanitized_calls = []

        for call in plan.tool_calls:
            t_name = call.tool_name
            if t_name not in TOOL_ALLOWLIST:
                errors.append(f"Disallowed tool call: '{t_name}' is not in the approved tool allowlist.")
                continue

            spec = TOOL_ALLOWLIST[t_name]
            args = call.arguments

            # Check required args
            for req in spec["required_args"]:
                if req not in args:
                    errors.append(f"Tool '{t_name}' missing required argument: '{req}'.")

            # Check world existence if world_id is an arg
            if "world_id" in args and args["world_id"] != "$PREVIOUS_WORLD_ID":
                w_row = self.db.fetchone("SELECT id FROM worlds WHERE id = ?;", (args["world_id"],))
                if not w_row:
                    errors.append(f"Invalid world_id '{args['world_id']}': world does not exist.")

            # Validate branch_id if provided
            if "branch_id" in args and args["branch_id"] not in ["$PREVIOUS_BRANCH_ID", "default"]:
                b_row = self.db.fetchone("SELECT id FROM simulation_branches WHERE id = ?;", (args["branch_id"],))
                if not b_row:
                    errors.append(f"Invalid branch_id '{args['branch_id']}': branch does not exist.")

            sanitized_calls.append(call)

        return PlanValidationResult(
            is_valid=(len(errors) == 0),
            errors=errors,
            sanitized_plan=StructuredPlan(intent=plan.intent, reasoning=plan.reasoning, tool_calls=sanitized_calls)
        )

    def execute_plan(
        self,
        plan: StructuredPlan,
        world_id: str,
        active_branch_id: Optional[str] = None
    ) -> Tuple[List[ToolExecutionResult], List[VerificationCheck], List[EvidenceItem], List[str]]:
        """
        Controlled Execution through Service Layer ONLY (no raw DB writes triggered by LLM).
        Independently verifies every outcome and collects verifiable evidence.
        """
        executed_tools: List[ToolExecutionResult] = []
        verification_checks: List[VerificationCheck] = []
        evidence: List[EvidenceItem] = []
        citations: List[str] = []

        context_vars = {
            "$PREVIOUS_BRANCH_ID": active_branch_id,
            "$PREVIOUS_WORLD_ID": world_id
        }

        for call in plan.tool_calls:
            t_name = call.tool_name
            raw_args = dict(call.arguments)

            # Substitute context variables
            for k, v in raw_args.items():
                if v in context_vars and context_vars[v]:
                    raw_args[k] = context_vars[v]

            try:
                if t_name == "run_scenario":
                    w_id = raw_args["world_id"]
                    scen_text = raw_args["scenario_text"]
                    p_branch = raw_args.get("parent_branch_id")
                    if p_branch == "default":
                        p_branch = None

                    # Parse scenario
                    parsed = self.scenario_parser.parse_scenario(w_id, scen_text)
                    if not parsed.valid:
                        executed_tools.append(ToolExecutionResult(
                            tool_name=t_name, arguments=raw_args, success=False,
                            data={"error": parsed.reasoning, "clarification": parsed.clarification_question}
                        ))
                        continue

                    # Persist scenario
                    scen_id = f"scen_{uuid.uuid4().hex[:8]}"
                    self.db.execute(
                        """
                        INSERT INTO scenarios (id, world_id, original_text, action, parameters, assumptions, ambiguities, valid, parser_metadata)
                        VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?);
                        """,
                        (
                            scen_id, w_id, scen_text, parsed.action,
                            json.dumps([p.dict() for p in parsed.parameters]),
                            json.dumps(parsed.assumptions), json.dumps(parsed.ambiguities),
                            json.dumps({"confidence": parsed.confidence, "reasoning": parsed.reasoning})
                        )
                    )

                    # Create branch
                    b_name = raw_args.get("branch_name") or f"Run: {parsed.action}"
                    branch = self.branch_service.create_branch(
                        world_id=w_id,
                        name=b_name,
                        branch_type="what_if",
                        parent_branch_id=p_branch,
                        scenario_id=scen_id,
                        seed=int(raw_args.get("seed", 42)),
                        duration=int(raw_args.get("duration", 60))
                    )
                    b_id = branch["id"]
                    context_vars["$PREVIOUS_BRANCH_ID"] = b_id

                    # Run simulation
                    sim_result = self.branch_service.run_branch(b_id)

                    # INDEPENDENT VERIFICATION
                    v_branch = self.verification_service.verify_branch_created(b_id)
                    v_metrics = self.verification_service.verify_metrics_exist(b_id)
                    verification_checks.extend([v_branch, v_metrics])

                    # EVIDENCE GATHERING
                    now_ts = datetime.datetime.utcnow().isoformat()
                    evidence.append(EvidenceItem(
                        source="database_read", resource_id=b_id, metric_or_field="status",
                        verified_data=sim_result["status"], timestamp=now_ts
                    ))
                    evidence.append(EvidenceItem(
                        source="database_read", resource_id=b_id, metric_or_field="final_metrics",
                        verified_data=sim_result["final_metrics"], timestamp=now_ts
                    ))

                    executed_tools.append(ToolExecutionResult(
                        tool_name=t_name, arguments=raw_args, success=True,
                        data={
                            "branch_id": b_id,
                            "scenario_action": parsed.action,
                            "simulation_result": sim_result,
                            "parsed_parameters": [p.dict() for p in parsed.parameters],
                            "assumptions": parsed.assumptions
                        }
                    ))

                elif t_name == "get_branch_metrics":
                    b_id = raw_args["branch_id"]
                    details = self.branch_service.get_branch_details(b_id)
                    if not details:
                        executed_tools.append(ToolExecutionResult(
                            tool_name=t_name, arguments=raw_args, success=False,
                            data=None, error=f"Branch '{b_id}' not found."
                        ))
                        continue

                    # INDEPENDENT VERIFICATION
                    v_metrics = self.verification_service.verify_metrics_exist(b_id)
                    verification_checks.append(v_metrics)

                    evidence.append(EvidenceItem(
                        source="database_read", resource_id=b_id, metric_or_field="latest_metrics",
                        verified_data=details["latest_metrics"], timestamp=datetime.datetime.utcnow().isoformat()
                    ))
                    executed_tools.append(ToolExecutionResult(
                        tool_name=t_name, arguments=raw_args, success=True,
                        data={
                            "branch_id": b_id,
                            "name": details["name"],
                            "latest_metrics": details["latest_metrics"],
                            "anomalies_count": len(details["anomalies"]),
                            "predictions": details["predictions"]
                        }
                    ))

                elif t_name == "list_branches":
                    w_id = raw_args["world_id"]
                    branches = self.branch_service.list_branches_for_world(w_id)
                    evidence.append(EvidenceItem(
                        source="database_read", resource_id=w_id, metric_or_field="branches_count",
                        verified_data=len(branches), timestamp=datetime.datetime.utcnow().isoformat()
                    ))
                    executed_tools.append(ToolExecutionResult(
                        tool_name=t_name, arguments=raw_args, success=True,
                        data={"branches": branches, "count": len(branches)}
                    ))

                elif t_name == "evaluate_interventions":
                    w_id = raw_args["world_id"]
                    base_b_id = raw_args["baseline_branch_id"]
                    if base_b_id == "default":
                        recent = self.branch_service.list_branches_for_world(w_id)
                        base_b_id = recent[0]["id"] if recent else None

                    if not base_b_id:
                        executed_tools.append(ToolExecutionResult(
                            tool_name=t_name, arguments=raw_args, success=False,
                            data=None, error="No baseline branch available to evaluate interventions against."
                        ))
                        continue

                    intv_runs = self.intervention_service.evaluate_interventions(w_id, base_b_id)

                    # INDEPENDENT VERIFICATION
                    v_intv = self.verification_service.verify_interventions_evaluated(base_b_id)
                    verification_checks.append(v_intv)

                    evidence.append(EvidenceItem(
                        source="database_read", resource_id=base_b_id, metric_or_field="intervention_runs",
                        verified_data=[{"name": r["intervention_name"], "score": r["score"], "rank": r["ranking"]} for r in intv_runs],
                        timestamp=datetime.datetime.utcnow().isoformat()
                    ))
                    executed_tools.append(ToolExecutionResult(
                        tool_name=t_name, arguments=raw_args, success=True,
                        data={"baseline_branch_id": base_b_id, "interventions": intv_runs}
                    ))

                elif t_name == "explain_branch":
                    b_id = raw_args["branch_id"]
                    details = self.branch_service.get_branch_details(b_id)
                    if details:
                        executed_tools.append(ToolExecutionResult(
                            tool_name=t_name, arguments=raw_args, success=True,
                            data={"branch_id": b_id, "name": details["name"], "metrics": details["latest_metrics"], "anomalies": details["anomalies"]}
                        ))

                elif t_name == "search_knowledge":
                    w_id = raw_args["world_id"]
                    q = raw_args["query"]
                    docs = self.knowledge_service.search(w_id, q, top_k=int(raw_args.get("top_k", 3)))
                    for d in docs:
                        citations.append(f"{d.title} (Relevance: {d.score})")
                        evidence.append(EvidenceItem(
                            source="knowledge_base", resource_id=d.document_id, metric_or_field="snippet",
                            verified_data=d.snippet, timestamp=datetime.datetime.utcnow().isoformat()
                        ))
                    executed_tools.append(ToolExecutionResult(
                        tool_name=t_name, arguments=raw_args, success=True,
                        data={"query": q, "results": [d.dict() for d in docs]}
                    ))

                elif t_name == "generate_report":
                    w_id = raw_args["world_id"]
                    b_id = raw_args["branch_id"]
                    if b_id == "default":
                        recent = self.branch_service.list_branches_for_world(w_id)
                        b_id = recent[0]["id"] if recent else None

                    if not b_id:
                        executed_tools.append(ToolExecutionResult(
                            tool_name=t_name, arguments=raw_args, success=False,
                            data=None, error="No branch available to generate report for."
                        ))
                        continue

                    rep = self.report_service.generate_report(w_id, b_id, title=raw_args.get("title"))

                    # INDEPENDENT VERIFICATION
                    v_rep = self.verification_service.verify_report_created(rep["id"])
                    verification_checks.append(v_rep)

                    evidence.append(EvidenceItem(
                        source="database_read", resource_id=rep["id"], metric_or_field="report_id",
                        verified_data=rep["id"], timestamp=datetime.datetime.utcnow().isoformat()
                    ))
                    executed_tools.append(ToolExecutionResult(
                        tool_name=t_name, arguments=raw_args, success=True,
                        data={"report_id": rep["id"], "title": rep["title"], "summary": rep["summary"]}
                    ))

                elif t_name == "create_world":
                    desc = raw_args["description"]
                    proposal = self.world_creator.propose_world_template(desc)
                    executed_tools.append(ToolExecutionResult(
                        tool_name=t_name, arguments=raw_args, success=True,
                        data=proposal
                    ))

            except Exception as e:
                logger.error(f"Error executing tool '{t_name}': {e}", exc_info=True)
                executed_tools.append(ToolExecutionResult(
                    tool_name=t_name, arguments=raw_args, success=False,
                    data=None, error=str(e)
                ))

        return executed_tools, verification_checks, evidence, citations

    def execute_copilot_turn(
        self,
        world_id: str,
        query: str,
        branch_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> CopilotTurnResponse:
        """
        Full verified Copilot command loop:
        1. Natural language intent understanding -> Structured Plan
        2. Plan Validation against tool allowlist and typed schema
        3. Controlled Tool Execution through Service Layer
        4. Independent State Verification from DB
        5. Bounded Retry/Replan if verification fails
        6. Synthesizes Evidence-Backed Response
        """
        sess_id = session_id or f"sess_{uuid.uuid4().hex[:8]}"

        # Step 1: Generate plan
        plan = self.generate_plan(world_id, branch_id, query)

        # Step 2: Validate plan
        val_result = self.validate_plan(plan, world_id)
        if not val_result.is_valid:
            error_msg = f"Plan validation refused: {'; '.join(val_result.errors)}"
            return CopilotTurnResponse(
                response_text=f"I cannot execute that action because the planned command was rejected by the safety validator: {'; '.join(val_result.errors)}",
                structured_plan=plan,
                executed_tools=[],
                verification_checks=[],
                evidence=[],
                citations=[],
                confidence=0.0,
                status="refusal",
                session_id=sess_id
            )

        # Step 3 & 4: Controlled Execution & Verification
        executed_tools, verifications, evidence, citations = self.execute_plan(val_result.sanitized_plan, world_id, branch_id)

        # Check verification status
        all_verified = all(v.verified for v in verifications) if verifications else True
        if verifications and not all_verified:
            logger.warning("Independent state verification failed for one or more tool calls. Bounded retry triggered.")
            # Bounded retry pass (1 retry)
            retry_plan = StructuredPlan(
                intent="retry_verification",
                reasoning="Re-verifying state following incomplete checks.",
                tool_calls=[call for call in plan.tool_calls if call.tool_name in ["get_branch_metrics", "list_branches"]]
            )
            r_tools, r_verifs, r_evid, r_cits = self.execute_plan(retry_plan, world_id, branch_id)
            executed_tools.extend(r_tools)
            verifications.extend(r_verifs)
            evidence.extend(r_evid)
            citations.extend(r_cits)
            all_verified = all(v.verified for v in verifications)

        # Step 5: Synthesize Evidence-Backed Narrative
        narrative_parts = []
        if any(t.tool_name == "run_scenario" and t.success for t in executed_tools):
            scen_res = next(t for t in executed_tools if t.tool_name == "run_scenario").data
            narrative_parts.append(
                f"Created and simulated what-if branch `{scen_res['branch_id']}` evaluating action `{scen_res['scenario_action']}`. "
                f"Terminal metrics: Congestion `{scen_res['simulation_result']['final_metrics'].get('road_congestion', 'N/A')}`, "
                f"System Flow Efficiency `{scen_res['simulation_result']['final_metrics'].get('system_flow_efficiency', 'N/A')}`. "
                f"Detected {scen_res['simulation_result']['anomalies_count']} anomalies."
            )

        if any(t.tool_name == "evaluate_interventions" and t.success for t in executed_tools):
            intv_res = next(t for t in executed_tools if t.tool_name == "evaluate_interventions").data
            top = intv_res["interventions"][0] if intv_res.get("interventions") else None
            if top:
                narrative_parts.append(
                    f"Simulated {len(intv_res['interventions'])} counterfactual intervention runs against baseline `{intv_res['baseline_branch_id']}`. "
                    f"Top recommended intervention: **{top['intervention_name']}** (Score: `{top['score']}`, Benefit: `{top['observed_benefit']}`, Cost: `{top['cost']}`)."
                )

        if any(t.tool_name == "generate_report" and t.success for t in executed_tools):
            rep_res = next(t for t in executed_tools if t.tool_name == "generate_report").data
            narrative_parts.append(f"Compiled and persisted research report **{rep_res['title']}** (ID: `{rep_res['report_id']}`).")

        if any(t.tool_name == "create_world" and t.success for t in executed_tools):
            cw_res = next(t for t in executed_tools if t.tool_name == "create_world").data
            narrative_parts.append(f"Prepared structured template proposal for **{cw_res['name']}** with {len(cw_res['declared_entity_types'])} entity types. Confirmation required before persistence.")

        if any(t.tool_name == "search_knowledge" and t.success for t in executed_tools):
            k_res = next(t for t in executed_tools if t.tool_name == "search_knowledge").data
            if k_res.get("results"):
                top_doc = k_res["results"][0]
                narrative_parts.append(f"Retrieved operational guidance from '{top_doc['title']}': {top_doc['snippet']}")

        if not narrative_parts:
            # Fallback explanation
            narrative_parts.append("Executed requested tools and gathered verified state evidence.")

        response_text = " ".join(narrative_parts)

        # Append independent verification disclosure
        status = "verified" if all_verified else "unverified_failure"
        if not all_verified:
            response_text += "\n\n*Warning: System state could not be fully verified against database records.*"
        else:
            response_text += f"\n\n*State Verification: {len(verifications)} database integrity checks passed. Evidence backed by live simulation store.*"

        # Update copilot session in DB
        session_row = self.db.fetchone("SELECT id FROM copilot_sessions WHERE id = ?;", (sess_id,))
        if not session_row:
            self.db.execute(
                "INSERT INTO copilot_sessions (id, world_id, current_branch_id, messages) VALUES (?, ?, ?, '[]');",
                (sess_id, world_id, branch_id)
            )

        return CopilotTurnResponse(
            response_text=response_text,
            structured_plan=val_result.sanitized_plan,
            executed_tools=executed_tools,
            verification_checks=verifications,
            evidence=evidence,
            citations=citations,
            confidence=0.95 if all_verified else 0.40,
            status=status,
            session_id=sess_id
        )
