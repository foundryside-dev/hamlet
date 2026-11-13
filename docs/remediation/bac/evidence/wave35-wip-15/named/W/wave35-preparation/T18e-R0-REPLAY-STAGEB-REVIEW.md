# R0 replay Stage B independent SPEC and QUALITY review

2026-11-13. **SPEC: CHANGES REQUIRED. QUALITY: CHANGES REQUIRED.** This is actual source review of the frozen producer, not approval inherited from Stage A. Material findings below precede any bounded GREEN acceptance. Root's current execution is pending receipt here; this reviewer ran no application imports, probes, tests, Git/index operations, source edits, copied sources or delegation.

## Source custody and dependency boundary

Root supplies R76 candidate `ea50156c62b594cb1343f4d2561120b77164707b`, HEAD `678513c7`. Measured and hashed before reading the revision; inspected the actual five whole bodies, plus the supplied diff and prose requirements/report/API. No sixth implementation/test/helper body was opened.

| Body | Lines | SHA256 |
|---|---:|---|
| replay_contract.py |352|eb40cf7a78d0ddec538a05649b34ddb2c5521dc1ac8f68de3319344b0fd73b7a|
| replay_buffer.py |715|85a30028b21a2400fbbe43f82ac7422a20320c7173535a4e3bfcb342a81e29b3|
| prioritized_replay_buffer.py |1142|6d0fd54102363bb89b27590fef3e97ccdca3de6dbdce214c0c4b1219759b2bc0|
| sequential_replay_buffer.py |1884|b29a5be9b48c99180ef64730802f041cf4536b30b8771d2ad945ceca7569bad6|
| test_replay_rng_custody.py |684|e70c17a0e79497a06cef3c78f4b09fc8a2310401d8a39bffec5d1d4d2d892ab2|

Production paths are under src/townlet/training; test path is tests/test_townlet/regressions/bac. Total4777/5000, headroom223; new test684/750. Prior Stage A reviews/seals remain intact.

Consumed current handoff/core contract and Stage B brief/report/API, source-qualified DOMAIN-REPLAY-API, DOMAIN-NESTED-TOKEN-API, DOMAIN-STATUS-LOCK-FACT, REPLAY-HELPER-RNG-FACTS, and accepted REPLAY-POISON-BOUNDARY. Historical helper and per_sampling internals remain their supplier's evidence. SamplingReceipt and validate_successor_masks dependencies are directly inspected in this packet and introduce ordinary validation/copy, not another draw. Arbitrary Mapping/Tensor subclasses, deepcopy/extension hooks and uninspected library internals are not thereby purity-qualified. Child bootstrap and new external verifier internals are outside this packet; actual child qualification remains root/supplier evidence.

## Material findings

### B1 — P1: fresh prepared authority can bless stale destination validation

Locations: flat `materialize_validated`664–667 and `load_for_mode`705–711; PER1084–1086 and1127–1132; shared `replay_prepare`143–148.

Both public validation APIs return a material DTO. Later materialization checks its class, copies it, and issues a **new current** owner revision/domain token. Flat/PER materialization does not repeat the destination compatibility checks performed during validation or bind that validation to the destination revision. Consequently a supported ordinary sequence can bypass the new current-owner promise: validate width1 state against a width1 owner; clear and repopulate the same owner with valid width2 rows; materialize the old validated result; immediately load that handle. The new revision/token match and installation restores width1. Direct fresh `prepare_serialized` of those same saved rows would reject the current width2 mismatch. No raw aliases, private access, fabricated DTO or exotic callback is needed. `load_for_mode` exposes the same schedule as a thread interleaving between its validation and materialization.

The owner lock is not continuous across that boundary, and issuance after the intervening mutation loses evidence that validation was stale. Fix by preserving issuer/revision authority for target-dependent validation or by revalidating the complete owned state against the **current** destination under the preparing lock before issuance. A pure data DTO may remain usable, but its old compatibility result cannot be promoted into current authorization. Also cover caller mutation of publicly returned DTO tensor/array material: either protect the validation result or revalidate owned bytes before issuing authority. Do not merely move the final install token check earlier. Add a genuine flat/PER validation→managed mutation→materialization regression and unchanged-live refusal assertion. Sequential's materialization repeats compatibility and width/archive work; review its returned mutable DTO under the same issuance rule rather than assuming all three families share the flat failure.

### B2 — P2: prepared material is stored in the caller-held authority object

Locations: replay_contract30–36,56,84–93.

`PreparedReplay` advertises opaque publication but has a public payload-taking constructor and a writable `_payload` slot. The issuer registry binds only identity to revision/token; `_prepared_payload` then trusts the material currently stored on that caller-held object. Thus the registry does not bind the authenticated identity to immutable issuer-held material. The accepted opaque-handle direction explicitly excludes a public material constructor, and this implementation leaves reinitialization/rebinding as a material substitution surface. This is separate from the documented cooperative quiescence of existing raw live tensor/deque aliases.

Make the handle identity-only and retain material with revision/token in the issuer's private issuance record, or provide an equivalent non-rebindable issuer-owned association. Fabricated/copied handles must remain refused, and cloning before installation must still prevent candidate material becoming a live alias. This is not a request to make Python private state secure against arbitrary reflection; it is a request that the normal authority object have no material constructor/storage surface. Add a finite fabricated/copied/reinitialized-handle control and verify live state remains unchanged.

### B3 — P2: recurrent “RNG-free leaf” classification omits real scratch sampling

Locations: sequential `_support`1057–1067, `_refresh_priority`1069 onward, store_captured_episode1226/1271, update_priorities1447/1509; Stage B report's blanket RNG-free leaf statement.

