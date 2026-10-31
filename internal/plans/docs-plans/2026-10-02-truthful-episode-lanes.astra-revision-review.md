# Independent Astra re-review: truthful episode lanes

**Verdict: APPROVED_WITH_WARNINGS.** The demonstrated database-preflight blocker is resolved. The recorder prerequisite and canonical recording/observer acceptance omissions are now explicitly addressed. I found no new blocking contradiction in the complete revised plan. Approval is for this implementation plan, with its stop/amendment gates, not for runtime correctness or product acceptance.

## Reviewed identity and scope

- Worktree: `/home/john/hamlet/.worktrees/episode-lane-plan`.
- Complete plan: `docs/plans/2026-10-02-truthful-episode-lanes.md`, all 1,576 lines.
- Exact SHA256: `159ab22fc58bb43a5c2e9756c5bfbc9546f10ecb1d5a42145a357b104acb1b6c`, independently rechecked after reading.
- Revision parent: `86857eb0e0730c113cbf27f21bd97a308095079b`. Runtime, tests, configs, scripts and dependency manifests remain unchanged from source anchor `ec463fdaaa632e4e1f778b938ace94f53a73a745`; this is a documentation revision in progress, not a clean implementation candidate.
- Reviewed the complete plan against PRD-0005, PDR-0158 and revised PDR-0159, the original retained `.astra-review.md`/`.json`, and the revision evidence receipt and byte archives. Repository instructions, SME protocol and plan-review criteria govern this single requested independent review. No nested reviewers were used.
- Root verified fresh primary Loomweave index at revision parent, completed run `4536021e`. Structural navigation used returned SEIs, including `DemoDatabase` (`loomweave:eid:2d36b618e6352b859e14e10037aaad88`), `LiveInferenceServer` (`loomweave:eid:20fcca2b7b5c8d1c06d6f9fd2d8cdeda`), and the actual export callers. Source reads and executed probes, not earlier approvals, ground the conclusions.
- All plan line references below refer to the exact reviewed bytes. Source references are relative to `/home/john/hamlet` and apply to the unchanged runtime source in this revision.

## Resolved findings

### B1 — Resolved, high confidence: original-family preservation on schema refusal

The previous fragment opened the original WAL-mode file through SQLite even with `mode=ro`, creating sidecars. The replacement at plan lines 723–734 and 1184–1300 never asks SQLite to open the original during preflight. It uses raw regular-file reads for header/family identity, refuses every existing `-wal`, `-shm` or `-journal`, and validates a companion-free current file on a disposable private copy. Full `table_xinfo` checks cover types, defaults, nullability, primary keys and hidden columns; a version stamp alone does not qualify a database.

The contract explicitly excludes live owners and interrupted-run recovery, requires exclusive caller custody through actual reopen, states that a Boolean assertion is not a lock, and states that fingerprints do not establish an atomic live snapshot. Valid committed WAL is refused and preserved, not silently ignored. PDR-0159 lines 25–32 records this deliberate scope choice. These limits make the mechanism internally coherent; they must remain visible at its callers.

I independently executed the archived 22-control probe against the archived exact proposal and the current primary source. All controls passed: 20 original families remained unchanged, and two externally injected mutations were refused with only the injected changes present. The probe includes closed WAL-mode old and malformed/current databases, committed-WAL cases, malformed schema cases and custody refusal. It also demonstrates that committed WAL contains data missing from a main-only copy, supporting the explicit refusal rule. This resolves the original demonstrated failure; it does not qualify live database opening or recovery.

### W1 — Planning omission resolved; high execution risk remains explicitly gated

Plan E0a, lines 89–138, now precedes E1 and substantial runtime work. It requires ten independently initialized real DemoRunner → recorder → database index/file attempts, ordinary immediate cleanup, stopped writer and no outstanding accepted entries. It forbids sleeps, polling, alternate writers and accepting a lucky attempt. A failure must be retained as RED and block E1 until a separately scoped PDR admits and verifies the demonstrated prerequisite. Passing ten attempts does not itself establish scheduler-independent durability.

This addresses the original warning without pretending the current recorder is repaired. Current `recording/recorder.py:145–160,199–220,305–307` still contains the immediate writer-stop ordering; the original five real-thread probes lost four artifacts but did not exercise database indexing. E0a supplies the missing ordinary-runner evidence. No full E0a execution or recorder repair is claimed by this re-review.

### W2 — Resolved, high confidence in the specified acceptance contract

