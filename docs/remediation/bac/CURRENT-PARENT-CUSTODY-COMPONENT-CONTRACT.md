# Current runtime/BANK parent custody component contract

2026-11-14. Runtime/BANK diagnostic contract source-verified at R133; the R144 ENV guard/diagnostic and R145 G1/G2 fixture components have separate bounded reviews and root adoptions. The historical R133/R132 executions below retain their original identities. Full C1/C2 acceptance remains open. Current R145 global mypy fails with 12 diagnostics in two files. Actual CUDA is UNRUN.

## Exact source

| Source under repository root | Lines | SHA256 |
| --- | ---: | --- |
| src/townlet/config/exploration_policy.py | 1343 | 5c5410d8bf6213f42cab3b18925efb164eec4670dd7f8c10b31af305f8a32363 |
| src/townlet/exploration/scoped_curiosity.py | 1492 | 110d640bdb607fd58d6e991dba49da2cc5236f169cc4c1db45627db6b8082f7c |
| src/townlet/exploration/parent_custody.py | 239 | 1b911c653ed1b1738c4de19b646bd1965cc0825b6f85e814e5ba25a43e02944f |
| tests/test_townlet/regressions/bac/test_runtime_bank_parent_custody.py | 1348 | 7102dd35e36481713b24fc2ec37e242e8d00d2ee9bc958db018ba89dd5638872 |
| src/townlet/population/vectorized.py | 3169 | 7f02f08359fa15aaa713e8e7221142d130f560cd96cea13334c64c54b088ee8a |
| tests/test_townlet/regressions/bac/test_parent_intrinsic_handoff.py | 900 | bbfdc1e8d60a609de6dacf7b68c0d6cb7e014df308dddddde5698ad2bf7fd673 |

R133 manifest SHA256: `6a29f0a6d8111dbfcddaf90652230a8290d8370864d6dbbead279c481f5a6b58`; candidate tree: `0f9f3305b637c0d0f6b2a24c50eef5e6af5a4592`. R132 results for 133 ordinary cases, seven isolated poison controls and 36 independent cases retain their own candidate identity; equal supplier/test bytes do not assert a new R133 execution. All 25 selected POP cases pass at R133 with full postflight custody.

## Public APIs and lifetime

- `ExplorationRuntime.retain_parent_custody()` returns a context manager yielding
  an opaque `RuntimeParentCustody`.
- `CuriosityBank.retain_parent_custody()` returns a context manager yielding
  an opaque `BankParentCustody` for direct BANK controllers.
- Each scope exposes `bind_operation(*, operation: RNGOperation)`, a context
  manager yielding None. The operation must be genuinely active and admitted.

Retain while operation-idle, then enter the actual controller invocation inside
retention, then bind its yielded operation around supported method calls.
Exit binding before invocation completion, consume the controller's own result
while retention still holds, and only then exit retention. No scope creates a
parent participant, invents lineage, enrolls devices, or grants recovery.

Runtime retention acquires common admission(None), runtime RLock, then BANK
RLock. Direct BANK retention acquires common admission(None), then BANK RLock.
Ordinary methods also admit before these owner locks. Bound methods reuse only
their exact authenticated explicit binding; they never adopt ambient lineage.
Unbound retained scopes refuse guarded methods. Epsilon's scalar observation
remains the harmless reentrant exception and grants no forwarding authority.

Scopes are issuer-retained identities, nonconstructible/noncopyable/nonportable,
bound to actual owner, Thread object, PID and lexical lifetime. Misused handles
refuse before owner-lock waiting. Ordinary foreign-thread work waits at common
admission, including safely across another thread's scope expiration.
Active scopes pin owners; exit expires records and clears execution references.

Runtime-owned BANK custody is delegated-only: only the private runtime forwarding
seam can issue one intended-method/current-call permit. BANK consumes that permit
before public body/admission/callbacks. Callback peers cannot reuse it; runtime
and BANK method-active guards plus existing authority/view/revision checks remain.
Direct BANK controller scopes remain supported outside runtime delegation.

