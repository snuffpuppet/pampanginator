# Graph Report - .  (2026-04-11)

## Corpus Check
- Corpus is ~48,558 words - fits in a single context window. You may not need a graph.

## Summary
- 565 nodes · 655 edges · 88 communities detected
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 43 edges (avg confidence: 0.59)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Chat API and Schemas|Chat API and Schemas]]
- [[_COMMUNITY_Project Docs and Dependencies|Project Docs and Dependencies]]
- [[_COMMUNITY_LLM Tool Call Parser Tests|LLM Tool Call Parser Tests]]
- [[_COMMUNITY_App Entry Point and Middleware|App Entry Point and Middleware]]
- [[_COMMUNITY_Admin UI Actions|Admin UI Actions]]
- [[_COMMUNITY_Feedback API Tests|Feedback API Tests]]
- [[_COMMUNITY_Chat Endpoint Tests|Chat Endpoint Tests]]
- [[_COMMUNITY_Tool Router Tests|Tool Router Tests]]
- [[_COMMUNITY_Three-Layer Knowledge Architecture|Three-Layer Knowledge Architecture]]
- [[_COMMUNITY_Vocabulary Contribution Admin|Vocabulary Contribution Admin]]
- [[_COMMUNITY_Training Data Export Tests|Training Data Export Tests]]
- [[_COMMUNITY_Feedback Service|Feedback Service]]
- [[_COMMUNITY_Knowledge Sharing Service|Knowledge Sharing Service]]
- [[_COMMUNITY_Vocabulary Proxy Tests|Vocabulary Proxy Tests]]
- [[_COMMUNITY_DB Pool Tests|DB Pool Tests]]
- [[_COMMUNITY_Admin Endpoints|Admin Endpoints]]
- [[_COMMUNITY_Data Import and Embedding Pipeline|Data Import and Embedding Pipeline]]
- [[_COMMUNITY_Vocabulary Search Service|Vocabulary Search Service]]
- [[_COMMUNITY_Data Authority and Knowledge Governance|Data Authority and Knowledge Governance]]
- [[_COMMUNITY_Feedback Endpoints|Feedback Endpoints]]
- [[_COMMUNITY_LLM Completion Service|LLM Completion Service]]
- [[_COMMUNITY_Contribution Merge Script|Contribution Merge Script]]
- [[_COMMUNITY_OTel Logging Setup|OTel Logging Setup]]
- [[_COMMUNITY_Admin UI Event Handlers|Admin UI Event Handlers]]
- [[_COMMUNITY_Prometheus Metrics|Prometheus Metrics]]
- [[_COMMUNITY_Grammar and Vocab Export Scripts|Grammar and Vocab Export Scripts]]
- [[_COMMUNITY_DB Connection Pool|DB Connection Pool]]
- [[_COMMUNITY_Sentence Embedding Service|Sentence Embedding Service]]
- [[_COMMUNITY_Vocabulary Lookup Frontend|Vocabulary Lookup Frontend]]
- [[_COMMUNITY_Vocabulary Proxy Routes|Vocabulary Proxy Routes]]
- [[_COMMUNITY_Tool Router Service|Tool Router Service]]
- [[_COMMUNITY_Vocabulary Seeding|Vocabulary Seeding]]
- [[_COMMUNITY_Conversation History|Conversation History]]
- [[_COMMUNITY_OpenTelemetry Instrumentation|OpenTelemetry Instrumentation]]
- [[_COMMUNITY_Training Data Export Endpoint|Training Data Export Endpoint]]
- [[_COMMUNITY_Chat Message UI|Chat Message UI]]
- [[_COMMUNITY_Vocabulary UI|Vocabulary UI]]
- [[_COMMUNITY_Health Check Tests|Health Check Tests]]
- [[_COMMUNITY_Interaction Logging|Interaction Logging]]
- [[_COMMUNITY_Contribution Packaging Script|Contribution Packaging Script]]
- [[_COMMUNITY_Chat Input Bar|Chat Input Bar]]
- [[_COMMUNITY_Translation View|Translation View]]
- [[_COMMUNITY_Model Comparison View|Model Comparison View]]
- [[_COMMUNITY_Training Data Export Script|Training Data Export Script]]
- [[_COMMUNITY_Docker Compose Config|Docker Compose Config]]
- [[_COMMUNITY_Kapampangan Text Component|Kapampangan Text Component]]
- [[_COMMUNITY_Grammar View|Grammar View]]
- [[_COMMUNITY_Health Endpoint|Health Endpoint]]
- [[_COMMUNITY_Independent Service Lifecycles|Independent Service Lifecycles]]
- [[_COMMUNITY_Config Over Code Principle|Config Over Code Principle]]
- [[_COMMUNITY_Infrastructure Version Pinning|Infrastructure Version Pinning]]
- [[_COMMUNITY_Async Test Infrastructure|Async Test Infrastructure]]
- [[_COMMUNITY_Init Module|Init Module]]
- [[_COMMUNITY_Init Module|Init Module]]
- [[_COMMUNITY_Init Module|Init Module]]
- [[_COMMUNITY_Tailwind Config|Tailwind Config]]
- [[_COMMUNITY_Vite Config|Vite Config]]
- [[_COMMUNITY_PostCSS Config|PostCSS Config]]
- [[_COMMUNITY_React App Root|React App Root]]
- [[_COMMUNITY_Frontend Entry Point|Frontend Entry Point]]
- [[_COMMUNITY_Vite Env Types|Vite Env Types]]
- [[_COMMUNITY_UI Utilities|UI Utilities]]
- [[_COMMUNITY_Scenario Selector|Scenario Selector]]
- [[_COMMUNITY_Home View|Home View]]
- [[_COMMUNITY_Bottom Navigation|Bottom Navigation]]
- [[_COMMUNITY_Side Panel|Side Panel]]
- [[_COMMUNITY_Chat Window|Chat Window]]
- [[_COMMUNITY_Chat View|Chat View]]
- [[_COMMUNITY_Typing Indicator|Typing Indicator]]
- [[_COMMUNITY_Vocabulary Store|Vocabulary Store]]
- [[_COMMUNITY_Grammar Store|Grammar Store]]
- [[_COMMUNITY_Vocabulary Types|Vocabulary Types]]
- [[_COMMUNITY_Conversation Store|Conversation Store]]
- [[_COMMUNITY_Init Module|Init Module]]
- [[_COMMUNITY_Init Module|Init Module]]
- [[_COMMUNITY_Init Module|Init Module]]
- [[_COMMUNITY_Init Module|Init Module]]
- [[_COMMUNITY_Init Module|Init Module]]
- [[_COMMUNITY_Init Module|Init Module]]
- [[_COMMUNITY_Init Module|Init Module]]
- [[_COMMUNITY_Vocab Flat Grammar Graph Decision|Vocab Flat Grammar Graph Decision]]
- [[_COMMUNITY_FastAPI Decision|FastAPI Decision]]
- [[_COMMUNITY_Zustand State Decision|Zustand State Decision]]
- [[_COMMUNITY_Pure Display Components Decision|Pure Display Components Decision]]
- [[_COMMUNITY_API Calls Centralized Decision|API Calls Centralized Decision]]
- [[_COMMUNITY_Vocabulary Data Lifecycle|Vocabulary Data Lifecycle]]
- [[_COMMUNITY_App Test Dependencies|App Test Dependencies]]
- [[_COMMUNITY_Vocabulary Test Dependencies|Vocabulary Test Dependencies]]

