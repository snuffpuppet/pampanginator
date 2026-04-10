# Kapampangan Tutor — Monorepo

## Structure
Three independent services in one repo. Each has its own database,
codebase, and lifecycle. No shared databases. No shared code.

  app/             — orchestration layer + React frontend + admin interface
  mcp-vocabulary/  — vocabulary MCP server
  grammar/         — grammar MCP server

## How to work here with Claude Code

For service-specific work, open Claude Code inside the service directory:
  cd app && claude
  cd mcp-vocabulary && claude
  cd grammar && claude

Open Claude Code at the repo root only for cross-service work (updating
docker-compose, changing API contracts between services, repo-wide changes).
Cross-service work should be rare — most changes are bounded to one service.

## Architecture
Read ARCHITECTURE.md at the repo root for the full design. It is the
authoritative reference for all decisions. Deviate only with justification.

## Skills
The following skills are installed and apply across all services:
- architecture-compliance: read before any structural change
- otel-instrumentation: read when modifying tracing
- otel-metrics: read when modifying metrics
