# Hamlet Rescue Recovery Plan

> 📌 **Recovered from archive 2026-08-26 — a COMPLETED plan, retained only as test provenance.**
>
> This is a historical implementation plan, not current intent and not a description of shipped
> behaviour. It is out of the archive for one reason: live test files cite this exact path to
> explain which plan task they implement, and those citations must resolve.
>
> Read it as provenance for those tests. For what the system actually does now, use
> `README.md` and the HLD set in `docs/architecture/`.


> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Recover Hamlet around one verified golden path, while deciding explicitly which simulation/runtime responsibilities should move to Murk.

**Architecture:** Keep Hamlet's domain compiler, curriculum vocabulary, DAC/reward semantics, and training policy as the product layer. Treat `/home/john/murk` as the preferred future simulation substrate for spatial topology, tick execution, observation extraction, vectorized stepping, replay, and live-world plumbing, but do not start the swap until Hamlet has one measurable golden path.

**Tech Stack:** Python 3.13, `uv`, PyTorch, Gymnasium/PettingZoo-style environment surfaces, Hamlet `UniverseCompiler`, Hamlet `VectorizedHamletEnv`, Murk Rust/PyO3 engine and Python bindings.

**Prerequisites:**
- No feature work during rescue.
- No backwards compatibility accommodations; delete old paths and stale references when touched.
- Before implementation, finish dependency installation once with `uv sync --all-extras` or an equivalent project-approved setup command.

---

## Current Truth

The worktree was clean at the start of this pass: `git status --short --branch` returned `## main...origin/main`.

The executable Hamlet spine is:
- `src/townlet/universe/compiler.py`: `UniverseCompiler` loads v2.1 experiment roots, shared config files, optional `items.yaml`, and every `levels/<level>/{curriculum,bars,affordances,training,drive}.yaml`.
- `configs/default_curriculum/experiment.yaml`: declares five levels: `L0_0_minimal`, `L0_5_dual_resource`, `L1_full_observability`, `L2_partial_observability`, and `L3_temporal_mechanics`.
- `src/townlet/environment/vectorized_env.py`: `VectorizedHamletEnv` consumes a `CompiledUniverse`, derives runtime controls from the selected level, builds a Hamlet substrate, and exposes the environment state to training.
- `src/townlet/demo/runner.py`: `DemoRunner` compiles the config, requires explicit `level_name`, rejects `training_config_path` override, and wires environment, curriculum, exploration, population, checkpointing, and TensorBoard.
- `src/townlet/population/vectorized.py`: `VectorizedPopulation` owns Q-networks, target networks, replay buffers, exploration wiring, and training-loop state.

The CI gates to preserve are:
- `.github/workflows/tests.yml`: `uv sync --all-extras`, `uv run python scripts/validate_compiler_cli.py`, then `uv run pytest`.
- `.github/workflows/lint.yml`: `uv run ruff check .`, `uv run black --check src tests`, `uv run mypy src/townlet --show-error-codes`, and `python scripts/no_defaults_lint.py src/townlet/ --whitelist .defaults-whitelist.txt`.
- `.github/workflows/config-validation.yml`: `uv run python scripts/validate_compiler_cli.py`.

The docs/task surface is not implementation-ready as a unit. It contains active future work (`docs/zzz. archive/plans/task-002a-phase9-hex-1d-topologies.md`, `docs/zzz. archive/plans/task-002a-phase10-graph-substrate.md`, `docs/zzz. archive/tasks/TASK-005B-VFS2.md`, `docs/zzz. archive/tasks/TASK-006-SUBSTRATE-AGNOSTIC-VISUALIZATION.md`, `docs/zzz. archive/tasks/TASK-007-LIVE-TRAINING-VISUALIZATION.md`, `docs/tasks/TASK-008-MODEL-ABSTRACTION-AND-EXPORT.md`, `docs/tasks/TASK-009-ND-POMDP.md`) plus a concrete cleanup plan in `docs/zzz. archive/plans/2025-11-25-test-suite-dead-code-cleanup.md` identifying backwards-compatibility tests and fallbacks that violate current repo policy.

