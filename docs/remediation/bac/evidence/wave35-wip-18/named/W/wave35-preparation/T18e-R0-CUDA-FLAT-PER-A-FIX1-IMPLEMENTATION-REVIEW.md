# Packet A implementation FIX1 review — R96

Verdict: **SPEC / QUALITY: CHANGES REQUIRED.** I5 is only partially repaired; two new assignment-type errors also require repair. This is a bounded source review of I1–I7 and the exact FIX1 delta, not packet A acceptance or CUDA qualification.

## Frozen inputs and scope

Base: `9acd85d3ccd897051288a13fd16e610b9ee1fca1`. Root candidate tree: `1c1c35cc064c0a13163b25fb02faa767839c2fcd`; supplied candidate manifest SHA-256: `c50b8ab162e6a65dd8af390ded131c9df8b77bb7edd1c21ff2d6cedd0203c0ef`.

The four admitted bodies total 4310 lines, within the 4450-line grant and hard 5-body/5000-line ceiling. Reviewed source hashes:

| Body | Lines | SHA-256 |
|---|---:|---|
| replay_contract.py | 683 | `169ed9e0c19f37b85f543b9e8a76f158821ea0f75edf37c7f2ef6b0e3d1fea0a` |
| replay_buffer.py | 804 | `b041535d46b33c91886430dae34babbbab3ea3e12991cd6fd2a8e8202ded698a` |
| prioritized_replay_buffer.py | 1257 | `78b741358019d75a6685fd0593cc0a7a03b6768e5be69921e55481bece26f536` |
| test_replay_cuda_producer.py | 1566 | `d352385e8adcda59bf98c11747e4cab5eacf40142ce7ee4bd86a68773c1e332f` |

Exact R95→R96 diff: `T18e-R0-CUDA-FLAT-PER-A-FIX1-R96.diff`, SHA-256 `00f3b26898d9b38d68b034f81d61f0198a8169907b27f678771502fce5c387a7`. Prior implementation review `T18e-R0-CUDA-FLAT-PER-A-IMPLEMENTATION-REVIEW.md` remains unchanged. No runtime, imports, Git, source edits, additional implementation bodies, or delegation were used for this review. Excluded helper/core/parent behavior remains supplier-qualified rather than independently re-reviewed.

## Finding dispositions

| Finding | FIX1 disposition |
|---|---|
| I1 installed archive preparation inventory | Addressed in source: raw preparation includes installed canonical archives, whose stored slots are borrowed for metadata traversal. Actual public preparation/install/completion proof remains B-dependent. See I5 for paths that must refuse before using these archives. |
| I2 accepted Mapping sources | Addressed in source: traversal accepts Mapping, including the accepted MappingProxyType transport. Public CUDA validation/preparation completion remains owed. |
| I3 DTO metadata clone sources | Addressed in source: flat/PER DTO and candidate traversal includes all dataclass fields; PER sampler configuration is traversed. This covers metadata cloned during reconstruction before validation, not only row fields. Downstream runtime remains owed. |
| I4 unarmed Tensor comparison/truth and diagnostic rendering | Addressed in source: exact version type checks precede comparisons; DTO target selection checks integer type before positivity. The test now preserves informative version repr and requires its GPU work inside genuine completion. This follows the root's R95 I4 ruling; it does not require rejected inputs to perform zero work. Public completion proof remains owed. |
| I5 unused CUDA on early refusal | **Partially addressed, still open**, with concrete residual witnesses below. Rank refusal with CPU prefix is executable and repaired; capacity/unready public B-dependent checks are not established by the reachable run. |
| I6 same-owner reentry before domain acquisition | Addressed in source: same-thread active replay scope is rejected before domain admission. Root reports all four real reentry controls pass. |
| I7 static gate | Original no-defaults failure repaired according to root's unchanged-defaults600 PASS. **New fix-diff type failures remain**: shared lines 263 and 297 assign device-or-None to `effective` inferred as device. Repair the annotations/control flow without suppression or ratchet changes. |

## Required repair: residual I5 source inventory

### Capacity refusal still scans sources never touched by the real validator

Flat inventory lines 181–185 and PER lines 241–245 build `(state, *retained, self._historical_archives)` for raw preparation. `_transport_target` suppresses the target on capacity mismatch but does not suppress unused source values. Direct validation similarly returns the whole state as inventory.

