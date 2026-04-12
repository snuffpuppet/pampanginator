# Kapampangan Language Tutor — Architecture Decisions

> Authoritative reference for all design decisions. Deviate only with justification.
> Implementation details (file structure, SQL schemas, API contracts, script usage)
> belong in README.md — this document captures principles and rationale only.

---

## Design Principles

- **Thin code, rich data** — logic lives in config and data, not in algorithms
- **Independent lifecycles** — grammar, vocabulary, and the LLM can each be improved without touching the others
- **Declarative over imperative** — intent should be readable without understanding the mechanism beneath it

---

## System Architecture

```
User browser
    ↓
app (port 8000)               Orchestration API + built React frontend
    │
    └── tyk-gateway (port 8080)       API gateway — MCP service ingress
            ├── mcp-vocabulary  (port 8001)    Vocabulary MCP server (pgvector semantic search)
            └── mcp-grammar     (port 8002)    Grammar graph MCP server (pgvector + graph traversal)

Developer tooling
    └── scalar (port 3500)            Interactive API catalog — browse and try-it-out all MCP APIs

Databases (each service owns its own — no sharing)
    ├── app-postgres     (port 5432)   interactions, feedback, pending_contributions
    ├── vocab-postgres   (port 5433)   vocabulary entries + embeddings
    └── grammar-postgres (port 5434)   grammar nodes, edges + embeddings

Observability
    ├── grafana        (port 3000)
    ├── prometheus     (port 9090)
    ├── tempo          (port 3200)
    ├── loki           (port 3100)
    ├── promtail
    └── otel-collector (port 4318)
```

---

## Monorepo Structure

The project is a monorepo of three independent services: `app/`, `mcp-vocabulary/`, and `mcp-grammar/`. Each has its own database, Dockerfile, data files, scripts, and tests. They share no code and no database.

**Why three separate services:**

The vocabulary, grammar, and orchestration layers have completely different rates of change and data concerns. Vocabulary expands constantly from user contributions. Grammar nodes are rarer, higher-authority additions. The orchestration layer changes with LLM features and UI work. Coupling them into a shared database would mean migrations that touch unrelated concerns, and coupling them into shared code would create accidental dependencies.

**Rule for contributors:** Most changes are bounded to a single subproject directory. If a change spans more than one of `app/`, `mcp-vocabulary/`, or `mcp-grammar/`, it is a cross-service change and requires more careful review of the service boundary.

For service-specific work, open Claude Code inside the service directory (`cd app && claude`, etc.). Open at the repo root only for cross-service changes.

**Composition rule:** Each sub-project's `docker-compose.yml` and `Makefile` are the single source of truth for that service. The root `Makefile` and `docker-compose.yml` orchestrate by delegating to sub-project Makefiles — they never duplicate service definitions. A change to a sub-project's compose or Makefile takes effect automatically in both standalone and full-stack modes without any corresponding change at the root. Docker Compose `include:` is not used because it requires v2.20+; instead, the root `Makefile up` target calls each sub-project `make up` in sequence, then starts the root-owned observability stack.

---

## Key Design Decisions

### Decision 1 — Config over code for tool routing and LLM backend

Tool definitions and routing live in `app/config/tools.yaml`. Adding a new MCP tool means editing config, not Python. The orchestration layer reads this file at startup and passes tool definitions to the LLM. The model decides which tools to call.

LLM backend selection, model name, token limits, and tool-calling capability live in `app/config/llm.yaml`. Switching models or disabling tool calls for a model that does not support them is a config edit and container restart — no code change.

**Implication:** Never hardcode tool names, model names, or endpoint URLs in Python. They belong in config.

---

### Decision 2 — LLM is stateless; state lives in the orchestration layer

Every LLM API call is stateless. Conversation history is maintained by the FastAPI app and sent with every call. No session state is held by the LLM or the MCP servers.

**Implication:** The orchestration layer owns history truncation, system prompt prepending, and session identity. Do not push state into the MCP servers.

---

### Decision 3 — System prompt encodes generative grammar rules AND persona

