# Token-Obs Unit 1 — Harness Adjudicability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the differential harness able to express DIV-008's adjudication — "tokens
change what agents see, never what the world does" — before the token cut: scripted-action
traces, a stream-scoped registered-divergence shape, non-short-circuiting per-stream
adjudication, and a shape-preflight exemption for registered streams; then verify all-AGREE
on current code plus the RNG-call-order spot-check.

**Architecture:** Actions become a first-class trace stream (format v3 → v4, recorded
always): in seeded-random mode a cross-cut RNG drift is a *visible, attributable*
actions-stream divergence instead of silent trace decorrelation; in scripted mode the
harness replays the old side's recorded actions into the new side via the driver's new
`--actions` flag, making the dynamics comparison pure by construction. `compare_traces`
stops returning on the first mismatching stream: it collects per-stream findings across
the whole trace, then adjudicates them against an optional `RegisteredStreamDivergence`
(sibling of `RegisteredHashDivergence`, same narrowness discipline: declared streams must
diverge — stale declarations land `REGISTERED_DIVERGENCE_ABSENT` — and any undeclared
stream divergence stays red). The shape/dtype preflight still hard-fails undeclared
streams but records-and-continues for declared ones (a token-width `obs` cannot be
byte-compared against the old width, and must not mask the `rewards`/`dones` verdict).

**Tech Stack:** Python 3.12, numpy, torch, pytest, uv. No new dependencies.

**Spec:** `docs/superpowers/specs/2026-08-22-token-observation-representation-design.md`
(§5 "The oracle cut", §6 unit 1). Round-2 SA review finding C1 is the defect record.
Tracker: `hamlet-fa6bb6da4a`.

## Global Constraints

- **No-tech-debt policy (`PDR-0012`/`PDR-0013`) binds:** wire-or-delete, loud failures, no
  fallbacks, no version checks keeping v3 readable — old traces refuse loudly.
- **The driver is SELF-CONTAINED BY RULE** (`driver.py:1-27`, pinned by
  `test_driver_source_is_self_contained`): executed by file path in BOTH interpreters
  including the frozen oracle worktree. It may import stdlib, numpy, torch, and townlet
  modules present at the oracle tag ONLY — never `townlet.oracle.*`. All new driver code
  obeys this.
- **`TRACE_FORMAT_VERSION` lives in TWO files** (`driver.py:46`, `trace_io.py:17`), kept
  in sync BY HAND (the driver cannot import trace_io). Both move 3 → 4 in the same commit.
- New registered shapes are added because a register entry needs them, never
  speculatively (`RegisteredDivergence` docstring rule): **DIV-008 is the entry** — it is
  design-committed (spec §5) and registered at unit 3; this unit builds and tests the
  mechanism it binds.
- Suppression mechanisms must be narrow (`PDR-0033`): a declared stream that does NOT
  diverge is a stale entry and fails; an undeclared stream that diverges fails; both
  directions tested.
- Test invocation: `UV_CACHE_DIR=.uv-cache uv run pytest <path> -v`. Type gate:
  `UV_CACHE_DIR=.uv-cache uv run mypy src/townlet`.
- Work only in `src/townlet/`, `tests/test_townlet/`, `docs/`. **Never touch `.oracle/`
  or `oracle_fixtures/`.**
- Commit after every task, style `feat(oracle): … (hamlet-fa6bb6da4a)` /
  `test(oracle): …`.
- At execution start, note work under the already-claimed `hamlet-fa6bb6da4a` (in
  progress, assignee `claude-fable`); do not re-claim.

---

### Task 1: Trace format v4 — actions stream + action_source

Every trace records the actions actually stepped, and the comparison adjudicates them as
a stream. `Trace` gains two required fields (zero-backcompat: v3 traces refuse at load).

**Files:**
- Modify: `src/townlet/oracle/trace_io.py` (`TRACE_FORMAT_VERSION`, `Trace`,
  `save_trace`, `load_trace`, `_stream_steps`)
- Modify: `src/townlet/oracle/driver.py` (`TRACE_FORMAT_VERSION`, `run_trace` records
  actions + `action_source` meta)
- Modify: existing tests that construct `Trace(...)` directly (grep step below)
- Test: `tests/test_townlet/unit/oracle/test_trace_io.py` (extend)

**Interfaces:**
- Produces: `Trace.actions: np.ndarray` (shape `(steps, num_agents)`, dtype int64),
  `Trace.action_source: str` (`"seeded-random"` or `"scripted:<sha256-16>"` — reported,
  NEVER compared, same rule as `code_root`/`pack_root`); `_stream_steps` yields, per
  step t: `(t, "actions", …)`, `(t, "dones", …)`, `(t, "rewards", …)`,
  `(t+1, "obs", …)` — actions first, mirroring causal order (action → consequence).
- Consumed by: Tasks 2, 4, 5.

- [ ] **Step 1: Write the failing tests** (append to `test_trace_io.py`)

