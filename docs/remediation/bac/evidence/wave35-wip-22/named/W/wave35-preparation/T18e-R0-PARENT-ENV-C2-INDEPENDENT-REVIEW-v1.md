# APP-C2 ENV independent contract review v1

2026-11-14. Reviewer `/root/bac_astra_env_c2_contract`, assigned Astra-medium contract review. Repository AGENTS.md read. Metadata-only review; no implementation acceptance, tests, imports, runtime, Git writes, branch/worktree/copy, or source edits. The sole authored artifact is this review.

**SPEC: FINITE CHANGES REQUIRED. QUALITY: pending that clarification.** One P2 contract gap remains: the finite callback continuation protocol is still a resolution question rather than an implementable, independently checkable contract. The rest of the selected exclusion slice is coherent. This is not a request to design the entire POP/native/cohort system, nor permission to remove existing behavior. Root retains implementation and evidence authority.

## Exact custody

Proposal `T18e-R0-PARENT-ENV-C2-PROPOSAL-v1.md` SHA256 `ac73d33427e0c4c4d708a11010f7e278b577978fa5075c3e41e241078778f667`; handoff `T18e-R0-PARENT-ENV-C2-ROOT-HANDOFF-v1.md` SHA256 `35c26c443dd77fba00e157190b9f3910391ad94e23756fb0768953fa701afb1f`. Both match assignment.

Read accepted parent integration V2, SHA256 `45801f6d05a751b4fa7458278f2c781290c094eafa267a65479efb34d9c427c6`, C1 contract review SHA256 `a8cb7f8d403740f1b938f31734cdf54698779b75911eca4ca95c497290fe760e`, and callback facts SHA256 `e1de4d895c218765d6538fc559a9f973e732bd5bb8064a92c93149fdcf7298f3`; seals verified. Also read the C1 genuine fixture and first-A-only-step suppliers. POP/fixture facts below are supplier-attributed, not newly inspected bodies or newly executed results.

Exactly two implementation bodies charged in full, measured and hashed before inspection, **3125 lines**:

| Body | Lines | SHA256 |
| --- | ---: | --- |
| src/townlet/environment/vectorized_env.py | 2889 | e5a447b0e3d45c861e2fd5e3adcde799f80581053a9512f10af1b365509d8409 |
| src/townlet/exploration/parent_custody.py | 236 | 5b592ac955d8e45b3369d4dac3a1bc2996093dfaa8427d732183d321aada801a |

Targeted ENV regions and the complete C1 helper were inspected. No optional runtime, BANK, POP, core, fixture, or external helper implementation body was admitted. This review does not certify those bodies by implication.

## P2: seal the finite reverse-call protocol before implementation

Sections 3 and 8.2 correctly reject a general callback bypass, but leave “exact single-call consumption and legitimate validator multiplicity” for further review. The proposed binding to the stored callable and current ENV call identifies a dynamic call window. Alone, it does not distinguish the genuine POP validator from an arbitrary nested hook running inside that same window. The distinction matters because the allowed participation validator performs tensor reads and may quarantine, while allowed runtime_failure abandonment mutates lifecycle state and issues/retains an abandonment record. They are not harmless identity reads.

Concrete source: ENV.step calls the configurable stored `_claim_vector_step` after predecessor/action/activity cloning and before its first world revision write; on return it rechecks phase/current token/participation. The POP facts establish claim -> `_step_record` -> accepted validation and optional owned-training participation validation, with fail-closed abandonment possible from owned-state checks. ENV's participation validator itself enters `_participation_busy` and checks physical state; abandonment has an explicit cleanup branch that can run while participation is fenced. A single reusable “claim callback active” allowance would therefore authorize more than a single intended reverse validation, including callbacks reached during its tensor work. A single blindly consumed slot, conversely, can reject a genuine unowned path or fail-closed cleanup. The proposal does not yet select the state transitions separating these cases.

Required finite amendment, before a writer baton:

1. Specify a concrete per-edge continuation record/state machine for claim and each empty-owner proof call: issuer, exact ENV method call and stored callable, thread/PID, accepted identity, parent binding if any, allowed arguments/authorities, consumption, and expiry. State which validator may occur zero times or once and why the actual owned/unowned source permits that count. Lock-free accepted identity validation may remain the separate non-authoritative exception.
2. Specify what authenticates the nested participation call and the fail-closed cleanup call, beyond method name or ambient dynamic extent. Preserve the public callable/transparent-observer surface. If the chosen cooperative trust model intentionally allows a configured observer to perform a narrowly bounded exact validation, say so explicitly; do not label that as proof of POP origin. In either case, prohibit inherited authority while executing the allowed validator itself, repeated consumption, cross-episode calls, and unrelated body/helper hooks.
3. Define cleanup precedence: genuine source-established runtime_failure cleanup must remain available when validation fails, without reopening peer work or accepting empty/positive-close authority. Preserve the primary exception and cleanup-note behavior. Specify whether cleanup is terminal for the continuation and how the outer ENV recheck refuses further effects.
4. Seal executable cases using the genuine fixture: owned claim with actual participation; unowned/no-participation claim; transparent observer forwarding once; nested validation/body hook attempting peer validation and runtime_failure cleanup; repeated/stale/changed arguments; real owned-state failure; callback raising before and after the legitimate check. Demonstrate no leaked continuation after all returns/errors. Refusal assertions must distinguish the preexisting ENV clone/read prefix from effects of the refused nested entry.

