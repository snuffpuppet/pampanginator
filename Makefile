COMPOSE      := docker compose
# Tests run under a separate project name so they can coexist with a running
# dev stack. Empty env-file suppresses warnings about OPENROUTER_API_KEY etc.
TEST_COMPOSE := docker compose -f docker-compose.test.yml --env-file /dev/null -p pampanginator-test

.PHONY: test test-fast test-build up down

## Run the unit-test suite inside Docker (builds image on first run)
test:
	$(TEST_COMPOSE) run --rm test

## Run tests, stop on first failure
test-fast:
	$(TEST_COMPOSE) run --rm test python -m pytest tests -x -q

## Force-rebuild the test image (after changing requirements)
test-build:
	$(TEST_COMPOSE) build --no-cache test

## Start the full dev stack
up:
	$(COMPOSE) up

## Stop the dev stack
down:
	$(COMPOSE) down
