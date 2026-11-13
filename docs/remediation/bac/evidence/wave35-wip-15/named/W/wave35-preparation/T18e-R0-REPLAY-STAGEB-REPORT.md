# R0 replay Stage B — producer code authored, execution pending

2026-11-13. This is a bounded five-body producer slice in the existing checkout at HEAD `678513c7540a61114d59a17d1b1e0eb8a06ce0a2`. Root owns source capture, execution, independent review and consumer integration. **No application imports, tests, probes, compiler, formatter, lint, Git or index action was run by this author.** Final hashes/line inventory are recorded at freeze below. The original R73 source-bound actual bypass RED, R74 API/prepared RED and R75 healthy fixture evidence remain historical; none is relabeled GREEN for this new code.

## Source and invariant map

| Existing body | Authored change and protected invariant |
| --- | --- |
| `replay_contract.py` | Replay-specific common custody owner: real weak participant, exact indexed-device registration, domain-before-owner RLock, owner revision/health, opaque `PreparedReplay` issuance with core token, real issuer/revision/current/one-use check, uncertain publication quarantine. Shared read/mutation/sample/prepare guards. |
| `replay_buffer.py` | Real direct and qualified flat Torch sample admission, owner reads/mutations, staged cloned flat restore and required lineage on domain-entering sample/prepare/install/load methods. |
| `prioritized_replay_buffer.py` | Real direct global NumPy and qualified global/local PER sample admission, priority/configuration/storage owner guards, preserved local Generator transport, staged cloned PER restore. Private archive validator avoids a new domain registration inside a held owner operation. |
| `sequential_replay_buffer.py` | Real direct/qualified uniform Python and qualified local priority sample admission, storage/tick/priority owner guards, preserved recurrent local Generator transport, staged cloned episode/priority/policy restore. Private archive validator avoids held-domain registration. |
| `test_replay_rng_custody.py` | Migrates only this new packet's domain-entering calls to explicit lineage; retains all healthy and causal observations; adds a distinct isolated `replay_poison` child consumer refusal with child-owned replay import paths/PPID and parent PID/queued PID pairing. |

Selected algorithms, receipts, captured legality, readiness and transport formats are unchanged. A conservative common lease encloses locally generated qualified sample branches without converting their owned RNG to ambient state. The source directly shows RNG-free owner-local leaf logic and only owner RLock/revision on reads/storage/configuration/priority/history; the source-qualified helper capsule covers ordinary builtin dense archive helpers, with no claim about arbitrary external callbacks or aliases. Per the accepted poison-boundary ruling, owner-local leaves do not pretend that diagnostic `status()` provides atomic global poison exclusion. Domain-entering sampling/preparation/install are genuinely poison-fenced; a local quarantined owner refuses every guarded operation. Raw public tensor/array/deque aliases require caller quiescence.

Prepared restore creates a producer-issued opaque handle only under registered `prepare`. For each load, fallible validation, archive merge, array/tensor/episode/Generator/policy cloning and compatibility checks finish under domain and owner exclusion before the final core token/owner revision authentication. The remaining publication closure assigns already staged references; any unexpected partial assignment quarantines. Successful publication consumes the handle and advances owner revision. Clean foreign/stale/used refusal has no live mutation. Native/full outer joint publication is outside this replay slice.

## Actual public API and caller migration

The accompanying `T18e-R0-REPLAY-CUSTODY-API.md` lists exact producer methods. All flat/PER `sample`, all three `sample_batch`, recurrent `sample_sequences`, `materialize_validated`, `prepare_serialized`, recurrent `prepare_for_mode`/`prepare_archived_import`, `load_prepared`, `load_for_mode` and `load_from_serialized` now require keyword `lineage: RNGOperation | None` where they enter common domain work. Standalone direct callers explicitly pass `None`; a genuinely nested caller passes the current authentic operation. These are breaking signatures, consistent with the pre-release no-compatibility rule. Readiness, serialization and RNG-free owner-local storage/configuration/priority methods remain direct owner-only calls, without gratuitous lineage parameters. Existing POP/runner/serving/manual/outer caller migrations are **not** claimed in this five-body source packet; root's separate owner inventories and actual source reviews must update their call sites before integration acceptance.

Each real replay constructor registers at idle after known device fields. CPU registration uses `()`. CUDA needs an explicit indexed initialized device and remains hardware-unqualified. A parent must construct/register replay before entering a held operation; no registration is attempted under a parent lease. Domain registration/operation kinds are actual `sample`, `prepare`, `install` calls, not labels. The core owner separately source-qualified both released-prepare→install and same-still-held-outer nested prepare→install token checks; an ordinary nested sibling after prepare advances currency, while an ordinary call still inside an open inner prepare may not, so owner revision/exclusion remain necessary. No implicit ambient lineage lookup or default `None` is used.

## Runtime, source and remaining gates

Tests and static checks are **UNRUN by author**. Root should capture the exact frozen five bodies, collect/import, execute existing healthy controls and causal nodes, then test the isolated child only after a separate verifier admits `replay_poison`, its four replay import paths and PID/PPID pairing. The old verifier rejects that role, so no child PASS is claimed. The child calls genuine public `domain.poison` with its own active lease, proving a consumer refusal only; it does not simulate a restoration/setter failure. Root's independent actual-source review, full caller lineage transport, applicable CUDA, broader suites, poison restoration cases, outer all-child publication and final R0/B1/programme gates remain open. Original accounting stays 28 qualified/38 remaining/66 total.

## Frozen five-body inventory

Read-only `wc -l`/SHA256 at author freeze (no runtime/source execution):

| Whole body | Lines | SHA256 |
| --- | ---: | --- |
| `src/townlet/training/replay_contract.py` | 352 | `eb40cf7a78d0ddec538a05649b34ddb2c5521dc1ac8f68de3319344b0fd73b7a` |
| `src/townlet/training/replay_buffer.py` | 715 | `85a30028b21a2400fbbe43f82ac7422a20320c7173535a4e3bfcb342a81e29b3` |
| `src/townlet/training/prioritized_replay_buffer.py` | 1142 | `6d0fd54102363bb89b27590fef3e97ccdca3de6dbdce214c0c4b1219759b2bc0` |
| `src/townlet/training/sequential_replay_buffer.py` | 1884 | `b29a5be9b48c99180ef64730802f041cf4536b30b8771d2ad945ceca7569bad6` |
| `tests/test_townlet/regressions/bac/test_replay_rng_custody.py` | 684 | `e70c17a0e79497a06cef3c78f4b09fc8a2310401d8a39bffec5d1d4d2d892ab2` |
| **Whole five** | **4777** | Hard cap5000;223 lines of headroom. |

Compared with Stage A, production gained130/38/50/69 lines in the four respective bodies; the test gained97 lines, including explicit caller migration and the isolated child. The distribution differs from provisional per-file ceilings but remains under the actual whole-five hard budget. The helper capsules were consumed as public prose; no sixth source body was read by this author. **CODE AUTHORED, TESTS/STATIC UNRUN; source frozen for root capture.**
