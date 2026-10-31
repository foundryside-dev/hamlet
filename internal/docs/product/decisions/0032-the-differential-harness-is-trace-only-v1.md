# PDR-0032 — The differential harness is trace-only v1, lives in `src/townlet/oracle/`, and runs both sides live

Date: 2026-08-13   Status: **accepted** (within grant — dispatch/accept; the three
structural choices were each put to the owner this session and each endorsed)
Author: Claude (standing product owner)
Related: `PDR-0006` (the strangler this serves), `PDR-0030` (the oracle it compares against),
`PDR-0031` (the config-declared seed that makes the comparison reproducible), `PDR-0028`
(the register that adjudicates diffs)
Tracker: `hamlet-e3af412673` (WS-7 content 3) · Spec:
`docs/superpowers/specs/2026-08-13-differential-harness-design.md` · Plan:
`docs/superpowers/plans/2026-08-13-differential-harness.md`
Delivered: `c27b879d`…`d54ad7df` (nine commits)

## Context

WS-7 content 3. The strangler judges every knockdown by running the frozen oracle
(`oracle-2026-08-13` → `0e875d7a`) beside the rebuild and asserting they agree everywhere
`known-divergences.md` does not say otherwise. Three structural questions had to be settled
before any code: what the v1 compares, where it lives, and how two incompatible versions of
the same package execute against one another.

## Options and the calls

**1. Scope — trace-only v1** (vs also building checkpoint-boundary probes now).
Taken: trace-only. The register's only two entries (DIV-001, DIV-002) are checkpoint-boundary
behaviours that *cannot* manifest in an env-step trace, and the nominated first knockdown
(terrain/substrate) has exactly the trace as its blast radius. Building probe machinery ahead
of any knockdown that needs it is speculative work. Probes arrive when a knockdown first
touches that surface.

**2. Home — `src/townlet/oracle/`** (vs `scripts/`, vs pytest-only).
Taken: a real package under all four gates with its own tests. `scripts/` would put the
programme's central artifact outside `mypy`'s scope — the one unchecked piece of code in the
repo. Pytest-only would conflate "the tree's own suite" with "old-vs-new comparison" and put a
worktree-spawning subprocess fixture inside every full run.

**3. Execution — injected driver, both sides live** (vs golden recorded traces, vs dual import
in one interpreter). Taken: one self-contained driver script, run by file path in two
subprocesses per cell with `PYTHONPATH` at each side's `src`, `cwd` at the repo root so both
compile the *same* working-tree pack. Golden traces were rejected because the recording would
become the spec instead of the tagged tree — the opposite of "consult the oracle
mechanically." Dual import was rejected because module caching and torch C-extensions make
same-process version aliasing unreliable, and an aliasing bug would poison the very
comparisons the strangler depends on.

## Consequence accepted knowingly

The driver **duplicates** trace-writing rather than importing `trace_io`, because it must run
under the frozen tag where `townlet.oracle` does not exist. The duplication is pinned by a
source-scan test and a round-trip test, and the format version is pinned equal in both files.
This is the one place the codebase's no-duplication instinct is deliberately overridden; the
alternative is a harness that cannot run against its own oracle.

## Reversal trigger

- **Re-open the scope call** the moment a knockdown touches a checkpoint boundary — at that
  point trace-only is insufficient by construction and probe scenarios become the blocking
  work, not speculative work.
- **Re-open the execution call** if a rebuild changes config schema such that the oracle can
  no longer parse the shared pack. That requires a register entry plus a per-cell pinned
  old-side pack, and it invalidates "both sides compile the same working-tree pack."
- **Re-open the home call** if the harness ever needs to run where `src/townlet/` is not
  importable (a packaging change, a CI image without the dev extras).
