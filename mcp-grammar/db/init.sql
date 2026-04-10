-- Grammar service — PostgreSQL schema
-- grammar-postgres only: grammar_nodes, grammar_edges, pending_contributions
-- Run automatically on first startup via docker-entrypoint-initdb.d/

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ---------------------------------------------------------------------------
-- Grammar graph — nodes and edges (Decision 13, 14)
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS grammar_nodes (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    label TEXT,
    meaning TEXT,
    embedding_text TEXT NOT NULL,
    embedding vector(384),
    authority_level INTEGER DEFAULT 3 CHECK (authority_level BETWEEN 1 AND 4),
    source TEXT,
    verified_by TEXT,
    verified_date DATE,
    notes TEXT,
    seeded_from_canonical BOOLEAN DEFAULT FALSE,  -- true for entries loaded from data/grammar_nodes.json
    contributor TEXT,
    added_date DATE DEFAULT CURRENT_DATE
);

CREATE INDEX IF NOT EXISTS grammar_nodes_embedding_idx
    ON grammar_nodes USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 10);

CREATE TABLE IF NOT EXISTS grammar_edges (
    from_node TEXT REFERENCES grammar_nodes(id) ON DELETE CASCADE,
    relationship TEXT NOT NULL,
    to_node TEXT REFERENCES grammar_nodes(id) ON DELETE CASCADE,
    PRIMARY KEY (from_node, relationship, to_node)
);

-- ---------------------------------------------------------------------------
-- Pending contributions (Decision 19 — grammar service)
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS pending_contributions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    submitted_at TIMESTAMPTZ DEFAULT NOW(),
    contributor TEXT NOT NULL,
    contribution_type TEXT NOT NULL
        CHECK (contribution_type IN ('grammar_node', 'grammar_edge')),
    payload JSONB NOT NULL,
    source_mode TEXT NOT NULL
        CHECK (source_mode IN ('git', 'sync', 'shared_db')),
    authority_level INTEGER NOT NULL,
    review_status TEXT DEFAULT 'pending'
        CHECK (review_status IN ('pending', 'approved', 'rejected')),
    reviewed_by TEXT,
    reviewed_at TIMESTAMPTZ,
    review_note TEXT
);

CREATE INDEX IF NOT EXISTS pending_contributions_status_idx ON pending_contributions (review_status);
CREATE INDEX IF NOT EXISTS pending_contributions_contributor_idx ON pending_contributions (contributor);
CREATE INDEX IF NOT EXISTS pending_contributions_submitted_idx ON pending_contributions (submitted_at);
