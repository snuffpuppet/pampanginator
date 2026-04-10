# Kapampangan Language Tutor — Architecture Decision Record

> This document captures the design decisions for the Kapampangan language tutor
> application. It is intended as a briefing document for Claude Code to understand
> the intended architecture before building or extending the system.

---

## Project Overview

A Kapampangan language tutor application consisting of a React frontend, a Python
FastAPI orchestration layer, and two MCP (Model Context Protocol) servers providing
domain knowledge to a configurable LLM backend (Anthropic Claude or any
OpenAI-compatible model via Ollama).

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
                  LLM Backend
                  (Anthropic / Ollama — stateless calls)
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

### Decision 1 — Config over code for tool routing and LLM backend selection

Tool definitions, routing logic, and LLM backend capabilities live in YAML files,
not in Python. Adding a new MCP tool or switching LLM backends means editing config,
not code.

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

The orchestration layer reads `tools.yaml` at startup and passes tool definitions
to the LLM. The model then decides which tools to call based on the query.

The same principle applies to the LLM backend itself. Backend selection, model name,
token limits, and whether tool calling is enabled are declared in `config/llm.yaml`,
not in code:

```yaml
active_backend: anthropic   # overridden by BACKEND env var

backends:
  anthropic:
    api_type: anthropic
    model: claude-sonnet-4-6
    max_tokens: 1024
    tools_enabled: true

  ollama:
    api_type: openai_compatible
    base_url: http://host.docker.internal:11434
    model: llama3.2
    max_tokens: 1024
    tools_enabled: true
```

Switching backends, swapping models, or disabling tool calls for a model that does
not support them is a config edit and container restart — no code change. Adding a
new backend (e.g. a hosted OpenAI-compatible endpoint) means adding a config block
and, if the API wire format differs, a thin adapter in `llm.py`.

### Decision 2 — LLM is stateless, state is managed by the orchestration layer

Every LLM API call is stateless. The conversation history is maintained by the
FastAPI app and sent with every call. The app is responsible for:
- Storing the message history per session
- Truncating or summarising history when it approaches the context window limit
- Prepending the system prompt on every call

No session state is held by the LLM or the MCP servers.

### Decision 3 — System prompt encodes generative grammar rules AND persona

The system prompt carries two distinct and permanent responsibilities:

1. **Persona and interaction behaviour** — tone, correction style, encouragement,
   confidence signalling, scenario handling
2. **Generative grammar rules** — the abstract structural patterns of Kapampangan
   that allow the LLM to reason about constructions not explicitly covered by the
   grammar graph

The system prompt must never be reduced to persona only. The generative grammar
rules are a permanent, load-bearing component of every API call. They are not
a temporary measure to be migrated into the graph — they serve a fundamentally
different purpose to the graph and the two are complementary, not alternatives.

Current system prompt file: `config/system_prompt.md`

### Decision 3a — Three-Layer Knowledge Architecture (core design tenet)

This decision captures a fundamental constraint of using an LLM for a
low-resource language and explains why the system requires three complementary
knowledge layers rather than any single one.

#### Background — why this matters for Kapampangan

Kapampangan is a low-resource language. LLMs have seen relatively little
Kapampangan text during training. This means the model's internal linguistic
representations — the statistical patterns absorbed from exposure to text —
are thin compared to high-resource languages like English or Spanish.

This has two specific consequences that pull in opposite directions:

**Consequence 1:** The LLM cannot be trusted to recall correct Kapampangan
word forms from training memory alone. Irregular verb forms, complex focus
system interactions, and forms that do not follow predictable rules are
particularly at risk of confident hallucination.

**Consequence 2:** The LLM cannot be replaced by a data retrieval system.
Producing natural, contextually appropriate Kapampangan requires genuine
linguistic reasoning — knowing when a rule applies, how rules interact, and
what sounds natural versus merely correct. This reasoning capability cannot
come from data retrieval alone. It requires a model that has sufficient
language-specific training to synthesise retrieved facts into fluent output.

