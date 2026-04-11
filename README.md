# Pampanginator

A Kapampangan language tutor with a pluggable LLM backend. The assistant, named **Ading** (younger sibling), teaches vocabulary, verb aspect morphology, grammar, and pronunciation through conversation. It grounds every answer in authoritative reference data stored in PostgreSQL/pgvector databases rather than relying on the model's training knowledge alone.

The LLM backend is configurable — all models are accessed via OpenRouter, giving access to Claude, Llama, Gemini, and others through a single API key. Two models can be compared side by side in the Compare view.

---

## Services

```
User browser
    ↓ dev: http://localhost:5173 (Vite dev server, HMR)
    ↓ prod: http://localhost:8000 (FastAPI serves compiled SPA + API)
    ↓
app (port 8000)               Orchestration API  [+ compiled React SPA in prod]
    ├── mcp-vocabulary  (port 8001)    Vocabulary MCP server (pgvector semantic search)
    └── mcp-grammar     (port 8002)    Grammar graph MCP server (pgvector + graph traversal)

Databases (each service owns its own — no sharing)
    ├── app-postgres     (port 5432)   interactions, feedback, pending_contributions
    ├── vocab-postgres   (port 5433)   vocabulary entries + embeddings
    └── grammar-postgres (port 5434)   grammar nodes, edges + embeddings

Observability stack
    ├── grafana        (port 3000)   Dashboards (Prometheus + Tempo + Loki)
    ├── prometheus     (port 9090)   Metrics scraper
    ├── tempo          (port 3200)   Distributed trace storage
    ├── loki           (port 3100)   Log aggregation
    ├── promtail                     Log shipper (reads Docker container logs)
    └── otel-collector (port 4318)   OTLP HTTP receiver → Tempo
```

**app** — FastAPI service that owns the agentic tool-use loop. Maintains per-session conversation history, logs every interaction to PostgreSQL, dispatches tool calls to the MCP servers, and serves the built React frontend as static files.

**mcp-vocabulary** — FastAPI service backed by pgvector. Generates sentence-transformer embeddings (all-MiniLM-L6-v2, 384 dims) at startup for semantic search. Seeds from `mcp-vocabulary/data/vocabulary.json` on first boot (or when `RESEED_ON_STARTUP=true`). Exposes vocabulary search and contribution endpoints.

**mcp-grammar** — FastAPI service backed by pgvector. Same embedding model. Seeds from `mcp-grammar/data/grammar_nodes.json` and `mcp-grammar/data/grammar_edges.json`. Exposes graph traversal using two-stage retrieval: semantic similarity to find anchor nodes, graph edges for relationship expansion.

---

## Quick Start

### Prerequisites

