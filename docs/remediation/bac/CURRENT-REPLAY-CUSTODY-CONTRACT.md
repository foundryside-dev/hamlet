# Shared and flat/PER replay custody — R81 source contract, R84 status

Current recurrent behavior and R84 CPU component evidence are documented in the [recurrent replay custody contract](CURRENT-RECURRENT-REPLAY-CUSTODY-CONTRACT.md). The shared and flat/PER interfaces below retain their R81 source basis. R84 supersedes this document's historical pending recurrent-B/defaults/style work; CUDA, owner/caller integration and programme gates remain open. See [BAC status](STATUS.md) for current gate outcomes.

2026-11-13. This capsule records the bounded fixed shared-contract/flat/PER producer at R81 tree `4bcb26ec56bc2664949baab7d6b14e3c1da76b01`, base `678513c7540a61114d59a17d1b1e0eb8a06ce0a2`, manifest SHA256 `f16cff139bc7caeb8e4dab7adf995ad5f52f16ca7b058c710bc41f428b8fa80e`. It supplements the historical Stage B capsule, which is preserved unchanged. It is not whole-replay, CUDA or programme acceptance.

The author directly inspected exactly these five admitted whole bodies; final lines/hashes were rechecked before this prose handoff, total3735:

| Path relative to /workspace/hamlet | Lines | SHA256 |
| --- | ---: | --- |
| `src/townlet/training/replay_contract.py` |374|`8de53fc6814a16bafb703728ed396d7b9a1298afdb415be4ec8d1d85ac1502a1`|
| `src/townlet/training/replay_buffer.py` |728|`817495558b45a51ba5df3751f83d1985135e23d9dfe6f827e3e323c45df01214`|
| `src/townlet/training/prioritized_replay_buffer.py` |1164|`b989a8f153cf6a2686140efcfb6ce1d4914f4379785c2c094e1cc5d1142033b8`|
| `tests/test_townlet/regressions/bac/test_replay_rng_custody.py` |1098|`5870d5315dd6f975f6e9513a492ba08f84671576f18e70f62795b122e13eabd7`|
| `src/townlet/exploration/rng_custody.py` |371|`9d6cd6fcfe62d8e53bda1e6ce7b34a89454ccc88373b5ec4cd072fe004ad66fb`|

## Directly inspected public interfaces

`lineage` below always means `RNGOperation | None` and is a **required keyword**. Explicit `None` requests standalone admission; nesting requires the exact authentic still-active issuing-thread outer operation. There is no omitted-argument default, implicit lineage lookup or separate domain. Construct/enroll owners at idle before an enclosing parent operation; registration is not permitted inside an active operation.

| Method | Flat ReplayBuffer | PrioritizedReplayBuffer |
| --- | --- | --- |
| constructor | `ReplayBuffer(capacity: int, device: torch.device)` | `PrioritizedReplayBuffer(capacity: int, alpha: float, beta: float, beta_annealing: bool, device: torch.device)` |
| direct sample | `sample(batch_size: int, *, lineage) -> dict[str, torch.Tensor]` | `sample(batch_size: int, *, lineage) -> dict` |
| typed sample | `sample_batch(request: ReplayRequest, *, lineage) -> UniformReplayBatch` | `sample_batch(request: ReplayRequest, *, lineage) -> PrioritizedReplayBatch` |
| validate DTO | `validate_serialized(state: Mapping[str, Any], *, expected_obs_dim: int) -> _ValidatedReplayState` | `validate_serialized(state: Mapping[str, Any], *, expected_obs_dim: int | None) -> _ValidatedPrioritizedState` |
| issue from DTO | `materialize_validated(state: _ValidatedReplayState, *, lineage) -> PreparedReplay` | `materialize_validated(state: _ValidatedPrioritizedState, *, lineage) -> PreparedReplay` |
| issue from transport | `prepare_serialized(state: Mapping[str, Any], *, expected_obs_dim: int | None, lineage) -> PreparedReplay` | same arguments/result |
| install | `load_prepared(candidate: object, *, lineage) -> None` | same arguments/result |
| load with mode | `load_for_mode(state: Mapping[str, Any], *, requested_mode: history.AccessMode, lineage) -> None` | same arguments/result |
| ordinary load | `load_from_serialized(state: Mapping[str, Any], *, lineage) -> None` | same arguments/result |

Both provide `rng_participant: RNGParticipant` for actual registered lifetime ownership. Readiness, length/stats, serialization/validation and historical reads take the owner guard; push/push_recorded, clear, historical installation and PER configuration/priority updates take owner mutation exclusion. These owner-local interfaces do not acquire common admission or need new lineage arguments. Existing data/geometry/legality validators still apply.

The shared guards use modern function-local `Owner: ReplayCustody`, `Result`, `**Arguments` parameters, preserving complete method signatures. Read/mutation/sample preserve result types; preparation transforms the internal material return to actual public `PreparedReplay`. Runtime `functools.wraps` metadata still exposes the internal preparation declaration's `object` result; static decorated API typing exposes `PreparedReplay`. Root's R81 three-family `assert_type` check verifies that static result, and owned-four mypy including recurrent passes. `Any` in transport values is not callable-signature erasure. Missing lineage raises TypeError before admission; actual supplied lineage still undergoes sole-domain authentication.

## Preparation, currentness and ownership

