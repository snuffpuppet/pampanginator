# Kapampangan Language Tutor — Architecture Decision Record

> This document captures the design decisions for the Kapampangan language tutor
> application. It is intended as a briefing document for Claude Code to understand
> the intended architecture before building or extending the system.

---

## Project Overview

A Kapampangan language tutor application consisting of a React frontend, a Python
FastAPI orchestration layer, and two MCP (Model Context Protocol) servers providing
domain knowledge to a Claude LLM via the Anthropic API.

The system is designed around three principles:
- **Thin code, rich data** — logic lives in config and data, not in algorithms
- **Independent lifecycles** — grammar rules, vocabulary, and the LLM can each be
  improved without touching the others
- **Declarative over imperative** — intent should be readable without understanding
  the mechanism beneath it

---

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Compose                        │
│                                                         │
│  ┌──────────────┐     ┌──────────────────────────────┐  │
│  │   React App  │────▶│   FastAPI Orchestration      │  │
│  │  (frontend)  │     │   (app container)            │  │
│  └──────────────┘     │                              │  │
│                       │  - Assembles API calls       │  │
│                       │  - Manages conversation      │  │
│                       │    history (state)           │  │
│                       │  - Routes tool calls         │  │
│                       └──────────┬───────────────────┘  │
│                                  │                      │
│                    ┌─────────────┴──────────────┐       │
│                    │                            │       │
│          ┌─────────▼──────────┐   ┌─────────────▼────┐  │
│          │  MCP Vocabulary    │   │  MCP Grammar     │  │
│          │  Server            │   │  Graph Server    │  │
│          │  (RAG / JSON)      │   │  (Knowledge      │  │
│          │                    │   │   Graph)         │  │
│          └────────────────────┘   └──────────────────┘  │
│                                                         │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
                  Anthropic Claude API
                  (stateless LLM calls)
```

---

## Container Design

### Container 1 — App (React + FastAPI)

Serves the React frontend and runs the FastAPI orchestration layer.

Responsibilities:
- Serve the React chat UI
- Maintain conversation history per session (in-memory or Redis)
- Load tool configuration from `tools.yaml`
- Assemble each LLM API call: system prompt + RAG/graph results + conversation history + user message
- Parse agent tool call decisions and route to the appropriate MCP server
- Return LLM response to the frontend

### Container 2 — MCP Vocabulary Server (RAG)

A FastAPI service wrapping a JSON vocabulary index.

Responsibilities:
- Load and index the Kapampangan vocabulary JSON at startup
- Expose HTTP endpoints for vocabulary lookup
- Return structured vocabulary entries to the orchestration layer

### Container 3 — MCP Grammar Graph Server (Knowledge Graph)

A FastAPI service wrapping a JSON or SQLite knowledge graph of Kapampangan grammar.

Responsibilities:
- Load the grammar graph at startup
- Expose HTTP endpoints for graph traversal
- Return structured grammar data (aspect forms, focus types, related forms) to the orchestration layer

---

## Key Design Decisions

### Decision 1 — Config over code for tool routing

Tool definitions and routing logic live in a YAML file, not in Python. Adding a new
MCP tool means editing config, not code.

File: `config/tools.yaml`

```yaml
tools:
  - name: vocabulary_lookup
    description: Look up a Kapampangan word, its definition, aspect forms, and example sentences
    endpoint: http://mcp-vocabulary:8001/lookup
    parameters:
      - name: term
        type: string
        required: true
      - name: type
        type: string
        required: false
        description: "word | phrase | verb | noun"

  - name: grammar_lookup
    description: Traverse the grammar graph to find aspect forms, focus types, or related forms
    endpoint: http://mcp-grammar:8002/traverse
    parameters:
      - name: root
        type: string
        required: true
      - name: relationship
        type: string
        required: false
        description: "aspect_of | focus_type | related_form | derived_noun"
