# Pampanginator

A Kapampangan language tutor with a pluggable LLM backend. The assistant, named **Ading** (younger sibling), teaches vocabulary, verb aspect morphology, grammar, and pronunciation through conversation. It grounds every answer in authoritative reference data rather than relying on the model's training knowledge alone.

The LLM backend is configurable — it runs against Anthropic's API (Claude) or a local model via Ollama. Both can be compared side by side in the Compare view.

---

## Services

```
User browser
    ↓
app (port 8000)               Serves built React frontend + tool-use API
    ├── mcp-vocabulary (port 8001)   Vocabulary index server
    └── mcp-grammar    (port 8002)   Grammar knowledge graph server
```

**app** — FastAPI service that owns the agentic tool-use loop. It maintains per-session conversation history, dispatches tool calls to the MCP servers, and serves the built React frontend as static files. The frontend is built before the Docker image is assembled (`npm run build` outputs to `app/frontend/`).

**mcp-vocabulary** — FastAPI service that loads `vocabulary.json` at startup and exposes a search endpoint. The LLM calls this whenever it needs to look up a Kapampangan word or English concept.

**mcp-grammar** — FastAPI service that loads `grammar_graph.json` at startup and exposes a graph traversal endpoint. The LLM calls this for any grammar question: verb aspects, focus types, pronouns, case markers, particles, and more.

### LLM backend (dev server)

The LLM communication layer lives in `frontend/vite.config.ts` as Vite dev server middleware. It handles `/api/chat`, `/api/chat/anthropic`, and `/api/chat/ollama`, and is where the Anthropic/Ollama backend selection happens. This middleware only runs during `npm run dev` — it is not included in the production build. The Compare view, which runs both backends side by side, also runs through this layer.

---

## Quick Start

### Prerequisites

- Docker and Docker Compose
- An Anthropic API key, or Ollama running locally on the host

No Node.js installation is required on the host machine.

### Configure the backend

Create a `.env` file in the project root:

```bash
# Use Anthropic (Claude)
BACKEND=anthropic
ANTHROPIC_API_KEY=your-key-here

# Or use a local Ollama model
# BACKEND=ollama
# OLLAMA_MODEL=llama3.2
# OLLAMA_URL=http://host.docker.internal:11434
```

### Dev mode (live reload)

```bash
docker compose up
```

Docker Compose automatically merges `docker-compose.yml` with
`docker-compose.override.yml`. The override adds a `frontend` container running the
Vite dev server with HMR, and mounts all service source directories so Python
changes reload without a restart.

Open `http://localhost:5173`.

### Prod mode (container rebuild)

```bash
docker compose -f docker-compose.yml up
```

Passing `-f` explicitly skips the override file. The app image is built using a
multi-stage Dockerfile: a Node.js stage compiles the frontend, the output is copied
into the Python runtime stage. No local Node.js required.

Open `http://localhost:8000`.

### API endpoints

| Service | Port | Key endpoints |
|---|---|---|
| app | 8000 | `POST /chat`, `DELETE /chat/{session_id}` |
| mcp-vocabulary | 8001 | `POST /lookup`, `GET /lookup/{term}`, `GET /status` |
| mcp-grammar | 8002 | `POST /traverse`, `GET /traverse/{root}`, `GET /status` |

### LLM endpoints (dev mode, via Vite dev server)

| Endpoint | Behaviour |
|---|---|
| `POST /api/chat` | Uses the backend configured in `.env` |
| `POST /api/chat/anthropic` | Always Anthropic (Compare page) |
| `POST /api/chat/ollama` | Always Ollama (Compare page) |
| `GET /api/status` | Returns active backend, model name, and key presence |

---

## Compare Page

The Compare view (`/compare`) sends the same question to both backends simultaneously and streams the responses side by side. This is useful for evaluating how a local Ollama model performs relative to Claude on Kapampangan-specific questions.

Both panels display elapsed response time. The status bar at the top shows which backends are available based on the current `.env` configuration — if the Anthropic key is absent the Claude panel will show an error; if Ollama is not running, its panel will prompt you to start it with `ollama serve`.

Neither panel uses tool calls — the comparison is a direct prompt-to-response measurement of the model's own Kapampangan knowledge.

---

## Observability Dashboard

Grafana loads automatically at `http://localhost:3000` (no login required).

The **Kapampangan Tutor** dashboard provides:

- **Request rate and error rate** across all three services
- **p50 / p99 latency** for end-to-end requests
- **LLM call duration** — time waiting for the Anthropic API, broken down by model
- **Token consumption** — input and output tokens per minute
- **Tool call rate** — how often vocabulary vs grammar lookups are triggered
- **Vocabulary hit/miss rate** — found vs not\_found, useful for identifying vocabulary gaps
- **Grammar traversal breakdown** — which relationship types are queried most
- **Live trace list** — recent traces from Tempo, click any to inspect the full span tree

Every histogram panel supports **exemplar click-through**: click a dot on a latency chart to open the exact trace for that request in Tempo.

### Tracing

Traces are stored in Tempo and accessible via the Grafana Explore view:

