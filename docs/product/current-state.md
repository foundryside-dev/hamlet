# Current State — HAMLET / Townlet        Checkpoint: 2026-08-11 · first checkpoint (workspace created this session)

## The bet right now

**Strangler rewrite behind the compiled-universe contract** — freeze the current system as an
oracle, then knock down and rebuild one design-space unit at a time against it. Keeps the
provenance spine; re-earns the rest through a differential harness. Moves **Declared-but-inert
config surfaces** (~40 → 0) and **Config-surface coverage** (~2 of 7 → 7 of 7). `PDR-0006`.

## In flight

Recovery milestone **`hamlet-1ade187dcc`**, eight work streams, dependency graph wired.

- **WS-1** `hamlet-67ffbd282a` (P0) — **ready, no prerequisites.** Cache not keyed on
  `primary_level`; recurrent path trains memoryless; +2. Must land **before** the oracle freeze —
  freezing a bug makes it a requirement.
- **WS-7** `hamlet-e3af412673` (P0) — the strangler's enabling stream. Blocked by WS-1. Contains
  `hamlet-834108b55a` (no seeding API).
- **WS-6** `hamlet-5e39fcccb0` — **ready.** Plan reconciliation, re-scoped down by `PDR-0006`.
- **WS-0** `hamlet-8eeaba1461` — **ready.** Frontend metadata + `.gitignore` root cause; migrate
  and retire the pre-filigree markdown stratum.
- **WS-2 / WS-3 / WS-4 / WS-5** — `hamlet-337b9e80fb`, `hamlet-1f89714685`, `hamlet-15050f280a`,
  `hamlet-ad2773718a`. All blocked. WS-3 now reshaped into the **differential harness**.

Superseded: `hamlet-7a932c4e40` (2026-05-16 architecture-gap milestone), annotated; its three open
children reparented into WS-0 / WS-3 / WS-5 with scope corrected.

## Open questions / blocked-on-owner

- **Confirm `vision.md` reads as you meant it.** It was written this session from your in-session
  statements (the authoring pivot; Townlet Town as first-class tech demo; the two claims and their
  tension). The words are mine; the substance is yours. A vision change is a one-way door — please
  read it back. **[escalation]**
- **The public README carries a false claim.** The 70% coverage badge is contradicted by the
  project's own audit (19%, itself untrusted). The repo is public. Correcting or removing it is an
  outward-facing edit — not done. **[escalation]**
- **Confirm the `src/townlet/recording/` deletion** (~1,150 LOC + ~2,600 test lines, WS-2). Filed
  as intent, not executed. **[escalation]**
- **Which knockdown is first?** Terrain/substrate is the strongest candidate — three of four
  substrate crashes collapse to one change, and it is where the 6-D demo hits its only wall.
- **Determinism beyond CPU** — GPU float nondeterminism and the `vtc_kernels.py` TorchScript-JIT
  path are untested. Both could weaken the oracle.
- **What is the real test coverage?** Unresolved from bootstrap. Needs one clean full-suite run.

## Last checkpoint did

This was the **first** checkpoint; the workspace did not exist at session start.

- Bootstrapped the five artifacts and recorded the **vision pivot** — from *game as experience* to
  *writing a game as experience*; authoring-first, UAC → BAC → one compiler. `PDR-0001`, `PDR-0003`.
- Ran a **maturity assessment** (12 agents, `wf_4ca82820-274`): REPAIR × 8, ~40 declared-but-inert
  config surfaces, `specification` weak in all 8. Report saved under `assessments/`. `PDR-0004`.
- Reframed inert surfaces as **unfinished plan steps, not decisions** — default is wire, not
  delete. `PDR-0005`, later amended.
- Adopted the **strangler strategy** and filed the whole program into filigree. `PDR-0006`.
- **Trial 001 passed**: Sims in six dimensions, ~6 lines of config, zero `src/townlet/` changes.
- **Verified determinism is satisfiable** but found no seeding door — a provenance hole, filed.

## Next session, start here

**WS-1** (`hamlet-67ffbd282a`) — ready, P0, and it gates the oracle freeze. Confirm the
cache→checkpoint-provenance link **by execution** first; that link is source-inferred, not run.

Then **WS-7**, starting with the seeding fix (`hamlet-834108b55a`), and mine
`docs/plans/2026-05-15-compiler-cleanup-modernization.md` for the knockdown playbook — the owner
already ran this operation on the compiler successfully.

Read `vision.md` before deciding anything, then `PDR-0006` for why strangler beat both repair and
full rebuild. Do not re-litigate that; it was decided with the owner on evidence.
