# Replay fix A — independent tests-first SPEC and QUALITY review

2026-11-13. **SPEC tests readiness: CHANGES REQUIRED. QUALITY tests readiness: CHANGES REQUIRED.** B1/B2 have genuine causal RED evidence; two test-fixture defects leave three B4 cases unexercised. Repair those fixtures and rerun them before the separate production grant. This review grants no production approval and requires no artificial RED for already-correct branches.

## Scope and seal inputs

Root supplies R77 tree `275c9adc2c9f8bd5f1220215a3bbcbc8dbb6d7bd`, base HEAD `678513c7540a61114d59a17d1b1e0eb8a06ce0a2`; production is unchanged from R76. Read Fix-A requirements first, report, review diff, original Stage B review/addendum/proposal/brief/report/API and named domain, poison, helper RNG and qualified-child prose capsules. Proposal SHA256 is `2a404c22afcbf97858cbf087b68bc7d5cb7402667d577cc719dac12c651a552b`. Fix-A brief/report/diff SHA256 respectively are `36ca25e703003c4211146eaf5ff48845ef3331355693a6abe02c9a21b8c240e7`, `67da28dc176142b6028154bd24c2f52ed30f40cd5a25caa0582a4b50fac4bfa6`, `699e1580a91cf1074e3e2eccb097fc93941e104f0882db0a56f3b01766cbeb08`.

Measured and hashed before source reads; exactly these five whole bodies were inspected, total3668, planned ceiling4471, hard limit5000:

| Body relative to /workspace/hamlet | Lines | SHA256 |
| --- | ---: | --- |
| src/townlet/training/replay_contract.py |352|eb40cf7a78d0ddec538a05649b34ddb2c5521dc1ac8f68de3319344b0fd73b7a|
| src/townlet/training/replay_buffer.py |715|85a30028b21a2400fbbe43f82ac7422a20320c7173535a4e3bfcb342a81e29b3|
| src/townlet/training/prioritized_replay_buffer.py |1142|6d0fd54102363bb89b27590fef3e97ccdca3de6dbdce214c0c4b1219759b2bc0|
| tests/test_townlet/regressions/bac/test_replay_rng_custody.py |1088|db262e93e89fdda40f4e4f94e86857c21905079ed76216e0dd6514c636293d5e|
| src/townlet/exploration/rng_custody.py |371|9d6cd6fcfe62d8e53bda1e6ce7b34a89454ccc88373b5ec4cd072fe004ad66fb|

No sixth recurrent/helper/caller body, runtime, imports, compiler, formatter, Git/index operation, source edits, source copies, branches/worktrees or delegation. Only this review artifact was written. Execution below is root-owned; reviewer inspected supplied logs as evidence, not by running the application. The recurrent exact required preparation/install signatures are supplied in the Fix-A report by its bounded source owner, not independently inferred from a sixth body.

## Material defects

### A-T1 — P2: archive fault controls fail during invalid fixture construction

Regression `_install_real_historical_archive`737–761, invoked by archive-copy cases at796. `_publication_owner` uses `_flat_rows`, whose reward object supplies only total rewards. Current serialization legitimately represents absent optional reward components as None. Copying these fields into `legacy` and changing only format_version to4 produces invalid old-format rows: flat575 and PER967 require tensors for all old component fields; only current-format rows may skip absent components.

Both root archive-copy executions fail on `rewards_extrinsic` None at the initial public loader, before preparation, the injected merge wrapper, or any healthy-reuse assertion. They therefore do not yet establish either family's archive staging guarantees. This is a fixture prerequisite failure, not production causal RED. Build valid finite float32 old-format component tensors in this fixture (or originate the archive from genuine component-bearing rows), retain the real public archive loader, and preserve the assertions that a real owned archive exists, actual merge completes before the fault, complete state stays unchanged, and fresh install/sample succeeds. Do not weaken production validation or replace the archive with a stub.

### A-T2 — P2: PER independence test uses Tensor mutation API on NumPy arrays

Regression894–895 and903–904 call `.fill_` on incoming and retained-material priorities/unit_ids. These are numpy.ndarray values; their in-place method is `.fill`. Root confirms AttributeError at894, before install. The later three occurrences would remain broken after fixing only the first.

Correct all four NumPy mutation calls, retaining Tensor `.fill_` calls and the real disposable Generator draw. Rerun the PER node through both pre-install input mutation and post-install retained material/RNG mutation, with complete state comparisons. The currently passing flat node does not discharge the distinct PER array/generator ownership path.

## Accepted test design and causal assessment

B1 tests572/601 exercise genuine current owners and public returned validation DTOs. Width1 validation followed by same-owner clear/width2 push distinguishes stale validation from fresh preparation, whose mismatch refusal is explicitly checked first. Invalid mutable observations, successor masks, PER priorities and IDs must not obtain new authority. The materialization assertions correctly fail at issuance on R77; no unrelated missing API or invalid fixture explains them. Complete state assertions after expected refusal remain to execute after the repair.

