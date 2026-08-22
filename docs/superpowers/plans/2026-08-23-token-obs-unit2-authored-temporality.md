# Token-Obs Unit 2 — Authored Temporality Made Real: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make ruling 6 of the token-observation design real — the engine publishes one
temporal primitive (`tick`) as an engine-written VFS global, profile-expression evaluation
actually runs (global on the shipped default, agent everywhere, item refused loudly), and
the two temporal bookkeepings collapse into one — with every dynamics byte identical to the
pinned oracle and every provenance-hash movement registered.

**Architecture:** Two oracle-discipline tasks first: cells learn to compose multiple
registered hash divergences (DIV-006 + the catch-up must bind the same cells), then the
six-commit pre-existing hash drift is measured commit-by-commit (DIV-004's worktree
method), registered as DIV-009, and bound — returning the matrix to exit 0 before this
unit adds anything. Then the build: the compiler injects a framework `tick` VariableDef
into every universe and admits bare `tick` as an ambient name in profile expressions; the
env writes it at one pinned point (top of `step()`, before any consumer); `time_of_day`
becomes a derivation of `global_tick` at its existing update point (byte-identical);
evaluation marks are derived from exposure (expression variables only — statics are
storage, never re-evaluated) instead of from the optional overlay file; the agent profile
gets the second evaluation call it always lacked; item-profile expressions refuse at
compile. Unit-2's own hash movement is measured the same way and registered as DIV-010.

**Tech Stack:** Python 3.12, numpy, torch, pytest, uv. No new dependencies.

**Spec:** `docs/superpowers/specs/2026-08-22-token-observation-representation-design.md`
(ruling 6, round-2 amendment 6, §6 unit 2). Tickets:
`hamlet-5cc071f4b6` (Task 2), `hamlet-df3a96bbac` (Task 5), `hamlet-5d74335111` +
`hamlet-bc0a5deeff` (Task 6). Tracker: `hamlet-fa6bb6da4a` (in progress, assignee
`claude-fable` — all filigree ops need `--actor claude-fable`; do not re-claim).

## Global Constraints

- **Streams never move in this unit.** `obs`/`actions`/`rewards`/`dones` must stay
  byte-identical to the oracle on every matrix cell. Only provenance hashes may move, and
  only under a register entry written BEFORE the binding (record-then-bind, PDR-0037).
  Verified fact this rests on: **no oracle fixture pack declares a single profile
  expression variable** (`grep -c "expression:" oracle_fixtures/configs/*/vfs_profiles.yaml
  oracle_fixtures/configs/*/*/vfs_profiles.yaml` → all zero), and no fixture pack declares
  an agent profile — so evaluation fixes change fixture-cell behaviour nowhere.
- **Never touch `.oracle/` or `oracle_fixtures/`.** `docs/oracle/known-divergences.md` IS
  editable — it is the live register; new entries append there.
- **DIV-008 is RESERVED** for the token cut (approved spec §5; unit-1 code docstrings bind
  the name). This unit's entries are **DIV-009** (drift catch-up) and **DIV-010** (unit-2
  build). The register gets an explicit one-line reservation note so the gap is visible,
  never silent.
- **No-tech-debt (`PDR-0012`/`PDR-0013`):** wire-or-delete (a renamed field's old name dies
  everywhere; `extract_observation_marks` is deleted when its one consumer goes), loud
  failures, no fallbacks, no dual-carry.
- **Narrowness (`PDR-0033`), both directions, for every declaration added:** a declared
  hash that does not move → `REGISTERED_DIVERGENCE_ABSENT`; an undeclared mover → red.
- **Statics are storage, never evaluation targets:** evaluation marks may only ever contain
  expression variables. A static profile variable re-emitted by the evaluator would clobber
  runtime writes (e.g. `trial_o`'s auction state) — pinned by test in Task 5.
- Test invocation: `UV_CACHE_DIR=.uv-cache uv run pytest <path> -v`. Type gate:
  `UV_CACHE_DIR=.uv-cache uv run mypy src/townlet`.
- Work only in `src/townlet/`, `tests/test_townlet/`, `docs/`, `configs/` (config updates
  are zero-backcompat fixes, named per task).
- Commit after every task, style `feat(vfs): … (hamlet-fa6bb6da4a)` /
  `feat(oracle): …` / `test(…): …` as given per task.
- Float32 note to carry in code comments where tick is stored: exact integers up to 2^24;
  persistent-lifetime counters are `hamlet-0268336cd1`'s question, not this unit's.

---

### Task 1: Hash declarations compose — `Cell.hash_divergences` is a tuple

Two register entries must bind the same cells (DIV-006 + DIV-009 on the profile cells;
DIV-010 joins in Task 7). The single-entry `hash_divergence` field cannot express that.
Generalize: a cell declares a TUPLE of `RegisteredHashDivergence`; the union of their
fields must match the moved set exactly; each entry's own fields must all move (else that
entry is stale); refs accumulate in declaration order. The old single-entry surface is
replaced, not dual-carried.

**Files:**
- Modify: `src/townlet/oracle/matrix.py` (`Cell.hash_divergence` → `hash_divergences`,
  `_DIV006` binding site)
- Modify: `src/townlet/oracle/trace_io.py` (`compare_traces` hash block)
- Modify: `src/townlet/oracle/harness.py` (`run_cell` threading)
- Test: `tests/test_townlet/unit/oracle/test_compare.py`, `test_matrix.py`,
  `test_harness.py` (update existing single-entry call sites)

**Interfaces:**
- Produces: `Cell.hash_divergences: tuple[RegisteredHashDivergence, ...] = ()`;
  `compare_traces(old, new, cell_id, *, hash_divergences: Any = (), stream_divergence: Any = None)`
  — `hash_divergences` is a (possibly empty) sequence, loosely typed (no matrix import).
  Verdict semantics: `mismatched` keys must equal the UNION of all entries' `declared`
  sets exactly; any entry with a field absent from `mismatched` →
  `REGISTERED_DIVERGENCE_ABSENT` with `detail["register_ref"]` = that entry's ref and
  `detail["declared_but_unmoved"]` = its unmoved fields; success `register_refs` = all
  entry refs in declaration order (deduped), stream ref appended as before. Overlapping
  fields between entries are legal (two causes may move one hash).
- Consumed by: Tasks 2 and 7 (cell bindings).

- [ ] **Step 1: Write the failing tests** (append to `test_compare.py`)

```python
def test_two_hash_entries_compose_with_overlap():
    a = RegisteredHashDivergence(register_ref="DIV-006", hash_fields=("observation_schema_hash", "vfs_hash"))
    b = RegisteredHashDivergence(register_ref="DIV-009", hash_fields=("actions_hash", "vfs_hash"))
    old = _trace(hashes={"observation_schema_hash": "1", "actions_hash": "1", "vfs_hash": "1", "config_hash": "z"})
    new = _trace(hashes={"observation_schema_hash": "2", "actions_hash": "2", "vfs_hash": "2", "config_hash": "z"})
    v = compare_traces(old, new, "cell", hash_divergences=(a, b))
    assert v.kind == "DIVERGED_AS_REGISTERED"
    assert v.register_refs == ("DIV-006", "DIV-009")


def test_one_stale_entry_among_two_fails_naming_it():
    a = RegisteredHashDivergence(register_ref="DIV-006", hash_fields=("observation_schema_hash",))
    b = RegisteredHashDivergence(register_ref="DIV-009", hash_fields=("actions_hash",))
    old = _trace(hashes={"observation_schema_hash": "1", "actions_hash": "1"})
    new = _trace(hashes={"observation_schema_hash": "2", "actions_hash": "1"})  # DIV-009 never moves
    v = compare_traces(old, new, "cell", hash_divergences=(a, b))
    assert v.kind == "REGISTERED_DIVERGENCE_ABSENT"
    assert v.detail["register_ref"] == "DIV-009"
    assert v.detail["declared_but_unmoved"] == ["actions_hash"]


def test_undeclared_mover_still_red_under_composition():
    a = RegisteredHashDivergence(register_ref="DIV-006", hash_fields=("observation_schema_hash",))
    old = _trace(hashes={"observation_schema_hash": "1", "actions_hash": "1"})
    new = _trace(hashes={"observation_schema_hash": "2", "actions_hash": "2"})
    v = compare_traces(old, new, "cell", hash_divergences=(a,))
    assert v.kind == "HASH_MISMATCH"
```

