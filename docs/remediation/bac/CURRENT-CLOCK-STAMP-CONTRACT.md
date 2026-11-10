# Current public curiosity clock/stamp contract

Implemented and source-verified public data primitives in world_curiosity_state.py. Final R4 tree 0918ce2f973b15e987fd943898ae92d39c1801c8 passed150 joint cases/2CUDA skips in38.5783s wall and fresh independent65 cases/1CUDA skip in16.5833s. These selections overlap and are not summed. Actual-source specification/quality reviews PASS after the typing and current-owner-fixture repairs. Covering current authored compile/EF/native/scope roundtrip passed in15.5241s. This is a bounded producer handoff, not integrated bank/service/retry or full BAC acceptance. CUDA behavior remains unqualified.

Historical R1 tree fc9be745ab293003ab8f69a8ad7dd52c23a48f2a collected96 and passed joint94 /2 CUDA SKIP /0 warnings in14.1006s wall, with191 source/573 config/13 artifact/4 process/index/import/Torch1/registry custody PASS. R1 CLI PASS in139.66098s wall remains historical evidence, not an R2 CLI result. R1 source quality required the narrow typing/style repair described below; the current fixed hashes supersede that candidate.

## Source custody

| Path | Lines | SHA256 |
| --- | ---: | --- |
| src/townlet/exploration/world_curiosity_state.py | 847 | ec3cf8ded83f952ca4c1993b084b2ee0c7f1e611bf172ab31830ecfdc27f352d |
| src/townlet/config/exploration_policy.py | 768 | af8843ec1a270cfa49ec44b7ac5615d33db0d4d16b2d169d161bb4a1cd402c8c |
| tests/test_townlet/regressions/bac/test_pw_rng_domains.py | 798 | 5e671b5693eb3741424b1fadb098eca6ea3d5f51599dddc1513c1f2292847848 |
| tests/test_townlet/regressions/bac/test_pw_clock_stamp.py | 316 | bffc26fff70116ac18d3cc43fa6c73c747c0e5ae7779abf077646aa0116a1a1e |

Exact4/2729 actual lines; ceilings1500/800/1100/1000 total4400, hard5/5000. Only WS changed in production, adding113 lines between existing KDF and descriptor without new imports/defaults/helper source. RP and existing RNG regression remain unchanged. Adopted proposal SHA2565251388f5ad7c0328b6be4825be595e4b3f8fafd2271f1babd6618ded8bac0f0 defines this ABI. Fixed R2 source and final R4 owner-fixture reviews passed independently.

## Exact public ABI

All arguments are required. ServiceClock and CuriosityEventId accept ordinary positional or keyword dataclass construction; stamp is keyword-only.

```python
@dataclass(frozen=True)
class ServiceClock:
    unit: Literal["vector_tick", "world_eligible_admission"]
    position: int

@dataclass(frozen=True)
class CuriosityEventId:
    curiosity_epoch: int
    world_id: str
    world_episode_seq: int
    eligible_seq: int

@dataclass(frozen=True, init=False, eq=False)
class CuriosityStepStamp:
    __hash__ = None
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

ServiceClock and EventId have value equality/hash and frozen fields. Stamp has identity equality and hashing disabled: hash(stamp) raises TypeError. It provides no tensor equality/content hash, serialization, mutable cursor, service operation or receipt cache.

The actual __hash__=None assignment carries a narrowly documented `# type: ignore[assignment]` for its deliberate incompatibility with Python object's inherited hash protocol type. Runtime unhashability and identity equality remain unchanged, and the hash(stamp) raises TypeError assertion is preserved among all64 new cases. The new test received Black formatting only. No general typing/style/default guard or suppression policy changed; root's actual R2 mypy confirms the owned error closed while7 required consumer errors remain.

ServiceClock.unit must be an exact str with one of the two literal values. position must have type int and be>=0. Units remain distinct at equal position. EventId requires exact ints with curiosity_epoch>=0, world_episode_seq>=1, eligible_seq>=0; world_id must be an exact nonempty str. bool, float and NumPy integer aliases refuse. Strings retain exact whitespace/case/Unicode without normalization. Python integer scalar domains are unbounded; stamp tensors remain int64.

## All-row stamp validation and tensor ownership

Both sequences must be exact nonempty tuples of equal length N>=1. world_ids must contain unique exact nonempty strings; every event_ids element must be an exact CuriosityEventId, and all rows must share a curiosity_epoch. Unequal per-world episode sequences are valid immutable data; reachability/authentication belongs to ENV and the live bank.

Tensor arguments must be Tensor instances with dense strided layout, shape(N,), matching exact CPU/CUDA device and dtypes int64/int64/bool respectively. Noncontiguous strided inputs are supported. Meta/sparse/other device layouts, wrong shapes/dtypes and mixed devices refuse. No casts, broadcasting, device transfers or flattening occur. CPU construction never queries/initializes CUDA runtime.

After geometry/type checks, constructor detach().clone()s each tensor into local owned candidates. Candidate episodes must be>=1, eligible sequences>=0, and each eligible=True row must have eligible_seq>=1. For every row, EventId world/episode/eligible contents must exactly equal ordered world_ids and tensor contents. Oversized standalone Python integer IDs cannot silently wrap into int64 stamp correlation. Only after complete batch validation are any fields published. Every tensor property returns a fresh detached clone, preventing supported input/output access from mutating stored state.