B2 tests618/624/636 establish the prohibited material constructor/slot/reinitializer surfaces and counterfeit identity refusal. Test765 separately captures real earlier material through `_issue_replay`, prepares a different current authentic identity, and substitutes the earlier material onto that current identity. The earlier preparation being stale does not make the current identity stale: source and actual DID NOT RAISE establish the intended identity/material-binding defect. Fresh preparation after each rejected admitted install is correct: domain failure can conservatively invalidate prior currency. Copied identities may be refused at copying or installation; fabricated/copied cases already pass. Positive fresh install and second-use refusal preserve the useful capability rather than permitting reject-all behavior.

B4 held-lineage tests674/687 use a real registered peer and authentic yielded lease; same-held preparation/install succeeds, while actual sibling sampling and genuine same-owner mutation independently invalidate. State snapshots include complete transport, capacity-sized tensors, physical position, health, flat wrapping and PER reverse mapping; transport additionally carries priorities, IDs, sampler engine/state/configuration, beta, legality, presence and history. Authority revision/currency exclusion from replay-data equality is deliberate and correct.

Tensor-copy faults call the original clone before raising, with evidence of the selected real cloned value. PER sampler faults reconstruct a distinct Generator and compare complete metadata before raising. Monkeypatch context cleanup precedes state/healthy-reuse checks. Assignment failure delegates real observation publication, fails on the following action assignment, proves new observations and old actions, then requires quarantine refusal of sample, prepare, install, clear and serialization. These are real producer seams, not mocked sample results. Flat input/candidate independence passes; PER independence remains blocked by A-T2. Archive merge seams are appropriately designed but remain blocked by A-T1.

The expanded existing child prepares all three real owners under one authentic held outer prepare lease before genuine public poison. It requires the exact poison exception for direct samples, new preparations and old installs, permits owner-local clear under the accepted boundary, then rechecks poison and refusals. It compares transport/ambient CPU state and additional flat/PER physical state. Diagnostic status is called outside owner exclusion, not used as atomic admission. Role `replay_poison`, message `replay poison fail closed`, actual PID/PPID queue pairing, child-owned replay import paths, manifest hashes and exclusive observation writing remain intact; bounded terminate/join/queue/process cleanup and parent healthy-domain/ambient checks are retained. This is consumer poison refusal, not a restoration failure or CUDA test.

## Actual R77 execution evidence

Inspected root logs under `/workspace/bac-review-2026-11-01/qualification/`; root reports all runtime/verifier sessions closed and full815-source custody verified. Collection logs show54 cases. Root additionally reports poison child38789/parent38734, actual PPID pairing and24.5657s harness duration; pytest itself reports17.10s. Custody verification and ancestry are attributed to root, not reimplemented here.

| Relative log | Observed result | SHA256 |
| --- | --- | --- |
| wave35-r77-replay-b1-b2/replay-b1-b2.log |18 selected:14 intended DID NOT RAISE failures,4 fabricated/copied PASS|b26c4d87f024380ab4bdc9b59285c688c78ce6effee9ed770e73d25f02ef9f33|
| wave35-r77-replay-b4/replay-b4.log |15 selected:12 PASS,3 prerequisite failures A-T1/A-T2|12cfbebcc848479af2ea1d4d438da44ce8c4ac662e32fff0813558dcdddd3fac|
| wave35-r77-replay-healthy/replay-healthy.log |16 selected:14 PASS,2 repeated A-T1 failures|f683cf1db08b6ba8719ae4a9fe1a3e3b33a10a456029522c4b7ff576902533cb|
| wave35-r77-replay-poison/replay-poison.log |expanded isolated child1 PASS|74107aa406cd7895d089b2b0c4e49c7b0cc0788002f643696c487d693b6c617e|

The14 expected failures comprise all8 B1 validations, B2 constructor/slot2, reinitializer2 and genuine other-issued-material substitution2. The healthy selection overlaps five new B4 staging cases because of its selector; it contains the original11 healthy passes but is not an additional16 unique controls. Do not add overlapping selections or classify the three prerequisite failures as intended RED.

## Disposition and retained gates

Narrow fixture repair is required before tests readiness can be approved. Preserve these immutable R77 failures and capture/rerun exact repaired bytes. No reason was found to manufacture RED for passing B4 branches. B1/B2 causal evidence is valid independently of the fixture defects.

B5 remains a required later production/type gate: shared Callable[..., Any] erasure and inaccurate public preparation returns must be repaired, then root must check genuine missing-lineage callers and actual PreparedReplay typing without defaults/suppression. Shared decorators must remain coherent with supplied recurrent signatures. Recurrent B3 scratch classification and recurrent-specific B4 remain separately required; scratch work is ambient-free/persistent-preserving, not literally RNG-free. B6 unindexed/lazy CUDA capability and device-completion/owner lifetime remain required separate design/hardware scope. CPU child evidence does not qualify CUDA. Static formatting/default ratchet, consumer migration, independent fixed-source checks and broader programme gates remain open. Accounting stays28 qualified/38 remaining/66 total.

Sealed review of the exact R77 tests-only bytes above; no production or package acceptance.
