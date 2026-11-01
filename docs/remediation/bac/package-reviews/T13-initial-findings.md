# Review provenance

Historical finding/triage source identity remains historical; see the final implementation receipt for repaired-source qualification and required remaining X04.

Original `T13-astra-core-review-r0.md`, SHA256 `d85f2f22dd6cb28162ca9c7d2891b0af87d121a2ea4d629e30be759d7e5b4900`, retained unchanged; portable rendering normalizes execution paths.

# T13 independent core review R0 — stationary

Verdict: REQUEST CHANGES for two P2 numeric-boundary contracts below. No new P1 is established in this five-source slice. The independent existing-test run passes 81 selected cases; neither finding has a newly executed reproducer because the authorized runtime permits existing counted tests only, with no new inline/scratch probes or test edits. These are source-confirmed paths, not claims of observed learner failure.

## Defects first

1. **P2 — legacy float32 representability refusal occurs after global RNG consumption.** `prioritized_replay_buffer.py:532–540` calls `_draw` before converting/checking float32 weights. PS preparation checks only float64 final weights. A legal two-row buffer with alpha=beta=1 and physical priorities approximately `[1e-6,3e38]` (obtainable by ordinary finite priority updates from TD `[0,3e38]`) and B=1 has low-priority q approximately3.33e-45 and correction approximately1.5e44. That is representable float64 and passes PS preflight, but cannot be returned in the preserved float32 dictionary. If the actual legacy draw selects that row, the method raises only after advancing the external NumPy stream. Thus the explicit pre-RNG representability-refusal requirement does not hold at the preserved public adapter boundary; the same unsupported request is draw-dependent. The rarity is not relied upon as runtime proof: the code ordering and positive support establish the branch. Preflight the adapter's final-beta float32 representability before its global choice, preserving float64 qualified support, no clipping, and the B=N/beta0 all-ones cases. Add a counted regression asserting the refusal and unchanged global RNG, plus fractional-beta representable and full-batch positives. Existing tiny-q tests exercise PS64, and current global-adapter tests exercise ordinary finite weights; neither detects this boundary.

2. **P2 — new6 restore accepts a maximum priority that insertion cannot serve.** `prioritized_replay_buffer.py:846` validates max_priority with upper bound infinity; its finite helper admits e.g.1e300, and the subsequent check only requires it to exceed active priorities. A well-formed new6 payload with ordinary finite float32 active priorities and max_priority=1e300 therefore validates, materializes and installs successfully, replacing a populated target. The next otherwise valid insertion is refused by the new explicit float32 maximum check at473–474. This is a missing off-side refusal for the new strict schema's numeric invariant. The permissive validator predicate is inherited; the new6 strict-state contract and insertion guard now make the inconsistency explicit. Validate the effective new6 insertion maximum before installation, with a located diagnostic and target/input/RNG purity test. Preserve genuine captured5/old4 semantics and do not use this malformed-new6 case as authority to discard or reclassify preserved captured history. No claimed authored-pack reachability or native current-validation closure follows from this finding.

## Actual-source review and refuted hypotheses

Read all five complete implementation/test sources, total3165 lines: PS145, PB1061, HC669, OP294, counted test996. All test spies/oracles remain in that test. No RC/POP/Brain/native witness/helper/fixture implementation was inspected. RC/RewardTensor and producer interfaces came from accepted task/P2/P3/interface prose. Reviewed actual implementation against the effective task header, preparation, HC coordination and independent review, interface readiness, core tests/implementation receipt, causal RED clearance and X04 overlay. Root AGENTS/CLAUDE/STATUS and requesting-code-review skill were read; direct bounded review assignment supersedes subdelegation/worktree defaults. Preservation and approved historical A supersede blanket compatibility deletion.

The successive explicit RNG route really samples each remaining support, rather than merely relabeling initial probabilities. Its independently enumerated q product and residual weights match `((B-k)+1/q)/N` with k1-based; B=N explicitly ones. Independent replacement uses initial P, repeats and B>N, with `(NP)^(-beta)`. The global adapter preserves a vector np.random.choice without replacement and reconstructs conditional q. Log-centering avoids priority sum overflow and residual support is recomputed instead of subtracting rounded mass. Final beta exponentiation supports q=1e-310 with beta0/.1 without overflowing an unnecessary reciprocal. Float64 support refusals precede draws and do not clip support. No sample-max normalization remains.

Physical indices and stable IDs have separate update methods. Whole-request validation and float32 candidate preparation precede assignment, duplicates reduce by max absolute error, clear retains issuance counter, overwritten IDs retire, and exhaustion is checked before insertion. Rows/masks/component presence align through ring wrap. Buffer history defines ID scope; restore across unrelated histories is explicitly not numeric authentication.

Owned configuration clones complete engine state off-side; five standard engine families are explicitly tagged and restored without hidden behavioral seed or global RNG mutation. PER6 has34 closed keys; exact original5 has27 and adapts deterministically while retaining all original fields except version. Genuine19-key maskless4 retains archive/query/export/fresh0/full-resume refusal. Fallible restore clones/engine/archive union precede assignment. HC now shares explicit supported-current version handling at classifier and policy constructor; historical kind identities remain4/4/5, current standard5/sequence6 remain distinct, and future/bool/mixed versions refuse.

