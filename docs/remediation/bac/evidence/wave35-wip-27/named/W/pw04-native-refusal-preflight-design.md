# PW04 native refusal: bounded additive semantic preflight

2026-11-14. Independent design review only; no implementation, Git, imports, tests, branches, worktrees or source copies. Recommendation: add a data-validation operation before C rather than weaken C's uncertainty fence. This report is the only authored file.

## Actual conflict and evidence boundary

Root supplies R167 tree `58d551e4044e3822bf5f66c0f20c4244255ba57d`: actual shared DemoRunner checkpoint2 → fresh restore → continued learning passes; original native-corruption refusal fails because the correctly rejected NaN tail is first deeply validated inside C's child preparation. C records preparation entered but not completed and conservatively makes ENV terminal. These are attributed execution facts, not independently run here. The original unchanged healthy-receiver assertion remains an obligation.

Read repository AGENTS.md; B API/review, C API and current-callers prose; current runtime/checkpoint contract prose. Four source bodies charged in full, counted before reading, total **4628 lines**:

| Body | Lines | SHA256 |
| --- | ---: | --- |
| `config/exploration_policy.py` | 1481 | `1b511bd1a8faae1e702dd5398ddb9a81bc655c266de9a56772caa63a5d019ccc` |
| `exploration/scoped_curiosity.py` | 1569 | `fa3c5ce8f8e75bd242e7d2fec3d5264a75952e881a87ec21eba8c039f9219e7c` |
| `exploration/curiosity_checkpoint.py` | 1158 | `b45ba7627b50c123de36862a678a8db98d4ab074db23d296b6cd81a05d74b6c1` |
| `environment/restore_attempt.py` | 420 | `a49770618943d1157162ea77c3b96116baa9cf401eb7aa0b5f7a3e882b6ea4ed` |

No POP/runner/provider/RNG-core/parent-custody body was opened. Their behavior beyond these callers/contracts is supplied by root or B owner. Coordination with B owner independently converged on the interface below. The NaN's exact producer-validator implementation remains outside this source packet; root's actual refusal demonstrates that exercised path.

## Finite interface

Add `ExplorationRuntime.validate_restore_data(*, state: Any, mode: str) -> None` and its BANK delegate `CuriosityBank.validate_restore_data(*, state: Any, mode: str) -> None`. Names are proposals, not existing APIs. Success means the current owned transport can survive the actual selected native semantic reconstruction under the receiving policy/device. It grants no installation authority, currentness promise, accepted episode, parent correlation, receipt or reusable success token. There are no accepted/parent/callback parameters and no fake INITIAL mode for a completed checkpoint.

The production restore coordinator calls this on the saved current runtime payload before acquiring C, preferably before staging other restore plans whose currency could be affected by native operations or participant retirement. Root owns the exact runner call site. Run it outside a C correlation overlay and outside retained parent custody that would prevent the cohort registration gap. Existing C preparation subsequently repeats full validation and genuine parent correlation against its real prepared world, followed by unchanged release/install/finalize stages.

1. Runtime uses its normal public operation guard and existing `_parse(state, initialization=False)`, preserving exact policy/envelope checks, selector/cadence data validation, owned copies, allocation report and post-report checks. Capture/check runtime and BANK revisions as in existing preparation. Delegate only the owned BANK data. Do not invoke `_correlate_cadence`, `_retain`, create a prepared handle or allocate an installation outcome.
2. BANK uses the existing preparation guard and two actual `prepare` admissions. First admission checks no pending completion, records `_preparation_identity`, runs `checkpoint.preflight`, reports allocation before owning input, owns it, validates origin and records. Extract common data checks where useful rather than maintain a parallel validator. Diagnostic schemas must still refuse. Do not call `check_mode` with invented authority or weaken it for existing real preparation.
3. At operation idle, create `_replacement_cohort` using the actual archive flag. In the second admission, recheck identity and invoke one common helper extracted from the existing native-cohort population block of `prepare_restore`: archived native validation; private boundary template validation and `_attach_private`; or shared bootstrap with saved restore configuration, actual producer validation/loading, gradient attachment and exact native/gradient roundtrip. Both real preparation and data preflight call that same helper. Recheck identity at completion. Keep lineage, allocation reporting and actual device-completion behavior.
4. On successful preflight, release its disposable state and return None. Never call `_seal_restore`, `_restore_publication`, `current_token`, receipt issuance, live owner installation, or mutate the restore registries. Installation into an exclusively disposable cohort is necessary semantic validation and does not publish to the receiver. Preserve saved histories, tails, gradients, counters, original order and origin archive; no normalization, pruning, replay or invented attribution.

