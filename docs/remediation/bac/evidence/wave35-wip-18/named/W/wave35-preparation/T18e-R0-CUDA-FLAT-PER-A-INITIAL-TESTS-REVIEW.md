# Packet A — initial constructor and CPU test review

2026-11-13. SPEC: PASS and QUALITY: PASS for the narrow initial test-source stage; no material findings. This approves root collection and causal baseline execution of these frozen tests, not whole-A implementation, CUDA integration, runtime results or production acceptance.

## Exact scope and seals

Root supplied R90 tree `8011596de86865f2d28457959ddb5fade90903d3`, manifest prefix `86cfef31`; these are attributed root identities, not independently obtained Git results. Measured the newly granted fourth body before reading: `tests/test_townlet/regressions/bac/test_replay_cuda_producer.py`, 321 lines, SHA256 `c1fd932e18638fd475360a4d31a0ff6c9c902611044f10df4dea0ca5d8725084`.

Read and hash-verified exact report `T18e-R0-CUDA-FLAT-PER-PRODUCER-A-REPORT.md`, SHA256 `7fee1d8de10c3f2481b16b45f1585e6a6eb7f3bb3120b9ff252755f182b40836`, and supplied diff `T18e-R0-CUDA-FLAT-PER-A-TESTS-R90-REVIEW.diff`, SHA256 `1b38acc7bae7a1488b0e7b431edc9d44d6b02252ebd852f0b69e80212182c876`. Diff contains precisely the new 321-line test body, with no production delta.

The previously reviewed production bodies' hashes still match:

| Body under src/townlet/training | Lines | SHA256 |
| --- | ---: | --- |
| replay_contract.py | 374 | 8de53fc6814a16bafb703728ed396d7b9a1298afdb415be4ec8d1d85ac1502a1 |
| replay_buffer.py | 728 | 817495558b45a51ba5df3751f83d1985135e23d9dfe6f827e3e323c45df01214 |
| prioritized_replay_buffer.py | 1164 | b989a8f153cf6a2686140efcfb6ce1d4914f4379785c2c094e1cc5d1142033b8 |

Total reviewed packet2587/four, within the planned3800/four and each body ceiling. RewardTensor exact constructor was consumed through the named prose capsule; no supplier implementation was added. No imports, runtime/probes, collection, lint, test execution, excluded helper/old-test/core/recurrent reads, source/test edits, Git actions, branches/worktrees, source copies or delegation. This review artifact is the only new authored file for this follow-up.

## Spec and fixture causality

The six constructor cases cover both actual concrete producers with CPU, dynamic CUDA and explicit cuda:3 selectors. Each invokes the real constructor, checks selector object preservation and emptiness, obtains the real lifetime participant, then authenticates it through the actual domain's empty device_operation. There is no fake domain, participant, policy, local contract or production return value.

_NoCUDA raises a specific AssertionError on CUDA API attribute lookup while allowing ordinary object introspection; absent dunder lookup follows AttributeError behavior. The monkeypatch is scoped inside each test so unwinding restores torch.cuda before pytest formats a failure. The sentinel observes CUDA module API access during the real method interval; it does not purport to prove arbitrary native CUDA absence. These admitted source bodies do not cache alternate CUDA API aliases that would bypass it.

Against current source, the four CUDA constructors are expected to fail inside actual construction: the two dynamic selectors at structural index rejection and the two indexed selectors at eager runtime validation. The CPU cases are positive controls. Root must confirm exact actual traceback causality; fixture/collection failures cannot count as constructor RED. This reviewer executed none of them.

The two CPU route cases use genuine dense tensors and exact RewardTensor arguments. Reward totals intentionally differ from optional components, masks include a terminal empty set, and presence columns are checked independently. The route sequence exercises actual push/readiness/serialization/validation/materialization/preparation/install/load/sample/clear paths with explicit lineage=None, issuer-produced handles and full serialized-state equality across current round trips. PER additionally exercises configuration ownership, physical and stable priority updates, the beta method, size, unconstrained push and real vocabulary declaration. The beta call covers its configured disabled branch; it does not claim enabled annealing coverage. Empty archive access is covered; nonempty archives are explicitly outside this initial group.

Tests retain the existing algorithms instead of substituting sampling outputs. Full-tree comparison checks tensor device/dtype/value, array dtype/value, mapping keys and recursive transport fields. The CPU state-restoration fixture snapshots Python, NumPy global and CPU Torch state before each test and restores them in finally; it performs no CUDA RNG snapshot. Global custody revisions are not fabricated/reset by the fixture.

## Independent sampler oracles

The two flat adapter cases seed the CPU default Generator directly, copy its initial state into a distinct CPU Generator, and derive expected indices from one independent randperm. They check actual sampled rows, typed receipt indices/conditional probabilities where applicable, exact final CPU Generator state and unchanged global NumPy state. Direct default-generator seeding avoids torch.manual_seed's CUDA-facing behavior inside these CPU controls.

PER direct sampling with an owned sampler and PER typed external sampling independently reconstruct a RandomState from the global initial state and perform one vectorized without-replacement choice with literal equal probabilities. Returned indices/rows and exact global continuation are checked; the direct case also checks the configured owner's sampler state remains unchanged. This matches the source-qualified global primitive and guards against silently rerouting direct sampling to the configured private Generator.

PER owned typed sampling uses an independently seeded Generator, enumerates the first four-member support and the second three-member residual support, and makes two explicit choices. Literal probabilities1/4 and1/3 and beta0 unit weights are correct for these equal insertion priorities. Expected indices, conditional probabilities, stable IDs, rows, private final state, unchanged caller Generator state and unchanged global NumPy/CPU Torch states are checked. The production sampling helper is not used to calculate expectations.

These are valid finite stream/continuation controls. Equal-priority beta0 cases do not qualify general nonuniform weighting, all RNG engines or complete distributional equivalence; neither the narrow grant nor report claims that scope. No mutation-sensitivity experiment or runtime PASS is inferred from static source review.

## Prospective collection and retained obligations

Parametrization yields the report's13 prospective cases: six constructors, two CPU route cases, two flat stream cases and three PER stream cases. Expected baseline is four constructor REDs plus nine healthy controls. Actual collection, static checks and runtime outcomes remain root-owned and unverified here.

All requirements in `T18e-R0-CUDA-FLAT-PER-A-PREFLIGHT-REVIEW.md`, SHA256 `8de4fd87215961891b937be110c0000e123e1fee3644ebae2f49d77ae3a6876c`, remain carried forward to later test/implementation grants: F1 local-versus-generic completion semantics; F2 REQUIRED outer-parent outcome/quarantine ownership handoff based on actual owner/device reachability; F3 branch/no-op/empty-path laziness; F4 independent input/storage/candidate/archive devices and inventory before copying; F5 causal completion exclusion, mutation currentness and clean failed-preparation preservation. No child outcome boolean closes F2, and no blanket quarantine or generic cleanup change is authorized.

Dynamic selection, nonempty GPU archives, retained/staged/source inventories, local activation, completion uncertainty, nested/preflight lifetime and real asynchronous one-/two-device behavior remain unwritten/unqualified at this initial stage. Authentic B activation, paired core/existing-test update, parent integration, final-byte review/CPU evidence and hardware gates remain mandatory. No programme count, B6 acceptance or production approval changes.
