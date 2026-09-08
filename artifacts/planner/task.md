# WorldTwin AI — Implementation Plan & Progress Tracking

## Due Diligence & Preparation
- [x] Survey environment, pre-installed Python packages, and runtime constraints.
- [x] Design domain-generic relational schema, database abstraction, and migration system.
- [x] Establish architectural contracts: Verified GenAI Command Loop, simulation engine, and API boundaries.

## Phase 1: Generalized Data Model & Migrations
- [ ] Implement database abstraction layer and incremental migration runner (Alembic-style versioned migrations).
- [ ] Create initial migration files:
  - 001_initial_core_schema.sql (World, EntityType, Entity, Relationship)
  - 002_simulation_branching.sql (Scenario, SimulationBranch, SimulationState, MetricSnapshot, Anomaly, Prediction)
  - 003_interventions_and_reports.sql (Intervention, InterventionRun, Report, KnowledgeDocument)
- [ ] Implement typed domain models / ORM entities and database access layer.
- [ ] Verify database initialization and migration execution.

## Phase 2: World Meta-Model & World Generation System
- [ ] Implement World Template schema validator (JSON Schema) for entities, relationships, metrics, rules, and scenarios.
- [ ] Implement Generator Engine that parses templates and instantiates a complete digital twin world.
- [ ] Create the default Campus World Template (buildings, roads, buses, students, major events) through the generator.
- [ ] Implement GenAI-assisted World Creator (proposal step with validation and human confirmation).

## Phase 3: Generalized Simulation Engine
- [ ] Implement rule & formula registry per world type (dynamic evaluation of metrics and state transitions).
- [ ] Implement deterministic seeded simulation runner with timeline steps and state snapshots.
- [ ] Guard all aggregate computations against empty collections (zero-division defense).
- [ ] Implement anomaly detection and honestly-labeled trend-extrapolation predictions.

## Phase 4: LLM Scenario Parsing & Branching Engine
- [ ] Build scenario parser with validation against world-specific scenario vocabulary.
- [ ] Implement true branch chaining: branch from parent branch terminal snapshot state.
- [ ] Store full time-series snapshots for scrubbing/playback.

## Phase 5: GenAI Command Layer & Verification Loop
- [ ] Implement Planner with strict Tool Schema allowlist (`run_scenario`, `get_branch_metrics`, `list_branches`, `evaluate_interventions`, `explain_branch`, `search_knowledge`, `generate_report`, `create_world`).
- [ ] Implement Pre-Execution Validation Layer (argument typing, entity/branch ID validation).
- [ ] Implement Service Layer execution (LLM never executes raw SQL).
- [ ] Implement Independent Verification Layer (re-queries database and verifies state changes).
- [ ] Implement Bounded Retry / Replan and Evidence-Backed Response generation.

## Phase 6: Knowledge Base / RAG Engine
- [ ] Implement RAG document store and search (TF-IDF / vector scoring per world).
- [ ] Wire knowledge retrieval directly into Copilot planning loop with cited evidence.

## Phase 7: Counterfactual Interventions System
- [ ] Implement Intervention Playbook generator per world.
- [ ] Implement actual counterfactual branch execution and outcome-based scoring.
- [ ] Implement multi-objective weighting (benefit, safety, cost, complexity) wired to ranking.

## Phase 8: Full-Stack Web Application (FastAPI + React/TypeScript)
- [ ] Build FastAPI REST API endpoints:
  - Worlds CRUD & Generation
  - Scenarios & Branching
  - Simulation Runs & Snapshots
  - Interventions & Scoring
  - Copilot Command Loop
  - Knowledge & Reports
  - Auth & Health status
- [ ] Build React + TypeScript frontend architecture (`frontend/`):
  - Types, API client, hooks, routes, views (Living World, Scenario Studio, Future Branches, Experiment Lab, AI Copilot, Intervention Lab, Knowledge Graph, Research Reports).
  - World switcher, timeline scrubber, batch runner.
  - Dark data-dense UI styling.
- [ ] Serve static/production web app from FastAPI.

## Phase 9: Testing & Verification
- [ ] Write unit tests for all services.
- [ ] Write integration test for scenario -> branch -> simulate -> verify pipeline.
- [ ] Write adversarial tests proving copilot never fabricates data and refuses out-of-scope calls.
- [ ] Run test suite and confirm 100% pass rate.

## Phase 10: Second World Demonstration (Hospital Digital Twin)
- [ ] Create complete Hospital World Template (wards, triage, staff, beds, surgeries, ambulances) via world generator without altering engine code.
- [ ] Run simulation, scenarios, and copilot queries on the Hospital world.