The system prompt carries two distinct responsibilities:

1. **Persona and interaction behaviour** — tone, correction style, encouragement, confidence signalling
2. **Generative grammar rules** — abstract structural patterns of Kapampangan that allow the LLM to reason about constructions not explicitly in the grammar graph

The grammar rules are not a temporary measure. They are a permanent, load-bearing component of every API call. If token cost is a concern, compress the persona section — not the grammar rules.

File: `app/config/system_prompt.md`

---

### Decision 3a — Three-Layer Knowledge Architecture

This is the core design tenet. Kapampangan is a low-resource language. LLMs have thin training data for it, which creates two problems that pull in opposite directions: the model cannot be trusted to recall correct forms from training alone, but it also cannot be replaced by a retrieval system — producing natural Kapampangan requires genuine linguistic reasoning.

The three-layer architecture addresses both simultaneously:

**Layer 1 — Generative grammar rules (system prompt)**
Encodes abstract structural patterns. Provides generalisation for uncovered constructions. Cannot guarantee correctness for irregular forms — rules describe the majority pattern, not every exception.

**Layer 2 — Verified specific forms (grammar MCP graph)**
Stores authoritative word forms for irregular forms, commonly confused constructions, and high-frequency roots where correct recall matters most. Provides recall accuracy for exceptions. Does not replace Layer 1 — the LLM still synthesises results into natural language.

**Layer 3 — Vocabulary with semantic context (vocabulary MCP RAG)**
Provides lexical coverage beyond training data: definitions, example sentences, cultural notes, domain vocabulary. Does not provide grammar — it is lexical, not structural.

**How the layers work together:**
```
System prompt rules   → generalisation for uncovered constructions
Grammar graph         → verified accuracy for irregular / high-stakes forms
Vocabulary RAG        → lexical coverage beyond training data
LLM                   → synthesises all three into natural language output
```

**When something goes wrong, identify which layer the error originates in before fixing:**
- Wrong form on a regular verb → system prompt rule may be unclear
- Wrong form on an irregular verb → form is missing from the grammar graph
- Correct forms, unnatural sentence → LLM synthesis limitation, model quality
- Unknown word → vocabulary RAG gap

**When adding to the grammar graph:**
Ask whether a capable LLM applying system prompt rules would reliably produce this form. If yes, it is regular and may not need to be in the graph. If no, it belongs in the graph as a verified override. Priority: irregular verb forms, commonly confused constructions, high-frequency roots.

**When selecting an LLM:**
The architecture does not compensate for a model with insufficient Kapampangan training. The minimum viable model is Claude Sonnet class or equivalent. Small locally-hosted models (sub-7B) are not suitable as the primary inference engine for this language.

---

### Decision 4 — Vocabulary as flat records, grammar as a typed graph

Vocabulary is a flat table. Relationships between vocabulary entries are not required for definition lookup.

Grammar is a typed directed graph (nodes and edges). Kapampangan grammar is deeply relational: verb roots relate to aspect forms, aspect forms relate to focus types, focus types relate to grammatical rules. A flat structure cannot represent these relationships for traversal.

---

### Decision 5 — Python FastAPI throughout

All backend services use Python FastAPI. Reasons: decorator-based routes are immediately readable, Pydantic models are declarative, minimal boilerplate, native async, strong AI/ML ecosystem fit. No Java, no Spring, no heavyweight frameworks.

---

### Decision 6 — Docker Compose; config and data mounted, not baked in

All services run as Docker containers. One container per service.

Config and data directories are volume-mounted, not baked into container images. The system prompt, tool config, LLM backend config, and canonical data files can be edited and take effect on container restart without rebuilding the image. This honours the independent lifecycle principle.

---

### Decision 7 — Config over code for UI behaviour

UI scenarios, panel definitions, and navigation labels live in `app/config/ui.yaml`. Adding a conversation scenario means editing config, not JSX. The React app reads this file and renders scenarios dynamically.

---

### Decision 8 — Zustand for state management

State lives in a Zustand store. Every state change is a named, readable action. No state is scattered across component-level `useState` for anything that crosses component boundaries.

