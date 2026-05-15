# Architecture Analysis — Coordination Plan

## Analysis Configuration

- **Scope**: `src/townlet/` (152 files, ~40K LOC), `scripts/`, `tests/test_townlet/` (305 files), `configs/`, `pyproject.toml`. Excluded: obsolete `src/hamlet/`, `frontend/` (Vue UI; referenced only as a downstream consumer).
- **Deliverables**: **Option A — Full Analysis** (discovery, catalog, diagrams, final report). No quality assessment / architect handover unless surfaced as warranted.
- **Strategy**: **Parallel fan-out** over 8 logical subsystems (justification below).
- **Time constraint**: None stated.
- **Complexity estimate**: **Medium-High** — substantial declarative-compiler machinery (universe + VFS + effects) and a vectorized GPU-tensor runtime, but boundaries are well-defined at the directory level.

## Logical Subsystem Grouping

15 source directories collapse to 8 cohesive subsystems by responsibility:

| # | Subsystem | Source directories | Approx. LOC |
|---|-----------|-------------------|-------------|
| 1 | Universe Compiler & Loaders | `universe/` (with `compilers/`, `dto/`, `loaders/`, `validation/`, `adapters/`) | 5,658 |
| 2 | Configuration / DTO Layer | `config/` | 4,725 |
| 3 | Environment & DAC Runtime | `environment/` | 5,283 |
| 4 | Effects (compiler + runtime) | `effects/` | 2,951 |
| 5 | Substrate, World & Items | `substrate/`, `world/`, `items/` | 7,983 |
| 6 | Agent, Population, Training, Exploration | `agent/`, `population/`, `training/`, `exploration/` | 5,435 |
| 7 | VFS (Variable & Feature System) | `vfs/` | 2,301 |
| 8 | Curriculum, Recording, Demo | `curriculum/`, `recording/`, `demo/` | 5,579 |

## Strategy Decision: Parallel

Justification per the orchestration heuristics:
- ≥ 5 subsystems → parallel favored.
- Total ≈ 40K LOC source → above the parallel threshold (20K).
- Directory boundaries cleanly partition responsibilities; the universe-compiler is the only inbound hub from configs into the runtime, and its inputs/outputs are typed DTOs (low coupling at the catalog level).

## Execution Log

- **2026-05-15 16:19** Created workspace `docs/arch-analysis-2026-05-15-1619/`.
- **2026-05-15 16:19** Discovered prior scoped pass at `docs/arch-analysis-2026-05-15-compiler-cleanup/` — referenced, not duplicated. That pass predates the universe/ reorganization visible in `git status`.
- **2026-05-15 16:19** Selected Option A (Full Analysis) without user prompt per the no-clarifying-questions session directive; menu still surfaced in this file.
- **2026-05-15 16:19** Holistic scan complete (this commit). Discovery findings → `01-discovery-findings.md`.
- **NEXT** Fan out 8 Explore subagents → catalog entries → merge to `02-subsystem-catalog.md`.

## Prior Work Cross-Reference

`docs/arch-analysis-2026-05-15-compiler-cleanup/` contains:
- `01-discovery-findings.md` — compiler-only discovery (treats `compiler.py` as a 4,431-line monolith)
- `02-compiler-map.md` — pipeline stage map
- Mid-flight cleanup; current `git status` shows the modular split in progress (`compilers/`, `dto/`, `loaders/`, `validation/`).

This analysis treats the **post-reorganization** state as ground truth and notes deltas where the older doc diverges.
