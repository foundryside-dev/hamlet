# Independent Astra review: truthful episode lanes

**Verdict: CHANGES_REQUESTED.** One concrete blocking defect in the proposed database preflight; two bounded execution/acceptance warnings. The environment/population/learning design is otherwise supported by the source inspected. This verdict evaluates the plan, not an implemented candidate.

## Reviewed identity and scope

- Repository: `/home/john/hamlet`, branch `fix/episode-lane-accounting`.
- Clean HEAD: `15774ed9fe68d38d02271fd46af8e6e36542ee8b`.
- Complete plan reviewed: `docs/plans/2026-10-02-truthful-episode-lanes.md`, all 1,162 lines.
- Plan SHA256: `e490ce761885cc1bb3b0d35a27f06ef2ddc518ba7f0ae932065ba95dd1fc10af`.
- Contract: `docs/product/prds/0005-truthful-episode-lanes.md` and `docs/product/decisions/0158-episode-lane-plan-and-boundary-semantics.md`.
- Independently checked that `src`, `tests`, `configs`, `scripts`, `pyproject.toml`, and `uv.lock` have no changes between the plan's `ec463fdaaa632e4e1f778b938ace94f53a73a745` source anchor and reviewed HEAD.
- Read repository AGENTS/CLAUDE instructions, SME protocol, plan-review skill, Loomweave workflow, and relevant RL guidance. Used the requested single comprehensive reviewer rather than nested reviewers. Prior approvals were not treated as evidence.
- Root verified Loomweave freshness at this HEAD before structural queries. Caller navigation used returned SEIs, including population stepping `loomweave:eid:ce75c872f482759f19ae29f7f79ff8c3`, reset `loomweave:eid:112ae46fbc999924c5a7282d75d84bda`, and checkpoint flush `loomweave:eid:4535d33f14734e2261ed644469421360`. Unresolved receiver sites were disclosed by the tools and inspected where relevant.

## Severity-ranked findings

### B1 — Medium, blocking: the specified read-only schema probe creates historical-artifact sidecars

**Plan anchors:** S1 lines 632–647 requires old-layout refusal before mutation and explicitly forbids creating sidecar files. The concrete implementation at lines 1018–1022 opens `sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)` and reads `PRAGMA user_version`; line 1040 says to run this gate before opening the write/WAL connection.

**Source anchor:** `src/townlet/demo/database.py:26–28` creates ordinary existing databases in WAL mode. A cleanly closed historical database therefore remains a WAL-mode database even when its `-wal` and `-shm` companions are absent.

**Executed evidence:** On the primary interpreter, Python 3.13.15 and SQLite 3.53.1, I created a disposable old unversioned WAL-mode database with one episode, committed and closed it, then executed the exact proposed read-only connection and version query. The directory changed as follows:

```text
before: ['old.db']
PRAGMA user_version: 0
during probe: ['old.db', 'old.db-shm', 'old.db-wal']
after connection.close(): ['old.db', 'old.db-shm', 'old.db-wal']
```

This contradicts a specified GREEN invariant. It is not a hypothetical concurrency concern or a claim that episode rows were changed. The root independently reproduced the same result and verified unchanged main-database bytes.

**Required plan fix:** Replace or qualify this implementation fragment with a preflight that actually satisfies the no-sidecar/no-mutation contract. At minimum, known old unversioned layouts can be rejected from a nonmutating header check before SQLite opens them; the remaining current-layout validation must also define safe handling of WAL state. Do not blindly substitute `immutable=1` for a live database and silently ignore committed WAL content. Add refusal cases for a closed WAL-mode old database with no companions, and malformed current-stamp WAL databases; compare the entire artifact family before/after, not just main-file bytes/schema/rows. Retain the existing strict refusal, no migration and no deletion policy.

### W1 — High execution risk, nonblocking plan warning: the excluded recorder dependency is now reproduced

**Plan anchors:** lines 39 and 759–763 already correctly require retained failure and a PDR scope amendment if ordinary recorder shutdown loses the acceptance artifact. S3 lines 725–733 requires the ordinary persisted artifact and observer path.

**Source anchors:** `src/townlet/recording/recorder.py:145–160` enqueues the end marker and immediately stops the writer during shutdown; `:199–220` runs only while `self.running`; `:305–307` sets that flag false. `src/townlet/demo/runner.py:206–217` shuts down the recorder before closing its database.

