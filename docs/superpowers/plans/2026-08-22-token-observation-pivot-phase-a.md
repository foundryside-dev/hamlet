# Token-Observation Pivot — Phase A (brain override + set_encoder proof) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Unblock the owner-authoritative token-observation direction by landing its two
prerequisite units: level-overridable `brain.yaml` with legible lineage forks
(hamlet-0d0115383e, PDR-0027), and a config-in/behaviour-out proof that
`architecture.type: set_encoder` actually runs (first unit of hamlet-fa6bb6da4a, PDR-0017).

**Architecture:** Per-level `brain.yaml` is a *complete* replacement file (no partial merge —
partial merges need default semantics, which the No-Defaults Principle forbids); the compiler
selects `levels/<level>/brain.yaml` over the pack-root file when present, so
`CompiledUniverse.brain` becomes "the effective base brain for the compiled level".
Lineage legibility rides the existing provenance spine: a new `pack_brain_hash` beside the
existing effective `brain_hash`, stamped into checkpoints and surfaced at load. The
`set_encoder` proof is a committed test pack whose agent-profile `tensor2d` variable compiles
to the token observation field the network slices.

**Tech Stack:** Python 3.12, pydantic v2 DTOs (`ConfigDict(extra="forbid")`), torch, pytest,
uv. No new dependencies.

**Spec:** `docs/product/decisions/0017-…`, `0027-…`, `0044-…`, `0107-…`; filigree tickets
`hamlet-0d0115383e` (deliverables re-scoped by PDR-0027) and `hamlet-fa6bb6da4a` (first unit
only). This plan implements Phase A of the pivot; Phase B is gated on Task 5's outcome (see
"After this plan" at the bottom).

## Global Constraints

- **EXECUTION GATE — do not start while the corpus freeze holds.** PDR-0090 freezes
  `src/townlet/` for the duration of the N=9 idea-corpus trials and their blind re-runs.
  Execute this plan only after a PDR records the corpus complete (check
  `docs/product/decisions/` for a successor to PDR-0090, or ask the owner). Writing/reviewing
  this plan is allowed; landing code is not.
- At execution start, claim atomically: `filigree start-work hamlet-0d0115383e --assignee <name>`
  (Tasks 1–2), then `hamlet-fa6bb6da4a` (Tasks 3–5).
- Work only in `src/townlet/`, `configs/`, `tests/test_townlet/`, `docs/`. Never touch
  `.oracle/` or `src/hamlet/`.
- Zero backwards compatibility: no fallbacks, no optional-for-migration fields, no version
  checks. Old shapes fail loudly.
- No-Defaults Principle: every new DTO field is required or genuinely optional-by-design;
  `extra="forbid"` everywhere.
- `brain_hash` is produced ONLY by `compute_brain_hash` over the EFFECTIVE config
  (`apply_training_overrides(base, level.training)`). Never `_compute_pydantic_hash` — the
  comment block at `src/townlet/universe/compiler.py:199-208` is load-bearing; extend it,
  don't fight it.
- Test invocation: `UV_CACHE_DIR=.uv-cache uv run pytest <path> -v`. Type gate:
  `UV_CACHE_DIR=.uv-cache uv run mypy src/townlet` (needs `uv sync --extra dev --extra recording`).
- Compile in tests with `use_cache=False` (pattern:
  `tests/test_townlet/integration/test_vtc_transition_schedule_runtime.py`).
- Commit after every task, message style `feat(bac): … (hamlet-<id>)` / `test(bac): …`.

---

### Task 1: Level-overridable `brain.yaml`

`CurriculumLevel` gains an optional complete per-level brain; the compiler selects it as the
effective base for the primary level. A level that says nothing inherits the pack brain
unchanged (PDR-0027 half 1).

**Files:**
- Modify: `src/townlet/universe/raw_configs_v21.py` (`CurriculumLevel` ~line 31; level loop ~line 250)
- Modify: `src/townlet/universe/compiler.py` (~line 209, and the `CompiledUniverse(brain=…)`
  construction site — find with `grep -n "brain=raw.brain" src/townlet/universe/compiler.py`)
- Modify: `src/townlet/universe/compiled.py` (`as_single_level` ~line 649 — see Step 6)
- Modify: `docs/config-schemas/brain.md` (document the level override + fork consequence)
- Test: `tests/test_townlet/unit/universe/test_brain_level_override.py` (new)

