# mcp-vocabulary/ — Vocabulary MCP Server

## This service owns
- Kapampangan vocabulary entries with semantic embeddings
- Vocabulary lookup and semantic search
- Vocabulary contribution review queue
- Canonical vocabulary data (mcp-vocabulary/data/vocabulary.json)
- Vocabulary-specific scripts (export, import, merge, package)

## This service does NOT own
- Grammar data — that is grammar/'s responsibility
- Interactions or feedback — that is app/'s responsibility
- Any knowledge of the app or grammar services

## Database
vocab-postgres — tables: vocabulary, pending_contributions
Schema: mcp-vocabulary/db/init.sql

## Canonical data
mcp-vocabulary/data/vocabulary.json is the source of truth for vocabulary.
The database is seeded from this file on startup if empty.
Set RESEED_ON_STARTUP=true to force reseed after pulling updated data.

## API surface (what app/ calls)
GET  /lookup?q={query}         — semantic vocabulary search
GET  /vocabulary/{id}          — single entry by id
POST /vocabulary               — add new entry
GET  /vocabulary/export        — export approved local additions
POST /contributions            — submit external contribution
GET  /contributions/pending    — list pending contributions
POST /contributions/{id}/approve
POST /contributions/{id}/reject
GET  /admin/stats              — seeded/local counts for sync status
GET  /admin/export             — export local additions as JSON
GET  /health

## Architecture decisions most relevant to this service
Decisions 3a, 4, 5, 11, 12, 14, 19
Full architecture: ../ARCHITECTURE.md

## Skills
- architecture-compliance: read before any structural change
- mcp-builder: read when building or modifying MCP endpoints
- otel-instrumentation: read when modifying tracing
- otel-metrics: read when modifying metrics
