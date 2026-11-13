# Packet A — R94 implementation source review

2026-11-13. SPEC: CHANGES REQUIRED. QUALITY: CHANGES REQUIRED. Seven finite findings below need one bounded fix/review round before B consumes A as its activation source. Missing B constants/device_invocation are separately acknowledged staging dependencies, not defects to hide with fallbacks. No production or runtime approval.

## Exact packet and evidence

Measured before source reads: replay_contract596 SHA256 `5b9001092323c777228bedadccedb9b6dcb8e64d705dd5292b7f126ee485ca66`; replay_buffer805 `1c6000e1938e58de0bf77d92be9dc9cff00f4ef8aa454f613c8ff41993b2a0fd`; prioritized_replay_buffer1253 `9d34c07e117c27b37842ec4a99d17c12e71c198e7ab13e36ebfd43f2374cee6f`; retained unchanged focused test1389 `c450390e461b0828c33189c176d8ea3c6f6161e95fec68fefa33db1b5bdd0ab3`. Total4043/four, hard5000/five. Actual production seals and supplied diff `2b6a495759fbb71445bf29e3195b638f769052523226f6c31a84ff5021d7553e` match.

Read final author report SHA256 `431b41aa512ec673e243794688a1f766cdb04cfd15317be997011d0b5dfd2206`. Root supplies R94 tree `b95a43f214939024a1b6a64fbdaa35634194e3db` and manifest `2a2a7898ea31e8254d086c83963c3030b68d1b43572fe214b2e7c87601ab2245`. Root reports88 collected, Ruff/Black PASS, constructor6 PASS, and two minimal probes failing specifically on missing device_invocation / REPLAY_BUFFER_PUSH_RECORDED_CUDA. Root reports custody verified and no active process. Those are attributed root results; no runtime or Git/custody audit was repeated here. The missing dependencies prevent downstream probe assertions from being executed.

This context retains only the same four bodies. No excluded core/recurrent/parent/helper/old-test/linter implementation, application import, runtime, source/test edit, Git action, source copy or delegation. Public core/outcome/archive/reward/sampling contracts remain supplier boundaries. This review artifact is the only authored file.

Below C/F/P mean the sealed shared/flat/PER files under src/townlet/training. Findings describe ordinary source-observable paths, not speculative real-GPU results.

## I1 — raw preparation omits installed archive sources

**High; F177–189, P237–249 versus F698–753/P1120–1199 and each _merge_archives.** prepare_serialized plans the supplied mapping plus retained row fields, but does not include self._historical_archives. The real materializer always merges/copies already installed archives, including the legacy/archive-only branch. materialize_validated does include them, so the two public preparation routes have inconsistent coverage.

Concrete witness: a CPU owner with a legitimately installed GPU-backed historical archive, no issuer-held candidate, and CPU current transport whose historical_archives list is empty. Raw preparation's plan can be entirely CPU/empty while _merge_archives clones/digests the installed GPU archive. Its source is absent from the invocation tuple and can escape completion even after B exists.

Required fix: include the installed archive sources on every actual raw preparation merge path, without adding them to pure validation paths that do not touch them. Regression target: both families, retained archive source3 distinct from input/target, current and archive-only preparation as applicable; verify actual copies occur under the declared scope and source3 completes. Preserve full live data and original currentness semantics.

## I2 — accepted Mapping transport can be invisible to inventory

**High; C113–119/C130–145 and F177–189/P237–249.** The family planner accepts Mapping, checks its version/key set, then passes the Mapping object to the collector. The collector descends only exact dict/OrderedDict/list/tuple. A standard MappingProxyType over a valid plain transport therefore passes the planner's schema checks but contributes no tensor devices. The unchanged public validators accept this Mapping and clone its row tensors; helper clone facts likewise cover Mapping inputs.

Concrete witness: CPU owner/destination, valid MappingProxyType transport with ordinary CUDA row tensors. validate_serialized can choose the owner-only CPU path and perform GPU reductions/clones; prepare_serialized can omit source devices. No arbitrary custom callback is needed to demonstrate this gap.