and to `test_matrix.py`:

```python
def test_profile_cells_bind_hash_divergences_tuple():
    from townlet.oracle.matrix import default_cells

    for cell in default_cells():
        assert isinstance(cell.hash_divergences, tuple)
        assert not hasattr(cell, "hash_divergence")  # old field is gone, not dual-carried
```

- [ ] **Step 2: Run to verify failure**

Run: `UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/oracle/test_compare.py tests/test_townlet/unit/oracle/test_matrix.py -v -k "compose or stale_entry_among or undeclared_mover or divergences_tuple"`
Expected: FAIL — `compare_traces() got an unexpected keyword argument 'hash_divergences'`.

- [ ] **Step 3: Implement**

`matrix.py`: on `Cell`, replace the `hash_divergence` field (keep its comment, retitled
plural) with:

```python
    hash_divergences: tuple[RegisteredHashDivergence, ...] = ()
```

and the profile-cell binding becomes `hash_divergences=(_DIV006,)`.

`trace_io.py` `compare_traces`: signature `hash_divergences: Any = ()`. Rework ONLY the
hash block (streams untouched). Shape (variable names must match the existing tail, which
tests `declared` truthiness — rename that local to `union_declared` and update the tail's
two uses):

```python
    entries = tuple(hash_divergences)
    union_declared: frozenset[str] = frozenset().union(*(e.declared for e in entries)) if entries else frozenset()
    mismatched = {k: ... for ...}  # existing mismatch computation, unchanged
    if set(mismatched) != set(union_declared):
        # existing HASH_MISMATCH return, unchanged in meaning; detail gains
        # "declared": sorted(union_declared)
    for entry in entries:
        unmoved = entry.declared - set(mismatched)
        if unmoved:
            return CellVerdict(
                kind="REGISTERED_DIVERGENCE_ABSENT",
                cell_id=cell_id,
                detail={"register_ref": entry.register_ref, "declared_but_unmoved": sorted(unmoved)},
            )
```

(the exact-match check above makes per-entry `unmoved` the only remaining absence case).
In the unified success tail, `refs` starts as
`tuple(dict.fromkeys(e.register_ref for e in entries))` when `union_declared` is
non-empty, and `detail["shape"]`'s hash-side test is `bool(union_declared)`.

`harness.py` `run_cell`: `hash_divergences=cell.hash_divergences` in the
`compare_traces` call.

Update every existing test constructing `hash_divergence=hd` → `hash_divergences=(hd,)`
(grep `hash_divergence=` across `tests/test_townlet/unit/oracle/`). The
`REGISTERED_DIVERGENCE_ABSENT` hash-side detail key changes from whatever the old
single-entry code emitted to `declared_but_unmoved` — update the pre-existing stale-hash
test accordingly; do not keep the old key.

- [ ] **Step 4: Run the whole oracle unit suite**

Run: `UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/oracle/ -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/townlet/oracle/ tests/test_townlet/unit/oracle/
git commit -m "feat(oracle): registered hash divergences compose — a cell binds a tuple of entries (hamlet-fa6bb6da4a)"
```

---

### Task 2: Measure, register DIV-009, bind — the matrix returns to exit 0

Discharges `hamlet-5cc071f4b6`. Six commits landed after the oracle tag
(`oracle-2026-08-17`, worktree base `4222a917`) moving provenance hashes with no register
entry: `7cbfbff8`, `cd3557b6`, `8868f237`, `ebd16fce`, `d60104f0`/`390769af`, `03764c6b`
(unit-1 verification, runs `runs/differential/20260823-000034` and `…-000700`; streams
byte-identical, so this is provenance-declaration drift, not behaviour). Follow DIV-004's
measurement discipline: compile at each commit boundary, attribute each hash to its first
mover, adjudicate each movement as intended (they are owner-accepted Phase B landings) or
escalate if one is not explainable.

**Files:**
- Modify: `docs/oracle/known-divergences.md` (DIV-008 reservation note + DIV-009 entry)
- Modify: `src/townlet/oracle/matrix.py` (bindings)
- Test: `tests/test_townlet/unit/oracle/test_matrix.py` (binding pins)
- Scratch: measurement script + output under the plan workspace (not committed)

**Interfaces:**
- Consumes: Task 1's `hash_divergences` tuple.
- Produces: `_DIV009_STANDING`, `_DIV009_PROFILE` (same `register_ref="DIV-009"`,
  per-block `hash_fields` = exactly what measurement shows for that block); all 20 cells
  bound; matrix exit 0.

- [ ] **Step 1: Measure per-commit hash movement**

Write and run (from repo root; NOT committed — output tables go into the register entry):

```bash
mkdir -p /tmp/hashprobe && cat > /tmp/hashprobe/probe.py <<'EOF'
import json, sys
from pathlib import Path
from townlet.universe.compiler import UniverseCompiler

pack, level = sys.argv[1], sys.argv[2]
u = UniverseCompiler().compile(Path(pack), primary_level=level)
fields = [f for f in dir(u) if f.endswith("_hash")]
print(json.dumps({f: getattr(u, f) for f in fields}, sort_keys=True))
EOF
for sha in 4222a917 7cbfbff8 cd3557b6 8868f237 ebd16fce d60104f0 390769af 03764c6b HEAD; do
  git worktree add -f /tmp/hashprobe/wt-$sha $sha 2>/dev/null
  for probe in "configs/default_curriculum L1_full_observability" "configs/test/items_smoke L0_smoke" "configs/differential/div003_rect L1_full_observability"; do
    (cd /tmp/hashprobe/wt-$sha && UV_CACHE_DIR=$OLDPWD/.uv-cache PYTHONPATH=/tmp/hashprobe/wt-$sha/src \
      uv run --project $OLDPWD python /tmp/hashprobe/probe.py $probe) \
      > /tmp/hashprobe/$sha-$(echo $probe | tr '/ ' '__').json 2>/tmp/hashprobe/$sha.err || echo "PROBE FAILED $sha $probe"
  done
done
```

Adapt mechanics as needed (the profile pack's level name, `uv run` vs direct venv python —
whatever runs; the DELIVERABLE is the per-commit table of which `*_hash` fields changed
at which boundary, for one standing, one differential, and one profile pack). If a listed
commit turns out not to move any hash, or an UNLISTED commit in `4222a917..HEAD` does,
record what measurement actually shows — the six-commit list is unit-1's hypothesis, not
gospel. Note: `d60104f0`/`390769af` and any commit whose probe fails to compile get
attributed by bracketing (nearest compiling neighbors). Clean up worktrees after
(`git worktree remove --force /tmp/hashprobe/wt-<sha>` each; `git worktree prune`).

- [ ] **Step 2: Write the register entry**

In `docs/oracle/known-divergences.md`, append after DIV-007:

