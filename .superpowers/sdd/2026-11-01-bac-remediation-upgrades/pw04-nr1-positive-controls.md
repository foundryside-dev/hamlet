# NR-1 independent optimizer-history component controls

Authored 2026-11-14; **unexecuted by this owner**. Root is sole test/application executor. This report supplies test readiness, not a passing result, native installation evidence, producer-counter proof, or PW04 acceptance.

New owned test: `tests/test_townlet/regressions/bac/test_population_optimizer_history.py`, 141 lines, SHA256 `2c7a52e760178719f2c6a0787afd7a862b4e2e3b861e17242ddc4c57bf735948` at handoff. The test calls production structural validators followed by the newly supplied pure classmethod `_validate_optimizer_update_history(checkpoint, optimizer=..., scheduler_initial_epoch=...)`. It does not construct a population, environment, native parent, checkpoint authority, or installation stand-in.

## Independent history oracle

Actual CPU Torch optimizers receive three named parameters (`early`, `late`, `never`) in two deliberately reordered groups: `[late, never]`, `[early]`. A first real backward/update uses only `early`; the second uses `late` and an explicitly zero tensor gradient for `early`. `never` receives no gradient. Therefore the independently specified optimizer-order history is `[1, 0, 2]` after two successful updates. The expected list is not calculated by copying production participation-counter logic or obtained from production export. State dictionaries come from real optimizer steps; deliberate negative mutations occur only afterward. StepLR's baseline is captured at actual scheduler construction before either step.

The finite 39 intended cases cover actual Adam, AdamW, RMSprop, stateless SGD and momentum SGD initial/lazy states; stateless SGD's permitted explicit empty parameter mappings; exact count types, negativity, topology, ledger bounds and per-parameter mismatch; erased participant/populated never-participant lazy state; adaptive optimizer reset, fractional and advanced steps; an impossible initial positive count; and a coherently rewound scheduler epoch/count. Adaptive state-step values are independently checked as early=2 and late=1. SGD tests explicitly check empty state or momentum-buffer-only state, inventing no SGD step counter.

## Scope and outstanding proof

Counted before source reads. Three charged whole implementation/test bodies at handoff: POP `src/townlet/population/vectorized.py` 3571; factory `src/townlet/agent/optimizer_factory.py` 162; new test 141; total **3874/5000 lines, 3/5 bodies**. Source bodies are charged in full even though only relevant POP sections were read. No existing parent test, runner, BANK, or runtime body was opened. Read AGENTS and the supplied NR-1 proposal/review. Only this new report and the new test were written; no Git operations, branches, worktrees, source copies, application imports or test execution.

Factory inspection confirms the supplied parameters iterator goes directly to the selected supported Torch optimizer without filtering. Root separately owns actual producer participation counters, strict schema8 export/restore, stable native owners, restored next-update continuity, ambient RNG refusal behavior and real runner artifacts. These component controls make no claims about those properties.

Long-counter saturation is deliberately separate from this small-history suite. Root supplied the actual Torch2.11 CPU probe result: after one genuine initialization update, seed scalar float32 step to `2**24 - 1`, then execute two actual steps; Adam/AdamW/RMSprop yield `[16777215, 16777216, 16777216]`. This report did not execute or independently inspect that probe and supplies no CUDA qualification. Root must retain its exact execution provenance separately; the component suite is not a substitute for that boundary evidence.

Ready for root execution and any resulting bounded correction. No GREEN/complete claim is made here.
