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

- `uv sync --all-extras --locked` — create or update the local virtual environment with the dev and recording extras.
- `uv run pytest -n auto` — run the complete suite in parallel with coverage; GPU tests skip when CUDA is unavailable and `perf` tests are deselected by default (`pytest -m perf --no-cov` runs them).
- `uv run ruff check .` / `uv run black --check src tests` / `uv run mypy src/townlet --show-error-codes` / `uv run python scripts/no_defaults_lint.py src/townlet/ --whitelist .defaults-whitelist.txt --ratchet .defaults-ratchet` — mirror the CI lint job.
- `npm ci && npm run dev` from `frontend/` — serve the visualization dashboard when validating inference pipelines.

## Coding Style & Naming Conventions

Python code follows Black formatting with a 140-character line limit and 4-space indentation. Keep imports sorted (Ruff enforces this), prefer type-hinted functions, and avoid hidden defaults so the no-defaults guard stays green. Use `snake_case` for functions and modules, `PascalCase` for classes, and suffix async utilities with `_async`. Frontend code should keep the existing Vue single-file component structure and ESLint defaults.

## Testing Guidelines

Pytest auto-discovers files named `test_*.py`, classes `Test*`, and functions `test_*`. Maintain ≥70% coverage by extending `tests/test_townlet/` alongside each feature, and mark CUDA-only scenarios with `gpu`. When reproducing bugs, add regression cases under `tests/test_townlet/regressions/` with fixtures in `fixtures/`. Use integration flows when the curriculum hand-off is involved.

## Commit & Pull Request Guidelines

Commit history uses Conventional Commit semantics (`feat(env): ...`, `fix(actions): ...`); continue that pattern with imperative subject lines under 72 characters. Every PR should outline functional impact, list test commands (`uv run pytest`, etc.), and link related issues. Provide screenshots when the UI changes, note migrations in `configs/`, and document behavioral shifts in `docs/` or the changelog as needed.

## Security & Configuration Tips

Load secrets via environment variables or `.env` files; never commit credentialized configs or generated databases (`test.db`) and large artifacts in `runs/`. Reuse the provided YAML configs instead of hard-coding paths, and validate new endpoints against `SECURITY.md` guidelines before exposing them in the API layer.
