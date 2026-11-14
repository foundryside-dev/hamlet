# APP-C2 ENV contract v2 — finite reverse-call authority

2026-11-14. One metadata/design revision responding to the independent P2 review.
No APP implementation, tests, application imports, runtime, Git action or new
implementation body read. This author retains only the previously measured ENV
2889 body, SHA256 `e5a447b0e3d45c861e2fd5e3adcde799f80581053a9512f10af1b365509d8409`.
The reviewer's separate C1 helper read is NOT part of this author's custody.

This version incorporates [v1](T18e-R0-PARENT-ENV-C2-PROPOSAL-v1.md), SHA256
`ac73d33427e0c4c4d708a11010f7e278b577978fa5075c3e41e241078778f667`, with the
replacements below. V1 remains byte-for-byte historical evidence. Its public
retention/binding API, full ingress/role inventory, direct-BANK empty route,
domain-before-owner ordering, 4800/three-body budget and mandatory later
completion/inventory/raw/manual/recurrent/constructor/restore/runner dependencies
remain normative. Sections below replace v1's tentative continuation paragraph,
resolution question 8.2, affected acceptance wording and C1 sequencing condition.

Reviewed change request: [independent review v1](T18e-R0-PARENT-ENV-C2-INDEPENDENT-REVIEW-v1.md),
SHA256 `b55471f9520e93af1f63674de0379aeeb904290bd1fe4084e00c4cf22ecdbf14`.
Original callback facts remain [the sealed POP supplier](T18e-R0-PARENT-C2-CALLBACK-GUARD-FACTS.md),
SHA256 `e1de4d895c218765d6538fc559a9f973e732bd5bb8064a92c93149fdcf7298f3`.
Current supplementary POP facts are sealed in
[claim predecessor facts v1](T18e-R0-PARENT-C2-CLAIM-PREDECESSOR-FACTS-v1.md), SHA256
`95f05b4e9f3ca90ff2c5f7433a51b94b1864e5e3f8f71fbc8605343c31e5f7ec`, supplied
by root's already source-bounded `bac_pop_standalone_step_prepare`, using unchanged POP3163 SHA256
`6c4f7ca085f0a7db34f42bebe22f0240ed12825627c13bcffb3c0d3be3f99022`; they are
attributed metadata, not an extra body inspection by this author.

## 1. Exact source facts and authority being added

Real claim first requires its authentic PreparedVectorStep identity in POP's
registry and stage `prepared`. It then calls `_step_record`, which rejects absent
or foreign POP accepted identity and calls `_validate_owned_training`. That sends
`accepted=prior.accepted`, `participation=self._initial_decision.participation`,
`predecessor=prior.observation` to ENV (POP944–953). This predecessor is POP's
independently owned prior reading, NOT the identity of ENV's outbound predecessor
clone or public current_obs. POP independently checks owned observations,
completion/counts/activity, later checks the claim argument and compares the
retained candidate before publishing participants/stage. ENV must preserve all
of these producer checks; its reverse validation is not a substitute for them.

Every healthy current POP reset seals initial participation before publishing
its accepted activation. A genuine unowned/None-accepted POP claim cannot succeed.
The existing unowned fixture establishes inference selectors, not an unowned
positive POP claim. This corrects the tentative positive-unowned-claim assumption
in v1/review acceptance; it does not remove a supported POP capability. ENV's
separately supported no-decision/manual route remains preserved, with its actual
fixture-driver qualification still required as in root's R121 D2 reconciliation.

The new continuation is an **ENV-issued, single-use permission to perform one
exact current physical validation returning None, or terminal current-episode
runtime-failure denial**. It issues no step claim, positive receipt, completion,
release or healthy-publication authority. Real POP alone authenticates and
publishes its claim; the outer controller alone earns its real effect receipts.

This explicitly states the existing cooperative callable/transparent-observer
boundary. The configured callback may delegate the one exact validation, or
cause fail-closed denial. ENV does not infer that arbitrary callable code is POP,
inspect the Python stack or authenticate immediate caller origin. Code explicitly
run by that configured callback outside an ENV guarded subcall shares only this
finite cooperative permission. It cannot turn it into POP completion authority.
This is a clarification of the narrow permission, not a new trusted-peer mutation
exception. A callback replacing genuine POP claim with fabricated successful
claim/completion remains outside the accepted protocol; C2 supplies no proof or
adapter legitimizing it. A transparent observer must forward the real callback
once, preserve arguments/result/exception, and must not pre-consume its validation.

