-- Kapampangan Tutor — PostgreSQL schema
-- Run automatically on first startup via docker-entrypoint-initdb.d/

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ---------------------------------------------------------------------------
-- Vocabulary (Decision 11, 12, 14)
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS vocabulary (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    term TEXT NOT NULL,
    meaning TEXT NOT NULL,
    part_of_speech TEXT,
    aspect_forms JSONB,           -- {"progressive": "...", "completed": "...", "contemplated": "..."}
    examples JSONB,               -- [{"kapampangan": "...", "english": "..."}]
    usage_notes TEXT,
    embedding_text TEXT NOT NULL,
    embedding vector(384),
    authority_level INTEGER DEFAULT 3 CHECK (authority_level BETWEEN 1 AND 4),
    source TEXT,
    verified_by TEXT,
    verified_date DATE,
    notes TEXT,
    seeded_from_canonical BOOLEAN DEFAULT FALSE,  -- true for entries loaded from data/vocabulary.json
    contributor TEXT,             -- who added this entry
    added_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS vocabulary_embedding_idx
    ON vocabulary USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 10);

CREATE INDEX IF NOT EXISTS vocabulary_term_idx ON vocabulary (lower(term));

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
-- Interaction logging (Decision 15)
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id TEXT NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    scenario TEXT,
    user_message TEXT NOT NULL,
    system_prompt_version TEXT NOT NULL,
    model TEXT NOT NULL,
    tools_used TEXT[],
    vocabulary_entries_retrieved JSONB,
    grammar_nodes_retrieved JSONB,
    authority_levels_used INTEGER[],
    llm_response TEXT NOT NULL,
    kapampangan_produced TEXT,
    english_gloss TEXT
);

-- ---------------------------------------------------------------------------
-- Feedback capture (Decision 15)
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    interaction_id UUID REFERENCES interactions(id) ON DELETE SET NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    rating TEXT CHECK (rating IN ('thumbs_up', 'thumbs_down')),
    correction_kapampangan TEXT,
    correction_english TEXT,
    correction_note TEXT,
    corrected_by TEXT,
    authority_level INTEGER DEFAULT 3 CHECK (authority_level BETWEEN 1 AND 4),
    reviewed BOOLEAN DEFAULT FALSE,
    applied BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS feedback_reviewed_idx ON feedback (reviewed);
CREATE INDEX IF NOT EXISTS feedback_interaction_id_idx ON feedback (interaction_id);

-- ---------------------------------------------------------------------------
-- Pending contributions (Decision 19 — shared knowledge model)
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS pending_contributions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    submitted_at TIMESTAMPTZ DEFAULT NOW(),
    contributor TEXT NOT NULL,
    contribution_type TEXT NOT NULL
        CHECK (contribution_type IN ('vocabulary', 'grammar_node', 'grammar_edge')),
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