## God Nodes (most connected - your core abstractions)
1. `MetricsMiddleware` - 9 edges
2. `_row()` - 9 edges
3. `_mock_pool()` - 9 edges
4. `GraphFragment` - 8 edges
5. `main()` - 8 edges
6. `_parse_sse_events()` - 8 edges
7. `Generative Grammar Rules (Section 6)` - 8 edges
8. `_OtelTraceFilter` - 7 edges
9. `_mock_http_client()` - 7 edges
10. `ChatRequest` - 7 edges

## Surprising Connections (you probably didn't know these)
- `Generative Grammar Rules (Section 6)` --semantically_similar_to--> `Layer 2: Verified Specific Forms (Grammar MCP Graph)`  [INFERRED] [semantically similar]
  app/config/system_prompt.md → ARCHITECTURE.md
- `mcp-grammar/CLAUDE.md (Grammar Service Instructions)` --semantically_similar_to--> `mcp-vocabulary/CLAUDE.md (Vocabulary Service Instructions)`  [INFERRED] [semantically similar]
  mcp-grammar/CLAUDE.md → mcp-vocabulary/CLAUDE.md
- `mcp-grammar Python Dependencies` --semantically_similar_to--> `mcp-vocabulary Python Dependencies`  [INFERRED] [semantically similar]
  mcp-grammar/requirements.txt → mcp-vocabulary/requirements.txt