Plan lines 670–684, 749–770 and 1325–1472 now define and atomically introduce format-2 frame canonical total plus required extrinsic, effective intrinsic and shaping contributors. Metadata and both database tables retain all components. S1 also owns the thin runner entry gate and masked component accumulators, so its strict reader need not await S2 to avoid recording five rows for a lane surviving two steps. All constructor/signature/success-fixture changes must land before S1 GREEN (lines 919–936).

The old source defects have concrete owners: `demo/runner.py:679–680` currently writes extrinsic/raw novelty, `demo/live_inference.py:1143` multiplies reward by step, and `training/tensorboard_logger.py:143–155` omits shaping forwarding. The plan replaces them with canonical frame fields, an inclusive selected-index prefix, and explicit shaping forwarding/tag emission even at zero (lines 835–842). The numeric tolerance is bounded to reward rounding; flags, counts, indices and reasons remain exact.

S3 lines 861–897 requires the same ordinary persisted artifact through real ReplayManager and actual LiveInferenceServer handlers/broadcast JSON, reconciled against an independently captured eligible DAC ledger. Non-unit intrinsic modulation, nonzero effective intrinsic/shaping, an earlier positive total and zero death-terminal total are required observations. Forward playback, repeated send, backward seek, reset and episode replacement prevent a message-history accumulator from passing. This is materially stronger than a synthetic serializer or final-total-only test.

## Residual warnings and execution gates

### R1 — High execution risk: retain the recorder stop/amendment boundary

**Confidence: high.** E0a can expose a real prerequisite before episode implementation starts. Its existing-source defect remains and no planning result closes it. Follow plan lines 125–138 and 937–942 literally: retain ordinary failing evidence, establish the bounded prerequisite scope, verify the lifecycle repair deterministically, then resume. Do not infer durability from the successful private-copy database probes or numeric fragment. No additional blocking plan revision is required because the revised dependency ordering already handles this condition.

### R2 — Medium execution gate, planning follow-up resolved: sequential export custody

**Confidence: high for source feasibility; no revised runtime export run exists.** Current `src/townlet/recording/video_export.py:219–225` retains a query `DemoDatabase` while calling `export_episode_video` at lines 236–247, which opens the same database again at line 53. This conflicts with the new stopped-owner precondition. The final localized revision at plan lines 735–748 expressly fixes that caller: materialize the list and close its owner before the batch loop; close each child's database in `finally` after real `ReplayManager.load_episode`, including failure/exception paths. Both source and test changes are atomic S1 work, with real two-recording sequential reopen and cleanup controls and the exact S1 file/gate list at lines 1520–1546.

This is source-supported: `recording/replay.py:53–88` performs the database lookup and materializes the recording, while subsequent metadata/frame/seek operations at lines 90–183 use in-memory state. `DemoDatabase.close` and context management exist at `database.py:388–405`. Closing after load does not require a replay redesign or live-WAL exception. The original static conflict is therefore covered by a concrete executable plan change, not left as a generic caller sweep.

Retain this required conformance gate during implementation; do not pass `exclusive_custody=True` merely to bypass an active owner. If another required caller genuinely needs concurrency, invoke plan lines 725–734 and 1186's explicit stop/amendment rule. I checked the apparent unified-runner counterexample: `UnifiedServer._run_inference` at `demo/unified_server.py:389–396` does not pass replay database/recording paths, so it does not itself create the competing replay owner. Completed-artifact replay must still close the producer before the observer opens the database.

## Complete-plan assessment beyond the three original findings

- The environment entry mask, newly terminated/retired event masks, death precedence and once-only retirement contribution remain coherent. New masks and frozen completion structures are intentional creations, not hallucinated existing interfaces.
- P1 specifies cloning completion snapshots, inactive recurrent-row preservation, full-shaped Q interfaces, eligible replay/RND admission, reset refusal before mutation and once-only completion. Caller cap, budget, shutdown and checkpoint flushing have explicit termination/truncation semantics and ownership. The existing single batch curriculum route remains the owner of curriculum publication.
- P2 lines 557–595 continues to require actual learner updates and observed nonempty terminal/truncation target categories. Nine two-agent episodes account for the current recurrent warmup ordering. Sequence lengths one and two cover different ghost/boundary cases; genuine replay sampling and target-input hooks prevent fabricated batches or reset successors from qualifying. Seven-row ingestion and 63-row cumulative witnesses remain distinct from optimizer sampling reuse.
- P3 lines 604–637 preserves the nested checkpoint hard cut, valid outer-identity refusal tests before mutation, fresh-episode resume and explicit clock units. No compatibility path or migration is introduced.
- The S1 atomic DTO/DDL/producer ownership avoids the newly expanded required fields becoming a temporary broken intermediate contract. S2 then qualifies the remaining counters and real logging sinks; S3 qualifies actual persistence and observer semantics. The plan does not permit fake placeholder components between those tasks.
- E0/E1/E4/F retain exact parent identity, preregistered acceptance coordinates, isolated parent imports, independent eligible ledgers, negative controls and bounded pinned-oracle supplementation. Historical artifacts remain historical. Neither the plan probe nor preserved parent failures can substitute for candidate acceptance.
- The surface area remains substantial, spanning environment, population, recording, database, observer and logging. The named task gates are credible staging boundaries, but the revision provides no basis to forecast completion by the product review date. No convergence or learning-performance claim follows from accounting acceptance.