```python
def _v4_trace(tmp_path, steps=2, num_agents=2, obs_dim=3):
    """Round-trippable v4 trace with actions. Reused by later tasks' tests."""
    from townlet.oracle.trace_io import RunParams, Trace, save_trace, load_trace

    params = RunParams(pack="p", level="L", num_agents=num_agents, steps=steps, seed=1, device="cpu")
    trace = Trace(
        params=params,
        hashes={"config_hash": "abc"},
        obs=np.zeros((steps + 1, num_agents, obs_dim), dtype=np.float32),
        rewards=np.zeros((steps, num_agents), dtype=np.float32),
        dones=np.zeros((steps, num_agents), dtype=bool),
        actions=np.zeros((steps, num_agents), dtype=np.int64),
        code_root="/src",
        pack_root="/packs",
        action_source="seeded-random",
    )
    path = tmp_path / "t.npz"
    save_trace(path, trace)
    return trace, load_trace(path)


def test_v4_round_trips_actions_and_action_source(tmp_path):
    trace, loaded = _v4_trace(tmp_path)
    np.testing.assert_array_equal(loaded.actions, trace.actions)
    assert loaded.actions.dtype == np.int64
    assert loaded.action_source == "seeded-random"


def test_v3_trace_refuses_loudly(tmp_path):
    """Zero-backcompat: a pre-actions trace is regenerated, never accommodated."""
    from townlet.oracle.trace_io import load_trace

    meta = {"format_version": 3, "params": {}, "hashes": {}, "code_root": "x", "pack_root": "y"}
    path = tmp_path / "old.npz"
    np.savez_compressed(
        path,
        obs=np.zeros((1, 1, 1), dtype=np.float32),
        rewards=np.zeros((0, 1), dtype=np.float32),
        dones=np.zeros((0, 1), dtype=bool),
        meta=np.array(json.dumps(meta)),
    )
    with pytest.raises(ValueError, match="format_version 3"):
        load_trace(path)


def test_stream_steps_order_actions_dones_rewards_obs(tmp_path):
    from townlet.oracle.trace_io import _stream_steps

    trace, _ = _v4_trace(tmp_path, steps=1)
    names = [(step, stream) for step, stream, _ in _stream_steps(trace)]
    assert names == [(0, "obs"), (0, "actions"), (0, "dones"), (0, "rewards"), (1, "obs")]
```

(`test_trace_io.py` already imports numpy/pytest/json — verify at the top of the file and
add any missing imports.)

- [ ] **Step 2: Run to verify failure**

Run: `UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/oracle/test_trace_io.py -v -k "v4 or v3_trace or stream_steps_order"`
Expected: FAIL — `Trace.__init__() got an unexpected keyword argument 'actions'`.

- [ ] **Step 3: Implement trace_io side**

In `trace_io.py`: set `TRACE_FORMAT_VERSION = 4`. On `Trace`, after `dones`:

```python
    actions: np.ndarray  # (steps, num_agents) int64 — the actions actually stepped
```

and after `pack_root`:

```python
    # "seeded-random" (drawn from the run seed) or "scripted:<sha256-16>" (replayed
    # from a file). REPORTED, never compared — the compared truth is the actions
    # STREAM itself: equal bytes mean equal actions regardless of how each side
    # obtained them, which is exactly what the scripted replay flow relies on.
    action_source: str
```

`save_trace`: add `actions=trace.actions` to `np.savez_compressed` and
`"action_source": trace.action_source` to `meta`. `load_trace`: read both
(`actions=data["actions"]`, `action_source=meta["action_source"]`).

`_stream_steps`: insert `entries.append((t, "actions", trace.actions[t]))` as the FIRST
per-step entry (before dones), and update its docstring: actions precede their
consequences.

- [ ] **Step 4: Implement driver side**

In `driver.py`: set `TRACE_FORMAT_VERSION = 4`. In `run_trace`, collect actions:

```python
    action_frames: list[np.ndarray] = []
```

inside the loop, after `actions = torch.randint(...)`:

```python
        action_frames.append(actions.cpu().numpy().astype(np.int64).copy())
```

in `meta`, beside `"code_root"`:

```python
        "action_source": "seeded-random",
```

and in `np.savez_compressed`: `actions=np.stack(action_frames).astype(np.int64),`.
Update the module docstring's format note: "format_version 4 … keys: obs, rewards,
dones, actions, meta; meta carries params, hashes, code_root, pack_root, and
action_source".

- [ ] **Step 5: Fix every other `Trace(` constructor in tests**

Run: `grep -rn "Trace(" tests/test_townlet/unit/oracle/ | grep -v "load_trace\|save_trace"`
Add `actions=np.zeros((<steps>, <num_agents>), dtype=np.int64)` and
`action_source="seeded-random"` to each, matching that fixture's declared steps/agents.
Where a helper builds traces (test_compare.py has one), fix the helper once.

- [ ] **Step 6: Run the whole oracle unit suite**

Run: `UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/oracle/ -v`
Expected: PASS everywhere. (`test_driver_source_is_self_contained` must still pass —
nothing new imports `townlet.oracle`.)

- [ ] **Step 7: Commit**

```bash
git add src/townlet/oracle/trace_io.py src/townlet/oracle/driver.py tests/test_townlet/unit/oracle/
git commit -m "feat(oracle): trace format v4 — actions are a recorded, adjudicated stream (hamlet-fa6bb6da4a)"
```

---

### Task 2: Driver `--actions` — scripted replay mode

**Files:**
- Modify: `src/townlet/oracle/driver.py` (argparse + `run_trace`)
- Test: `tests/test_townlet/unit/oracle/test_driver.py` (extend)

**Interfaces:**
- Consumes: Task 1's v4 recording.
- Produces: driver CLI `--actions <path.npz>` (optional; file holds key `"actions"`,
  shape `(steps, num_agents)`, integer dtype). `run_trace(..., actions_path: Path | None)`
  keyword. In scripted mode `action_source = f"scripted:{sha256(actions.tobytes()).hexdigest()[:16]}"`.
  Validation is loud: wrong key, wrong shape, non-integer dtype, or any value outside
  `[0, env.action_dim)` raises `ValueError` naming the offense. `seed_all(seed)` still
  runs (env internals may consume RNG).

- [ ] **Step 1: Write the failing tests** (append to `test_driver.py`; follow that
  file's existing pattern for invoking `run_trace` on a small pack — reuse whatever pack
  constant/fixture its existing tests use; if it only tests via subprocess `main`, use
  `run_trace` directly here for speed, with `configs/test/model_config` / `L0_test`,
  `num_agents=2`, `steps=3`, `seed=7`, `device="cpu"`)