## Completion and restore boundaries

BANK public admitted work uses a fresh device invocation with its own declared
tuple: `()` for CPU, or its explicit singleton CUDA index. This preserves current
membership; it is not complete foreign-source/rejected-prefix inventory.
BANK retains exclusion through its own completion and sealed-outcome read.
Own True sets monotonic completion uncertainty without callbacks/CUDA/new locks;
own False does not heal body/publication failure. Native own completion is not
deferred. Later controller True after copied BANK outputs does not automatically
mark BANK/native uncertainty. No public late-parent quarantine hook is provided.
Runtime has no separate RNG participant; the controller owns its later effects.

Existing non-cohort runtime/BANK episode, stamp, reward/service, completion,
evidence, snapshot/checkpoint and runtime selector/commit methods compose through
binding while preserving their own preconditions. Standalone construction and
restore/private-initialization/install remain supported. Bound `prepare_restore`,
`prepare_private_initialization` and `install_restore` refuse before their body;
active-parent cohort publication awaits its separate idle-registration protocol.
Standalone preparation retains its public-call guard across the idle cohort gap.
Scope/permit records are nonrestored; BANK execution fields and monotonic latch
are slots outside its prepared dictionary. Final runtime install uses authorized
forwarding followed only by preallocated runtime state/revision/handle assignments.

## Episode quarantine is a distinct existing operation

Runtime `quarantine_episode(*, accepted, reason)` forwards reason unchanged.
BANK authenticates accepted first, then accepts only exact-str
`empty_participation` or `runtime_failure`. An identical accepted/reason pair is
idempotent; a changed pair refuses. A new valid pair sets local failure and
quarantine and advances mutation revision; runtime forwarding invalidates its
revision/restore handles accordingly. Healthy BANK snapshot/checkpoint paths
then refuse. Unsupported reasons fail before those assignments but after accepted
validation; the real admitted completion still runs. Local failure alone does
not exclude this cleanup body, but common poison still excludes admission.
This callback-bearing episode operation is not a parent completion consumer.
Correcting a caller's reason string alone does not repair missing replay lineage
or qualify its full failure/cleanup sequence; that requires genuine execution.

Conditional raw native/storage routes, complete device-prefix inventory, true
outer-owner health/publication, and required failed owner assertions remain open.
No compatibility adapter, fabricated authority, implicit recovery or scope waiver
is part of this component contract.

## Complete diagnostic export and standalone POP cleanup

Runtime and BANK expose generic `diagnostic_state()`. Runtime returns `exploration-runtime-diagnostic-v1` with nested `curiosity-bank-diagnostic-v1`; the existing failure-only API retains its distinct schema and failure requirement. Generic `failure_reason=None` describes actual locally available BANK state, including initial state without an invented accepted token. `runtime_failure` requires authenticated ordinary local quarantine. These labels do not assert whole-run health. Empty participation, pending completion, missing authentication, monotonic own-completion uncertainty, poison and custody restrictions still refuse. Existing parent binding, one-call forwarding permits, callback guards and lock order remain in force.

The payload retains fresh complete native state, gradients, RNG, cursors, caches, step and completion history. Private per-world native `healthy=False` remains admissible under its native contract; shared failed native capture still refuses. Diagnostic export neither heals failure nor grants recovery. Runtime's restore parser rejects generic/failure diagnostic runtime schemas and nested diagnostic BANK payloads; BANK's supported prepare-restore and private-initialization receivers reject both BANK diagnostic schemas before cohort creation. Opaque installs still require retained identity handles. This describes those supported receiver boundaries, not a nonexistent runtime private-initialization API.