Required fix: inventory the actual known accepted mapping fields/ordinary mapping views, preserving the accepted cooperative limits for custom protocols. Silently ignoring a supported value container is not a purity boundary. Do not newly reject accepted Mapping inputs merely to make inventory easy. Regression target: both families' valid direct validation and preparation on the mapping view, real output/refusal semantics, exact source-device completion, and no fake local policy. Any broader custom-hook purity claim remains excluded.

## I3 — malformed DTO non-row fields are copied but not inventoried

**High; F142–151/P192–201 versus reconstructed mappings at F704 onward/P1127 onward.** Family DTO traversal includes storage columns, archives and legacy_state only. The materializer reconstructs and recursively clones more fields before content validation: position/size/geometry and, in PER, priorities/unit_ids and other scalar metadata. DTO type annotations/frozen field rebinding do not establish content validity; materialize_validated exists to revalidate data, not trust it as authority.

Concrete ordinary witness: obtain a valid DTO, use dataclasses.replace to make position an ordinary CUDA scalar Tensor while leaving size and rows valid, then materialize it. The reconstruction includes position, history._clone clones it, and only subsequent _require_int rejects its type. Current collector misses that source entirely. A PER priorities Tensor replacement supplies another concrete clone-before-refusal case.

Required fix: reflect the complete ordinary data that this reconstruction actually copies, including malformed values touched before refusal, while preserving original validation order/errors. Do not treat malformed DTO metadata as authority or add unsafe truth conversion during planning. Regression target: both-family position replacement plus the PER extra copied field if needed, source distinct from rows/target, clone-before-refusal coverage, no issued handle/publication, unchanged live state, and exact completion.

## I4 — planning itself performs Tensor work before arming

**High; F182–186/P242–246.** Both planners compute the key schema using version == 4 (and PER also == 5) before checking type(version) is int. A malformed dense CUDA Tensor in format_version invokes tensor equality and truth conversion during the initial owner-only metadata plan, before a local gate or admitted invocation is armed. The original validators first short-circuit on the version's exact type and reject without performing that tensor work.

The materialize target expression also truth-tests state.size/state.size_current without first establishing scalar type, which can execute malformed DTO Tensor truth conversion before the body has made its owned copy. This is the same metadata-versus-effects ordering defect; do not repair one expression while leaving equivalent unarmed truth tests.

Required fix: perform safe structural/type checks before any comparison/truthiness that can dispatch tensor work, letting the original validation produce its normal error. Regression target: raw format_version Tensor for both families with an unarmed-work sentinel and unchanged runtime/live state; malformed DTO size must not be truth-tested before its actual clone/validation scope. These are ordinary malformed data values, not an arbitrary-object sandbox requirement.

## I5 — unused selected target can bootstrap before metadata-only refusal

**Medium; F154–198/P204–261 feeding C177–182/C208–213.** Target planning presently treats a nonempty push or a syntactically keyed nonempty current checkpoint as enough to resolve the selected device. It does not account for already-determinable early metadata refusal.

Concrete witness: create ordinary populated CPU transport, use a different target capacity, set the destination selector to uninitialized cuda:3 and call prepare_serialized. The planner selects CUDA from positive size; resolve_cuda can initialize it before the original validator rejects capacity, which occurs before any input clone or destination allocation. A rank-invalid nonempty CPU observations argument in push similarly selects an unused CUDA target before its first shape/dtype refusal. A CPU retained unconstrained batch that cannot be ready also needlessly selects the new CUDA target before _readiness refuses.

Required fix: respect the finite early metadata-only rejection/no-allocation branches before resolving a target. Do not demand that all data-dependent failures be predicted without executing their properly armed validation; distinguish that case from these source-obvious structural refusals. Regression target: both-family CPU payload/capacity mismatch and rank-invalid CPU push under fail-on-CUDA sentinel, preserve original errors and owner mutation rules, no target bootstrap. Existing untouched-extra-key tests cover only one early-refusal branch and do not close this finding.

## I6 — admitted reentry guard comes after domain acquisition

**Medium; C158–161 compared with C199–205.** _local_operation rejects the current thread's active replay scope before seeking domain custody. _device_operation instead enters domain.admission first and reaches its reentry check only in _owner_operation. A forbidden same-owner callback from a CPU-local body can therefore acquire/wait for domain while already holding the owner lock. With a peer holding domain and waiting for that owner, this is the domain/owner inversion the design forbids, even though the call would eventually reject if it obtained both locks.

