# Differential Harness — Design (WS-7 content 3)

**Date:** 2026-08-13 · **Stream:** WS-7 (`hamlet-e3af412673`) · **Owner-approved:** yes
**Provenance:** `PDR-0006` (strangler), `PDR-0030` (oracle pinned: `oracle-2026-08-13` →
`0e875d7a`), `PDR-0031` (seed is config), `docs/oracle/ORACLE.md`,
`docs/oracle/known-divergences.md`. Reshapes WS-3 (`hamlet-1f89714685`).

## Purpose

Run the frozen oracle and the working tree against the same declared universe and the same
seed, and assert their env-step traces agree everywhere the known-divergences register does
not say otherwise. This is the program's central artifact: every knockdown is judged by it.

**v1 scope (owner call):** trace-only. The register's current entries (DIV-001/002) are
checkpoint-boundary behaviours that cannot manifest in an env trace, and the first knockdown
candidate (terrain/substrate) has exactly the env-step trace as its blast radius.
Checkpoint-boundary probe scenarios are added when a knockdown first touches that surface.

## Decisions made (owner-approved 2026-08-13)

1. **Scope:** trace-only v1. Any trace divergence is a rebuild defect — no current register
   entry can exempt one.
2. **Home:** `src/townlet/oracle/` — a real package under all four gates
   (ruff/black/mypy/pytest), with its own unit tests. The central artifact is held to the
   same bar as the product.
3. **Execution model:** injected driver, both sides live. One self-contained driver script,
   run in two subprocesses per cell — `PYTHONPATH` at the oracle worktree's `src` and at the
   working tree's `src`. Nothing is ever committed to the frozen tag. (Golden recorded
   traces rejected: the recording would become the spec instead of the tagged tree. Dual
   import in one interpreter rejected: module caching and torch C-extensions make it
   unreliable.)

## Architecture

`src/townlet/oracle/` — four modules plus `__init__.py`:

### `__init__.py`
- `ORACLE_TAG = "oracle-2026-08-13"` — the single machine-readable authority for the
  current oracle ref. When the oracle moves forward (`PDR-0030` reversal path), this one
  constant moves with the new tag; `ORACLE.md` records the history.

### `driver.py` — the injected trace producer
- **Self-contained by rule:** imports only stdlib, numpy, torch, and townlet modules that
  exist at the tag (`townlet.determinism`, `townlet.universe.compiler`,
  `townlet.environment.vectorized_env`). It must never import from `townlet.oracle` itself —
  it runs unmodified in *either* side's interpreter, including the frozen one.
- **CLI:** `python -m townlet.oracle.driver --pack <dir> --level <name> --num-agents N
  --steps N --seed N --device cpu|cuda --out <file.npz>`.
  (Invoked with explicit `PYTHONPATH`; on the old side `townlet.oracle` does not exist, so
  the harness invokes it by **file path** (`python <path-to-driver.py> …`), not by module.)
- **Behaviour** (mirrors `tests/test_townlet/integration/test_determinism.py::_trace_hash`,
  the verified-deterministic recipe):
  1. `UniverseCompiler().compile(pack, primary_level=level, use_cache=False)`
  2. `seed_all(seed)`
  3. `VectorizedHamletEnv(universe=…, level_name=…, num_agents=…, device=…)`, `reset()`
  4. N steps; actions drawn on CPU (`torch.randint(0, action_dim, (num_agents,))`) then
     moved to the env device — the action stream is device-independent
  5. Write the trace file (format below), then exit 0. Any exception: traceback to stderr,
     exit non-zero.