- `mcp-vocabulary Data Provenance` --semantically_similar_to--> `mcp-grammar Data Provenance`  [INFERRED] [semantically similar]
  mcp-vocabulary/data/PROVENANCE.md → mcp-grammar/data/PROVENANCE.md
- `Minimal test app: all routes, no lifespan, no telemetry.` --uses--> `MetricsMiddleware`  [INFERRED]
  app/tests/conftest.py → mcp-vocabulary/middleware.py

## Hyperedges (group relationships)
- **Three-Layer Knowledge Synthesis: System Prompt + Grammar Graph + Vocabulary RAG → LLM Output** — architecture_layer1_system_prompt, architecture_layer2_grammar_graph, architecture_layer3_vocab_rag, architecture_mcp_grammar, architecture_mcp_vocabulary [EXTRACTED 1.00]
- **Shared Embedding Pipeline: sentence-transformers + pgvector across mcp-grammar and mcp-vocabulary** — dep_sentence_transformers, architecture_pgvector, architecture_mcp_grammar, architecture_mcp_vocabulary [EXTRACTED 0.95]
- **Feedback → Correction → Training Data Export Loop** — architecture_interaction_logging, architecture_training_data_export, architecture_authority_levels, readme_feedback_training [EXTRACTED 0.90]

## Communities

### Community 0 - "Chat API and Schemas"
Cohesion: 0.06
Nodes (42): BaseModel, chat(), chat_model_a(), chat_model_b(), _chat_with_model(), clear_session(), Returns the active backend and model names for display in the UI., Stream a response using the primary model (ACTIVE_MODEL from llm.yaml). (+34 more)

### Community 1 - "Project Docs and Dependencies"
Cohesion: 0.08
Nodes (33): AGENTS.md (Codex/Agent Instructions), OTel Instrumentation Pattern (init_telemetry ordering), Structural Rules (Skills Enforcement), Vite Dev Server Compare Page LLM Bypass, app Python Dependencies, app-postgres Database, App Service (Orchestration + React Frontend), grammar-postgres Database (+25 more)

### Community 2 - "LLM Tool Call Parser Tests"
Cohesion: 0.09
Nodes (5): mock_known_tools(), Unit tests for _try_parse_text_tool_call in services/llm.py.  This function dete, Patch get_tool_definitions so the parser sees vocabulary_lookup and grammar_look, Some models output: {"name": vocabulary_lookup, ...} without quotes on the value, test_unquoted_tool_name_value()

### Community 3 - "App Entry Point and Middleware"
Cohesion: 0.15
Nodes (10): BaseHTTPMiddleware, app(), client(), Shared test fixtures for mcp-vocabulary.  Creates a minimal FastAPI app with all, Minimal test app: all routes, no lifespan, no telemetry., Minimal test app: all routes, no lifespan, no embeddings., lifespan(), MCP Vocabulary Server  Connects to PostgreSQL at startup, loads the sentence-tra (+2 more)

### Community 4 - "Admin UI Actions"
Cohesion: 0.11
Nodes (2): readStream(), streamChat()

### Community 5 - "Feedback API Tests"
Cohesion: 0.11
Nodes (1): Tests for /api/feedback endpoints.  All database calls are mocked via services.f

### Community 6 - "Chat Endpoint Tests"
Cohesion: 0.14
Nodes (13): _parse_sse_events(), Tests for POST /api/chat and DELETE /api/chat/{session_id}.  All LLM and interac, Interaction log failures must never surface to the user., The schema accepts any role string; the LLM decides what to do with it., Parse SSE body into a list of data payloads (skip [DONE])., If LLM already mentions training knowledge, don't prepend the caveat., test_chat_caveat_not_doubled_when_already_in_response(), test_chat_emits_interaction_id() (+5 more)