---

### Decision 9 — Components as pure display functions

With state and services extracted, components are thin display functions. They receive props and render structure — no logic, no API calls, no internal state management. This is the frontend equivalent of thin code.

---

### Decision 10 — All HTTP calls in one file

All API calls live in `app/frontend/src/services/api.ts` and nowhere else. If the backend URL or request format changes, one file changes.

---

### Decision 11 — PostgreSQL with pgvector as the persistence layer

Each service has its own PostgreSQL instance with the pgvector extension. No shared databases between services.

pgvector adds native vector similarity search to PostgreSQL, meaning semantic lookup and relational queries run in the same database with standard SQL. No separate vector database service is required.

**Why not ChromaDB + SQLite + JSON files separately:**
Three storage systems means three backup strategies, three volume mounts, three failure modes. PostgreSQL with pgvector provides all capabilities in one well-understood, production-proven service.

---

### Decision 12 — Semantic vector search for vocabulary and grammar

Both MCP servers use semantic vector search rather than exact keyword matching.

A user asking "how do I say I'm starving" must match a vocabulary entry for "hungry". A user asking "past tense of mangan" must match a grammar node described as "completed aspect". Learners use varied, imprecise, English-centric language. Exact match fails them systematically.

Embedding model: `sentence-transformers/all-MiniLM-L6-v2` (384-dim, runs locally inside each MCP server container). No external API dependency for retrieval.

The embedding text for each entry is designed to match the natural language ways a user or the agent would describe what they are looking for — not just the linguistic label.

---

### Decision 13 — Two-stage retrieval for the grammar graph

The grammar MCP server uses two stages:

1. **Semantic entry point** — embed the query, find the most similar grammar nodes (what part of grammar is this about?)
2. **Graph traversal** — from the retrieved nodes, walk edge relationships (what relational context does the LLM also need?)

Returning a single matched node in isolation misses the point. The LLM needs to understand where that node sits in the grammar structure. Graph traversal in stage 2 is what produces genuinely useful grammatical context rather than just a single retrieved fact.

---

### Decision 14 — Authority levels as a first-class data property

Every vocabulary entry and grammar node carries an authority level (1–4). The system treats sources with different trust levels differently in retrieval and in the confidence the LLM expresses.

| Level | Source |
|---|---|
| 1 | Native speaker verified |
| 2 | Linguistic / academic source |
| 3 | Community sources |
| 4 | LLM inference (unverified) |

Level 1 grammar nodes override rule application unconditionally — the LLM does not attempt to generate a form when a verified form exists. Level 4 entries are flagged as unverified and the system explicitly invites correction.

---

### Decision 15 — Interaction logging and feedback capture

Every conversation turn is logged to PostgreSQL with full context: retrieved vocabulary entries, grammar nodes, authority levels, model version, system prompt version. A correction is only useful as training data if you know what information the model had when it produced the output.

Corrections are never auto-applied without human review. Human judgement stays in the loop.

---

### Decision 16 — Training data export

Interaction and feedback data is stored in raw format. Training formats (SFT JSONL, DPO preference pairs) are produced at export time. This preserves flexibility — training formats change depending on the model and fine-tuning approach, but raw data can be exported to any format.

Only reviewed and applied feedback is eligible for training data export. Authority level filtering ensures only sufficiently verified data enters the training corpus.

---

### Decision 17 — Vocabulary page (user-facing)

Vocabulary contribution is a first-class user feature, not admin-only. Users can search semantically, see near-miss results when no exact match exists, and add entries directly. Submitted entries are immediately searchable — no restart required.

---

### Decision 18 — Admin interface

The `/admin` route is password-gated via `VITE_ADMIN_PASSWORD`. Four tabs: Review (correction queue), History (full feedback log), Export (training data download), Contributions (knowledge sharing management). See README for full detail.

---

### Decision 19 — Two-mode operation: live reload in dev, container rebuild in prod

