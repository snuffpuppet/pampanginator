COMPOSE    := docker compose
REPO_ROOT  := $(shell pwd)/..

# Python runner: whole monorepo mounted at /repo so path relationships are preserved.
# Script lives at /repo/gateway/scripts/build_apis.py; MONOREPO_ROOT = /repo.
PYTHON_RUN := docker run --rm \
  -v $(REPO_ROOT):/repo \
  python:3.12-alpine \
  sh -c "pip install pyyaml==6.0.2 -q 2>/dev/null && python /repo/gateway/scripts/build_apis.py"

.PHONY: up down logs generate check-generated

## Start the gateway stack (tyk-gateway + tyk-redis + scalar)
up:
	docker network create pampanginator 2>/dev/null || true
	@if [ ! -f portal/catalog.json ]; then \
	  echo "portal/catalog.json missing — running generate first..."; \
	  $(MAKE) generate; \
	fi
	$(COMPOSE) up -d

## Stop the gateway stack
down:
	$(COMPOSE) down

## Follow gateway logs
logs:
	$(COMPOSE) logs -f tyk-gateway

## Regenerate gateway/apis/*.json, gateway/portal/catalog.json, and gateway/apis/.spec-hash
## from MCP service openapi.yaml files. No local Python/pip install required.
generate:
	mkdir -p apis portal
	$(PYTHON_RUN)

## Fail if gateway artifacts are stale relative to their source openapi.yaml files.
## Compares stored SHA-256 hashes in apis/.spec-hash against live openapi.yaml files.
## Run 'make generate' to fix.
check-generated:
	@python3 -c " \
import hashlib, sys, os; \
hash_file = 'apis/.spec-hash'; \
repo_root = '$(REPO_ROOT)'; \
lines = open(hash_file).read().splitlines() if os.path.exists(hash_file) else []; \
assert lines, 'apis/.spec-hash not found — run make generate'; \
stale = [p for line in lines if line for sha, p in [line.split('  ', 1)] \
  if hashlib.sha256(open(os.path.join(repo_root, p), 'rb').read()).hexdigest() != sha]; \
(print('\\n'.join(f'{p}: hash mismatch' for p in stale)) or sys.exit(1)) if stale \
  else print('gateway artifacts are up to date') \
"
