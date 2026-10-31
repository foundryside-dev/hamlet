# 00 — Coordination Plan

## Analysis Configuration

- **Scope:** Entire repository at `/home/john/hamlet`
- **Date:** 2026-05-16
- **Deliverables:** Option A (Full Analysis) — comprehensive document set
  - Selected unilaterally per user directive ("no clarifying questions") and stated goal of *recreating the document set*
- **Strategy:** PARALLEL — 8 codebase-explorer subagents in one batch, one validator, one diagram agent, one quality agent, one security agent
- **Time constraint:** None stated
- **Complexity estimate:** **Medium-High**
  - Source: 45,117 LOC Python, 162 files
  - Tests: 77,265 LOC Python, 324 files (test corpus ≥ source — ultralarge trigger)
  - Frontend: 10,432 LOC Vue/JS
  - Docs: 499 markdown files (just under ultralarge threshold)
  - Decision: stay on standard track because src LOC stays under 50K and subsystem count is tractable; document the test-corpus signal as a quality finding rather than expanding to ultralarge track.

## Critical Constraint from User

> "This analysis will be the start of a recreation of the document set so do not rely on documentation to assess the state of the architecture."

**Implication:** Treat `docs/`, `CLAUDE.md`, `AGENTS.md`, `README.md`, and `CHANGELOG.md` as **possibly stale**.
Subagents derive findings from **code only**. Documentation is allowed as a corroborating signal but
never as the sole source for any catalog claim.

**Concrete drift already observed during orientation:**
- `CLAUDE.md` references config packs `L0_0_minimal, L0_5_dual_resource, L1_full_observability, L2_partial_observability, L3_temporal_mechanics` as the active curriculum.
- The actual `configs/` directory contains: `aspatial_test, default_curriculum, L5_multi_agent, reference, simple, test`.
- The active config layout is `configs/default_curriculum/<level>/` (hierarchical v2.1), per `scripts/run_demo.py --config configs/default_curriculum --level L1_full_observability`.

## Subsystem Partition (8 groups)

| ID | Group | Locations | LOC (approx) |
|----|-------|-----------|--------------|
| SG1 | Universe Compiler (UAC) | `src/townlet/universe/` | 5,750 |
| SG2 | Variable & Feature System (VFS) | `src/townlet/vfs/` | 7,080 |
| SG3 | Configuration DTO Layer | `src/townlet/config/` | 4,728 |
| SG4 | Environment & DAC Reward Engine | `src/townlet/environment/` | 5,041 |
| SG5 | Substrate & World Expression | `src/townlet/substrate/`, `src/townlet/world/` | 6,831 |
| SG6 | RL Training Stack | `src/townlet/{agent,population,training,exploration,curriculum}/` | 6,427 |
| SG7 | Effects & Items | `src/townlet/{effects,items}/` | 4,480 |
| SG8 | Demo, Recording, Frontend | `src/townlet/{demo,recording}/`, `frontend/` | ~15,000 |

Cross-cutting concerns (`scripts/`, `configs/`, `tests/`, `deploy/`) are summarised by the coordinator
in the final report rather than handed to a per-subsystem explorer.

## Execution Log

- **2026-05-16 12:00** Workspace created at `docs/arch-analysis-2026-05-16-1200/`
- **2026-05-16 12:01** User invoked `/axiom-system-archaeologist:analyze-codebase` with no-clarifying-questions directive
- **2026-05-16 12:02** Selected Option A (Full Analysis) per stated goal of document-set recreation
- **2026-05-16 12:05** Orientation scan completed: 162 src files, 324 test files, 27 Vue components, 499 docs
- **2026-05-16 12:07** Identified 8-group partition; coordination plan written
- **2026-05-16 12:08** Discovery findings written (`01-discovery-findings.md`)
- **2026-05-16 12:10** Dispatched 8 parallel `codebase-explorer` subagents (SG1–SG8)
- **2026-05-16 12:30** All 8 explorers completed; per-subsystem evidence at `temp/sg{1..8}-*.md`
- **2026-05-16 12:35** Merged into `02-subsystem-catalog.md` with cross-cutting synthesis (deps matrix, drift catalog, concerns)
- **2026-05-16 12:40** Dispatched `analysis-validator` with 10 high-risk claims to ground-truth
- **2026-05-16 12:50** Validator returned **NEEDS_REVISION (warnings only)**: 8/10 confirmed, 2 refuted (decay_epsilon and VTCInteractionProgress both alive)
- **2026-05-16 12:52** Applied W1-W5 revisions to `02-subsystem-catalog.md`
- **2026-05-16 13:00** Dispatched diagram + quality + security in parallel
- **2026-05-16 13:20** All three completed:
  - `03-diagrams.md` — 5 Mermaid diagrams (Context, Container, Component-tick, Compile-pipeline, WebSocket sequence)
  - `05-quality-assessment.md` — concerning trending healthy; test README now rebaselined to measured counts plus 19% local coverage artifact, changelog worklog/release-note cleanup, P1 cleanups ~15-28 engineer-hours
  - `07-security-surface.md` — one **High** finding (RCE via tampered checkpoint, `weights_only=False`), 4 Medium deployment-posture findings
- **2026-05-16 13:25** Final synthesis `04-final-report.md` written with prioritised doc-recreation plan
- **2026-05-16 13:26** Awaiting advisor review before declaring complete
