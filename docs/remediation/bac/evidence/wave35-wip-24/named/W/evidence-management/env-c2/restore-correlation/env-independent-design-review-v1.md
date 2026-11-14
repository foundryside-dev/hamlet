# C3 ENV independent design review v1 — changes required

2026-11-14. Reviewer `/root/bac_astra_env_c2_review`. **CHANGES REQUIRED: two
finite material contract gaps.** The segmented admission/order approach is
supported conditionally; the proposed complete C3 interface/failure contract is
not approved yet. This is not a request for a general restore redesign or a
reason to withdraw already qualified bounded C2 evidence. Existing18 G3/G4
obligations and all remaining owner failures remain required.

## Exact proposal and source custody

Read and SHA256-verified:

- `producer-facts-v1.md`:
  `bdd365df98fbf5521198eeef77336002beffdb4cded61063117633301cd28116`.
- `core-currency-supplier-v1.md`:
  `b24eab4821f3b5bf73d663acd8dc5e8733838e93b9bb2327cf727f3b72a7395b`.

Compared against already-owned full ENV/helper sources and focused test context:
ENV2949 `aefccf149c20d9d1b7505539a7e261c7a0aa9ce9e40898a1fc18f5f3691c9b22`;
helper252 `bc83c8ce94da32cf9296692e167bbab42c52794cb2d3da91595d19b3cd176022`.
No BANK/runtime/core/fixture/WorldRecord/VFS implementation body was opened.
Their statements here are supplier-attributed. No APP edit/import/runtime,
Git/index operation or execution copy occurred. Existing whole-body custody is
ENV2949/helper252/focused tests840/own probe393 =4434/four. Historical review and
execution evidence remain unchanged. Root reports repeated independent R144
nine PASS and component adoption; this review does not reclassify those results.

## What is supported in the proposed sequence

Continuous outer idle admission, ENV retention before standalone runtime/BANK,
and a pure reverse check that reuses already-held ENV exclusion provide a sound
order on the inspected ENV side. It avoids acquiring a fresh ENV lock under
BANK and does not manufacture lineage. Separate child invocations leave the real
registration gap operation-idle. An active parent invocation spanning that gap
would still be wrong; the existing C1 bound-cohort refusal must remain.

The deliberate ENV-retention gaps around ordinary `authority.restored` and final
`ENV.install_world_restore` are necessary with today's helper: unbound retained
ENV custody refuses ordinary guarded work. The outer common mutex continues
excluding cooperative peers through those gaps. Existing ENV wrappers use
admission and exclusion, not RNG operation/token APIs. `authority.restored`
issues a WorldRecord release but does not install it or change ENV phase,
generation or revision. That supports the proposed sequencing, not an assertion
that every intervening activity is currency-neutral.

The core supplier resolves the earlier conditional question precisely: admission
ENTER drains retirement, EXIT does not; later admission/operation drains can
invalidate generation, including unrelated owner GC. Successful issuer exit can
normalize its own still-current token; a distinct immediate install validates
at revision r+1. No additional top-level validate/prepare operation may intervene
without staling it. Required strong lifetimes, exact token/owner/currentness
checks and ordinary stale refusal must remain. No refresh, reprepare, drain
suppression or global pin fiction is acceptable. The real3+1 BANK and2+1 cadence
correlations remain supplier-bound requirements, not arbitrary ceremonial calls.

## P2-1: Specify the exact pure currentness predicate and its issuance invariant

The proposed method is feasible in principle, but its present requirements
delegate the essential semantics to phrases such as “reuse the real internal
validation semantics,” “current healthy/uncertainty policy,” and “genuine
immutable owned payload/current receiving-state correlation.” The actual ENV
does not expose a single pure implementation with all those properties.

`_bound_env` calls `_check_committed_participation`; that path can encode/read
tensors and quarantine on failure. `_require_phase` performs a participation
fence, while `_valid_record` checks issuer/kind/owner/generation/registry identity
only. `prepare_world_restore` performs portable snapshot validation and VFS
projection before issuing the prepared record; `authority.restored` compares
joint receipt/state and issues a release. None may be reused wholesale as a
guaranteed effect-free currentness predicate. The proposed callback must not
silently omit physical/health constraints or execute those effectful paths.

Required finite amendment:

1. Define the exact issuance invariant established by genuine ENV preparation:
   which owned immutable prepared facts, receiving binding/identity and generation
   are sealed, and what evidence makes those facts current later. If extra
   issuer-retained prevalidated metadata is necessary, name it and its lifetime
   explicitly. This is not permission to revalidate arbitrary caller payloads or
   reconstruct a new prepared record inside the callback.
2. Enumerate the exact source-backed pure predicates: authentic live scope and
   owner/pinned bindings, Thread/PID, no active ENV method/reverse continuation,
   required fresh-bound state, applicable existing participation/failure flags,
   and exact originally issued prepared record plus receiving-state correlation.
   A valid fresh-bound receiver normally has no committed participation to
   validate. Specify how an inconsistent receiver refuses without entering
   `_check_committed_participation` or mutating quarantine state. Do not imply an
   implemented completion-uncertainty latch exists in current C2.
