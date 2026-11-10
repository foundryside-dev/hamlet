# Owned native metadata — tests-only handoff

Status: authored only; no runtime/import/collection/compile/pytest/probe executed. Production WS/RND/PF/RP byte-frozen. Root retains execution and production authorization. No extra source slot, repository/source copy, index/commit, branch/worktree, or subagent used.

## Exact bounded inventory

| Slot | Lines | SHA256 | Named ceiling |
| --- | ---: | --- | ---: |
| WS src/townlet/exploration/world_curiosity_state.py | 871 | a639d6f927492cf0334a49f330f514b6472be75f624f24a2f1b5e8381af93b2c | 1100 |
| RND src/townlet/exploration/rnd.py | 834 | 0848cfe8f08635fac6843d90bdf38ca7c08f92ef8220d7859e2ce65dae4ecf0d | 900 |
| PF src/townlet/exploration/provider_factory.py | 153 | 7ca30733720017eea4a8063be0261dfd365c9547f501649bd71d937eecd5efb0 | 200 |
| RP src/townlet/config/exploration_policy.py | 768 | af8843ec1a270cfa49ec44b7ac5615d33db0d4d16b2d169d161bb4a1cd402c8c | 800 |
| NEW tests/test_townlet/regressions/bac/test_owned_native_metadata.py | 313 | 3b1c6408835b43239afa920eca51d03ac82c0219caf3d7b01fc347c934ef1dbb | 2000 |

Five whole sources, total2939/5000 named ceiling. Four production sources total2626 unchanged. Prose read: owned brief, AGENTS, wave29 ordered-native gap and owned-call witnesses, wave25 provider APIs and actual ENV fixture API (compilation/policy public facts only), wave28 fixture APIs and provider-native facts. No CP/BANK/adaptive/ICM/Count/EPS/oldtest/helper implementation read.

## Authored fixture and causal targets

Actual UniverseCompiler token_set_smoke/L0_test/use_cache=False supplies typed training and drive; actual resolver chooses rnd/adaptive_rnd. Data from approved wave28 fixture capsule: B2/E4/LR.001, private world native-world, training seed731, paced budget1/capacity4/drop_oldest. Actual PF and WorldRNGState create both direct native controls and OwnedWorldBackend construction. Direct native is created within model_init activation. Service uses genuine private eligible admission clocks3 then4, positive learning, RMS update, pending last row and next-update gradients. There is no fabricated learning algorithm or validator. Callbacks return state/primitive witnesses, never backend/module/optimizer objects.

Root prerequisite nodes (same new file):
- test_real_factory_emits_ordered_native_metadata_and_learning_tail[rnd]
- test_real_factory_emits_ordered_native_metadata_and_learning_tail[adaptive_rnd]
These should establish genuine factory/schema/metadata/learning/queue/validator controls before interpreting RED. Compilation is module-scoped; no CUDA access/qualification.

Root initial causal RED nodes:
- test_owned_callback_preserves_actual_native_mapping[rnd]
- test_owned_snapshot_preserves_native_metadata_order_and_tail[rnd]
Both record/obtain actual native OrderedDict before asserting mapping kind across owner copy. Intended assertion is explicit "native network mapping kind was lost at the ownership boundary". Adaptive variants exercise actual nested RND via public .rnd without reading adaptive source.

Additional finite nodes:
- test_prepare_install_real_native_resume_learning_and_rng[rnd|adaptive_rnd]: native input bypasses owner snapshot loss by taking direct provider checkpoint; genuine native validate/prepare/load/install must reach installed type/metadata equality; input independently owned, installed source mutations isolated, continuation tail consumed, model/Adam/RMS/native/RNG/next-update gradients equal. Residual pre-load gradients expressly outside this owner's promise.
- test_real_native_validator_rejects_order_or_metadata_only_mutation: both families x transport_order/candidate_metadata. First calls genuine candidate.validate_state, then changes only network entry order OR genuine Torch module version metadata. Expected guard ValueError "validation mutated". Baseline can ignore these because _owned drops metadata and _same ignores entry order. Candidate/module mutation is off-side; original input and installed destination values remain exact.
- test_callback_numeric_recursive_metadata_is_independently_owned[rnd|adaptive_rnd]: narrowly authored OrderedDict nested metadata with Tensor, NumPy array/scalars, tuple/list; detached/independently-owned callback output and metadata. This is generic copier evidence, not arbitrary custom native model schema load support.
- test_observation_revision_stales_prepared_handle_without_changing_state[rnd|adaptive_rnd]: actual prepare succeeds, pure snapshot invalidates handle; exact native/RNG values remain equal. Every observation's revision effect is intentional. Continuation test also rejects consumed installed handle.

Expected authored collection is16 nodes (seven test functions, one double parameter); root must collect to confirm. Expected baseline four controls PASS and twelve guarantee failures is a static expectation only, not evidence. Global Python/NumPy/Torch streams checked around every test, including exceptional paths. Pure destination observations establish explicit baselines outside preparation, not false mutation claims about revision.

## Static verification performed

Scoped .venv/bin/black --check and .venv/bin/ruff check on ONLY the new test: both successful. Black formatting and Ruff import sorting applied to ONLY the new test. SHA/line inventory read by shell. No runtime commands performed.

## Minimal prospective repair, pending causal RED

WS._owned needs narrow OrderedDict preservation before generic Mapping normalization: insertion order, recursive entries, optional recursively owned _metadata. WS._same must observe exact OrderedDict order and optional recursive _metadata presence/value. Ordinary generic Mapping/list/tuple/dataclass/Tensor/NumPy/RNG/quarantine/revision semantics remain the source contract. Native provider validators/loaders and PF/RND/RP remain unchanged. No equality relaxation, provider algorithm alteration, metadata stripping, gradient promise, legacy loader or hardware scope proposed.

Root must freeze/collect/run genuine prerequisites and intended RED before any WS production baton. Independent Astra review plus owner suites/static guards and actual PW07 RND/adaptive integration remain downstream acceptance work.

## WS-only production handoff after root's genuine causal RED

Root explicitly authorized WS-only production after reporting16 collected, two real-factory controls PASS, and full16 with four PASS/twelve genuine RED (eight actual OrderedDict/metadata-loss assertions and four actual validator-impurity DID NOT RAISE), zero fixture errors. Those are root-reported execution results; this worker performed no runtime.

Only src/townlet/exploration/world_curiosity_state.py changed:871->883 lines, SHA256 cb8a7fd9f27c73537ec3f18f37b6cd5a3d88ca23c281b76376cece8be5f9dfb1. Twelve added lines import OrderedDict, copy ordered entries and optional recursively owned _metadata before the existing generic Mapping branch, and compare ordered keys plus optional recursive metadata presence/value before generic Mapping equality. The existing exact-type comparison remains. Other Mapping/list/tuple/dataclass/Tensor/NumPy/RNG/quarantine/revision/prepared-handle paths remain unchanged; no provider validator or algorithm change, fallback or equality relaxation.

Stationary five-source production-handoff inventory: WS883/RND834/PF153/RP768/newtest313, total2951/5000. RND/PF/RP/newtest hashes remain exactly as recorded in the initial inventory above. Main CP/BANK/test were neither read nor edited. Scoped .venv/bin/black on WS reported unchanged and scoped .venv/bin/ruff check on WS passed. No runtime/import/collection/compile/pytest/probe/index/commit/push/copy/subagent/branch/worktree operation performed by worker. Root owns GREEN, independent Astra review, existing owner suites/static guards and coherent main PW07 execution. The initial tests-only inventory is retained as the pre-production phase record, superseded for WS by this handoff.