```

The orchestration layer reads this file at startup and passes the tool definitions
to the LLM API call. Claude then decides which tools to call based on the query.

### Decision 2 — LLM is stateless, state is managed by the orchestration layer

Every Anthropic API call is stateless. The conversation history is maintained by the
FastAPI app and sent with every call. The app is responsible for:
- Storing the message history per session
- Truncating or summarising history when it approaches the context window limit
- Prepending the system prompt on every call

No session state is held by the LLM or the MCP servers.

### Decision 3 — System prompt encodes persona and interaction rules only

As the MCP servers are built out, the system prompt should be progressively reduced
to persona and behaviour rules only. Grammar rules that can be represented in the
knowledge graph should migrate there. This keeps the system prompt stable and short,
reducing token cost per call.

Current system prompt file: `config/system_prompt.md`

### Decision 4 — Vocabulary as JSON, Grammar as graph

The vocabulary store is a flat JSON file — appropriate for definition lookup where
relationships between entries are not required.

The grammar store is a graph structure (nodes and edges) because Kapampangan grammar
is deeply relational. Verb roots relate to aspect forms, aspect forms relate to focus
types, focus types relate to grammatical rules. A flat structure cannot represent
these relationships for traversal.

For the initial build, the grammar graph can be implemented as a structured JSON
file with nodes and edges arrays. SQLite with relationship tables is the next step
if query complexity grows.

Grammar graph JSON structure:

```json
{
  "nodes": [
    { "id": "mangan", "type": "verb_root", "meaning": "to eat" },
    { "id": "mengan", "type": "verb_form", "meaning": "ate / has eaten" },
    { "id": "mamangan", "type": "verb_form", "meaning": "will eat" },
    { "id": "actor_focus", "type": "focus_type", "label": "Actor Focus" }
  ],
  "edges": [
    { "from": "mengan", "relationship": "COMPLETED_ASPECT_OF", "to": "mangan" },
    { "from": "mamangan", "relationship": "CONTEMPLATED_ASPECT_OF", "to": "mangan" },
    { "from": "mangan", "relationship": "BELONGS_TO_FOCUS", "to": "actor_focus" }
  ]
}
```

### Decision 5 — Python FastAPI throughout

All backend services use Python FastAPI. Chosen for:
- Decorator-based route definitions — intent is immediately readable
- Pydantic data models — declarative schema definitions, not validation logic
- Minimal boilerplate — no framework lifecycle to learn
- Native async support
- Excellent compatibility with AI/ML Python ecosystem
- Strong Claude Code familiarity

No Java, no Spring, no Camel, no heavyweight frameworks.

### Decision 6 — Docker Compose for local and production

All services run as Docker containers orchestrated by Docker Compose. One container
per service. Services communicate over the internal Docker network by service name.

The React frontend is built and served as static files by the FastAPI app container
(or via nginx in the same container). No separate container for the frontend in
production.

### Decision 11 — Two-mode operation: live reload in dev, container rebuild in prod

The system has two operating modes. Both are fully containerised — Node.js is not
required on the host in either mode.

**Dev mode** — `docker compose up` (no flags required)

Docker Compose automatically merges `docker-compose.yml` with
`docker-compose.override.yml` when no `-f` flag is given. The override file adds:

- A `frontend` container running the Vite dev server on port 5173, with the
  `frontend/` source directory mounted. Vite HMR picks up file changes instantly
  with no restart required.
- Volume mounts on `app`, `mcp-vocabulary`, and `mcp-grammar` that overlay the
  baked-in source with the live working directory. All three services run with
  `--reload` so Python changes also propagate without restart.

The Vite dev server middleware handles `/api/chat`, `/api/chat/anthropic`, and
`/api/chat/ollama` — this is the LLM communication layer in dev mode. Ollama, if
used, runs on the host and is reached from the frontend container via
`host.docker.internal`.

**Prod mode** — `docker compose -f docker-compose.yml up`

Passing `-f docker-compose.yml` explicitly skips the override file. The `app`
Dockerfile uses a multi-stage build: a Node.js stage compiles the frontend source
into static files, which are copied into the Python runtime stage. No source mounts,
no Vite dev server. The app container serves the built static files from `/app/frontend`.

The `/api/chat` streaming endpoints (backend selection, Anthropic/Ollama dispatch,
SSE response format) must be implemented in FastAPI for prod mode to have a working
LLM path. This is a known open item — until that work is done, prod mode does not
have end-to-end LLM communication.

### Decision 12 — Observability stack: Grafana + Tempo + Prometheus

The observability stack consists of four containers: `otel-collector`, `tempo`,
`prometheus`, and `grafana`.

Chosen over the Jaeger alternative referenced in the original architecture:
- Tempo integrates natively with Grafana (same organisation, shared datasource
  model) — traces and metrics live in one UI with exemplar links between them
- Prometheus + Grafana is the de facto standard for metrics in containerised
  workloads; adding Tempo to the same Grafana instance costs no additional UI
  complexity
- Jaeger is traces-only; metric/trace correlation requires additional tooling

Stack data flow:
- FastAPI services export spans via OTLP HTTP to `otel-collector:4318`
- The collector batches and forwards to `tempo:4317` (OTLP gRPC)
- Services expose a `/metrics` endpoint; Prometheus scrapes them on their
  respective ports
- Grafana reads from both Tempo (traces) and Prometheus (metrics), with
  exemplars linking individual metric data points to their originating traces

### Decision 13 — Infrastructure image versioning: pin minor versions, document upgrade path

Third-party infrastructure images (`grafana/tempo`, `grafana/grafana`,
`prom/prometheus`, `otel/opentelemetry-collector-contrib`) must be pinned to a
specific version tag in `docker-compose.yml`. Using `latest` is prohibited.

Rationale: `grafana/tempo:latest` resolved to 2.10.3 which introduced a
default-on Kafka ingestion path, breaking startup without config changes. This
was discovered during debugging, not at a deliberate upgrade. Breaking config
changes in minor versions of these projects are common and not always clearly
flagged in changelogs.

Pinning creates a deliberate upgrade decision: pull the new image, read the
migration notes, update any affected config files, and commit both together as
a single reviewable change with the version delta noted in the commit message.

---

## Project File Structure

```
kapampangan-tutor/
│
├── docker-compose.yml              # Service definitions
│
├── config/
│   ├── tools.yaml                  # MCP tool definitions and routing (declarative)
│   └── system_prompt.md            # LLM system prompt (persona + interaction rules)
│
├── app/                            # Container 1 — Orchestration + Frontend
│   ├── Dockerfile
│   ├── main.py                     # FastAPI app entry point
│   ├── routes/
│   │   ├── chat.py                 # /chat endpoint — handles conversation turns
│   │   └── health.py               # /health endpoint
│   ├── services/
│   │   ├── llm.py                  # Anthropic API call assembly and execution
│   │   ├── tool_router.py          # Reads tools.yaml, routes tool calls to MCP servers
│   │   └── history.py              # Conversation history management
│   ├── models/
│   │   └── schemas.py              # Pydantic data models
│   ├── frontend/                   # React build output (served as static files)
│   └── requirements.txt
│
├── mcp-vocabulary/                 # Container 2 — RAG Vocabulary Server
│   ├── Dockerfile
│   ├── main.py                     # FastAPI app entry point
│   ├── routes/
│   │   └── lookup.py               # /lookup/{term} endpoint
│   ├── services/
│   │   └── index.py                # Loads and searches the vocabulary JSON
│   ├── data/
│   │   └── vocabulary.json         # Kapampangan vocabulary store
│   └── requirements.txt
│
├── mcp-grammar/                    # Container 3 — Knowledge Graph Server
│   ├── Dockerfile
│   ├── main.py                     # FastAPI app entry point
│   ├── routes/
│   │   └── traverse.py             # /traverse endpoint
│   ├── services/
│   │   └── graph.py                # Loads graph, executes traversal queries
│   ├── data/
│   │   └── grammar_graph.json      # Kapampangan grammar knowledge graph
│   └── requirements.txt
│
└── frontend/                       # React source (built into app/frontend/)
    ├── src/
    │   ├── App.jsx
    │   ├── components/
    │   │   ├── ChatWindow.jsx
    │   │   ├── MessageBubble.jsx
    │   │   └── InputBar.jsx
    │   └── services/
    │       └── api.js              # Calls the FastAPI /chat endpoint
    └── package.json
