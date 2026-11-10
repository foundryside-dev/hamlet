# PW07 existing owner-suite coherence: readonly preparation

Status: ready for root's separate tests-only baton if a concrete production API incompatibility appears. No existing test/source changes are required by the approved schema replacement on the inspected evidence. This is static preparation, not collection, execution, component approval or release evidence.

Authority: PW07-owner-fixture-brief.md, original task, main brief including governing zero-backwards-compatibility clarification, approved ABI proposal and design review; root's subsequent direction explicitly preserves the suites unchanged unless a concrete behavioral coverage gap requires an assertion. Initial authority permits only this ignored report. Root retains source/integration/runtime/index/publication ownership. Another sole new-test writer remains active.

## Actual fixture finding

Both existing suites construct actual CuriosityBank objects and obtain their BANK/diagnostic data from the current checkpoint_state/snapshot_world emitters. Neither suite authors a BANK envelope, contains a curiosity-bank-state-v1 or curiosity-bank-world-v1 literal, asserts an exact BANK/diagnostic key set, or hardcodes a curiosity_epoch assertion/event constructor. Their unrelated compiled_schema_version 1.42 and world-roster-v1 literals are genuine other contracts and must remain unchanged.

Consequently replacing the producer's BANK envelope with v2 and adding initialization_origin=None to regular shared/private state does not require rewriting an existing fixture. The world-v2 metadata additions also do not require modifying existing diagnostic consumers. Typed whole-tree equality compares both current emitter outputs and retains all their keys, so new None-origin/future-counter fields remain visible to existing invariance and ownership controls automatically. This conclusion is narrower than a runtime success claim.

Concrete source anchors (pre-change line numbers):

- private-bank _native:127 selects only the existing private/shared backend nesting; no version check or normalization. _equal:47 checks exact types/keys and all values. _private_domain:919 preserves every world-local field, normalizing only explicitly allowed descriptor/accepted binding/global-tick provenance; it does not whitelist/drop new fields. Its regular origin=None and world-local future counters can stay in the comparison unchanged.
- private-bank test_initial_snapshot_has_no_fabricated_event:472 checks ordinary INITIAL identity/cache/pending/cursor semantics, all still required unchanged. No converted epoch/history expectations belong here.
- scope-restore Rig.train:322 consumes existing native backend nesting; no BANK version dependency. same:112 and independent:145 preserve all mapping fields/tensor custody. prepare:452 retains the existing exact explicit same-scope API and must not call the new conversion operation.
- scope-restore test_initial_and_live_scope_roundtrip:905 gets both INITIAL and live envelopes from the current emitter, preserving complete ordinary-origin state through restore and next-update replay. test_private_restore_matches_by_world_id:719 preserves real completed authority, original completion data and receiving-order permutations. Neither requires converting ordinary epoch0 to epoch1.
- scope-restore Correlation:404 reads real completion/world/cursor fields; no origin/key-set/schema version assumption. The new regular None origin does not change this same-scope correlation.
- scope-restore current HC test:1383 transports the emitter's complete BANK object under an expressly test-owned key and requires exact independent equality. No HC/provider/replay implementation or fixture read was needed or performed.

## Finite disposition and preserved refusal controls

Required migration edits identified: ZERO. Required ordinary epoch expectation changes: ZERO. Required provider/native schema changes in these tests: ZERO. No fallback/old-native acceptance is requested.

Do not add literal version/key equality checks solely to mirror the new emitter. Such change detectors would not demonstrate a missing behavior. Optional assertion ideas from initial inspection are withdrawn under root's explicit direction; the genuine fresh/clone/epoch/archive behavior belongs to the new PW07 conversion tests. Their source is outside this inventory and was not read.

Preserve every existing function name, decorator, parameter value/ID, positive learning assertion and negative control. In particular retain:

- all 55 INVALID_CASES nodes: 10 metadata defects; 15 trainable RNG/model/moment/queue/gradient-NaN defects; 12 trainable model-dtype/Adam-integral-alias/Adam-step/moment-dtype defects; 7 RND gradient-shape/custody/profile/target defects; 7 EPS/gradient-extra defects; 4 Count/LRU/key-width/gradient-extra defects;
- exact unchanged-state/revision/ambient-RNG assertions followed by healthy restore/retry, independent installed actual Parameter/gradient/Adam/storage witnesses, live dedup and next genuine updates;
- foreign/copied/consumed/stale restore handles, caller mutation custody, allocation-report/last-owner/cache/receipt/outcome refusal and real earlier native preparation;
- copied real ENV token rejection, completed parent mismatch and late callback refusal, historical closure non-authority, quarantine and pending-completion purity, batch0, escaped retained callback custody, active captured replay and private counters;
- all private-bank action/width/dtype/tick/eligibility/token preflight, stale/content/mode/retry, malformed completion and post-provider quarantine controls.

The existing tests do not explicitly author an obsolete BANK-v1 envelope or a missing-initialization_origin envelope. Do not mislabel the 55 existing malformed native/metadata controls as literal schema-version tests. A concrete absent obsolete-schema refusal guarantee, if not independently covered by the new PW07 suite, is for root to resolve from actual producer/test evidence; it is not a stale fixture requiring repair, and no speculative patch was authored here.

Production compatibility caveats to inspect only after root supplies current API facts: retained backend nesting and old same-scope prepare_restore signature; regular origin=None/epoch0 and unchanged INITIAL/live/completed phase semantics; genuinely world-local future counters under ordinary private state. A failure in those guarantees is a source/API issue unless actual changed supported contract establishes otherwise. Do not drop new fields from whole-tree comparisons or normalize counters to make a failing source pass. Shared diagnostic future-counter semantics were not needed for any fixture and are not guessed.

## Static identity/node inventory

| Existing owner suite | Test function identities | Parametrized node count |
| --- | ---: | ---: |
| test_pw_private_bank.py | 35 | 84 |
| test_pw_scope_restore.py | 22 | 147 |
| Total | 57 | 231 |

Counts come from inspection of the current explicit decorators/constants and historical contract attribution, not pytest collection. Scope-restore expanded counts in source order: 10,3,1,1,5,55,10,25,3,3,6,5,1,2,6,1,2,2,1,1,2,2 =147. No node identities would change under the zero-edit disposition.

## Exact whole-source inspection inventory

All THREE named sources were read in full, without opening any fourth implementation/test/helper source. Current counts were checked after inspection.

| Source | Lines / ceiling | SHA256 |
| --- | ---: | --- |
| src/townlet/exploration/scoped_curiosity.py | 1122/1250 | 5ad7ca86549c886f3dc587535ba321df5a1a6737097af38a803cea41051938cc |
| tests/test_townlet/regressions/bac/test_pw_private_bank.py | 1348/1475 | 45cc06aa000158c4b1c26f3000bca7a2fcc87477e961e64b87039f6383ec9b73 |
| tests/test_townlet/regressions/bac/test_pw_scope_restore.py | 1498/1575 | d1036d44536bafb2f8fa85b6226cb76cc6be655dd44c4c91346287ee343a776c |

Current whole sources3/3968; named ceilings4300. Read governing prose plus the current public BANK/checkpoint contracts in wave28; source-verified dependency capsules were not needed. No CP/WS/ICM/RP/provider/helper/new-conversion-test implementation, git-source/introspection or copied hidden extra source was read. No runtime/import/compile/pytest/index/commit/push/subagents/branches/worktrees/repository/source copies/install/delete/external messages. Sole write: this ignored report, whose exact path was confirmed by git check-ignore before writing.

No blocker to preserving the existing suites unchanged. Await root's separate tests-only baton and concrete changed API facts if an actual fixture incompatibility arises. Parent/runner/current replay/sampler/T26, independent review and full acceptance gates remain required and unclaimed.
