"""
Migration 003: Interventions, Knowledge Base, Reports, and Copilot Sessions
Creates tables for Interventions, InterventionRuns, KnowledgeDocuments,
Reports, and CopilotSessions.
Keyed by world_id and branch_id.
"""

from backend.app.database import Database

def upgrade(db: Database):
    script = """
    CREATE TABLE IF NOT EXISTS interventions (
        id TEXT PRIMARY KEY,
        world_id TEXT NOT NULL,
        name TEXT NOT NULL,
        description TEXT NOT NULL,
        scenario_action TEXT NOT NULL,
        parameters TEXT NOT NULL,       -- JSON list
        cost REAL NOT NULL DEFAULT 1.0, -- normalized 1-10
        complexity REAL NOT NULL DEFAULT 1.0, -- normalized 1-10
        expected_benefit REAL NOT NULL DEFAULT 1.0, -- normalized 1-10
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (world_id) REFERENCES worlds(id) ON DELETE CASCADE
    );

    CREATE INDEX IF NOT EXISTS idx_interventions_world ON interventions(world_id);

    CREATE TABLE IF NOT EXISTS intervention_runs (
        id TEXT PRIMARY KEY,
        world_id TEXT NOT NULL,
        intervention_id TEXT NOT NULL,
        baseline_branch_id TEXT NOT NULL,
        counterfactual_branch_id TEXT NOT NULL,
        outcome_metrics TEXT NOT NULL,   -- JSON diff & final metrics
        score REAL NOT NULL,             -- Combined multi-objective score
        weights_used TEXT NOT NULL,      -- JSON weights {benefit, safety, cost, complexity}
        ranking INTEGER,
        status TEXT NOT NULL DEFAULT 'completed',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (world_id) REFERENCES worlds(id) ON DELETE CASCADE,
        FOREIGN KEY (intervention_id) REFERENCES interventions(id) ON DELETE CASCADE,
        FOREIGN KEY (baseline_branch_id) REFERENCES simulation_branches(id) ON DELETE CASCADE,
        FOREIGN KEY (counterfactual_branch_id) REFERENCES simulation_branches(id) ON DELETE CASCADE
    );

    CREATE INDEX IF NOT EXISTS idx_intruns_world ON intervention_runs(world_id);
    CREATE INDEX IF NOT EXISTS idx_intruns_base ON intervention_runs(baseline_branch_id);

    CREATE TABLE IF NOT EXISTS knowledge_documents (
        id TEXT PRIMARY KEY,
        world_id TEXT NOT NULL,
        title TEXT NOT NULL,
        category TEXT NOT NULL,
        content TEXT NOT NULL,
        metadata TEXT NOT NULL,          -- JSON
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (world_id) REFERENCES worlds(id) ON DELETE CASCADE
    );

    CREATE INDEX IF NOT EXISTS idx_knowledge_world ON knowledge_documents(world_id);

    CREATE TABLE IF NOT EXISTS reports (
        id TEXT PRIMARY KEY,
        world_id TEXT NOT NULL,
        branch_id TEXT NOT NULL,
        title TEXT NOT NULL,
        format TEXT NOT NULL DEFAULT 'markdown',
        content TEXT NOT NULL,
        summary TEXT NOT NULL,
        metadata TEXT NOT NULL,          -- JSON (metrics summary, anomaly counts, etc.)
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (world_id) REFERENCES worlds(id) ON DELETE CASCADE,
        FOREIGN KEY (branch_id) REFERENCES simulation_branches(id) ON DELETE CASCADE
    );

    CREATE INDEX IF NOT EXISTS idx_reports_world ON reports(world_id);
    CREATE INDEX IF NOT EXISTS idx_reports_branch ON reports(branch_id);

    CREATE TABLE IF NOT EXISTS copilot_sessions (
        id TEXT PRIMARY KEY,
        world_id TEXT NOT NULL,
        current_branch_id TEXT,
        messages TEXT NOT NULL DEFAULT '[]', -- JSON serialized list of turns with verification evidence
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (world_id) REFERENCES worlds(id) ON DELETE CASCADE,
        FOREIGN KEY (current_branch_id) REFERENCES simulation_branches(id) ON DELETE SET NULL
    );

    CREATE INDEX IF NOT EXISTS idx_copilot_world ON copilot_sessions(world_id);
    """
    db.executescript(script)

def downgrade(db: Database):
    script = """
    DROP TABLE IF EXISTS copilot_sessions;
    DROP TABLE IF EXISTS reports;
    DROP TABLE IF EXISTS knowledge_documents;
    DROP TABLE IF EXISTS intervention_runs;
    DROP TABLE IF EXISTS interventions;
    """
    db.executescript(script)