Neither problem alone is solvable by any single mechanism. The three-layer
architecture addresses both simultaneously.

#### The three layers

**Layer 1 — Generative grammar rules (system prompt)**

The system prompt encodes the abstract structural patterns of Kapampangan:
the verb focus system, aspect formation, pronoun ordering rules, case markers,
negation, ligatures, and the mandatory-pronoun constraint.

These rules are *generative* — a model that understands them can apply them
to words it has never encountered and reason about constructions not
explicitly stored anywhere in the data layer.

What this layer provides: **generalisation**. When a word or construction is
not in the grammar graph, the LLM falls back on these rules and produces a
reasonable attempt. For regular, predictable forms this is reliable. For
irregular forms the rules will fail — which is why Layer 2 exists.

What this layer cannot provide: guaranteed correctness for irregular and
unpredictable forms. Rules describe the majority pattern. A model applying
the -in- infix rule to an irregular root will produce a confidently wrong
answer. Rules cannot encode every exception.

**Layer 2 — Verified specific forms (grammar MCP graph)**

The grammar graph stores specific, authoritative word forms — particularly
irregular forms, commonly confused forms, and high-frequency roots where
correct recall matters most.

The graph is not a complete grammar engine. It does not replace the rules in
the system prompt. It stores the specific instances where rule application
would fail or be unreliable, providing the LLM with a verified answer to
retrieve rather than a rule to apply incorrectly.

What this layer provides: **recall accuracy for exceptions**. When the LLM
retrieves a form from the graph, it does not need to apply a rule — it has
the correct answer. This eliminates the class of errors that arise from
applying regular rules to irregular forms.

What this layer cannot provide: linguistic intuition or naturalness
judgements. The graph returns structured data. The LLM still has to synthesise
that data into natural language. If the model has thin Kapampangan training,
it may retrieve the correct form but assemble a stilted or unnatural sentence
around it.

**Layer 3 — Vocabulary with semantic context (vocabulary MCP RAG)**

The vocabulary RAG provides word definitions, example sentences, cultural
notes, domain-specific vocabulary, and usage context. It compensates for the
LLM's limited Kapampangan lexical coverage from training.

What this layer provides: **lexical grounding**. Words and phrases the model
may not know from training are available at query time, with usage examples
that give the model context for how to use them naturally.

What this layer cannot provide: grammar. The RAG is lexical, not structural.
It does not know that *mangan* belongs to actor focus or that its completed
aspect is irregular.

#### How the layers work together

The layers are complementary. Each covers what the others cannot:

```
System prompt rules   → generalisation for uncovered constructions
Grammar graph         → verified accuracy for irregular / high-stakes forms
Vocabulary RAG        → lexical coverage beyond training data
LLM                   → synthesises all three into natural language output
```

A query flows through all three layers simultaneously. The LLM receives the
system prompt rules, any graph results it retrieved, and any vocabulary
entries retrieved, and synthesises them into a response. The quality of that
synthesis depends on the LLM's underlying Kapampangan competence — which is
why model selection matters more than any architectural decision for this
language specifically.

#### Implications for building and maintaining the system

**When adding to the grammar graph:**

Ask: would a capable LLM applying the system prompt rules reliably produce
this form? If yes, the form is regular — it may not need to be in the graph.
If no, the form is irregular or high-risk — it belongs in the graph as a
verified override.

Priority for graph population: irregular verb forms, commonly confused
constructions, high-frequency roots, forms where the rule produces a
plausible but wrong answer.

**When modifying the system prompt:**

The grammar rules section is not optional and must not be shortened to reduce
token cost without explicit justification. Removing generative rules degrades
the system's ability to handle constructions not covered by the graph. If
token cost is a concern, reduce the persona section or compress examples —
not the grammar rules.

**When selecting an LLM:**