## Validation Run

Completed:
- `python scripts/no_defaults_lint.py src/townlet/ --whitelist .defaults-whitelist.txt`
- Result: scanned 136 Python files, loaded 110 whitelist patterns, reported "No defaults detected. Clean." with 777 whitelisted violations.

Attempted but stopped:
- `uv run python scripts/validate_compiler_cli.py`
- `uv run ruff check .`
- `uv run pytest`

Reason: this fresh environment began downloading the heavy runtime stack (`torch`, `tensorflow`, CUDA/NVIDIA wheels, etc.) and did not reach command execution during the planning timebox. The duplicate `uv` commands were stopped, then the representative compiler-validation probe was stopped after continued dependency installation. The implementation sprint must begin by completing dependency setup once, then rerun all gates from scratch.

## Murk Replacement Assessment

Answer to "how much of what we have now can be replaced by `/home/john/murk`": a lot of the engine, not the Hamlet product.

Replace candidates:
- Hamlet spatial substrate implementations and topology expansion plans: Murk already provides Line1D, Ring1D, Square4, Square8, Hex2D, Fcc12, and ProductSpace.
- Hamlet observation extraction internals: Murk exposes `ObsSpec -> ObsPlan -> flat f32 tensors` with masks, foveation, pooling, and batching.
- Hamlet vectorized environment hot path: Murk `BatchedVecEnv` steps N worlds and extracts observations in one Rust call with one GIL release.
- Replay/determinism plumbing: Murk has deterministic replay, per-tick snapshot hashing, and divergence reporting.
- Live/demo simulation backend: Murk has `LockstepWorld` for training and `RealtimeAsyncWorld` for live interaction.
- Future graph/hex/1D infrastructure plans: defer or delete Hamlet-native topology work unless a Murk gap is proven.

Keep in Hamlet:
- YAML experiment/curriculum vocabulary and `UniverseCompiler` semantics.
- DAC/reward composition and pedagogical curriculum levels.
- Brain/training policy, Q-network factories, exploration strategy, replay-buffer research code, and TensorBoard metrics until a Murk-backed adapter proves parity.
- Product docs that explain Hamlet pedagogy rather than low-level simulation machinery.

Not replaceable without new adapter work:
- Hamlet affordance semantics, meters/bars, item inventory behavior, and VFS/DAC expression semantics do not map directly onto Murk fields/propagators yet.
- Hamlet's PyTorch-specific `VectorizedPopulation` expects `VectorizedHamletEnv` behavior and tensors; Murk's Python surface is Gymnasium/Numpy-oriented.
- Existing checkpoints and run artifacts should be discarded rather than migrated if the engine changes.

Decision: implement one Hamlet golden path first, then build a Murk adapter spike. Do not continue expanding Hamlet-native substrate families before that spike.

## Rescue Classification

Core blockers:
- Establish one golden vertical path: config compile -> env instantiate -> reset -> short step/training loop -> checkpoint/inspection.
- Complete dependency setup and run the CI-equivalent gates locally.
- Remove policy-violating backwards-compatibility tests/fallbacks called out by `docs/zzz. archive/plans/2025-11-25-test-suite-dead-code-cleanup.md`.
- Reduce default curriculum golden path to a tiny deterministic rescue level or add a dedicated rescue config pack.

Delete or archive as stale:
- Native Hamlet topology expansion plans for 1D, Hex, Graph, and frontend topology visualization until Murk replacement is adjudicated.
- Backwards-compatibility tests, migration prose, and fallback code paths when encountered.
- Template bug/task files that are not real work items (`docs/zzz. archive/bugs/JANK-00-TEMPLATE.md`, `docs/zzz. archive/bugs/BUG-XX-TEMPLATE.md`) after confirming no local process depends on them.

Defer:
- Frontend visualization and live training UI.
- Model export and abstraction.
- Full ND/POMDP expansion.
- Reward-tensor provenance upgrades, unless the golden path is blocked by reward opacity.

Already fine enough for now:
- The no-defaults linter is executable and green.
- CI workflow intent is clear and should remain the acceptance gate.
- v2.1 experiment-root structure is the right compile boundary.