### Community 7 - "Tool Router Tests"
Cohesion: 0.11
Nodes (5): Unit tests for services/tool_router.py.  Tests load_tools(), get_tool_definition, VOCABULARY_LOOKUP_ENDPOINT env var should override the YAML endpoint., Restore _tools to its original state after each test., reset_tool_state(), test_dispatch_endpoint_overridable_via_env()

### Community 8 - "Three-Layer Knowledge Architecture"
Cohesion: 0.13
Nodes (18): app/config/system_prompt.md (Ading Persona + Grammar Rules), Layer 1: Generative Grammar Rules (System Prompt), Layer 2: Verified Specific Forms (Grammar MCP Graph), Layer 3: Vocabulary with Semantic Context (Vocabulary MCP RAG), Rationale: Why Three-Layer Knowledge Architecture, Three-Layer Knowledge Architecture, Ading (Tutor Persona), Abakada Syllabary (Kapampangan) (+10 more)

### Community 9 - "Vocabulary Contribution Admin"
Cohesion: 0.12
Nodes (14): ContributionReviewBody, export_contributions(), ExportContributionsRequest, force_reseed(), get_pending_contributions(), Admin knowledge sharing routes — Decision 19.  Exposes endpoints for the admin C, Truncate and reseed vocabulary and grammar tables from canonical data files., Return pending contributions from the pending_contributions table. (+6 more)

### Community 10 - "Training Data Export Tests"
Cohesion: 0.29
Nodes (13): _mock_pool(), _parse_jsonl(), Tests for POST /api/export/training-data.  DB pool is mocked — no real database, Minimal dict-like mock of an asyncpg Record., _row(), test_export_content_disposition_header(), test_export_dpo_produces_chosen_rejected(), test_export_dpo_thumbs_up_is_skipped() (+5 more)

### Community 11 - "Feedback Service"
Cohesion: 0.16
Nodes (14): _apply_correction_to_vocabulary(), approve(), _feedback_row(), get_all(), get_pending(), Feedback capture and review service (Decision 15, 18).  Handles writing feedback, Mark feedback as reviewed=true, applied=true.      If correction_kapampangan is, Mark feedback as reviewed=true, applied=false. (+6 more)

### Community 12 - "Knowledge Sharing Service"
Cohesion: 0.14
Nodes (13): approve_contribution(), export_local_contributions(), get_pending_contributions(), get_sync_status(), load_ks_config(), Knowledge sharing service — sync status queries and contribution management.  Su, Trigger a full reseed on both MCP servers by calling their /admin/reseed endpoin, Fetch local (non-seeded) vocabulary and grammar entries from their respective se (+5 more)

### Community 13 - "Vocabulary Proxy Tests"
Cohesion: 0.22
Nodes (8): _mock_http_client(), Tests for /api/vocabulary endpoints (proxy to mcp-vocabulary).  All outbound htt, Return a mock httpx.AsyncClient that responds to `method` with the given payload, test_add_vocabulary_proxies_to_mcp(), test_add_vocabulary_sends_full_body(), test_search_vocabulary_passes_limit_and_authority(), test_search_vocabulary_proxies_to_mcp(), test_search_vocabulary_upstream_error_propagates_status()

### Community 14 - "DB Pool Tests"
Cohesion: 0.29
Nodes (9): Tests for mcp-vocabulary/services/db.py startup behaviour.  Verifies that connec, Ensure module-level _pool is None before and after each test., connect() wraps InvalidPasswordError with a diagnostic RuntimeError., connect() raises KeyError when DATABASE_URL is not set., connect() sets the module-level pool on success., reset_pool(), test_connect_raises_key_error_when_env_var_missing(), test_connect_raises_runtime_error_on_invalid_password() (+1 more)