**Interfaces:**
- Consumes: `load_brain_config(config_dir: Path) -> BrainConfig` (`config/brain_config.py:494`
  — reads `<dir>/brain.yaml`, raises FileNotFoundError if absent);
  `apply_training_overrides(brain, training) -> BrainConfig` (`:562`);
  `compute_brain_hash(config) -> str` (`:534`).
- Produces: `CurriculumLevel.brain: BrainConfig | None` (None = inherit pack brain);
  `CompiledUniverse.brain` semantics change to "effective base brain of the compiled level"
  (its one production consumer, `DemoRunner` at `demo/runner.py:454`, already treats it as
  the base to merge training overrides into, so it is corrected by construction — same for
  `demo/live_inference.py:369-375`).

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_townlet/unit/universe/test_brain_level_override.py
"""Per-level brain.yaml override (PDR-0027, hamlet-0d0115383e).

A level directory MAY contain a complete brain.yaml; if present it replaces the
pack-root brain as the effective base for that level. A level that says nothing
inherits the pack brain unchanged.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import yaml

from townlet.universe.compiler import UniverseCompiler

PACK = Path("configs/test/model_config")
LEVEL = "L0_test"


def _clone_pack(tmp_path: Path, name: str) -> Path:
    target = tmp_path / name
    shutil.copytree(PACK, target)
    return target


def _write_level_brain(pack_dir: Path, hidden_layers: list[int]) -> None:
    brain = yaml.safe_load((pack_dir / "brain.yaml").read_text())
    brain["architecture"]["feedforward"]["hidden_layers"] = hidden_layers
    (pack_dir / "levels" / LEVEL / "brain.yaml").write_text(yaml.safe_dump(brain, sort_keys=False))


def test_level_without_brain_yaml_inherits_pack_brain(tmp_path: Path) -> None:
    pack_dir = _clone_pack(tmp_path, "baseline")
    universe = UniverseCompiler().compile(pack_dir, primary_level=LEVEL, use_cache=False)
    assert universe.brain.architecture.feedforward.hidden_layers == [256, 128]


def test_level_brain_yaml_replaces_pack_brain_and_moves_the_hash(tmp_path: Path) -> None:
    baseline_dir = _clone_pack(tmp_path, "baseline")
    forked_dir = _clone_pack(tmp_path, "forked")
    _write_level_brain(forked_dir, hidden_layers=[64, 64])

    compiler = UniverseCompiler()
    baseline = compiler.compile(baseline_dir, primary_level=LEVEL, use_cache=False)
    forked = compiler.compile(forked_dir, primary_level=LEVEL, use_cache=False)

    assert forked.brain.architecture.feedforward.hidden_layers == [64, 64]
    assert baseline.brain.architecture.feedforward.hidden_layers == [256, 128]
    assert forked.brain_hash != baseline.brain_hash


def test_identical_level_brain_yaml_is_not_a_hash_fork(tmp_path: Path) -> None:
    baseline_dir = _clone_pack(tmp_path, "baseline")
    copied_dir = _clone_pack(tmp_path, "copied")
    shutil.copy(copied_dir / "brain.yaml", copied_dir / "levels" / LEVEL / "brain.yaml")

    compiler = UniverseCompiler()
    baseline = compiler.compile(baseline_dir, primary_level=LEVEL, use_cache=False)
    copied = compiler.compile(copied_dir, primary_level=LEVEL, use_cache=False)
    assert copied.brain_hash == baseline.brain_hash
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/universe/test_brain_level_override.py -v`
Expected: test 2 FAILS (override ignored — `hidden_layers == [256, 128]` and equal hashes);
tests 1 and 3 may already pass.

- [ ] **Step 3: Implement — DTO and loader**

In `src/townlet/universe/raw_configs_v21.py`, add the field to `CurriculumLevel`
(after `training`, before `items_appearance`):

```python
    training: TrainingV2Config
    # Optional COMPLETE per-level brain.yaml (PDR-0027). None = inherit the pack brain
    # unchanged. Never a partial patch: partial merges need default semantics, which the
    # No-Defaults Principle forbids.
    brain: BrainConfig | None = None
    items_appearance: ItemsAppearanceConfig | None = None
```

In the level-loading loop (~line 260, after `training = load_training_v2_config(level_dir)`):

```python
                level_brain = load_brain_config(level_dir) if (level_dir / "brain.yaml").exists() else None
```

and pass `brain=level_brain` in the `CurriculumLevel(...)` construction (~line 275).
`load_brain_config` is already imported at the top of the file.

- [ ] **Step 4: Implement — compiler selection**

In `src/townlet/universe/compiler.py` replace line 209 with:

```python
        # PDR-0027: a level's complete brain.yaml replaces the pack brain as the effective
        # base. brain_hash stays what it was: the EFFECTIVE config for the primary level.
        base_brain = raw.levels[primary_level].brain or raw.brain
        brain_hash = compute_brain_hash(apply_training_overrides(base_brain, raw.levels[primary_level].training))
```

Then `grep -n "brain=raw.brain" src/townlet/universe/compiler.py` and change that
construction argument to `brain=base_brain` (thread `base_brain` down to the construction
site if it is in a helper — follow how `brain_hash` already travels).

- [ ] **Step 5: Run tests to verify they pass**

Run: `UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/universe/test_brain_level_override.py tests/test_townlet/unit/universe/ -v`
Expected: all PASS (the second target catches regressions in existing compiler tests).

- [ ] **Step 6: Close the `as_single_level` wrong-brain surface**

`CompiledUniverse.as_single_level(level_name)` (`compiled.py:649`) returns
`"brain": self.brain` for ANY requested level — correct today, wrong the moment a
non-primary level declares its own brain. Make it fail loudly instead of lying:

```python
    def as_single_level(self, level_name: str) -> dict[str, Any]:
        """Return a dict of shared + level-specific configs for callers expecting a flat bundle."""
        level = self.get_level(level_name)
        if level_name != self.metadata.primary_level:
            raise ValueError(
                f"as_single_level({level_name!r}) on a universe compiled for "
                f"{self.metadata.primary_level!r}: brain is the PRIMARY level's effective base "
                "(PDR-0027) and may differ per level. Recompile with "
                f"primary_level={level_name!r} instead."
            )
```

Run `grep -rn "as_single_level" src/ tests/` first; if a production caller passes a
non-primary level, stop and re-read that call site before applying (it would already be a
latent bug — fix the caller to recompile, per the error message).

- [ ] **Step 7: Verify cache correctness**

The compile cache must notice a newly added level `brain.yaml`. Find what feeds
`config_hash` (`grep -n "config_hash" src/townlet/universe/compiler.py` and follow to its
input collection). If it hashes all files under the experiment dir, nothing to do. If it
hashes an explicit file list, add `levels/*/brain.yaml` to it and add this test to
`test_brain_level_override.py`:

```python
def test_adding_level_brain_yaml_changes_config_hash(tmp_path: Path) -> None:
    baseline_dir = _clone_pack(tmp_path, "baseline")
    forked_dir = _clone_pack(tmp_path, "forked")
    _write_level_brain(forked_dir, hidden_layers=[64, 64])

    compiler = UniverseCompiler()
    baseline = compiler.compile(baseline_dir, primary_level=LEVEL, use_cache=False)
    forked = compiler.compile(forked_dir, primary_level=LEVEL, use_cache=False)
    assert baseline.metadata.config_hash != forked.metadata.config_hash
```

- [ ] **Step 8: Document, type-check, commit**

Add to `docs/config-schemas/brain.md`: a level directory MAY contain a complete
`brain.yaml`; it replaces the pack brain for that level; overriding forks the lineage and
moves `brain_hash` (point at PDR-0027).

Run: `UV_CACHE_DIR=.uv-cache uv run mypy src/townlet`
Expected: clean.

```bash
git add src/townlet/universe/raw_configs_v21.py src/townlet/universe/compiler.py \
        src/townlet/universe/compiled.py docs/config-schemas/brain.md \
        tests/test_townlet/unit/universe/test_brain_level_override.py
git commit -m "feat(bac): brain.yaml is level-overridable as a complete file (PDR-0027, hamlet-0d0115383e)"
```

---

### Task 2: Lineage legibility — the fork is stated before the artifact is used

PDR-0027 half 2: *"An experiment artifact whose effective brain diverges from its pack
baseline must carry that fact visibly, and every loader must surface it before the artifact
is used."* Mechanism chosen: `pack_brain_hash` beside `brain_hash` on `CompiledUniverse` and
in every checkpoint; loaders emit a fork banner.

**Files:**
- Modify: `src/townlet/universe/compiler.py` (compute + pass `pack_brain_hash`)
- Modify: `src/townlet/universe/compiled.py` (field ~line 195, `clone()` ~line 334,
  `to_dict()` ~line 393, and the matching `from_dict`/deserialization path)
- Modify: `src/townlet/training/checkpoint_utils.py` (`attach_universe_metadata` ~line 52,
  `assert_checkpoint_dimensions` brain_hash block ~line 99)
- Test: `tests/test_townlet/unit/training/test_brain_lineage_legibility.py` (new)

**Interfaces:**
- Consumes: Task 1's `base_brain` selection in `compiler.py`; `CompiledUniverse.brain_hash`.
- Produces: `CompiledUniverse.pack_brain_hash: str | None` (hash of the PACK-root brain
  under the same level training overrides); `CompiledUniverse.brain_forked` property
  (`bool`); checkpoint key `"pack_brain_hash"`; a `logger.warning` fork banner containing
  the phrase `"brain lineage fork"`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_townlet/unit/training/test_brain_lineage_legibility.py
"""A brain fork must be legible at load time, not discovered at runtime (PDR-0027)."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

