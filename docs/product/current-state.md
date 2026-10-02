# Current state — Townlet · 2026-10-02

## Delivered and verified

The retained October 1 hosted-main reading is **`95b2f828dae4f52d6e30e79600fc3491364a1eb5`** after
[PR #44](https://github.com/foundryside-dev/hamlet/pull/44), merged October 1 at
15:08:34 UTC. Its exact-main Lint, Config Validation and Tests all succeeded.
Hosted tests report **4,276 passed / 19 skipped / 15 warnings / 85% coverage**.
[Hosted receipt](evidence/static-access-review/hosted-delivery.md) records identities,
run links and log custody; the previous brief's local-only claim is superseded.

| Package | Accepted contract | Evidence |
| --- | --- | --- |
| Declaration Cut A | Content discovery, scoped merge, provenance/duplicates, authored clock | PDR-0149 |
| Canonical-variable Cut B | Explicit lifetime/default/expression semantics, symbols and typed token scope | PDR-0151 |
| Static access | Explicit finite roles, independent exposure, checked access/write intent, immutable policy and cache/checkpoint identity | PDR-0153 |
| Review repairs | Effect preflight/reapplication, immediate nested refusal rollback, deterministic item allocation and structured variable identities | [PDR-0156](decisions/0156-static-access-review-refusal-and-identity-repairs.md) |

PR #42 delivered the first three at `72977928`; PR #44 delivered repairs qualified
at `7eb7ded3`, with unchanged runtime/test/config source through the merge.
Retained local qualification is **4,277 passed / 18 skips / 15 warnings / 85%
coverage**, plus 397 focused item/effect and 988 compiler/oracle/access checks.
The earlier owner-requested local merge passed 432 post-merge checks. These are
separate readings, not a fresh suite during this resume.
[Verification](evidence/static-access-review/verification.md) retains their limits.
Both requested Filigree Markdown reference files were committed as `80d6a5ce`
and included in PR #44. The three review repair issues remain closed:
`hamlet-f75ff623be`, `hamlet-bae419a592`, `hamlet-940089c925`.

## Selected package: truthful episode lanes

The owner's branch **`fix/episode-lane-accounting`** implements
[PRD-0005](prds/0005-truthful-episode-lanes.md). Complete production candidate
`462e8a3980845d76e7987cfea67fb63432bcb847` has passed **4,652 tests / 18 skips /
31 warnings / 85% branch coverage**, plus lint/type/no-defaults/compiler and
33-pack gates. The accepted final candidate is `7dc1d02e78d8b70bd096fc4c84b4d95a9822c94f`: only
two test readers changed after that full suite; 30 strict affected cases pass
with zero warnings and all other 1,059 execution files remain exact.
[Astra accepts criteria1–8](evidence/episode-lanes/implementation-review.md),
with no blocking findings. Execution `hamlet-78ad37dd49` and engine bug
`hamlet-d6fc84d147` qualify for closure at the local documentation landing. [Verification](evidence/episode-lanes/verification.md) retains the
full source/evidence identities, actual commands, skipped cases and limits.

The authored two/five fixture now reports survival **`[2,5]`**, five vector ticks,
seven live transitions and **zero accounting error**. Standard/PER replay retain
seven actual transitions; recurrent sequences complete `[2,5]` once each.
RND normalization/ingestion use eligible samples; completed outcomes own their
observations/meters. Actual Q/predictor updates and loss targets qualify terminal
versus cap bootstrap. Two consecutive ordinary recorded episodes reconcile real
SQLite/TensorBoard/curriculum/recording/replay/observer and both CSV exporters.
Budget/cap/checkpoint cuts preserve valid successors and complete once.

Strict format cuts refuse old nested population checkpoints, recordings and DBs;
historical artifacts remain unchanged. Astra's implementation review found one
exporter refusal that opened original WAL-mode SQLite files and created sidecars.
The repaired reader validates an isolated snapshot, preserves the whole original
family on success/refusal and passes actual exporter and custody controls.

The six final lifecycle recipes qualify all 799 prospectively declared changes
and preserve 4,008 other parent readings. Eight real learned numerical recipes
qualify through the prospectively reviewed CPU-controlled reset fixture in
[PDR-0160](decisions/0160-align-controlled-reset-inputs-without-changing-production-rng.md).
The original uncontrolled bank remains failed: replay changes global RNG
consumption, so this qualification does not establish production RNG isolation.

The unchanged static-access and frozen scripted commands retain **exit1**:
exactly seven dead-entry row99 rewards lose false retirement bonuses.
[PDR-0161](decisions/0161-adjudicate-exact-inherited-terminal-bonus-coordinates.md)
qualifies those exact coordinates through a prospectively frozen checker and
42 rejected private-copy corruption controls. Original outputs, dirty flags,
register allowances, frozen input bytes and harness remain preserved. No whole
reward-stream allowance is added and neither original command is called passing.

The baseline/planning receipts remain historical evidence of the parent defects,
including `[5,5]` survival, phantom replay/RND rows and unstable final meters.
E0a's ten ordinary shutdown/index witnesses and S3's real producer-to-observer
pipeline pass; general recorder repair was unnecessary. The accepted revised
plan in PDR-0159 and its original prospective declarations remain unchanged.

## Recovery and product judgment

Recovery remains open. **PDR-0058's register-growth trigger remains unresolved**:
sixteen divergences, five retired and eleven nonterminal, including DIV-016. Review task
**`hamlet-4554a428b2`** must produce a concrete exit/instrument proposal. The frozen
oracle, inputs, current exit and authority grant stay intact. Episode integrity
is a prerequisite for credible learning evidence, not a substitute retirement exit.
[PDR-0157](decisions/0157-episode-lane-package-and-merged-repair-delivery.md) records
this scope and delivery reconciliation.

No current-main multi-scenario compile → render → converge milestone is qualified.
Historical M4 remains four passing token cells at training `9d4e942f`, one training
seed and its fixed protocol. Static access is not per-owner privacy
(`hamlet-83a043a9b9`); effect reset (`hamlet-d76684f549`), initial-item cache fidelity,
RNG isolation, complete BAC cognition, viewer behavior, Murk and model export
remain separate work. No north-star authoring success rate is revived.

Astra's plan re-review, original implementation refusal and scoped repair audits
are retained separately from its final **ACCEPTED** verdict.
[PDR-0162](decisions/0162-accept-bounded-truthful-episode-lanes.md) records the
local acceptance and reversal conditions. This checkpoint is local to the feature
branch. There is no new main merge, push/PR, hosted CI, CUDA or convergence
reading for this package. Keep the recovery exit review and effect-reset task
open; accept any later scope change only from a concrete dependency witness.