Flat/PER validation DTOs are data, not authority. Materialization first reconstructs and owns the complete DTO representation, then reruns the actual full serialized validator under domain-before-owner exclusion against current target geometry and content. A managed clear/repopulate width change cannot promote stale destination validation into fresh authority. Caller-mutated invalid tensors, successor legality, PER priorities or stable IDs cannot acquire prepared authority. Legacy payloads remain genuine archival history under existing mode rules; current payloads retain active rows and their validated legality mode. PER captured5 adapters and sampler metadata retain their existing supported semantics.

`PreparedReplay` is identity-only with a weak-reference slot. It has no material-taking public constructor, payload field or material getter; construction/reinitialization and copying/serialization refuse. Only the issuer creates a registered identity. Its private weak registry binds owner revision, core current token and owned material together. Fabricated, copied, foreign, consumed or stale identities cannot install. A caller possessing the normal handle cannot rebind its material.

Preparation issues inside actual registered `prepare`; install enters actual registered `install`. Both acquire the sole process domain before the owner RLock. Same-held authentic outer prepare→install and released prepare→later install are supported subject to the source-qualified core revision/generation/currency rules. Intervening ordinary sibling sampling, owner mutation or other invalidating domain work stales a candidate. The handle is not an ambient snapshot or a portable restore permission.

Install stages all fallible archive merges/validation, tensor/array copies and PER Generator reconstruction before final issuer/owner revision/current-token checking, then publishes already staged references. Installed bytes do not alias input or retained candidate material. Success consumes the identity once and advances owner revision. A clean prepublication failure preserves live replay data; a refused admitted operation can legitimately stale other released currency, so a subsequent healthy positive attempt needs fresh preparation. An exception after publication begins quarantines the owner rather than claiming rollback. Quarantine blocks guarded samples, preparation/install, clear and serialization; local clear cannot heal it.

Common poison refuses actual sample/preparation/install admission. Healthy owner-local reads/ordinary data mutations may remain available under the accepted finite boundary; they do not heal poison or certify permission to resume. Diagnostic `status()` is not admission and must not be acquired under a replay owner lock. Existing raw public tensor/array aliases and callback-bearing extensions retain their cooperative quiescence/supported-profile limits.

## Preserved sampling and device boundaries

Flat retains selected-device Torch randperm. PER direct sampling retains its global vectorized NumPy route, even when configured with a private Generator; qualified PER retains its selected legacy/global versus owned-Generator law and exact engine/state/origin transport. No algorithm, seed, stream checkpoint, receipt, readiness, history mode or sampling capability was removed by A.

CPU registration uses empty device inventory without CUDA queries. A makes no CUDA semantics change. The current shared source still rejects unindexed CUDA and requires initialized indexed enrollment at construction: this is the retained B6 capability/lifecycle defect, not an approved replacement contract. Ordinary lazy/unindexed CUDA support and owner-lock versus asynchronous device-completion lifetime require their separate design/implementation/hardware packet. R81 CPU evidence does not discharge them.

## Historical R81 recurrent supplier boundary and handoff

This section records what remained at R81/WIP15. Its “next slice B” work list is historical and is superseded by the [R84 recurrent contract](CURRENT-RECURRENT-REPLAY-CUSTODY-CONTRACT.md). Keep the original R81 source/review/results below as evidence for that checkpoint; they are not current pending-B claims.

No recurrent implementation body was read in A. Its exact public signatures were supplied by the original bounded source owner: `prepare_serialized(self, state: Mapping[str, Any], *, expected_obs_dim: int | None, lineage: RNGOperation | None) -> object` internally under `@replay_prepare`, and `load_prepared(self, candidate: object, *, lineage: RNGOperation | None) -> None`. Both keywords are required. The shared decorator's public transformation yields `PreparedReplay`; root R81 static assertions independently verify that result for flat/PER/recurrent, and retained recurrent runtime controls pass. These are supplier/static/runtime interface facts, not an A inspection of recurrent internals.

**Next slice B must assess recurrent returned mutable DTO validity/current-target issuance under original B1.** Shared identity repair and passing retained recurrent controls do not prove recurrent malformed-DTO rejection or complete unchanged-state refusal. B must also complete recurrent-specific B4, B3's real disposable-generator support classification/ambient and persistent preservation, the actual recurrent ASG002 default ratchet601>600 and recurrent formatting. Scratch support is ambient-free/persistent-preserving work with a real disposable draw, not literally RNG-free. It must not be silently removed or moved into an owner-to-domain lock inversion.

The scoped independent R81 review `T18e-R0-REPLAY-FIX-A-PRODUCTION3-REVIEW.md`, SHA256 `49741e76e1f77fc71ff7a176945b170eb17660a496fbd2d37613f96011b47178`, approves SPEC/QUALITY only for B1 flat/PER, B2/B5 shared and flat/PER/shared B4. Root53+poison1 and independent53+poison1 pass at exact R81 bytes; repeated runs are the same54 controls. Root verifies source/process and actual child PID/PPID custody. Global Ruff, owned Black, owned-four types and all-three public result assertions pass. R79 global mypy15 (oracle6/POP9) is source-bound prior caller evidence, not a fresh R81 global result or migration completion. B6, callers, broader suites and final fresh programme reviews remain mandatory; accounting stays28/38/66.
