# PDR-0137 — M4 is a deterministic engineering qualification, not a statistical study

Date: 2026-09-01   Status: **accepted** (human owner: no scientific audience; unpack this as an engineering problem)
Author: Codex (standing product owner)
Related: `PDR-0114`, `PDR-0122`, `PDR-0132`, `hamlet-25fc3fb955`

## Context

The original reversal trigger inherited a five-training-seed IQM and confidence-interval
procedure from a research-style comparison. Applied to four M4 cells, that is twenty full
training runs. The frozen baseline shows that each seed consumed a 12-hour guard; even with both
local GPUs, the literal matrix is roughly 120 GPU-hours. That cost does not answer a product
question HAMLET currently has. The project is pre-release, deterministic for a fixed seed and has
no scientific audience to support with population-level inference.

The engineering question is narrower: does each implemented token architecture learn the shipped
L2 task to the existing gross-regression floor under a real, equal transition budget, while its
structural contracts remain intact?

## The call

M4 runs the four actual configurations — token feedforward and token recurrent, each with mean and
attention aggregation — on **training seed 45 only**. Seed 45 is the shortest frozen budget
(2,278,640 summed-live-agent transitions) and the lowest-scoring baseline member (98.83 greedy
mean survival), making it the strictest inexpensive deterministic representative. Each candidate
gets that exact budget, subject only to the indivisible eight-lane vector-step shortfall of at most
seven transitions.

Every cell must independently reach **79.19466666666668 greedy mean survival** under the frozen
100-episode, eight-agent, seed-12345 evaluation. The 79.19 floor is unchanged. The result is a raw,
reproducible engineering qualification; it is not called an IQM, given a confidence interval or
generalised beyond the pinned seed and pack. A failing cell is an engineering failure to debug,
not an invitation to rerun seeds until one passes.

The source tree, harness, four complete brain templates, compiled token identities, parameter
counts, commands, timings, transition accounting and all 800 raw survival values remain pinned in
the artifacts. Structural acceptance remains unchanged: batch 256, mean and attention execution,
visibility, cross-universe transfer, recurrent BPTT/memory and checkpoint refusal all stay gated.

## Consequences

- The M4 training cohort is four runs, not twenty; the confidence-interval machinery is deleted.
- `PDR-0114` reversal trigger 1 is superseded only in its sampling/statistical procedure. Its
  architecture coverage, equal-budget comparison and 79.19 floor remain in force.
- This ruling does not weaken implementation coverage and does not create a deferred verification
  item. It removes evidence that served no engineering decision for this product stage.