```

---

## API Contracts

### POST /chat (Orchestration layer)

Request:
```json
{
  "session_id": "string",
  "message": "string"
}
```

Response:
```json
{
  "response": "string",
  "tools_used": ["vocabulary_lookup", "grammar_lookup"],
  "session_id": "string"
}
```

### GET /lookup/{term} (MCP Vocabulary Server)

Response:
```json
{
  "term": "mangan",
  "definition": "to eat",
  "part_of_speech": "verb",
  "focus_type": "actor_focus",
  "aspect_forms": {
    "progressive": "mangan",
    "completed": "mengan",
    "contemplated": "mamangan"
  },
  "examples": [
    { "kapampangan": "Mangan ta na!", "english": "Let's eat!" }
  ]
}
```

### POST /traverse (MCP Grammar Graph Server)

Request:
```json
{
  "root": "mangan",
  "relationship": "aspect_of"
}
```

Response:
```json
{
  "root": "mangan",
  "relationship": "aspect_of",
  "results": [
    { "node": "mengan", "relationship": "COMPLETED_ASPECT_OF" },
    { "node": "mamangan", "relationship": "CONTEMPLATED_ASPECT_OF" },
    { "node": "mangan", "relationship": "PROGRESSIVE_ASPECT_OF" }
  ]
}
```

---

## Docker Compose Configuration

```yaml
version: "3.9"