Concrete route: a CPU owner with no outstanding prepared handles receives a supported-version, correct-kind, exact-key-set raw transport whose plain integer capacity differs from the owner, and whose observations value is CUDA. This is a real early-refusal path: flat `_validate_serialized` checks version, key set, kind, then capacity at lines 564–584; PER checks version, kind, key set, then capacity at lines 932–959. Both raise the capacity error before row tensor work, archive reconstruction, or materialization. The CUDA observations value is never touched by the actual body. Nevertheless the planner finds it and enters CUDA custody before that refusal. Thus this witness does not depend on creating or installing GPU archive state, and is suitable for an independent planning regression.

The analogous preparation path with an already installed GPU archive and CPU capacity-mismatched input also inventories that archive although validation refuses before archive merging. It needlessly resolves/enrolls/completes the source; it need not newly initialize CUDA if prior legitimate installation already initialized it. This is not the explicitly accepted conservative inventory of issuer-held prepared candidates: the witness has no such handles, and concerns ordinary input and installed archives.

Required correction: make source inventory follow the known validation prefix, as well as suppressing the unused target. Preserve sources actually used by refusal diagnostics or earlier work. In particular do not undo I4 by dropping malformed version Tensor sources whose repr is genuinely rendered under protection. Do not change accepted transport semantics or invent a replacement validation order.

### Bad plain-push observations still inventory untouched dones

Shared `_push_inventory` lines 135–139 unconditionally returns `(dones, next_action_masks)` when observations fail rank/dtype/width checks. For plain `push` with `action_dim is None`, flat lines 302–318 and PER lines 523–530 create no masks, then `_validate_push` rejects malformed observations first (flat 267–268; PER 483–484). CUDA `dones` is untouched on this path, yet the planner resolves it. A CPU owner, bad-rank CPU observations, and CUDA dones therefore exposes the remaining no-unused-CUDA failure even though the existing CPU-prefix rank controls pass.

Required correction must distinguish the route and vocabulary state. Plain push with a known action vocabulary really allocates masks on the dones device before observation validation; recorded push really validates successor masks before `_push`. Those actual prefix effects must retain coverage. Do not generalize the plain-push exception to these branches.

These are incomplete repairs of existing I5, not a new project-wide inventory requirement. The first is not cured by `_transport_target`; the second is introduced by the new shared prefix approximation within the I5 repair.

## Bounded regression and verification obligations

1. Add paired flat/PER pure-plan controls with CPU owner, no prepared handles, correct raw schema/kind/version, plain mismatched capacity, and unused CUDA observations. Assert no selected CUDA target or source. Preserve an actual public validation assertion of the original capacity error without CUDA work after correction; keep public admitted preparation and authentic installed-archive scenarios for B-enabled execution.
2. Add paired flat/PER plain-push controls with `action_dim is None`, malformed observations, and CUDA dones. Assert the actual original refusal and no unrelated CUDA effect, with normal mutation bookkeeping preserved. Retain paired coverage for known-vocabulary and recorded prefixes that genuinely touch dones/masks before refusal; do not suppress fixture events.
3. Repair both `effective` assignment types and rerun owned production type checking. The missing `AmbientRNGDomain.device_invocation` attribute is an explicit B dependency, distinct from these two A assignment errors. Do not manufacture or ignore the B API to make A checks appear green.
4. Rerun the narrowly affected source/test gates and reachable controls after the fix. Preserve all public downstream assertions currently blocked on B; private plan assertions are supplementary evidence, not completion/quarantine proof.

## Evidence and staged limits

Root-supplied R96 results: 113 tests collected; four owned files Ruff/Black PASS; unchanged global defaults600 PASS. Reachable16 PASS with zero skips/warnings: constructor6, rank early-refusal2, same-owner reentry4, standalone archive fixtures2, untouched-extra-key direct validation2. Root reports sequential source/config/protected/registry/import/thread/index custody verified. Reachable log SHA-256: `a7b603018c2d6bbdf7a50ca8cec1e18050e307333de744b445e979ed1f67b2e8`. These results are attributed to root, not independently rerun here.

Root's subsequent owned-three-production mypy gate failed with three errors: two new `effective` assignments at shared lines 263/297, and the known absent B `device_invocation` at line 307. Root reports static custody PASS; owned-mypy log SHA-256 `0553ba68837631ca49daa88c2c1ca5abae03fcfb57b755b9a1dfdd42ea7715c2`.

B contract constants, policy activation, and per-invocation completion API remain required dependencies. No B-dependent runtime or poison child was rerun. Ten poison children, strict verifier/tool activation, real failure identity/order, completion/quarantine before owner unlock and peer behavior, parent outer-failure handoff, and hardware qualification remain explicitly owed. Source sufficiency for repaired I1–I4/I6 does not close these runtime gates. Stage A remains unaccepted pending the finite repairs above and the subsequently authorized integration evidence.