**Executed evidence:** Five disposable probes used the real `EpisodeRecorder`, its real writer thread, two ordinary `record_step` calls, `finish_episode`, and immediate ordinary `shutdown`. No sleeps, polling wrapper or substituted writer were used. Four of five runs produced no artifact; their stopped writers left respectively 1, 2, 1 and 2 queued entries. One run persisted successfully. These probes disabled database indexing (`database=None`) and are evidence of the recorder queue lifecycle, not a complete DemoRunner persistence acceptance test.

**Recommendation:** Bring the ordinary runner shutdown witness forward into the prerequisite stage. The plan's explicit stop/amendment rule remains appropriate, but this is now an evidenced likely prerequisite, not merely an uncertainty to discover after completing S1/S2. Do not treat one lucky persistence run as durability qualification, and do not repair the excluded lifecycle without the stated scope amendment.

### W2 — Medium acceptance warning: specify reward reconciliation for the ordinary recording-to-observer path

**Plan anchors:** S2 lines 690–710 and the concrete accumulation at 1064–1075 switch episode totals to canonical composed DAC contributors. S3 lines 725–750 tests eligible frame count, completion reason and ordinary playback, but does not expressly reconcile frame reward values or the observer's cumulative reward with that ledger.

**Source anchors:** `src/townlet/demo/runner.py:679–680` records `extrinsic_only` plus predecessor raw RND logging novelty; `src/townlet/recording/data_structures.py:63–64` labels those fields extrinsic and RND novelty. `src/townlet/demo/live_inference.py:1143` publishes `step_data['reward'] * step_data['step']` as cumulative reward. The existing multi-agent TensorBoard wrapper at `src/townlet/training/tensorboard_logger.py:143–155` also does not forward its available `shaping_reward` argument.

The new episode-level canonical intrinsic value is already weighted/modulated, whereas recorded step novelty currently is not. An ordinary playback test that only checks completion reason can still pass while displaying a different cumulative reward. In the retained two-episode planning artifact, metadata total is approximately `0.51717156`, while the existing final observer formula would publish approximately `-15.29489040`. That old number includes the known phantom frames, but the multiplication formula remains wrong after row filtering: a zero-reward terminal frame still publishes zero cumulative reward after an earlier positive reward.

**Recommendation:** State the format-2 per-frame reward semantics explicitly and identify the exact producer/projection updates needed to reconcile them. Add a non-vacuous fixture with a positive earlier reward, zero-reward terminal row, and nonzero intrinsic modifier/shaping contribution; assert persisted step components/totals, episode metadata, relevant TensorBoard components, and emitted observer cumulative total against the same eligible prefix ledger. This is a bounded accounting projection concern, not a request for browser UX or general playback redesign. I have not made it a second blocker because the plan's broad canonical-consumer requirement can accommodate those caller updates; the detailed acceptance steps should make them explicit.

## Checks that support the proposed core design

- **Authored instrument feasibility independently executed:** copied `configs/test/model_config` to a disposable directory, appended precisely the proposed END_LANE declaration, enabled it in `L0_test`, compiled with `use_cache=False`, and constructed a real two-agent `VectorizedPopulation` from the compiled feedforward brain with adaptive exploration. Real forwards plus the specified exploration-selection schedule yielded initial energy `[1,1]`, terminal events only at 2/5, independent counts `[2,5]`, and five world ticks. Current source published `[5,5]`, admitted ten replay rows and produced adaptive history `[2,1,1,1,5]`; Q updates were zero at batch size 128. This verifies the compact proposed fixture's construction and parent defect, not a repair.
- **Eligible terminal rows:** the proposed entry mask correctly includes the terminal transition; the current bug locations are `vectorized_env.py:1174–1199` and `population/vectorized.py:803–835,1069–1082`. New mask fields and completion dataclasses are deliberate creations, not nonexistent-API mistakes.
- **Actual learner nonvacuity:** recurrent warmup checks at `population/vectorized.py:840–855` precede completion/storage at `:1075–1082`, supporting the plan's ninth-batch requirement. Existing recurrent bootstrap consumes the stored successor at `:865–917`; feedforward targets use stored successors at `:994–1004`. The plan expressly requires observed terminal and truncation boundary categories and actual loss targets, so it does not substitute admission counts for learning evidence.
- **RND:** current normalization updates occur in `rnd.py:196–205`; predictor training consumes actual buffered rows at `:240–257`. Separate predecessor/predictor and successor/normalization ledgers, seven-row and 63-row witnesses, and actual predictor hooks match these seams.
- **Once-only completion/reset:** P1 moves lifecycle ownership into population, clones CPU outcomes and recurrent data, preserves completed counts until reset, and refuses a pending reset before mutation. It updates flush callers atomically. Current runner has one batch curriculum route at `runner.py:700–711`; retaining it avoids duplicate death completion.
- **Recurrent curriculum interface:** preserving full Q rows and restoring inactive hidden rows addresses the actual adversarial call path at `population/vectorized.py:731–770`; the plan also requires a non-static curriculum witness instead of assuming zero placeholders harmless.
- **Checkpoint hard cut:** nested state validation precedes mutation in `runner.py:345–364` and `live_inference.py:458–470`. A population format bump with valid outer identity tests is an executable way to reject obsolete learned state while preserving fresh-episode resume and avoiding migrations.
- **Attribution:** E0's clean parent capture, E1's preregistered exact coordinates and negative controls, direct-parent isolated imports, and controlled pinned-oracle supplementation address the standing trace format's blind spots. `check_epistemic_access.py:81–120,402–468` indeed refuses output/reset changes rather than accepting broad hash allowances. The plan preserves that distinction and does not authorize oracle re-freezing.
- **Gates/order:** E0 before execution-bearing edits, the environment/population tracer before sink work, the atomic schema/metadata constructor cut, scoped task gates, and one final unfiltered suite are coherent. Current pytest addopts contain coverage but no slow-test exclusion, so F's literal unfiltered command matches its stated intent. No new full suite or learning acceptance was run during this review.