```python
def _run(tmp_path, out_name, actions_path=None, steps=3, seed=7):
    from townlet.oracle.driver import run_trace

    out = tmp_path / out_name
    run_trace(
        pack="configs/test/model_config",
        pack_root=str(Path.cwd()),
        level="L0_test",
        num_agents=2,
        steps=steps,
        seed=seed,
        device="cpu",
        out=out,
        actions_path=actions_path,
    )
    return np.load(out.with_suffix(".npz")) if not out.name.endswith(".npz") else np.load(out)


def test_scripted_actions_are_stepped_verbatim(tmp_path):
    first = _run(tmp_path, "a.npz")
    recorded = first["actions"]
    script = tmp_path / "script.npz"
    np.savez_compressed(script, actions=recorded)
    replay = _run(tmp_path, "b.npz", actions_path=script)
    np.testing.assert_array_equal(replay["actions"], recorded)
    meta = json.loads(str(replay["meta"]))
    assert meta["action_source"].startswith("scripted:")
    # Same seed + same actions ⇒ identical dynamics on one tree:
    np.testing.assert_array_equal(replay["obs"], first["obs"])
    np.testing.assert_array_equal(replay["rewards"], first["rewards"])


def test_scripted_actions_wrong_shape_refuses(tmp_path):
    script = tmp_path / "bad.npz"
    np.savez_compressed(script, actions=np.zeros((99, 2), dtype=np.int64))
    with pytest.raises(ValueError, match="actions"):
        _run(tmp_path, "c.npz", actions_path=script)


def test_scripted_actions_out_of_range_refuses(tmp_path):
    script = tmp_path / "oob.npz"
    np.savez_compressed(script, actions=np.full((3, 2), 10_000, dtype=np.int64))
    with pytest.raises(ValueError, match="action_dim"):
        _run(tmp_path, "d.npz", actions_path=script)
```

(np.load on the driver's `--out`: `np.savez_compressed(out, ...)` appends `.npz` only if
missing — pass names already ending in `.npz` to keep paths exact, as above.)

- [ ] **Step 2: Run to verify failure**

Run: `UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/oracle/test_driver.py -v -k scripted`
Expected: FAIL — `run_trace() got an unexpected keyword argument 'actions_path'`.

- [ ] **Step 3: Implement**

In `driver.py` — `run_trace` gains `actions_path: Path | None` (keyword, required in the
signature with no default is wrong here: `None` IS the declared seeded-random mode, not a
fallback — document that in the docstring). Add stdlib import `hashlib`. After
`env = VectorizedHamletEnv(...)`:

```python
    scripted: np.ndarray | None = None
    if actions_path is not None:
        with np.load(actions_path, allow_pickle=False) as data:
            if "actions" not in data:
                raise ValueError(f"actions file {actions_path} has no 'actions' array")
            scripted = np.asarray(data["actions"])
        if scripted.shape != (steps, num_agents):
            raise ValueError(f"actions shape {scripted.shape} != declared (steps={steps}, num_agents={num_agents})")
        if not np.issubdtype(scripted.dtype, np.integer):
            raise ValueError(f"actions dtype {scripted.dtype} is not integer")
        if scripted.min() < 0 or scripted.max() >= env.action_dim:
            raise ValueError(
                f"actions contain values outside [0, action_dim={env.action_dim}): "
                f"min={int(scripted.min())}, max={int(scripted.max())}"
            )
```

In the step loop, replace the action draw with mode dispatch (the random branch is
byte-identical to today's — same call, same device order, so seeded-random traces are
unchanged by this task):

```python
    for t in range(steps):
        if scripted is None:
            actions = torch.randint(0, env.action_dim, (env.num_agents,)).to(env.device)
        else:
            actions = torch.from_numpy(scripted[t].astype(np.int64)).to(env.device)
```

`action_source` in meta:

```python
        "action_source": ("seeded-random" if scripted is None else "scripted:" + hashlib.sha256(scripted.astype(np.int64).tobytes()).hexdigest()[:16]),
```

argparse: `parser.add_argument("--actions", type=Path, default=None, help="npz with an 'actions' array to replay verbatim (scripted mode)")`
and pass `actions_path=args.actions` in `main`'s `run_trace` call.

- [ ] **Step 4: Run tests**

Run: `UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/oracle/test_driver.py -v`
Expected: PASS (including `test_driver_source_is_self_contained` — hashlib/np/torch only).

- [ ] **Step 5: Commit**

```bash
git add src/townlet/oracle/driver.py tests/test_townlet/unit/oracle/test_driver.py
git commit -m "feat(oracle): driver --actions replays a scripted action file verbatim, loudly validated (hamlet-fa6bb6da4a)"
```

---

### Task 3: `RegisteredStreamDivergence` + Cell fields

**Files:**
- Modify: `src/townlet/oracle/matrix.py`
- Test: `tests/test_townlet/unit/oracle/test_matrix.py` (extend)

**Interfaces:**
- Produces:

```python
@dataclass(frozen=True)
class RegisteredStreamDivergence:
    register_ref: str            # e.g. "DIV-008"
    streams: tuple[str, ...]     # exact set of trace streams permitted (and required) to diverge

    @property
    def declared(self) -> frozenset[str]: ...
```

  valid stream names: `{"obs", "actions", "dones", "rewards"}`. `Cell` gains
  `stream_divergence: RegisteredStreamDivergence | None = None` and
  `scripted_actions: bool = False` (both declared, defaulting to the overwhelming
  no-declaration case, same pattern as `expected`/`hash_divergence`).
- Consumed by: Task 4 (`compare_traces`), Task 5 (`run_cell`).

- [ ] **Step 1: Write the failing tests** (append to `test_matrix.py`)