**Dev mode** (`docker compose up` from `app/`) — Starts FastAPI on `:8000` (source volume-mounted, `--reload`) and a Vite dev server on `:5173`. Browse the app at `:5173`; Vite proxies all `/api/*` requests to FastAPI at `:8000`. HMR works for the frontend; Python changes reload without rebuild. FastAPI serves no static files in dev — `:8000` is API-only.

**Prod mode** — The app `Dockerfile` uses a multi-stage build: Node.js compiles the frontend into `assets/`, the output is copied into the Python runtime stage at `/app/frontend`. FastAPI's `StaticFiles` mount activates when `assets/` is present, serving the full SPA from `:8000`. No separate frontend server required.

---

### Decision 20 — Observability: Grafana + Tempo + Prometheus + Loki

Chosen over Jaeger: Tempo integrates natively with Grafana, allowing traces and metrics in one UI with exemplar links between them. Loki + Promtail adds log aggregation in the same Grafana instance, completing traces + metrics + logs without a separate stack.

Data flow: services export spans via OTLP HTTP → otel-collector → Tempo. Services expose `/metrics` → Prometheus scrapes them. Promtail ships container logs → Loki. Grafana reads all three with exemplar click-through from latency charts to individual traces.

---

### Decision 21 — Infrastructure images: pin minor versions

Third-party infrastructure images must be pinned to a specific version tag in `docker-compose.yml`. Using `latest` is prohibited.

Reason: `grafana/tempo:latest` resolved to a version that introduced a Kafka-default ingestion path, breaking startup without config changes — discovered during debugging, not at a deliberate upgrade. Breaking config changes in minor versions of these projects are common and not clearly flagged.

Upgrade process: pull the new image, read migration notes, update affected config files, commit both together with the version delta in the commit message.

---

### Decision 23 — Shared Docker network for cross-project service discovery

All three sub-projects and the observability stack join an external Docker bridge network named `pampanginator`. This allows services in separate Docker Compose projects to reach each other by container name (`http://mcp-vocabulary:8001`, `http://otel-collector:4318`) rather than via host ports.

Each sub-project Makefile creates the network with `docker network create pampanginator 2>/dev/null || true` before starting its services, making standalone mode self-contained: `cd app && make up` works without any prior setup. The network persists between `make down` calls — it has no state and is recreated idempotently on the next `make up`.

Only the services that need cross-project visibility join `pampanginator`: the three application services (`app`, `mcp-vocabulary`, `mcp-grammar`) and `otel-collector`. Databases stay on their sub-project's private default network.

---

### Decision 22 — Shared Knowledge Model

The canonical knowledge base lives in version-controlled flat files in each service's `data/` directory. The PostgreSQL database is a materialised, queryable view of those files — not the source of truth.

- **Source of truth:** `mcp-vocabulary/data/vocabulary.json`, `mcp-grammar/data/grammar_nodes.json`, `mcp-grammar/data/grammar_edges.json`
- **Runtime store:** PostgreSQL, seeded from those files on startup
- **Contribution path:** local database → export → review → merge into files → repo

This mirrors how source code is managed. Contributors diverge locally, contributions are reviewed, approved changes are merged into the canonical files, and all instances reseed on next startup.

**Three operating modes** (selectable via config, data model is identical across all three):

| Mode | How |
|---|---|
| `git` (default) | Export a zip, commit to branch, submit PR; maintainer reviews and merges |
| `sync` | Canonical file hosted at a URL; contributors send packages to maintainer who publishes |
| `shared_db` | All instances write to a shared cloud PostgreSQL; maintainer approves via admin interface |

**Seeding behaviour:** vocab and grammar MCP servers check whether their tables are empty on startup. If empty, they seed from the data files. `RESEED_ON_STARTUP=true` forces a full reseed — use this after pulling updated canonical data files.

---

### Decision 24 — Contract-first API specification for MCP services

MCP service APIs are defined contract-first: a hand-authored OpenAPI YAML in `{service}/api/openapi.yaml` is the source of truth. Server stubs (FastAPI route ABCs + Pydantic models) are generated from it; handlers subclass the generated abstract classes and implement the business logic. The service consumes the contract; it does not produce it.