Malformed contract inputs raise ValueError. Allocation/device failures propagate. No caller tensor, existing stamp, provider state, global RNG or live cursor is mutated on constructor refusal. Inputs must remain quiescent during construction. Frozen Python fields/private storage provide cooperative ownership, not protection from arbitrary introspection or object.__setattr__. Raw reward/scale ownership belongs to the later reward result.

## Initial, inactive, reset, resume and explicit clone handoffs

These are required live-owner semantics, not implemented lifecycle operations of the data types:

- Fresh curiosity epoch is0. ENV's pre-acceptance episode cursor0 has no EventId/stamp. First successful actual ENV acceptance supplies episode1; no row/batch/tick-derived substitute authenticates it.
- At an accepted episode's start, episode-local eligible cursor is0. First actual eligible admission receives1, subsequent eligible admissions increment by1. An inactive row retains its current local cursor, including0 before any admission or a positive previous admission cursor thereafter. Its eligible=False remains authoritative: equal ID to a prior active row creates no new admission/service opportunity or retry receipt.
- Ordinary reset consumes the actual newly accepted episode identity, resets episode-local eligible cursor0 and retains learned parameters, optimizer/tail/RNG and cumulative service position. Ordinary resume preserves epoch, accepted identity and all eligible/service cursors unchanged.
- Required explicit current-format conversion/evaluation cloning uses source epoch+1, clears active last-event caches, starts episode-local eligible cursor and cumulative service origin0, and retains the actual restored world episode identity. Inherited learned/history counters are template data, never active inherited dedup IDs. Source artifacts remain preserved. This bridge adds no clone/conversion API, obsolete-format decoder or compatibility mechanism.

ENV remains sole accepted world/episode authority. The current implemented v4 world/VFS producer receipt supersedes historical v3/VFS scalar statements; no ENV/VFS source was reopened here. Fresh INITIAL world/RNG snapshots can legitimately have accepted cursors0 without fabricated event stamps.

## Consumer limits and dependency handoffs

Current readonly IntrinsicTransitionContext still has only owned predecessor/actions/successor/active_on_entry/vector_tick; no world-ID or stamp field exists. Actual context/caller migration remains separately bounded. It must carry all-row stamps and correlate N/device/order/actual eligibility with the actual transition and exact accepted ENV token. Existing dependency is WS→RP. A future RP→WS stamp consumer must avoid a reciprocal module-initialization cycle, using a bounded local runtime import with TYPE_CHECKING annotations or another explicitly reviewed cycle-safe arrangement, while retaining runtime stamp validation.

PW04 must consume ServiceClock through explicit service-at-clock APIs and native unit/position/budget validation. Shared vector_tick cadence remains supported; private opportunities depend on own eligible admissions. The primitive clock does not check monotonic history, idle-service opportunities, lawful provider unit switches or current quotas. Genuine current private learning and supported shared behavior remain required.

Future bank owns accepted-token authentication, actual eligibility, current epoch/episode/eligible/service cursors, phase order and bounded receipt state. It must validate the entire batch before mutation, admit only the next phase event, replay an immediate equal-last-content receipt without mutation and reject changed-content/expired/out-of-order retries. None of those live behaviors is implemented or qualified by these constructors. Existing RNG/OwnedWorldBackend behavior is retained; this bridge does not claim complete provider-native semantic validation.

Known RP legacy policy payload/projection/from_dict and stale scope-origin work belongs to its actual owners under AGENTS.md's explicit no-compat ruling. This bridge supplies no fallback and does not repair readonly consumers. PW04 provider/POP native coherence, real bank routing/learning/completion, actual ordinary-runner scalar/native-format9 consumer, native-parent checkpoints, family/restart/E2E and final BAC acceptance remain OPEN. No new defect in uninspected source is asserted.

The separately bounded current-only scope fixture adds tests/test_townlet/regressions/bac/test_pw_scope_contract.py,250lines,SHA25606f8a23deea73de495ee0adc427317386dc1e75487fb2bd6eb7496ed9214b295. Final author/reviewer inventory is5/2979 actual lines, ceiling5/4900. Historical native1.41 artifact hashes/provenance remain preserved DATA; current compiled loading refuses them. Standalone obsolete EF missing its required static_policy refuses specifically with KeyError(static_policy); parent compiled old-schema refusal remains ValueError. All later current1.42 authored compile/EF/native identity, provider/scope/seed and options assertions are retained. No adapter or artifact conversion was added.

Five non-mypy global guards pass. Compiler CLI actually passed at fixed R2 in136.22438836097717s; final R4 changes only the owner test, and src/config/scripts subtrees are byte-identical. This is explicit input-equivalence reuse, not a claim of an R4 CLI rerun. Final R4 Ruff/Black/defaults/expression-doc guards pass; Black55.5770s. Global mypy still fails with7 required oracle/POP caller errors and zero owned diagnostics. Source/fixture/process custody passes192 source hashes,573 configs,13 protected artifacts and the unchanged14-entry worktree registry (MAIN1available). All runtime sessions closed before publication. Full acceptance obligations above remain open.
