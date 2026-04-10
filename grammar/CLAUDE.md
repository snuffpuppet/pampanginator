# grammar/ — Grammar MCP Server

## This service owns
- Kapampangan grammar graph (nodes and edges) with semantic embeddings
- Two-stage retrieval (semantic search + graph traversal)
- Grammar contribution review queue
- Canonical grammar data (grammar/data/grammar_nodes.json,
  grammar/data/grammar_edges.json)
- Grammar-specific scripts (export, import, merge, package)

## This service does NOT own
- Vocabulary data — that is vocab/'s responsibility
- Interactions or feedback — that is app/'s responsibility
- Any knowledge of the app or vocab services

## Database
grammar-postgres — tables: grammar_nodes, grammar_edges, pending_contributions
Schema: grammar/db/init.sql

## Canonical data
grammar/data/grammar_nodes.json and grammar/data/grammar_edges.json are
the source of truth. The database is seeded from these files on startup
if empty. Set RESEED_ON_STARTUP=true to force reseed.

## API surface (what app/ calls)
POST /traverse                 — two-stage semantic search + graph traversal
GET  /node/{id}               — single node by id
POST /node                    — add new node
POST /edge                    — add new edge
GET  /grammar/export          — export approved local additions
POST /contributions           — submit external contribution
GET  /contributions/pending   — list pending contributions
POST /contributions/{id}/approve
POST /contributions/{id}/reject
GET  /admin/stats             — local-addition counts for sync status
GET  /admin/export            — export local additions as JSON
GET  /health

## Two-stage retrieval
Stage 1: embed query → pgvector cosine similarity → find entry nodes
Stage 2: traverse grammar_edges from entry nodes → return relational context
Both stages run on every /traverse call. Never return a single node without
its graph context.

## Architecture decisions most relevant to this service
Decisions 3a, 4, 5, 11, 13, 14, 19
Full architecture: ../ARCHITECTURE.md

## Skills
- architecture-compliance: read before any structural change
- mcp-builder: read when building or modifying MCP endpoints
- otel-instrumentation: read when modifying tracing
- otel-metrics: read when modifying metrics
