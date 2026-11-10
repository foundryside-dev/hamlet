# CLOCK-STAMP public primitive ABI proposal

Status: design capsule only, ready for root's fresh Astra-medium review. No implementation, tests, runtime/import/formatter/Git/index operation or PASS is claimed. Read-only inspection stayed inside the three existing authorized source/test files; only this named ignored document was written. Root retains integration, original66task/release and final BAC acceptance obligations. This completes a missing PW02 public data handoff before PW04; it introduces no bank, reward result or lifecycle coordinator.

## Exact inventory and custody

| Path | Current lines | SHA256 | Binding ceiling | Role |
| --- | ---: | --- | ---: | --- |
| src/townlet/exploration/world_curiosity_state.py | 734 | 8b242ef58af2840c069db3d599606ba4760eea675e6be5bf00d8eb89c23b5b82 | 1500 | later modify |
| src/townlet/config/exploration_policy.py | 768 | af8843ec1a270cfa49ec44b7ac5615d33db0d4d16b2d169d161bb4a1cd402c8c | 800 | readonly |
| tests/test_townlet/regressions/bac/test_pw_rng_domains.py | 798 | 5e671b5693eb3741424b1fadb098eca6ea3d5f51599dddc1513c1f2292847848 | 1100 | readonly |
| tests/test_townlet/regressions/bac/test_pw_clock_stamp.py | reserved, not opened/created | no implementation hash claimed | 1000 | later create |

Existing inventory: 3/2300; complete reserved inventory: 4/4400 ceilings. Hard 5 files/5000 lines and each named ceiling remain binding. No extra helper, probe, source or executable wrapper is authorized. Brief and producer documents are prose receipts, not additional implementation inspection. No repository revision was independently resolved with Git.

Consumed receipts: CURRENT-WORLD-IDENTITY-CONTRACT.md (historical constructor/lifecycle v3); wave18 CURRENT-WORLD-VFS-CONTRACT.md (implemented current v4, superseding stale VFS/v3 statements); wave16 PW04-READINESS-report.md; wave05 PW02-interface-capsule.md and PW02-phase2-work-report.md. Their attributed runtime results are predecessor evidence, not executions for this bridge.

## Public signatures in world_curiosity_state.py

All constructor arguments below are required. No aliases, inferred defaults, legacy decoder or fallback. Fields appear in the stated order.

```python
@dataclass(frozen=True)
class ServiceClock:
    unit: Literal["vector_tick", "world_eligible_admission"]
    position: int
    def __post_init__(self) -> None: ...

@dataclass(frozen=True)
class CuriosityEventId:
    curiosity_epoch: int
    world_id: str
    world_episode_seq: int
    eligible_seq: int
    def __post_init__(self) -> None: ...

@dataclass(frozen=True, init=False, eq=False)
class CuriosityStepStamp:
    event_ids: tuple[CuriosityEventId, ...]
    world_ids: tuple[str, ...]
    _world_episode_seqs: torch.Tensor
    _eligible_seqs: torch.Tensor
    _eligible: torch.Tensor

    def __init__(
        self, *, event_ids: tuple[CuriosityEventId, ...],
        world_ids: tuple[str, ...], world_episode_seqs: torch.Tensor,
        eligible_seqs: torch.Tensor, eligible: torch.Tensor,
    ) -> None: ...

    @property
    def world_episode_seqs(self) -> torch.Tensor: ...
    @property
    def eligible_seqs(self) -> torch.Tensor: ...
    @property
    def eligible(self) -> torch.Tensor: ...
```

ServiceClock and CuriosityEventId keep ordinary frozen-dataclass value equality/hash. Stamp deliberately uses identity equality, avoiding ambiguous tensor-generated equality; no stamp hash, tensor ordering, iterator, dictionary serialization or content-fingerprint API is introduced. Future receipt owner compares complete owned context content using its explicit protocol. Frozen Python/private attributes provide cooperative in-process ownership, not protection from arbitrary introspection or object.__setattr__.

## Strict domains and first/inactive representation

ServiceClock.unit requires exact str and exactly one of the two declared literals. position requires type(value) is int and >=0: bool, floats including 0.0, NumPy integer scalars and aliases refuse. Equal positions with different units remain distinct values. The type neither advances a cursor nor approves a service opportunity, regression, unit switch or replay.

CuriosityEventId requires exact ints: curiosity_epoch>=0, world_episode_seq>=1, eligible_seq>=0. world_id requires type(value) is str and nonempty. IDs are preserved byte-for-byte in Python string terms: no strip, Unicode normalization, row/name/batch/tick-derived substitute or case folding. Whitespace and canonically distinct Unicode strings are legal distinct identities.