```markdown
## DIV-008 — RESERVED: the token-observation cut

Reserved by the approved token-observation design
(`docs/superpowers/specs/2026-08-22-token-observation-representation-design.md` §5);
registered at migration unit 3. Unit-1 code (`RegisteredStreamDivergence`) already names
it. Listed here so the numbering gap is visible, never silent.

## DIV-009 — Pre-token-cut compiler-surface hash drift: six Phase B landings moved provenance, behaviour did not
```

The DIV-009 body follows DIV-004/DIV-005's shape: what changed (per-commit table from
Step 1 — commit, subject, hash fields first moved, why that surface moves that hash);
the evidence (unit-1 runs `20260823-000034`/`20260823-000700`: all streams byte-identical
in plain AND scripted modes across all 10 CPU cells); the adjudication (each movement is
an owner-accepted landing recorded in product checkpoints — cite `ba2766e6` and the
others' subjects; ANY movement you cannot explain from its commit is a STOP-and-escalate,
not an entry line); the binding (which cell blocks declare which field sets); and the
terminal condition (retired when the oracle re-tags — an owner decision, out of scope).

- [ ] **Step 3: Bind the cells**

In `matrix.py`, from the measured tables (field tuples below are unit-1's expected
outcome — correct them to match measurement exactly):

```python
_DIV009_STANDING = RegisteredHashDivergence(
    register_ref="DIV-009",
    hash_fields=("actions_hash", "pack_brain_hash", "transition_graph_hash", "vfs_hash"),
)
_DIV009_PROFILE = RegisteredHashDivergence(
    register_ref="DIV-009",
    hash_fields=(
        "actions_hash", "pack_brain_hash", "transition_graph_hash", "vfs_hash",
        # items/effects additionally moved these two per unit-1's report — keep only if
        # measurement confirms DIV-006 alone does not already account for them exactly:
    ),
)
```

Standing + differential cells: `hash_divergences=(_DIV009_STANDING,)`. Profile cells:
`hash_divergences=(_DIV006, _DIV009_PROFILE)` — note `vfs_hash` (and possibly the two
schema hashes) overlap DIV-006; overlap is legal per Task 1. Update `default_cells()`'s
docstring paragraph about "declare nothing" — it is no longer true and must say what is
now declared and why (DIV-009). Pin in `test_matrix.py`:

```python
def test_all_cells_bind_div009():
    from townlet.oracle.matrix import default_cells

    for cell in default_cells():
        refs = [d.register_ref for d in cell.hash_divergences]
        assert "DIV-009" in refs
        assert refs == sorted(set(refs), key=refs.index)  # no duplicate entries
```

- [ ] **Step 4: Run the full CPU matrix**

Run: `UV_CACHE_DIR=.uv-cache uv run python -m townlet.oracle.harness`
Expected: **exit 0** — every CPU cell `DIVERGED_AS_REGISTERED` (refs `("DIV-009",)` or
`("DIV-006", "DIV-009")`), streams clean, CUDA `SKIPPED`. Any `HASH_MISMATCH` left means
the binding does not match measurement — fix the binding from the report.json evidence,
never by widening fields beyond what moved. Any stream divergence: STOP, that is a new
finding.

- [ ] **Step 5: Run the oracle suite, commit, close the ticket**

Run: `UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/oracle/ -v`
Expected: PASS.

```bash
git add docs/oracle/known-divergences.md src/townlet/oracle/matrix.py tests/test_townlet/unit/oracle/test_matrix.py
git commit -m "feat(oracle): DIV-009 registered and bound — the six-commit hash drift is adjudicated, matrix exit 0 (hamlet-5cc071f4b6)"
filigree close hamlet-5cc071f4b6 --actor claude-fable --comment "Discharged: measured per-commit (DIV-004 worktree method), registered as DIV-009, bound on all 20 cells via composed hash declarations; matrix exit 0 plain mode. Table in the register entry."
```

(If `filigree close` has a different flag shape, use `filigree update … --status closed`
plus `add-comment`; check `filigree close --help` first.)

---

### Task 3: The engine tick variable

Spec §6 unit 2(a): `tick` as an always-on, engine-written VFS global, independent of
`enable_temporal_mechanics`, write point pinned at the TOP of `step()` so every consumer
of that step — action executor, effects (`current_step=global_tick`), evaluator — sees
one value, and any observation of it reads the same registry cell.

**Files:**
- Modify: `src/townlet/universe/compilers/vfs.py` (`build_runtime_variables` injection +
  collision refusal)
- Modify: `src/townlet/vfs/profiles.py` (`compile_global_profile` ambient names)
- Modify: `src/townlet/environment/vectorized_env.py` (write at top of `step()`, write in
  `reset()`)
- Test: `tests/test_townlet/unit/universe/test_engine_tick_variable.py` (new),
  `tests/test_townlet/unit/environment/test_engine_tick_runtime.py` (new)

**Interfaces:**
- Produces: every compiled universe's `vfs_variables` contains
  `VariableDef(id="tick", scope="global", type="scalar", default=0.0, lifetime="episode",
  readable_by=["agent", "engine"], writable_by=["engine"])`; profile expressions may
  reference bare `tick` (ambient — type `float` in the profile type schema, excluded from
  dependency resolution); an authored variable named `tick` refuses at compile.
- Consumed by: Task 5 (liveness tests use `tick`-driven expressions), unit 5 (L3
  `day_phase` authoring).

- [ ] **Step 1: Write the failing compiler tests** (`test_engine_tick_variable.py`, new
  file; use `prepare_config_dir` from `tests.test_townlet.helpers.config_builder` and
  `UniverseCompiler` exactly as `tests/test_townlet/unit/environment/test_vectorized_env_runtime.py`
  does)

```python
"""The engine tick variable: injected always, ambient in expressions, collision-refused."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from tests.test_townlet.helpers.config_builder import PRIMARY_LEVEL_NAME, prepare_config_dir
from townlet.universe.compiler import UniverseCompiler


def _compile(config_dir: Path):
    return UniverseCompiler().compile(config_dir, primary_level=PRIMARY_LEVEL_NAME)


def _write_profiles(config_dir: Path, payload: dict) -> None:
    (config_dir / "vfs_profiles.yaml").write_text(yaml.safe_dump(payload))


_BASE_PROFILES = {
    "version": "1.0",
    "evaluation_mode": "eager",
    "debug_logging": False,
    "global_profile": {"variables": []},
    "agent_profile": None,
    "item_profiles": [{"profile_name": "default_item", "variables": []}],
}


def test_tick_variable_is_injected_into_every_universe(tmp_path):
    u = _compile(prepare_config_dir(tmp_path))
    tick = next(v for v in u.vfs_variables if v.id == "tick")
    assert str(tick.scope) in ("global", "VariableScope.GLOBAL") or tick.scope.value == "global"
    assert tick.writable_by == ["engine"]
    assert "agent" in tick.readable_by


def test_authored_variable_named_tick_refuses(tmp_path):
    config_dir = prepare_config_dir(tmp_path)
    payload = {**_BASE_PROFILES, "global_profile": {"variables": [
        {"semantic_type": "custom", "name": "tick", "type": "float", "initial_value": 0.0}
    ]}}
    _write_profiles(config_dir, payload)
    with pytest.raises(ValueError, match="tick"):
        _compile(config_dir)


def test_profile_expression_may_reference_bare_tick(tmp_path):
    config_dir = prepare_config_dir(tmp_path)
    payload = {**_BASE_PROFILES, "global_profile": {"variables": [
        {"semantic_type": "custom", "name": "double_tick", "type": "float", "expression": "tick * 2.0"}
    ]}}
    _write_profiles(config_dir, payload)
    u = _compile(config_dir)
    gp = u.compiled_vfs_profiles.global_profile
    assert any(v.name == "double_tick" for v in gp.variables)
    # tick is ambient, never an in-profile dependency edge:
    assert "tick" not in (gp.dependencies or {}).get("double_tick", ())
```

