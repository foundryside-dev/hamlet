# Per-invocation CUDA completion outcome — proposed additive design

Status: PROPOSAL; pending independent peer review and explicit root adoption. Designer: `/root/bac_astra_cuda_core_review`. No implementation approval, source edit or execution is implied.

Scope: retained core821/test1409 (2230 lines), existing public contracts and supplier capsule `P/T18e-R0-CUDA-OPERATION-COMPLETION-OUTCOME-FACTS.md` SHA256 `871cdf42` prefix. Core identity `0a0f19d37ac85b1584ea028e7e7268a04d18e9f39db0e41b9780181913aae477`; test identity `b044538dfe656976c0171d81fae4c3d44bba9b47f8b5072d846cfe2d9acf962e`. No new implementation body, runtime/import, Git/index, branch/worktree/copy or delegation. This is a bounded use of the brainstorming skill; root has requested a concrete proposal, not implementation or a programme restart.

## Need and chosen mechanism

The producer must distinguish completion failure for its own invocation while still holding its mutation lock. The current exception surface cannot do this: body error E plus synchronization error using that same E deduplicates to the same object as body-only E. A retired standalone operation cannot authenticate an accessor; nested operations deliberately share parent identity.

Recommend one new source-issued **single-use context object**, returned by one new method. It yields the unchanged authentic RNGOperation and retains an immutable historical completion outcome after its exit. The context object is the per-invocation identity; it grants no new draw, membership, token, publication, local-route or parent authority. Existing `operation` and `device_operation` signatures/results and active-operation authentication remain unchanged. This additive surface serves a new capability, not a compatibility adapter.

Alternatives considered: an operation-wide boolean cannot identify nested invocations or survive retirement safely. A separate outer receipt gate plus inner operation could bound inspection to a live gate, but adds another mandatory scope, lock/pin lifetime and gate admission policy. A callback invites unrelated execution during completion and is outside the authorized design. The recommended context object keeps one operation scope and adds only immutable post-exit evidence. This choice is the designer's proposal, not an already adopted policy.

## Exact public surface

```python
class RNGDeviceInvocation:  # opaque, source-issued; no public constructor
    def __enter__(self) -> RNGOperation: ...
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> Literal[False]: ...
    def completion_failed(self) -> bool: ...

class AmbientRNGDomain:
    def device_invocation(
        self,
        *,
        participant: RNGParticipant,
        operation_kind: str,
        lineage: RNGOperation | None,
        cuda_devices: tuple[int, ...],
    ) -> RNGDeviceInvocation: ...
```

`TracebackType` is `types.TracebackType`; `Literal` is from typing. The public object satisfies `AbstractContextManager[RNGOperation]`. On successful normal exit `__exit__` returns False; on failures it preserves the existing propagation/aggregation behavior, including re-raising the original body exception when appropriate. No defaults are introduced. No full-member companion API, public receipt issuer, policy registrar, per-device result list or operation getter is added in this packet.

`device_invocation` binds the exact participant, kind, supplied lineage and explicit immutable device tuple. Issuance checks PID and exact issuer/type/argument shape without CUDA work; it does not admit work or freeze membership. Full membership, registered entrypoint, active lineage, poison, inventory, reentry and runtime readiness checks occur again at `__enter__` under the same real domain exclusion and in the same order as existing `device_operation`. Changes between construction and entry cannot bypass them. Constructing a handle has no generation/revision/currency effect and performs no CUDA query. The context cannot be entered twice, reentered recursively, moved to another thread, or used to suppress failures. Unused handles do not pin owners or hold domain exclusion.

## Authentication and lifetime

The domain issues the exact opaque object and maintains a private identity-keyed weak registry of its invocation record. As with existing capabilities, ordinary construction, initialization, copying, deep copying and serialization are refused. A manually allocated lookalike, subclass, attribute-forged object or foreign record is not registered authority. Registry records must not strongly retain their own weak key.

Bind issuing process and **issuing thread object identity**, not only a recyclable numeric thread ID. Every public invocation method checks actual PID first, before registry/lock/CUDA access; inherited objects receive the existing inherited-process RuntimeError and exact text. Then check exact class, source-issued identity and issuing thread. Foreign/forged/wrong-thread use raises ValueError. Lifecycle misuse raises RuntimeError. A wrong-thread call must not wait for domain or owner exclusion. Context entry still obtains the ordinary real domain lock for operation work. Outcome reads require no domain/owner lock acquisition and no CUDA access; they do not use `_usable` and remain readable after poison.

