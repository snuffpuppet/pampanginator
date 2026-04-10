# app/ — Orchestration Service + React Frontend

## This service owns
- React frontend (chat UI, vocabulary page, admin interface)
- FastAPI orchestration layer
- Conversation history and session management
- Interaction logging and feedback capture
- Training data export
- LLM API calls via Anthropic SDK

## This service does NOT own
- Vocabulary data — call http://mcp-vocabulary:8001
- Grammar data — call http://grammar:8002
- vocab-postgres or grammar-postgres — never access these directly

## Database
app-postgres — tables: interactions, feedback, sessions, pending_contributions
Schema: app/db/init.sql

## Architecture decisions most relevant to this service
Decisions 1, 2, 3, 3a, 6, 7, 8, 9, 10, 15, 16, 17, 18, 19
Full architecture: ../ARCHITECTURE.md

## Skills
- architecture-compliance: read before any structural change
- otel-instrumentation: read when modifying tracing
- otel-metrics: read when modifying metrics
- frontend-design: read when building or modifying React components
