# Token Unit 5 — Pack Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close `hamlet-55b2826a02`: every surviving pack compiles, constructs and steps under one test; every live token type and scope is exercised config-in/behaviour-out from a committed pack; L3 temporality is one authored `day_phase` token; `observation_mode` and the reference pack's malformed shape are gone.

**Architecture:** Config packs are the authoring surface, so every exercise starts from YAML and asserts on the compiled `TokenSpec` and the live observation tensor. The compiler's exposure rule gains one narrow admission (an expression variable with a declared `initial_value`), the items DTO reuses the effects command DTO so bad shapes refuse at parse, and one discovery-driven smoke test walks `configs/`.

**Tech Stack:** Python 3.13, pydantic v2, torch, pytest; `uv run` with `UV_CACHE_DIR=.uv-cache`.

**Spec:** `docs/product/decisions/0143-unit-5-scope-is-ruled-observation-mode-dies-day-phase-is-authored-agent-tokens-stay-absent.md` (the ruling) over `docs/superpowers/specs/2026-08-22-token-observation-representation-design.md` §6 unit 5.

## Global Constraints

- Zero backwards compatibility: delete, never deprecate; a removed key must fail validation as an extra field.
- No-defaults principle: every new pack key is explicit in every pack that needs it.
- Never branch on a variable's name in engine code.
- Every production change starts from a failing test; commit after each task with the trailer `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>` and `Claude-Session: https://claude.ai/code/session_01R8msWETtLnHAAFkY6W4rY4`.
- Gates before any push (PDR-0127): `uv run ruff check .`, `uv run black --check src tests scripts`, `uv run mypy src/townlet`, `uv run python scripts/no_defaults_lint.py src/townlet/ --whitelist .defaults-whitelist.txt`, `uv run python scripts/validate_compiler_cli.py`, `git diff --check`, `uv run pytest`.
- Width literals in tests are MEASURED after a change, never guessed: run the compile, read `token_spec.total_dims`, then pin.
- Work only in `src/townlet/`, `configs/`, `tests/`, `docs/`.

---

### Task 1: Delete the inert `observation_mode` stratum key

**Files:**
- Modify: `src/townlet/config/stratum_config.py:22-45` (delete `ObservationModeConfig`), `:210-213` (delete the field)
- Modify: every `stratum.yaml` under `configs/` that declares `observation_mode:` (30 files)
- Modify: `docs/architecture/STRATA.md:52`, `README.md:116-122`, `CLAUDE.md:176-179`
- Test: `tests/test_townlet/unit/substrate/test_config.py`

**Interfaces:**
- Produces: `StratumConfig` without `observation_mode`; a pack declaring it fails with pydantic `ValidationError` ("Extra inputs are not permitted").

- [ ] **Step 1: Write the failing test** (append to `tests/test_townlet/unit/substrate/test_config.py`; add `from pydantic import ValidationError` and `from townlet.config.stratum_config import StratumConfig` to its imports)

```python
def test_observation_mode_is_no_longer_a_stratum_key():
    """`observation_mode` had no consumer anywhere in src/townlet (PDR-0143); it is deleted, not deprecated."""
    data = {
        "version": "1.0",
        "substrate": {
            "type": "grid",
            "grid": {"topology": "square", "width": 8, "height": 8, "boundary": "clamp", "distance_metric": "manhattan", "diagonals": False},
        },
        "vision_support": "both",
        "temporal_support": "enabled",
        "observation_mode": {"mode": "full_auto"},
    }
    with pytest.raises(ValidationError, match="observation_mode"):
        StratumConfig(**data)
    del data["observation_mode"]
    assert StratumConfig(**data).temporal_support == "enabled"
```

- [ ] **Step 2: Run it to verify it fails**

Run: `UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/substrate/test_config.py::test_observation_mode_is_no_longer_a_stratum_key -q --no-cov`
Expected: FAIL — `DID NOT RAISE` (the key is currently accepted).

- [ ] **Step 3: Delete the DTO surface**

In `src/townlet/config/stratum_config.py` delete the whole `class ObservationModeConfig(BaseModel): ...` block and the `observation_mode: ObservationModeConfig = Field(...)` field on `StratumConfig`. Remove any import that becomes unused (`model_validator` if nothing else uses it — check with ruff).

- [ ] **Step 4: Strip the key from every pack**