### `trace.py` — format and comparison
- **Format:** one `.npz` per run:
  - arrays: `obs` (steps+1 × agents × obs_dim — includes the reset observation),
    `rewards` (steps × agents), `dones` (steps × agents)
  - metadata (stored as an npz string field, JSON-encoded): `side`, `commit`
    (`git rev-parse HEAD` of the side's tree), `pack`, `level`, `num_agents`, `steps`,
    `seed`, `device`, and the compiled universe's provenance hashes as exposed on
    `CompiledUniverse`.
- **Comparison:** `compare_traces(old, new) -> CellVerdict`.
  - Stage 1 — provenance: if the two sides' compiled hashes differ → `HASH_MISMATCH`
    (names which hashes differ). Trace arrays are not consulted.
  - Stage 2 — exact bytes per array, in step order. On mismatch: first divergent step,
    which stream (`obs`/`rewards`/`dones`), divergent agent/dim indices at that step, and
    a max-abs-diff summary → `DIVERGE`.
  - Metadata that must match by construction (pack, level, seed, steps, device) mismatching
    is a harness bug → hard error, not a verdict.

### `harness.py` — orchestrator and CLI
- **CLI:** `python -m townlet.oracle.harness [--cell PACK:LEVEL …] [--cuda]
  [--oracle-ref TAG]` (default `ORACLE_TAG`).
- **Worktree:** ensures `.oracle/<tag>/` exists via
  `git worktree add --detach .oracle/<tag> <tag>`; `.oracle/` is gitignored. Missing tag or
  worktree failure aborts loudly, printing the exact remedy command.
- **Per cell:** two driver subprocesses (old side: `PYTHONPATH=.oracle/<tag>/src`, invoked
  by driver file path; new side: `PYTHONPATH=src`), `cwd` = repo root for both so the
  **shared pack path from the working tree** is read by both sides. Then
  `compare_traces`.
- **Environment hygiene:** subprocess env carries only what the run needs; the msgpack
  compile cache is bypassed (`use_cache=False` in the driver) so neither side reads the
  other's artifacts.
- **Venv note (recorded assumption):** both sides run in the repo's uv venv. Valid while
  the dependency lock is unchanged since the tag (it is, at HEAD). If a rebuild moves the
  lock, the old side gets its own env — that change lands with the knockdown that forces
  it.
- **Output:** `runs/differential/<run-id>/` containing all trace files and `report.json`;
  human-readable table to stdout. Exit 0 iff every cell is `AGREE` or `SKIPPED`.

### `matrix.py` — the declared comparison matrix
- Explicit list of cells: `(pack, level, num_agents, steps, seed, device)`. No discovery
  magic; cells are declared, per the no-defaults principle.
- **v1 matrix:** the five `default_curriculum` levels (the three distinct universes among
  them — see `PDR-0018` — plus the two POMDP/temporal variants), CPU, `num_agents=4`,
  `steps=100`, `seed=42`. CUDA duplicates of each cell exist behind `--cuda`; without the
  flag they report `SKIPPED("cuda not requested")`, with the flag but no CUDA device,
  `SKIPPED("cuda unavailable")` — never silent.

## Verdicts

`AGREE` · `DIVERGE(step, stream, indices, max_abs_diff)` · `HASH_MISMATCH(hash_names)` ·
`OLD_SIDE_ERROR(stderr)` · `NEW_SIDE_ERROR(stderr)` · `SKIPPED(reason)`

`report.json` per cell additionally carries `register_refs: []` — the binding point where a
future register entry that touches traces will attach its suppression. v1 has no
suppression logic: the register's entries cannot produce trace diffs, so **any `DIVERGE` or
`HASH_MISMATCH` is a rebuild defect or a missing register entry** (both findings, per the
register's own rule). The report states this and cites `docs/oracle/known-divergences.md`.

## Error handling

- Driver exceptions: full traceback on stderr, non-zero exit → `*_SIDE_ERROR` verdict
  carrying the captured stderr. Loud, never swallowed (no broad `except` — the antipattern
  DIV-002 exists to delete).
- Harness pre-flight failures (tag missing, worktree add fails, pack path absent): abort
  the whole run with the remedy, before any cell executes.

## Testing (TDD, in `tests/test_townlet/unit/oracle/` + one integration test)

1. **Comparison unit tests:** identical traces → `AGREE`; a single perturbed element →
   `DIVERGE` locating exactly that step/stream/index; differing provenance hashes →
   `HASH_MISMATCH` naming them; constructed-metadata mismatch → raises.
2. **Driver smoke (in-process):** run the driver's main against `L0_0_minimal`, small
   steps, temp output — file exists, format round-trips, arrays have the declared shapes.
3. **Integration (marked slow):** subprocess **self-comparison** — the working tree run as
   both sides — must `AGREE`. Exercises the subprocess plumbing without needing the oracle
   worktree in CI.
4. A full old-vs-new run is a **CLI operation**, not a suite test (keeps the suite fast;
   the pytest-only home was rejected for exactly this).

## Acceptance criteria (falsifiable)

- (a) Full CPU matrix, working tree at HEAD (`fb87c848`, two doc-only commits past the
  tag) vs oracle → **all cells `AGREE`**.
- (b) A deliberate uncommitted behaviour mutation in the working tree (e.g. perturb a
  reward constant) → `DIVERGE` naming the correct stream and step — **red verified by
  mutation**, house rule.
- (c) All four gates green with the new package and tests included.

## Out of scope (v1)

- Checkpoint-boundary probe scenarios (DIV-001/002 adjudication) — added when a knockdown
  touches that surface.
- Register-driven suppression logic — arrives with the first trace-touching entry.
- Per-cell pinned old-side packs (needed only if a schema change makes the shared pack
  unparseable by the oracle) — requires a register entry first.
- Training-loop comparison (optimizer/backward) — the oracle explicitly does not claim GPU
  training determinism (`ORACLE.md`).
