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
- Grammar data — call http://mcp-grammar:8002
- vocab-postgres or grammar-postgres — never access these directly

## Database
app-postgres — tables: interactions, feedback, sessions, pending_contributions
Schema: app/db/init.sql

## Running this service

### Standalone (from app/)
    make up              # app API + app-postgres + Vite dev server on :5173
    make down
    make logs
    make shell           # bash in running container

Dev entry point: http://localhost:5173 (Vite, with HMR — proxies /api/* to :8000)
API only: http://localhost:8000 (FastAPI — no frontend served in dev)
app-postgres: :5432

MCP services are optional when running standalone — vocabulary/grammar calls
will fail until those services are up. To connect to them start each
independently (they bind to host ports 8001 and 8002):
    cd ../mcp-vocabulary && make up
    cd ../mcp-grammar && make up

### Full stack (from repo root)
    make up              # all services — delegates to each sub-project's docker-compose.yml
    make up-app          # only this service (delegates to app/Makefile)

### Environment
Required: OPENROUTER_API_KEY
Key defaults (see ../.env.example for all variables):
    POSTGRES_PASSWORD=kapampangan_dev
    VOCABULARY_SERVICE_URL=http://host.docker.internal:8001
    GRAMMAR_SERVICE_URL=http://host.docker.internal:8002
    BACKEND=openrouter

### Tests
    make test            # run app test suite in Docker
    make test-fast       # stop on first failure
    make test-build      # rebuild test image after requirements change

## Architecture decisions most relevant to this service
Decisions 1, 2, 3, 3a, 6, 7, 8, 9, 10, 15, 16, 17, 18, 19
Full architecture: ../ARCHITECTURE.md

## Skills
- architecture-compliance: read before any structural change
- otel-instrumentation: read when modifying tracing
- otel-metrics: read when modifying metrics
- frontend-design: read when building or modifying React components
