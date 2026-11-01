# Review provenance

Final scoped source/spec review or common-candidate binding. The final binding uses tested tree `42bf1b690f523ed2bb8bf47d12f53d00ea6cb93c`, identical to qualified source release `07ce97550cf2f9dae67cb56d1d8014218c39d523`; earlier identities in the body retain their original meaning.

Original artifact `T12-checkpoint-owner-independent-review-r6.md`, SHA256 `3a4c6bed97a992122cdf8727d4cdf0c172f043305af4faeed07f7c8649454bec`, retained unchanged. This portable rendering normalizes execution paths. Runtime results are coordinator-attributed unless the body explicitly records reviewer execution.

# T12 checkpoint owner repair — independent static review R6

Verdict: **PASS for the bounded checkpoint-owner expectation repair. No confirmed P1/P2 or material gap in this repair.** This is approval of the actual assertion contract against approved history A, not a runtime PASS, release decision, full native/C07 admission or whole-BAC completion.

## Fixed identity and review boundaries

Existing MAIN `/workspace/hamlet`; HEAD `44e9d494eb94da1450b3e7a1832acea23dbbdb8e`; candidate tree `42bf1b690f523ed2bb8bf47d12f53d00ea6cb93c`; manifest `.superpowers/sdd/2026-11-01-bac-remediation-upgrades/wave06/green-r6-candidate.json`, inventory `T12-checkpoint-owner`. Index SHA256 before review: `9073140fc617a453fd958d175032dd0be975a26f1693fd60f6f7a464c7fe7140`. Read-only cached comparison to the candidate and working-tree comparison returned exit0; final checks are recorded below.

Exactly five complete sources /4975 lines were charged and read. No sixth source, fixture implementation, comparator implementation, population implementation or checkpoint utility implementation was opened. Public comparator exact-type/key/tensor semantics and prerequisite execution are accepted from root's explicit receipt, not independently established from excluded source.

| Complete source | Lines | SHA256 |
|---|---:|---|
| tests/test_townlet/integration/test_checkpointing.py |1665|c7044acb8e7f247511c80e8ab792a14040fff7eb646ee99f27bc96ab262cdf34|
| src/townlet/training/sequential_replay_buffer.py |1237|14196e7109120682476736e927076ca2dcd9926cdda206cac1ab4641189e3ea5|
| src/townlet/training/historical_checkpoint.py |666|013fe456f867bc9b5e28ab95ee9b07e5b0fa155653abfd07de3a35159c969761|
| src/townlet/demo/runner.py |1001|94842641bdce645fdd90d188d5bbdf6e09e7f4c071d15756202e173acd47c15d|
| tests/test_townlet/regressions/test_episode_lane_population.py |406|74b7245dd73b64c9aad409050c98aaa72887420e9020dfe325512efc13ddb3c1|

Read repository AGENTS/CLAUDE, remediation standing-rule prose, causal maintenance receipt R6, implementation draft and native-proof independent review R5. Applied the requesting-code-review reviewer rubric (actual source/design alignment, severity, evidence and explicit deferred judgments); using-superpowers explicitly exempts dispatched subagents. No further delegation. User preservation and approved `BAC-HISTORY-A-2026-11-01` supersede blanket delete-compat guidance. Existing project/session/tool authority governs; no durable user-only fallback is saved or adopted, a failed rule grants/restricts nothing, and specific creation approval does not fan out. Root remains sole integration owner.

## Actual-path assessment and refuted concerns

**The old active-two assertion protected current captured replay:** refuted. The actual node at checkpointing120 builds the existing recurrent architecture through `make_lane_population`, which calls the real VectorizedPopulation constructor after authored compilation (lane_population25–79). There is no replacement replay or captured-data fabrication. The revised test explicitly requires unconfigured geometry/options, exact bare5 keys, integer version5, two one-row episodes and exact eight episode fields. These are nonterminal checkpoint closures with preserved successors, not captured6 fragments. Production is unchanged by R6.

**Fresh0 is merely an implementation concession:** refuted by approved A and the inspected mechanism. SB638–641 materializes a validated bare5 state as a complete standalone archive plus empty prepared state. SB459–471 serializes that unconfigured archive-bearing state as the exact four-key inspection envelope. HC validates domain, complete original state, count, approval, reward semantics and content digest. Captured6 materialization takes a separate path restoring its active fragments; the repaired test never exercises or redefines that branch.