Checkpoint `preflight` plus `validate_records` alone is insufficient. They validate envelope/phase/policy/descriptor/caches/completion and private counter correlations, but do not deeply validate shared native learning state. `validate_native` calls the actual trainable producer's `validate_state`; none has its explicit schedule validation and Count uses its genuine loader. The common helper must retain the full current route, including saved Adam reconstruction configuration and exact post-load checks, rather than add a special NaN scan.

## Failure and lifetime limits

This operation is non-publishing, not literally side-effect-free: it allocates/registers owners and performs real managed native/RNG work. A semantic body rejection with successful actual completion preserves healthy receiver state under existing BANK admission behavior. A real completion failure must still poison the domain and preserve quarantine/uncertainty; never catch an exception class and certify safety. No new healthy retry guarantee covers genuine completion failure.

C remains unchanged: an actual failure after its `preparation_entered` marker and before completion stays uncertain and terminal. Preflight success cannot bypass any later guard, make a mutated payload trusted, refresh currency or authorize C. Existing true publication/completion failures and callback failures retain their original behavior.

Disposable cohort lifetime is a concrete integration check, not permission to alter core currentness. The validator must not retain candidates in runtime/BANK registries, and their intended lifetime must finish before subsequent authoritative preparation currency. Root/B owner must confirm the actual owner-lifetime route: delayed participant retirement after a real token is issued can legitimately invalidate it. No production GC sweep, peer pinning, token refresh or retirement exemption is proposed. The RNG-core body is outside this review budget; this is an explicit external fact to resolve during the bounded implementation review.

## Bounded review and verification criteria

- Original native corruption case rejects before C acquisition, preserves the original healthy-receiver assertions, and permits a corrected genuine restore/continuation. Do not relax or replace its assertions or relabel the R167 failure.
- Existing actual shared checkpoint2 → fresh restore → continued-learning witness still passes on the new exact candidate. Preserve R167's successful evidence with its original source scope; do not assign it to new bytes.
- Focused data-preflight control confirms no issued handle/outcome/receipt or live publication, unchanged selector/cadence/native history, and the same genuine producer rejection path. Cover the exercised NaN tail, with existing Adam/counter validation controls reused where applicable rather than a new acceptance programme.
- Existing B/C uncertainty, actual completion-poison and authority/currentness controls still pass. A preflight success followed by a real later preparation fault must not turn C's uncertain failure into healthy refusal.
- Source review confirms one shared native validation implementation, actual custody/idle registration/completion, no candidate retention beyond intended lifetime, and no changes to C's fence. Root supplies source-exact execution and custody evidence; this design report claims no test success or PW04 closure.

## Root-supplied lifetime resolution

After the proposal was drafted, root verified the existing public core route: `domain.unregister(participant=...)` requires a usable idle domain, no active invocation and no local CUDA gate; it removes actual membership and increments generation. Weak callbacks only queue retirement for a later idle operation. `WorldRNGState` and `_BackendOwner` expose actual `rng_participant`; owner adoption replaces the RNG registration with the owner participant and rewrites the input RNG's participant, while its lifetime-owner reference creates a cycle. These are attributed source facts, not additional bodies opened here.

Therefore use explicit, deduplicated retirement of the disposable cohort's actual currently adopted participants, after native admission exits and before later POP/world staging. Include partial cohort construction failure: track actual successful registrations/owners as construction progresses so a later failure does not leave earlier disposable members awaiting GC. Do not unregister a stale pre-adoption participant twice. On genuine poison, ordinary unregister is itself unavailable; preserve fatal uncertainty rather than bypass core checks or mask the original failure as healthy refusal. Existing real preparation keeps its cohort retention semantics unchanged; this cleanup belongs to validation-only disposable ownership.

