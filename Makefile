COMPOSE      := docker compose
# Tests run under a separate project name so they can coexist with a running
# dev stack. Empty env-file suppresses warnings about OPENROUTER_API_KEY etc.
TEST_COMPOSE      := docker compose -f docker-compose.test.yml --env-file /dev/null -p pampanginator-test
TEST_COMPOSE_VOCAB   := docker compose -f mcp-vocabulary/docker-compose.yml --env-file /dev/null -p pampanginator-mcp-vocabulary-test
TEST_COMPOSE_GRAMMAR := docker compose -f grammar/docker-compose.dev.yml --env-file /dev/null -p pampanginator-grammar-test

.PHONY: test test-fast test-build test-vocab test-grammar test-all up down build

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
	docker compose -f docker-compose.test.yml --env-file /dev/null -p pampanginator-test run --rm test-grammar

## Run all three test suites (app, vocab, grammar)
test-all:
	$(TEST_COMPOSE) run --rm test
	$(TEST_COMPOSE) run --rm test-mcp-vocabulary
	$(TEST_COMPOSE) run --rm test-grammar

## Start the full dev stack
up:
	$(COMPOSE) up -d

## Stop the dev stack
down:
	$(COMPOSE) down

## Stop the dev stack
build:
	$(COMPOSE) build
