COMPOSE      := docker compose
TEST_COMPOSE := docker compose -f docker-compose.test.yml --env-file /dev/null -p mcp-vocabulary-test

.PHONY: up down logs test test-fast test-build shell

## Start the mcp-vocabulary service + vocab-postgres (standalone dev)
up:
	docker network create pampanginator 2>/dev/null || true
	$(COMPOSE) up -d

## Stop the service
down:
	$(COMPOSE) down

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