Fresh bank epoch is 0. Fresh ENV accepted-episode cursor is 0 before acceptance; **there is no CuriosityEventId/stamp for an unaccepted episode**. First actual ENV acceptance supplies episode sequence1. Primitive validation does not fabricate or authenticate acceptance. Runtime must correlate the exact accepted token/world binding before publishing a stamp. EventId's eligible_seq0 is an explicit no-admission-yet marker, needed because every accepted context includes inactive rows; it is not a service event.

At each accepted episode's start, the later bank's episode-local eligible cursor is0. A first actually eligible row receives eligible_seq1; successive actual eligible rows increment by1 within that accepted episode. An inactive row retains its current episode-local eligible cursor (0 before its first eligible admission, otherwise the latest positive cursor) and has eligible=False. Thus an inactive row can share an EventId with a previous active row; it must never be processed as an admission or replay solely because its ID compares equal. Only eligible=True identifies an admitted phase event. Epoch/episode/world/eligible sequence together distinguish admitted events; phase and payload belong to the future bank receipt protocol.

Ordinary reset consumes only ENV's new accepted episode identity and resets the bank's episode-local eligible cursor0. It retains learned parameters, optimizer/tail/RNG and cumulative service position. Resume preserves epoch, accepted identity and all local/service cursors; it does not rebase them. New conversion/evaluation-clone APIs are outside this bridge. No obsolete-format conversion is authorized.

## Complete stamp validation and ownership

Require exact nonempty tuples for both sequences, equal length N>=1, each world ID exact nonempty str, no duplicates, and each event ID an exact CuriosityEventId. All rows share one curiosity_epoch. Mixed episode sequence values are allowed: only ENV knows reachable histories, and no first-element or full-roster-equality inference belongs here.

Require all three inputs to be torch.Tensor instances, dense strided layout, concrete CPU or CUDA device (no meta/sparse/other device path), rank1 and exact shape(N,). world_episode_seqs and eligible_seqs must be torch.int64; eligible must be torch.bool. All three must share exactly the same device. No casting, broadcasting, device transfer, flattening or coercion. Noncontiguous strided inputs are acceptable and cloned into owned storage. CPU construction never probes/initializes CUDA. Actual CUDA tests remain a hardware gate.

Check the entire batch before publishing fields: every episode tensor value>=1, eligible sequence>=0, and eligible=True implies eligible_seq>=1. For each row i require event_ids[i].world_id==world_ids[i], event_ids[i].world_episode_seq==world_episode_seqs[i], and event_ids[i].eligible_seq==eligible_seqs[i]. Correlation is exact, ordered and covers inactive rows too. Int64 tensors bound stamp sequences to representable nonnegative signed64 values; standalone EventId/clock Python integers are unbounded. Larger IDs cannot silently wrap into a stamp.

First validate types, tuples and geometry, then detach().clone() the three inputs into local candidates, then validate candidate values/correlation and publish all fields with object.__setattr__. This checks owned values and publishes no partial stamp; callers must keep inputs quiescent during construction. Properties return fresh detached clones on every access. Tuples contain frozen immutable values. Tensor repr/dataclass field inspection is not a public mutation API; internal underscore tensors must never be returned by supported accessors. No raw reward/scale/RMS ownership follows: those belong to the later reward result.

All malformed semantic/type/domain/shape/dtype/device/layout/correlation inputs raise ValueError, consistent with existing primitive validators. Allocation/device failures propagate their underlying exception. Failures do not mutate caller inputs, any existing stamp, RNG globals, provider state or bank state. Construction performs no provider callbacks or cursor changes. No test should assert rollback after arbitrary future live callbacks; their quarantine/transaction semantics belong to their actual owner.

## Live authority and consumer handoffs

The future bank owns accepted-token authentication, epoch/current episode/eligible/service cursors, phase ordering, serialization, eligibility correlation with actual context and bounded last receipt. It validates the **whole batch** against those authorities before any mutation. It admits only the next phase event, returns the bounded equal-last-content receipt without mutation for an immediate lawful retry, and rejects changed-content, expired and out-of-order retries. Inactive rows cannot create opportunities or dedup-cache entries. These rules are required later; adding immutable data does not implement them. No new live coordinator is proposed.

PW04 consumes ServiceClock through current explicit admit_and_service_at(..., clock=...) APIs and native checkpoint unit/position validation. Shared vector_tick cadence remains a real supported choice; private cadence uses cumulative own eligible admissions and idle rows create no opportunities. Provider checks own lawful unit/position/budget semantics before mutation; the clock object alone has no history. Existing shared and genuine private learning stay supported, with real mutable predictors/Adam, never frozen-parameter qualification. Public stamps are available to later routing; PW04 must not claim bank dedup from a stamp constructor test.