## 2. Private record and issuance

No new public API, permit issuer or caller-supplied route flag is added. ENV's
source-controlled outcall seam allocates a private, nonportable record under
already-held ENV/common custody immediately before ONE actual callback call.
The record retains:

* exact ENV and outer method-call identity, selected edge kind and callable;
* actual Thread object/PID; exact retained ENV scope and bound RNGOperation when
  present, or exact ordinary admitted ENV call identity when standalone;
* exact current accepted object, world generation/revision and actual stored
  role-owner/callback identities; claim additionally retains exact outbound
  PreparedVectorStep and the current committed participation result/reading
  references from ENV's own producer state, if such a decision exists;
* state, a consumed-validation bit, a terminal-denial bit and the actual first
  validation exception if one occurs. These live only until the outcall unwinds.

No copy of a token, reconstructed reading, serialized record, generic method
name or ambient flag is positive authority. Entry/identity checks happen before
any candidate tensor work. The record cannot be issued by a callback, reused by
another call, transferred across threads/PIDs or made persistent by restore.
Scope binding authenticates admitted execution only; this record does not claim
new inventory or completion certification. Existing true flags remain checks,
not substitutes for the mutex or record.

There is at most one active external continuation for this ENV call. Issuance is
disabled during validator execution, cleanup, ordinary body/helper execution,
receipt validation and any nested public entry. Internal source-owned private
implementations remain distinct; none can mint a public callback permission.

## 3. Claim state machine and argument policy

At the actual stored claim invocation, issue `CLAIM_READY`. The exact accepted
identity must still be current. Capture whether ENV has a committed participation
decision; this is not inferred from callback strings, a public phase flag or
borrowed POP fields.

| Current state / attempted edge | Transition and required result |
| --- | --- |
| CLAIM_READY, committed decision present, first `validate_initial_participation` | Atomically consume the single validation slot and enter VALIDATING BEFORE tensor/property/equality work. Require exact recorded accepted and exact current committed participation object. Then execute the existing complete validator under held custody. |
| CLAIM_READY, no committed decision | No participation-validation slot exists. The configured no-decision/manual claim can return without this check; an effectful participation entry refuses. This is not a positive unowned POP claim. |
| VALIDATING, any effectful public reverse validation, abandonment, peer operation or new scope | Refuse before that nested entry's effects. Keep the outer consumed slot/state; no inherited permission and no second record. Narrow lock-free accepted-token identity checks remain non-authoritative. |
| VALIDATING returns normally | Set CHECKED; slot stays consumed. |
| VALIDATING raises E, including argument/currentness refusal | Retain exact E; set CHECK_FAILED and terminal denial before propagating E. The slot stays consumed even if the callback catches E. |
| CHECKED/CHECK_FAILED, second participation validation | Refuse before its validator body/tensor work; never reset the slot or replace the first failure. |
| CLAIM_READY/CHECKED/CHECK_FAILED, exact runtime-failure cleanup | Enter terminal CLEANING as specified below; it is not another validation slot. |
| Callback returns | First expire external permission. For a committed-decision route require CHECKED and no terminal denial; otherwise refuse before the first ENV world-revision/physics write. No-decision route requires no terminal denial. Then retain all existing phase/token/participation rechecks. |
| Callback raises | Expire permission in finally and propagate the actual callback failure under the precedence rules below; no ENV body continuation. |

The validator's predecessor must be authenticated by **content**, not equality
of Python object identity with ENV's clone. Only the recorded accepted and exact
recorded/current committed participation are eligible. For this single request,
the existing ENV validator checks actual tensor geometry/dtype/device/finite
reading, current committed physical state and equality with ENV's retained
committed observation. It runs those checks without weakening or skipping them.
Successful return means exactly that current reading passed, not POP-origin or
claim proof. The legitimate POP-owned `prior.observation` passes this same
policy. Equal-but-independently-owned predecessor storage remains supported;
foreign token/participation, changed content, wrong layout/device and stale
generation/revision do not gain success by consuming the slot.

