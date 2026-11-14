# Current runtime/BANK parent custody component contract

2026-11-14. Source-verified draft for root review/publication, at R122 below.
This describes implemented component APIs; full C1 acceptance remains open.
The required owner regression gate retains 215 failures; mypy has 15 diagnostics.
ENV/POP/cohort/recurrent/runner integration remains required. No CUDA hardware
qualification or whole-parent completion guarantee is supplied by this document.

## Exact source

| Source under repository root | Lines | SHA256 |
| --- | ---: | --- |
| src/townlet/config/exploration_policy.py | 1313 | 50a738825ae151cbf7a2907660e4cd06df7e42ae78128135eda891b3c6c885f9 |
| src/townlet/exploration/scoped_curiosity.py | 1443 | 55e0ac73ed65932aaf19c0622c8f11c5bb3801fda8957492ccf513d270a104b4 |
| src/townlet/exploration/parent_custody.py | 239 | 1b911c653ed1b1738c4de19b646bd1965cc0825b6f85e814e5ba25a43e02944f |
| tests/test_townlet/regressions/bac/test_runtime_bank_parent_custody.py | 854 | ca3b0fd10c1fb49e508237901054dd655c9df34fea3745592c216e6c4d5ad5bc |

R122 manifest SHA256: `6075b1b51c3d2de05a78691fe8646963ee4bbc4b0fa22d2839ec0af91856f80e`;
candidate tree: `7d3be1eeda87015e939f1dd90275b05a1586676b`.

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
BANK lines 931–939 authenticate accepted first, then accept only exact-str
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