Readonly RP source confirms IntrinsicTransitionContext currently owns predecessor/actions/successor/active_on_entry/vector_tick only, with detached input/output clones. No stamp/world-ID field exists. A separately bounded actual context/caller migration must carry these exact all-row stamps and correlate N/device/order/actual eligibility with that context and ENV accepted identity. This bridge does not modify RP or infer a sixth source. accepted ENV sequences are consumed directly; current v4 VFS receipt is authoritative for identity transport, not a grant to inspect ENV/VFS/provider/runner.

Known readonly RP consumer work remains: legacy policy payload recognition/projection/from_dict fallback and legacy scope-origin paths are present. AGENTS.md owner no-compat ruling requires their actual owners to remove obsolete APIs and update callers/tests together. This bridge neither repairs them nor endorses preserving them. Ordinary runner current scalar/native-format9 consumer remains OPEN per producer receipts; no native runner/bank/full BAC result is implied.

Existing WS descriptor/KDF/WORLD_SEED_COMPONENTS, RNG activation/snapshot/restore, global restoration failure custody and OwnedWorldBackend construction/call/prepared restore behavior remain unchanged. Preserve their genuine learning/ownership guarantees and retained artifacts; do not add adapters or claim provider-specific validation is complete.

## Finite tests-first matrix

After fresh technical review root clears tests-only in the one reserved regression. Initial runtime requires separate root clearance and frozen source/config/process custody. Use assertions on missing public attributes before exercising behavior, so initial RED identifies absent promised ABI rather than collection/import/config failure. Root records the actual failure cause. No runtime was executed to draft this matrix.

| Causal control in test_pw_clock_stamp.py | Positive witness | Refusal/ownership witness |
| --- | --- | --- |
| test_service_clock_strict_typed_units | both units,0 and positive positions; unequal units at equal position | bool/float/NumPy-int/negative/unknown and nonexact string unit; frozen assignment |
| test_event_id_initial_and_exact_identity | epoch0/ENV episode1/local0; whitespace/distinct Unicode; positive sequences | negative epoch/local, episode0, aliases, empty/nonexact ID; no normalization; frozen fields |
| test_step_stamp_first_eligible_and_inactive | accepted episode1 with local1 active/local0 inactive, then inactive positive retained; unequal episodes | active local0; bad inactive correlation; mixed epochs; duplicate world IDs |
| test_step_stamp_all_row_order_and_geometry | N>=1, permuted whole correlated rows remain distinct valid bindings | mismatched order/content/length; list inputs; empty batch; late-last-row invalidity; rank/dtype/layout/device/malformed non-tensor |
| test_step_stamp_owns_inputs_and_outputs | noncontiguous inputs; mutate original and every accessor result independently | stamp retains pristine tensors/order; outputs detached and independently stored; frozen field assignment |
| test_primitive_refusal_has_no_external_effects | valid construction under captured Torch/Python/NumPy ambient state | invalid last row leaves all inputs, previous stamp and ambient states exactly equal; no bank mock claiming implemented dedup |
| test_step_stamp_cuda_ownership_when_available | genuine CUDA tensors retain device and clone independence | CPU/CUDA mixture refuses; record SKIP when absent, never CPU-promote to CUDA PASS |

No bank/service retry simulator or new helper source is needed. Put fixtures/helpers only inside the reserved test and count its full lines. Standalone IDs test arbitrarily large Python ints; stamp test rejects attempted overflowing/mismatched correlation rather than coercing it. Tensor domain tests include negative episode/local, int32/float/bool aliases and last-row mismatches. Check all tuple elements, not only the first.

Root's exact new-suite command after runtime clearance: `uv run pytest --no-cov -p no:cacheprovider tests/test_townlet/regressions/bac/test_pw_clock_stamp.py -q`. Then production confined to WS, same GREEN command, readonly test_pw_rng_domains.py owned regressions, required static/default guards and fresh other-model review at frozen candidate. Root chooses authorized full/joint gates. No legacy-suite edit, guard weakening, prior-source PASS substitution or runtime fanout is included.

## Findings and limits

Confirmed gap: current WS exports no ServiceClock, CuriosityEventId or CuriosityStepStamp. Current RP context has no stamp. PW04's required local clock boundary therefore lacks its promised public primitive producer today. Existing WS ownership/RNG implementation is present; earlier prose calling those entirely absent is historical.

Required later work: ENV-token authentication and actual first-event allocation; real context migration; bank cursors/phase/receipt retry semantics; PW04 native local cadence/provider/POP integration; actual runner/native-format9 and final acceptance. These are not optional extensions or solved by typed immutable data.

Optional extensions excluded: portable stamp schema, generated content hash, arbitrary equality API, new conversion/clone lifecycle, cross-device continuation or a second transaction controller. Refuted inference: an immutable EventId cannot itself prove an accepted ENV event or implement dedup; equal inactive IDs do not identify new admissions; a typed ServiceClock cannot itself enforce monotonic service. No new defect in uninspected provider/runner source is claimed.