Reason: the API shape is read by at least three consumers — the service itself, the API gateway (Phase 2), and the dev portal — plus any generated clients. Whichever consumer authors the spec is authoritative and the others drift. Making the YAML the single upstream artifact eliminates that class of drift by construction, and extends the "declarative over imperative" and Decision 1 (config over code) principles from runtime config to the API surface itself.

**Scope:** applies to MCP services with external consumers (`mcp-vocabulary`, and `mcp-grammar` when it gains external clients). `app/` remains code-first — its HTTP surface is an implementation detail of the orchestration layer, not a contract.

**Mechanism:**

- **Generator:** `openapitools/openapi-generator-cli` pinned to a specific tag (per Decision 21), run via a dedicated `docker-compose.codegen.yml` — no host-side installs (per Decision 6).
- **Split:** `api/_generated/` holds regeneratable abstract-base classes and Pydantic models. `api/_generated/impl/` holds hand-written subclasses that provide the business logic; `impl/*` is listed in `.openapi-generator-ignore` so regeneration never clobbers it.
- **Drift gate:** `make generate` writes a SHA-256 of the spec to `api/_generated/.spec-hash`. A pytest check (`tests/test_generated.py`) fails if the live spec hash diverges from the recorded one, forcing the developer to regenerate and commit before CI passes. `make check-generated` provides the same gate outside the test suite.
- **Served spec:** FastAPI's `/openapi.json` is overridden to return the authored YAML verbatim, so gateway and portal see byte-identical bytes to what the generator consumed.

**Lifecycle:** edit `api/openapi.yaml` → `make generate` → implement any new abstract methods in `api/_generated/impl/` → commit all three (YAML, regenerated stubs, updated `.spec-hash`) in one PR. Adding an endpoint to the YAML without implementing it causes startup to fail with `TypeError: Can't instantiate abstract class`, surfacing the gap immediately rather than at request time.

---

### Decision 25 — API gateway as the single ingress for MCP services

All traffic from `app/` to MCP services is routed through Tyk Gateway OSS (`:8080`). MCP services remain directly accessible on their own ports for standalone development but in full-stack mode the gateway is the canonical entry point.

Reason: a single ingress point provides one place for cross-cutting concerns — CORS, rate limiting, observability, and future auth — without duplicating that logic in each service. It also makes the published API surface explicit: what the gateway routes is what consumers see.

**Components:**
- **Tyk Gateway OSS** (`tykio/tyk-gateway`, pinned tag) — the reverse-proxy. File-based API definitions in `gateway/apis/` (per Decision 6; per Decision 21).
- **Tyk Redis** — Tyk's internal state store. Internal network only; never exposed to host.
- **Scalar API Reference** (`scalarapi/api-reference`, pinned tag) — interactive API catalog at `:3500`. Reads each MCP service's `openapi.json` via the gateway and renders all published APIs in one sidebar with try-it-out.

**Location:** all three containers live in `gateway/docker-compose.yml`, a new top-level directory following the monorepo composition rule (Decision 23). `gateway/` owns its own compose and Makefile; the root `Makefile up` target delegates to it after bringing up the MCP services.

**Tyk API definitions are generated, not hand-authored** (extends Decision 24): `gateway/scripts/build_apis.py` reads each MCP service's `api/openapi.yaml` and emits a Tyk Classic API definition JSON. The same drift gate applies — `gateway/apis/.spec-hash` records the SHA-256 of each source YAML; `make check-generated` (and `tests/test_drift.py`) fail if the live spec no longer matches the recorded hash.

**Auth posture (dev):** keyless. Tyk enforces no API key in the default configuration. Rate limits are set in `gateway/policies/policies.json` but not enforced per-consumer. Future hardening — API keys, OAuth, per-consumer quotas — is a policy edit, not an architecture change.

**Standalone preserved:** `cd mcp-vocabulary && make up` continues to work without the gateway. The gateway routing is purely additive. `app/` falls back to direct-mode by setting `VOCABULARY_SERVICE_URL=http://mcp-vocabulary:8001`.