```bash
python3 - <<'EOF'
import pathlib, re
for p in pathlib.Path("configs").rglob("stratum.yaml"):
    lines = p.read_text().splitlines(keepends=True)
    out, skip = [], 0
    for i, line in enumerate(lines):
        if re.match(r"^\s*observation_mode:\s*(#.*)?$", line):
            skip = 1  # drop this line and the `mode:` line that follows
            continue
        if skip and re.match(r"^\s*mode:\s*\S+", line):
            skip = 0
            continue
        out.append(line)
    p.write_text("".join(out))
EOF
grep -rn observation_mode configs && echo "STILL PRESENT" || echo "clean"
```
Expected: `clean`. Then `UV_CACHE_DIR=.uv-cache uv run python scripts/validate_compiler_cli.py` → `✅ Universe compiler CLI validation passed`.

- [ ] **Step 5: Correct the three documents**

STRATA.md: delete the line `- \`observation_mode\` — \`full_auto | max_compact | full_manual\` (§6.4).` (there is no §6.4). README.md: delete the `observation_mode:` / `mode: full_auto` lines from the stratum example and rewrite the sentence at line 122 to: ``Declaring the deleted `observation_encoding` or `observation_mode` keys fails validation (PDR-0143).`` CLAUDE.md: replace ``A config that still declares the old selector fails validation as an extra field. `observation_mode` belongs to the separate observation-layout surface.`` with ``A config that still declares the old selector, or the deleted `observation_mode` key, fails validation as an extra field (PDR-0143).``

- [ ] **Step 6: Run the tests and lint**

Run: `UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/substrate tests/test_townlet/unit/universe -q --no-cov -p no:cacheprovider && UV_CACHE_DIR=.uv-cache uv run ruff check src tests && UV_CACHE_DIR=.uv-cache uv run mypy src/townlet/config/stratum_config.py`
Expected: all pass.

- [ ] **Step 7: Commit**

```bash
git add src/townlet/config/stratum_config.py configs tests/test_townlet/unit/substrate/test_config.py docs/architecture/STRATA.md README.md CLAUDE.md
git commit -m "feat(stratum): delete the inert observation_mode key — no consumer existed (PDR-0143, hamlet-55b2826a02)"
```

---

### Task 2: Author `day_phase` — one exposed cyclical token on `default_curriculum`

**Files:**
- Modify: `src/townlet/config/vfs_profiles_config.py:95-107` (and the same validator on `AgentVFSVariableConfig` / `ItemVFSVariableConfig`)
- Modify: `src/townlet/vfs/profiles.py:245-290`
- Modify: `src/townlet/universe/compilers/vfs.py:328-332`
- Modify: `configs/default_curriculum/vfs_profiles.yaml:4-14`
- Modify: `tests/test_townlet/unit/universe/test_vfs_profile_compilation.py:84-99`, `tests/test_townlet/integration/test_temporal_mechanics.py:254-281`, `tests/test_townlet/integration/test_compact_token_runtime.py:34-46`, `tests/test_townlet/integration/test_compact_token_acceptance.py:80`, `tests/test_townlet/unit/universe/test_token_emission.py:58-75`
- Test: the files above

**Interfaces:**
- Consumes: `NormalizationSpec(kind="cyclical_sin_cos", period=24)`; `TokenSpec.compact_layout().get_type("variable_element")` → `CompactTokenTypeLayout(start, compact_row_width, dynamic_features)`; `TokenSpec.get_type("variable_element").slot_bindings[i].filler_ref`.
- Produces: an exposed expression variable is admitted iff it declares `initial_value`; `default_curriculum` levels carry one `variable_element` slot bound to `day_phase`.

- [ ] **Step 1: Write the failing DTO tests** (new file `tests/test_townlet/unit/config/test_vfs_profile_init_sources.py`)

```python
"""An expression variable may declare its reset value; a tensor initializer may not coexist with an expression."""

import pytest
from pydantic import ValidationError

from townlet.config.vfs_profiles_config import GlobalVFSVariableConfig


def _base(**extra):
    return {"name": "day_phase", "type": "float", "semantic_type": "temporal", **extra}


def test_expression_with_declared_initial_value_is_accepted():
    var = GlobalVFSVariableConfig(**_base(expression="tick", initial_value=0.0))
    assert var.expression == "tick" and var.initial_value == 0.0


def test_expression_with_tensor_initializer_refuses():
    with pytest.raises(ValidationError, match="initial_value_mode"):
        GlobalVFSVariableConfig(**_base(expression="tick", initial_value_mode="zeros", shape=[2]))


def test_no_init_source_refuses():
    with pytest.raises(ValidationError, match="exactly one"):
        GlobalVFSVariableConfig(**_base())
```