States: ISSUED -> ENTERING -> ACTIVE -> EXITED, or ENTERING -> ENTRY_FAILED. ACTIVE starts only when the underlying operation has successfully yielded its genuine lineage. `completion_failed()` is readable only in EXITED after an ACTIVE invocation. It refuses ISSUED, ENTERING, ACTIVE and ENTRY_FAILED rather than returning a misleading False. A premature getter refusal does not mutate the invocation. Entry failure never authorizes body execution and has no completion outcome.

On exit the result is sealed before any aggregated error is delivered to the wrapper. The original issuing thread may repeatedly read it for as long as it retains the handle, including after operation retirement, subsequent unrelated operations or participant retirement. This historical read requires no still-live operation or membership: those facts were authenticated at entry and are immutable provenance. It does not make the old lineage/token current or reusable. No public reset or transfer exists. Retaining a completed handle must not pin the owner, operation, original exceptions, traceback, generator or closure; release execution references at termination. Retain only finite result/provenance needed for authentic reads. Weak registration expires when the handle is collected.

Owner-lock custody is a producer obligation, not something a boolean accessor can prove. The producer must retain its actual mutation lock through operation exit, outcome read and quarantine transition using its already approved admission/owner lock ordering. Core does not inspect private producer locks or introduce a new lock order. Historical readability after owner release is diagnostic evidence only; it is not permission to mutate an owner without custody.

## Exact attribution and completion rules

Each successful entry creates a distinct invocation record, even when two nested scopes yield the **same** genuine parent RNGOperation. Existing lineage joins, pins, token/currentness bookkeeping, currency/revision changes, ambient restoration and poison propagation are preserved by sharing the real operation implementation, not by reconstructing an operation publicly.

The outcome describes **this scope's own exit completion phase**, not all failures occurring while its body is active and not the current domain poison state. For a nested invocation that phase uses its exact admitted subset. For a standalone outermost invocation it uses the existing final union of admitted operation devices, including descendants; changing this union rule is forbidden. Thus an outer invocation can have True because its own union completion fails on a descendant device, without claiming that the outer owner's own device was the cause. This distinction must remain explicit in producer interpretation.

False means that the invocation's own required completion phase ran to successful completion, including vacuous completion of an empty inventory. True means that a synchronization in that phase failed, or that an entered invocation's required completion phase could not finish and therefore cannot certify completion. It does not identify individual failing devices. Never derive it from body errors, reported gate errors, common poison, the final failures list, or exception structure/identity.

Record the result at the completion call site, before appending failures or deduplicating. A pending entered invocation starts uncertified; only successful return from its actual `_complete` establishes False. Any failure or interruption before that success leaves True. Sealing occurs in unconditional exit cleanup before control returns/raises to the wrapper; no partially exited handle is reported as success. Internal cleanup faults remain real failures and must not be suppressed to manufacture a receipt.

Preserve the present `_complete` short-circuit semantics: sorted device iteration stops at the first synchronization exception. Devices before it may have completed; the failing device and unvisited tail are not certified; the invocation returns True. Do not quietly change to all-device attempts, add a second synchronization pass, retry, or mark partial success as full completion. Empty-device completion invokes no CUDA attribute and returns False even when a body error propagates.

Nested and sibling results never overwrite one another. If child A fails completion and parent/sibling B's own completion succeeds, A=True and B=False even if A's error is included in B's propagated exception or domain poison remains set. If poison forbids a later sibling's entry, that sibling has ENTRY_FAILED, not False. A parent is True only when its own completion fails/is unfinished; a descendant's reported failure alone is insufficient. Existing poison refusal still applies regardless of a historical False receipt.

The outcome does not cover bootstrap/query failures before entry, restoration failure, body-invoked gate failures, or semantic producer validation. Those retain their existing explicit handling. A receipt False must never clear poison or undo independently justified owner quarantine. A receipt True permits only the producer's already specified response to uncertainty in its own invocation; this proposal does not mandate blanket quarantine of all participants or all nested owners.

## Required wrapper shape

The existing producer wrapper holds its actual owner mutation lock at this point; admission/lock acquisition remains in the separately accepted producer design. With those locks already arranged:

```python
invocation = domain.device_invocation(
    participant=participant,
    operation_kind=operation_kind,
    lineage=lineage,
    cuda_devices=cuda_devices,
)
entered = False
try:
    with invocation as operation:
        entered = True
        # Existing work uses this genuine operation, including nested lineage.
        perform_existing_work(operation)
finally:
    if entered and invocation.completion_failed():
        # Existing owner-local quarantine transition, under the still-held lock.
        mark_this_owner_completion_uncertain()
```

