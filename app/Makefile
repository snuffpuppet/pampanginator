COMPOSE      := docker compose
TEST_COMPOSE := docker compose -f ../docker-compose.test.yml --env-file /dev/null -p pampanginator-app-test

.PHONY: up up-frontend down logs build rebuild test test-fast test-build shell

## Start app + app-postgres + Vite dev server on :5173
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

## Run the app test suite inside Docker
test:
	$(TEST_COMPOSE) run --rm test

## Run tests, stop on first failure
test-fast:
	$(TEST_COMPOSE) run --rm test python -m pytest tests -x -q

## Force-rebuild the test image (after changing requirements)
test-build:
	$(TEST_COMPOSE) build --no-cache test

## Open a shell in the running app container
shell:
	$(COMPOSE) exec app /bin/bash