- [ ] **Step 2: Run them to verify the first fails**

Run: `UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/config/test_vfs_profile_init_sources.py -q --no-cov`
Expected: `test_expression_with_declared_initial_value_is_accepted` FAILS with "must choose exactly one"; the other two pass.

- [ ] **Step 3: Relax the validator** — replace the body of `validate_value_xor_expression` on all three variable DTOs (`GlobalVFSVariableConfig`, `AgentVFSVariableConfig`, `ItemVFSVariableConfig`):

```python
    @model_validator(mode="after")
    def validate_value_xor_expression(self):
        """One static source (initial_value XOR initial_value_mode) or an expression; an
        expression may ALSO declare initial_value — its exact value at episode start, which
        is what exposure identity needs (PDR-0143)."""
        has_value = self.initial_value is not None
        has_mode = self.initial_value_mode is not None
        has_expr = self.expression is not None
        if has_value and has_mode:
            raise ValueError(f"Variable '{self.name}' must choose exactly one of initial_value or initial_value_mode")
        if has_mode and has_expr:
            raise ValueError(f"Variable '{self.name}' cannot combine initial_value_mode with an expression")
        if not (has_value or has_mode or has_expr):
            raise ValueError(f"Variable '{self.name}' must provide exactly one of initial_value, initial_value_mode, or expression")
        return self
```

- [ ] **Step 4: Run the DTO tests** — Expected: 3 passed.

- [ ] **Step 5: Write the failing compiler test** — in `tests/test_townlet/unit/universe/test_vfs_profile_compilation.py` change the existing refusal test (line ~98) so the un-defaulted case matches the new message, and add the admitted case:

```python
    with pytest.raises(ValueError, match=r"phase.*expression.*without a declared initial_value"):
        UniverseCompiler().compile(experiment_dir, primary_level=PRIMARY_LEVEL_NAME, use_cache=False)

    profiles["global_profile"]["variables"][0]["initial_value"] = 0.0
    (experiment_dir / "vfs_profiles.yaml").write_text(yaml.safe_dump(profiles))
    compiled = UniverseCompiler().compile(experiment_dir, primary_level=PRIMARY_LEVEL_NAME, use_cache=False)
    spec = compiled.get_level(PRIMARY_LEVEL_NAME).token_spec
    assert [b.filler_ref for b in spec.get_type("variable_element").slot_bindings] == ["phase"]
    declared = {v.id: v for v in compiled.get_level(PRIMARY_LEVEL_NAME).vfs_variables}["phase"]
    assert declared.default == 0.0
```

- [ ] **Step 6: Run it to verify it fails** — Expected: FAIL at the first `pytest.raises` (message still says "cannot be exposed: variable_element identity requires one exact declared default").

- [ ] **Step 7: Pass `initial_value` through the expression branch** — in `src/townlet/vfs/profiles.py` change the static-branch condition from `if var.initial_value is not None or getattr(var, "initial_value_mode", None) is not None:` to `if var.expression is None:`, and in the expression branch's `CompiledVariable(...)` replace `initial_value=None,` with `initial_value=var.initial_value,`.

- [ ] **Step 8: Narrow the compiler refusal** — in `src/townlet/universe/compilers/vfs.py` replace the `if exposed and expression is not None:` block with:

```python
        if exposed and expression is not None and compiled_var.initial_value is None:
            raise ValueError(
                f"Exposed VFS variable '{compiled_var.name}' uses an expression without a declared initial_value and "
                "cannot be exposed: variable_element identity requires the exact declared reset value. Declare "
                "initial_value (the value at episode start) or remove exposed_to."
            )
```
`default_value` already falls back to `compiled_var.initial_value` when set, so the registry resets the variable to the declared value and the descriptor's `declared_initial` is that same value.

- [ ] **Step 9: Run the compiler tests** — `UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/universe/test_vfs_profile_compilation.py -q --no-cov` → all pass.

- [ ] **Step 10: Author the pack variable** — replace the `time_of_day_phase` block in `configs/default_curriculum/vfs_profiles.yaml` with:

```yaml
global_profile:
  variables:
  # The authored day clock (PDR-0143, spec §6 unit 5): ONE cyclical token, sin and cos in the
  # same value block. `period` mirrors L3's `day_length: 24`; levels without temporal
  # mechanics still observe the clock — their worlds simply do not act on it.
  - name: day_phase
    id: day_phase
    type: float
    semantic_type: temporal
    expression: tick
    initial_value: 0.0
    exposed_to: [agent]
    normalization:
      kind: cyclical_sin_cos
      period: 24
    description: >-
      Authored day clock derived from the ambient engine tick; exposed as one cyclical token.
```

- [ ] **Step 11: Rewrite the temporal isolation tests** — in `tests/test_townlet/integration/test_temporal_mechanics.py` replace `class TestTemporalExpressionIsolation` with:

```python
class TestAuthoredDayPhase:
    """L3 temporality is ONE authored cyclical token (PDR-0143): declared in vfs_profiles.yaml,
    bound to a variable_element slot, sin and cos of the tick in one value block."""

    VARIABLE = "day_phase"
    PERIOD = 24

    def _lanes(self, env) -> tuple[int, int]:
        bindings = env.token_spec.get_type("variable_element").slot_bindings
        slot = [b.filler_ref for b in bindings].index(self.VARIABLE)
        layout = env.token_spec.compact_layout().get_type("variable_element")
        assert layout is not None
        start = layout.start + slot * layout.compact_row_width
        return start, start + layout.dynamic_features.index("value_0")

    def test_day_phase_is_bound_and_present(self, temporal_env):
        env = temporal_env
        obs = env.reset()
        row, v0 = self._lanes(env)
        assert obs[0, row].item() == 1.0  # presence
        assert obs[0, v0].item() == pytest.approx(0.0)  # sin(0)
        assert obs[0, v0 + 1].item() == pytest.approx(1.0)  # cos(0)

    def test_day_phase_follows_the_tick_as_sin_cos(self, temporal_env):
        env = temporal_env
        env.reset()
        wait = env.action_dim - 1
        obs = None
        for _ in range(7):
            obs, *_ = env.step(torch.tensor([wait], device=env.device))
        # evaluation runs before the tick increments, so after 7 steps day_phase == 6
        assert float(env.vfs_registry.get(self.VARIABLE, reader="engine").reshape(-1)[0]) == 6.0
        _row, v0 = self._lanes(env)
        assert obs[0, v0].item() == pytest.approx(1.0, abs=1e-6)  # sin(2π·6/24)
        assert obs[0, v0 + 1].item() == pytest.approx(0.0, abs=1e-6)
```
Keep the `torch` import already present in the file.

- [ ] **Step 12: Measure the new widths and re-pin** — run:

```bash
UV_CACHE_DIR=.uv-cache uv run python - <<'EOF'
import sys; sys.path.insert(0, "src")
from pathlib import Path
from townlet.universe.compiler import UniverseCompiler
for lv in ("L1_full_observability", "L2_partial_observability"):
    s = UniverseCompiler().compile(Path("configs/default_curriculum"), primary_level=lv, use_cache=False).get_level(lv).token_spec
    print(lv, s.total_dims, s.fixed_total_dims, dict(s.census))
EOF
```
Replace every `115` in `tests/test_townlet/integration/test_compact_token_runtime.py` (lines 34, 35, 46) and the `115` / `4090` in the `grid2d` row of `SUBSTRATE_CASES` in `test_compact_token_acceptance.py` with the printed values; update the `variable_element` count and total in `test_token_emission.py::TestL1TokenEmission::test_census_matches_task6_worked_table` / `test_total_dims_is_task6_measurement` to the printed values and rename the docstrings to say "measured 2026-09-02 after `day_phase` (PDR-0143)". Leave the replay-buffer tests alone — their `115` is an arbitrary shape.

- [ ] **Step 13: Run the affected suites**

Run: `UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/integration/test_temporal_mechanics.py tests/test_townlet/integration/test_compact_token_runtime.py tests/test_townlet/integration/test_compact_token_acceptance.py tests/test_townlet/unit/universe tests/test_townlet/unit/config tests/test_townlet/unit/vfs -q --no-cov -p no:cacheprovider`
Expected: all pass. Any other test that pinned the L1/L2 width or `variable_element: 0` fails here — re-pin it by measurement in the same commit.

- [ ] **Step 14: Adjudicate against the oracle**