import yaml

from townlet.training.checkpoint_utils import attach_universe_metadata
from townlet.universe.compiler import UniverseCompiler

PACK = Path("configs/test/model_config")
LEVEL = "L0_test"


def _forked_pack(tmp_path: Path) -> Path:
    target = tmp_path / "forked"
    shutil.copytree(PACK, target)
    brain = yaml.safe_load((target / "brain.yaml").read_text())
    brain["architecture"]["feedforward"]["hidden_layers"] = [64, 64]
    (target / "levels" / LEVEL / "brain.yaml").write_text(yaml.safe_dump(brain, sort_keys=False))
    return target


def test_unforked_universe_has_matching_lineage_hashes(tmp_path: Path) -> None:
    pack_dir = tmp_path / "baseline"
    shutil.copytree(PACK, pack_dir)
    universe = UniverseCompiler().compile(pack_dir, primary_level=LEVEL, use_cache=False)
    assert universe.pack_brain_hash == universe.brain_hash
    assert universe.brain_forked is False


def test_forked_universe_carries_the_fork(tmp_path: Path) -> None:
    universe = UniverseCompiler().compile(_forked_pack(tmp_path), primary_level=LEVEL, use_cache=False)
    assert universe.pack_brain_hash != universe.brain_hash
    assert universe.brain_forked is True