services:

  app:
    build: ./app
    ports:
      - "8000:8000"
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - VOCABULARY_SERVICE_URL=http://mcp-vocabulary:8001
      - GRAMMAR_SERVICE_URL=http://mcp-grammar:8002
    volumes:
      - ./config:/app/config        # Mount config directory so changes don't require rebuild
    depends_on:
      - mcp-vocabulary
      - mcp-grammar

  mcp-vocabulary:
    build: ./mcp-vocabulary
    ports:
      - "8001:8001"
    volumes:
      - ./mcp-vocabulary/data:/app/data   # Mount data so vocabulary can be updated without rebuild

  mcp-grammar:
    build: ./mcp-grammar
    ports:
      - "8002:8002"
    volumes:
      - ./mcp-grammar/data:/app/data      # Mount data so grammar graph can be updated without rebuild
```

Key design choice: config and data directories are **mounted as volumes**, not baked
into the container image. This means the system prompt, tool config, vocabulary JSON,
and grammar graph can all be edited and take effect on container restart — without
rebuilding the image. This honours the independent lifecycle principle.

---

## Observability

Implemented. See Decision 12 for stack rationale and Decision 13 for image
versioning policy.

Each MCP server call, Anthropic API call, and vocabulary/grammar lookup is a
traceable span. Latency visibility shows immediately whether slowness lives in
the grammar graph traversal, vocabulary lookup, or the LLM response itself.
Prometheus metrics with trace exemplars allow jumping directly from a slow
percentile on the Grafana dashboard into the specific trace that caused it.

---

## Future Considerations

These are known future directions, not current requirements.

**Workflow engines (Camunda / BPMN)** — if orchestration logic grows complex enough
to warrant visual modelling of process flows, a BPMN workflow engine becomes
appropriate. Not needed for this project at current scope.

**Functional / declarative languages** — Elixir (pipe-based data transformation),
Elm (frontend, no runtime errors), or Clojure (data-first) are worth exploring for
future projects where the logic complexity justifies the tradeoff against current LLM
training quality on those languages.

**Knowledge graph database** — if the grammar graph grows complex or query patterns
require deep traversal, migrate from JSON graph to SQLite with relationship tables,
then to Neo4j if scale demands it.

**Multi-language support** — the architecture is intentionally language-agnostic at
the orchestration layer. The system prompt, vocabulary MCP server, and grammar MCP
server are the language-specific components. A different language could be supported
by swapping those three components while reusing all orchestration logic.

---

## Frontend Architecture

The same architectural principles that govern the backend apply to the React
frontend: thin code, rich data, declarative over imperative, and clear separation
of concerns.

### Layer Separation

The frontend is strictly divided into three layers that never cross:

```
UI Layer      → React components — pure display, no logic, no API calls
State Layer   → Zustand store — what the app knows right now
Service Layer → api.js — how the app talks to the outside world
```

A component never makes an API call directly. A service never knows what a
component looks like. Every state change flows through a named, readable action
in the store.

```
ChatWindow.jsx          ← renders messages, reads from store only
    ↓ reads from
useConversation.js      ← manages state, calls services only
    ↓ calls
api.js                  ← handles all fetch calls, returns data only
```

Each layer is independently readable and testable without understanding the others.

### Decision 7 — Config over code for UI behaviour

UI scenarios, panel definitions, and content labels live in a YAML config file.
Adding a new conversation scenario means editing config, not JSX.

File: `config/ui.yaml`

```yaml
scenarios:
  - id: family
    label: Family Conversation
    icon: 🏠
    opening_prompt: "Practice a warm family dinner conversation"

  - id: professional
    label: Professional Context
    icon: 💼
    opening_prompt: "Practice a formal workplace introduction"

  - id: market
    label: At the Market
    icon: 🛒
    opening_prompt: "Practice buying food at a Pampanga market"

sidebar_panels:
  - grammar_notes
  - vocabulary_cards