No evidence found for a defect in the core estimator formula, duplicate reduction, configured RNG alias isolation, genuine5 adaptation, or the narrow HC version fix. The independent test oracles calculate probabilities directly from small powers/math.fsum and enumerate actual forced branches. The old-formula negative remains independent. A remaining coverage gap beyond the two findings: no explicit PS64 final-weight-overflow refusal regression distinct from support-underflow; the source preflight itself appears correct. This is optional test strengthening, not another blocker.

## Runtime and identity

Base HEAD41edeb0858cba98a8dcb6ba2af36355457ef4e0a; fixed candidate tree e82f99701b06bd65c65e4112628fc2de1aa6d921. Read-only `GIT_OPTIONAL_LOCKS=0 git diff --cached --quiet e82f99701b06bd65c65e4112628fc2de1aa6d921` succeeded before and after execution. Five source SHA256 values matched before/after. No git write-tree/index/stage/commit/branch/worktree/copy/delete operation occurred.

Verified output directory, spec and basetemp absent before creation. Wrote only guard JSON metadata externally and this ignored prose. Executed exactly one existing counted-core pytest process, workers1, through the provided runner API without reading its implementation:

`python qualification/run_bac_packet_checks.py qualification/wave07-astra-core-r0-spec.json`

Actual child command:

`.venv/bin/python -m pytest tests/test_townlet/regressions/bac/test_per_estimator.py -k 'ordered or independent or tiny_positive or representable or malformed or atomic or allocation or captured5 or genuine_per4 or owned_generator or stale_ids or global_adapter or hc_' -q --no-cov -p no:cacheprovider -p bac_source_identity --basetemp=/tmp/bac-wave07-astra-core-r0`

Result:128 collected,81 selected PASS,47 deselected; pytest4.49s, runner9.114s, exit0. External log `qualification/wave07-astra-core-r0/adversarial.log`, SHA256962dfaa10c2c228e2951f405452c72dc91dfcd2c2c692d9c9f6b11a6a0223192. Runner attests fixed candidate/index and manifest0b893f7838447cb4ce68c1638acfb8c13ffa3d91fb5ab18c78accf52e58c0922; provided plugin/import/Torch1 checks govern process identity. Runtime complete, no process active.

Source SHA256:

- PS c198a25046f5ade3bbc3008e129eb07f558635500bc58640244eeeb94d4624ee
- PB 19f28cbff599b8d934ae29e6078b39d1afa8ecc96d8ad2df65238dec6eb5393c
- HC 2a27ab721e743c25f835bd4e25cff1f52a3d984875115649f5ab9e78e8ba4df1
- OP 10dc3ef7dc288d954147046c95bc8362df2162f3829986be26b2724e86dd4916
- Test 97647ebb9e4d8947bda82f8389dc909383ebb1ea6aa49162eba2b3d51262b0ea

Review-input SHA256:

- task-T13.md 968c9aa836d5e21f341ab98ce8b016c0f882bba6c1b802e872eee0cb2d33db87
- T13-preparation.md dd3585c6db9331a4221c1e95a4c941f1d37adf5ba59af0152096d6d30374b088
- T13-HC-COORDINATION.md 6845c544d14f97a8ae9e40650485806b7d73319b5a5624856c8e7db1c51bc75c
- T13-HC-COORDINATION-REVIEW.md 91b484deee7f38f515837eafeca50a44d9ea2b8e88c5bfbeffac4bc692c1d832
- T13-interface-readiness.md 2b076c4bc1ba53183e37eb008ca8d21c6b748ca7a56a49b6cb535a718b649ca9
- T13-core-test-authoring.md 56c4faea81d5c3502e8b833443fa0bb25b94894041a170880e54519955fa2e11
- T13-core-implementation-r0.md 05240a21c523f86c00ee081b815a2bf3afcdbd9af450c7073a768ee46ebb9fee
- causal-red-clearance.json a9734a2574f732bd2bc4cfc43175a0390890b1115e616fcbe8f884bc97d0b508
- X04-acceptance-overlay.json bd1e028dd6df9ed2bbaad38cb93a9aa0adeffd28ba227e8441110c2d27b68d8c

## Scope and remaining gates

This review does not execute the separately owned native learner, T11 owners, broader HC consumers, six guards or full suite. Root's prior causal RED/current native control results are attributed evidence, not my execution. New bounded C01 real-learner reachability remains distinct from historical B04 API-only evidence. OP supports modes but actual population replacement/stable-handle wiring is a later consumer obligation; this core does not claim it. Complete native validators, empty PER acceptance, canonical outer/nested registry accounting and resource/RNG atomicity remain required T24/T25 work. Actual newly affected consumer regressions cannot be waived by those future labels.

X04 is required existing P1 telemetry work owned T15 beforeG2/T35 sink acceptance, not optional and not introduced by T13. POP was not read. Core passes do not close X04 or whole BAC. Root owns repair, independent rereview, six guards, mandatory full4-worker qualification before affected-boundary release, G2 and all later coverage/slow/hardware/CI acceptance. No capability reduction, fixture rewrite or closure waiver is recommended.

STATIONARY. No source/test/index changes. No durable user-only fallback saved/adopted; failed rule neither grants nor restricts; specific creation approval never fans out.
