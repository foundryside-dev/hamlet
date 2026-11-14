# PW04 restore B independent source review

2026-11-14. Review of the actual repaired BANK/runtime observation and correlation implementation, not a new architecture proposal. **Disposition: one P2 observation-contract defect remains; no demonstrated P1 publication/authority defect in this bounded packet.** The owner-lock race repair is source-supported. Component evidence does not close native runner or original G3/G4 obligations.

## Custody and evidence boundary

Read repository AGENTS.md and exactly these five whole implementation/test bodies, totaling **4415 lines**. No Git command, runtime/import/test execution, source edit, branch, worktree, source copy, or further delegation was performed. This report is the only authored artifact.

| Body | Lines | SHA256 read and rechecked |
| --- | ---: | --- |
| `src/townlet/exploration/scoped_curiosity.py` | 1569 | `fa3c5ce8f8e75bd242e7d2fec3d5264a75952e881a87ec21eba8c039f9219e7c` |
| `src/townlet/config/exploration_policy.py` | 1479 | `d19d8814ef619903e1987b297343655cbe80cfca020e7b3f88fff941f01b7f94` |
| `src/townlet/exploration/parent_custody.py` | 398 | `e66de4a4fae161c96c910cdd649834778836220b56b2a5227f1f269bc4e78ba8` |
| `src/townlet/environment/restore_attempt.py` | 420 | `a49770618943d1157162ea77c3b96116baa9cf401eb7aa0b5f7a3e882b6ea4ed` |
| `tests/test_townlet/regressions/bac/test_restore_installation_outcomes.py` | 549 | `e7765e5950b11a248b25d01d537cc07c9b3077935e8d6b87f55c277a4a7e0809` |

Prose inputs: local `pw04-restore-b-api.md`, `pw04-restore-attempt-c-api.md`, and wave35-wip-25 W `evidence-management/env-c2/restore-correlation/{producer-facts-v3,env-independent-design-review-v3}.md`. The B capsule's older pending-GREEN wording is superseded only by root's attributed report: R162 genuinely reproduced the race; R163 tree `34d6bace9a1ac608da2516cbf7a8475460e7b37f` passed combined B/C24 and isolated real completion-poison1 with custody PASS. I did not independently inspect execution artifacts or run those selections. These results must not be assigned to later C/native-finalizer edits or otherwise different bytes without a new custody mapping.

Core facts are supplied, not a sixth body read: the actual exited invocation's `completion_failed()` remains true until successful completion, distinguishes a body exception with successful completion, and requires authentic PID/Thread. The supplied core hash is `6cb01ca77b58db5f4c4784dc36da566c06cf68c2a7c2ce227bb780549f3344f8`.

## P2: runtime overlay guard skips first-attempt observation

`exploration_policy.py:767–781` validates `_world_restore_context` permission at line774 **before** locating the genuine install publication and calling `_begin_installation`, and before the surrounding `try/finally` at line782. Therefore an actual `install_restore` call refused by this newly added public guard leaves its genuine pending observation unchanged: `call_entered=False`, `status=pending`, although the first actual call has already occurred. The ordinary retained-custody guard regression at test193 does not exercise this earlier guard.

Concrete source-derived reproducer, not executed: retain a genuine standalone runtime preparation and its observation; acquire a genuine C runtime attempt for a fresh receiving world; during its real prepare cadence callback, call `runtime.install_restore(prepared=the_retained_handle)` and catch the overlay refusal. The overlay is already used by the enclosing prepare call, and install is not permitted in its prepare phase. The old handle remains registered, but its observation still claims pending. No fake attempt, fake outcome, or private permit mutation is needed. This is an observation contract defect even if the old handle has become stale for eventual installation: the declared result is for the first actual attempt, including pre-operation guard refusal.

Repair the order so a genuine install observation begins before every public execution/overlay guard and seals on that guard's exception, while preserving the repaired owner-lock lifetime and one-use overlay semantics. Add the genuine-overlay refusal regression with sealed/call-entered/no-operation/no-consumption/no-publication expectations, and ensure a later attempt cannot rewrite that result. This review does not propose changing admission/currentness or adding a comparator.

Safety limit: pending/in-progress is conservatively uncertain in C (`restore_attempt.py:96`), so this finding does **not** demonstrate false no-publication certification, successful installation, or a terminal-fence bypass. It does prevent unqualified acceptance of the advertised all-guard first-attempt outcome contract.

## Source-supported properties

