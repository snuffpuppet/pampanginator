-- App service — PostgreSQL schema
-- app-postgres only: interactions, feedback, pending_contributions
-- Run automatically on first startup via docker-entrypoint-initdb.d/

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

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
-- Pending contributions (Decision 19 — app service)
-- Holds contributions submitted via the app admin interface before they are
-- forwarded to the appropriate service (vocab or grammar) for review.
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