## Golden Path

Use a deliberately small first path:

`configs/default_curriculum` -> `L0_0_minimal` -> `UniverseCompiler.compile(..., primary_level="L0_0_minimal", use_cache=False)` -> `VectorizedHamletEnv.from_universe(..., num_agents=2, device="cpu")` -> reset -> 5 deterministic actions -> construct `VectorizedPopulation` only if env smoke passes -> run one short training loop capped at 1-2 episodes -> save and inspect one checkpoint.

If `L0_0_minimal` is not actually minimal enough, create `configs/rescue_smoke` and make that the golden path. Do not repair all default-curriculum levels before this single path works.

## Implementation Tranches

### Tranche 1: Golden-Path Smoke

**Files:**
- Modify or create tests under `tests/test_townlet/integration/`.
- Read: `scripts/validate_compiler_cli.py`, `src/townlet/universe/compiler.py`, `src/townlet/environment/vectorized_env.py`, `src/townlet/demo/runner.py`, `configs/default_curriculum/**`.
- Optional create: `configs/rescue_smoke/**` only if `L0_0_minimal` is too large or semantically incoherent for a smoke path.

**Steps:**
1. Complete dependency setup with `uv sync --all-extras`.
2. Add a focused integration test that compiles the rescue config with `use_cache=False`.
3. Run the test and confirm failure or pass.
4. If it fails, fix the earliest compiler/config boundary. Prefer deleting incoherent config surface over supporting both shapes.
5. Extend the test to instantiate `VectorizedHamletEnv`, reset, and step a tiny deterministic action sequence.

**Acceptance criteria:**
- `uv run python scripts/validate_compiler_cli.py configs/default_curriculum` or the new rescue config succeeds.
- A named smoke test passes on CPU without writing large run artifacts.
- The failure mode for level-directory validation remains loud and explicit.

**Verification commands:**
```bash
uv run python scripts/validate_compiler_cli.py configs/default_curriculum
uv run pytest tests/test_townlet/integration -k "golden or smoke" -q
python scripts/no_defaults_lint.py src/townlet/ --whitelist .defaults-whitelist.txt
```

### Tranche 2: Compiler Boundary Cleanup

**Files:**
- `src/townlet/universe/compiler.py`
- `src/townlet/universe/raw_configs_v21.py`
- `src/townlet/config/*`
- `tests/test_townlet/unit/universe/*`
- `tests/test_townlet/unit/config/*`

**Steps:**
1. Make the rescue config schema strict at the experiment-root boundary.
2. Delete any fallback/migration code encountered while fixing compile failures.
3. Add red/green unit tests for each compiler error that blocked Tranche 1.
4. Ensure `scripts/validate_compiler_cli.py` validates only real packs and expected-negative fixtures.

**Acceptance criteria:**
- Invalid config fails before runtime instantiation.
- Expected-negative config fixtures still fail for the documented reason.
- No new whitelist entries are required for default-like behavior.

**Verification commands:**
```bash
uv run pytest tests/test_townlet/unit/universe tests/test_townlet/unit/config -q
uv run python scripts/validate_compiler_cli.py
python scripts/no_defaults_lint.py src/townlet/ --whitelist .defaults-whitelist.txt
```

### Tranche 3: Runtime Contract Fixes

**Files:**
- `src/townlet/environment/vectorized_env.py`
- `src/townlet/population/vectorized.py`
- `src/townlet/demo/runner.py`
- `src/townlet/training/*`
- `tests/test_townlet/unit/environment/*`
- `tests/test_townlet/unit/population/*`
- `tests/test_townlet/integration/*`

**Steps:**
1. Make env reset/step return shapes, masks, rewards, dones, and info that match `VectorizedPopulation`.
2. Run a short `DemoRunner` path with 1-2 episodes, CPU, and a temporary checkpoint directory.
3. Fix checkpoint save/load only for the current format; reject old formats loudly.
4. Preserve TensorBoard/checkpoint behavior only if it does not block the tiny training loop.

**Acceptance criteria:**
- One short training loop runs end to end.
- One checkpoint is produced and can be inspected or loaded under the current format.
- Runtime shape mismatches fail with direct messages naming the field/config boundary.