def test_checkpoint_stamps_lineage_and_loader_states_the_fork(tmp_path: Path, caplog) -> None:
    universe = UniverseCompiler().compile(_forked_pack(tmp_path), primary_level=LEVEL, use_cache=False)
    checkpoint: dict = {}
    attach_universe_metadata(checkpoint, universe)
    assert checkpoint["pack_brain_hash"] == universe.pack_brain_hash
    assert checkpoint["brain_hash"] == universe.brain_hash

    from townlet.training.checkpoint_utils import surface_brain_lineage

    with caplog.at_level(logging.WARNING):
        surface_brain_lineage(checkpoint)
    assert any("brain lineage fork" in record.message for record in caplog.records)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/training/test_brain_lineage_legibility.py -v`
Expected: FAIL — `pack_brain_hash` attribute does not exist.

- [ ] **Step 3: Implement — compiled artifact**

In `compiler.py`, next to Task 1's `base_brain` block:

```python
        # PDR-0027 half 2: the pack baseline under the SAME level training overrides, so a
        # pack_brain_hash != brain_hash difference isolates exactly one cause — the level
        # declared its own brain.
        pack_brain_hash = compute_brain_hash(apply_training_overrides(raw.brain, raw.levels[primary_level].training))
```

and pass `pack_brain_hash=pack_brain_hash` wherever `brain_hash=brain_hash` is passed
(`grep -n "brain_hash=brain_hash" src/townlet/universe/compiler.py`).

In `compiled.py`, beside `brain_hash: str | None = None` (~line 195):

```python
    # Hash of the PACK-ROOT brain under the primary level's training overrides (PDR-0027).
    # pack_brain_hash != brain_hash means: this level declared its own brain.yaml.
    pack_brain_hash: str | None = None

    @property
    def brain_forked(self) -> bool:
        """True when the compiled level's effective brain diverges from the pack baseline."""
        return self.pack_brain_hash is not None and self.pack_brain_hash != self.brain_hash
```

Thread `pack_brain_hash` through `clone()` (~line 334), `to_dict()` (~line 393), and the
deserialization path (`grep -n "brain_hash" src/townlet/universe/compiled.py` and mirror
every site).

- [ ] **Step 4: Implement — checkpoint stamp and loader banner**

In `checkpoint_utils.py`, `attach_universe_metadata` (after the `brain_hash` line, ~52):

```python
    checkpoint["pack_brain_hash"] = universe.pack_brain_hash
