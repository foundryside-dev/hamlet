# PW04 C3 B producer API capsule

2026-11-14. Source-owner capsule for C integration/review. Not independent review or
PW04 closure. Root reports R161 candidate `74522435…` passed the combined 18 B/C
non-poison cases and the one separately executed actual B completion-poison case,
with source custody verified. These are component results, not native runner
qualification. A newly authored observer race regression remains RED-to-run and
the corresponding repair is pending.

Source inspected and authored in this packet:

| Whole body | Lines | SHA256 at capsule creation |
| --- | ---: | --- |
| exploration/scoped_curiosity.py | 1565 | `58fa466c500649447046b0a34bcaec9da49ab8237d31bdaee1c31f28d022fcf6` |
| config/exploration_policy.py | 1475 | `a12c8214901a5988253e7d9589a3f38f3d0de48f62c267ea07dd43b7665dd9fb` |
| exploration/parent_custody.py | 398 | `e66de4a4fae161c96c910cdd649834778836220b56b2a5227f1f269bc4e78ba8` |

The owned test file is `test_restore_installation_outcomes.py`388; the now-approved
fifth body is `environment/restore_attempt.py`420. Total 4246 lines before further
growth. The originally assigned 900-line parent handoff test was never opened and
was replaced by the 239-line original exploration custody helper. No other source
body was inspected; core/ENV/POP facts are attributed below.

## Exact observer contract

Both actual producers expose `restore_installation_outcome(*, prepared) ->
RestoreInstallationOutcome`. Exact types are
`townlet.exploration.parent_custody.RestoreInstallationOutcome` and
`RestoreInstallationResult`. `outcome.read()` returns a frozen, slotted,
preallocated result with fields:

- `status`: pending / in_progress / sealed.
- `call_entered`, `operation_entered`, `handle_consumed`: actual source call,
  BANK invocation admission and BANK token removal, respectively.
- `bank_publication`: none / complete / uncertain.
- `runtime_publication`: not_applicable for BANK; otherwise none / complete /
  uncertain for the selector/cadence/revision/handle suffix.
- `completion`: not_entered / succeeded / failed / uncertified.
- `returned_normally`, `runtime_handle_consumed`: actual represented normal
  path and runtime publication of the empty handle registry.

One observation belongs to each genuinely prepared handle. It records the **first
actual installation attempt** and never changes after sealing. An unconsumed
standalone retry remains lawful and can install successfully without rewriting
that first-attempt result. C must require a pending observation before its own
one-use install; it cannot adopt an already attempted handle. Pending/in-progress
is never evidence of no publication.

Public lookup authenticates the currently registered handle, producer, PID and
creating Thread under only its existing local lock. It refuses incompatible
public execution. It performs no domain admission, RNG/native operation, status
read or callback. Cache the outcome before consuming the handle. Its `read()`
remains available after consumption, dictionary replacement or domain poison;
read authenticates issuer/PID/Thread and returns an immutable existing result.
Observation objects refuse copying/serialization. The module's weak outcome
registry retains neither outcome nor handle in its value; its owner reference is
weak. The outcome itself intentionally retains its issuer and original handle.

## Actual source recording cuts

BANK allocates the observation in `_seal_restore` before final current-token
issuance and retains it in the genuine preparation record. `_serialized` observes
entry before the original public guard; `_admission` records actual invocation
entry and completion. `install_restore` records token consumption immediately
after the real pop, sets publication uncertain immediately before assigning its
replacement dictionary, and complete only after assignment returns. The registry
is outside the replacement dictionary. Existing failure flags are preserved.

Runtime allocates its observation before the actual BANK preparation, retains
BANK's genuine observation in `_ExplorationPublication`, observes its own public
guard, incorporates actual BANK results and marks its own suffix uncertain before
publication/complete after all assignments. No extra BANK comparator, RNG operation
or native post-publication validation was added. Immutable result variants are
allocated before any token exists; cut recording selects existing values.

**Known R161 limitation:** active observer pointers are restored after the current
public guard releases its owner lock. A subsequent concurrent call could have its
pointer overwritten, and a delayed runtime first-attempt classification could
read a later child's result. The approved repair moves active-pointer lifetime and
BANK-result capture inside the existing owner exclusion; only local result sealing
remains outside. A deterministic genuine concurrent-install regression has been
authored, not yet run. R161 passing controls do not refute this race.

Core completion facts were supplied by root against RNG core SHA
`6cb01ca77b58db5f4c4784dc36da566c06cf68c2a7c2ce227bb780549f3344f8`:
`completion_failed()` authenticates PID/Thread and requires an exited invocation.
It remains true until actual `_complete` succeeds. A body exception followed by
successful completion yields false; a completion failure yields true. Entry failure
has no exited completion observation. B reports uncertified before consulting this
actual accessor and never infers publication/completion from exception text.

## Genuine C correlation

`runtime.validate_restore_receiver(*, curiosity_owner)` verifies exact current BANK
identity and the original issuer object retained from construction, where BANK
already authenticated issuer.owner is BANK. This avoids invoking an arbitrary
issuer property during the new association check. It uses local custody only.

`runtime.correlate_world_restore(*, attempt)` lazily imports C's actual
`runtime_restore_context(attempt=..., runtime=...)`. C authenticates its registered
live attempt and yields scope/prepared/operation. B holds its runtime lock, permits
exactly one selected prepare/private-initialization or install, and expires the
overlay on every exit. Each real `_correlate_cadence` checks exact parent identity,
calls the public pure ENV check, invokes the original constructor-bound comparator,
then calls the pure check after normal return. Original None-return, unchanged-view
and revision comparisons remain. Prepared runtime handles retain their actual
attempt identity; composed installation requires that same live overlay. Ordinary
None-associated handles retain the standalone route.

No fake C attempt or no-op cadence callback was used. Existing B tests use genuine
fresh compiled ENV, runtime and POP, including POP's real initial cadence validator.
Runtime-profile C positive/comparison-count controls are being added next through
the actual C hook. C's direct-BANK seven passing controls are not that proof.

## R162 RED and subsequent candidate repair

Root reports R162 exact candidate `6cac386e…` reproduced the deterministic
concurrent-install failure: after two actual completed BANK calls, a stale active
observer caused the next legitimate observation lookup to refuse. The repair is
now authored: BANK and runtime install/restore their active observer pointers
inside their existing owner exclusions; runtime also captures the actual BANK
result and runtime handle disposition before releasing that exclusion. Only
sealing the local first-attempt result remains outside. No new admission or
native operation was added. This supersedes the earlier pending-repair status;
GREEN verification of the repair is still owed.

Pre-format candidate source hashes: BANK `fa3c5ce8f8e75bd242e7d2fec3d5264a75952e881a87ec21eba8c039f9219e7c`
(1569 lines), runtime `d19d8814ef619903e1987b297343655cbe80cfca020e7b3f88fff941f01b7f94`
(1479), helper unchanged (398). The test body is 526 lines, C body420;
five-body inventory4392. Root formatting may change these hashes/counts.

New runtime-profile component tests exercise genuine registered C attempts with
actual ENV/runtime/BANK/POP owners: shared and per-world successful composition,
four BANK plus three real POP cadence comparisons, fourteen mandatory public
pure checks, full native state comparison, and an adversarial real cadence
callback that catches its own stale-world refusal. These tests are authored but
unrun. They do not establish native runner artifacts, resumed learning, or PW04
closure. No test execution was performed by this source owner.
