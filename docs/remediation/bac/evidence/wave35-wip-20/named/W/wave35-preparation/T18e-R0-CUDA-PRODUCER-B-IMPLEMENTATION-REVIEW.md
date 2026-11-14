# Producer B activation — independent implementation review

2026-11-13. Reviewer `/root/bac_astra_activation_review`.

**SPEC PASS / QUALITY PASS for the bounded final B implementation and activation-test contribution. No concrete P1/P2 defect found.** This is independent static source review, not a claim that root's pending R111 runtime passed or that B6/R0, post-poison GPU capability or hardware/global qualification is complete.

## Frozen scope

I verified the implementation report SHA256 `73906ec1f600cf285c960de34f3ef012b2ff962dbea4ecedc9abc45bf6a05d09` and reviewed actual code against the previously consumed preparation, its independent review and exact supplier capsule. The earlier 420-line activation review remains unchanged and historical.

| Body | Lines | SHA256 |
| --- | ---: | --- |
| src/townlet/exploration/rng_custody.py | 1195 | 6cb01ca77b58db5f4c4784dc36da566c06cf68c2a7c2ce227bb780549f3344f8 |
| src/townlet/training/replay_contract.py | 881 | 8c0251c3c46e9c296e7b3bb5afcf2f6cdce8083fa22666c5a662be454a9a12f4 |
| src/townlet/training/replay_buffer.py | 816 | 683e0b9b0f500cc523391b8574acbfc31bf8dc8a36d92ad0547323621261838d |
| src/townlet/training/prioritized_replay_buffer.py | 1310 | 7a76183ded0712103c81ebd31b3e05425b3738e9338689cacfbefbc8fd493a29 |
| tests/test_townlet/regressions/bac/test_replay_cuda_activation.py | 597 | cf2e0c46d3910eb3b2aa01ebb746664333d7c83e52278e5cafd5f9f08a3fa8fe |

Whole-body charge4799/five, measured before this review's source reads. Shared/flat/PER hashes match the earlier reviewed bytes. I read the final activation test and actual new core implementation, with relevant caller/lifetime/completion sections within the four implementation bodies. No other implementation/test body was read, including the separately owned core2360 test, producer regression, archive helper or relocation/diff substitute. No runtime, branches/worktrees/checkouts/copies, source/test edits or subagents. Only this report was authored. Root remains sole integration/execution owner.

## Canonical issuance and lazy resolution

Core140–330 implements frozen descriptors and exactly18 distinct source-issued opaque constants with flat8/PER10 routes matching producer dispatch. Constants and descriptor construction perform no producer class lookup or CUDA query. Every row has healthy=True/post_poison=False; no obsolete-record union, test issuer, caller policy registration, caller module/name/predicate or nineteenth PER load constant exists.

Descriptor rationale text identifies ordinary inputs and retained-state effects consistently with the adopted profiles: retained legality, archive ownership/digest, priority/ID staging, sampler metadata and the validation-only flat load prelude. Tags resolve to the stipulated primary formal types. This remains descriptive metadata; no new arbitrary-input purity test or rejection is added.

`_resolve_local_cuda_record` at587 checks real PID first, actual RLock ownership next and CUDA transaction reentry before descriptor inspection/imports. It selects fixed imports only by the closed source owner/input tags and rejects unknown tags or non-class resolutions. Missing/partially unavailable module attributes/import failures propagate before a result exists. Producer classes are referenced only in the private resolver body, avoiding eager core→producer cycles at core import. Runtime import-order probes remain separate evidence, not inferred from this syntax alone.

`_local_cuda_policy` at632 repeats PID/lock/reentry checks and authenticates exact contract and descriptor types before cache use. A miss publishes only after successful complete resolution and exact frozen record-type validation; an import/type failure cannot leave a successful entry. A hit requires the current source descriptor by identity and returns the existing concrete policy. Resolving another route changes only its own dictionary entry. No policy resolution mutates readiness, poison, RNG generation/revision/currency or owner health, and no owner instance/participant/gate/error is retained in the finite descriptor-policy cache.

Fixed canonical imports are the accepted cooperative source boundary. This does not promise security against arbitrary Python mutation of imported module attributes or private dictionaries. Such a stronger claim would exceed both the plan and the repository's stated custody model.

## Live authority, ordering and lifetime

Public local entry at728 checks PID and transaction reentry before acquiring exclusion, then rechecks reentry and rejects nested public local gates. It authenticates source contract and actual registered member before invoking canonical resolution. The resulting owner must have exactly the resolved canonical concrete class; subclasses and module/name spoofs receive no authority. A strong local owner reference survives resolution, then the gate stores/pins that exact owner. Closing clears pins and owner reference; cached class metadata cannot keep retired instances alive.

`_gate_record` at653 resolves nothing. PID, issuing thread, actual lock and any lineage are authenticated before live local binding is used. The live participant must still identify the same owner, the cache must exist, its descriptor must be the current manifest descriptor, its record must be the exact gate policy, and the owner's concrete class must match. Descriptor removal/replacement or cached policy replacement therefore invalidates rather than silently rebinds the active gate. Completion, outcome lookup and close all consume this authentication. Populating another route does not invalidate the first policy.