(Adjust the scope assertion to whatever `VariableDef.scope` actually is — enum or str —
after reading `townlet/vfs/schema.py`; assert its `.value`/string equals `"global"`.
`prepare_config_dir`'s template pack may or may not carry a `vfs_profiles.yaml` — read
`tests/test_townlet/helpers/config_builder.py` and the template it copies; `_write_profiles`
overwrites or creates it at pack root.)

- [ ] **Step 2: Write the failing runtime tests** (`test_engine_tick_runtime.py`, new)

```python
"""Runtime tick: written at the top of step, zeroed on reset, engine-only."""

from __future__ import annotations

import pytest
import torch

from tests.test_townlet.helpers.config_builder import PRIMARY_LEVEL_NAME, prepare_config_dir
from townlet.universe.compiler import UniverseCompiler


def _make_env(tmp_path, num_agents=2):
    u = UniverseCompiler().compile(prepare_config_dir(tmp_path), primary_level=PRIMARY_LEVEL_NAME)
    env = u.create_environment(num_agents=num_agents, level_name=PRIMARY_LEVEL_NAME, device="cpu")
    env.reset()
    return env


def _tick_value(env) -> float:
    return float(env.vfs_registry.get("tick", reader="engine").reshape(-1)[0])


def test_tick_counts_steps_and_resets(tmp_path):
    env = _make_env(tmp_path)
    assert _tick_value(env) == 0.0
    for k in range(3):
        env.step(torch.zeros(env.num_agents, dtype=torch.long, device=env.device))
    assert _tick_value(env) == float(env.global_tick)
    env.reset()
    assert _tick_value(env) == 0.0


def test_tick_is_engine_writable_only(tmp_path):
    env = _make_env(tmp_path)
    with pytest.raises(PermissionError):
        env.vfs_registry.set("tick", torch.tensor(99.0), writer="agent")
```

