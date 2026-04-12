COMPOSE      := docker compose
CODEGEN      := docker compose -f docker-compose.codegen.yml
TEST_COMPOSE := docker compose -f docker-compose.test.yml --env-file /dev/null -p mcp-vocabulary-test

.PHONY: up down logs build rebuild test test-fast test-build shell generate check-generated

## Start the mcp-vocabulary service + vocab-postgres (standalone dev)
up:
	docker network create pampanginator 2>/dev/null || true
	$(COMPOSE) up -d

## Stop the service
down:
	$(COMPOSE) down

## Build service images (incremental)
build:
	$(COMPOSE) build

## Rebuild all service images from scratch (no cache)
rebuild:
	$(COMPOSE) build --no-cache

## Show logs
logs:
	$(COMPOSE) logs -f

## Run the mcp-vocabulary test suite inside Docker
test:
	$(TEST_COMPOSE) run --rm test-mcp-vocabulary

## Run tests, stop on first failure
test-fast:
	$(TEST_COMPOSE) run --rm test-mcp-vocabulary python -m pytest tests -x -q

## Force-rebuild the test image (after changing requirements)
test-build:
	$(TEST_COMPOSE) build --no-cache test-mcp-vocabulary

## Open a shell in the running service container
shell:
	$(COMPOSE) exec mcp-vocabulary /bin/bash

## Regenerate api/_generated/ from api/openapi.yaml (Docker-only, no local install required)
generate:
	mkdir -p api/_generated
	$(CODEGEN) run --rm codegen
	python3 -c "import hashlib; print(hashlib.sha256(open('api/openapi.yaml','rb').read()).hexdigest())" \
	  > api/_generated/.spec-hash

## Fail if api/_generated/ is stale relative to api/openapi.yaml
check-generated:
	@mkdir -p /tmp/vocab-codegen-check
	@rm -rf /tmp/vocab-codegen-check/*
	@docker run --rm \
	  -v $(PWD)/api:/local/api:ro \
	  -v /tmp/vocab-codegen-check:/local/api/_generated \
	  openapitools/openapi-generator-cli:v7.10.0 \
	  generate \
	  --input-spec /local/api/openapi.yaml \
	  --generator-name python-fastapi \
	  --output /local/api/_generated \
	  --additional-properties=sourceFolder=.,fastapiImplementationPackage=impl,packageName=mcp_vocabulary_api \
	  > /dev/null 2>&1
	@diff -rq --exclude='.openapi-generator' api/_generated /tmp/vocab-codegen-check \
	  || (echo "\napi/_generated is stale — run 'make generate' and commit the result" && exit 1)
	@echo "api/_generated is up to date"
