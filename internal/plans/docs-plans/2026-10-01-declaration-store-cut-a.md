# Declaration-store Cut A Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task by task.

**Goal:** Discover every authored YAML document by content, merge declarations with source provenance, and preserve the current compiled semantics.

**Architecture:** A declaration store replaces filename dispatch and feeds the existing strict configuration DTOs. Existing wrapped sections and uniquely identifying bare configuration shapes are the closed authoring vocabulary; no legacy filename reader exists. Provenance uses family/scope/entity keys rather than transport filenames.

**Tech stack:** Python 3.13, PyYAML nodes, Pydantic, pytest, existing compiler and differential CPU harness.

**Prerequisites:** Isolated `/tmp/hamlet-declaration-cut-a` worktree, dedicated locked environment, implementation issue `hamlet-e62029114c` claimed atomically. The original untracked PRD is copied unchanged from the parent checkout. No source, configuration, test or script changes exist between baseline `ea3648db` and task starting HEAD `64f5d3f5`.

## Completion amendment

PDR-0149 records the owner-authorized extension to October 1 and accepts checkpoint
`75383d18`. The original planning assumptions below describe the pre-extension state.
The Cut A acceptance gate is now satisfied; technical scope and evidence requirements
remain unchanged.

## Acceptance contract

- The September 16 calendar window in PRD-0002 was missed. The October 1 instruction authorizes continuing the existing work; it does not retroactively satisfy that calendar criterion. Report functional acceptance separately from that expired window.
- Preserve every semantic hash in `docs/product/evidence/declaration-cut-a/before-hashes.json`: 31 discovered cases and 884 hash readings. Only `metadata.config_hash` may move on the two explicitly edited packs. A renamed-file test naturally changes transport identity while preserving semantic hashes.
- Preserve authored array order, which is part of the current ABI. Merge fragments in sorted pack-relative path/document order; do not sort existing arrays by entity name.
- Scope remains pack versus `levels/<id>`; arbitrary subfolders within either scope are transport. Required families are checked by declaration, not by filename. Every `.yaml`/`.yml` document outside `.compiled` is consumed or refused. Symlinks outside the pack are refused.
- Singleton declarations are identified by `(scope, family)`. Named catalog entries use their existing declared identifiers, qualified by family/profile; cascades use their ordered source/target pair. Duplicate declarations refuse even when equal. Repeated catalog structural headers must agree. Ordered appearance rules remain one singleton declaration because they have no rule identifier.
- Day length can explicitly reference a declared global ambient-tick temporal variable through `period_of`. Resolve it before constructing existing DTOs, keeping inactive levels null and preserving existing compiled values. Invalid or duplicated coupled clock facts refuse with both origins; do not redesign clocks.
- Existing serialization defects, variable semantics, access roles, environment, learner, rendering and convergence are separate work. If this cut requires semantic hash changes, stop and record the existing PDR-0147 reversal condition.

## Task 1: Bank the baseline

Files: `docs/product/evidence/declaration-cut-a/before-hashes.json`, this plan, copied PRD-0002.

1. Run `.venv/bin/pytest tests/test_townlet/integration/test_pack_smoke.py tests/test_townlet/unit/universe/test_source_map_wiring.py --no-cov -q` before source changes. Result: 36 passed.
2. Compile each smoke case without cache; capture all top-level and per-level hash fields plus metadata config hash. Result: 31 cases, 884 readings.
3. Commit the snapshot before the first production source edit. Retain the original `items_smoke` files in a refusal fixture before correcting the live pack.

Done when the committed snapshot is attributable to the original source and locked dependency environment.

## Task 2: Discovery, identity, merge and typed loading

Create `src/townlet/universe/declarations.py`; replace loading in `raw_configs_v21.py` and `loaders/preflight.py`; add discovery diagnostic codes in `error_codes.py`.
Test `tests/test_townlet/unit/universe/test_declaration_store.py`.

1. Write compiler-path tests that rename/move a drive document, combine documents in one file, introduce unknown documents, duplicate singleton/catalog identifiers, missing families and misplaced declarations. Require actual file:line origins, including both sides of collisions.
2. Run the new tests with `--no-cov`; observe failures because the old loader ignores renamed declarations or stray documents.
3. Implement recursive node-aware discovery, content classification and scoped merge into the existing DTOs; remove filename loading entirely from the compiler path. Preserve disabled item-catalog behavior in this semantics-preserving cut.
4. Run focused tests and the pack smoke suite. Expected: renamed and multi-document packs compile; malformed input yields structured errors; corrected shipped packs still reset/step.

Done when every discovered document has a disposition and declaration identity determines loading.

## Task 3: Source provenance through consumers

Modify `source_map.py`, `validation/limits.py`, `validation/semantics.py`, `validation/references.py`, `compiler.py`, compiler metadata/optimization diagnostics and CLI messages.
Tests: existing `test_source_map_wiring.py`, `test_resource_limits.py`, `test_compiler_cli.py`, plus new declaration diagnostics tests.

1. Pin failures after transport relocation: limits, vocabulary mismatch, nested DAC references and malformed DTO fields.
2. Observe red against filename-derived locations.
3. Bind diagnostics to declaration family/scope/entity origins and remove filename-dependent validation. Propagate discovery provenance once rather than reparsing canonical filenames.
4. Run the named focused tests; require actionable source locations and stable codes.

Done when all named PRD front-end/error families have provenance and no compiler filename selects semantic behavior.

## Task 4: Clock reference and forcing fixture

Modify `configs/default_curriculum/levels/L3_temporal_mechanics/curriculum.yaml` and comments in its root `vfs_profiles.yaml`. Correct only the original strays in `configs/test/items_smoke` after their refusal fixture is pinned.
Tests: declaration-store clock-reference tests and smoke/baseline comparison.

1. Test a declared clock-period reference, missing target, wrong target kind, ambiguous identity and conflicting literal duplication, with both origins.
2. Observe red, then implement resolution in the frontend without changing configuration/runtime DTO shapes.
3. Resolve the original numeric clock values and compare all semantic hashes with the committed snapshot.

Done when the single authored period controls L3 runtime time and clock token normalization, while every original effective value remains unchanged.

## Task 5: Authoring references and acceptance

Update `CLAUDE.md`, `docs/architecture/COMPILER.md` and affected live `docs/config-schemas/` references. Add an exact-tip acceptance record under `docs/product/evidence/declaration-cut-a/`.

1. Run focused compiler tests and the all-pack CLI validator, then compare every baseline hash. No unexpected movement is acceptable.
2. Run required integration gates: ruff, black, mypy, no-defaults guard, complete pytest, CPU differential matrix. Register only the approved input drift; preserve the oracle and prior divergence meanings.
3. Obtain independent code/acceptance review, resolve findings and run checks justified by fixes.
4. Commit, integrate into the parent recovery branch without touching unrelated dirty paths, and inspect hosted checks if pushed. Record local integration, push and hosted outcomes separately.
5. Read PRD criteria individually in `hamlet-41e79fb08b`; do not mark calendar acceptance passed or claim convergence.

Done when implementation and evidence are concrete and reviewable; Cut B starts only after this checkpoint's stated acceptance is resolved.
