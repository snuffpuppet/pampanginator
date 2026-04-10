# Pampanginator

A Kapampangan language tutor with a pluggable LLM backend. The assistant, named **Ading** (younger sibling), teaches vocabulary, verb aspect morphology, grammar, and pronunciation through conversation. It grounds every answer in authoritative reference data stored in a PostgreSQL/pgvector database rather than relying on the model's training knowledge alone.

The LLM backend is configurable — it runs against Anthropic's API (Claude) or any OpenAI-compatible model via Ollama. Both can be compared side by side in the Compare view.

---

## Services

```
User browser
    ↓
app (port 8000)               Orchestration API + built React frontend
    ├── mcp-vocabulary (port 8001)   Vocabulary MCP server (pgvector semantic search)
    └── mcp-grammar    (port 8002)   Grammar graph MCP server (pgvector + graph traversal)
    └── postgres       (port 5432)   PostgreSQL 16 + pgvector (shared by all three)

Observability stack
    ├── grafana        (port 3000)   Dashboards (Prometheus + Tempo + Loki)
    ├── prometheus     (port 9090)   Metrics scraper
    ├── tempo          (port 3200)   Distributed trace storage
    ├── loki           (port 3100)   Log aggregation
    ├── promtail                     Log shipper (reads Docker container logs)
    └── otel-collector (port 4318)   OTLP HTTP receiver → Tempo
```

**app** — FastAPI service that owns the agentic tool-use loop. Maintains per-session conversation history, logs every interaction to PostgreSQL, dispatches tool calls to the MCP servers, and serves the built React frontend as static files.

**mcp-vocabulary** — FastAPI service backed by pgvector. Generates sentence-transformer embeddings (all-MiniLM-L6-v2, 384 dims) at startup for semantic search. Seeds from `data/vocabulary.json` on first boot (or when `RESEED_ON_STARTUP=true`). Exposes vocabulary search and contribution endpoints.

**mcp-grammar** — FastAPI service backed by pgvector. Same embedding model. Seeds from `data/grammar_nodes.json` and `data/grammar_edges.json`. Exposes graph traversal using two-stage retrieval: semantic similarity to find anchor nodes, graph edges for relationship expansion.

---

## Quick Start

### Prerequisites

- Docker and Docker Compose
- An Anthropic API key, or Ollama running locally on the host

No Node.js installation is required on the host machine.

### Configure

Copy `.env.example` to `.env` and fill in the values:

```bash
cp .env.example .env
```

Key variables:

```bash
# LLM backend
BACKEND=anthropic
ANTHROPIC_API_KEY=your-key-here

# Or use a local Ollama model
# BACKEND=ollama
# OLLAMA_MODEL=llama3.2
# OLLAMA_URL=http://host.docker.internal:11434

# Admin interface password (optional — if unset, admin is open)
VITE_ADMIN_PASSWORD=your-admin-password
```

The LLM backend can also be configured per-service in `config/llm.yaml` (model, temperature, max tokens, whether the agentic tool-use loop is enabled).

### Dev mode (live reload)

```bash
docker compose up
```

Docker Compose automatically merges `docker-compose.yml` with `docker-compose.override.yml`. The override adds a `frontend` container running the Vite dev server with HMR, and mounts all service source directories so Python changes reload without a rebuild.

Open `http://localhost:5173`.

> **Note:** After adding new Python dependencies to `requirements.txt`, run `docker compose build <service>` to reinstall them — the dev server hot-reload picks up code changes but not new packages.

### Prod mode (container rebuild)

```bash
docker compose -f docker-compose.yml up
```

Passing `-f` explicitly skips the override file. The app image is built using a multi-stage Dockerfile: a Node.js stage compiles the React frontend, the output is copied into the Python runtime stage. No local Node.js required.

Open `http://localhost:8000`.

---

## API Endpoints

### Orchestration app (port 8000)

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/chat` | Stream a chat response (SSE) |
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

### MCP Vocabulary server (port 8001)

| Method | Path | Description |
|---|---|---|
| `POST` | `/lookup` | Semantic search for vocabulary entries |
| `POST` | `/vocabulary` | Add a vocabulary entry |
| `GET` | `/status` | Service health and entry count |
| `GET` | `/docs` | Swagger UI |

### MCP Grammar server (port 8002)

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
| `/compare` | Side-by-side Anthropic vs Ollama comparison |
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

The MCP server also exposes the data to the agentic loop: when Claude needs to ground a translation or correction in authoritative data, it calls `vocabulary_lookup` which hits the same semantic search.

### Vocabulary data lifecycle

Canonical data lives in `data/vocabulary.json` (plus `grammar_nodes.json` and `grammar_edges.json`). On first boot, each MCP server checks whether its table is empty and seeds from these files. Set `RESEED_ON_STARTUP=true` to force a full re-seed.

To add vocabulary outside the UI, use the CLI scripts:

```bash
# Export local (non-seeded) additions as a contribution zip
python scripts/export_contributions.py

# Import a vocabulary JSON file into the running database
python scripts/import_knowledge.py --file data/vocabulary.json --mode incremental

# Merge a contributor's additions into the canonical data files
python scripts/merge_contributions.py --contrib-dir /path/to/contrib/