### Community 15 - "Admin Endpoints"
Cohesion: 0.21
Nodes (10): export_local(), get_stats(), Admin endpoints for the vocabulary MCP server.  POST /admin/reseed  — truncates, Force a full reseed of the grammar_nodes and grammar_edges tables from canonical, Force a full reseed of the vocabulary table from data/vocabulary.json., Return local-addition counts for the orchestration app's sync status view., Return seeded and local-addition counts for the orchestration app's sync status, Export locally added grammar nodes and their edges (seeded_from_canonical = FALS (+2 more)

### Community 16 - "Data Import and Embedding Pipeline"
Cohesion: 0.32
Nodes (10): _build_vocab_embedding_text(), embed(), import_grammar_edges(), import_grammar_nodes(), import_vocabulary(), main(), Returns (imported, skipped). Called after nodes., Returns (imported, skipped). Called before edges. (+2 more)

### Community 17 - "Vocabulary Search Service"
Cohesion: 0.23
Nodes (10): add_entry(), _build_embedding_text(), lookup(), Vocabulary search service.  All searches run against the PostgreSQL vocabulary t, Insert a new vocabulary entry. Generates the embedding from the entry fields., Synchronous shim — do not use in new code. Use search() instead., Construct the embedding text for a vocabulary entry per Decision 12 format., Embed `query` and run cosine similarity search against vocabulary.embedding. (+2 more)

### Community 18 - "Data Authority and Knowledge Governance"
Cohesion: 0.24
Nodes (12): Authority Levels as First-Class Data Property (Decision 14), Shared Knowledge Model / Canonical Data Files (Decision 22), Training Data Export (Decision 16), mcp-grammar Data Provenance, Data Authority Levels (1-4 Scale), Knowledge Sharing Mode: git (default), Admin Interface (/admin), Feedback and Training Data Pipeline (+4 more)

### Community 19 - "Feedback Endpoints"
Cohesion: 0.18
Nodes (8): approve_feedback(), ApproveRequest, FeedbackRequest, pending_feedback(), Sets reviewed=true, applied=false. No correction is written., Returns all feedback where reviewed=false, ordered by timestamp descending., Sets reviewed=true, applied=true.     If correction_kapampangan is set on the re, reject_feedback()

### Community 20 - "LLM Completion Service"
Cohesion: 0.24
Nodes (10): complete(), _complete_openai_compatible(), complete_with_model(), init(), LLM service — reads config/llm.yaml and exposes a single complete() function.  S, Read llm.yaml, select the active backend, apply env var overrides., Send messages to the configured LLM backend, handle any tool calls, and return:, Complete using an explicit model override (used by comparison endpoints). (+2 more)

### Community 21 - "Contribution Merge Script"
Cohesion: 0.4
Nodes (8): load_json(), load_manifest(), main(), merge_grammar_edges(), merge_grammar_nodes(), merge_vocabulary(), Returns (merged_canonical, new_entries, conflicts).     conflicts: list of dicts, write_report()

### Community 22 - "OTel Logging Setup"
Cohesion: 0.36
Nodes (4): _OtelTraceFilter, Structured JSON logging with OpenTelemetry trace correlation.  Call setup_loggin, Inject service name, trace_id, and span_id into every log record., setup_logging()

### Community 23 - "Admin UI Event Handlers"
Cohesion: 0.22
Nodes (0): 

### Community 24 - "Prometheus Metrics"
Cohesion: 0.38
Nodes (4): metrics_endpoint(), Prometheus metrics for the vocabulary MCP service.  All metric definitions live, Expose metrics in OpenMetrics format. Must use openmetrics.exposition., Expose metrics in OpenMetrics format. Must use openmetrics.exposition.

### Community 25 - "Grammar and Vocab Export Scripts"
Cohesion: 0.43
Nodes (5): export_grammar_edges(), export_grammar_nodes(), export_vocabulary(), main(), Export edges where at least one endpoint is a locally added node.

### Community 26 - "DB Connection Pool"
Cohesion: 0.57
Nodes (4): connect(), disconnect(), pool(), Database connection pool for the vocabulary MCP server.  Provides a module-level

### Community 27 - "Sentence Embedding Service"
Cohesion: 0.38
Nodes (5): embed(), load(), Embedding service — loads sentence-transformers/all-MiniLM-L6-v2 once at startup, Load the model into memory. Must be called once at app startup., Embed a single string and return a 384-dimensional vector.      Raises RuntimeEr

### Community 28 - "Vocabulary Lookup Frontend"
Cohesion: 0.52
Nodes (6): buildVocabContext(), findRelevant(), getDatabaseSize(), isDatabaseLoaded(), load(), tokenise()

### Community 29 - "Vocabulary Proxy Routes"
Cohesion: 0.29
Nodes (6): add_vocabulary(), AddVocabularyRequest, Vocabulary proxy routes.  The frontend calls these endpoints on the orchestratio, Proxy to mcp-vocabulary GET /lookup?q=..., Proxy to mcp-vocabulary POST /vocabulary, search_vocabulary()

### Community 30 - "Tool Router Service"
Cohesion: 0.29
Nodes (5): dispatch(), get_tool_definitions(), Tool router — reads tools.yaml and dispatches tool calls to MCP servers.  At sta, Return tool definitions in the requested API format.      format="anthropic" — A, Send a tool call to its MCP server and return the response body.

### Community 31 - "Vocabulary Seeding"
Cohesion: 0.38
Nodes (5): _build_embedding_text(), Startup seeding for the vocabulary table.  Reads data/vocabulary.json (mounted a, Seed grammar graph from canonical data files if tables are empty or RESEED_ON_ST, Seed vocabulary from canonical data file if table is empty or RESEED_ON_STARTUP=, seed_if_needed()

### Community 32 - "Conversation History"
Cohesion: 0.4
Nodes (3): append(), Conversation history management.  Maintains per-session message history in memor, _truncate()

### Community 33 - "OpenTelemetry Instrumentation"
Cohesion: 0.6
Nodes (2): init_telemetry(), OpenTelemetry initialisation for the vocabulary MCP service.  Call init_telemetr

### Community 34 - "Training Data Export Endpoint"
Cohesion: 0.4
Nodes (4): export_training_data(), ExportRequest, Training data export endpoint.  Runs the export query and streams the result as, Query interactions joined to approved feedback and stream the result as     a JS

### Community 35 - "Chat Message UI"
Cohesion: 0.5
Nodes (0): 

### Community 36 - "Vocabulary UI"
Cohesion: 0.5
Nodes (0): 

### Community 37 - "Health Check Tests"
Cohesion: 0.5
Nodes (2): Health probe must not require DB or LLM — it should always respond., test_health_is_fast()

### Community 38 - "Interaction Logging"
Cohesion: 0.5
Nodes (3): log_interaction(), Interaction logging service (Decision 15).  After every LLM response, write a re, Insert a record into the interactions table.     Returns the new interaction id

### Community 39 - "Contribution Packaging Script"
Cohesion: 0.67
Nodes (1): main()

### Community 40 - "Chat Input Bar"
Cohesion: 1.0
Nodes (2): handleKeyDown(), handleSend()

### Community 41 - "Translation View"
Cohesion: 0.67
Nodes (0): 

### Community 42 - "Model Comparison View"
Cohesion: 1.0
Nodes (2): handleKey(), runComparison()

### Community 43 - "Training Data Export Script"
Cohesion: 1.0
Nodes (2): main(), run()

### Community 44 - "Docker Compose Config"
Cohesion: 0.67
Nodes (3): Docker Compose; Config and Data Mounted (Decision 6), Rationale: Composition Rule for Sub-Project Docker Compose, Shared Docker Network pampanginator (Decision 23)

### Community 45 - "Kapampangan Text Component"
Cohesion: 1.0
Nodes (0): 

### Community 46 - "Grammar View"
Cohesion: 1.0
Nodes (0): 

### Community 47 - "Health Endpoint"
Cohesion: 1.0
Nodes (0): 

### Community 48 - "Independent Service Lifecycles"
Cohesion: 1.0
Nodes (2): Independent Lifecycles Design Principle, Rationale: Why Three Separate Services

### Community 49 - "Config Over Code Principle"
Cohesion: 1.0
Nodes (2): Config Over Code (Decision 1), Thin Code Rich Data Design Principle

### Community 50 - "Infrastructure Version Pinning"
Cohesion: 1.0
Nodes (2): Pin Infrastructure Image Minor Versions (Decision 21), Rationale: Why Pin Infrastructure Image Versions

### Community 51 - "Async Test Infrastructure"
Cohesion: 1.0
Nodes (2): pytest-asyncio (async test runner), mcp-grammar Test Dependencies

### Community 52 - "Init Module"
Cohesion: 1.0
Nodes (0): 

### Community 53 - "Init Module"
Cohesion: 1.0
Nodes (0): 

### Community 54 - "Init Module"
Cohesion: 1.0
Nodes (0): 

### Community 55 - "Tailwind Config"
Cohesion: 1.0
Nodes (0): 

### Community 56 - "Vite Config"
Cohesion: 1.0
Nodes (0): 

### Community 57 - "PostCSS Config"
Cohesion: 1.0
Nodes (0): 

### Community 58 - "React App Root"
Cohesion: 1.0
Nodes (0): 

### Community 59 - "Frontend Entry Point"
Cohesion: 1.0
Nodes (0): 

### Community 60 - "Vite Env Types"
Cohesion: 1.0
Nodes (0): 

### Community 61 - "UI Utilities"
Cohesion: 1.0
Nodes (0): 

### Community 62 - "Scenario Selector"
Cohesion: 1.0
Nodes (0): 

### Community 63 - "Home View"
Cohesion: 1.0
Nodes (0): 

### Community 64 - "Bottom Navigation"
Cohesion: 1.0
Nodes (0): 

### Community 65 - "Side Panel"
Cohesion: 1.0
Nodes (0): 

### Community 66 - "Chat Window"
Cohesion: 1.0
Nodes (0): 

### Community 67 - "Chat View"
Cohesion: 1.0
Nodes (0): 

### Community 68 - "Typing Indicator"
Cohesion: 1.0
Nodes (0): 

### Community 69 - "Vocabulary Store"
Cohesion: 1.0
Nodes (0): 

### Community 70 - "Grammar Store"
Cohesion: 1.0
Nodes (0): 

### Community 71 - "Vocabulary Types"
Cohesion: 1.0
Nodes (0): 

### Community 72 - "Conversation Store"
Cohesion: 1.0
Nodes (0): 

### Community 73 - "Init Module"
Cohesion: 1.0
Nodes (0): 

### Community 74 - "Init Module"
Cohesion: 1.0
Nodes (0): 

### Community 75 - "Init Module"
Cohesion: 1.0
Nodes (0): 

### Community 76 - "Init Module"
Cohesion: 1.0
Nodes (0): 

### Community 77 - "Init Module"
Cohesion: 1.0
Nodes (0): 

### Community 78 - "Init Module"
Cohesion: 1.0
Nodes (0): 

### Community 79 - "Init Module"
Cohesion: 1.0
Nodes (0): 

### Community 80 - "Vocab Flat Grammar Graph Decision"
Cohesion: 1.0
Nodes (1): Vocabulary as Flat Records, Grammar as Typed Graph (Decision 4)

### Community 81 - "FastAPI Decision"
Cohesion: 1.0
Nodes (1): Python FastAPI Throughout (Decision 5)

### Community 82 - "Zustand State Decision"
Cohesion: 1.0
Nodes (1): Zustand for State Management (Decision 8)

### Community 83 - "Pure Display Components Decision"
Cohesion: 1.0
Nodes (1): Components as Pure Display Functions (Decision 9)

### Community 84 - "API Calls Centralized Decision"
Cohesion: 1.0
Nodes (1): All HTTP Calls in One File api.ts (Decision 10)

### Community 85 - "Vocabulary Data Lifecycle"
Cohesion: 1.0
Nodes (1): Vocabulary Data Lifecycle

### Community 86 - "App Test Dependencies"
Cohesion: 1.0
Nodes (1): app Test Dependencies

### Community 87 - "Vocabulary Test Dependencies"
Cohesion: 1.0
Nodes (1): mcp-vocabulary Test Dependencies

## Knowledge Gaps
- **124 isolated node(s):** `Expose metrics in OpenMetrics format. Must use openmetrics.exposition.`, `Inject service name, trace_id, and span_id into every log record.`, `Ensure module-level _pool is None before and after each test.`, `connect() wraps InvalidPasswordError with a diagnostic RuntimeError.`, `connect() raises KeyError when DATABASE_URL is not set.` (+119 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Kapampangan Text Component`** (2 nodes): `KapampanganText.tsx`, `KapampanganText()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Grammar View`** (2 nodes): `Grammar.tsx`, `handleAskAding()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Health Endpoint`** (2 nodes): `health.py`, `health()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Independent Service Lifecycles`** (2 nodes): `Independent Lifecycles Design Principle`, `Rationale: Why Three Separate Services`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Config Over Code Principle`** (2 nodes): `Config Over Code (Decision 1)`, `Thin Code Rich Data Design Principle`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Infrastructure Version Pinning`** (2 nodes): `Pin Infrastructure Image Minor Versions (Decision 21)`, `Rationale: Why Pin Infrastructure Image Versions`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Async Test Infrastructure`** (2 nodes): `pytest-asyncio (async test runner)`, `mcp-grammar Test Dependencies`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Init Module`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Init Module`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Init Module`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Tailwind Config`** (1 nodes): `tailwind.config.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Vite Config`** (1 nodes): `vite.config.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `PostCSS Config`** (1 nodes): `postcss.config.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `React App Root`** (1 nodes): `App.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Frontend Entry Point`** (1 nodes): `main.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Vite Env Types`** (1 nodes): `vite-env.d.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `UI Utilities`** (1 nodes): `ui.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Scenario Selector`** (1 nodes): `ScenarioSelector.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Home View`** (1 nodes): `Home.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Bottom Navigation`** (1 nodes): `BottomNav.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Side Panel`** (1 nodes): `SidePanel.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Chat Window`** (1 nodes): `ChatWindow.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Chat View`** (1 nodes): `Chat.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Typing Indicator`** (1 nodes): `TypingIndicator.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Vocabulary Store`** (1 nodes): `vocabulary.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Grammar Store`** (1 nodes): `grammar.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Vocabulary Types`** (1 nodes): `vocabulary.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Conversation Store`** (1 nodes): `conversation.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Init Module`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Init Module`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Init Module`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Init Module`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Init Module`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Init Module`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Init Module`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Vocab Flat Grammar Graph Decision`** (1 nodes): `Vocabulary as Flat Records, Grammar as Typed Graph (Decision 4)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `FastAPI Decision`** (1 nodes): `Python FastAPI Throughout (Decision 5)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Zustand State Decision`** (1 nodes): `Zustand for State Management (Decision 8)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Pure Display Components Decision`** (1 nodes): `Components as Pure Display Functions (Decision 9)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `API Calls Centralized Decision`** (1 nodes): `All HTTP Calls in One File api.ts (Decision 10)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Vocabulary Data Lifecycle`** (1 nodes): `Vocabulary Data Lifecycle`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `App Test Dependencies`** (1 nodes): `app Test Dependencies`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Vocabulary Test Dependencies`** (1 nodes): `mcp-vocabulary Test Dependencies`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `mcp-grammar Service` connect `Project Docs and Dependencies` to `Three-Layer Knowledge Architecture`?**
  _High betweenness centrality (0.003) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `MetricsMiddleware` (e.g. with `MCP Vocabulary Server  Connects to PostgreSQL at startup, loads the sentence-tra` and `Shared test fixtures for mcp-vocabulary.  Creates a minimal FastAPI app with all`) actually correct?**
  _`MetricsMiddleware` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `GraphFragment` (e.g. with `Two-stage retrieval as per Decision 13:      **Stage 1 — Semantic search:** embe` and `GET variant for quick browser or curl inspection. Same two-stage logic.`) actually correct?**
  _`GraphFragment` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Expose metrics in OpenMetrics format. Must use openmetrics.exposition.`, `Inject service name, trace_id, and span_id into every log record.`, `Ensure module-level _pool is None before and after each test.` to the rest of the system?**
  _124 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Chat API and Schemas` be split into smaller, more focused modules?**
  _Cohesion score 0.06 - nodes in this community are weakly interconnected._
- **Should `Project Docs and Dependencies` be split into smaller, more focused modules?**
  _Cohesion score 0.08 - nodes in this community are weakly interconnected._
- **Should `LLM Tool Call Parser Tests` be split into smaller, more focused modules?**
  _Cohesion score 0.09 - nodes in this community are weakly interconnected._