```python
def test_stream_divergence_validates_ref_and_streams():
    from townlet.oracle.matrix import RegisteredStreamDivergence

    d = RegisteredStreamDivergence(register_ref="DIV-008", streams=("obs",))
    assert d.declared == frozenset({"obs"})

    with pytest.raises(ValueError, match="register_ref"):
        RegisteredStreamDivergence(register_ref="div8", streams=("obs",))
    with pytest.raises(ValueError, match="at least one"):
        RegisteredStreamDivergence(register_ref="DIV-008", streams=())
    with pytest.raises(ValueError, match="duplicates"):
        RegisteredStreamDivergence(register_ref="DIV-008", streams=("obs", "obs"))
    with pytest.raises(ValueError, match="not a trace stream"):
        RegisteredStreamDivergence(register_ref="DIV-008", streams=("observations",))


def test_cell_defaults_declare_nothing_new():
    from townlet.oracle.matrix import default_cells

    for cell in default_cells():
        assert cell.stream_divergence is None
        assert cell.scripted_actions is False
```

- [ ] **Step 2: Run to verify failure**

Run: `UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/oracle/test_matrix.py -v -k "stream_divergence or defaults_declare"`
Expected: FAIL — `ImportError: cannot import name 'RegisteredStreamDivergence'`.

- [ ] **Step 3: Implement**

In `matrix.py`, after `RegisteredHashDivergence` (reusing `_REGISTER_REF_RE`):

```python
_TRACE_STREAMS = ("obs", "actions", "dones", "rewards")


@dataclass(frozen=True)
class RegisteredStreamDivergence:
    """One cell's declared binding for the THIRD divergence shape: a named trace
    stream diverges as intended, everything else does not.

    Built for DIV-008 (the token-observation cut, spec
    docs/superpowers/specs/2026-08-22-token-observation-representation-design.md §5):
    the observation representation changes, so the `obs` stream diverges on every
    cell, while world dynamics under scripted actions — `actions`, `dones`,
    `rewards` — must stay byte-exact. Added because that register entry needs it,
    the bar the sibling classes set.

    Narrowness (PDR-0033, both directions, enforced in compare_traces):
    - `streams` is an ENUMERATED set from the closed trace-stream vocabulary,
      never a wildcard. An undeclared stream diverging keeps the cell red.
    - Every declared stream must ACTUALLY diverge somewhere in the trace; one
      that does not is a stale entry and lands REGISTERED_DIVERGENCE_ABSENT.
    - Hash movement is a separate declaration (`RegisteredHashDivergence`) —
      a declared OUTPUT-stream delta does not bless provenance movement, and
      vice versa. DIV-008 binds both, under one register_ref.
    """

    register_ref: str
    streams: tuple[str, ...]

    def __post_init__(self) -> None:
        if not _REGISTER_REF_RE.fullmatch(self.register_ref):
            raise ValueError(f"register_ref must look like 'DIV-008', got {self.register_ref!r}")
        if not self.streams:
            raise ValueError("streams must enumerate at least one trace stream — an empty set is a wildcard by another name")
        if len(set(self.streams)) != len(self.streams):
            raise ValueError(f"streams contains duplicates: {self.streams!r}")
        for name in self.streams:
            if name not in _TRACE_STREAMS:
                raise ValueError(f"streams entry {name!r} is not a trace stream (one of {_TRACE_STREAMS})")

    @property
    def declared(self) -> frozenset[str]:
        return frozenset(self.streams)
```

On `Cell`, after `hash_divergence`:

```python
    # Names the entry under which named trace STREAMS are allowed — and
    # required — to diverge, everything else byte-exact. The third declaration
    # axis, orthogonal to pack_divergence (inputs) and hash_divergence
    # (provenance): DIV-008 binds stream + hash together at the token cut.
    stream_divergence: RegisteredStreamDivergence | None = None
    # Run this cell's trace with harness-scripted actions (old side records,
    # new side replays) instead of per-side seeded draws. DIV-008 cells declare
    # it; --scripted forces it matrix-wide for verification runs.
    scripted_actions: bool = False
```

- [ ] **Step 4: Run tests**

Run: `UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/oracle/test_matrix.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/townlet/oracle/matrix.py tests/test_townlet/unit/oracle/test_matrix.py
git commit -m "feat(oracle): RegisteredStreamDivergence — the third declared shape, built for DIV-008 (hamlet-fa6bb6da4a)"
```

---

### Task 4: `compare_traces` — non-short-circuiting per-stream adjudication

The core of the unit. Replaces the first-mismatch `return` with full-trace collection,
adds the `stream_divergence` parameter, and exempts declared streams from the hard
shape-preflight (recording the shape mismatch as their expected divergence instead).

**Files:**
- Modify: `src/townlet/oracle/trace_io.py` (`compare_traces`)
- Test: `tests/test_townlet/unit/oracle/test_compare.py` (extend; reuse/extend its
  existing trace-builder helper, now v4 per Task 1)

**Interfaces:**
- Produces: `compare_traces(old, new, cell_id, *, hash_divergence: Any = None,
  stream_divergence: Any = None) -> CellVerdict` (both typed loosely — no matrix
  import, existing convention). Verdict semantics:
  - no declarations, all streams byte-exact, hashes equal → `AGREE` (unchanged);
  - any UNDECLARED stream divergence → `DIVERGE`, with `detail["streams"]` mapping EVERY
    diverging stream name → its first finding + `diff_entries` count (the
    non-short-circuit payoff: a diverging `obs` no longer hides `rewards`);
  - declared streams that ALL diverge + all undeclared streams clean + hash side
    satisfied → `DIVERGED_AS_REGISTERED`, `register_refs` = deduped
    `(hash_divergence.register_ref?, stream_divergence.register_ref?)`;
  - any declared stream that did NOT diverge → `REGISTERED_DIVERGENCE_ABSENT`
    (`detail["declared_but_unmoved_streams"]`);
  - hash logic unchanged in meaning (declared-set exact match; undeclared mover →
    `HASH_MISMATCH`), still adjudicated before streams — a hash contract breach is
    terminal because it means the DECLARATION is wrong, not the behaviour.
