COMPOSE      := docker compose
# Tests run under a separate project name so they can coexist with a running
# dev stack. Empty env-file suppresses warnings about OPENROUTER_API_KEY etc.
TEST_COMPOSE      := docker compose -f docker-compose.test.yml --env-file /dev/null -p pampanginator-test
TEST_COMPOSE_VOCAB   := docker compose -f mcp-vocabulary/docker-compose.yml --env-file /dev/null -p pampanginator-mcp-vocabulary-test
TEST_COMPOSE_GRAMMAR := docker compose -f mcp-grammar/docker-compose.test.yml --env-file /dev/null -p pampanginator-grammar-test

.PHONY: test test-fast test-build test-vocab test-grammar test-all up down build \
        up-app up-vocab up-grammar down-app down-vocab down-grammar \
        logs-app logs-vocab logs-grammar

## Run the app unit-test suite inside Docker (builds image on first run)
test:
	$(TEST_COMPOSE) run --rm test

## Run app tests, stop on first failure
test-fast:
	$(TEST_COMPOSE) run --rm test python -m pytest tests -x -q

## Force-rebuild the app test image (after changing requirements)
test-build:
	$(TEST_COMPOSE) build --no-cache test

## Run the mcp-vocabulary service test suite
test-vocab:
	docker compose -f docker-compose.test.yml --env-file /dev/null -p pampanginator-test run --rm test-mcp-vocabulary

## Run the grammar service test suite
test-grammar:
	$(TEST_COMPOSE_GRAMMAR) run --rm test-mcp-grammar

## Run all three test suites (app, vocab, grammar)
test-all:
	$(TEST_COMPOSE) run --rm test
	$(TEST_COMPOSE_VOCAB) run --rm test-mcp-vocabulary
	$(TEST_COMPOSE_GRAMMAR) run --rm test-mcp-grammar

## Start the full dev stack — sub-projects first, then observability.
## All services join the 'pampanginator' Docker network and reach each other by name.
## Each sub-project can also be started standalone with 'make up' inside its directory.
up:
	docker network create pampanginator 2>/dev/null || true
	$(MAKE) -C app up
	$(MAKE) -C mcp-vocabulary up
	$(MAKE) -C mcp-grammar up
	$(COMPOSE) up -d

## Stop the dev stack — observability first, then sub-projects
down:
	$(COMPOSE) down
	$(MAKE) -C app down
	$(MAKE) -C mcp-vocabulary down
	$(MAKE) -C mcp-grammar down

## Build observability images (sub-project images build automatically on 'make up')
build:
	$(COMPOSE) build

## Start only the app service (standalone dev)
up-app:
	$(MAKE) -C app up

## Start only the vocabulary service (standalone dev)
up-vocab:
	$(MAKE) -C mcp-vocabulary up

## Start only the grammar service (standalone dev)
up-grammar:
	$(MAKE) -C mcp-grammar up

## Stop only the app service
down-app:
	$(MAKE) -C app down

## Stop only the vocabulary service
down-vocab:
	$(MAKE) -C mcp-vocabulary down

## Stop only the grammar service
down-grammar:
	$(MAKE) -C mcp-grammar down

## Follow logs for the app service
logs-app:
	$(MAKE) -C app logs

## Follow logs for the vocabulary service
logs-vocab:
	$(MAKE) -C mcp-vocabulary logs

## Follow logs for the grammar service
logs-grammar:
	$(MAKE) -C mcp-grammar logs