`_support` calls real `per_sampling.sample_units` with a cloned owned generator. The supplied helper capsule confirms beta0 and batch1 still perform actual choice. After a priority domain exists, storing captured rows can reach that path through refresh, and priority updates reach it directly. These owner-only operations do not consume ambient RNG or advance the live generator, but they are **not literally RNG-free**. The accepted leaf ruling was explicitly conditional on that classification; the broad prose cannot stand unchanged.

Smallest reconciliation: explicitly classify these paths as owner-local scratch-generator validation, prove complete ambient and live-generator preservation while executing the real selected support check, and state their post-common-poison behavior. If this finite scratch exception is accepted, owner-only exclusion is sufficient for the ambient-isolation invariant and there is no need to replace the algorithm or blanket-gate all storage. Otherwise the consuming support route must admit before the owner lock with authentic lineage. Do not insert domain acquisition inside `_support` while holding the owner lock, silently suppress its draw, or describe clone sampling as a no-draw validation. This finding does not identify a demonstrated ambient bypass; it identifies a concrete false classification requiring explicit reconciliation.

### B4 — P2: new publication/nesting guarantees lack their finite causal controls

Locations: regression473–566 and child611–636; shared publication104–112 and three new load_prepared bodies.

The retained four prepared tests cover flat stale/one-use, foreign PER and released peer currency. Local continuation exercises successful PER/recurrent load. They do not exercise same-held-outer prepare→install or sibling ordinary work invalidation, failure during the newly staged copies, partial publication/quarantine, or retained candidate/live alias isolation. The only new Stage B behavioral test is a direct-sampler poison child; it does not test poison refusal of preparation/install or nonhealing by a local clear. These are explicit new guarantees and important branch distinctions, not a demand for a broad test programme.

Add compact genuine controls around the existing real producer seams: nested success then intervening sibling/owner mutation refusal; clean staged clone/merge failure before publication with full live preservation and healthy usability; a forced assignment failure after at least one real field publication followed by quarantine refusal (including clear); and installed material independence. Extend the existing isolated child to exercise a preissued prepared handle and prepare/install refusal after poison, with permitted local work unable to heal it. The shared guard can be tested once, but each family's distinct staging path needs evidence adequate to its changed implementation. Preserve exact runtime/child custody and remeasure whole files before growth; do not evade the cap or replace real sampling/storage with mocks.

## Accepted source observations

All actual public direct and qualified sampling methods enter the one domain, then the owner RLock, before their existing selected primitives. Required explicit lineage is present. No registration-only gate, default lineage, implicit ambient lookup or second domain appears. Current sample methods call internal non-admitting helpers and reentrant owner reads; they do not perform another public sample with unrelated None. Prepare wrappers likewise use internal materialization. Existing composed load methods pass the caller's authentic lease when nested, or use released prepare/install with None; the core supplier explicitly supports both token cases. The stale-validation gap in B1 is a separate earlier boundary.

Owner-only locks cover storage/configuration/priorities/tick/clear/archive/read/transport. Same-owner mutation attempts advance revision conservatively. No status query appears under those locks. Archive-only temporary validators bypass registration solely for private validation and never escape as usable public owners; their actual validation path uses private methods, avoiding missing guard state and held-domain registration. The ordinary helper profile supports archive copy/digest classification, subject to B3's distinct scratch sampling and the stated extension limits.

Direct configured PER retains its global vectorized NumPy algorithm; qualified PER retains its configured local residual choice schedule or global path. Flat still uses selected-device Torch randperm. Uniform recurrent sampling remains Python random; prioritized sampling still publishes its cloned advanced local generator only after batch construction. Local transport retains the selected engine/state/origin. No ambient checkpoint or replacement seed was added.

Each install obtains actual domain admission and owner exclusion, checks issued identity, stages archives and tensor/array/episode/policy/generator copies, then validates revision/current token immediately before calling its publication closure. Successful publication consumes the handle and increments revision. Exceptions within the assignment closure quarantine the owner. Installed tensor/array/episode material is newly owned; no successful publication directly installs the old candidate tensor aliases. B2 concerns authority/material binding, not omission of these clones. Failure tests in B4 remain necessary to qualify this new suffix.

CPU inventory is empty without CUDA availability queries. Explicit indexed CUDA and initialization requirements are published; CUDA remains hardware-unqualified. In particular owner guards currently exit before the enclosing domain's device-completion exit. Source/runtime qualification must not infer same-owner CUDA completion exclusion from the CPU lock tests: asynchronous completion and owner-only device work require applicable hardware/stream-order evidence or an adjusted owner-lock lifetime. This is retained hardware scope, not a claim of tested CUDA correctness.

## Execution, migration and final disposition

The test calls in this five-body packet were migrated to required lineage. External POP/BANK/runtime/runner/serving/manual callers have not been reviewed or migrated here and are correctly marked open. Constructor registration must occur at idle before any enclosing held lease. The required API changes are intentional; no compatibility fallback is justified.

The spawned child records its actual PPID and resolved replay module paths after bootstrap identity, poisons its own authentic domain operation, and proves direct consumer refusal while preserving selected data/ambient observations. It is a public-poison consumer control, not a genuine restoration/setter failure witness. Parent Process/queue PID and PPID checks are present. The distinct external verifier is pending and no child PASS is inferred. Parent domain is not intentionally poisoned.

Root collection/prerequisites were starting when this review was assigned. No exact R76 PASS receipt has been received by this reviewer at this writing. Stage A results remain source-bound history. Even an all-green current20 ordinary cases plus child would not resolve B1–B4 without the stated corrections/controls. Actual root and independent fixed-source GREEN, static checks, caller migration and applicable hardware remain required after source findings are addressed. Package/global R0/B1 acceptance and outer all-child publication are not granted; accounting remains28/38/66.