3. Distinguish original issuer-owned prepared data from user-supplied objects
   before any potentially effectful property/equality/content access. Explain
   which comparisons are proven ordinary immutable data, or which exact retained
   preparation evidence avoids such work. Require pure refusal as well as pure
   success; no callbacks, cloning/device work, issuer call, RNG admission or
   lifecycle assignment is allowed in this method.
4. State whether operation-bound ENV scopes are admitted or refused by this
   selected interface; the proposed path needs only an unbound authentic retained
   scope, even while a lower owner has its own standalone operation. Keep that
   narrow authority distinct from generic ENV callback mutation permission.

This is a finite specification correction for the proposed method, not a demand
to rescan BANK/core or redesign world snapshots. A precise issuer-owned pure
predicate can be implemented in the ENV/helper slice; it has not yet been fully
defined by the supplied proposal.

## P2-2: Name and enforce the finite post-publication failure disposition

Step5 currently says failure after runtime publication requires “the actual
owning failure/quarantine policy”; step6 releases after the controller's “actual
success/failure disposition.” No such concrete source-owned joint policy or API
is supplied. It cannot be assumed to exist.

Actual ENV install performs phase/record/release/VFS checks BEFORE setting
`restoring` and entering its quarantine-on-error try block. If runtime/BANK has
already published and one of those earlier ENV checks fails, ENV can remain
fresh-bound while runtime/BANK is restored. Errors inside ENV's mutation try do
quarantine ENV, but that does not automatically classify or quarantine the other
owners. `abandon_episode` requires the exact current accepted token; a fresh-bound
destination has none. It is therefore not an available public cleanup API for
this failure. Existing scope expiry releases references/exclusion; it is not a
terminal transaction failure state. The idle admission gate also supplies no
joint completion outcome or fail-closed publication policy.

There is also a concrete before-publication cut: release has been issued before
runtime.install, which may consume its handle and refuse stale membership due
to the core's permitted retirement drain. The protocol must not leave that
privately issued release usable as an alternate successful ENV-only install,
advertise the consumed handle as retryable, or silently reprepare to erase the
failure. This does not require rollback or indiscriminate whole-owner poison;
it requires explicit capability ownership and failure handling for this attempt.

Required finite amendment:

1. Name the source-controlled owner of the restore attempt and its exact phases:
   prepared, release-held, runtime-publication started/completed, ENV-publication
   started/completed, and terminal failed/complete as applicable. Identify the
   actual observation establishing each cut, including child completion failure
   that may escape after a publication assignment.
2. For each refusal/error cut, define which owner remains unchanged, which may be
   partially changed/uncertain, who consumes the real child outcome, and which
   later healthy publication/use is refused. Preserve original exceptions and
   forbid duplicate installation. Keep genuine stale no-publication refusal
   distinct from uncertain post-publication failure.
3. Specify how the controller keeps the release/prepared/native capabilities
   private and unusable for success after failure, and how failed runtime/ENV
   combinations are prevented from reentering healthy flows. If this requires
   a new terminal failure state or owner API, name its exact issuer, authenticated
   inputs, assignment/effect policy and allowed call cut. If existing APIs suffice,
   provide their actual source-qualified contract. Do not invent fresh-bound
   abandonment or say “quarantine” without an enforcing owner path.
4. Add genuine fault witnesses at the prepublication stale-token cut, runtime
   publication/completion cut and ENV precheck/mutation cuts. Require the actual
   failure disposition before releasing the outer gate; no fake rollback, blanket
   child quarantine, token refresh or success-by-exception-catching.

This additional finite owner protocol is already required T26 work, not optional
hardening. It can be separately bounded if necessary, but full C3 restore
qualification cannot declare it discharged merely because pure callbacks and
healthy restore fixtures pass. The proposal may document an enabling interface
slice while this mandatory protocol remains open; it must not relabel that slice
as completed joint restore safety or drop the original18 G3/G4 obligations.

## Scope, caps and next review

No new BANK/core/runtime API is proven necessary for the pure ENV check. The
post-publication protocol may need a separate source-owned controller/owner
change; that is an explicit unresolved implementation dependency, not permission
for this reviewer to inspect or edit another body. Before APP authorization,
assign finite exact files/whole-body ceilings for ENV/helper implementation,
the real consumer choreography and its failure-policy owner/tests. The current
reviewer's4434/four custody leaves566 lines below5000; adding an unrelated
consumer/test body is not free. Preserve source boundaries by splitting coherent
producer/caller packets at root if needed, without weakening required behavior.

Approve neither a generic reentry exception nor an unspecified all-child failure
policy to fit a budget. Return a precise additive proposal addressing P2-1 and
P2-2; the admitted ordering/currency facts can be reused unchanged. Existing
qualified C2 diagnostic/component evidence can retain its separate disposition
while C3 design repair continues.