(WAIT action id 0 assumption: use whatever no-op action the template pack guarantees —
read the pack's `actions.yaml`; any valid action id works, the test only counts steps.)

- [ ] **Step 3: Run to verify failure**

Run: `UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/universe/test_engine_tick_variable.py tests/test_townlet/unit/environment/test_engine_tick_runtime.py -v`
Expected: FAIL — `StopIteration` (no tick variable) / compile succeeds where refusal
expected / registry `KeyError: tick`.

- [ ] **Step 4: Implement**

`compilers/vfs.py`, top of module:

```python
_ENGINE_TICK_ID = "tick"


def _engine_tick_variable_def() -> VariableDef:
    return VariableDef(
        id=_ENGINE_TICK_ID,
        scope="global",
        type="scalar",
        default=0.0,
        lifetime="episode",
        readable_by=["agent", "engine"],
        writable_by=["engine"],
        # float32 storage is integer-exact to 2^24; persistent-lifetime counters are
        # hamlet-0268336cd1's question, not this variable's contract.
        description="Engine-written step counter — the one temporal primitive (token-obs design ruling 6).",
    )
```

In `build_runtime_variables`: prepend `variables = [_engine_tick_variable_def(), *base_variables]`,
then after assembling ALL variables (profiles + statics included), refuse collisions:

```python
        clashes = [v.id for v in variables[1:] if v.id == _ENGINE_TICK_ID]
        if clashes:
            raise ValueError(
                "Variable id 'tick' is reserved for the engine-written step counter "
                "(token-obs design ruling 6). Rename the authored variable."
            )
```

(also refuse a profile variable NAMED `tick` before it becomes a VariableDef — the
profile loop converts names to ids, so the single check above catches both paths; verify
with the Step-1 test).

`vfs/profiles.py` `compile_global_profile`: admit ambient names. Read the function first;
the required behaviour is (a) the type schema used for expression checking gains
`{"tick": "float"}`, (b) `tick` never appears in `dependencies` nor triggers the
undefined-variable refusal. Implement as a module constant
`AMBIENT_ENGINE_NAMES = {"tick": "float"}` consumed at both the schema-build and the
dependency-extraction filter (`_extract_variable_refs` callers subtract ambient names).
Item profiles do NOT get ambient `tick` (item expressions refuse entirely in Task 6).

`vectorized_env.py`:
- In `step()`, as the FIRST statements (before action execution — find `def step(` and
  place ahead of everything that consumes `global_tick`):

```python
        # Pinned tick write point (token-obs unit 2): every consumer of THIS step —
        # action executor, effects (current_step), evaluator — sees this one value,
        # and any read of the registry's tick returns the same.
        self.vfs_registry.set_engine_value("tick", torch.tensor(float(self.global_tick), device=self.device))
```

- In `reset()`, immediately after `self.global_tick = 0`: the same write. Match the
  registry's global-scalar storage shape — read `VariableRegistry` allocation for
  scope-global scalars first and shape the tensor accordingly (0-dim vs `[1]`); the
  `set_engine_value` validation will refuse a wrong shape loudly, which is the point.

- [ ] **Step 5: Run the new tests, then the affected suites**

Run: `UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/universe/ tests/test_townlet/unit/environment/ tests/test_townlet/unit/vfs/ tests/test_townlet/unit/expression/ -v`
Expected: PASS. If a pre-existing test pins the exact `vfs_variables` set or
`variable_schema_hash` literal, update it — the tick variable is now part of every
universe (that is the feature, not a regression). Do NOT run the oracle matrix here; its
hash adjudication for this change lands in Task 7.

- [ ] **Step 6: Commit**

```bash
git add src/townlet/universe/compilers/vfs.py src/townlet/vfs/profiles.py src/townlet/environment/vectorized_env.py tests/
git commit -m "feat(vfs): the engine tick variable — always-on, engine-written, ambient in profile expressions (hamlet-fa6bb6da4a)"
```

---

### Task 4: One temporal pipeline — `time_of_day` derives from `global_tick`

Spec §6 unit 2(c). Today `time_of_day` is a second, independently incremented counter
(`vectorized_env.py:1125-1129`, plus init at `:358` and reset at `:830`). Replace the
independent increment with a derivation AT THE SAME UPDATE POINT, so every existing read
(action gate at phase 1, evaluator context at 3.6, reward calculator at phase 6 —
`reward_calculator.py:39` reads it AFTER `global_tick` incremented but BEFORE the old
update line, which is why the update point must not move) sees byte-identical values.

**Files:**
- Modify: `src/townlet/environment/vectorized_env.py` (three sites above)
- Test: `tests/test_townlet/unit/environment/test_temporal_pipeline.py` (new)

**Interfaces:**
- Produces: the invariant `env.time_of_day == (env.global_tick % env.day_length if
  env.enable_temporal_mechanics else 0)` at every step boundary; no second counter.
- Consumed by: unit 5 (L3 `day_phase` authoring), unit 6 (temporal-block deletion).

- [ ] **Step 1: Write the failing test**

```python
"""time_of_day is a derivation of global_tick — one temporal pipeline."""

from __future__ import annotations

import inspect

import torch

from tests.test_townlet.helpers.config_builder import PRIMARY_LEVEL_NAME, prepare_config_dir
from townlet.universe.compiler import UniverseCompiler
import townlet.environment.vectorized_env as vec_mod


def test_no_independent_time_of_day_increment_remains():
    src = inspect.getsource(vec_mod)
    assert "self.time_of_day + 1" not in src  # the second bookkeeping is gone


def test_time_of_day_equals_tick_mod_day_length_on_temporal_pack(tmp_path):
    # L3 is the shipped temporal level; compile the real pack read-only.
    u = UniverseCompiler().compile(Path("configs/default_curriculum"), primary_level="L3_temporal_mechanics")
    env = u.create_environment(num_agents=2, level_name="L3_temporal_mechanics", device="cpu")
    env.reset()
    day = int(env.day_length)
    for k in range(1, 2 * day + 2):
        env.step(torch.zeros(env.num_agents, dtype=torch.long, device=env.device))
        assert env.time_of_day == env.global_tick % day == k % day


def test_time_of_day_is_zero_without_temporal_mechanics(tmp_path):
    u = UniverseCompiler().compile(prepare_config_dir(tmp_path), primary_level=PRIMARY_LEVEL_NAME)
    env = u.create_environment(num_agents=1, level_name=PRIMARY_LEVEL_NAME, device="cpu")
    env.reset()
    env.step(torch.zeros(1, dtype=torch.long, device=env.device))
    assert env.time_of_day == 0
```

(add `from pathlib import Path` to imports; if stepping the full L3 pack for `2*day+2`
steps is slow, drop to `day + 2` — the wraparound assertion is the point. Dones: agents
may die under zeroed actions; the invariant must hold regardless, and `step()` keeps
running after dones in this engine — verify and, if an episode hard-stops, `env.reset()`
inside the loop and continue counting from the new tick.)

- [ ] **Step 2: Run to verify failure**

Run: `UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/environment/test_temporal_pipeline.py -v`
Expected: `test_no_independent_time_of_day_increment_remains` FAILS (the `+ 1` line
exists); the invariant tests may already pass — that is fine and expected (the derivation
is byte-identical by design; the failing source-scan test is what forces the change).

- [ ] **Step 3: Implement**

In `step()`, replace lines `1125-1129` (`# 6. Increment time of day…` block) with:

```python
        # 6. time_of_day is DERIVED from global_tick at this same point in the step —
        # one temporal pipeline (token-obs unit 2c). The update point is load-bearing:
        # the reward calculator reads time_of_day between the global_tick increment and
        # here, and moving this line changes reward timing against the pinned oracle.
        self.time_of_day = (self.global_tick % int(self.day_length)) if self.enable_temporal_mechanics else 0
```

Wait — check the arithmetic against the OLD sequence before committing: old code
incremented `time_of_day` by 1 with wraparound after `global_tick` was incremented at
line 1096, so at this point old `time_of_day` = (previous value + 1) % D and previous
value entering the step equalled `global_tick_entering % D`. With
`global_tick = k+1` here, `(k+1) % D` equals the old result. The reset/init sites
(`:358`, `:830`) keep their `= 0` assignments (both counters zero together — the
derivation holds there trivially).

- [ ] **Step 4: Run the tests + environment suite**

Run: `UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/environment/ -v`
Expected: PASS — especially every pre-existing temporal/L2/L3 test, byte-untouched.

- [ ] **Step 5: Commit**

```bash
git add src/townlet/environment/vectorized_env.py tests/test_townlet/unit/environment/test_temporal_pipeline.py
git commit -m "feat(env): time_of_day derives from global_tick — the second temporal bookkeeping dies (hamlet-fa6bb6da4a)"
```

---

### Task 5: Evaluation marks derive from exposure — expressions evaluate on the shipped default

Discharges `hamlet-df3a96bbac`. Today marks come ONLY from the optional
`variables_reference.yaml` overlay (`extract_observation_marks`, consumed at
`universe/compiler.py:471-480`, threaded as `CompiledUniverse.vfs_observation_marks`,
read at `vectorized_env.py:1062`) — absent the overlay, `mark_and_sweep` evaluates
nothing, forever. Mark-and-sweep's own definition ("only evaluate observed variables")
gives the fix: a profile EXPRESSION variable whose `exposed_to` names an observer is
observed, so it is marked. Statics are never marked (they are storage — re-evaluating
one clobbers runtime writes). The field is renamed to what it is.

**Files:**
- Modify: `src/townlet/universe/compilers/vfs.py` (delete `extract_observation_marks`,
  add `derive_evaluation_marks`)
- Modify: `src/townlet/universe/compiler.py`, `src/townlet/universe/pipeline.py`,
  `src/townlet/universe/compiled.py` (field rename `vfs_observation_marks` →
  `vfs_evaluation_marks`: dataclass field, `REQUIRED_FIELDS` at `compiled.py:102`,
  serialize at `:397`, deserialize at `:618`, `to_level` deepcopy at `:339`)
- Modify: `src/townlet/environment/vectorized_env.py` (`_initialize_vfs_subsystem` +
  the `marks =` line in `step()`)
- Modify: `configs/test/vfs_profiles_smoke/vfs_profiles.yaml` (`is_night` expression:
  `"temporal.tick % 24 >= 18"` → `"tick % 24 >= 18"` — the marks fix makes it evaluate,
  and `temporal.*` is empty on non-temporal packs; bare ambient `tick` is Task 3's
  surface. Zero-backcompat: the config is updated, not accommodated)
- Test: `tests/test_townlet/unit/universe/test_evaluation_marks.py` (new),
  `tests/test_townlet/unit/environment/test_profile_evaluation_liveness.py` (new)

**Interfaces:**
- Produces: `CompiledUniverse.vfs_evaluation_marks: dict[str, set[str]] | None` —
  per-scope (`"global"`, `"agent"`) sets containing EXACTLY the expression variables
  whose `exposed_to` is non-empty, unioned with overlay-`observable` marks intersected
  with expression-variable names. `VFSCompiler.derive_evaluation_marks(profiles_config:
  VFSProfilesConfig | None, overlay_variables: tuple[VariableDef, ...] | None) ->
  dict[str, set[str]] | None`. The env passes `marks.get("global", set())` to the global
  call (and Task 6 passes `marks.get("agent", set())`).
- Consumed by: Task 6.

- [ ] **Step 1: Write the failing compiler tests** (`test_evaluation_marks.py`)

```python
"""Evaluation marks derive from exposure: expression vars only, statics never."""

from __future__ import annotations

from pathlib import Path

import yaml

from tests.test_townlet.helpers.config_builder import PRIMARY_LEVEL_NAME, prepare_config_dir
from townlet.universe.compiler import UniverseCompiler


def _compile_with_profiles(tmp_path, profile_payload):
    config_dir = prepare_config_dir(tmp_path)
    (config_dir / "vfs_profiles.yaml").write_text(yaml.safe_dump(profile_payload))
    return UniverseCompiler().compile(config_dir, primary_level=PRIMARY_LEVEL_NAME)


def test_expression_variables_are_marked_without_any_overlay(tmp_path):
    u = _compile_with_profiles(tmp_path, {
        "version": "1.0", "evaluation_mode": "mark_and_sweep", "debug_logging": False,
        "global_profile": {"variables": [
            {"semantic_type": "custom", "name": "base", "type": "float", "initial_value": 1.0},
            {"semantic_type": "custom", "name": "derived", "type": "float", "expression": "base + 1.0"},
        ]},
        "agent_profile": {"variables": [
            {"semantic_type": "custom", "name": "flag", "type": "bool", "expression": "bar.energy < 0.2"},
        ]},
        "item_profiles": [{"profile_name": "default_item", "variables": []}],
    })
    assert u.vfs_evaluation_marks == {"global": {"derived"}, "agent": {"flag"}}


def test_statics_are_never_marked(tmp_path):
    u = _compile_with_profiles(tmp_path, {
        "version": "1.0", "evaluation_mode": "mark_and_sweep", "debug_logging": False,
        "global_profile": {"variables": [
            {"semantic_type": "custom", "name": "counter", "type": "int", "initial_value": 0},
        ]},
        "agent_profile": None,
        "item_profiles": [{"profile_name": "default_item", "variables": []}],
    })
    assert not (u.vfs_evaluation_marks or {}).get("global")


def test_old_field_name_is_gone(tmp_path):
    u = _compile_with_profiles(tmp_path, {
        "version": "1.0", "evaluation_mode": "eager", "debug_logging": False,
        "global_profile": None, "agent_profile": None,
        "item_profiles": [{"profile_name": "default_item", "variables": []}],
    })
    assert not hasattr(u, "vfs_observation_marks")
```

- [ ] **Step 2: Write the failing liveness test** (`test_profile_evaluation_liveness.py`)

```python
"""hamlet-df3a96bbac: expressions evaluate on the shipped default shape —
mark_and_sweep, no variables_reference.yaml."""

from __future__ import annotations

import torch
import yaml

from tests.test_townlet.helpers.config_builder import PRIMARY_LEVEL_NAME, prepare_config_dir
from townlet.universe.compiler import UniverseCompiler


def _make_env(tmp_path, profile_payload, num_agents=2):
    config_dir = prepare_config_dir(tmp_path)
    (config_dir / "vfs_profiles.yaml").write_text(yaml.safe_dump(profile_payload))
    ref = config_dir / "variables_reference.yaml"
    if ref.exists():
        ref.unlink()  # the shipped-default shape: NO overlay file
    u = UniverseCompiler().compile(config_dir, primary_level=PRIMARY_LEVEL_NAME)
    env = u.create_environment(num_agents=num_agents, level_name=PRIMARY_LEVEL_NAME, device="cpu")
    env.reset()
    return env


_PROFILES = {
    "version": "1.0", "evaluation_mode": "mark_and_sweep", "debug_logging": False,
    "global_profile": {"variables": [
        {"semantic_type": "custom", "name": "stash", "type": "float", "initial_value": 1.0},
        {"semantic_type": "custom", "name": "tick_echo", "type": "float", "expression": "tick * 2.0"},
    ]},
    "agent_profile": None,
    "item_profiles": [{"profile_name": "default_item", "variables": []}],
}


def _global_value(env, name) -> float:
    return float(env.vfs_registry.get(name, reader="engine").reshape(-1)[0])


def test_global_expression_advances_under_mark_and_sweep_default(tmp_path):
    env = _make_env(tmp_path, _PROFILES)
    for _ in range(3):
        env.step(torch.zeros(env.num_agents, dtype=torch.long, device=env.device))
    # evaluator ran at tick k-1 on the last step (pre-increment) — the value MOVED,
    # which is the whole ticket; pin the exact phase relation:
    assert _global_value(env, "tick_echo") == 2.0 * (env.global_tick - 1)


def test_static_survives_engine_write_unclobbered(tmp_path):
    env = _make_env(tmp_path, _PROFILES)
    env.vfs_registry.set_engine_value("stash", torch.tensor(7.0))
    env.step(torch.zeros(env.num_agents, dtype=torch.long, device=env.device))
    assert _global_value(env, "stash") == 7.0  # statics are storage, never re-evaluated
```

(Shape the `set_engine_value` tensor to the registry's global-scalar storage, as in
Task 3.)

- [ ] **Step 3: Run to verify failure**

Run: `UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/universe/test_evaluation_marks.py tests/test_townlet/unit/environment/test_profile_evaluation_liveness.py -v`
Expected: FAIL — `AttributeError: vfs_evaluation_marks` / `tick_echo` frozen at its
default (the empty-mark inertness this task kills).

- [ ] **Step 4: Implement**

`compilers/vfs.py`: DELETE `extract_observation_marks` (its one consumer is replaced).
Add:

```python
    def derive_evaluation_marks(
        self,
        profiles_config: VFSProfilesConfig | None,
        overlay_variables: tuple[VariableDef, ...] | None,
    ) -> dict[str, set[str]] | None:
        """Marks = the expression variables observation can see.

        Mark-and-sweep means "only evaluate observed variables". A profile EXPRESSION
        variable whose exposed_to names an observer is observed, so it is marked; the
        optional variables_reference.yaml overlay may mark additional profile expression
        variables via `observable`. Statics are NEVER marked: they are storage, and
        re-emitting their initial value would clobber runtime writes. (hamlet-df3a96bbac)
        """
        if profiles_config is None:
            return None
        overlay_observable = {v.id for v in (overlay_variables or ()) if getattr(v, "observable", False)}
        marks: dict[str, set[str]] = {}
        for scope_key, profile in (("global", profiles_config.global_profile), ("agent", profiles_config.agent_profile)):
            if profile is None:
                continue
            expression_vars = {v.name for v in profile.variables if v.expression is not None}
            exposed = {v.name for v in profile.variables if v.expression is not None and v.exposed_to}
            scoped = exposed | (overlay_observable & expression_vars)
            if scoped:
                marks[scope_key] = scoped
        return marks or {}
```

`universe/compiler.py`: at the `extract_observation_marks` call site (`:471-480`),
replace with `derive_evaluation_marks(profiles_config, raw.variables_reference)` —
read the surrounding code for the actual local names carrying the raw profiles config
and overlay tuple; thread the renamed field through `pipeline.py:51` and both compiler
call chains (`:496`, `:541`).

`compiled.py`: rename the field everywhere listed above (dataclass, `REQUIRED_FIELDS`,
serializer key, deserializer `_required_field` key, `to_level`). Old `.compiled` caches
now refuse loudly on the missing field — correct behaviour, no shim.

`vectorized_env.py`: `_initialize_vfs_subsystem` stores
`self.vfs_evaluation_marks = universe.vfs_evaluation_marks` (rename both branches); the
`step()` marks line becomes:

```python
                marks = self.vfs_evaluation_marks.get("global", set()) if self.vfs_evaluation_marks else set()
```

`configs/test/vfs_profiles_smoke/vfs_profiles.yaml`: `is_night` expression →
`"tick % 24 >= 18"`.

Grep `vfs_observation_marks` repo-wide (src, tests, docs config-schemas) — zero hits
must remain outside `docs/` history notes; update any test constructing universes with
the old kwarg.

- [ ] **Step 5: Run the suites**

Run: `UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/universe/ tests/test_townlet/unit/environment/ tests/test_townlet/unit/vfs/ tests/test_townlet/unit/expression/ -v && UV_CACHE_DIR=.uv-cache uv run mypy src/townlet`
Expected: PASS, mypy clean.

- [ ] **Step 6: Commit + ticket**

```bash
git add src/townlet/ tests/ configs/test/vfs_profiles_smoke/
git commit -m "feat(vfs): evaluation marks derive from exposure — expressions evaluate on the shipped default (hamlet-df3a96bbac)"
filigree add-comment hamlet-df3a96bbac --actor claude-fable "Discharged in token-obs unit 2: marks derive from exposure (expression vars only), field renamed vfs_evaluation_marks, overlay observable retained as additive marks, statics never marked (clobber pinned by test). Close on unit-2 verification (Task 7)."
```

---

### Task 6: Agent-profile evaluation builds; item-profile expressions refuse

Spec §6 unit 2(d), ruled BUILD for agent / REFUSE for item: the agent profile compiles
through the same `CompiledGlobalProfile` machinery and its expressions already produce
`[num_agents]`-shaped tensors from `bar.*` references — the missing piece is literally
the second evaluation call (`hamlet-5d74335111`: one call site, global only). Item
profiles have no evaluator, no bar namespace, and zero users
(`grep "expression:" configs/**/vfs_profiles.yaml` shows none under `item_profiles`) —
they refuse at compile until an evaluation build has a consumer (`hamlet-bc0a5deeff`:
never silently inert).

**Files:**
- Modify: `src/townlet/environment/vectorized_env.py` (`step()` — agent evaluation call
  after the global write-back)
- Modify: `src/townlet/vfs/profiles.py` (`compile_item_profile` refusal)
- Test: extend `tests/test_townlet/unit/environment/test_profile_evaluation_liveness.py`;
  `tests/test_townlet/unit/vfs/test_item_profile_expression_refusal.py` (new)

**Interfaces:**
- Consumes: Task 5's `vfs_evaluation_marks["agent"]`; Task 3's ambient `tick`.
- Produces: agent-profile expression variables evaluate every step under their marks;
  write-back requires exact shape `(num_agents,)` else `ValueError` naming the variable
  and shapes (no scalar broadcast — a constant belongs in `initial_value`); item-profile
  variables with `expression` refuse at compile citing `hamlet-bc0a5deeff`.

- [ ] **Step 1: Write the failing tests** (append to `test_profile_evaluation_liveness.py`)

```python
_AGENT_PROFILES = {
    "version": "1.0", "evaluation_mode": "mark_and_sweep", "debug_logging": False,
    "global_profile": None,
    "agent_profile": {"variables": [
        {"semantic_type": "custom", "name": "wealth_static", "type": "float", "initial_value": 1.0},
        {"semantic_type": "custom", "name": "low_energy", "type": "bool", "expression": "bar.energy < 2.0"},
    ]},
    "item_profiles": [{"profile_name": "default_item", "variables": []}],
}


def test_agent_expression_evaluates_per_agent(tmp_path):
    env = _make_env(tmp_path, _AGENT_PROFILES)
    env.step(torch.zeros(env.num_agents, dtype=torch.long, device=env.device))
    value = env.vfs_registry.get("low_energy", reader="engine")
    assert value.shape[0] == env.num_agents
    # bars are normalized [0,1] in this engine, so energy < 2.0 is true for every agent —
    # the assertion is that the expression RAN and wrote per-agent, not its economics:
    assert bool(value.reshape(-1).all())


def test_agent_static_is_never_clobbered(tmp_path):
    env = _make_env(tmp_path, _AGENT_PROFILES)
    env.vfs_registry.set_engine_value("wealth_static", torch.full((env.num_agents,), 9.0))
    env.step(torch.zeros(env.num_agents, dtype=torch.long, device=env.device))
    assert float(env.vfs_registry.get("wealth_static", reader="engine").reshape(-1)[0]) == 9.0
```

and the refusal test (`test_item_profile_expression_refusal.py`):

```python
"""hamlet-bc0a5deeff: item-profile expressions have no evaluator — refuse at compile."""

from __future__ import annotations

import pytest

from townlet.config.vfs_profiles_config import ItemVFSProfileConfig
from townlet.vfs.profiles import VFSProfileCompiler


def test_item_profile_expression_refuses_at_compile():
    profile = ItemVFSProfileConfig(
        profile_name="p",
        variables=[{"name": "rot", "type": "float", "expression": "1.0"}],
    )
    with pytest.raises(ValueError, match="hamlet-bc0a5deeff"):
        VFSProfileCompiler().compile_item_profile(profile, bar_schema={})
```

(match `compile_item_profile`'s real signature — read it first; pass whatever
`bar_schema`/kwargs it requires.)

- [ ] **Step 2: Run to verify failure**

Run: `UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/environment/test_profile_evaluation_liveness.py tests/test_townlet/unit/vfs/test_item_profile_expression_refusal.py -v -k "agent or item_profile_expression"`
Expected: agent tests FAIL (`low_energy` never evaluated — the zero-call-sites ticket);
refusal test FAILS (compile currently succeeds).

- [ ] **Step 3: Implement**

`vectorized_env.py`, in `step()` immediately after the global-profile write-back loop
(same guard structure, same context builder — the context is already batched
`[num_agents]` for bars):

```python
            agent_profile = self.universe.compiled_vfs_profiles.agent_profile
            if agent_profile is not None:
                agent_marks = self.vfs_evaluation_marks.get("agent", set()) if self.vfs_evaluation_marks else set()
                updated_agent_vfs = self.vfs_evaluator.evaluate_global_profile(
                    profile=agent_profile,
                    bars=bars_dict_vfs,
                    vfs_state=current_vfs_state,
                    marks=agent_marks,
                    device=self.device,
                    step=self.global_tick,
                    affordances=self._build_vfs_affordance_context(),
                    temporal=self._build_vfs_temporal_context(),
                    agent_positions=self.positions.to(dtype=torch.float32, device=self.device),
                    affordance_positions={k: v.to(dtype=torch.float32, device=self.device) for k, v in self.affordances.items()},
                    vfs_types={name: var.type for name, var in self.vfs_registry.variables.items()},
                    num_agents=self.num_agents,
                    item_vfs=self.vfs_registry.item_vfs,
                    item_profile_map=self.vfs_registry.item_profile_map,
                    item_index_to_profile=self.vfs_registry.item_vfs_index_to_profile,
                )
                for var_name, value in updated_agent_vfs.items():
                    if var_name not in self.vfs_registry.variables:
                        continue  # unknown-id policy unchanged this unit (hamlet-0ddc83e377 → unit 3)
                    if value.shape != (self.num_agents,):
                        raise ValueError(
                            f"Agent-profile variable '{var_name}' evaluated to shape {tuple(value.shape)}, "
                            f"expected ({self.num_agents},). A constant belongs in initial_value, not an expression."
                        )
                    self.vfs_registry.set_engine_value(var_name, value)
```

Note the evaluator re-emits STATICS for marked... no: marks contain only expression
variables (Task 5's derivation), and the evaluator evaluates only marked variables plus
their in-profile dependencies. A static that IS a dependency of a marked expression will
be re-emitted at its initial value by the evaluator loop — read
`evaluator.py:177-192` and confirm whether `result` includes dependency statics; if it
does, filter the write-back to `var.ast is not None` variables (build the name set from
`agent_profile.variables` once) so statics are NEVER written back, and add the same
filter to the GLOBAL write-back loop above it. Pin with the two static-clobber tests
(global one exists from Task 5; agent one here — extend `_PROFILES` in the global test so
its static is a dependency of the expression, making the filter load-bearing, e.g.
`"tick_echo"` → `"stash + tick * 2.0"` and update the expected value to `7.0 + 2.0*(k-1)`
in `test_static_survives…` and `1.0 + 2.0*(k-1)` in the advance test).

`vfs/profiles.py` `compile_item_profile`: first statement —

```python
        for var in profile.variables:
            if var.expression is not None:
                raise ValueError(
                    f"Item-profile variable '{var.name}' declares an expression, but item-profile "
                    "expressions have no evaluator (hamlet-bc0a5deeff) — nothing would ever run it. "
                    "Declare initial_value and drive the variable via effects, or wait for the "
                    "evaluation build. Refusing loudly beats silent inertness."
                )
```

- [ ] **Step 4: Run the suites**

Run: `UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/environment/ tests/test_townlet/unit/vfs/ tests/test_townlet/unit/universe/ -v && UV_CACHE_DIR=.uv-cache uv run mypy src/townlet`
Expected: PASS, mypy clean. (No shipped or fixture pack declares an item-profile
expression, so the refusal breaks no pack — re-verify with the grep from the task
preamble and say so in the report.)

- [ ] **Step 5: Commit + tickets**

```bash
git add src/townlet/ tests/
git commit -m "feat(vfs): agent-profile expressions evaluate; item-profile expressions refuse at compile (hamlet-5d74335111, hamlet-bc0a5deeff)"
filigree add-comment hamlet-5d74335111 --actor claude-fable "Discharged in token-obs unit 2: second evaluation call wired (agent profile, per-agent shapes enforced loudly, statics filtered from write-back). Close on unit-2 verification (Task 7)."
filigree add-comment hamlet-bc0a5deeff --actor claude-fable "Discharged in token-obs unit 2: item-profile expression variables refuse at compile, naming this ticket. Evaluate-or-refuse, never silently inert. Close on unit-2 verification (Task 7)."
```

---

### Task 7: Measure DIV-010, bind, verify the whole unit

The unit's acceptance: unit-2's own compile-surface movement is measured (same worktree
method, baseline = Task 2's end commit), registered as DIV-010, bound beside DIV-009 —
then the matrix exits 0 in BOTH modes with every stream byte-identical, proving the
build changed provenance and nothing else.

**Files:**
- Modify: `docs/oracle/known-divergences.md` (DIV-010 entry)
- Modify: `src/townlet/oracle/matrix.py` (bindings gain the DIV-010 entry)
- Test: `tests/test_townlet/unit/oracle/test_matrix.py` (binding pin extended)
- No other src changes (a failure here is a finding — report it, do not paper over it)

- [ ] **Step 1: Measure unit-2 movement**

Re-run Task 1 Step 1's probe with two worktrees only: Task 2's end commit vs HEAD, same
three packs. Expected movement: `variable_schema_hash` + `vfs_hash` everywhere (the tick
VariableDef); possibly others if the marks field participates in a hash — the
measurement, not the expectation, writes the entry. Any STREAM-relevant surprise
(`observation_schema_hash` moving) means an observation surface moved — STOP and
diagnose before registering anything.

- [ ] **Step 2: Register DIV-010**

Append to `docs/oracle/known-divergences.md`:

```markdown
## DIV-010 — Authored temporality (token-obs unit 2): the engine tick variable and derived evaluation marks move compiled provenance, behaviour does not
```

Body per DIV-004's shape: what changed (tick VariableDef injected into every universe;
`vfs_observation_marks` → `vfs_evaluation_marks` with exposure-derived content), the
measured field table per pack block, why streams cannot move (tick is not observed —
not in any observation spec; no fixture pack declares a profile expression or an agent
profile, verified by grep, so evaluation fixes fire nowhere on fixture cells), the
binding, and the terminal condition (superseded by the token cut's DIV-008 entry or
retired at re-tag).

- [ ] **Step 3: Bind**

`matrix.py`: `_DIV010 = RegisteredHashDivergence(register_ref="DIV-010",
hash_fields=(<measured>))` — appended to every cell's tuple: standing/differential
`(_DIV009_STANDING, _DIV010)`, profile `(_DIV006, _DIV009_PROFILE, _DIV010)`. Extend
`test_all_cells_bind_div009` to assert `"DIV-010" in refs` too (rename it
`test_all_cells_bind_the_drift_and_unit2_entries`).

- [ ] **Step 4: Full CPU matrix, both modes**

Run: `UV_CACHE_DIR=.uv-cache uv run python -m townlet.oracle.harness`
Then: `UV_CACHE_DIR=.uv-cache uv run python -m townlet.oracle.harness --scripted`
Expected: **exit 0 in both**, every CPU cell `DIVERGED_AS_REGISTERED` with exactly the
composed refs, every stream byte-identical (the scripted run is the dynamics proof:
identical actions in, identical `rewards`/`dones`/`obs` out, with the L3 cell covering
the temporal pipeline change). Any stream divergence or `HASH_MISMATCH`: STOP — that is
a defect in this unit (most likely the time_of_day derivation or an accidental
observation change); diagnose against the per-cell report.json before touching anything.

- [ ] **Step 5: Full gates**

Run: `UV_CACHE_DIR=.uv-cache uv run mypy src/townlet && UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/ tests/test_townlet/integration/ -v`
Expected: mypy clean, all PASS (the integration dir includes unit-1's RNG stability
test — still green).

- [ ] **Step 6: Record, close tickets, commit, push**

```bash
filigree add-comment hamlet-fa6bb6da4a --actor claude-fable "Unit 2 (authored temporality) landed: composed hash declarations; DIV-009 registered+bound (drift catch-up discharged, hamlet-5cc071f4b6 closed); engine tick VFS variable (always-on, ambient in expressions, pinned write point); time_of_day derived from global_tick; evaluation marks derive from exposure (hamlet-df3a96bbac); agent-profile evaluation live (hamlet-5d74335111); item-profile expressions refuse (hamlet-bc0a5deeff); DIV-010 registered+bound. Verification: matrix exit 0 plain AND scripted (run ids: <fill from runs/differential/>), streams byte-identical, full suites + mypy green."
filigree close hamlet-df3a96bbac --actor claude-fable
filigree close hamlet-5d74335111 --actor claude-fable
filigree close hamlet-bc0a5deeff --actor claude-fable
git add docs/oracle/known-divergences.md src/townlet/oracle/matrix.py tests/test_townlet/unit/oracle/test_matrix.py
git commit -m "feat(oracle): DIV-010 registered and bound — unit 2's provenance movement adjudicated, matrix green both modes (hamlet-fa6bb6da4a)"
git push origin project-recovery-2
```

(Same `filigree close` caveat as Task 2. The three closes belong here, after
verification, not at their landing tasks — their comments there say so.)

---

## Self-review notes (done at plan time)

- **Spec coverage:** (a) tick always-on, pinned write point → Task 3; (b) shipped-default
  evaluation → Task 5; (c) one temporal pipeline → Task 4; (d) scope decision recorded —
  agent BUILD (Task 6), item REFUSE (Task 6), the decision text lives in the tasks and
  the ticket comments. Oracle discipline → Tasks 1, 2, 7 (record-then-bind, measured
  entries, streams-never-move). `hamlet-5cc071f4b6` → Task 2.
- **Deliberately NOT in this unit:** silent unknown-id write-back drop (hamlet-0ddc83e377,
  unit 3 — Task 6 preserves it with a pointer comment); `exposed_to` fail-open
  (hamlet-d97b4d6b4a, unit 3 — Task 5's derivation deliberately rides today's fail-open,
  and narrows automatically when unit 3 makes exposure explicit); normalization
  (unit 3); the temporal block and `temporal.*` expression namespace (die at unit 6 —
  untouched here for byte-stability); spawn-condition ambient `tick` (no consumer, YAGNI);
  the unit-3 carry-forward batch from unit 1 (fa6bb6da4a comment 234).
- **Type consistency:** `hash_divergences` (tuple) name matches across matrix/trace_io/
  harness/tests; `vfs_evaluation_marks` across compiled/pipeline/compiler/env;
  `derive_evaluation_marks` consumes `VFSProfilesConfig` (raw DTO — exposed_to lives
  there, NOT on `CompiledVariable`); `_ENGINE_TICK_ID` used at both injection and
  collision check; `evaluate_global_profile` reused verbatim for the agent profile
  (compiled agent profiles ARE `CompiledGlobalProfile`, per `compiled.py:128-130`).
- **Known judgement calls carried in the plan:** DIV-008 stays reserved (visible note);
  drift and unit-2 movement are TWO entries (distinct causes, composed on cells); statics
  filtered from write-back in BOTH profile loops (clobber tests make it load-bearing);
  agent write-back requires exact `(num_agents,)` (constants belong in initial_value);
  `vfs_profiles_smoke`'s `temporal.tick` expression is updated, not accommodated
  (zero-backcompat); bare-`tick` ambient over `vfs.tick`/`temporal.tick` (matches
  in-profile bare-name reference style; `temporal.*` is scheduled to die).
