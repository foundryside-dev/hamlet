# Repository Guidelines

## CRITICAL: Pre-Release Status - ZERO Backwards Compatibility Required

**THIS PROJECT IS PRE-RELEASE WITH ZERO USERS AND ZERO DOWNLOADS.**

**ABSOLUTE RULES:**

1. **NO backwards compatibility arrangements** - Delete old code paths immediately
2. **NO fallback mechanisms** - Breaking changes are free and encouraged
3. **NO deprecation warnings** - Just break things and update references
4. **NO migration paths** - Old configs/code should fail loudly, not be supported
5. **NO "support both old and new"** - Technical debt for a non-existent user base is inexcusable

## Project Structure & Module Organization

Core reinforcement-learning code lives in `src/townlet/` (`environment/`, `agent/`, `training/`). Config presets are under `configs/`, and runnable entry points (for example `scripts/run_demo.py`) sit in `scripts/`. Tests mirror the runtime layout: units in `tests/test_townlet/unit/`, integration and e2e flows beside them. The Vue observer UI is isolated in `frontend/`, and experiment artifacts belong in `runs/` but out of version control.

## Build, Test, and Development Commands

- `uv sync` — create or update the local virtual environment with dev extras.
- `uv run pytest` — execute the default suite (skipping `slow`) with coverage enabled.
- `uv run pytest -m "slow"` — opt into long-running or GPU-tagged scenarios before proposing major changes.
- `uv run ruff check` / `uv run black --check .` / `uv run mypy src` — mirror the CI lint pipeline.
- `npm install && npm run dev` from `frontend/` — serve the visualization dashboard when validating inference pipelines.

## Coding Style & Naming Conventions

Python code follows Black formatting with a 140-character line limit and 4-space indentation. Keep imports sorted (Ruff enforces this), prefer type-hinted functions, and avoid hidden defaults so the no-defaults guard stays green. Use `snake_case` for functions and modules, `PascalCase` for classes, and suffix async utilities with `_async`. Frontend code should keep the existing Vue single-file component structure and ESLint defaults.

## Testing Guidelines

Pytest auto-discovers files named `test_*.py`, classes `Test*`, and functions `test_*`. Maintain ≥70% coverage by extending `tests/test_townlet/` alongside each feature, and place heavyweight scenarios under `slow` or `gpu` markers so they stay opt-in locally. When reproducing bugs, add regression cases under `tests/test_townlet/regressions/` with fixtures in `fixtures/`. Use integration flows when the curriculum hand-off is involved.

## Commit & Pull Request Guidelines

Commit history uses Conventional Commit semantics (`feat(env): ...`, `fix(actions): ...`); continue that pattern with imperative subject lines under 72 characters. Every PR should outline functional impact, list test commands (`uv run pytest`, etc.), and link related issues. Provide screenshots when the UI changes, note migrations in `configs/`, and document behavioral shifts in `docs/` or the changelog as needed.

## Security & Configuration Tips

Load secrets via environment variables or `.env` files; never commit credentialized configs or generated databases (`test.db`) and large artifacts in `runs/`. Reuse the provided YAML configs instead of hard-coding paths, and validate new endpoints against `SECURITY.md` guidelines before exposing them in the API layer.

<!-- filigree:instructions:v3.2.0:c1c023c3 -->
<!-- filigree:last-writer:filigree install -->
## Filigree Issue Tracker

`filigree` tracks this project's work. Use it to find, claim, update and close
issues: `filigree session-context` at session start, then
`filigree start-next-work --assignee <name>`.

Full reference: the **filigree-workflow** skill (patterns, priorities,
observations, error codes), `filigree --help`, and the `mcp__filigree__*` tool
schemas. Prefer the MCP tools when available; fall back to the CLI.

Two rules `--help` will not tell you:

1. Claim atomically: `work_start` / `work_start_next` (MCP) or `start-work` /
   `start-next-work` (CLI). Never chain a claim with a separate status update;
   that two-step form races other agents.
2. On `SCHEMA_MISMATCH` the installed filigree is older than the project
   database. Surface it to the user; do not retry.
<!-- /filigree:instructions -->

<!-- loomweave:instructions:v1.5.0:39edbf6d -->
<!-- loomweave:last-writer:loomweave install -->
## Loomweave (code structure + SEI identity)

Loomweave pre-extracts this repo into a queryable map — entities, their
call/reference/import/relation edges, and subsystems — each carrying a Stable
Entity Identity (SEI). Ask its `mcp__loomweave__*` tools, not grep, for "what
calls X", "what subclasses X", "where is X defined", "find the thing that
does Y".

- Never hand-construct an entity id: take it from `entity_find` / `entity_at` /
  `entity_resolve`, and bind cross-tool records on the `sei`, not the `id`.
- If `project_status_get` reports stale, re-index before answering.

Full reference: `loomweave-workflow` skill, `loomweave --help`, MCP schemas.
<!-- /loomweave:instructions -->
