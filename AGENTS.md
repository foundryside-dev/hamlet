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

<!-- filigree:instructions:v3.1.0:65e6fb25 -->
<!-- filigree:last-writer:filigree install -->
## Filigree Issue Tracker

`filigree` tracks tasks for this project. Data lives in `.filigree/`. Prefer
the MCP tools (`mcp__filigree__*`) when available; fall back to the `filigree`
CLI otherwise.

### Workflow

```bash
# At session start
filigree session-context                            # ready / in-progress / critical path

# Pick up the next startable issue (atomic claim + transition into its working status)
filigree start-next-work --assignee <name>
# ...or claim a specific issue
filigree start-work <id> --assignee <name>

# Do the work, commit, then
filigree close <id>
```

Use the atomic claim+transition verbs — `work_start` / `work_start_next`
(MCP) or `start-work` / `start-next-work` (CLI). Do **not** chain
`work_claim` (MCP) or `filigree claim` (CLI) with a subsequent status
update — the two-step form races against other agents; the combined verb is
atomic.

**Ready ≠ startable.** The working status is type-specific (tasks →
`in_progress`, features → `building`). Bugs start at `triage`, which has no
single-hop transition into work (`triage → confirmed → fixing`), so a triage
bug is *ready* but not directly *startable*: `work_start` on one returns
`INVALID_TRANSITION` naming the next status, and `work_start_next` skips it.
`work_ready` items carry a `startable` flag (plus a `next_action` hint when
false). Pass `advance=true` (MCP) / `--advance` (CLI) to walk the soft
transitions to the nearest working status automatically.

### Observations: when (and when not) to use them

`observation_create` is a fire-and-forget scratchpad for *incidental* defects — things
you notice *outside the scope of your current task* (a code smell in a
neighbouring file, a stale TODO, a missing test for an edge case you happened
to spot). Notes expire after 14 days unless promoted. Include `file_path` and
`line` when relevant. At session end, skim `observation_list` and either
`observation_dismiss` or `observation_promote` for what has accumulated.

**You fix bugs in your currently defined scope. You do NOT use observations
to finish work prematurely.** If a defect, gap, or follow-up belongs to your
current task, you own it — handle it as part of that task: fix it now, expand
the task's scope, file a proper issue with a dependency, or surface it to the
user. Filing it as an observation and closing the task is *not* completing
the task; it is shipping known-broken work and hiding the debt in a 14-day
expiring scratchpad. The test is "would I have noticed this even if I weren't
working on this task?" If no, it's task scope, not an observation.

### Priority scale

- P0: Critical (drop everything)
- P1: High (do next)
- P2: Medium (default)
- P3: Low
- P4: Backlog

### Reaching for tools

MCP tool schemas describe each tool; `filigree --help` and `filigree <verb>
--help` are the authoritative CLI reference. You do not need to memorise
either catalogue. The verbs you will reach for most:

- **Find work:** `work_ready`, `work_blocked`, `issue_list`, `issue_search`
- **Claim work:** `work_start`, `work_start_next`
- **Update:** `comment_add`, `label_add`, `issue_update`, `issue_close`
- **Admin (irreversible):** `issue_delete` (MCP) / `delete-issue` (CLI) —
  hard-deletes a terminal issue and its rows; `admin_undo_last` cannot reverse it.
- **Scratchpad:** `observation_create`, `observation_list`, `observation_promote`, `observation_dismiss`
- **Cross-product entity bindings (ADR-029):** `entity_association_add`,
  `entity_association_remove`, `entity_association_list`,
  `entity_association_list_by_entity`. Used when a sibling tool (e.g.
  Loomweave) needs to bind a Filigree issue to a function, class, or
  module identifier it owns. The `entity_id` is an opaque external string
  from Filigree's perspective and may be a `loomweave:eid:...` SEI or a legacy
  locator; callers may also supply `entity_kind` explicitly. The consumer (the sibling tool's read
  path) does drift detection against the stored
  `content_hash_at_attach`. `entity_association_list_by_entity` is the
  reverse-lookup surface — given an opaque external entity ID, return every
  Filigree issue bound to it (project isolation is by DB file). Also
  reachable over HTTP as
  `GET/POST /api/issue/{issue_id}/entity-associations`,
  `DELETE /api/issue/{issue_id}/entity-associations?entity_id=…`,
  and `GET /api/entity-associations?entity_id=…`.
- **Health:** `stats_get`, `metrics_get`, `mcp_status_get`

Pass `--actor <name>` (CLI) so events attribute to your agent identity. It
works in either position — before the verb (`filigree --actor X update …`) or
after it (`filigree update … --actor X`); the post-verb value overrides the
group-level one.

### Error handling

Errors return `{error: str, code: ErrorCode, details?: dict}`. Switch on
`code`, not on message text. Codes: `VALIDATION`, `NOT_FOUND`, `CONFLICT`,
`INVALID_TRANSITION`, `PERMISSION`, `NOT_INITIALIZED`, `IO`,
`INVALID_API_URL`, `FILE_REGISTRY_DISPLACED`, `REGISTRY_UNAVAILABLE`,
`LOOMWEAVE_REGISTRY_VERSION_MISMATCH`, `LOOMWEAVE_OUT_OF_SYNC`,
`BRIEFING_BLOCKED`, `STOP_FAILED`, `SCHEMA_MISMATCH`, `INTERNAL`.

On `INVALID_TRANSITION`, call `workflow_transition_list` (MCP) or
`filigree transitions <id>` to see what the workflow allows from here.

Two failure modes deserve a specific response:

- **`SCHEMA_MISMATCH`** — the installed `filigree` is older than the project
  database. The error message contains upgrade guidance. Surface it to the
  user; do not retry.
- **`ForeignDatabaseError`** — filigree found a parent project's database
  but no local `.filigree.conf`. Run `filigree init` in the current
  directory. Do **not** `cd` upward to a different project unless that was
  the actual intent.
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

<!-- warpline:instructions:v1.3.0 -->
## Warpline (temporal change-impact)

`warpline` answers "if I touch X, what breaks, and what must I re-verify?".
Prefer the MCP tools (`mcp__warpline__*`); fall back to the `warpline` CLI.

Call `warpline_change_list` (shim: `changed`) for a rev range first, then follow
its `next_actions` into `reverify` / `blast_radius`. A `completeness` of
`NO_SNAPSHOT` means warpline cannot see, NOT that nothing is affected.

Enrich-only, local-only, advisory: warpline never gates. The `warpline-workflow`
skill carries the full tool set, the closed vocabularies, and the loop.
<!-- /warpline:instructions -->