Do not add an extra public cloning/comparison callback to authenticate arguments.
Consume and suspend before the existing checks touch tensors; their rejected
prefix remains actual work and belongs to the separately required inventory.
Do not claim wrong-content refusal is zero CUDA work. Identity-ineligible
accepted/participation refuses before that validator's tensor prefix, although
ENV.step's earlier predecessor/action/activity clones already occurred.

This record does not authorize `validate_initial_participation_reading`: claim's
actual producer uses the active-only validator. Owned selector/query reading
validation remains an ordinary guarded ENV entry under its correct scope; it is
not another claim continuation. A generic allowlist of both validators is not
permitted.

## 4. Empty-owner proof records

Use the approved finite owner set: ENV plus actual activation-bound BANK's
DIRECT retained custody, with no runtime-delegated scope. Existing standalone
empty abandonment also remains supported. Iterate the actual retained consumers
in existing order, population then BANK; each actual proof call gets a separate
private `EMPTY_READY` record tied to that exact owner and captured callable.
Getattr/callability lookup occurs with no external continuation armed. Do not
replace the owner with runtime or issue a fake proof.

`EMPTY_READY` allows zero effectful participation checks and at most one exact
current-episode runtime-failure cleanup. POP's genuine empty proof already
requires its actual idle state and performs only ENV's lock-free accepted check
on the reverse edge. BANK's genuine accepted callback is also identity-only.
Those identity checks have no consumption count because they confer no owner or
publication authority. Their existing exact-token policy is unchanged.

Normal callback return expires that owner's record BEFORE ENV validates the
actual `empty_episode` receipt/fields. Only successful genuine receipt validation
allows the next owner call. A failure or terminal cleanup stops the loop; no
second owner proof is issued under the first record. Receipt-validation hooks
have no inherited continuation. After both genuine proofs, ENV's own ordinary
empty-abandon body proceeds under its original method guard; it does not borrow
a callback permit. Empty proof never becomes positive closure/cadence/release.

## 5. Terminal cleanup and error precedence

Only `abandon_episode(accepted=record.accepted, reason="runtime_failure")` is
eligible. Check exact accepted identity and literal built-in reason before
calling the existing cleanup implementation. Empty abandonment, reset, restore,
activation, step, close, release and new scope entry are never cleanup rights.
Cleanup is eligible only at callback level in CLAIM_READY/CHECKED/CHECK_FAILED
or EMPTY_READY. It is unavailable during VALIDATING, CLEANING, after expiry, in
ENV-dispatched body/helper work or from another call/thread/episode.

Before cleanup body work, mark terminal denial, enter CLEANING and disable all
external continuation rights. Execute the existing exact-current-episode
fail-closed implementation, preserving its participation-fence escape and
quarantine rules. ENV's own private quarantine operations inside its validator
remain legal internal operations; they are not public reentry permissions.
On success or failure, finish in DENIED; no repeated cleanup or other callback
effect can reopen the record. Nested cleanup hooks therefore cannot acquire a
second cleanup permission. If cleanup fails before phase assignment, the record
still forbids outer healthy continuation. When a callback swallows cleanup and
returns, ENV refuses before physics/proof-loop progress irrespective of phase.

Error precedence is explicit:

1. A callback's escaping exception remains that exact exception object. Record
   expiry/reference release performs assignments only and must not replace it.
2. A validation failure E that the callback swallows remains retained. If the
   callback returns, ENV rethrows that same E before ordinary body work, instead
   of manufacturing success or a replacement validation exception.
3. Genuine POP failure cleanup retains its existing behavior: POP catches a
   cleanup error and adds it as a note on its original Exception, then propagates
   the original failure. C2 must neither swallow that note nor add a new
   exception from continuation finalization. ENV cannot infer an exception
   caught privately inside arbitrary callback code; no stack inspection or
   invented exception provenance is introduced.
4. If a configured observer explicitly raises a different non-cleanup exception
   after a failed check, preserve its ordinary exception/chaining behavior and
   terminal denial; C2 does not reinterpret arbitrary callback causality. The
   real producer/transparent-observer controls must preserve the real primary.
5. Cleanup without an earlier failure is a permitted fail-closed denial, never
   success. If it returns and the callback returns, raise a deterministic ENV
   continuation-refused error before body progress; if it raises, preserve the
   escaping cleanup error. No healthy-result guarantee comes from that route.

