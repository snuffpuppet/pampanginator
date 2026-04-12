# API Gateway

Tyk Gateway OSS + Scalar API Reference for the Kapampangan Tutor monorepo.

## Ports

| Service | Host port | Purpose |
|---|---|---|
| `tyk-gateway` | `:8080` | API ingress — all MCP service traffic routes here |
| `scalar` | `:3500` | Interactive API catalog (browse & try-it-out) |

## Quick start

```bash
# From gateway/ (standalone)
make generate   # generates apis/*.json, portal/catalog.json, apis/.spec-hash
make up         # starts tyk-gateway + tyk-redis + scalar

# From monorepo root (full stack)
make up         # starts all services + observability + gateway
```

Browse the catalog: http://localhost:3500

## Architecture

The Tyk API definitions in `apis/` are **generated** from each MCP service's
`api/openapi.yaml` by `scripts/build_apis.py`. Never edit `apis/*.json` or
`portal/catalog.json` by hand — they will be overwritten on the next
`make generate`.

Source of truth → generated artifacts:

```
mcp-vocabulary/api/openapi.yaml  →  gateway/apis/mcp-vocabulary.json
                                 →  gateway/portal/catalog.json  (Scalar config)
                                 →  gateway/apis/.spec-hash       (drift gate)
```

## Drift gate

A pytest check (`tests/test_drift.py`) fails if any source `openapi.yaml` has
changed since the last `make generate` run. Rerun and commit:

```bash
make generate
git add gateway/apis/ gateway/portal/
git commit
```

## Updating the API (when mcp-vocabulary/api/openapi.yaml changes)

1. Edit `mcp-vocabulary/api/openapi.yaml`
2. `cd mcp-vocabulary && make generate`  (regenerates service stubs + spec-hash)
3. `cd ../gateway && make generate`      (regenerates Tyk def + Scalar catalog)
4. Commit all three: spec, service stubs, gateway artifacts
5. Restart the gateway: `make down && make up`

## Adding a new MCP service to the catalog

1. Ensure the service has `api/openapi.yaml` (follow Decision 24 in ARCHITECTURE.md)
2. Add an entry to the `SERVICES` list in `gateway/scripts/build_apis.py`
3. Run `make generate` → new `apis/{service}.json` and updated `portal/catalog.json`
4. Restart the gateway

## Standalone app without gateway

```bash
# From app/
VOCABULARY_SERVICE_URL=http://mcp-vocabulary:8001 make up
```