POP preserves its healthy `checkpoint_state()` route, explicit proven failed route, all twelve outer fields and evaluation order. The failed route uses generic `diagnostic_state()` so an available BANK can be reported truthfully after a different POP failure. Standalone step cleanup retains actual failure/completion evidence. Complete payload comparison, fresh receiver failed-progress refusal and capture sentinel identity remain required and are exercised by the bounded POP selection. Diagnostic transport cannot resume failed progress. Two R133 return casts change typing only; no fallback, cached subset or exception swallowing is introduced.

Source-review basis is the R131 independent producer review (`245f090945f240a57122ed404979761e524681261394efe42dd55ea62bc8a6e8`), fresh R132 POP review and R133 typing addendum (`ecdb4e5098ae04d3e98e0d2d610b39149722467d298ab942d94c521f9b12fdeb`). These component reviews are not the independent terminal checkpoint review. R132 retains 12 intentional fork DeprecationWarnings. R128's missing original postflight stays explicit; later POP reruns do not rewrite historical custody. Package accounting remains 28 qualified / 38 remaining / 66 total.

## R144 ENV component and R145 fixture adoption

The R144 ENV guard/diagnostic component is separately adopted at executed tree `ed561dc04fcffba4f6617f343862d54db6a8dad0`. It records 51 targeted cases and nine independent adversarial cases passed, without a combined unique-coverage claim. Runtime/BANK retention, lifetime and completion constraints above remain in force; ENV exclusion does not establish outer completion health, complete child/device inventory or restore composition.

| Source under repository root | Lines | SHA256 |
| --- | ---: | --- |
| src/townlet/environment/vectorized_env.py | 2949 | aefccf149c20d9d1b7505539a7e261c7a0aa9ce9e40898a1fc18f5f3691c9b22 |
| src/townlet/environment/parent_custody.py | 252 | bc83c8ce94da32cf9296692e167bbab42c52794cb2d3da91595d19b3cd176022 |
| tests/test_townlet/regressions/bac/test_environment_parent_custody.py | 840 | 372745a1c584d92ac0349479010f1d195a4fae9d89d4c2ba449a445297e6f68b |
| tests/test_townlet/regressions/bac/test_initial_participation_env.py | 1343 | 80a9ef90c939214b9d709b94e7f058041e4cfa24cfaa0421b8cb0d31a0c327d1 |

R145 manifest SHA256 is `d29b30f41e6c9d46f471e8fadbaa3d80f5b8b58481b0534ac2b798cd5381bc53`, candidate tree `192bfdbd16fd998e0095f303c5e93a49e346a471`. Its one-file fixture migration retains all 39 original test functions and assertions and records 82 cases passed with full controller/two-worker custody. The separate first-transition pass overlaps that selection. Eleven G1/G2 failures are resolved; 18 known G3/G4 restore failures, four prior unqualified skips and a full owner rerun remain. R142's 234 PASS / 30 FAIL / 4 SKIP is historical evidence, not a new R145 execution.

Local P1 full-ancestry admission is unsupported: cgroup membership is `/`, the mount root is `/..`, and PID 1 namespace access returns EACCES. This is not CPU scarcity: four CPU and 16 GiB remain available for authorized local APP and inert checks. Actual P2 Task 4 remains UNRUN pending access to the user-provided server and measured ancestry; the promised 16-worker CUDA server is unprobed. The two identified P1 code fixes are not qualified in WIP24; subsequent implementation is outside this checkpoint.

The width-three manual ENV driver is designed, not implemented. Complete child/source/device inventory, outer completion consumers, restore/cohort/recurrent integration, P1 real-input repair, P2 actual backstop, P4 strict dispatch, actual full chain and CUDA remain required. P2 Task 4 is AST-only unqualified preparation; checkpointed P4's 99 inert passes lack independent review. P5 v4 adoption is tooling scope only. No original package closure is claimed: 28 qualified / 38 remaining / 66 total. See [WIP24 evidence](evidence/wave35-wip-24.json) and its [selection plan](evidence/wave35-wip-24/selection-plan.json) for exact adoptions, reviews, failures and source/helper identities.
