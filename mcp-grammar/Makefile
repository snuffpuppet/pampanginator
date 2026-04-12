COMPOSE      := docker compose
TEST_COMPOSE := docker compose -f docker-compose.test.yml --env-file /dev/null -p mcp-grammar-test

.PHONY: up down logs build rebuild test test-fast test-build shell

## Start the mcp-grammar service + grammar-postgres (standalone dev)
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

## Run the mcp-grammar test suite inside Docker
test:
	$(TEST_COMPOSE) run --rm test-mcp-grammar

## Run tests, stop on first failure
test-fast:
	$(TEST_COMPOSE) run --rm test-mcp-grammar python -m pytest tests -x -q

## Force-rebuild the test image (after changing requirements)
test-build:
	$(TEST_COMPOSE) build --no-cache test-mcp-grammar

## Open a shell in the running service container
shell:
	$(COMPOSE) exec mcp-grammar /bin/bash
