"""
Migration 001: Core World Metamodel
Creates tables for World, EntityType Registry, Entity, and Relationship.
Domain-generic, keyed by world_id.
"""

from backend.app.database import Database

def upgrade(db: Database):
    script = """
    CREATE TABLE IF NOT EXISTS worlds (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        world_type TEXT NOT NULL,
        description TEXT,
        schema_definition TEXT NOT NULL, -- JSON template/spec defining entity types, metrics, rules
        current_timestamp TEXT NOT NULL DEFAULT (DATETIME('now')),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS entity_types (
        world_id TEXT NOT NULL,
        name TEXT NOT NULL,
        display_name TEXT NOT NULL,
        schema_definition TEXT NOT NULL, -- JSON Schema for entity state & attributes
        rules_definition TEXT NOT NULL,  -- JSON references to simulation rules
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (world_id, name),
        FOREIGN KEY (world_id) REFERENCES worlds(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS entities (
        id TEXT PRIMARY KEY,
        world_id TEXT NOT NULL,
        entity_type TEXT NOT NULL,
        name TEXT NOT NULL,
        position TEXT NOT NULL,       -- JSON: coordinates {x, y}, optional {geo: {lat, lng}}, optional {topology: {node, edge, level}}
        state TEXT NOT NULL,          -- JSON: dynamic state variables
        attributes TEXT NOT NULL,     -- JSON: static/semi-static properties
        relationships TEXT NOT NULL,  -- JSON: list of related entity IDs
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (world_id) REFERENCES worlds(id) ON DELETE CASCADE
    );

    CREATE INDEX IF NOT EXISTS idx_entities_world ON entities(world_id);
    CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(world_id, entity_type);

    CREATE TABLE IF NOT EXISTS relationships (
        id TEXT PRIMARY KEY,
        world_id TEXT NOT NULL,
        source_entity_id TEXT NOT NULL,
        target_entity_id TEXT NOT NULL,
        relationship_type TEXT NOT NULL,
        attributes TEXT NOT NULL,     -- JSON
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (world_id) REFERENCES worlds(id) ON DELETE CASCADE,
        FOREIGN KEY (source_entity_id) REFERENCES entities(id) ON DELETE CASCADE,
        FOREIGN KEY (target_entity_id) REFERENCES entities(id) ON DELETE CASCADE
    );

    CREATE INDEX IF NOT EXISTS idx_rel_world ON relationships(world_id);
    CREATE INDEX IF NOT EXISTS idx_rel_source ON relationships(source_entity_id);
    CREATE INDEX IF NOT EXISTS idx_rel_target ON relationships(target_entity_id);
    """
    db.executescript(script)

def downgrade(db: Database):
    script = """
    DROP TABLE IF EXISTS relationships;
    DROP TABLE IF EXISTS entities;
    DROP TABLE IF EXISTS entity_types;
    DROP TABLE IF EXISTS worlds;
    """
    db.executescript(script)