## Confidence Assessment

**Overall confidence: High for B1 and the bounded source/probe findings; Moderate for completeness of future implementation acceptance.**

| Finding | Confidence | Basis |
| --- | --- | --- |
| B1 sidecar creation | High | Executed exact proposed SQLite opening/query on a normal closed WAL artifact; independently reproduced by root |
| W1 recorder loss | High | Four observed failures in five real writer-thread shutdown probes, matching the loop/stop source |
| W2 reward projection gap | High for current behavior; Moderate for future omission | Current source and retained artifact values directly verified; a future implementation could satisfy the broad contract by updating these callers |
| Compact authored fixture feasibility | High | Real compiler, compiled brain and population probe at reviewed source |
| Learner/bootstrap/checkpoint plan feasibility | High statically | Read actual update ordering, target formulas and pre-mutation gates; no repaired candidate exists |

## Risk Assessment

**Implementation risk: High. Reversibility: Moderate.** Source edits are reversible, but the package deliberately changes learned/persisted artifact contracts and spans several asynchronous consumers.

| Risk | Severity | Likelihood | Mitigation |
| --- | --- | --- | --- |
| Historical artifact family changed on intended refusal | Medium | High with proposed SQLite fragment | Fix B1 and assert complete directory/file-family preservation |
| Missing ordinary recording acceptance artifact | High | Demonstrated, scheduling-dependent | Execute early ordinary runner witness; follow explicit PDR dependency process |
| Truthful metadata alongside misleading reward projection | Medium | High if current projection retained | Explicit per-frame semantics and prefix-ledger consumer assertions |
| False confidence from seven admissions or only long recurrent windows | High | Addressed by plan | Retain actual losses/gradients, seq1 and seq2, terminal/truncation nonempty assertions |
| Broad oracle allowance hides unrelated changes | High | Addressed by plan | Preserve preregistration, isolated parent/oracle captures and corrupted-coordinate controls |

## Information Gaps

1. There is no implemented candidate: no proposed GREEN result, full-suite result, ordinary runner persistence success, exact after-seam attribution or independent PRD acceptance can be claimed.
2. The recorder probes isolated the real queue/writer lifecycle; they did not instantiate the full ordinary runner, SQLite indexing and observer. That exact test remains necessary.
3. The detailed recording task does not yet specify a complete per-frame canonical reward/projection contract. Its acceptance needs the bounded clarification in W2.
4. Full CUDA behavior and asynchronous production stress were not executed. No corresponding claim is made.

## Caveats and Required Follow-ups

Before relying on this plan for execution, resolve B1 in the plan and demonstrate its proposed preflight with the WAL refusal controls. Preserve the demonstrated recorder failure and follow the existing scope-amendment condition rather than bypassing it. Make W2's consumer reconciliation explicit when forming format 2.

The remaining proposed behavior must still pass the plan's actual learner/predictor, target, reset, sink, exact attribution and unfiltered-suite gates on one identified candidate. The review does not authorize or establish implementation, product acceptance, merge, push, hosted CI, recovery exit or convergence.

All probes used the primary environment, disposable `/tmp` directories, and read-only inspection of retained planning evidence. No repository, tracker, Git, memory or historical artifact was edited. Disposable probe directories were removed; this report is the sole retained review file. Repository cleanliness, HEAD and plan hash were checked again at completion.