The architecture does not compensate for an LLM with insufficient Kapampangan
training. A weak model will fail to synthesise retrieved facts into natural
output regardless of how well-structured the retrieval is. For Kapampangan
specifically, the minimum viable model is Claude Sonnet class or equivalent.
Locally hosted small models (sub-7B parameters) are not suitable as the
primary inference engine for this language.

**When the system produces an error:**

Identify which layer the error originates in before attempting a fix:
- Wrong word form on a regular verb → system prompt rule may be unclear
- Wrong word form on an irregular verb → the form is missing from the graph
- Correct forms, unnatural sentence → LLM synthesis limitation, model quality
- Unknown word → vocabulary RAG gap
- Confident wrong answer on complex construction → LLM training limitation,
  may not be fixable by any data change

#### What this architecture cannot fix

Generation naturalness for complex constructions is bounded by the LLM's
Kapampangan training data. No amount of retrieved grammar data or rules
compensates for a model that has not seen enough Kapampangan to internalise
the feel of the language. This system is designed to be an effective learning
and assistance tool. It is not designed to replace native speaker review for
authoritative translation.

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

In dev mode, `/api/chat` is served by the FastAPI `app` container — the same code
path as production. The Vite dev server proxies to it. The Compare page's
`/api/chat/anthropic` and `/api/chat/ollama` endpoints are implemented as convenience
routes in the Vite middleware for direct per-backend comparison; they do not go
through the FastAPI agentic loop.

**Prod mode** — `docker compose -f docker-compose.yml up`

Passing `-f docker-compose.yml` explicitly skips the override file. The `app`
Dockerfile uses a multi-stage build: a Node.js stage compiles the frontend source
into static files, which are copied into the Python runtime stage. No source mounts,
no Vite dev server. The app container serves the built static files from `/app/frontend`.

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
│   ├── llm.yaml                    # LLM backend selection and capabilities (declarative)
│   ├── tools.yaml                  # MCP tool definitions and routing (declarative)
│   ├── system_prompt.md            # LLM system prompt (persona + interaction rules)
│   ├── otel-collector.yaml         # OTel collector pipeline config
│   ├── tempo.yaml                  # Tempo trace storage config
│   ├── prometheus.yaml             # Prometheus scrape targets
│   └── dashboard/                  # Grafana provisioning and dashboard JSON
│
├── app/                            # Container 1 — Orchestration + Frontend
│   ├── Dockerfile
│   ├── main.py                     # FastAPI app entry point
│   ├── telemetry.py                # OTel tracing init
│   ├── metrics.py                  # Prometheus metric definitions
│   ├── middleware.py               # Request duration/count middleware
│   ├── routes/
│   │   ├── chat.py                 # /chat endpoint — handles conversation turns
│   │   └── health.py               # /health endpoint
│   ├── services/
│   │   ├── llm.py                  # Agentic loop — reads llm.yaml, dispatches to configured backend
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
      - BACKEND=${BACKEND:-anthropic}           # selects active backend; overrides llm.yaml
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:-}
      - OLLAMA_URL=${OLLAMA_URL:-http://host.docker.internal:11434}
      - OLLAMA_MODEL=${OLLAMA_MODEL:-llama3.2}
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
into the container image. This means the LLM backend config, system prompt, tool config, vocabulary JSON,
and grammar graph can all be edited and take effect on container restart — without
rebuilding the image. This honours the independent lifecycle principle.

---

## Observability

Implemented. See Decision 12 for stack rationale and Decision 13 for image
versioning policy.

Each MCP server call, LLM backend call, and vocabulary/grammar lookup is a
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
LLM backend → response rendered. End-to-end latency is visible in one view.

---

## Build Order for Claude Code

Suggested implementation sequence:

1. Scaffold Docker Compose with three empty service containers
2. Build MCP Vocabulary Server — load JSON, expose `/lookup` endpoint, write Pydantic schemas
3. Build MCP Grammar Graph Server — load graph JSON, expose `/traverse` endpoint
4. Build FastAPI orchestration layer — read `tools.yaml` and `llm.yaml`, assemble LLM API calls, route tool results
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
