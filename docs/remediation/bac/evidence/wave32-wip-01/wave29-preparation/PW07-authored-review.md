# PW07 independent authored-test adequacy review R1

SPEC: CHANGES REQUIRED.
QUALITY: CHANGES REQUIRED.

Reviewed frozen test SHA256 99153567e765a696c77ba401ef15e23edb30b6c45b8aaadc22e84c4f901ae26d (937 whole lines), authored patch SHA256 6fb8aa366991967157601a69360b1626ca9233895c6dd1dc2d22e3aac0dd5ba3, and appended author report SHA256 86c013ad4a8d1b7c910eb524b67eda2727ac92a8ac9f789babb2738899b1b91d. Test/report hashes matched actual files. Approved ABI proposal and original three named acceptance identities remain the review baseline; the earlier design review is unchanged.

The three exact named tests each cover all five families, both initialization choices and both service modes. Real typed policy/ENV authority, positive-LR native optimizer evidence, residual gradients, real captured replay serialization/load, and explicitly limited local other-role receipts are substantial positives. The following finite issues block calling this authored suite adequate for the approved ABI.

## F1 — Installed parent release is discarded: confirmed prerequisite fixture failure

Rig.install_parent calls env.install_world_restore but discards its returned installed release, then stores self.restored_release from authority.restored as self.release. Rig.begin subsequently passes that pre-install record to prepare_episode. Required disposition: retain the actual return of install_world_restore as self.release, following the supplied actual ENV API; keep genuine authority authentication and rerun all prerequisite cases before broad RED.

Root reports actual collection106 and prerequisite12PASS/5FAIL in17.4926s, with all five test_source_shared_and_live_same_scope_restore_remain_real families failing at next Rig.begin -> ENV prepare_episode with stale/unissued capability. This is attributed root execution, not an independent run. The static fixture defect explains that failure and would also stop later conversion positives before their next real updates. Do not count those failures as conversion RED.

## F2 — Compatibility negatives do not reach coherent source/target mismatches

test_invalid_conversion_refuses_without_live_effects edits source policy.provider_parameters.learning_rate alone. That makes the source internally inconsistent with its native policy/identity rather than supplying two separately valid, incompatible current source/target configurations. All ordinary fixtures otherwise construct the same family/LR/batch/capacity/geometry/seed/device pair. Thus an implementation that omits selected source-target compatibility checks could pass the current negative matrix through source validation alone.

Required disposition: add finite coherent mismatched target/source controls using actual resolved policies/descriptors for wrong family, selected LR, batch/capacity, geometry, seed/membership and declared profile; each side must pass its own relevant construction/native prerequisite before conversion refusal. Cover omitted initialization argument separately from invalid enum. Add actual foreign/stale parent-record custody cases alongside copied-record refusal, retaining source/destination equality and genuine retry. Do not fabricate malformed policies as substitutes for compatibility tests or require unavailable hardware to test a declared-profile mismatch.

## F3 — Converted ordinary restore lacks INITIAL and live-origin paths

The main origin test exercises private_initialized receiving permutation and completed private restore. test_initial_conversion_has_no_episode_or_closing_history begins directly without exporting/restoring that converted INITIAL state. test_source_shared_and_live_same_scope_restore_remain_real exercises only origin-less shared live state. No test restores a converted epoch1 live reservation/cache/receipt state against its actual receiving accepted token, or restores converted INITIAL origin before first begin.

Required disposition: exercise converted INITIAL ordinary restore and converted live ordinary restore, retaining exact origin/baselines/epoch/native/RNG/gradients and obtaining a genuine subsequent service/update. Include a foreign-epoch cached event/receipt refusal and positive exact retry. Retain origin-less private ordinary restore as the explicit zero-baseline countercontrol. This is required BANK continuation evidence, not an added active simulator scope-switch feature.

## F4 — Numeric archive/input and fixed-target ownership remain unwitnessed

The archive custody test mutates caller/output cursor scalar fields and clears callback mappings. It does not mutate supplied/returned model, optimizer, gradient, pending tensor, Count data or adaptive history after preparation/installation. storages(actual) examines newly emitted native snapshots, which are independently cloned even if underlying live owners alias. live.storage_ids records trainable modules/gradients/Adam, omitting RND/adaptive fixed target live storage. As a result, sharing a frozen target across private worlds or retaining numeric input/archive aliases can evade these assertions.