- Consumed by: Task 5 (`run_cell` threads `cell.stream_divergence`).

- [ ] **Step 1: Write the failing tests** (append to `test_compare.py`; `_trace(...)`
  below stands for that file's existing builder helper extended per Task 1 — it must
  accept overrides for `obs`, `rewards`, `dones`, `actions`, and `hashes`)

```python
from townlet.oracle.matrix import RegisteredHashDivergence, RegisteredStreamDivergence

DIV8_STREAMS = RegisteredStreamDivergence(register_ref="DIV-008", streams=("obs",))


def test_undeclared_divergence_reports_every_stream_not_just_the_first():
    """SA-C1: today the first mismatching stream (frame-zero obs) masks the rest."""
    old = _trace()
    new = _trace(obs=old.obs + 1.0, rewards=old.rewards + 1.0)
    v = compare_traces(old, new, "cell")
    assert v.kind == "DIVERGE"
    assert set(v.detail["streams"]) == {"obs", "rewards"}


def test_registered_obs_divergence_with_clean_dynamics_passes():
    old = _trace()
    new = _trace(obs=old.obs + 1.0)
    v = compare_traces(old, new, "cell", stream_divergence=DIV8_STREAMS)
    assert v.kind == "DIVERGED_AS_REGISTERED"
    assert v.register_refs == ("DIV-008",)


def test_registered_obs_shape_change_is_exempt_from_preflight():
    """(d): the token cut changes total_dims — a declared stream may differ in SHAPE."""
    old = _trace(obs_dim=4)
    new = _trace(obs_dim=9)
    v = compare_traces(old, new, "cell", stream_divergence=DIV8_STREAMS)
    assert v.kind == "DIVERGED_AS_REGISTERED"
    assert v.detail["streams"]["obs"]["shape_changed"] is True


def test_registered_obs_but_rewards_also_diverge_fails():
    old = _trace()
    new = _trace(obs=old.obs + 1.0, rewards=old.rewards + 0.5)
    v = compare_traces(old, new, "cell", stream_divergence=DIV8_STREAMS)
    assert v.kind == "DIVERGE"
    assert "rewards" in v.detail["streams"]
    assert v.register_refs == ()


def test_undeclared_shape_change_still_hard_fails():
    old = _trace(obs_dim=4)
    new = _trace(obs_dim=9)
    v = compare_traces(old, new, "cell")
    assert v.kind == "DIVERGE"
    assert v.detail["streams"]["obs"]["shape_changed"] is True


def test_declared_stream_that_never_diverges_is_a_stale_entry():
    old = _trace()
    new = _trace()  # byte-identical
    v = compare_traces(old, new, "cell", stream_divergence=DIV8_STREAMS)
    assert v.kind == "REGISTERED_DIVERGENCE_ABSENT"
    assert v.detail["declared_but_unmoved_streams"] == ["obs"]


def test_hash_and_stream_declarations_compose_under_one_ref():
    """The DIV-008 shape: hashes move as declared AND obs diverges as declared."""
    hd = RegisteredHashDivergence(register_ref="DIV-008", hash_fields=("observation_schema_hash",))
    old = _trace(hashes={"observation_schema_hash": "a", "config_hash": "z"})
    new = _trace(hashes={"observation_schema_hash": "b", "config_hash": "z"}, obs_shift=1.0)
    v = compare_traces(old, new, "cell", hash_divergence=hd, stream_divergence=DIV8_STREAMS)
    assert v.kind == "DIVERGED_AS_REGISTERED"
    assert v.register_refs == ("DIV-008",)  # deduped, one entry binding both shapes


def test_actions_stream_divergence_is_adjudicated():
    """RNG-stream coupling becomes visible: differing draws are an actions DIVERGE."""
    old = _trace()
    new = _trace(actions=old.actions + 1)
    v = compare_traces(old, new, "cell")
    assert v.kind == "DIVERGE"
    assert "actions" in v.detail["streams"]
```