**Replay equality was broadly discarded:** refuted. checkpointing215–224 preserves identical top-level keys and exact recursive comparison of every non-replay field for recurrent mode, while standard mode keeps original whole-checkpoint equality. The replay-specific replacement is stronger than a count-only exception: exact four envelope keys and version1; exact empty nested5 capacity/count/episodes; exactly one six-field archive; honest standalone sequential5 domain; count2; approved reference; historical reward semantics; serialized/public digest identity; and complete source-to-record/source-to-public-archive equality. Every recorded observation, action, reward/component, done, successor and episode boundary is included in those complete payload comparisons.

**Lane completion/reset protections were removed:** refuted. Two actual saves still assert checkpoint completion reasons and unchanged `[1, 1]` survival history. Reset checks retain empty completion slots, zero population/environment step counts, nonterminal fresh environment, empty recurrent pending episode lists and zero rollout hidden state. The standard two-row/done checks remain. Runner253–312 flushes before building and writing the checkpoint; runner364–369 calls native validation/load. The node invokes that real runner path, then explicitly applies the runner's fresh-episode policy. Runner570–573 independently confirms reset at the next episode boundary. No skip or xfail was added.

**An empty replay assertion allows historical data loss or active archive sampling:** refuted. The test compares complete originals, queries all five primary row fields in original order, checks episode IDs `[0, 1]`, exports through the public archive API and loads that file for complete recursive equality. It checks both raw and qualified occupancy 0, empty episode storage/length, unqualified identity, and actual dictionary sampling refusal. HC query/export code preserves component presence and verifies exported content digests; SB's sampler sees only active episodes. Historical rows cannot satisfy this witness by silently disappearing or remaining active.

**Inspection can mutate source/destination unnoticed:** covered for the exercised successful operations. The final destination checkpoint is compared to its deep snapshot after public archive query/export and sampling refusal. Original artifact bytes and complete live source checkpoint are compared afterward. These are real owned snapshots, not aliases of mutable state. This is positive-path preservation evidence, not proof of every mutation/failure/alias scenario.

## Findings and optional strengthening

No confirmed P1/P2 in this scoped repair. No required repair recommendation.

Optional P3: the query loop at checkpointing278–281 checks primary rows and episode IDs but does not independently assert the three queried component values/presence masks. Complete archive original/export comparisons already protect their preservation, and HC's inspected query handles presence explicitly. Adding direct query-component checks would strengthen this particular public query witness; their absence does not justify blocking this bounded repair or inferring component loss.

## Behaviors considered but not closed

- Evolved optimizer/scheduler continuation and qualified recurrent learning: source uses one environment step and a large batch threshold, so exact non-replay equality covers naturally populated state but cannot establish evolved optimizer or real recurrent learning. T14/T15 remain required.
- Complete current native/C07 admission and captured6 integration: this node truthfully uses native population6 with bare sequential5; it neither admits invented native versions nor tests integrated qualified6 continuation. Full validators remain required.
- Canonical outer archive registry, nested subset/domain deduplication and single accounting: the witness checks the real standalone archive domain at replay storage, not a canonical outer union. T24/T25 remain required.
- All-failure learned-state/resource/RNG atomicity against populated targets: runner performs sequential owner loads/restores, and this positive test supplies no failure matrix. No transactional claim is made.
- Relocated second-generation native save/load with new raw rows: covered only by root-attributed earlier native-proof evidence, not this node. Two original saves here prove idempotent lane closure, not two generations of restored archive transport.
- Repository regression freedom and standing guards: runtime belongs to root, and a finite static PASS cannot establish these. Any newly caused current-consumer failure still requires repair before release.

## Runtime attribution and stationary handoff

Root reports R5 full suite `1 failed, 4899 passed, 10 skipped, 13 warnings`, failing at this recurrent old equality assertion. The separate native proof2, core69+46 and current42 PASS results are root-attributed prior evidence. At dispatch R6 owner collection was active; whole owner/recurrent suite, guards and replacement full gate remained pending. This reviewer ran no import, runtime, test, probe, lint or helper. No repaired-node GREEN is inferred.

Only this ignored prose report was written. No source/index/stage/commit mutation, git write-tree, branch/worktree/source copy/checkout, deletion or subdelegation occurred. Final post-write checks confirmed the same HEAD, all five hashes and 4975 total lines, unchanged index SHA, ignored report status, and read-only working/cached equality (exit0). Reviewer is **STATIONARY**; root owns remaining qualification/integration/release.