- Docker with Docker Compose v2.19 or later
- An OpenRouter API key (get one at https://openrouter.ai/keys)

No Node.js installation is required on the host machine.

### 1. Configure

Copy `.env.example` to `.env` and fill in the values:

```bash
cp .env.example .env
```

Key variables:

```bash
# PostgreSQL — all three database instances use this password
POSTGRES_PASSWORD=change_me         # REQUIRED

# LLM backend — all models accessed via OpenRouter
OPENROUTER_API_KEY=your-key-here    # REQUIRED

# Override the active model (optional — defaults to value in app/config/llm.yaml)
# OPENROUTER_MODEL=anthropic/claude-sonnet-4-6

# Admin interface password (optional — if unset, admin is open)
VITE_ADMIN_PASSWORD=your-admin-password
```

The model and backend are configured in `app/config/llm.yaml`. The `OPENROUTER_MODEL` env var overrides the model at runtime without a rebuild.

### 2. Start

```bash
make up
```

This creates a `pampanginator` Docker bridge network (if it doesn't exist), starts all three services and their databases, then starts the observability stack. All services discover each other by name on that network.

**Open `http://localhost:5173`** — the Vite dev server with HMR. All `/api/*` requests are proxied to FastAPI on `:8000`.

On first boot, `mcp-vocabulary` and `mcp-grammar` detect empty databases and seed automatically from their canonical data files. No manual seeding step is required.

```bash
make down     # stop everything
make logs-app # follow logs for a specific service
```

### Dev workflow

Source directories are volume-mounted into each container — Python and config changes hot-reload without a rebuild. Frontend changes are handled by Vite HMR.

After adding new Python dependencies to `requirements.txt`, rebuild the affected image:

```bash
docker compose -f app/docker-compose.yml build app
```

### Prod mode

The app `Dockerfile` uses a multi-stage build: a Node.js stage compiles the React frontend, the output is copied into the Python runtime stage. FastAPI then serves the SPA as static files alongside the API. No separate frontend server or local Node.js is required.

```bash
docker compose -f app/docker-compose.yml build app
make up
```

**Open `http://localhost:8000`** — the full app served from a single port.

### Reseeding

The `mcp-vocabulary` and `mcp-grammar` services seed automatically on first boot. To force a full reseed after pulling updated canonical data files:

```bash
# Reseed all services
RESEED_ON_STARTUP=true make up

# Reseed a single service (from its own directory)
cd mcp-vocabulary && RESEED_ON_STARTUP=true make up
cd mcp-grammar    && RESEED_ON_STARTUP=true make up
```

Canonical data files:
- `mcp-vocabulary/data/vocabulary.json`
- `mcp-grammar/data/grammar_nodes.json`
- `mcp-grammar/data/grammar_edges.json`

---

## Testing

The backend unit test suites run entirely inside Docker. No API key, no running database, and no internet connection are required — all external services (LLM, database, MCP servers) are mocked.

### Prerequisites

Only Docker is required. Test images are built automatically on first run.

### Run the tests

```bash
make test           # app service tests only
make test-vocab     # vocab service tests only
make test-grammar   # grammar service tests only
make test-all       # all three suites in sequence
```

```bash
make test-fast      # stop on first failure (faster feedback during development)
make test-build     # force-rebuild the app test image after changing requirements
```

### What is covered (app service)

| File | What it tests |
|------|--------------|
| `tests/test_health.py` | `/health` liveness probe |
| `tests/test_chat.py` | SSE streaming, caveat logic, error handling, session ID generation |
| `tests/test_feedback.py` | Submit / approve / reject feedback, filter passthrough, 404 and 500 handling |
| `tests/test_vocab.py` | MCP proxy, 503 on connection failure, upstream status propagation |
| `tests/test_export.py` | SFT/DPO export logic, correction fallback, content-disposition header |
| `tests/test_llm_utils.py` | `_try_parse_text_tool_call` — normalisation and rejection of text-based tool calls |
| `tests/test_tool_router.py` | `load_tools`, Anthropic/OpenAI schema conversion, dispatch error handling |

Tests use `pytest-asyncio` with `asyncio_mode = auto`. The test app is a minimal FastAPI instance with all routes registered but no lifespan, telemetry, or static file mount. Each test patches only the specific service calls it exercises.

Each of `mcp-vocabulary/` and `mcp-grammar/` has an equivalent test setup under their own directories.

### Test infrastructure

| File | Purpose |
|------|---------|
| `app/Dockerfile.test` | Slim test image — app dependencies + pytest, no frontend build |
| `docker-compose.test.yml` | Runs all three test containers; mounts service directories for live source |
| `app/pytest.ini` | `asyncio_mode = auto`, `testpaths = tests` |
| `app/requirements-test.txt` | `pytest`, `pytest-asyncio` |

---

## API Endpoints

### Orchestration app (port 8000)

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/chat` | Stream a chat response (SSE) |
| `POST` | `/api/chat/model-a` | Stream using model A (primary model from llm.yaml) |
| `POST` | `/api/chat/model-b` | Stream using model B (comparison model from llm.yaml) |
| `GET` | `/api/status` | Active backend, model names, and API key presence |
| `GET` | `/api/vocabulary/search` | Semantic vocabulary search |
| `POST` | `/api/vocabulary` | Add a vocabulary entry |
| `POST` | `/api/feedback` | Submit thumbs-up or thumbs-down feedback |
| `GET` | `/api/feedback/pending` | List unreviewed thumbs-down corrections |
| `GET` | `/api/feedback` | List all feedback (filterable) |
| `POST` | `/api/feedback/{id}/approve` | Approve a correction, write it to vocabulary |
| `POST` | `/api/feedback/{id}/reject` | Mark a correction rejected |
| `POST` | `/api/export/training-data` | Download SFT or DPO JSONL for fine-tuning |
| `GET` | `/api/admin/sync/status` | Knowledge sharing sync status |
| `POST` | `/api/admin/sync/export` | Download local contributions as a zip archive |
| `GET` | `/api/admin/contributions/pending` | List pending contributions (Mode 3) |
| `POST` | `/api/admin/contributions/upload` | Upload a contribution zip for review (Mode 2) |
| `POST` | `/api/admin/contributions/{id}/approve` | Approve an uploaded contribution |
| `POST` | `/api/admin/contributions/{id}/reject` | Reject an uploaded contribution |
| `GET` | `/health` | Liveness probe |
| `GET` | `/metrics` | Prometheus metrics (OpenMetrics format) |
| `GET` | `/docs` | Swagger UI |

### Vocab server (port 8001)

| Method | Path | Description |
|---|---|---|
| `POST` | `/lookup` | Semantic search for vocabulary entries |
| `POST` | `/vocabulary` | Add a vocabulary entry |
| `GET` | `/status` | Service health and entry count |
| `GET` | `/docs` | Swagger UI |

### Grammar server (port 8002)

| Method | Path | Description |
|---|---|---|
| `POST` | `/traverse` | Two-stage semantic + graph traversal |
| `GET` | `/status` | Service health and node/edge count |
| `GET` | `/docs` | Swagger UI |

---

## Frontend Views

| Path | Description |
|---|---|
| `/` | Home — quick-action tiles and scenario launcher |
| `/chat` | Conversation with Ading |
| `/translate` | Dedicated translation mode (EN↔KP) |
| `/grammar` | Grammar explorer |
| `/vocabulary` | Vocabulary search (semantic), flashcard drill, and add-entry form |
| `/compare` | Side-by-side comparison of two configurable OpenRouter models |
| `/admin` | Admin interface (password-gated) |

### Admin interface (`/admin`)

Four tabs:

- **Review** — pending thumbs-down corrections from users, with approve/reject controls and authority level override
- **History** — full feedback log with filters (rating, authority level, date range, applied status)
- **Export** — download training data as SFT or DPO JSONL for fine-tuning, with date range and authority level filters
- **Contributions** — knowledge sharing: export local vocabulary additions as a zip, upload and review incoming contribution zips (Mode 2), review pending shared-DB contributions (Mode 3)

---

## How Vocabulary Search Works

Vocabulary entries are stored in PostgreSQL with a 384-dimensional pgvector embedding per entry. At query time:

1. The query text is embedded with the same sentence-transformer model
2. A cosine similarity search finds the nearest neighbours in the vector index
3. Results include `similarity_score` — the frontend shows a "near miss" notice when the best match is below 0.72

The mcp-vocabulary server also exposes the data to the agentic loop: when the LLM needs to ground a translation or correction in authoritative data, it calls `vocabulary_lookup` which hits the same semantic search.

### Vocabulary data lifecycle

Canonical data lives in `mcp-vocabulary/data/vocabulary.json` (plus `mcp-grammar/data/grammar_nodes.json` and `mcp-grammar/data/grammar_edges.json`). On first boot, each MCP server checks whether its table is empty and seeds from these files. Set `RESEED_ON_STARTUP=true` to force a full re-seed.

To manage vocabulary outside the UI, use the scripts in `mcp-vocabulary/scripts/`:

```bash
# Export local (non-seeded) additions as a contribution zip
python mcp-vocabulary/scripts/export_contributions.py

# Import a vocabulary JSON file into the running database
python mcp-vocabulary/scripts/import_knowledge.py --file mcp-vocabulary/data/vocabulary.json --mode incremental

# Merge a contributor's additions into the canonical data files
python mcp-vocabulary/scripts/merge_contributions.py --contrib-dir /path/to/contrib/

# Package a contribution for sharing (Mode 2)
python mcp-vocabulary/scripts/package_contribution.py --contributor "Name"
```

Training data export lives in `app/scripts/`:

```bash
python app/scripts/export_training_data.py --min_authority_level 1 --format dpo --output training_data.jsonl
```

---

## How the Grammar Server Works

Grammar knowledge is stored as a typed directed graph in PostgreSQL. Each node is a grammar concept (verb root, focus type, pronoun set, etc.) with an embedding; edges carry a relationship type (`aspect_of`, `focus_type`, `related_form`, `derived_noun`).

When the LLM calls `grammar_lookup`, the server runs two-stage retrieval:

1. **Semantic anchor** — embed the query, find the most similar node(s) in the vector index
2. **Graph expansion** — walk edges from the anchor nodes, optionally filtered by relationship type, returning connected nodes and their labels

This means grammar questions are answered even when the exact node id is not known.

---

## Knowledge Sharing

Contributors working on separate databases can share vocabulary and grammar additions through three modes, configured in `app/config/knowledge_sharing.yaml`:

| Mode | How |
|---|---|
| `git` (default) | Export a zip, commit to a shared repo, teammates import from repo |
| `sync` | Automatic push/pull against a hosted canonical URL |
| `shared_db` | All contributors write to a common cloud PostgreSQL instance |

The **Contributions tab** in the admin interface handles the Mode 2 zip workflow end-to-end: export your local additions, share the zip, and the recipient uploads it for review before applying.

---

## Feedback and Training Data

Every chat interaction is logged to the `interactions` table. Users can rate any Ading response with thumbs up or down. Thumbs-down opens an inline correction form (Kapampangan fix, English gloss, corrector identity, authority level 1–4).

Approved corrections are written back to the vocabulary database, closing the loop between user feedback and the knowledge base.

The **Export tab** in the admin interface downloads approved interactions as:

- **SFT** — supervised fine-tuning pairs (prompt + response) in JSONL
- **DPO** — direct preference optimisation triples (prompt + chosen + rejected) in JSONL

Both formats are filtered by minimum authority level and optional date range.

---

## Observability Dashboard

Grafana loads automatically at `http://localhost:3000` (no login required).

The **Kapampangan Tutor** dashboard provides:

- **Request rate and error rate** across all three services
- **p50 / p99 latency** for end-to-end requests
- **LLM call duration** — time waiting for the LLM backend, broken down by model
- **Token consumption** — input and output tokens per minute
- **Tool call rate** — how often vocabulary vs grammar lookups are triggered
- **Live trace list** — recent traces from Tempo, click any to inspect the full span tree

Every histogram panel supports **exemplar click-through**: click a dot on a latency chart to open the exact trace in Tempo.

Traces are accessible directly via **Explore → Tempo** → service: `kapampangan-app`.

Raw metrics are available at `http://localhost:9090`.

---

## Configuration

| File | Purpose |
|---|---|
| `app/config/system_prompt.md` | Ading's persona, language profile, and interaction rules |
| `app/config/tools.yaml` | Tool definitions passed to every LLM API call |
| `app/config/llm.yaml` | LLM backend selection, model, temperature, tool-use toggle |
| `app/config/knowledge_sharing.yaml` | Contributor name and knowledge sharing mode |
| `app/config/ui.yaml` | Navigation labels, quick-action tiles, scenario definitions |
| `app/config/otel-collector.yaml` | OTel collector pipeline |
| `app/config/tempo.yaml` | Tempo trace storage config |
| `app/config/prometheus.yaml` | Prometheus scrape targets |
| `app/config/dashboard/` | Grafana datasource and dashboard provisioning |

The `app/config/` directory is mounted into the `app` container — changes to the system prompt, tool definitions, and LLM settings take effect on a service restart with no image rebuild.

---

## Project Layout

```
app/                     Orchestration service + React frontend
  config/                Runtime configuration (mounted, not baked in)
    system_prompt.md     Ading's persona and grammar rules
    tools.yaml           MCP tool definitions and routing
    llm.yaml             LLM backend selection and model config
    knowledge_sharing.yaml  Knowledge sharing mode and settings
    ui.yaml              Navigation, scenarios, sample prompts
    dashboard/           Grafana provisioning
  db/
    init.sql             PostgreSQL schema (interactions, feedback, pending_contributions)
  frontend/              React SPA
    vite.config.ts       Dev server config — proxies /api to :8000
    src/
      components/        Chat, Translate, Grammar, Vocabulary, Compare, Admin, ...
      services/api.ts    All fetch() calls — one file
      store/             Zustand stores (conversation, vocabulary)
      config/ui.ts       Navigation, scenarios, sample prompts
  scripts/
    export_training_data.py
  services/
    llm.py               Agentic loop (tool use, multi-turn, streaming)
    tool_router.py       Dispatches tool calls to MCP servers
    db.py                asyncpg connection pool
    interactions.py      Interaction logging
    knowledge.py         Knowledge sharing service
  routes/
    chat.py              POST /api/chat, /api/chat/model-a, /api/chat/model-b, GET /api/status
    feedback.py          Feedback CRUD and review endpoints
    vocab.py             Vocabulary search and add proxy
    export.py            Training data export (SFT/DPO JSONL)
    admin_knowledge.py   Knowledge sharing admin endpoints
    health.py            GET /health
  tests/                 Unit tests (pytest-asyncio, all external services mocked)
  Dockerfile
  Dockerfile.test

mcp-vocabulary/          Vocabulary MCP server
  data/
    vocabulary.json      Canonical vocabulary entries (source of truth)
    PROVENANCE.md        Contributor and source metadata
  db/
    init.sql             PostgreSQL schema (vocabulary table + pgvector)
  scripts/
    export_contributions.py
    import_knowledge.py
    merge_contributions.py
    package_contribution.py
  services/
    embed.py             Sentence-transformer embedding (all-MiniLM-L6-v2)
    seed.py              Seeds from data/vocabulary.json if table is empty
    db.py                asyncpg pool
  routes/
    lookup.py            POST /lookup (semantic search)
    vocab.py             POST /vocabulary (add entry)
  tests/                 Unit tests
  Dockerfile
  Dockerfile.test
  Makefile               up, down, logs, test, test-fast, test-build, shell

mcp-grammar/             Grammar graph MCP server
  data/
    grammar_nodes.json   Canonical grammar concept nodes (source of truth)
    grammar_edges.json   Canonical grammar relationship edges (source of truth)
    PROVENANCE.md        Contributor and source metadata
  db/
    init.sql             PostgreSQL schema (grammar_nodes, grammar_edges + pgvector)
  services/
    embed.py             Sentence-transformer embedding
    seed.py              Seeds from data/ if tables are empty
    db.py                asyncpg pool
  routes/
    traverse.py          POST /traverse (two-stage semantic + graph retrieval)
  tests/                 Unit tests
  Dockerfile
  Dockerfile.test
  Makefile               up, down, logs, test, test-fast, test-build, shell

docker-compose.yml       Observability stack; root Makefile delegates sub-projects then starts this
docker-compose.test.yml  Test runner definitions (all three suites)
Makefile                 test, test-vocab, test-grammar, test-all, up, down, build
```