```

The React app reads this config at startup and renders scenarios dynamically.
The component code does not change when scenarios are added or removed.

### Decision 8 — Zustand for state management

State is managed in a single Zustand store. Every state change is a named,
readable action. No state is scattered across component-level useState hooks
for anything that crosses component boundaries.

Chosen over Redux (too much boilerplate) and scattered useState (too hard to
trace). The store is the single source of truth for what the app knows.

File: `frontend/src/store/conversation.js`

```javascript
const useConversation = create((set) => ({
  messages: [],
  isLoading: false,
  activeScenario: null,

  sendMessage: async (text) => {
    set({ isLoading: true })
    const response = await api.chat(text)
    set((state) => ({
      messages: [...state.messages,
        { role: 'user', content: text },
        response
      ],
      isLoading: false
    }))
  },

  setScenario: (scenario) => set({ activeScenario: scenario }),
  clearConversation: () => set({ messages: [] })
}))
```

Reading this file tells you everything the app can do — without reading a
single component.

### Decision 9 — Components as pure display functions

With state and services extracted, components are thin display functions only.
They receive props and render structure. No logic, no API calls, no state
management inside components.

```jsx
// components/MessageBubble.jsx
const MessageBubble = ({ role, content }) => (
  <div className={`bubble bubble--${role}`}>
    {content}
  </div>
)
```

This is the frontend equivalent of thin code. Anyone can read a component and
understand exactly what it renders without understanding the rest of the system.

### Decision 10 — All HTTP calls in one place

All API calls live in `services/api.js` and nowhere else. Components and the
store import from this file. If the backend URL or request format changes,
one file changes.

```javascript
// services/api.js
const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export const api = {
  chat: async (message, sessionId) => {
    const res = await fetch(`${BASE_URL}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, session_id: sessionId })
    })
    return res.json()
  }
}
```

### Updated Frontend File Structure

```
frontend/
├── config/
│   └── ui.yaml                     # Scenarios, panels, labels — declarative
├── src/
│   ├── services/
│   │   └── api.js                  # All HTTP calls, nothing else
│   ├── store/
│   │   └── conversation.js         # Zustand store — all app state and actions
│   ├── components/                 # Pure display components — no logic
│   │   ├── ChatWindow.jsx          # Renders message list from store
│   │   ├── MessageBubble.jsx       # Renders a single message
│   │   ├── ScenarioSelector.jsx    # Renders scenarios from ui.yaml
│   │   ├── SidePanel.jsx           # Renders grammar notes / vocab cards
│   │   └── InputBar.jsx            # Captures user input, calls store action
│   └── App.jsx                     # Wires store to components, reads ui.yaml
└── package.json
```

### Where to look when reviewing a change

| Type of change | Location |
|---|---|
| Display / layout change | `components/` |
| Behaviour / logic change | `store/conversation.js` |
| API integration change | `services/api.js` |
| New scenario or panel | `config/ui.yaml` |
| New component | `components/` + register in `App.jsx` |

No hunting through components for where an API call lives. No wondering what
triggers a state change. Each layer has one job and the location of every
change is predictable before you open a file.

### OTel extends to the frontend

The same OpenTelemetry instrumentation used in the backend can be extended to
the browser via `@opentelemetry/sdk-web`. A single user interaction then
produces one complete trace from button click → FastAPI → MCP server →
Anthropic API → response rendered. End-to-end latency is visible in one view.

---

## Build Order for Claude Code

Suggested implementation sequence:

1. Scaffold Docker Compose with three empty service containers
2. Build MCP Vocabulary Server — load JSON, expose `/lookup` endpoint, write Pydantic schemas
3. Build MCP Grammar Graph Server — load graph JSON, expose `/traverse` endpoint
4. Build FastAPI orchestration layer — read `tools.yaml`, assemble Anthropic API calls, route tool results
5. Connect conversation history management
6. Scaffold React frontend — create layer structure: `store/`, `services/`, `components/`
7. Implement `api.js` service layer — single fetch call to `/chat`
8. Implement Zustand store — `sendMessage`, `setScenario`, `clearConversation` actions
9. Implement components as pure display functions reading from store
10. Load `ui.yaml` in `App.jsx` — render scenarios dynamically
11. Wire Docker Compose volumes for config and data
12. End-to-end test: user message → tool call → MCP response → LLM response → UI

---

*Document generated from architectural design conversation. Treat as the authoritative
design intent for this project. Deviate only with explicit justification.*