Root's selected production ordering is immediately after outer metadata/counter checks and before POP plan or other staging. This resolves the external scheduling/lifetime question above without a new authority mechanism. B owner has the same core facts. The implementation must make the finite cleanup explicit; a plain local-reference drop is insufficient.

## Correction and R168 fixed-source review

Root subsequently corrected its initial lifetime capsule after tracing complete construction. **The previous paragraph's claim that construction replaces the original input RNG registration is wrong and superseded.** `OwnedWorldBackend.construct` forks the input RNG; that fork initially shares its participant, but the original input is the registered member owner. Adoption therefore does not retire the original registration; it registers a separate backend owner and rewrites only the fork. The original input RNG and returned owner are distinct live registrations. A factory failure before owner construction leaves the input registration live. Both must be explicitly retired, with actual participant identities deduplicated. This corrected fact was supplied to B before execution and is reflected in the inspected fix. No root/core implementation body was added to this review budget.

Fresh R168 source inventory is the same four bodies, **4706 lines**:

| Body | Lines | SHA256 |
| --- | ---: | --- |
| `config/exploration_policy.py` | 1495 | `18dc76f96ec6c31f4ef919277bc302a1fdd3d600db352c53858944a9e261ae15` |
| `exploration/scoped_curiosity.py` | 1623 | `3a3939d691bda6c43359ae6d1020e1106d6271c3fbb21e4159368278ddc0a79e` |
| `exploration/curiosity_checkpoint.py` | 1158 | `b45ba7627b50c123de36862a678a8db98d4ab074db23d296b6cd81a05d74b6c1` |
| `environment/restore_attempt.py` | 430 | `540e07c823ff8a3346080b2bf671cbbe83fa178390ea3934001650f1cb0092bd` |

**Disposition: no P1/P2 defect found in this bounded implementation review; execution qualification pending.**

- Runtime's actual `validate_restore_data` uses the existing operation wrapper, `_parse(initialization=False)`, pre/post revision checks and genuine BANK delegation. It never creates a prepared runtime handle/outcome, performs parent cadence correlation, or publishes selector/cadence. The existing C overlay admits only real preparation/install and therefore does not treat data validation as a C stage.
- BANK's actual method performs two `prepare` admissions around idle cohort construction. It calls the current preflight/origin/records validators and the shared `_populate_restore_cohort`, then verifies receiver identity. The same helper now serves ordinary `prepare_restore`, with its full archive/template/private/shared reconstruction, saved configuration, actual producer validators, gradient attachment and exact native roundtrip. Ordinary preparation still correlates real authority and seals its handle; data validation does neither.
- `_replacement_cohort` records each input RNG before private factory construction and each returned owner immediately afterward. It also records the archive RNG and shared reservation. `_disposable_cohort` deduplicates actual `rng_participant` identities and unregisters after the nested admission exits, on success or exception, including partial construction failure. Thus a successful eight-world private preflight should retire sixteen registrations; a second-world factory failure should retire the first input+owner and second input, three registrations. These are source-derived expectations, not observed results. Ordinary preparation passes `disposable=None` and retains its original cohort lifetime.
- Cleanup never grants authority or depends on GC. If body failure and retirement both fail, `BaseExceptionGroup` preserves both errors; a poisoned domain is not healed or called healthy. Actual BANK admission retains `_completion_uncertain` on failed completion and does not clear live failure flags. No exception-class waiver was added.
- C's inspected `_uncertain` predicate retains the exact preparation-entered/not-completed rule and existing installation-outcome requirements. No semantic weakening of that fence was found. No history pruning, tail normalization, token refresh, or install bypass appears in the additive route.

The external parent-custody method dispatch change is B-owner supplied: the new method is forbidden in bound custody. Its body is outside this four-body review. Root owns the runner ordering, execution and test bodies; those have not been independently inspected here. Native healthy-refusal and continued-learning qualification therefore remain pending exact R168 execution, alongside the focused disposal controls. This review does not upgrade R167 evidence to new bytes or close PW04.