(`obs_shift=1.0` in the composition test: extend `_trace` with an `obs_shift` float
override adding a constant to obs, or construct via `obs=` explicitly — match the
helper's style. Where obs dims differ, the helper builds each trace independently.)

- [ ] **Step 2: Run to verify failure**

Run: `UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/oracle/test_compare.py -v -k "undeclared or registered_obs or stale_entry or compose or actions_stream"`
Expected: FAIL — `compare_traces() got an unexpected keyword argument 'stream_divergence'`
(and, once added naively, the every-stream test fails against the old short-circuit).

- [ ] **Step 3: Implement**

In `trace_io.py`, replace the stream loop of `compare_traces` (keep params check and the
hash block verbatim — only its final `if declared:` success shape moves down). New
signature and body from the hash block's end:

```python
def compare_traces(
    old: Trace, new: Trace, cell_id: str, *, hash_divergence: Any = None, stream_divergence: Any = None
) -> CellVerdict:
    """Adjudicate one cell from both sides' traces.

    `hash_divergence` (matrix.RegisteredHashDivergence) permits — and requires —
    exactly the named provenance hashes to differ. `stream_divergence`
    (matrix.RegisteredStreamDivergence) permits — and requires — exactly the named
    trace STREAMS to diverge, shape changes included, while every other stream
    stays byte-exact. Both are typed loosely to keep this module free of a matrix
    import. Adjudication no longer stops at the first mismatching stream: every
    stream is compared in full, so a registered obs divergence can never mask the
    rewards/dones verdict (SA-C1, token-obs design §5/§6 unit 1).
    """
```

after the (unchanged) params + hash-mismatch logic — with the old `if declared:` /
`return AGREE` tail DELETED — append:

```python
    declared_streams: frozenset[str] = stream_divergence.declared if stream_divergence is not None else frozenset()

    # Collect findings for EVERY stream; never return mid-scan (SA-C1).
    findings: dict[str, dict[str, object]] = {}

    def _record(stream: str, entry: dict[str, object]) -> None:
        if stream not in findings:
            entry["diff_entries"] = 1
            findings[stream] = entry
        else:
            findings[stream]["diff_entries"] = int(findings[stream]["diff_entries"]) + 1  # type: ignore[call-overload]

    for (old_step, stream, old_arr), (_, _, new_arr) in zip(_stream_steps(old), _stream_steps(new), strict=True):
        if old_arr.shape != new_arr.shape or old_arr.dtype != new_arr.dtype:
            # Shape/dtype preflight (FIX 1) — still BEFORE byte comparison, but it
            # RECORDS rather than returns: for a declared stream this IS the
            # expected divergence (the token cut changes obs width, and bytes of
            # different shapes cannot be compared); for an undeclared stream it is
            # adjudicated red below with everything else.
            _record(
                stream,
                {
                    "step": old_step,
                    "shape_changed": True,
                    "old_shape": list(old_arr.shape),
                    "new_shape": list(new_arr.shape),
                    "old_dtype": str(old_arr.dtype),
                    "new_dtype": str(new_arr.dtype),
                },
            )
            continue
        if old_arr.tobytes() == new_arr.tobytes():
            continue
        if stream in declared_streams:
            # Expected to diverge — record cheaply, skip localization.
            _record(stream, {"step": old_step, "shape_changed": False})
            continue
        mask = _divergence_mask(old_arr, new_arr)
        if not mask.any():
            mask = np.ones_like(mask)
        diff_indices = np.argwhere(mask)
        entry: dict[str, object] = {
            "step": old_step,
            "shape_changed": False,
            "indices": [list(map(int, idx)) for idx in diff_indices[:_MAX_REPORTED_INDICES]],
            "diff_count": int(len(diff_indices)),
        }
        if old_arr.dtype != np.bool_:
            diffs = np.abs(old_arr[mask].astype(np.float64) - new_arr[mask].astype(np.float64))
            max_abs_diff = float(np.max(diffs)) if diffs.size else 0.0
            entry["max_abs_diff"] = max_abs_diff if np.isfinite(max_abs_diff) else "non-finite"
        _record(stream, entry)

    diverged = frozenset(findings)
    undeclared_streams = diverged - declared_streams
    unmoved_streams = declared_streams - diverged

    if undeclared_streams:
        return CellVerdict(
            kind="DIVERGE",
            cell_id=cell_id,
            detail={
                "streams": {name: findings[name] for name in sorted(diverged)},
                "undeclared_streams": sorted(undeclared_streams),
                **({"declared_streams": sorted(declared_streams)} if declared_streams else {}),
            },
        )
    if unmoved_streams:
        # A declared stream that never diverged is a stale entry — the exact
        # condition REGISTERED_DIVERGENCE_ABSENT names for the other two shapes.
        return CellVerdict(
            kind="REGISTERED_DIVERGENCE_ABSENT",
            cell_id=cell_id,
            detail={
                "register_ref": stream_divergence.register_ref,
                "declared_but_unmoved_streams": sorted(unmoved_streams),
                "streams": {name: findings[name] for name in sorted(diverged)},
            },
        )

    refs: tuple[str, ...] = ()
    if declared:  # the hash declaration manifested exactly (checked above)
        refs = refs + (hash_divergence.register_ref,)
    if declared_streams:
        if stream_divergence.register_ref not in refs:
            refs = refs + (stream_divergence.register_ref,)
    if refs:
        return CellVerdict(
            kind="DIVERGED_AS_REGISTERED",
            cell_id=cell_id,
            detail={
                "shape": ("hash+stream" if declared and declared_streams else "hash-only" if declared else "stream-only"),
                **({"mismatched": mismatched} if declared else {}),
                **({"streams": {name: findings[name] for name in sorted(diverged)}} if declared_streams else {}),
            },
            register_refs=refs,
        )
    return CellVerdict(kind="AGREE", cell_id=cell_id, detail={})
```

Note: the pre-existing hash-only success branch (old lines 251-259) is REPLACED by the
unified `refs` tail above — delete it; there must be exactly one success-shape exit.

- [ ] **Step 4: Run the compare suite, then the whole oracle suite**

Run: `UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/oracle/test_compare.py tests/test_townlet/unit/oracle/ -v`
Expected: PASS — including every pre-existing compare test (AGREE, hash shapes, NaN/-0.0
localization, shape preflight for undeclared streams). If a pre-existing test asserted
the OLD single-stream `detail` shape (`detail["stream"]`), update it to the new
`detail["streams"]` mapping — the detail schema change is deliberate and this unit's
point; do not preserve the old key alongside the new one.

- [ ] **Step 5: Commit**

```bash
git add src/townlet/oracle/trace_io.py tests/test_townlet/unit/oracle/test_compare.py
git commit -m "feat(oracle): per-stream adjudication — registered stream divergences, no masking, preflight exemption (hamlet-fa6bb6da4a)"
```

---

### Task 5: Harness wiring — scripted replay flow + stream declarations

**Files:**
- Modify: `src/townlet/oracle/harness.py` (`run_cell`, `_validate_lone_trace`, `main`)
- Test: `tests/test_townlet/unit/oracle/test_harness.py` (extend)

**Interfaces:**
- Consumes: Tasks 1–4.
- Produces: `run_cell(..., scripted: bool)` keyword (threaded from
  `cell.scripted_actions or args.scripted`); harness CLI `--scripted`; scripted flow =
  old side runs seeded-random and records → harness writes
  `run_dir / f"{safe}.actions.npz"` from `old_trace.actions` → new side runs with
  `--actions` that file. `compare_traces` call gains
  `stream_divergence=cell.stream_divergence`. `_validate_lone_trace` also checks
  `actions` shape `(p.steps, p.num_agents)`.

- [ ] **Step 1: Write the failing tests** (append to `test_harness.py`, following its
  existing self-comparison pattern — it already runs `run_cell` with
  `old_src == new_src` on a small pack; mirror that fixture's arguments)

```python
def test_scripted_self_comparison_agrees_and_replays_actions(tmp_path):
    """Self-comparison in scripted mode: new side replays old's recorded actions;
    the actions stream matches by construction and the verdict is AGREE."""
    cell = _small_cell()  # the file's existing small-pack cell helper
    verdict = run_cell(
        repo_root=REPO_ROOT,
        old_src=REPO_ROOT / "src",
        old_pack_root=REPO_ROOT,
        new_src=REPO_ROOT / "src",
        cell=cell,
        run_dir=tmp_path,
        run_cuda=False,
        scripted=True,
    )
    assert verdict.kind == "AGREE", verdict.detail
    safe = cell.cell_id.replace(":", "_")
    actions_file = tmp_path / f"{safe}.actions.npz"
    assert actions_file.exists()
    with np.load(tmp_path / f"{safe}.new.npz") as new_side:
        meta = json.loads(str(new_side["meta"]))
    assert meta["action_source"].startswith("scripted:")


def test_scripted_mode_refuses_expected_crash_cells(tmp_path):
    """Scripted replay needs an old-side trace; a cell declaring an old-side crash
    has none — loud HARNESS_ERROR, never a silent fallback to random."""
    from townlet.oracle.matrix import RegisteredDivergence

    cell = dataclasses.replace(
        _small_cell(),
        expected=RegisteredDivergence(register_ref="DIV-003", old_stderr_substring="registered crash signature"),
    )
    verdict = run_cell(
        repo_root=REPO_ROOT,
        old_src=REPO_ROOT / "src",
        old_pack_root=REPO_ROOT,
        new_src=REPO_ROOT / "src",
        cell=cell,
        run_dir=tmp_path,
        run_cuda=False,
        scripted=True,
    )
    assert verdict.kind == "HARNESS_ERROR"
    assert "scripted" in str(verdict.detail)
```

(add `import dataclasses` / `import json` / `import numpy as np` to the test file's
imports if absent; `REPO_ROOT` / `_small_cell` per the file's existing conventions —
if it names them differently, use its names.)

- [ ] **Step 2: Run to verify failure**

Run: `UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/oracle/test_harness.py -v -k scripted`
Expected: FAIL — `run_cell() got an unexpected keyword argument 'scripted'`.

- [ ] **Step 3: Implement**

`run_side` gains pass-through `actions: Path | None = None`; when set, extend `cmd` with
`["--actions", str(actions)]`.

`run_cell` signature gains `scripted: bool`. At the top, after the CUDA gate:

```python
    if scripted and cell.expected is not None:
        return CellVerdict(
            kind="HARNESS_ERROR",
            cell_id=cell.cell_id,
            detail={
                "reason": (
                    "scripted mode requires an old-side trace to replay, but this cell "
                    "declares an old-side crash (expected=" + cell.expected.register_ref + ") — "
                    "the two declarations are incompatible; run this cell unscripted"
                ),
            },
        )
```

In the normal (old side succeeded) path, between `old_failure` handling and the
new-side run, restructure to load the old trace first and replay when scripted:

```python
    actions_file: Path | None = None
    if scripted:
        old_trace = load_trace(old_out)
        actions_file = run_dir / f"{safe}.actions.npz"
        np.savez_compressed(actions_file, actions=old_trace.actions)
    new_failure = run_side(
        driver=driver, src=new_src, params=cell.params, out=new_out, repo_root=repo_root, pack_root=new_pack_root, actions=actions_file
    )
    if new_failure is not None:
        ...  # unchanged NEW_SIDE_ERROR branch
    if not scripted:
        old_trace = load_trace(old_out)
    new_trace = load_trace(new_out)
```

(`import numpy as np` at the top of harness.py.) The `compare_traces` call becomes:

```python
    verdict = compare_traces(
        old_trace, new_trace, cell_id=cell.cell_id, hash_divergence=cell.hash_divergence, stream_divergence=cell.stream_divergence
    )
```

`run_cell_safely` gains and forwards `scripted: bool`. `_validate_lone_trace` adds
`"actions": (p.steps, p.num_agents)` to `expected_shapes` and
`"actions": trace.actions.shape` to `actual_shapes`.

`main`: `parser.add_argument("--scripted", action="store_true", help="replay the old side's recorded actions into the new side on every cell (DIV-008 verification mode)")`
and in the loop pass `scripted=cell.scripted_actions or args.scripted`.

Update the module docstring's shape list: three declared shapes (crash / hash-only /
stream-scoped), and `_ADJUDICATION_NOTE` gains one sentence: "Shape 3 (stream-scoped):
both sides ran, EXACTLY the enumerated trace streams diverge — shape changes included —
and every other stream matches byte-for-byte."

- [ ] **Step 4: Run the full oracle suite**

Run: `UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/oracle/ -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/townlet/oracle/harness.py tests/test_townlet/unit/oracle/test_harness.py
git commit -m "feat(oracle): scripted replay flow + stream declarations wired through run_cell (hamlet-fa6bb6da4a)"
```

---

### Task 6: Verification — all-AGREE on current code, RNG spot-check, gates

The unit's acceptance: the rebuilt harness certifies the CURRENT tree cleanly in both
modes, and the seeded-random draw is proven call-order stable.

**Files:**
- Test: `tests/test_townlet/integration/test_oracle_rng_stability.py` (new)
- No src changes (any failure here is a finding, handled per its own step)

- [ ] **Step 1: RNG-call-order spot-check test**

```python
# tests/test_townlet/integration/test_oracle_rng_stability.py
"""Seeded-random action draws are call-order stable on the current tree.

The scripted-action mode exists because RNG-stream coupling across the token cut
would decorrelate traces for a non-defect reason (spec §5). This pins the
BASELINE: two same-seed runs of the driver on ONE tree draw identical actions and
produce identical streams — so any future actions-stream divergence is real
evidence of RNG-consumption change, not noise. (Round-2 systems review asked for
exactly this check before trusting unit 1's all-AGREE as a clean baseline.)
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from townlet.oracle.driver import run_trace

PACK = "configs/test/model_config"
LEVEL = "L0_test"


def _trace(tmp_path: Path, name: str) -> dict[str, np.ndarray]:
    out = tmp_path / name
    run_trace(
        pack=PACK, pack_root=str(Path.cwd()), level=LEVEL, num_agents=2, steps=25,
        seed=1234, device="cpu", out=out, actions_path=None,
    )
    with np.load(out if out.suffix == ".npz" else out.with_suffix(".npz")) as data:
        return {k: np.asarray(data[k]) for k in ("obs", "rewards", "dones", "actions")} | {
            "action_source": json.loads(str(data["meta"]))["action_source"]
        }


def test_same_seed_same_tree_draws_identical_actions_and_streams(tmp_path):
    a = _trace(tmp_path, "a.npz")
    b = _trace(tmp_path, "b.npz")
    assert a["action_source"] == b["action_source"] == "seeded-random"
    for key in ("actions", "obs", "rewards", "dones"):
        np.testing.assert_array_equal(a[key], b[key]), key
```

- [ ] **Step 2: Run it**

Run: `UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/integration/test_oracle_rng_stability.py -v`
Expected: PASS. A FAILURE here is a **finding about the current tree** (nondeterministic
draws today) — stop, record it on `hamlet-fa6bb6da4a`, and escalate before the cut; do
not paper over it.

- [ ] **Step 3: Full CPU matrix, plain mode**

Run: `UV_CACHE_DIR=.uv-cache uv run python -m townlet.oracle.harness`
Expected: exit 0 — ten CPU cells `AGREE` except the four profile-variable cells... note
the profile cells are cpu+cuda pairs: on a CPU run expect the two CPU profile cells
`DIVERGED_AS_REGISTERED` (DIV-006, hash-only — now `"shape": "hash-only"` in detail),
the eight other CPU cells `AGREE`, all ten CUDA cells `SKIPPED`. Any other kind on any
cell: stop and diagnose (the v4 driver runs on BOTH sides — it is injected from the new
tree — so a failure is a real regression, likely in the driver or compare changes).

- [ ] **Step 4: Full CPU matrix, scripted mode**

Run: `UV_CACHE_DIR=.uv-cache uv run python -m townlet.oracle.harness --scripted`
Expected: exit 0, same verdict pattern. This is the unit's headline evidence: the
scripted flow works end-to-end against the frozen oracle side (whose interpreter runs
the same injected v4 driver), and the current tree's dynamics are byte-stable under
replayed actions.

- [ ] **Step 5: Type gate + full oracle suite one last time**

Run: `UV_CACHE_DIR=.uv-cache uv run mypy src/townlet && UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/oracle/ tests/test_townlet/integration/test_oracle_rng_stability.py -v`
Expected: mypy clean, all PASS.

- [ ] **Step 6: Record the verification runs on the ticket, commit**

```bash
filigree add-comment hamlet-fa6bb6da4a --actor claude-fable "Unit 1 (harness adjudicability) landed: trace v4 with actions stream + action_source; driver --actions scripted replay; RegisteredStreamDivergence (third shape, for DIV-008); compare_traces per-stream non-short-circuiting with preflight exemption for declared streams; harness --scripted replay flow. Verification: full CPU matrix exit 0 in plain AND scripted modes (run ids: <fill from runs/differential/>), RNG-call-order spot-check green. DIV-008 itself is registered at unit 3, per the record-then-bind rule."
git add tests/test_townlet/integration/test_oracle_rng_stability.py
git commit -m "test(oracle): RNG-call-order stability pinned — the scripted mode's baseline is clean (hamlet-fa6bb6da4a)"
git push origin project-recovery-2
```

---

## Self-review notes (done at plan time)

- **Spec coverage:** (a) → Tasks 1+2+5; (b) → Task 3; (c) → Task 4; (d) → Task 4
  (record-and-continue preflight); "verified all-AGREE on current code" → Task 6 steps
  3–4; "RNG-call-order spot-check" → Task 6 steps 1–2. Driver self-containment → Global
  Constraints + Task 2 (hashlib/np/torch only). The spec's "four harness changes" map:
  scripted mode (Tasks 1/2/5), stream shape (3), non-short-circuit (4), preflight
  exemption (4).
- **Deliberately NOT in this unit:** the DIV-008 register entry (unit 3, record-then-bind),
  any change under `oracle_fixtures/`, and any matrix cell declaring the new shape (no
  entry exists yet to bind — `test_cell_defaults_declare_nothing_new` pins that).
- **Type consistency check:** `RegisteredStreamDivergence.declared` (frozenset) mirrors
  `RegisteredHashDivergence.declared`; `compare_traces` keyword names match Task 5's call
  site; `scripted` kwarg name identical across `run_cell`/`run_cell_safely`; stream names
  in `_TRACE_STREAMS` match `_stream_steps` literals ("obs","actions","dones","rewards").
- **Known judgement calls carried in the plan:** action_source is meta (reported, never
  compared) because the actions STREAM is the compared truth; scripted × expected-crash
  is a loud incompatibility; the old detail schema (`detail["stream"]`) is replaced, not
  dual-carried (no-tech-debt).