Normal and exceptional exits clear the private record, pins, callable/argument/
exception references and active link before any subsequent ENV body/helper
dispatch. The still-held outer mutex/scope is released only by its owning
context. Fresh later public calls follow their actual current phase/health
policy; they cannot reuse any consumed or expired continuation.

## 6. Required causal controls

Use the genuine supplied fixtures and source-qualified producer calls, with
transparent observers only. These are required implementation evidence, none
executed here. They refine v1 cases 3/4/6/7; its remaining cases stay required.

* Genuine owned claim: real `make_parent`/reset/activation/candidate/prepare;
  ENV performs the single real claim; observe the exact accepted/participation
  and genuine POP-owned predecessor reaching the active validator once. Keep
  the independently owned predecessor; do not substitute ENV's clone or force
  private POP state. Exercise ordinary and explicitly bound composition.
* Transparent claim observer forwards the real callback exactly once and
  preserves its result/exception. Pre-consuming validation then forwarding
  must fail at the genuine second check; it cannot fabricate a successful POP
  claim/completion. Unrelated callback return values are never fixture authority.
* Genuine unowned selector controls remain healthy; attempted unowned/None or
  foreign accepted public prepare/claim refuses at actual POP authority checks.
  Do NOT label this a successful unowned claim. Preserve the source-supported
  no-decision manual ENV route's zero-check policy; its positive executable
  driver remains the required R121 D2 fixture work, not a fabricated C2 claim.
* Inside the actual allowed validator's tensor/observation work, a transparent
  hook attempts effectful participation validation and runtime-failure cleanup.
  Both refuse before their own bodies; the legitimate outer validator still
  delegates its real work. Repeat during cleanup. Assert no second slot/record,
  no peer physics/lifecycle effects and no swallowed-refusal authority leak.
* After the real claim returns, an actual ENV body/helper hook attempts the same
  reverse operations. Its former record is expired. Existing legitimate raw
  bars/helper reads remain available under v1's explicit cooperative raw policy;
  they confer no callback mutation or validation permission.
* Repeated validation, changed accepted/participation, wrong reading content or
  layout, stale identity/revision, cross-thread/PID and foreign-scope attempts
  distinguish identity-before-work refusal from a genuine validator's reached
  tensor prefix. A caught validation failure cannot yield healthy outer progress.
* Real owned-state failure in POP before/after the validator reaches genuine
  runtime-failure cleanup. Preserve exact primary object and existing cleanup
  note; ENV is denied and no first physics write follows. Separately inject
  callback failure before the check, after successful check, and after a failed
  check; exercise both propagation and swallowed-failure denial.
* Genuine all-retired standalone and ENV/direct-BANK bound empty abandonment
  obtains actual POP then BANK proofs, separate expiring records, and no
  participation-validation permission. Test first-proof failure, second-proof
  failure and receipt-validation hook reentry without synthetic proof issuers.
* On every normal/error path observe no retained record or execution references
  after exit. A later genuine operation cannot inherit old permission. Preserve
  retained actual owner exclusion through the independently specified outer cut.

Do not claim an impossible positive unowned POP path merely to meet a test label.
Do not remove manual/no-decision behavior because its old fixture is invalid.
The source fact changes the expected result of that specific claim control;
the genuine manual fixture remains an explicit prerequisite for its own eventual
positive qualification.

## 7. C1 dependency status and next action

Root's [R121 owner reconciliation](R121-OWNER-RECONCILIATION-v1.md), SHA256
`91bda13dd0760a64c13322c4f3f5a5fdb47edd3baf3523f7e4463988b597284e`, establishes
C1 component evidence only, with full item 8/owner integration still pending
real POP step/restore lineage and fixture repairs. Nothing in this revision
accepts C1 integration or waives those failures. After this finite design is
independently approved, root may grant C2 prerequisite enabling implementation
while C1 remains explicitly component-only; full qualification is not silently
inferred from that sequencing. Root still owns the sole APP writer baton.

Final writer/reviewer budget remains ENV<=3350 + new ENV helper<=450 + focused
tests<=1000 =4800/three bodies. No extra implementation body is authorized by
this clarification. Source-complete inventory and exact completing-owner
consumer association remain mandatory later; no arbitrary invocation receipt,
completion bool, blanket child quarantine or new recovery route is introduced.