## Independently executed validation

1. Re-ran the retained preflight harness from the revision worktree using the primary interpreter:

   ```text
   /home/john/hamlet/.venv/bin/python -B -P docs/product/evidence/episode-lanes/planning/astra-revision/probe.py.txt --proposal docs/product/evidence/episode-lanes/planning/astra-revision/preflight.py.txt --source /home/john/hamlet/src/townlet/demo/database.py
   ```

   Result: 22 controls passed; 20 unchanged families; two injected-only change refusals. Python 3.13.15; SQLite 3.53.1. Proposal SHA256 `0640b8073ac9b9c60c5d6fa43a370b56db830ac84ff9f9def8955824a1d54406`; harness SHA256 `8585884478697a532febcaf01a0fbc3937997717f5cacf417a0368bcb8126d54`; current database source SHA256 `945ea042fdacc9b265ce6a2e4b4d62fd9b876c816c6a00dd29df94d99d2bb082`.
2. Extracted and executed the complete numeric fragment at plan lines 1331–1417 without editing it. Its canonical two-frame reconciliation and terminal inclusive prefix passed. Eleven additional refusal controls passed: bool/string/NaN/Inf rewards, three invalid selected indices, and separate corruption of each of the four frame reward fields. A near-rounding comparison was accepted; the terminal prefix remained 1.0 after the zero-reward terminal row.
3. Reviewed the final localized export caller amendment and its exact S1 file/gate list, then rechecked the final plan SHA256. The preflight and numeric fragments are unchanged by this amendment. Source/caller assessment is static except for the explicitly listed probes. I did not run the full test suite or claim that future regression files already exist or pass.

## Confidence Assessment

High confidence that B1 is resolved within the stated stopped-owner, companion-free contract: the specific failure mechanism is removed and independently tested, including committed-WAL counterevidence. High confidence that W1/W2 now have executable ownership and meaningful acceptance gates. Moderate-to-high confidence in whole-plan feasibility: source/API/caller checks support the design, but actual learning, shutdown and complete ordinary sink acceptance still require implementation.

## Risk Assessment

Following the revised plan is reasonable. The highest remaining delivery risk is the demonstrated recorder lifecycle prerequisite; the early E0a boundary materially reduces wasted downstream work. The strict database custody policy intentionally refuses otherwise valid pending-WAL artifacts and will require disciplined caller sequencing. The canonical format cut has a broad fixture/caller footprint; S1 must remain atomic and its full gates must run. Historical artifact preservation and the no-migration rule remain appropriate.

## Information Gaps

No candidate implementation exists for these changes. This review has not executed full E0a, real candidate Q/RND updates, format-2 ordinary persistence/broadcast, all current export callers under the new custody policy, or the final default/slow acceptance matrix. The private-copy probes do not establish exclusive custody in a deployed caller. Static coordinate/spatial assumptions outside the bounded recording representation were not expanded into a separate redesign or acceptance claim.

## Caveats and Required Follow-ups

No blocking plan revisions are requested. Execute E0 and E0a before substantive episode work; preserve and resolve any demonstrated prerequisite through the named scope gate. Execute the now-specified S1 export connection sequencing and real reopen/cleanup tests without weakening custody. Keep the exact real-artifact observer and nonvacuous learning checks. Retain the original review and its receipts unchanged. Record this re-review separately; PRD-0005 remains unaccepted until candidate evidence satisfies all criteria.

Only this report and disposable probe outputs were written by this reviewer; no repository, tracker, Git, retained historical artifact or environment mutation was performed.
