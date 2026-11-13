# Independent owner caller/fixture SPEC + QUALITY review

2026-11-13. Reviewer: bac_astra_recurrent_owner_review. **APPROVE scoped source repair; no findings.** This is an owner-test caller/fixture review, not programme acceptance or a fresh production qualification.

## Identity and scope

Root-supplied R85 tree `e1d5bf0e123cc04eca943a34125bdfbd1e6fc42a`, manifest `9df6603bae0b0ebeedecf199e222cacddb4de501e1242c148117f9c85d678246`, base `29d0204a`. I did not independently inspect Git or reconstruct that tree. Read repository AGENTS.md and the OWNER-CALLER BRIEF, PREFLIGHT, GRANT and REPORT, then reviewed the supplied REVIEW.diff against the current owner source and admitted production contracts.

Measured before source reading: owner test617, sequential replay1930, replay contract374, RNG custody371 = exactly four admitted bodies /3292 lines. Growth is six owner lines; below owner650 and hard5/5000. No fifth body, imported implementation, whole plan or execution copy was opened. Within admitted files, inspected the owner module and relevant sampler, storage, loader, shared custody and domain implementation paths.

Independently verified SHA256:

- Owner test: `15c6b65d60e45c4e865689593de42d2079dc34318949462c51b257a5923796b2`.
- Sequential replay: `e261a0caca68c74cc36bdb9469b126aa0bdae38eeababf358a20bf96f8373317`.
- Shared replay contract: `8de53fc6814a16bafb703728ed396d7b9a1298afdb415be4ec8d1d85ac1502a1`.
- RNG custody: `9d6cd6fcfe62d8e53bda1e6ce7b34a89454ccc88373b5ec4cd072fe004ad66fb`.
- Supplied REPORT: `487c800db33f0bc0f68236448dd7f9b9da35ce3e2d5d5ae9817fdd575be996a7`.
- Supplied REVIEW.diff: `db5e9fa602877137a2fb61b0d6022701581b7fb978ba2bf938ea1b6fc41740d6`.

## Specification and quality conclusions

All 21 original missing caller declarations are repaired exactly as granted: seven samples, thirteen serialized loads and one mode load. The new six-row sample makes 22 current affected calls. The module holds no surrounding RNG operation or backend activation at those calls. Explicit `lineage=None` truthfully declares standalone work; it does not fabricate parent authority. The shared decorator requires the keyword, and the domain rejects None during genuine same-thread nesting. The public loaders explicitly forward the declaration through preparation and installation. No new default, compatibility adapter, fake operation, production edit or exception suppression appears in the supplied patch.

The deterministic replacement accepts the actual `random.choices(population, weights, k)` seam used by sequential replay at line473. It selects the actual stored episode, while the existing randint seam selects start zero. Neither replaces the sampler nor fabricates a batch or custody callback. The terminal at index3 now makes the original four-row terminal-inclusive all-true mask assertion honest. The additional six-row real sample asserts exactly four true rows followed by two false rows, retaining all composed reward values. This detects failure to mask after a terminal without weakening the existing mask or reward assertions.

The six-row post-terminal transport is intentionally stored through the existing unconfigured direct path. It is not passed off as valid configured captured storage: `_captured_rows` still refuses real rows after a terminal. Existing qualified fixtures retain declared action_dim8, bounded actions and final-only terminals. The separate archive/inspection test continues to exercise the preserved format5 transport and historical-legality refusal, while configured format6 and malformed format7 paths retain their existing roles.

The supplied diff removes no test definition, parametrization, original assertion, refusal regex or nonmutation check. The original 49-case shape is therefore retained by source inspection (actual collection is root evidence). Exact-state roundtrips, unsupported versions, exact key sets/capacity/kind, malformed tensor contracts, component handling, archive identity, empty sampling, clear and stats checks remain present. The only assertion changes are additions strengthening terminal coverage.

## Execution evidence and limits

This reviewer has executed no imports, tests, runtime, static checks, Git/index commands, source edits, branches, worktrees, copies, deletion or delegation. Read-only shell inspection, line measurement and hashing were used. This review file is the only write.

Root separately reports R85 first formerly blocked node PASS1 (3.9820597s), replay53 + recurrent54 PASS, collection158 including owner49, targeted Ruff + Black PASS, and completed source/process custody816/573/13/14MAIN1 verified. Those are supplied results, not independently executed or log-verified by this reviewer. At the time of this source review, root reports full owner49 and both isolated child runs still running; no terminal result is inferred. The developer REPORT's checks are also attributed to its author.

Source approval is confined to the owner caller/fixture repair. Full owner runtime qualification and any separately granted independent execution remain distinct evidence. Production remains the root-reported independently approved R84 production. Final B6, CUDA, other callers and programme requirements remain open as applicable; accounting stays28/38/66. Nothing here grants acceptance waivers or changes that accounting.

## Authorized independent execution and final disposition

After the source review above, root reported its full owner49 PASS (4.5180249s) and retained replay109 PASS including both actual isolated children, then explicitly authorized this reviewer to run the existing exclusive independent spec. I executed exactly:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 CUDA_VISIBLE_DEVICES='' PYTHONPATH=/workspace/bac-review-2026-11-01/qualification:/workspace/hamlet/src python /workspace/bac-review-2026-11-01/qualification/run_bac_packet_checks_locked.py /workspace/bac-review-2026-11-01/qualification/wave35-r85-independent-owner-sequential-spec.json
```

Session95798 completed exit0. The actual emitted harness result is owner-sequential PASS, elapsed4.393503427505493s; the resulting log footer confirms **49 passed in0.15s**. Log `/workspace/bac-review-2026-11-01/qualification/wave35-r85-independent-owner-sequential/owner-sequential.log`, emitted SHA256 `e0448535e2dab830bb0d0b2a13c01c541b7b4298894f73248d6e36206289d560`. The emitted candidate tree and manifest match the R85 identities above; harness SHA256 is `180558c22da088a57326aa9251fbb64761e2788f18cb982532525b84b571f791`. No helper implementation or spec was opened or changed, and this reviewer ran no custody verifier.

Root subsequently confirmed its sequential `verify_bac_run` PASS for this independent execution:816source/573configs/13artifacts/14registryMAIN1, process/import/thread/source-index custody, exact R85 tree/manifest and all sessions closed. This custody verification is attributed to root, distinct from the reviewer-executed test result.

**Final SPEC + QUALITY disposition: APPROVE this owner-only repair, with independent other-model actual49 PASS and root-confirmed custody. No findings.** Root's final candidate selection is158 unique cases =109 replay +49 owner. The independently repeated owner49 is the same49, not98 coverage; first-node PASS1 also overlaps owner49. R84's original owner result remains1PASS/1FAIL at the missing-lineage prerequisite, before intended masking assertions; R85's repaired exact node and full selection supply subsequent causal evidence, without replacing that failure history.

This update supersedes only the earlier pending-runtime status. Final B6, CUDA, other callers, integration and whole-programme acceptance are not established by this packet. Accounting remains28/38/66.