This does not claim arbitrary callbacks are pure or supported lifecycle operations. The accepted protocol explicitly requires unrelated lifecycle reentry refusal, and the source already maintains the issuing-thread scope needed to refuse it before acquiring a new domain gate. Ordinary declared helper reuse has been moved to private _readiness and needs no public-admission bypass.

Required fix: apply the same active issuing-thread rejection before admitted domain entry, retaining explicit lineage checks and allowing intended sequential nested calls after the earlier invocation scope ends. Regression target: an observed CPU-local body seam attempts same-owner sample/prepare and verifies rejection before the domain admission call is requested. An observation-only admission hook can make this deterministic without creating hanging threads or replacing authority. Keep the normal same-parent sequential prepare/install positive control. Do not reinterpret the parent preflight ordering contract as permission for owner-first admission.

## I7 — required no-defaults gate is failing

**Required quality gate; root execution evidence.** Root reports ASG002 at C178/209 ternary assignments and allowed-pattern count620 versus the established600 ratchet, with the gate currently stopping at the two unwhitelisted cases. Ruff/Black PASS does not close this check. The author report acknowledges the failure.

Required fix: repair the source forms and rerun the unchanged actual guard. Do not raise the ratchet, expand a whitelist, add fallbacks or weaken the guard. A subsequent count failure must also be resolved at source; stopping after the first two diagnostics is not acceptance. No excluded linter body was read or is needed to report this observed failure.

## Boundaries that the implementation correctly expresses

The family-specific initializer opts flat/PER into empty CUDA-free registration while preserving the public selector. The base initializer/current full-member guards remain for the unread recurrent consumer; no automatic family-wide migration or missing-method fallback was introduced. The detached PER archive validator still bypasses custody and calls undecorated validation; it does not allocate through the new effective-device property.

The18 route-name bindings match the accepted capsule. Strings select fixed core-owned exported constants; they are not caller-issued contracts. Absent constants are looked up lazily only for CUDA local routes. Actual B canonical-class/route policy and post-poison permission still require their separate reviewed activation; this producer does not fabricate them.

For a correct inventory, the shared nesting retains the actual owner guard through local complete or device_invocation exit, outcome inspection and _quarantine_replay. The entered flag avoids reading an outcome after entry failure. The original body/completion exception behavior is delegated to the authentic core, not guessed by exception comparison. Mutation revision increments, original issuer payload/revision/token storage, final post-staging validation, handle consumption and partial-publication quarantine remain intact. Same-object completion collision therefore has a proper planned outcome path, conditional on B's actual API.

Effective-device use is invocation-local at the changed allocation/transfer sites, and installed candidate tensors are still cloned on their own devices. Sampling algorithms remain flat randperm, PER direct global-vectorized and qualified owned/external Generator laws. Private _readiness reuse avoids opening a public local gate from inside an admitted scope. Metadata-only routes retain owner-only exclusion.

Preflight pins passed owners strongly, authenticates participants through no-op enrollment, takes one domain gate, resolves planned selectors before final owner locks, acquires locks in stable id order and holds them until its caller's parent has exited; ExitStack releases in reverse order. Actual retained/issuer enrollment is done while those locks are held. This source shape does not establish the still-owed multi-owner/lineage/unwind controls or parent outer-failure ownership response. No parent/core source was read to claim those facts.

## Fix and qualification handoff

I1–I6 need finite regressions at final source; existing R92/R93 tests do not cover these exact new counterexamples. Only11 lines remain under the current test ceiling, and54/45/47 under current production ceilings. Root must explicitly reslice/regrant as needed before growth; do not compress controls or move code into uncounted helpers. The hard five-body/5000 bound remains. This review proposes no additional implementation body or open-ended audit.

Constructor6 PASS establishes the previously failing constructor stage at these bytes. Minimal missing-B probes are honest prerequisite failures; no full repeat into those absent APIs is requested. After A fixes and independent re-review, B still owes actual named contracts, canonical resolution/cache policy, adopted device_invocation, paired core/existing-test review and final-byte integrated CPU controls. Ten poison children remain UNRUN until those prerequisites and strict custody exist. Parent outer-failure ownership, real one-/two-device CUDA and programme gates remain required; no accounting or capability waiver follows.