This is a contract completion request, not a requirement for stack inspection, arbitrary callable introspection, public permits, or a new generic policy engine. If current source cannot provide the selected distinction within ENV/helper, root must obtain one bounded producer handoff rather than quietly expanding the packet or pretending a boolean authenticates origin.

## Accepted decisions and retained boundaries

- Genuine common admission precedes a new ENV mutex. Explicit binding uses the actual yielded operation, never ambient adoption; ordinary other-thread work waits at admission. Retained exclusion spans child return, parent exit and the consumer window. Per-method activity and existing participation flags remain additional checks, never mutex substitutes.
- The selected empty route is **ENV + actual activation-bound BANK direct custody**, without runtime retention/delegation. ENV activation retains the receipt owners; abandonment calls those owners directly. The current C1 helper makes delegated BANK binding runtime-owned and rejects direct BANK calls without the runtime forwarding permit. Thus this route avoids a real delegated-authority conflict without weakening C1. Runtime-retained empty abandonment remains an explicit required later forwarding dependency. A wrong mixed route may already have obtained POP proof before BANK refusal; no no-effect claim is approved.
- Nine genuine role bindings and real owner receipts remain required. Scope binding authenticates execution admission, not participant/inventory/effect association. No arbitrary invocation receipt or bool can authorize completion publication. The later source-controlled ENV completion consumer, truthful source/destination/rejected-prefix inventory, monotonic uncertainty and healthy-publication refusal remain required and unimplemented by C2.
- Lock-free `validate_accepted_episode` remains only instantaneous identity validation. It must not acquire fresh ENV exclusion from runtime/BANK or certify phase/health. Full WorldBoundaryAuthority methods require ENV guard coverage, not just `_bound_env` lookup. Raw tensor aliases remain a cooperative capability requiring actual retained custody; guarding a getter does not protect later alias use.
- Internal calls and external helper access require explicit dispositions. In particular, a global public-method busy guard must not accidentally reject source-owned bars access from physics/helper code. ENV-only conversion of its internal calls does not itself prove all externally called helper accesses migrated. Preserve those supported accesses with a narrowly stated policy; do not assert automatic alias safety or read extra bodies outside budget.

## Required executable acceptance after amendment

The proposal's cases 1–7 and 9 remain required for C2, with case 8 explicitly required in the later completion packet. The minimum genuine implementation evidence must cover:

- `make_parent`/real enter, `candidate`, genuine POP `prepare_vector_step`, exactly one ENV claim, actual returned handoff and reward/service identities in standalone and explicitly bound ENV/runtime modes. This is component composition, not completed POP progress.
- Real all-retired `begin` and both standalone and ENV/direct-BANK bound empty abandonment; genuine POP/BANK proofs, no manufactured normal closure or cadence advance.
- A fresh nonrecurrent A-only first real POP step, one real replay row below readiness two, actual prepare_close/close effects and release/next reset. Do not substitute direct ENV step for POP completion, change thresholds, or perform a second learning-eligible step and misclassify its missing lineage failure.
- All ingress dispositions, whole boundary-authority calls, internal recursion, genuine reset/participation retries and refusals, standalone restore/cadence identity callbacks, and post-exit lifetime/owner pin cleanup. Include ordinary diagnostic reads and supported raw/manual usage under their stated policy.
- Causal thread barriers proving domain-before-ENV ordering and blocking through child-return/parent-exit/consumer cuts; authentic scope/operation misuse refusals before nested effects; partial acquisition and callback exception cleanup. The finite reverse-call cases listed in the P2 amendment are mandatory, not optional adversarial extras.
- All selected family/scope profiles with real behavior retained. CPU evidence establishes causal control flow only. No recurrent, manual, CUDA, native, constructor/cohort, or runner capability becomes optional because this packet cannot qualify it.

Current root-supplied status is C1 component **67 PASS plus two independent qualifications**, but owner suite **215 FAIL**. Full C1 acceptance item 8 remains blocked by POP step/restore missing lineage and obsolete test fixtures. This review neither independently reruns those results nor closes C1. Dependent C2 preparation can proceed; root must reconcile owner failures and qualification before treating C1 acceptance as complete or granting the proposal's post-qualification writer step.

## Budget and next step

The planned final ENV <=3350 + new ENV helper <=450 + new tests <=1000 = **4800 lines / three bodies** is coherent for a fresh implementation packet, subject to remeasurement and the callback clarification. It leaves 200 lines under the hard ceiling; no extra helper/fixture body is free. This reviewer's separately charged C1 helper adds 236 lines: a follow-on review at all three maxima would be **5036 / four**, so assign a fresh implementation reviewer or demonstrate actual same-reviewer total <=5000 before reading final bodies. Do not drop acceptance or hide executable probes to fit.

Next action: revise only the finite callback continuation contract and acceptance details, preserve exact historical proposal bytes, then independently review the new seal. No source implementation or test execution is authorized by this review. No broader parent/CUDA gate is closed.
