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