Required disposition: directly witness actual fixed-target storage separation and actual private RNG ownership/continuation independence, preserving the fresh same-ID initialized RNG baseline. Mutate representative real caller native/gradient/tail/Count/history numeric data after preparation and returned archive numeric data after install, then assert actual candidate/live/source/archive equality and independence. Keep None/zero/nonzero gradients and trainable Adam pairing assertions. These are ownership controls required by the ABI, not a request to read unowned implementations.

## F5 — Baseline corner cases and actual archive exclusion are insufficiently causal

Current source fixtures always use B2, fresh RND offset0, no dropped admissions, and a one-row final tail. assert_future checks production-computed future_service_counters, while native checks only conservation and optimizer count progression. There is no independent explicit comparison of emitted inherited_baseline to source C/D/U, no nonzero signed RND offset case, and no nonzero dropped baseline case. The service spy records new admissions, not actual trained minibatch content; its comment claims the minibatch consists solely of those rows without observing the training batch.

Required disposition: independently calculate and assert inherited native baselines/source counters/translated native position plus public-local clocks and deltas; cover valid signed nonzero RND optimizer offset and a genuine dropped-row baseline. Add a genuine multirow shared pending archive and witness the actual next trained batch (or an independent equivalent learned/Adam update oracle) to exclude archived rows from training. Preserve real >=2 source updates and unchanged archive/source/B after target work. Do not change accepted provider algorithms to construct these controls.

## F6 — Report refusal witness does not establish pre-allocation admission

test_allocation_refusal_is_before_publication_and_retryable asserts zero attach_gradients calls after report refusal. Candidate models, RNG owners, owned input or source-native validation could already have been allocated/performed before report and the test would still pass. The late refusal currently witnesses both final gradient attachments and an actual runtime allocation seam, which is useful but distinct.

Required disposition: witness the actual candidate factory/RNG/native preparation/input-copy boundaries and require none to occur before a refusing first report. Keep the late actual allocation failure after prior genuine native preparation, complete active owner/storage/gradient/RNG/revision equality and successful retry. Account explicitly for disposable source validation when counting attachment/preparation witnesses rather than assuming it is a target world.

## Scope and disposition

These are authored fixture/coverage repairs before production implementation. No implementation defect is asserted in nonexistent conversion code. Required parent/runner/native sampler/T26 integration remains external, as correctly stated by the suite. Existing old-maskless approved-A behavior remains with its actual owner. No capability weakening or K01 scope change is accepted. If substantive repairs cannot fit the named test1000/whole5000 ceilings, root must resolve the budget before exceeding them; do not compress away meaningful validation or add an unlisted helper.

No independent runtime was run. Root's 106 collection and 12/5 prerequisite results are explicitly attributed and do not establish repaired fixtures or causal conversion RED. The next gate is one bounded tests-only repair round, rerun genuine prerequisites, then intended missing-operation/guarantee RED, followed by independent authored re-review.

## Exact source inventory and custody

Same five whole sources only: CP901/cap1400 SHA d0e63d86e154866656db0047194048420c2a7220a2b5958de59d524cafeb8e4c; BANK1122/cap1250 SHA 5ad7ca86549c886f3dc587535ba321df5a1a6737097af38a803cea41051938cc; ICM481/cap550 SHA eb7003c15404fea5e3ce8d5779f88235b96b622b853a1c11731a300d3059c90f; RP768/cap800 SHA af8843ec1a270cfa49ec44b7ac5615d33db0d4d16b2d169d161bb4a1cd402c8c; new conversion test937/cap1000 SHA above. Actual5/4209, ceilings5000. Four production sources were inspected in the design review and the new fifth test was inspected in full here. Read-only authored patch/report are review artifacts, not additional semantic sources. Dependency facts remain supplied public contracts/capsules; no old tests/helpers/unlisted implementation reads, source/runtime/import/index/commit/subagent/branch/worktree/copy actions. Only this ignored review file is written; the design review remains immutable.