# Package a contribution for sharing (Mode 2)
python scripts/package_contribution.py --contributor "Name"
```

---

## How the Grammar Server Works

Grammar knowledge is stored as a typed directed graph in PostgreSQL. Each node is a grammar concept (verb root, focus type, pronoun set, etc.) with an embedding; edges carry a relationship type (`aspect_of`, `focus_type`, `related_form`, `derived_noun`).

When Claude calls `grammar_lookup`, the server runs two-stage retrieval:

1. **Semantic anchor** — embed the query, find the most similar node(s) in the vector index
2. **Graph expansion** — walk edges from the anchor nodes, optionally filtered by relationship type, returning connected nodes and their labels

This means grammar questions are answered even when the exact node id is not known.

---

## Knowledge Sharing

Contributors working on separate databases can share vocabulary and grammar additions through three modes, configured in `config/knowledge_sharing.yaml`:

| Mode | How |
|---|---|
| `git` (default) | Export a zip, commit to a shared repo, teammates import from repo |
| `sync` | Automatic push/pull against a hosted canonical URL |
| `shared_db` | All contributors write to a common cloud PostgreSQL instance |

The **Contributions tab** in the admin interface handles the Mode 2 zip workflow end-to-end: export your local additions, share the zip, and the recipient uploads it for review before applying.

---

## Feedback and Training Data

Every chat interaction is logged to the `interactions` table. Users can rate any Ading response with 👍 or 👎. Thumbs-down opens an inline correction form (Kapampangan fix, English gloss, corrector identity, authority level 1–4).

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
| `config/system_prompt.md` | Ading's persona, language profile, and interaction rules |
| `config/tools.yaml` | Tool definitions passed to every LLM API call |
| `config/llm.yaml` | LLM backend selection, model, temperature, tool-use toggle |
| `config/knowledge_sharing.yaml` | Contributor name and knowledge sharing mode |
| `config/ui.yaml` | Navigation labels, quick-action tiles, scenario definitions |
| `config/otel-collector.yaml` | OTel collector pipeline |
| `config/tempo.yaml` | Tempo trace storage config |
| `config/prometheus.yaml` | Prometheus scrape targets |
| `config/dashboard/` | Grafana datasource and dashboard provisioning |

The `config/` directory is mounted into the `app` container — changes to the system prompt, tool definitions, and LLM settings take effect on a service restart with no image rebuild.

---

## Project Layout

```
data/                    Canonical knowledge base (seeded into PostgreSQL on first boot)
  vocabulary.json        Vocabulary entries
  grammar_nodes.json     Grammar concept nodes
  grammar_edges.json     Grammar relationship edges
  PROVENANCE.md          Contributor and source metadata

db/
  init.sql               PostgreSQL schema (vocabulary, grammar, interactions, feedback,
                         pending_contributions tables + pgvector extension)

scripts/                 CLI tools for data management
  export_contributions.py    Export local additions as a contribution zip
  import_knowledge.py        Import vocabulary/grammar from JSON into the database
  merge_contributions.py     Merge incoming contributions into canonical data files
  package_contribution.py    Package a contribution zip for sharing

frontend/                React SPA
  vite.config.ts         Dev server + fallback LLM middleware (Anthropic/Ollama)
  src/
    components/
      Home.tsx           Quick-action tiles and scenario launcher
      Chat.tsx           Main conversation interface with feedback controls
      Translate.tsx      Dedicated translation mode
      Grammar.tsx        Grammar explorer
      Vocabulary.tsx     Semantic search, flashcard drill, add-entry form
      Compare.tsx        Side-by-side LLM comparison
      Admin.tsx          Admin interface (review / history / export / contributions)
      MessageBubble.tsx  Chat bubble with thumbs-up/down and inline correction form
      BottomNav.tsx      Navigation bar
    services/api.ts      All fetch() calls — one file (Decision 10)
    store/               Zustand stores (conversation, vocabulary)
    config/ui.ts         Navigation, scenarios, sample prompts

app/                     Orchestration service
  main.py                FastAPI app setup and router registration
  telemetry.py           OTel tracing initialisation
  metrics.py             Prometheus metric definitions
  middleware.py          Request duration and count middleware
  logging_setup.py       Structured JSON logging
  services/
    llm.py               Agentic loop (tool use, multi-turn, streaming)
    tool_router.py       Dispatches tool calls to MCP servers
    db.py                asyncpg connection pool
    interactions.py      Interaction logging
    knowledge.py         Knowledge sharing service (sync status, export, approve/reject)
  routes/
    chat.py              POST /api/chat
    feedback.py          Feedback CRUD and review endpoints
    vocab.py             Vocabulary search and add proxy
    export.py            Training data export (SFT/DPO JSONL)
    admin_knowledge.py   Knowledge sharing admin endpoints
    health.py            GET /health

mcp-vocabulary/          Vocabulary MCP server
  main.py                FastAPI app + seeding on startup
  services/
    embed.py             Sentence-transformer embedding (all-MiniLM-L6-v2)
    seed.py              Seeds from data/vocabulary.json if table is empty
    db.py                asyncpg pool
  routes/
    lookup.py            POST /lookup (semantic search)
    vocab.py             POST /vocabulary (add entry)

mcp-grammar/             Grammar graph MCP server
  main.py                FastAPI app + seeding on startup
  services/
    embed.py             Sentence-transformer embedding
    seed.py              Seeds from data/grammar_nodes.json + grammar_edges.json
    db.py                asyncpg pool
  routes/
    traverse.py          POST /traverse (two-stage semantic + graph retrieval)

config/                  Runtime configuration (mounted, not baked in)
```