This is explanatory flow, not a new callback API: `perform_existing_work` denotes existing producer code. The entered flag prevents querying an unavailable result after entry failure. The producer's quarantine transition must follow its separately specified exception-preservation rules; this proposal supplies no arbitrary error-handling callback. Clean body failure with successful completion reads False and propagates as before. Body E plus synchronization E reads True even though deduplication still exposes only E. Both inspection and any justified owner transition precede owner unlock. The retained handle cannot substitute for this invocation's freshly created local variable.

## Finite causal acceptance tests

Use the planned bounded core/test packet and existing qualified CPU CUDA stand-ins. Every test asserts actual phase events, not just final poison/status.

1. Standalone success yields a genuine operation usable by existing authenticated methods, retires it normally, then reads False under the still-held owner lock. The retired operation still fails authentication; the receipt remains readable. Empty inventory forbids all CUDA attribute access.
2. Same exception object E: body-only E with successful completion yields False; body E plus synchronization E yields True. Both outward errors retain exact E identity. A distinct body/sync pair preserves existing ordered grouping. Poison only follows actual existing failure rules.
3. Subset completion with devices (0,1,2), failure at 1: trace exactly 0 then 1, no 2 or retry; True is sealed before exception handling and before owner unlock. Successful (0,1,2) yields False. Body-only failure still attempts required completion.
4. Nested scopes yield the same parent lineage but distinct invocation handles. Child's own synchronization failure followed by parent successful completion yields child True/parent False. Reverse schedule (child success, parent union failure) yields child False/parent True. Preserve token/currentness and nested ordinary-work invalidation controls.
5. Two successful sibling scopes retain independent False receipts; later parent failure cannot mutate either. A failed child followed by poison-refused sibling entry leaves the sibling unreadable/ENTRY_FAILED. No fabricated successful sibling under poison.
6. Reported gate/body failures with own successful completion yield False while retaining original poison/error propagation. Pre-entry inventory/bootstrap/readiness refusal has no readable outcome and no body or completion trace.
7. Constructor forgery, object.__new__ lookalike, subclass, copy/deepcopy/serialization, wrong issuer, wrong thread and recycled numeric-ID scenarios cannot obtain or modify an outcome. Test thread-object binding deterministically without fake PID. No callback path or public status mutator is added.
8. Pre-entry/active getter, duplicate enter/exit and reuse refuse without altering a valid record or running another completion. Repeated post-exit read is stable, including after poison, unrelated operations and participant retirement. Owner and execution-state weak-reference controls demonstrate no completed-handle pin leak.
9. Honest inherited-process guard-only fork within the already qualified spawned-child protocol refuses all public handle methods before domain-lock or CUDA probes. No Torch/CUDA fork work or fake PID. Wrong-thread tests show refusal before blocking and no CUDA events. New child execution requires the existing independent verifier admission process.
10. Deterministic owner competitor trace demonstrates completion, receipt read and any owner-local uncertainty transition happen before owner release and before the competitor observes owner state. A clean body-only error does not trigger completion-based quarantine. Test against producer integration when that owner source is admitted; core-only tests cannot claim that producer behavior.
11. Root public-consumer type probe checks exact method arguments, `RNGDeviceInvocation`, context yielding RNGOperation and bool result; owned mypy/style/default guards remain required. Instrumentation asserts parity with existing device_operation for exclusion, pins, revisions, union completion and exception identity. No test weakens existing admission, local contract, poison or source-issued authority checks.

These are contract cases, not a prescribed number of pytest nodes. No new hardware claim follows from CPU stand-ins.

## Scheduling and adoption boundary

Implement, if adopted, in B's already planned bounded core+test packet with a private shared completion-report hook/record, not a public callback and not duplicated operation semantics. Supplier author may provide implementation facts but is not the policy approver. No earlier implementation is required unless another producer packet would otherwise ship using this outcome: that packet must wait for the API's independently reviewed implementation and executable qualification. Existing qualified core-only results remain valid for their earlier scope; they never claimed this new producer attribution capability.

Independent peer review and root adoption must settle this exact API/lifetime/attribution proposal before implementation. Existing finite source routing, source freeze, tests-first and child-verifier gates apply. Actual CUDA hardware, B6 producer integration and full-programme obligations remain separate and open.