Run: `UV_CACHE_DIR=.uv-cache uv run python -m townlet.oracle.harness --cell default_curriculum:L3_temporal_mechanics` and read the two verdicts under `runs/differential/<run-id>/report.json`. The `obs` stream already diverges under DIV-008 (declared on all twenty cells). If the report names an UNREGISTERED divergence (a new signature the register does not bind), add `DIV-011 — Authored day_phase (token-obs unit 5)` to `docs/oracle/known-divergences.md` following the section layout of DIV-010 (Status / Scope / Cause / Streams / Adjudication / Binding), and bind it in `src/townlet/oracle/matrix.py` next to the DIV-010 declaration at line 297 with the same `RegisteredDivergence(...)` shape and the exact signature the report printed. Then re-run the cell; expected: no unregistered divergence.

- [ ] **Step 15: Commit**

```bash
git add src/townlet/config/vfs_profiles_config.py src/townlet/vfs/profiles.py src/townlet/universe/compilers/vfs.py configs/default_curriculum/vfs_profiles.yaml tests docs/oracle src/townlet/oracle
git commit -m "feat(vfs): author day_phase as one exposed cyclical token; an exposed expression variable declares its initial_value (PDR-0143, hamlet-55b2826a02)"
```

---

### Task 3: Malformed item commands refuse at parse; the reference pack constructs and steps

**Files:**
- Modify: `src/townlet/config/items_config.py:111-135` (`ItemInteractionsConfig.validate_commands`) and `:46-70` (`ItemCustomCommand.validate_effects`)
- Modify: `configs/reference/model_pack/items.yaml:14-17`
- Test: `tests/test_townlet/unit/config/test_items_command_shapes.py` (new), `tests/test_townlet/integration/test_reference_model_pack.py`

**Interfaces:**
- Consumes: `townlet.config.effects_config.CommandConfig` (pydantic, `extra="forbid"`, `spawn_effect: str | None`, `target: str | None`, `intensity: float | None`).
- Produces: `ItemInteractionsConfig(on_use=[...])` raises `ValueError` naming the offending command for any shape `CommandConfig` rejects.

- [ ] **Step 1: Write the failing DTO test** (new file)

```python
"""Item interaction commands are effects commands and refuse malformed shapes at parse (hamlet-5a87550adb)."""

import pytest
from pydantic import ValidationError

from townlet.config.items_config import ItemInteractionsConfig


def test_nested_spawn_effect_mapping_refuses_at_parse():
    with pytest.raises(ValidationError, match="spawn_effect"):
        ItemInteractionsConfig(on_use=[{"spawn_effect": {"effect_id": "ate_food", "target": "agent", "intensity": "self.vfs.calories"}}])


def test_sibling_key_spawn_effect_is_accepted():
    cfg = ItemInteractionsConfig(on_use=[{"spawn_effect": "ate_food", "target": "target", "intensity": 1.0}])
    assert cfg.on_use[0]["spawn_effect"] == "ate_food"


def test_unknown_command_key_refuses():
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        ItemInteractionsConfig(on_drop=[{"modify": "target.bar.energy", "value": "1.0", "bogus": 1}])
```

- [ ] **Step 2: Run to verify the first and third fail** — `UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/config/test_items_command_shapes.py -q --no-cov` → tests 1 and 3 FAIL (`DID NOT RAISE`).

- [ ] **Step 3: Validate through the effects command DTO** — in `src/townlet/config/items_config.py` add `from townlet.config.effects_config import CommandConfig` and replace the body of both validators (`validate_effects` on `ItemCustomCommand`, `validate_commands` on `ItemInteractionsConfig`) with:

```python
        if not v and cls.__name__ == "ItemCustomCommand":
            raise ValueError("Custom commands must provide at least one effect command")
        for cmd in v:
            if not isinstance(cmd, dict):
                raise ValueError(f"Command must be dict, got {type(cmd)}")
            # The same grammar the effects compiler executes: a malformed shape refuses here,
            # not at ItemManager construction (hamlet-5a87550adb).
            CommandConfig.model_validate(cmd)
        return v
```
(In `ItemCustomCommand.validate_effects` keep its existing empty-list refusal; in `ItemInteractionsConfig.validate_commands` an empty list is fine.) Delete the now-unused `supported_command_keys` / `ordered` blocks.

- [ ] **Step 4: Run the DTO tests** — Expected: 3 passed. Then run `UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/config tests/test_townlet/unit/items tests/test_townlet/integration/test_items_integration.py tests/test_townlet/integration/test_custom_item_verbs_integration.py -q --no-cov -p no:cacheprovider` — any fixture that fails now carried a malformed command; fix the fixture's YAML to the sibling-key shape, never the validator.

