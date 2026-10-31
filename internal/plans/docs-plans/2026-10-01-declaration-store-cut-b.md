# Declaration-store Cut B Implementation Plan

> Execute task by task with focused behavioral tests and independent review.

**Goal:** Compile all authored variables through one explicit declaration contract and typed observation scope.

**Architecture:** A single pack-scope VariablesConfig replaces the three historical DTO entry points.
Canonical declarations lower into registry descriptors and internal expression/item profile products.
Symbol resolution and token emission consume that same roster; cache load checks required scope and identity.

**Tech Stack:** Python 3.13, Pydantic 2, PyYAML, MessagePack, torch, pytest; existing differential harness.

**Prerequisites:** accepted PDR-0149; worktree `/tmp/hamlet-declaration-cut-b`, branch
`feat/declaration-store-cut-b`; independent `uv sync --frozen --all-extras` environment.
Baseline declaration/pack checks: 38 passed. Before evidence must be committed before source edits.
Authoritative acceptance: PRD-0003 (not the old Cut A hash-identical bar).

## Task 1 — Bank baseline and close the design

Files: create `docs/product/evidence/declaration-cut-b/before-hashes.json`,
`before-variable-products.json`, `before-variable-transports.json`, `before-cpu-traces.json`,
`before-resets.json`, command/provenance record; PRD-0003 and this plan.

1. Compile all 31 cases without cache at 599cad15; inventory every dataclass hash including
   each level and metadata.config_hash; capture descriptor and representative CPU state/step/reset.
2. Preserve provenance, counts and exact reproducible command. Confirm no source changes yet.
3. Independent review checks canonical model, fixed access policy, item limits and hash strategy.
4. Commit the plan and force-add ignored JSON evidence. Expected: no source/config/test diff.

## Task 2 — Typed token-binding scope

Files: `src/townlet/universe/dto/token_spec.py`, `universe/token_hashes.py`,
`universe/compiled.py`, `environment/observation_encoder.py`, `environment/token_publishers.py`;
related token/coherence/publisher tests under `tests/test_townlet/unit/` and `integration/`.

1. Add failing behavioral tests for scope-routing independent of ref shape; missing/invalid scope;
   registry declaration mismatch; invalid item profile; mixed publisher persistence.
2. Run tests and retain the expected failure reading.
3. Add required `SlotBinding.scope: VariableScope | None`; explicit null on non-variable bindings.
   Emit scope from declarations. Route publisher by scope and validate scope/descriptor agreement.
4. Persist required scope, bump compiled schema 1.26 to 1.27, enforce canonical cache bindings.
   Include scope in semantic observation identity; preserve compact payload and layout geometry.
5. Run focused tests, Ruff/Black/mypy as appropriate; independent specification and quality review.
6. Commit. No canonical variable frontend changes in this task, so attribution is separable.

## Task 3 — One variable DTO and compiler inventory

Create: `src/townlet/config/variables_config.py`.
Modify: `config/environment_config.py`, `vfs/profiles.py`, `vfs/schema.py`,
`universe/declarations.py`, `raw_configs_v21.py`, `compiler.py`, `pipeline.py`,
`compilers/vfs.py`, `compilers/observation.py`, `validation/references.py`,
`validation/limits.py`, `symbol_table.py`, and internal artifact serialization where required.
Delete obsolete profile authoring DTO and overlay parser once all callers are converted.

1. Add failing schema/frontend tests proving canonical payload acceptance, required init/lifetime,
   loud old-surface refusal and reference/collision provenance.
2. Implement PRD-0003 canonical fields. Example authorable value:

```yaml
variables:
  version: '1.0'
  evaluation_mode: mark_and_sweep
  debug_logging: false
  extents: {}
  item_profiles: [default_item]
  declarations:
  - id: day_phase
    scope: global
    type: scalar
    lifetime: persistent
    semantic_type: temporal
    exposed_to: [agent]
    initial_value: 0.0
    expression: tick
    normalization: {kind: cyclical_sin_cos, period: 24}
```

3. Register the complete canonical roster exactly once; qualify item identities and refuse
   duplicates with both origins. Remove setdefault/first-wins/dedup admission paths.
4. Compile expression/item products from the canonical roster. Preserve dependency ordering,
   supported expression context and runtime state semantics. Fixed internal roles are engine
   readable/writable plus current agent read policy, independent of transport/scope.
5. Update clock period authority to canonical global variable and keep Cut A refusal guarantees.
6. Convert every live pack explicitly; do not modify `oracle_fixtures` or `.oracle`. Preserve
   meaningful declaration order and runtime descriptions or attribute necessary descriptor changes.
7. Update executable tests/fixtures and remove tests specific to deleted authoring APIs. Add
   config-in witnesses for lifetime/reset, overlay write/reward, item qualifiers and exposure.
8. Run targeted config/compiler/VFS/token integration; inspect all pack hashes and trajectories.
9. Review and commit the coherent authoring change.

## Task 4 — Differential attribution and contract verification

Files: new Cut B comparison script/evidence; existing `townlet/oracle` register/matrix inputs;
focused register/matrix tests. Do not widen old DIV entries or alter frozen oracle fixtures.

1. Compare 31 cases to the banked Cut A result; retain each changed field/value and attribution.
2. Compare observations/actions/rewards/reset traces; no silent learned-world change allowances.
3. Record new DIV-014 (or next unused ID) using complete input byte deltas and measured
   descriptors/semantic scope hash changes. Scope-only layout bytes stay identical; any actual
   layout/environment movement needs separate bisect and explicit register explanation.
4. Run a CPU matrix against the verified existing clean frozen oracle worktree. Each CPU cell
   must AGREE or DIVERGED_AS_REGISTERED, no ENGINE_ERROR/UNREGISTERED_DIVERGENCE; exit 0.
5. Retain exact command/report and source commit. CUDA skips are recorded, not claimed passed.

## Task 5 — Documentation, gates, review and product checkpoint

Files: canonical compiler/config/VFS documentation; `docs/product/evidence/declaration-cut-b/acceptance.md`;
new acceptance PDR; tracker implementation, defect and separate acceptance issues.

1. Update active authoring examples and product claims; historical documents remain marked historical.
2. Run `.venv/bin/ruff check .`; `.venv/bin/black --check src tests`;
   `.venv/bin/mypy src/townlet --show-error-codes`;
   `.venv/bin/python scripts/no_defaults_lint.py src/townlet/ --whitelist .defaults-whitelist.txt`;
   `.venv/bin/python scripts/validate_compiler_cli.py`.
3. At the integration checkpoint run `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 .venv/bin/pytest`
   with repository default coverage. Expected: all selected tests pass and coverage >=70%.
4. Independent spec review precedes independent code-quality review. Resolve all blocking findings.
5. Commit implementation/evidence, integrate into local project-recovery-4 while preserving
   unrelated dirty skill refs, feature-push draft PR, read all hosted exact-tip results.
6. Record actual per-criterion evidence and product PDR; close issues only for established claims.
   No main merge, deployment or convergence claim is included.