- BANK `_serialized` now installs/restores `_installation_active` inside `_bank_call` exclusion. Runtime does the equivalent inside `_runtime_call`, and incorporates the actual BANK outcome plus runtime handle disposition before exclusion ends. Only local sealing/normal-return bookkeeping remains outside. A later completed call cannot reinstall an earlier active pointer through that suffix. The deterministic test322 exercises actual BANK calls and a subsequent legitimate lookup; R162 RED/R163 GREEN is attributed above.
- BANK marks consumption immediately after the actual token pop, uncertain publication before dictionary assignment, and complete after assignment returns. Execution facts live in slots outside the restorable dictionary. Actual invocation completion is independently recorded in `_admission`, first uncertified and then from `completion_failed()`. A body refusal can therefore truthfully be consumed/no-publication/completion-succeeded. Publication failure does not falsely erase native failure flags.
- Runtime incorporates BANK's result rather than guessing from the exception. Its selector/cadence/revision/empty-handle suffix is marked uncertain before assignments and complete after all return. Suffix failure after actual BANK success remains partial/uncertain; there is no rollback, new currentness check, exporter or extra native invocation after publication.
- `_begin_installation` only changes a pending cell; sealed outcomes survive lawful unconsumed standalone retries unchanged. Frozen preallocated result variants separate observation from authority. Outcome lookup is owner-local and contains no RNG admission; read is issuer/PID/Thread authenticated and remains available after consumption or poison. Weak registry values contain a weak owner and handle ID, not their outcome/handle keys; ordinary preparation ownership may intentionally retain a live observation.
- Genuine runtime correlation authenticates C's registered lexical attempt and selected child/stage/unbound ENV scope, holds the runtime exclusion, permits one selected call and expires on every exit. Prepared runtime publications retain their exact attempt identity. `_correlate_cadence` brackets the original bound comparator with actual public pure checks and retains return/view/revision checks. Current tests use real compiled ENV/runtime/BANK/POP and genuine POP cadence validation, with four BANK plus three cadence comparisons and fourteen checks for shared/per-world INITIAL composition. The stale callback swallowing its own refusal is still caught by the mandatory outer check.
- Revisions and actual current tokens remain authoritative: the observer path neither refreshes tokens nor promises success after unrelated retirement or no-draw operations. The real intervening-operation regression219 is an appropriate negative control.

## Remaining bounded evidence gaps

1. The new P2 overlay-guard path needs real RED/GREEN verification. The current repaired race control exercises BANK, not a separately scheduled runtime concurrency interleaving or concurrent same-handle calls. Runtime source exclusion is persuasive, but those execution claims are not established by test322 alone.
2. Runtime suffix fault coverage currently injects at `_state` before assignment. It does not individually demonstrate faults after `_state`, at/after `_revision`, or at/after empty-handle assignment. BANK dictionary before/after cases are covered. The runtime implementation conservatively marks the entire suffix uncertain, but the full cut matrix remains evidence owed.
3. The isolated actual completion-poison test is direct BANK. Runtime propagation through an actual BANK completion failure is source-supported but not separately exercised in this owned test. Outcome lifetime control covers a consumed BANK observation and foreign-thread read; it does not separately establish runtime abandoned/prepared lifetime, serialization/fork identity, or every published lifetime promise.
4. The owned composed controls are INITIAL component composition. They do not establish COMPLETED, reorder/private initialization, manual/direct-BANK continuation, native all-owner artifacts, original ledger negatives, resumed learning, or original18 G3/G4 closure. Their local component finalizer is explicitly not the real full runner continuation. Those remain their respective source-owner/runner obligations, not grounds to relabel component tests as native proof.

The repaired owner-lock race and actual recorded publication/completion cuts can be retained. Resolve the finite P2 guard omission and qualify the remaining declared cuts against exact candidate bytes; no broader design restart is indicated. PW04/native runner acceptance remains open.

## R165 fixed-source follow-up (GREEN pending)

2026-11-14. Append-only follow-up preserves the original finding and evidence limits above. Root reports R164 reproduced the intended P2 assertion: the observation remained pending rather than sealed after the actual overlay refusal; source custody PASS. This is attributed execution evidence, not a test run by this reviewer. R165 GREEN has not been supplied at this review cut.

The same five-body inventory now totals **4484 lines**. Rechecked exact current hashes after root formatting:

| Body | Lines | R165 reviewed SHA256 |
| --- | ---: | --- |
| `exploration/scoped_curiosity.py` | 1569 | `fa3c5ce8f8e75bd242e7d2fec3d5264a75952e881a87ec21eba8c039f9219e7c` |
| `config/exploration_policy.py` | 1481 | `1b511bd1a8faae1e702dd5398ddb9a81bc655c266de9a56772caa63a5d019ccc` |
| `exploration/parent_custody.py` | 398 | `e66de4a4fae161c96c910cdd649834778836220b56b2a5227f1f269bc4e78ba8` |
| `environment/restore_attempt.py` | 420 | `a49770618943d1157162ea77c3b96116baa9cf401eb7aa0b5f7a3e882b6ea4ed` |
| `test_restore_installation_outcomes.py` | 616 | `ef9bde3d93b707a0184e3e5ff7dd20e31d8eeefa2618e7d5377da803a73a92be` |

**P2 source disposition: addressed, execution qualification pending.** Runtime now begins the genuine registered install observation under its existing local lock before checking the overlay permission; both steps are inside the existing `try/finally`. An overlay refusal therefore seals a truthful first-attempt no-operation/no-publication result. This early bookkeeping does not install `_installation_active`, enter a domain/native operation, consume a native/runtime handle, or change overlay permission on refusal. The active pointer and actual BANK-result capture remain inside `_runtime_call` owner exclusion, preserving the previous race repair.

The new `test_runtime_prepare_overlay_refusal_seals_first_install_attempt` uses the described genuine standalone handle, cached pending observation, real C attempt and real POP cadence comparator. It asserts every requested first-result field after the exact overlay refusal, continues the genuine C child/world/finalizer sequence, checks the same immutable result through later cadence callbacks, and checks identity again after a later refused old-handle call. It neither fabricates an outcome nor replaces the real cadence comparison. Thus its assertions address the reported defect and preserve successful component composition; no execution PASS is inferred merely from reading them.

No additional P1/P2 defect found in this narrow correction. Remaining runtime concurrency/suffix/poison/lifetime cut coverage and native consumer/full-runner obligations above remain open. R163 successes still refer only to their recorded candidate; R164 RED and forthcoming R165 outcomes must retain their own exact custody. No Git/runtime/test command or source edit was performed in this follow-up.
