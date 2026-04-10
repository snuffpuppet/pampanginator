-- Vocabulary service — PostgreSQL schema
-- vocab-postgres only: vocabulary, pending_contributions
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
-- Pending contributions (Decision 19 — vocab service)
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS pending_contributions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    submitted_at TIMESTAMPTZ DEFAULT NOW(),
    contributor TEXT NOT NULL,
    contribution_type TEXT NOT NULL
        CHECK (contribution_type IN ('vocabulary')),
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
