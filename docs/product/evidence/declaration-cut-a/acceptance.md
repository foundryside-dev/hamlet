# Declaration-store Cut A — acceptance evidence

Production-source/matrix checkpoint: `144788f88b4e3c70ab0648e452672f9b61a5b7f2`.
Final executable/test checkpoint: `75600ef1802007678b46edbddeb01715d365ca00` on
`feat/declaration-store-cut-a`, based on `project-recovery-4@64f5d3f5`.
The later evidence commit changes documentation only; production/test trees remain this checkpoint.
Prepared 2026-10-01 Australia/Canberra. PR: [#40](https://github.com/foundryside-dev/hamlet/pull/40).

## Claim and formal boundary

This checkpoint implements PRD-0002/PDR-0147 Cut A: authoring transports are discovered
by content, declarations merge by scoped identity, and unsupported/malformed inputs fail
with source provenance. No environment, learner, network, observation or variable-access
semantics are changed. Cut B and the compile/render/converge milestone remain separate.

The PRD's September 16 acceptance window was missed. Its exact wording is:
“Missing the date without an accepted extension recorded in a PDR is a reject on every
criterion.” The October 1 continuation instruction does not record such an extension.
Consequently **formal acceptance remains rejected on calendar grounds**, regardless of
functional test results. No acceptance PDR or retroactive date extension is fabricated.

## Criterion readings

| PRD criterion | Functional evidence | Formal date reading |
| --- | --- | --- |
| 1: Original strays are loud | Original five source blobs banked before correction in `tests/test_townlet/fixtures/declaration_store/items_smoke_strays`; public compiler refusal test names every path and line | Missed |
| 2: One clock authority | Default L3 references `day_phase`; period mutation changes both effective curriculum time and token normalization; unknown/wrong-kind/fractional/boolean/inactive and equal/unequal duplicate controls refuse | Missed |
| 3: Required declaration | Nested renamed drive and experiment witnesses compile; missing drive names its family rather than a mandated filename | Missed |
| 4: Collisions | Singleton and catalog collisions name both actual declaring origins, including pack profile namespaces and level documents | Missed |
| 5: Refusal provenance | Registry-linked witness covers all 21 codes in the four pinned families via real public compiler refusals; checks every raised issue's code, source and positive line | Missed |
| 6: Hash integrity | Committed before snapshot and complete after comparison: 31 cases, 884 readings, all 853 semantic readings identical; six transport-digest readings move only on the two approved packs | Missed |
| 7: Gates/harness | Final gate outcomes are recorded below; DIV-013 changes only input bindings, with no new output allowance | Missed |
| 8: Hygiene/docs | Filename dispatch/parallel source parser/obsolete preflight APIs/dead static-variable filename loader deleted; canonical authoring references corrected; no defaults whitelist added | Missed |

The before snapshot was committed at `ee520090`, before the first production edit.
The preceding plan/PRD-only commit `cc21d013` did not contain the ignored JSON; the
follow-up forced-added it before implementation. The original parent PRD draft remains
untouched. Source baseline for the readings is `64f5d3f5`.

## Reproduction and gate outcomes

Run from the isolated worktree with its independent locked virtual environment. Installation
used `uv sync --locked --extra dev --extra recording`; Python 3.13.1, torch 2.11.0+cu130.
CPU correctness is the claim. CUDA, training convergence and browser acceptance are unmeasured.

- `.venv/bin/ruff check .`
- `.venv/bin/black --check src tests`
- `.venv/bin/mypy src/townlet --show-error-codes`
- `.venv/bin/python scripts/no_defaults_lint.py src/townlet/ --whitelist .defaults-whitelist.txt`
- `.venv/bin/python scripts/validate_compiler_cli.py`
- `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 .venv/bin/pytest`
- `.venv/bin/python scripts/check_declaration_cut_a_hashes.py --output /tmp/after-hashes.json`

Ruff, Black, mypy and no-defaults passed at the engineering checkpoint. No whitelist edit;
558 source/test Python files formatted, 177 source files type-checked. All 28 CLI packs passed
including three expected failures. The after comparison passed with zero unexpected movements.
At evidence preparation, full pytest and hosted exact-tip outcomes are pending. The completed
`144788f8` suite found exactly three obsolete test assumptions (3969 passed, 18 skipped,
three failed; coverage 84%). Commit `75600ef1` repairs those tests; all 24 cases in their
complete files/initialization class pass. The complete suite is rerunning without exclusions.
Interrupted earlier attempts are not passing evidence.

Terminal local-suite, pushed-tip CI and local recovery-branch integration readings are recorded
after execution in implementation issue `hamlet-e62029114c`, acceptance issue
`hamlet-41e79fb08b`, and [PR #40](https://github.com/foundryside-dev/hamlet/pull/40).
This immutable preparation record does not predict those later outcomes or use an earlier
workflow SHA as proof of the evidence commit. The acceptance decision is
[PDR-0148](../../decisions/0148-declaration-cut-a-banks-engineering-evidence-but-misses-the-acceptance-window.md).

The CPU matrix uses the harness's `default_cells`, `run_cell_safely`, `write_report` and
`exit_code` against the existing clean `oracle-2026-08-17` worktree, whose HEAD is verified
against the tag. This avoids creating or editing anything under `.oracle/`. Both sides use
the usual declared pack roots; the old side reads untouched `oracle_fixtures/` and the new
side reads `configs/`. Exact checkpoint report: `runs/differential/declaration-cut-a-cpu-144788f8/report.json`.
The exact-checkpoint matrix completed with exit 0: ten CPU cells were
`DIVERGED_AS_REGISTERED`; ten CUDA cells were skipped. The committed `cpu-matrix.json`
retains all verdicts and clean-source provenance. `cpu-matrix-command.txt` retains the
exact runner used against the existing oracle worktree.

DIV-013 records the complete byte deltas for default_curriculum/items_smoke, preserves the
inherited DIV-007/008/012 input rows, and declares no hash fields or streams. Tests pin both
complete delta inventories. Existing output-divergence tuples are unchanged.

## Remaining filename literals under `src/townlet/universe/`

No canonical filename chooses a loader, validator or diagnostic. Survivors are:

- `declarations.py`: `.yaml`/`.yml` suffix vocabulary for transport enumeration.
- `compilers/vfs.py`: historical emitted `VariableDef.description` text mentioning the VFS
  profile filename; descriptive payload retained without any reader/error dispatch.
- `compiled.py`, `compiler.py`, `raw_configs_v21.py`, `dto/universe_metadata.py`,
  `dto/token_spec.py`, `compilers/metadata.py`, `compilers/observation.py`, `compilers/vfs.py`:
  explanatory comments/docstrings referring to conventional examples or historical changes.

The separate observer presentation adapter still reads its conventional file. The compiler
recognizes/validates that metadata but does not publish a new display transport. This limitation
is explicit in the authoring references rather than an execution compatibility path.

## Deferred defects and custody

Item token capacity still includes ground plus held capacity while the registry arena uses only
world capacity. Dead durability rows and held-item invisibility remain filed, unchanged.
The pre-existing item-appearance cache serialization defect also remains; this cut makes no
claim of warm-cache fidelity for item spawning. Existing level/cache identity regression tests
qualify their stated paths; broader artifact repair belongs to the next program of work.

The original parent checkout's unrelated skill-document edits and untracked PRD are preserved.
Frozen oracle fixtures are unchanged. No migration readers, new behavioral defaults, training campaign or
Murk migration are included. Local integration, push and hosted checks are reported separately
when completed. Cut B does not start before the formal checkpoint decision.