Public nested-gate refusal and private cache population while holding an existing gate remain distinct. The implementation does not accidentally add `_has_local_gate` refusal to the private resolver/cache methods, so the separately specified same-lock second-route stability control is possible without granting public reentry.

Permission checks retain the separate healthy/post-poison bits and READY requirement. With all18 post_poison=False, poisoned local GPU entry refuses before CUDA resolution/body. This is the adopted staged permission, not proof of post-poison GPU safety or removal of the outstanding qualification obligation. Existing CPU-only local work remains independent of this manifest. Resolution is not an operation/admission replacement and does not grant prepared publication/currentness.

Shared replay still plans under owner exclusion, obtains the real gate after releasing that exclusion, replans, executes the actual leaf under exact completion and reads the authentic failure flag before owner release. Existing invocation/outer completion, quarantine, error identity, prepared authority and sampling algorithms were not replaced by B. Detached PER archive validation remains unenrolled and receives no production contract.

## Final activation tests and repaired limitations

The final597 file retains real canonical constructors/registration, exact18 manifest/policy checks, wrong-family/subclass/spoof/invalid authority refusal, sequential cache identity, retired-owner collection and a cold failed lookup followed by genuine restored success. The manifest and resolver are not mocked. The cold-cache fixture uses idle admission and scoped restoration without poison/health reset. It checks absence of successful publication after missing class, rather than merely accepting any exception.

The all18 success flag is now read after completion exits while the gate remains live. This resolves the earlier review's timing limitation. Expired access still refuses.

The stable priority case now wraps the capacity4 ring to IDs `[4,5,2,3]`, updates IDs `[4,2,4]` with distinct errors and asserts the full priority array. It discriminates ID-to-slot lookup from direct physical indexing and max reduction from last-write duplicate handling. The added stale-ID case presents a valid ID followed by retired0, requires the real conversion/completion path, checks no numeric/ID/max publication, checks the expected revision change and verifies usable owner/domain status. Thus the earlier stable-ID numeric limitation is resolved.

The metadata tensor seam still performs real CPU numeric/copy operations and explicitly disallows a non-CPU conversion destination. Its added clone observation retains real torch cloning. Independent source/archive controls verify nonempty values and ownership; no digest, canonical archive or policy is fabricated.

Added public push controls for both families execute source-CUDA planned routes into actual CPU storage, then verify owned observations/successors/actions/rewards, component presence and explicit all-legal successor masks. Mutating the source afterwards cannot change committed values.

The flat `load_for_mode` case exercises the actual validation-only local contract, requires its completion before gate exit and later admitted conversion, verifies the expected two source-device completions, full restored state and detachment. It does not turn later admitted materialization/install into another local route.

The PER historical case constructs a genuine nonempty canonical archive using the supplied helper interface, runs real public install and property retrieval, observes clone/digest CPU transport within each gate's completion, and checks digest identity, distinct returned objects, preserved values and input/returned-data isolation. Helper internals remain attributed to the accepted supplier facts, not independently read here. These are CPU protocol/numeric controls, not real GPU purity/kernel qualification.

## Finite defects and qualification gaps

- **Blocking implementation/test defects:** none found within this five-body static review.
- **Earlier minor test gaps:** completed-outcome timing and stable-ID/duplicate discrimination are repaired at the final test hash. The additional plain push, flat load prelude and PER archive controls are genuine public-body evidence, not empty gate admission.
- **Remaining public-route evidence:** this file now exercises nine distinct public CUDA-planned local routes: flat push/serialize/load_for_mode; PER push/serialize/update_priorities/update_unit_priorities/install_historical_archive/historical_archives. The other nine rows require root's exact existing producer-route ledger: flat push_recorded/readiness/validate_serialized/historical_archives/install_historical_archive; PER push_recorded/declare_unconstrained_action_dim/readiness/validate_serialized. This is scheduled qualification ownership, not a request to duplicate those bodies here or a claim they are missing from root's selection.
- **Separate core packet:** exact runtime import order, inherited PID/cache guards, lock/reentry/thread refusal, active second-route cache stability and tamper controls remain dependent on the independently owned core test review and root's execution. The production implementation supports the accepted interfaces; I did not inspect or claim its separate test results.
- **Execution/global boundary:** root reports R110 five fixture passes and20 causal RED failures on earlier source. R111 collection/runtime was pending when this review was requested. No new PASS count is asserted here. Existing isolated completion/poison, admitted/prepared/competition, parent outcome/lineage, recurrent and applicable actual one-/two-device CUDA qualification remain governed by their own packets. This review neither waives nor duplicates them.

No additional blocker-driven probe is requested. Root's already scheduled exact-byte activation/core/producer selections and independent core review are the appropriate next verification. Re-review is required for subsequent relevant source/test byte changes.