```

New function (place after `assert_checkpoint_dimensions`):

```python
def surface_brain_lineage(checkpoint: Mapping[str, Any]) -> None:
    """State a brain-lineage fork BEFORE the artifact is used (PDR-0027).

    Legibility, not validation: assert_checkpoint_dimensions still enforces effective
    brain_hash equality for resume. This makes the fork visible to a human loading an
    artifact whose brain diverges from its pack baseline.
    """
    pack_hash = checkpoint.get("pack_brain_hash")
    effective_hash = checkpoint.get("brain_hash")
    if pack_hash is not None and effective_hash is not None and pack_hash != effective_hash:
        logger.warning(
            "brain lineage fork: this checkpoint's effective brain (%s...) diverges from its "
            "pack baseline (%s...) at level %s — a per-level brain.yaml override. It is NOT "
            "interchangeable with unforked artifacts of the same pack (PDR-0027).",
            str(effective_hash)[:16],
            str(pack_hash)[:16],
            checkpoint.get("primary_level"),
        )
```

Call `surface_brain_lineage(checkpoint)` at the TOP of
`assert_checkpoint_identity` (~line 194) so every load path states the fork before any
validation can raise. Note the deliberate asymmetry with the strict-hash guards above:
a checkpoint WITHOUT `pack_brain_hash` (pre-fork era) passes silently here — this is
legibility metadata, and the strict `brain_hash` equality check already refuses genuinely
incompatible artifacts.

- [ ] **Step 5: Run tests to verify they pass**

Run: `UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/training/test_brain_lineage_legibility.py tests/test_townlet/unit/training/ tests/test_townlet/unit/universe/ -v`
Expected: all PASS.

- [ ] **Step 6: Type-check, commit**

Run: `UV_CACHE_DIR=.uv-cache uv run mypy src/townlet`

```bash
git add src/townlet/universe/compiler.py src/townlet/universe/compiled.py \
        src/townlet/training/checkpoint_utils.py \
        tests/test_townlet/unit/training/test_brain_lineage_legibility.py
git commit -m "feat(bac): a brain fork is stated at load, not discovered at runtime (PDR-0027, hamlet-0d0115383e)"
```

Then close the ticket:
`filigree close hamlet-0d0115383e --expected-assignee <name> --reason="brain.yaml level-overridable as a complete file; fork legibility via pack_brain_hash stamp + load banner; both config-in/behaviour-out tested (PDR-0027)"`

---

### Task 3: The authored `set_encoder` pack

PDR-0007's definition-of-done: the option must be authored in a config pack at a
non-default value. A committed test pack whose agent-profile `tensor2d` variable becomes the
token observation field.

**Files:**
- Create: `configs/test/set_encoder_smoke/` (copy of `configs/test/model_config/`, two files edited)
- Test: `tests/test_townlet/unit/universe/test_set_encoder_pack.py` (new)

**Interfaces:**
- Consumes: the compiler's PDR-0075 rule — an agent-profile variable with
  `exposed_to: [agent]` compiles to its own observation field named after the variable,
  flattened dims (`tensor2d [4,3]` → 12), `semantic_type` required from the closed
  vocabulary (`custom` here); compiled profile variables get `readable_by=["agent","engine"]`,
  `writable_by=["engine"]` (`universe/compilers/vfs.py:283-284`).
- Produces: pack `configs/test/set_encoder_smoke` with level `L0_test`, observation field
  `need_tokens` (dims 12), pack-level `architecture.type: set_encoder`. Tasks 4–5 depend on
  these exact names.

- [ ] **Step 1: Copy the base pack**

```bash
cp -r configs/test/model_config configs/test/set_encoder_smoke
```

- [ ] **Step 2: Declare the token variable**

Edit `configs/test/set_encoder_smoke/vfs_profiles.yaml` — add an `agent_profile` block
(the file currently has `item_profiles` and no agent profile; match the syntax of
`configs/test/vfs_profiles_smoke/vfs_profiles.yaml`):

```yaml
agent_profile:
  variables:
    - name: need_tokens
      semantic_type: custom
      type: tensor2d
      shape: [4, 3]
      initial_value_mode: zeros
      exposed_to: [agent]
      description: "Flattened token rows for the set-encoder proof: 4 tokens x 3 features."