- [ ] **Step 5: Write the failing reference-pack runtime test** (append to `test_reference_model_pack.py`; add `import torch` and `from townlet.environment.vectorized_env import VectorizedHamletEnv`)

```python
def test_reference_model_pack_constructs_and_steps() -> None:
    """The reference pack's whole claim: it compiles AND runs (hamlet-5a87550adb)."""
    compiled = UniverseCompiler().compile(CONFIG_DIR, primary_level=PRIMARY_LEVEL, use_cache=False)
    env = VectorizedHamletEnv(universe=compiled, level_name=PRIMARY_LEVEL, num_agents=2, device=torch.device("cpu"))
    obs = env.reset()
    assert obs.shape == (2, env.token_spec.total_dims)
    obs, _rewards, _dones, _info = env.step(torch.full((2,), env.action_dim - 1, dtype=torch.long))
    assert torch.isfinite(obs).all()
```

- [ ] **Step 6: Run it to verify it fails** — Expected: FAIL at compile with the new parse refusal naming `spawn_effect`.

- [ ] **Step 7: Fix the reference pack shape** — in `configs/reference/model_pack/items.yaml` replace

```yaml
      - spawn_effect:
          effect_id: ate_food
          target: agent
          intensity: self.vfs.calories
```
with
```yaml
      # Effects-command grammar: `spawn_effect: <id>` with sibling keys. Inside an item
      # command `target` is the agent using the item; `intensity` must be a float literal
      # (an expression is not representable in the effect's compiled identity).
      - spawn_effect: ate_food
        target: target
        intensity: 1.0
```

- [ ] **Step 8: Run the reference tests** — `UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/integration/test_reference_model_pack.py tests/test_townlet/regressions/test_affordance_token_identity.py -q --no-cov` → pass. If `step` raises on the `ate_food` effect's `target.vfs.is_digesting` write, read the traceback: the fix belongs in the pack (a missing declaration), not the engine.

- [ ] **Step 9: Commit and close the bug**

```bash
git add src/townlet/config/items_config.py configs/reference/model_pack/items.yaml tests/test_townlet/unit/config/test_items_command_shapes.py tests/test_townlet/integration/test_reference_model_pack.py
git commit -m "fix(items): item commands validate through the effects command DTO; reference pack constructs and steps (hamlet-5a87550adb, PDR-0143)"
```
Then `filigree close hamlet-5a87550adb --actor claude --reason "<commit sha>: malformed shapes refuse at parse; reference pack constructs and steps under test"` (walk `triage → confirmed → fixing → verifying` first with `filigree update` if `close` reports INVALID_TRANSITION).

---

### Task 4: One pack-wide smoke test, discovered from the tree

**Files:**
- Create: `tests/test_townlet/integration/test_pack_smoke.py`

**Interfaces:**
- Consumes: `UniverseCompiler().compile(pack, primary_level=level, use_cache=False)`, `VectorizedHamletEnv(universe=, level_name=, num_agents=, device=)`, `env.reset() -> Tensor[num_agents, total_dims]`, `env.get_action_masks() -> Tensor[num_agents, action_dim] (bool or float)`, `env.step(actions) -> (obs, rewards, dones, info)`, `TokenSpec.row_layout() -> ((type, slot, start, end), ...)`, `TokenSpec.census`.
- Produces: the unit-5 inert-guard: every non-negative pack/level compiles, constructs, resets, steps; `census["agent"] == 0` everywhere (structural absence, PDR-0143).

- [ ] **Step 1: Write the test**

