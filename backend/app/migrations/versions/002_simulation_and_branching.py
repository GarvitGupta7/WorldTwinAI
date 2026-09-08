"""
Migration 002: Simulation and Branching
Creates tables for Scenarios, SimulationBranches, SimulationStates,
MetricSnapshots, SimulationEvents, Anomalies, and Predictions.
Keyed by world_id and branch_id.
"""

from backend.app.database import Database

def upgrade(db: Database):
    script = """
    CREATE TABLE IF NOT EXISTS scenarios (
        id TEXT PRIMARY KEY,
        world_id TEXT NOT NULL,
        original_text TEXT NOT NULL,
        action TEXT NOT NULL,
        parameters TEXT NOT NULL,      -- JSON list of parameters
        assumptions TEXT NOT NULL,     -- JSON list of assumptions
        ambiguities TEXT NOT NULL,     -- JSON list of ambiguities
        valid INTEGER NOT NULL DEFAULT 1,
        parser_metadata TEXT NOT NULL, -- JSON parser telemetry (confidence, reasoning, world_vocabulary_match)
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (world_id) REFERENCES worlds(id) ON DELETE CASCADE
    );

    CREATE INDEX IF NOT EXISTS idx_scenarios_world ON scenarios(world_id);

    CREATE TABLE IF NOT EXISTS simulation_branches (
        id TEXT PRIMARY KEY,
        world_id TEXT NOT NULL,
        parent_branch_id TEXT,         -- Nullable; if specified, chains from parent's terminal state
        scenario_id TEXT,              -- Nullable (e.g. baseline branch has no scenario)
        branch_type TEXT NOT NULL,     -- 'baseline', 'what_if', 'counterfactual', 'intervention'
        name TEXT NOT NULL,
        seed INTEGER NOT NULL DEFAULT 42,
        duration INTEGER NOT NULL DEFAULT 60, -- steps
        status TEXT NOT NULL DEFAULT 'pending', -- 'pending', 'running', 'completed', 'failed'
        initial_state_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP,
        FOREIGN KEY (world_id) REFERENCES worlds(id) ON DELETE CASCADE,
        FOREIGN KEY (parent_branch_id) REFERENCES simulation_branches(id) ON DELETE SET NULL,
        FOREIGN KEY (scenario_id) REFERENCES scenarios(id) ON DELETE SET NULL
    );

    CREATE INDEX IF NOT EXISTS idx_branches_world ON simulation_branches(world_id);
    CREATE INDEX IF NOT EXISTS idx_branches_parent ON simulation_branches(parent_branch_id);

    CREATE TABLE IF NOT EXISTS simulation_states (
        id TEXT PRIMARY KEY,
        branch_id TEXT NOT NULL,
        world_id TEXT NOT NULL,
        step INTEGER NOT NULL,
        timestamp TEXT NOT NULL,
        state_snapshot TEXT NOT NULL,  -- Full JSON representation of entities at step
        state_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (branch_id) REFERENCES simulation_branches(id) ON DELETE CASCADE,
        FOREIGN KEY (world_id) REFERENCES worlds(id) ON DELETE CASCADE
    );

    CREATE INDEX IF NOT EXISTS idx_states_branch_step ON simulation_states(branch_id, step);

    CREATE TABLE IF NOT EXISTS metric_snapshots (
        id TEXT PRIMARY KEY,
        branch_id TEXT NOT NULL,
        world_id TEXT NOT NULL,
        step INTEGER NOT NULL,
        timestamp TEXT NOT NULL,
        metrics TEXT NOT NULL,         -- JSON map of metric name -> value
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (branch_id) REFERENCES simulation_branches(id) ON DELETE CASCADE,
        FOREIGN KEY (world_id) REFERENCES worlds(id) ON DELETE CASCADE
    );

    CREATE INDEX IF NOT EXISTS idx_metrics_branch_step ON metric_snapshots(branch_id, step);

    CREATE TABLE IF NOT EXISTS simulation_events (
        id TEXT PRIMARY KEY,
        branch_id TEXT NOT NULL,
        world_id TEXT NOT NULL,
        step INTEGER NOT NULL,
        timestamp TEXT NOT NULL,
        event_type TEXT NOT NULL,
        description TEXT NOT NULL,
        details TEXT NOT NULL,         -- JSON
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (branch_id) REFERENCES simulation_branches(id) ON DELETE CASCADE,
        FOREIGN KEY (world_id) REFERENCES worlds(id) ON DELETE CASCADE
    );

    CREATE INDEX IF NOT EXISTS idx_events_branch ON simulation_events(branch_id);

    CREATE TABLE IF NOT EXISTS anomalies (
        id TEXT PRIMARY KEY,
        branch_id TEXT NOT NULL,
        world_id TEXT NOT NULL,
        step INTEGER NOT NULL,
        metric_name TEXT NOT NULL,
        severity TEXT NOT NULL,        -- 'info', 'warning', 'critical'
        threshold REAL NOT NULL,
        actual_value REAL NOT NULL,
        description TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (branch_id) REFERENCES simulation_branches(id) ON DELETE CASCADE,
        FOREIGN KEY (world_id) REFERENCES worlds(id) ON DELETE CASCADE
    );

    CREATE INDEX IF NOT EXISTS idx_anomalies_branch ON anomalies(branch_id);

    CREATE TABLE IF NOT EXISTS predictions (
        id TEXT PRIMARY KEY,
        branch_id TEXT NOT NULL,
        world_id TEXT NOT NULL,
        target_metric TEXT NOT NULL,
        horizon_steps INTEGER NOT NULL,
        predicted_values TEXT NOT NULL, -- JSON list of projected step values
        confidence REAL NOT NULL,
        method TEXT NOT NULL,           -- e.g., 'trend_extrapolation_linear_exponential'
        limitations TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (branch_id) REFERENCES simulation_branches(id) ON DELETE CASCADE,
        FOREIGN KEY (world_id) REFERENCES worlds(id) ON DELETE CASCADE
    );

    CREATE INDEX IF NOT EXISTS idx_predictions_branch ON predictions(branch_id);
    """
    db.executescript(script)

def downgrade(db: Database):
    script = """
    DROP TABLE IF EXISTS predictions;
    DROP TABLE IF EXISTS anomalies;
    DROP TABLE IF EXISTS simulation_events;
    DROP TABLE IF EXISTS metric_snapshots;
    DROP TABLE IF EXISTS simulation_states;
    DROP TABLE IF EXISTS simulation_branches;
    DROP TABLE IF EXISTS scenarios;
    """
    db.executescript(script)