```

- [ ] **Step 3: Author the set_encoder brain**

Edit `configs/test/set_encoder_smoke/brain.yaml` — replace the `architecture:` block only
(keep optimizer/loss/q_learning/replay as copied):

```yaml
architecture:
  type: set_encoder
  set_encoder:
    token_field_name: need_tokens
    max_tokens: 4
    token_dim: 3
    token_embed_dim: 16
    base_hidden_dim: 32
    q_head_hidden_dim: 64
```

Also update the top-level `description:` to name the pack's purpose (set_encoder smoke).

- [ ] **Step 4: Write the compile test**

```python
# tests/test_townlet/unit/universe/test_set_encoder_pack.py
"""The committed set_encoder pack compiles and exposes the token field (hamlet-fa6bb6da4a)."""

from __future__ import annotations

from pathlib import Path

from townlet.universe.compiler import UniverseCompiler

PACK = Path("configs/test/set_encoder_smoke")
LEVEL = "L0_test"


def test_set_encoder_pack_compiles_with_token_field() -> None:
    universe = UniverseCompiler().compile(PACK, primary_level=LEVEL, use_cache=False)

    assert universe.brain.architecture.type == "set_encoder"
    se = universe.brain.architecture.set_encoder
    assert se is not None and se.token_field_name == "need_tokens"

    field = universe.observation_spec.get_field_by_name("need_tokens")
    assert field.dims == se.max_tokens * se.token_dim == 12