```python
"""Every surviving pack compiles, constructs, resets and steps — discovered from configs/, not listed.

A pack that lands in configs/ is exercised the day it lands; a deleted one stops silently.
The three negative VFS fixtures are excluded by name because refusing is their contract.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import torch

from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.universe.compiler import UniverseCompiler

CONFIGS = Path(__file__).parents[3] / "configs"
NEGATIVE_FIXTURES = {
    CONFIGS / "test" / "vfs_circular_dependency",
    CONFIGS / "test" / "vfs_type_mismatch",
    CONFIGS / "test" / "vfs_undefined_var",
}
STEPS = 4
NUM_AGENTS = 2


def _cases() -> list[tuple[Path, str]]:
    cases = []
    for stratum in sorted(CONFIGS.rglob("stratum.yaml")):
        pack = stratum.parent
        if pack in NEGATIVE_FIXTURES or not (pack / "levels").is_dir():
            continue
        for level in sorted(p.name for p in (pack / "levels").iterdir() if p.is_dir()):
            cases.append((pack, level))
    assert cases, "no packs discovered under configs/"
    return cases


@pytest.mark.parametrize(("pack", "level"), _cases(), ids=lambda v: v.name if isinstance(v, Path) else v)
def test_pack_compiles_constructs_resets_and_steps(pack: Path, level: str) -> None:
    universe = UniverseCompiler().compile(pack, primary_level=level, use_cache=False)
    env = VectorizedHamletEnv(universe=universe, level_name=level, num_agents=NUM_AGENTS, device=torch.device("cpu"))
    spec = env.token_spec
    obs = env.reset()
    assert obs.shape == (NUM_AGENTS, spec.total_dims)
    assert spec.census["agent"] == 0, "agent tokens have no declaration surface (PDR-0143); a surface that makes them live must add an exercise"
    for _ in range(STEPS):
        masks = env.get_action_masks()
        if masks.dtype != torch.bool:
            masks = masks > 0.5
        actions = masks.float().argmax(dim=-1)  # first valid action per agent
        obs, rewards, dones, _info = env.step(actions)
        assert torch.isfinite(obs).all() and torch.isfinite(rewards).all()
    for _type, _slot, start, _end in spec.row_layout():
        presence = obs[:, start]
        assert torch.all((presence == 0.0) | (presence == 1.0)), f"presence lane at {start} is not 0/1"
```

- [ ] **Step 2: Run it** — `UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/integration/test_pack_smoke.py -q --no-cov -p no:cacheprovider`
Expected: every case passes. A failing case is a real defect in that pack or the engine: fix the pack's YAML if the refusal is an authoring error, fix the engine if a valid declaration crashes, and record a deleted pack in the unit-5 PDR — never add the case to `NEGATIVE_FIXTURES`.

- [ ] **Step 3: Commit**

```bash
git add tests/test_townlet/integration/test_pack_smoke.py
git commit -m "test(packs): every surviving pack compiles, constructs, resets and steps; agent tokens asserted structurally absent (PDR-0143, hamlet-55b2826a02)"
```

---

### Task 5: Effect rows and item-arena rows are exercised from committed packs

**Files:**
- Modify: `configs/test/items_smoke/vfs_profiles.yaml:15-19` (expose `durability`)
- Modify: `tests/test_townlet/integration/test_effects_smoke.py` (append), `tests/test_townlet/integration/test_item_vfs_observations.py` (append)

**Interfaces:**
- Consumes: `env.effect_manager.spawn_effect(effect_id=, target_entity_id=, intensity=, current_step=)` (effects_smoke declares `energy_regen`); `spawn_and_pickup_item(env, agent_idx, item_type, initial_state)` (existing helper in `test_item_vfs_observations.py`); `TokenSpec.compact_layout().get_type("effect" | "variable_element")`.

- [ ] **Step 1: Write the failing effect-row test** (append to `test_effects_smoke.py`)

```python
def test_effect_rows_appear_in_the_observation_when_an_effect_spawns(compile_universe, effects_smoke_config_path, cpu_device):
    """Config-in/behaviour-out for the `effect` token type: a declared effect's row is absent
    until it spawns, present with a live remaining fraction after, and decays as it ticks."""
    universe = compile_universe(effects_smoke_config_path)
    env = VectorizedHamletEnv.from_universe(universe=universe, level_name="L0_effects", num_agents=1, device=cpu_device)
    layout = env.token_spec.compact_layout().get_type("effect")
    assert layout is not None and layout.capacity > 0
    remaining = layout.dynamic_features.index("remaining_fraction")

    obs = env.reset()
    before = obs[0, layout.start : layout.start + layout.capacity * layout.compact_row_width].view(layout.capacity, layout.compact_row_width)
    assert before[:, 0].sum().item() == 0.0  # no effect row present at reset

    env.effect_manager.spawn_effect(effect_id="energy_regen", target_entity_id=0, intensity=1.0, current_step=0)
    wait = env.action_space.get_action_by_name("WAIT").id
    obs, *_ = env.step(torch.full((1,), wait, dtype=torch.long, device=cpu_device))
    rows = obs[0, layout.start : layout.start + layout.capacity * layout.compact_row_width].view(layout.capacity, layout.compact_row_width)
    present = rows[:, 0] == 1.0
    assert present.sum().item() == 1
    first = rows[present][0, remaining].item()
    assert 0.0 < first <= 1.0

    obs, *_ = env.step(torch.full((1,), wait, dtype=torch.long, device=cpu_device))
    rows = obs[0, layout.start : layout.start + layout.capacity * layout.compact_row_width].view(layout.capacity, layout.compact_row_width)
    assert rows[rows[:, 0] == 1.0][0, remaining].item() < first
```