1. Open `http://localhost:3000`
2. Go to **Explore** → select the **Tempo** datasource
3. Search by service: `kapampangan-app`
4. Click any trace to see the full span tree: `app → mcp-vocabulary → mcp-grammar → Anthropic API`

### Prometheus

Raw metrics are available at `http://localhost:9090`. All three services expose a `/metrics` endpoint in OpenMetrics format.

---

## How the Vocabulary Server Works

At startup, `mcp-vocabulary` reads `mcp-vocabulary/data/vocabulary.json` and builds three in-memory indexes:

- **exact index** — Kapampangan word (lowercase) → entry
- **form index** — any inflected form → entry (covers all aspect forms, derived forms)
- **gloss index** — each significant English word in a definition → list of entries

When Claude calls `vocabulary_lookup`, the server searches these indexes in order: exact match first, then inflected form, then prefix, then English gloss. It returns up to six entries by default, including definition, part of speech, IPA pronunciation, aspect forms, example sentences, and etymology where available.

### Vocabulary data lifecycle

The vocabulary data originates from [kaikki.org](https://kaikki.org), which extracts structured JSON from Wiktionary. The fetch script at `frontend/src/` (or a separate scripts directory) downloads the Kapampangan subset and writes it to `mcp-vocabulary/data/vocabulary.json`.

Because the data directory is Docker-mounted (`./mcp-vocabulary/data:/app/data`), you can update `vocabulary.json` and restart just the vocabulary service without rebuilding the image:

```bash
# Update vocabulary data, then:
docker compose restart mcp-vocabulary
```

The server re-reads the file and rebuilds all three indexes on startup. No migration or schema change is required — the JSON structure is fixed by the kaikki.org extraction format.

---

## How the Grammar Server Works

At startup, `mcp-grammar` reads `mcp-grammar/data/grammar_graph.json` and builds an in-memory directed graph:

- **nodes** — grammar concepts and verb forms, each with an `id`, `word`, and metadata
- **out-edges** — indexed by `from` node id
- **in-edges** — indexed by `to` node id

When Claude calls `grammar_lookup`, it passes a root (a verb root like `mangan`, or a concept id like `actor_focus`, `demonstratives`, `absolutive_pronouns`) and an optional relationship filter. The server finds the node, collects all edges in both directions, optionally filters by relationship type, and returns the connected nodes with their relationship labels.

Supported relationship types: `aspect_of`, `focus_type`, `related_form`, `derived_noun`, `all`.

### Grammar data lifecycle

The grammar graph is handcrafted: it encodes Kapampangan verb morphology, the focus system (actor / object / goal / locative / circumstantial), pronoun sets, case markers, particles, demonstratives, and other grammatical structures as a network of typed relationships.

The data file lives at `mcp-grammar/data/grammar_graph.json` and is also Docker-mounted, so updates take effect on restart without a rebuild:

```bash
# Edit grammar_graph.json, then:
docker compose restart mcp-grammar
```

The graph has no external dependencies — it is a self-contained JSON file maintained alongside the codebase. Adding a new verb or grammar concept means adding nodes and edges to this file; no code changes are needed.

---

## Configuration

| File | Purpose |
|---|---|
| `config/system_prompt.md` | Ading's persona, language profile, and interaction rules |
| `config/tools.yaml` | Tool definitions loaded into every Anthropic API call |
| `config/otel-collector.yaml` | OTel collector pipeline (OTLP HTTP in → Tempo gRPC out) |
| `config/tempo.yaml` | Tempo trace storage config |
| `config/prometheus.yaml` | Prometheus scrape targets |
| `config/dashboard/datasources.yaml` | Grafana datasource provisioning (Tempo + Prometheus) |
| `config/dashboard/dashboards.yaml` | Grafana dashboard provisioning config |
| `config/dashboard/pampanginator-dashboard.json` | The Grafana dashboard definition |

The `config/` directory is mounted into the `app` container so changes to the system prompt and tool definitions take effect on a service restart — no image rebuild required.

---

## Project Layout

```
frontend/                React chat UI
  vite.config.ts         Dev server + LLM API middleware (Anthropic & Ollama)
  src/
    components/
      Chat.tsx           Main conversation interface
      Compare.tsx        Side-by-side LLM comparison view
      Grammar.tsx        Grammar explorer
      Vocabulary.tsx     Vocabulary browser and drill
    services/api.ts      All fetch() calls — one file per Decision 10
    config/ui.ts         Navigation, scenarios, sample prompts

app/                     Orchestration service (tool use + history)
  main.py                FastAPI app setup
  telemetry.py           OTel tracing init
  metrics.py             Prometheus metric definitions
  middleware.py          Request duration/count middleware
  services/
    llm.py               Agentic loop (tool use, multi-turn)
    tool_router.py       Dispatches tool calls to MCP servers
    history.py           Per-session conversation history (in-memory)
  routes/
    chat.py              POST /chat
    health.py            GET /health

mcp-vocabulary/          Vocabulary index server
  services/index.py      Three-index search implementation
  routes/lookup.py       GET /lookup/{term}, POST /lookup

mcp-grammar/             Grammar graph server
  services/graph.py      In-memory graph traversal
  routes/traverse.py     POST /traverse, GET /traverse/{root}

config/                  Runtime configuration (mounted, not baked in)
```
