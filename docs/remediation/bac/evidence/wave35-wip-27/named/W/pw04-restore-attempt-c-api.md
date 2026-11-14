# C3 packet C: finite source integration agreement

Proposed implementation handoff, not qualification. Existing owned bodies are ENV
3041, ENV custody 418 and manual session 292 lines. New attempt module is bounded
to 700 lines and focused component tests to 300; all growth remains within five
whole bodies/5000 lines. No imported implementation/test helper body was opened.

## Runtime authentication agreement

The new `townlet.environment.restore_attempt.runtime_restore_context(*, attempt,
runtime)` context manager will yield an immutable `RuntimeRestoreContext` with
`scope`, `prepared`, and `operation` (`prepare` or `install`). It authenticates the
exact issued attempt and weak registry, PID/thread, live lexical ENV association,
selected runtime/profile, actual current unbound ENV scope, expected stage and a
one-use overlay permission. It does not add an RNG/currentness operation or pure
callback count. B retains the actual attempt identity on its prepared handle and
calls the supplied scope's pure validation before/after its original real cadence
comparator. B accepted this interface. A lazy runtime import avoids module cycles.

The context catches escaping failures using C's genuine observation-derived abort
while ENV exclusion is retained. B's runtime lock and overlay expire on all paths.

## Source staging and failure bookkeeping

Public factories are the approved explicit authority methods
`restore_bank_attempt` and `restore_runtime_attempt`, each taking exact prepared
world, selected actual child, fixed parent comparator and fixed finalizer. They
retain one continuous idle domain gate, but never an active ordinary ENV call
across the lexical attempt. Per-stage ENV retention surrounds actual child work;
ordinary release issuance and world installation occur outside retained scopes.

The attempt owns prepare/private-initialize, release, child install, world install
and finish stages. Only genuine child preparation supplies the retained handle
and outcome. The first-attempt outcome must still be `pending` before C's one-use
installation; C cannot adopt an already-attempted handle. COMPLETE remains sealed
and later abort/context exit must preserve ordinary exact-pair installation retry.

Selected preparation and release are escrowed. Distinct preallocated one-use
identities authorize the source calls into `authority.restored` and
`env.install_world_restore`. Their ordinary routes reject escaped active/failed
escrow; unrelated valid preparations and successful installed pairs remain valid.

At acquisition, preallocate a weak-key escrow cell whose value never retains its
key or attempt. Failure changes its status and ENV terminal flag by assignment;
it does not allocate a weak-set entry after poison. A's pure predicate and the
ordinary release/install routes check failed escrow. Existing explicit revoked
records remain refused. This small A→C integration is not a claim that A already
implemented attempts or broad terminal ingress.

Abort distinguishes genuine no-publication from partial/uncertain child effects
using B's immutable result, not exceptions or caller booleans. Preparation-call
failure without certified completion remains uncertain. A successful child install
followed by world/finalizer failure fences the receiver. Cleanup uses the existing
ENV lock under the still-held outer gate, without new admission or accepted-token
cleanup. Native child health flags are preserved; no rollback/reprepare occurs.

## Genuine native finalizer borrowing

Root approved the narrow proposed hook `validate_restore_finalizer(*, attempt,
owner, restored) -> None`. It authenticates the exact live attempt and its
source-entered FINALIZING stage with a preallocated one-use callback identity,
the actual installed world/release pair, unchanged pinned role bindings and the
actual receiving owner. It grants no transferable token and performs no new
admission, RNG operation, export or fresh-bound A check after world publication.
The real producer's data-only plan remains owner/revision-bound and one-use;
this cannot refresh an old PreparedReplay token. C calls the fixed continuation
once and expires borrowed authority on return/error. Actual native consumer
continuation still needs its own source qualification.

## Terminal routes

ENV custody will refuse healthy guarded methods before admission on a terminal
receiver; copied action labels, phase/cursor diagnostics and existing fail-closed
runtime-failure cleanup remain non-authoritative. Participation ingress, the
unguarded accepted-token validator, genuine manual session checks and attempt
factories also enforce the terminal flag. No raw Tensor alias is claimed fenced.

## Focused tests and limits

The first RED file creates the actual compiled ENV and actual CuriosityBank,
lawful portable INITIAL world input, a real saved-bank comparison and component
world-install journal. Other role slots are identity-only and confer no native
owner proof. No fake child, fake installation outcome or no-op comparator is used.
These controls cover component composition/authentication/failure semantics only;
real POP stable-owner continuation, native artifacts, runner continued learning,
full original G3/G4 obligations and final independent qualification remain owed.

## ENV-owned native layout staging (implemented, qualification pending)

`env.prepare_native_layout(state, *, parent_plan)` returns an opaque
`PreparedNativeLayout`. It authenticates the actual POP-issued plan through
`townlet.population.vectorized.validate_native_population_data(plan=parent_plan,
owner=env)` and uses ENV's existing full affordance validation to materialize
owned tensors before BANK installation. Its ENV-local weak registry records a
weak reference to the exact parent plan, PID/thread, layout revision, original
affordance dictionary identity, precomputed tensor assignments and next revision.
It does not reuse a WorldRecord or pin the world generation which restore advances.

`env.install_native_layout(*, prepared, parent_plan, attempt, restored)` requires
the same genuine POP plan and C's actual fixed finalizer with owner exactly ENV.
After authenticating the issued handle and unchanged layout revision/dictionary,
it consumes the handle, publishes the preallocated tensors and invalidates the
layout cache. No tensor construction or checkpoint decoding occurs in publication.
The existing dictionary and ENV identities are preserved. Ordinary configured,
randomized and explicit layout mutations advance the separate revision before
publishing, invalidating earlier staged handles even if mutation subsequently fails.

The finalizer hook also accepts exact receiving ENV in addition to its pinned
registered role owners; foreign ENV and calls outside FINALIZING remain denied.
Its `restored: object` annotation describes an opaque input checked by exact
identity and does not weaken runtime authority. Repeated pure checks inside the
one genuine callback are allowed; each child data preparation remains one-use.

Root R163 verified the two intended missing-layout-API RED cases and the existing
C component cases. Layout production source now exists but still requires root
execution and independent review; successful genuine POP layout publication,
staleness and reuse controls belong to the real native integration witness and
are not established by the component's foreign-plan refusal tests.