- [ ] **Step 2: Run it** — Expected: PASS if the publisher already fills rows from the pack, FAIL otherwise. Either way it is the committed exercise; if it fails, the failing assertion names the defect — fix the engine, not the test.

- [ ] **Step 3: Write the failing item-arena test** (append to `test_item_vfs_observations.py`)

```python
def test_exposed_item_variable_publishes_through_the_item_arena():
    """Config-in/behaviour-out for the item-arena `variable_element` scope: `durability` is
    declared exposed on the `medical` profile, so a held medkit's row carries its normalized
    value and moves when the item's VFS state changes."""
    universe = UniverseCompiler().compile(Path("configs/test/items_smoke"), primary_level="L0_smoke", use_cache=False)
    env = VectorizedHamletEnv(universe=universe, level_name="L0_smoke", num_agents=1, device=torch.device("cpu"))
    env.reset()
    layout = env.token_spec.compact_layout().get_type("variable_element")
    assert layout is not None and layout.capacity > 0
    v0 = layout.dynamic_features.index("value_0")

    def rows():
        obs = env._get_observations()
        return obs[0, layout.start : layout.start + layout.capacity * layout.compact_row_width].view(layout.capacity, layout.compact_row_width)

    assert rows()[:, 0].sum().item() == 0.0
    spawn_and_pickup_item(env, agent_idx=0, item_type="medkit", initial_state={"durability": 50.0})
    live = rows()
    present = live[:, 0] == 1.0
    assert present.sum().item() == 1
    assert live[present][0, v0].item() == pytest.approx(0.5)  # minmax 0..100
```
Add `import pytest` to the file's imports.

- [ ] **Step 4: Run it to verify it fails** — Expected: FAIL at `layout.capacity > 0` (nothing is exposed yet).

- [ ] **Step 5: Expose the variable** — in `configs/test/items_smoke/vfs_profiles.yaml` change the `medical` profile's `durability` to:

```yaml
      - name: durability
        type: float
        initial_value: 100.0
        exposed_to: [agent]
        normalization:
          kind: minmax
          min: 0.0
          max: 100.0
          clip: true
```

- [ ] **Step 6: Run both new tests plus the items and effects suites**

Run: `UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/integration/test_effects_smoke.py tests/test_townlet/integration/test_item_vfs_observations.py tests/test_townlet/integration/test_items_integration.py tests/test_townlet/integration/test_compact_token_acceptance.py tests/test_townlet/unit/universe/test_token_emission.py tests/test_townlet/unit/oracle -q --no-cov -p no:cacheprovider`
Expected: pass. `items_smoke` is an oracle-matrix cell, so run `UV_CACHE_DIR=.uv-cache uv run python -m townlet.oracle.harness --cell items_smoke:L0_smoke` and register a divergence exactly as in Task 2 Step 14 if the report names an unregistered one.

- [ ] **Step 7: Commit**

```bash
git add configs/test/items_smoke/vfs_profiles.yaml tests/test_townlet/integration/test_effects_smoke.py tests/test_townlet/integration/test_item_vfs_observations.py docs/oracle src/townlet/oracle
git commit -m "test(tokens): effect rows and item-arena variable rows exercised config-in/behaviour-out from committed packs (PDR-0143, hamlet-55b2826a02)"
```

---

### Task 6: Full gates, README truth, and the unit-5 checkpoint (product step)

- [ ] **Step 1: Run the full PDR-0127 gate set** (see Global Constraints) and record the counts.
- [ ] **Step 2: README** — the "Observation Dimensions" and stratum sections must not claim the old L1 width or the `observation_mode` key; verify with `grep -n 'observation_mode\|full_auto' README.md CLAUDE.md docs/architecture/*.md` → no hits outside archive/records.
- [ ] **Step 3:** Push `project-recovery-3`, close `hamlet-55b2826a02` with commands and counts, then run `/product-checkpoint` (PDR for unit-5 acceptance; the umbrella `hamlet-fa6bb6da4a` closes only when every child is terminal).