**Verification commands:**
```bash
uv run pytest tests/test_townlet/unit/environment tests/test_townlet/unit/population -q
uv run pytest tests/test_townlet/integration -k "demo or checkpoint or golden" -q
uv run python scripts/validate_compiler_cli.py
```

### Tranche 4: Docs And Task Cleanup

**Files:**
- `docs/zzz. archive/plans/2025-11-25-test-suite-dead-code-cleanup.md`
- `docs/zzz. archive/plans/task-002a-phase9-hex-1d-topologies.md`
- `docs/zzz. archive/plans/task-002a-phase10-graph-substrate.md`
- `docs/tasks/*.md`
- `docs/bugs/*.md`
- `README.md`, `docs/README.md`, `CHANGELOG.md` as needed.

**Steps:**
1. Mark feature plans as frozen/deferred until the golden path and Murk adapter spike are complete.
2. Execute or close the backwards-compatibility cleanup plan.
3. Move obsolete plans to `docs/plans/archive/` or delete templates/stale artifacts when they are not useful evidence.
4. Update the rescue status in the docs index.

**Acceptance criteria:**
- Active docs no longer imply native Hamlet topology expansion is next.
- Backwards-compatibility cleanup is either complete or converted into concrete remaining tasks.
- The next implementation tranche is obvious from docs alone.

**Verification commands:**
```bash
rg -n "backward|backwards|compat|fallback|migration|deprecated|support both" src tests docs
uv run ruff check .
uv run black --check src tests
```

### Tranche 5: Murk Adapter Spike

**Files:**
- Create: `src/townlet/environment/murk_adapter.py`
- Create: `tests/test_townlet/integration/test_murk_adapter_smoke.py`
- Read: `/home/john/murk/crates/murk-python/python/murk/env.py`
- Read: `/home/john/murk/crates/murk-python/python/murk/batched_vec_env.py`
- Read: `/home/john/murk/docs/CONCEPTS.md`

**Steps:**
1. Add Murk as a local dev dependency only for the spike, or document the source-build prerequisite without committing dependency churn if packaging is not ready.
2. Build the smallest adapter that maps the rescue config to Murk `Config`, fields, `ObsEntry`, and action commands.
3. Prove reset/step parity for the rescue path: same observation length, action count, reward sign expectations, and termination/truncation behavior.
4. Decide: replace Hamlet runtime with Murk, keep Hamlet runtime temporarily, or fork the product around Murk.

**Acceptance criteria:**
- A Murk-backed smoke test runs without touching Hamlet's old substrate code.
- The adapter either proves enough parity to justify replacement or records concrete Murk gaps.
- Native topology expansion remains frozen unless this spike says Murk cannot cover it.

**Verification commands:**
```bash
uv run pytest tests/test_townlet/integration/test_murk_adapter_smoke.py -q
uv run ruff check src/townlet/environment/murk_adapter.py tests/test_townlet/integration/test_murk_adapter_smoke.py
```

## Stop/Go Gates

Gate 1: Do not touch frontend, model export, or new topology features until Tranche 1 passes.

Gate 2: Do not begin Murk replacement until a Hamlet golden path exists, unless Tranche 1 proves the current runtime is incoherent beyond a one-session repair.

Gate 3: Do not preserve old configs, old checkpoints, or legacy tests. Delete them or make them fail loudly.

Gate 4: Do not call the rescue complete until these commands have fresh results:
```bash
uv run python scripts/validate_compiler_cli.py
uv run pytest
uv run ruff check .
uv run black --check src tests
uv run mypy src/townlet --show-error-codes
python scripts/no_defaults_lint.py src/townlet/ --whitelist .defaults-whitelist.txt
```

## First Implementation Session

Start with Tranche 1 only. The first commit should be either:
- `test(rescue): add golden path smoke coverage`
- or `fix(config): make rescue smoke config compile`

Do not combine docs cleanup, Murk adapter work, and runtime fixes in the first commit. The first job is to make one path real enough that every later replacement decision has a measured baseline.
