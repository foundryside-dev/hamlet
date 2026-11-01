# T18c implementation receipt

Adds real encoder/inverse/forward models with Adam, raw half forward-feature-MSE curiosity and detached successor targets. Reward computation is separate from transition admission/service. Bounded FIFO, paced vector-tick budgets, overflow accounting and complete owned atomic state make real service observable. Observation-only calls refuse missing transition context.

28 focused cases and161 exploration-owner cases passed; independent warm-Adam/further-update continuation and source review retained. The common final-tree full suite passed6103 tests,15 skipped.

Source change: `9426e3dd0b3be7af132848a615775552fa8ad14e`. Qualified common release: `322e67a3a01770e7c78b4052cb22e999726c8f62`, tested tree `eada2071e845a03f1bf4e34c7e9b3cfc21c505d6`. The full suite passed **6103 tests,15 skipped,15 warnings** in1331.23s (1338.53s wall). Both earlier failed runs and causal fixture repairs remain recorded in [the qualification receipt](../evidence/wave04-qualification.json). Prefix commit heads were not separately full-qualified.

CPU proof only; no CUDA or cross-device bitwise claim. Private initialization/RNG/local service clocks and actual bank/production reward wiring remain required.

All six standing guards passed on repaired r11; source hashes and exact tree/import/fixture checks accompany the final qualification receipt. Source/test owners and reviewers stayed within at most five whole source files/5000 source lines, including counted probes. Existing14 worktrees preserved; no project branch/worktree/source copy created by this wave.

Historical approval A and strict per-world approval B remain in force. No scope reduction, new publication/merge authority, whole-BAC completion, GPU pass or final acceptance is claimed. Later finite packets,22 fresh final source/design lenses plus synthesis, finite learning/E2E, coverage/slow/applicable hardware/source-verified docs and exact-tip remote CI remain owed.
