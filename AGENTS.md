# AGENTS.md — Pampanginator

## Architecture overview

Three FastAPI services + React SPA, all containerised with Docker Compose:

- `app` (port 8000) — orchestration layer, agentic tool-use loop, serves built React frontend as static files
- `mcp-vocabulary` (port 8001) — pgvector semantic search over vocabulary entries
- `mcp-grammar` (port 8002) — pgvector semantic search + graph traversal over grammar nodes/edges
- `postgres` (port 5432) — pgvector/pg16, shared by all three services
- Observability: Grafana (3000), Prometheus (9090), Tempo (3200), Loki (3100), otel-collector (4318)

All three Python services have identical structure: `main.py`, `telemetry.py`, `metrics.py`, `middleware.py`, `routes/`, `services/`, `models/`.

## Dev vs prod mode

```bash
# Dev — auto-merges docker-compose.override.yml, mounts source dirs, --reload on all services
docker compose up
# Open http://localhost:5173 (Vite HMR frontend)

# Prod — skips override, multi-stage Dockerfile builds React into the app image
docker compose -f docker-compose.yml up
# Open http://localhost:8000
```

The `-f` flag is the only difference. Forgetting it in prod silently uses dev mode.

After adding Python dependencies to `requirements.txt`, you must rebuild:
```bash
docker compose build <service>   # hot-reload does NOT pick up new packages
```

## Required setup

Copy `.env.example` to `.env`. Minimum required variables:
```
POSTGRES_PASSWORD=changeme
OPENROUTER_API_KEY=your-key-here
```

`VITE_ADMIN_PASSWORD` — if unset, `/admin` is open to everyone (dev convenience).

## Config is mounted, not baked in

`config/` is mounted as a volume at runtime. Changes to `config/system_prompt.md`, `config/tools.yaml`, `config/llm.yaml`, and `config/ui.yaml` take effect on **container restart only** — no image rebuild needed.

`data/` (vocabulary/grammar JSON) is mounted read-only into the MCP servers.

## Knowledge base seeding

MCP servers seed from `data/` on first boot only (table-empty check). To reseed:
```bash
RESEED_ON_STARTUP=true docker compose up
# or set reseed_on_startup: true in config/knowledge_sharing.yaml
```

Canonical data files: `data/vocabulary.json`, `data/grammar_nodes.json`, `data/grammar_edges.json`.

## Frontend build

`vite.config.ts` sets `outDir: '../app/frontend'` — the build output lands in `app/frontend/`, which is what the FastAPI app serves in prod.

Frontend is TypeScript + React + Zustand + Tailwind. No test suite exists. Build check:
```bash
# Inside the frontend container (dev mode) or locally if Node is available:
npm run build   # runs tsc && vite build
```

The Vite dev server implements `/api/chat`, `/api/chat/anthropic`, and `/api/chat/ollama` as in-process middleware — these **bypass the FastAPI agentic loop entirely** (no tool calls, no interaction logging). They exist only for the Compare page. In prod, all `/api/chat` traffic goes through FastAPI.

## LLM backend

`config/llm.yaml` sets the active backend and model. The `BACKEND` env var overrides `active_backend`. `OPENROUTER_MODEL` overrides the model without a rebuild.

All models are accessed via OpenRouter (`https://openrouter.ai/api/v1`). Sub-7B models are architecturally unsuitable for Kapampangan — the language is low-resource. Claude Sonnet class is the minimum for grammar questions.

## OTel instrumentation pattern

`init_telemetry(app)` must be called **after** `app = FastAPI()` and **before** route registration. `HTTPXClientInstrumentor` propagates `traceparent` headers to MCP server requests. All three services follow this same pattern.

Service names (used in Grafana/Tempo): `kapampangan-app`, `kapampangan-mcp-vocabulary`, `kapampangan-mcp-grammar`.

Infrastructure image versions are pinned in `docker-compose.yml` — never change to `latest` (Tempo 2.7+ changed the default write path, breaking config).

## Structural rules (skills enforced)

Four skills apply to this project — load before acting:

| Task | Skill to load |
|---|---|
| Any file/directory/dependency structural change | `architecture-compliance` |
| Building or modifying MCP servers | `mcp-builder` (at `/mnt/skills/examples/mcp-builder/SKILL.md`) |
| Adding/modifying OTel tracing spans | `otel-instrumentation` |
| Adding/modifying Prometheus metrics | `otel-metrics` |
| Building/modifying React components | `frontend-design` |

## All HTTP calls live in one file

`frontend/src/services/api.ts` — all `fetch()` calls. Components and stores never call fetch directly (Decision 10). Zustand stores in `frontend/src/store/`.

## Data scripts

```bash
python scripts/import_knowledge.py --file data/vocabulary.json --mode incremental
python scripts/export_contributions.py
python scripts/merge_contributions.py --contrib-dir /path/to/contrib/
python scripts/package_contribution.py --contributor "Name"
```

Scripts run against a live database — requires the postgres container to be up and `DATABASE_URL` set in environment.

## No CI / no test suite

There are no automated tests, no CI workflows, and no linting config in this repo. Verification is manual: start the stack and test through the UI or Swagger docs (`/docs` on each service).