```

- [ ] **Step 5: Run, fix, pass**

Run: `UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/universe/test_set_encoder_pack.py -v`

If compilation fails, likely causes in order: a name collision on `need_tokens`
(rename per the compiler's error), a missing `semantic_type`, or `validate_v21_semantics`
rules about profiles — read the CompilationError, it names the file and rule. Also
sanity-check the CLI end-to-end:
`UV_CACHE_DIR=.uv-cache uv run python -m townlet.universe validate configs/test/set_encoder_smoke`
Expected: both pass.

- [ ] **Step 6: Commit**

```bash
git add configs/test/set_encoder_smoke tests/test_townlet/unit/universe/test_set_encoder_pack.py
git commit -m "feat(bac): author the first set_encoder pack — the option exists in config, not only in code (hamlet-fa6bb6da4a)"
```

---

### Task 4: Config-in/behaviour-out proof that `set_encoder` runs

PDR-0017's first unit, verbatim: *"a config-in/behaviour-out test that authors
`architecture.type: set_encoder` and asserts the tokens reach the network and change its
output."* Four assertions: the network is built from config; token values flow
registry → observation → Q-values; the token slice is treated as a SET (permutation
invariance of mean-pooling); gradients reach the token encoder.

**Files:**
- Test: `tests/test_townlet/integration/test_set_encoder_runtime.py` (new)
- Modify (only if a defect is found): whichever of
  `population/vectorized.py` / `agent/network_factory.py` / `agent/networks.py` /
  `environment/observation_encoder.py` the failure names

**Interfaces:**
- Consumes: Task 3's pack (`configs/test/set_encoder_smoke`, level `L0_test`, field
  `need_tokens`); `VectorizedHamletEnv(universe=…, level_name=…, num_agents=…, device=…)`;
  `VectorizedPopulation` construction pattern from
  `tests/test_townlet/integration/test_episode_execution.py`; `env.vfs_registry.set(id, value,
  writer="engine")`; `env._get_observations() -> torch.Tensor`.
- Produces: the green (or red) evidence Task 5 adjudicates. No new API.

- [ ] **Step 1: Write the test file**

```python
# tests/test_townlet/integration/test_set_encoder_runtime.py
"""set_encoder, config-in/behaviour-out (PDR-0017 first unit, hamlet-fa6bb6da4a).

An unexercised code path in this codebase is not presumptively working. This file is the
first thing that ever DRIVES architecture.type: set_encoder from an authored pack.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import torch

from townlet.agent.networks import SetEncoderQNetwork
from townlet.curriculum.static import StaticCurriculum
from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.exploration.epsilon_greedy import EpsilonGreedyExploration
from townlet.population.vectorized import VectorizedPopulation
from townlet.universe.compiler import UniverseCompiler

PACK = Path("configs/test/set_encoder_smoke")
LEVEL = "L0_test"
NUM_AGENTS = 2


@pytest.fixture
def setup():
    universe = UniverseCompiler().compile(PACK, primary_level=LEVEL, use_cache=False)
    device = torch.device("cpu")
    env = VectorizedHamletEnv(universe=universe, level_name=LEVEL, num_agents=NUM_AGENTS, device=device)
    population = VectorizedPopulation(
        env=env,
        curriculum=StaticCurriculum(difficulty_level=0.5),
        exploration=EpsilonGreedyExploration(epsilon=0.1, epsilon_min=0.1, epsilon_decay=1.0),
        agent_ids=[f"agent_{i}" for i in range(NUM_AGENTS)],
        device=device,
        obs_dim=env.observation_dim,
        brain_config=universe.brain,
        action_dim=env.action_dim,
        train_frequency=1,
        batch_size=16,
        sequence_length=1,
        max_grad_norm=1.0,
        vision_window_size=5,
    )
    population.reset()
    return universe, env, population


def _token_slice(universe) -> slice:
    field = universe.observation_spec.get_field_by_name("need_tokens")
    return slice(field.start_index, field.end_index)


def test_config_builds_a_set_encoder_network(setup) -> None:
    universe, env, population = setup
    assert isinstance(population.q_network, SetEncoderQNetwork)
    assert population.is_set_encoder is True
    net = population.q_network
    assert (net.max_tokens, net.token_dim) == (4, 3)
    assert net.token_slice == _token_slice(universe)


def test_tokens_reach_the_network_and_change_its_output(setup) -> None:
    universe, env, population = setup
    net = population.q_network
    sl = _token_slice(universe)

    obs_zero = env._get_observations()
    assert torch.all(obs_zero[:, sl] == 0.0), "token field should initialize to zeros"
    q_zero = net(obs_zero)

    tokens = torch.rand(NUM_AGENTS, 4, 3) + 0.1  # strictly nonzero: every row is non-empty
    env.vfs_registry.set("need_tokens", tokens, writer="engine")

    obs_tokens = env._get_observations()
    assert torch.any(obs_tokens[:, sl] != 0.0), "registry write must reach the observation"
    q_tokens = net(obs_tokens)
    assert not torch.allclose(q_zero, q_tokens), "token values must change Q-values"


def test_token_rows_are_a_set_not_a_sequence(setup) -> None:
    universe, env, population = setup
    net = population.q_network
    sl = _token_slice(universe)

    tokens = torch.rand(NUM_AGENTS, 4, 3) + 0.1
    env.vfs_registry.set("need_tokens", tokens, writer="engine")
    obs = env._get_observations()

    permuted = obs.clone()
    rows = permuted[:, sl].reshape(NUM_AGENTS, 4, 3)
    permuted[:, sl] = rows[:, [2, 0, 3, 1], :].reshape(NUM_AGENTS, 12)

    assert torch.allclose(net(obs), net(permuted), atol=1e-6), (
        "mean-pooled token rows must be permutation-invariant; if this fails the slice is "
        "being consumed as a flat vector, not a token set"
    )


def test_gradients_flow_into_the_token_encoder(setup) -> None:
    universe, env, population = setup
    net = population.q_network
    env.vfs_registry.set("need_tokens", torch.rand(NUM_AGENTS, 4, 3) + 0.1, writer="engine")
    obs = env._get_observations()

    net.zero_grad()
    net(obs).sum().backward()
    grad = net.token_encoder[0].weight.grad
    assert grad is not None and torch.any(grad != 0.0), "loss must reach the token encoder"
```

- [ ] **Step 2: Run the tests**

Run: `UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/integration/test_set_encoder_runtime.py -v`

Three possible outcomes — each has a different next step:
1. **All PASS** → Step 4 (commit), then Task 5 outcome A.
2. **FAIL on plumbing the test controls** (wrong registry write shape, wrong fixture kwarg):
   fix the TEST — the registry's error messages name expected shapes.
3. **FAIL inside src/townlet** (network never built, field not filled, slice misaligned,
   pooling not invariant): this is the finding the unit exists to produce. Go to Step 3.

- [ ] **Step 3 (only on outcome 3): Fix the defect at its site — or stop**

Use superpowers:systematic-debugging. A shape/wiring defect in
`NetworkFactory.build_set_encoder`, `VectorizedPopulation._build_network`, or the
observation fill path is in scope: fix minimally, keep the test unchanged, re-run.
A DESIGN defect (the token path cannot express what it claims; the architecture is
fundamentally broken) is NOT in scope: per PDR-0017's second reversal trigger it
**escalates to the owner as a design fork ("repair or replace the token path") and must not
be decided in this plan**. Stop after recording the failure evidence in
`hamlet-fa6bb6da4a` (`filigree add-comment`), and go to Task 5 outcome B.

- [ ] **Step 4: Commit**

```bash
git add tests/test_townlet/integration/test_set_encoder_runtime.py
git commit -m "test(bac): set_encoder proven config-in/behaviour-out — tokens reach the network, change Q, pool as a set (hamlet-fa6bb6da4a)"
```

---

### Task 5: Adjudicate the outcome and re-point the pivot

This task is bookkeeping-with-teeth: PDR-0017's reversal triggers were written for exactly
this moment, and the tracker state must match whichever fired. No code.

**Files:**
- Create: `docs/product/decisions/NNNN-<outcome>.md` (next free PDR number at execution time)
- Modify: filigree state for `hamlet-fa6bb6da4a` (and `hamlet-424adcb84f` stays blocked on it)

**Interfaces:**
- Consumes: Task 4's outcome; PDR-0017 (triggers), PDR-0044 (priority), PDR-0107
  (relational exposure waits on this chain).

- [ ] **Step 1: Determine which PDR-0017 trigger fired**

  - **Outcome A — the proof passed.** PDR-0017 trigger 1 (*"set_encoder turns out to work
    … the first unit then collapses to a formality and the transformer step can be
    scheduled directly"*) fires.
  - **Outcome B — the proof failed on a design defect.** PDR-0017 trigger 2 fires: the
    question becomes "repair or replace the token path", which **escalates to the owner**.
    Do not proceed to any Phase B planning.

- [ ] **Step 2: Write the outcome PDR**

House style: Date / Status / Author / Owner sign-off / Related / Tracker header, then
Context, The call, Consequences, Reversal trigger. Content by outcome:

  - **A:** "set_encoder is proven; PDR-0017's first unit is complete and its trigger 1
    fires." Consequences: the aggregator upgrade (mean-pool → self-attention) and the
    token-representation design become schedulable; `hamlet-fa6bb6da4a` gets a comment
    scoping its REMAINING work (the migration proper); PDR-0107's wait now has a live
    dependency rather than an unproven one. Reversal trigger: the aggregator upgrade
    shows the DeepSets proof did not generalize (attention needs different plumbing).
  - **B:** "set_encoder is broken in kind X; per PDR-0017 trigger 2 this is an owner
    decision." The PDR records only the evidence and the escalation — NOT a repair/replace
    choice.

- [ ] **Step 3: Update the tracker**

```bash
# Outcome A:
filigree add-comment hamlet-fa6bb6da4a "First unit complete: set_encoder proven config-in/behaviour-out (tests/test_townlet/integration/test_set_encoder_runtime.py, PDR-NNNN). Remaining scope: the token-observation migration proper (Phase B plans)."
# Outcome B:
filigree add-comment hamlet-fa6bb6da4a "First unit FAILED: <evidence>. PDR-0017 trigger 2 fired — escalated to owner (PDR-NNNN). Do not start Phase B."
```

`hamlet-424adcb84f` (dynamic variables) needs no touch — it already blocks on
`hamlet-fa6bb6da4a` per PDR-0107.

- [ ] **Step 4: Commit and push**

```bash
git add docs/product/decisions/
git commit -m "product: the set_encoder proof adjudicated — PDR-0017 trigger <1|2> fired (PDR-NNNN)"
git push origin <current-branch>
```

---

## After this plan (Phase B — separate plans, NOT planned here)

Deliberately unplanned: each depends on Task 5's outcome and on design decisions that would
be speculation today. In dependency order, all gated on Outcome A:

1. **Aggregator upgrade** — mean-pool → self-attention inside `SetEncoderQNetwork`
   (PDR-0017: "a transformer is an aggregator upgrade, not a new build").
2. **Token representation of the full observation** — how meters/spatial/affordance blocks
   become tokens; supersedes the superset+mask fixed-width ABI. This is the migration
   proper and the big design document.
3. **Relational/message exposure as tokens** — reopens PDR-0107 via its third trigger
   ("the token migration lands"); pair/group/message state becomes tokens, the two
   observation gates open.
4. **Dynamic variables** — `hamlet-424adcb84f`, targeting variable-token representation
   (vfs.md §15.3 option 2).

Also noticed during planning, worth a filigree note at execution (not this plan's scope):
`SetEncoderConfig.token_field_name` is validated only at network-build time
(`network_factory.py:196`), not at compile time — an author typo surfaces at runtime, which
is the compile-time-underspecification shape PDR-0052 exists to kill.
