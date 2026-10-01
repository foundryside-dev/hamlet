# PRD-0004 — Static epistemic access

Status: **accepted at local implementation checkpoint**.
Qualified source: `b70fda104e5061ed2735e8b31b7f8f9caaf99f19`;
[PDR-0153](../decisions/0153-static-epistemic-access-accepted-against-prd-0004.md) records
all eight criteria. Authorized local integration is complete; see the
[postmerge receipt](../evidence/static-epistemic-access/local-integration.md).
Prepared: 2026-10-01 Australia/Sydney. Source baseline:
`bdf64fadc69739c3e204845f9797d08500f46d46` (completed Cut B).
Authority: PDR-0120 intent, rebased after PDR-0151. The planning package was
authorized first; the subsequent explicit owner instruction to execute the plan,
commit and merge authorizes implementation and local integration. Publication is
not authorized by that instruction.
Planning: `hamlet-b59513c8e2`; implementation: `hamlet-a3272e31c0`;
independent acceptance: `hamlet-e911091cb2`.

## Outcome

An author can explicitly deny policy reads and declare runtime-immutable state,
without breaking unrelated simulation steps. Canonical declarations, internal
profiles, accessors, publishers, persisted artifacts and checkpoint identity agree.
An engine-updated hidden variable can still influence a declared reward while it
has no direct policy observation and refuses agent reads.

This is a static role-access contract, not ownership privacy or a security sandbox
against Python code with access to internal tensors. Rewards or deliberately public
derived values can reveal information about hidden inputs; no information-theoretic
noninterference claim is made.

## Accepted bounded contract

Every canonical variable, including item-profile variables, explicitly declares:

```yaml
readable_by: [engine]       # or [engine, agent], in either order
writable_by: [engine]      # or [] for runtime-immutable state
exposed_to: []             # independent selection of direct policy input
```

Readers are exactly `engine` and `agent`; engine read is required. Writers are
exactly `engine`, or the empty set. Duplicate/unknown roles, missing fields and
engine-unreadable declarations fail with declaration provenance. No `acs`,
`actions`, `vtc`, `social_model`, arbitrary actor strings or agent-write selector is
admitted. The engine executes world actions, effects, expressions, rewards and
spawn predicates; choosing an action does not turn its simulation into an agent
registry write. Observation publication reads as agent.

The engine-read requirement is deliberate: current simulation snapshots require
all world state. Engine confidentiality would need a separate dependency-aware
execution design. This package does not claim to implement that design.

`exposed_to: [agent]` requires agent-read permission; contradictions refuse rather
than create silently absent slots. Agent-readable but unexposed state is valid.
Engine-only unexposed state is valid. Existing normalization and supported
scope/type/expression restrictions stay in force, including private-scope exposure
refusal. Permissions never broaden an unsupported observation shape or scope.

Default construction and tick/episode reset initialize declared storage through
private lifecycle operations. They can initialize immutable state. Runtime item
`initial_state` overrides are explicit writes: they require engine-write permission,
even when the override equals the default. Current authored item appearance/command
DTOs do not admit this field; unsupported authored forms refuse. Dynamically
constructed commands and direct runtime overrides receive the same check before
mutation. Runtime immutable means no authored/runtime write;
it does not mean persistent across reset.

All general ordinary and item access entry points require an explicit actor.
The explicitly named `set_engine_value` operation has a fixed engine actor and
still checks policy; it is not an implicit actor default.
Convenience getters use the same permission checks; private raw arena reads remain
internal storage operations behind an authorized publisher plan.
Delete the unused duplicate `ScopedVariableRegistry` and port its meaningful
fixtures to canonical storage. No default actor,
unchecked public convenience path, compatibility overload or boolean bypass flag.
Denied reads/writes raise a consistent `PermissionError` naming variable/profile,
actor and operation. Denial precedes mutation, including same-value writes.
Validated role sets are immutable for a runtime instance, held by one registry-owned
policy authority shared by accessors and publisher plans. Mutable declaration or
profile objects cannot silently alter that authority. Policy changes require a new
instance; this is not a whole-artifact immutability redesign.

VTC carries actual attempted write targets through execution and commits only those
targets. Unchanged snapshot entries are not writes. Equality comparison must never
decide authorization: an executed write of the current value is still a write.
Known authored targets (expressions, action/social rules, reachable lifecycle
commands and item overrides) are checked before runtime construction. Dynamic or
constructed programs retain runtime checks. Conditional denied writes are refused
as declarations, rather than waiting for the condition to become true.

Permission metadata persists in registry definitions and global/agent/item compiled
profiles. Item identity uses `(profile, variable_id)` rather than an arena column.
Permission changes affect canonical variable identity and the existing four-term
VFS identity for registry AND item state, including hidden variables. Load recomputes
this identity and checks definition/profile/token coherence. Bump artifact schema
from 1.28; older versions and missing policies fail loudly. Permission-set ordering
is semantically irrelevant. Token widths/type ABI do not gain permission one-hots.
Exact resume/serving reject a permission-changed VFS; transfer remains a distinct
existing operation, not a permissive resume.

## Acceptance criteria

1. **Authoring:** required permissions on the one canonical model; every live pack
   and executable fixture converted explicitly; missing, duplicate, unsupported,
   engine-unreadable and exposure-conflicting policies refuse with source location.
   No historical variable readers, aliases or defaults return.
2. **Runtime access:** get/set, global/agent convenience reads, engine writeback,
   item reads/writes and their production callers use checked explicit actors.
   Denied operations preserve their target operation state; returned public values cannot mutate storage.
3. **Write intent:** immutable global/agent/item literals construct/reset/step
   normally; an unrelated WAIT does not re-commit them. Known denied expression,
   action, social, effect, affordance and item-override targets fail early. Runtime
   no-op writes also deny; do not silently discard them. Preauthorize complete
   attempted VFS targets before committing transition bars/dones/state, and all
   spawn overrides before allocation/registration. Earlier independent commands
   need not roll back.
4. **Observation:** public permitted registry/item values publish correctly;
   hidden values have no binding or payload. Agent-read permission alone does not
   expose a value. Invalid persisted/constructed publisher bindings refuse.
   Distinct agent rows and item profile/liveness gates retain current behavior.
5. **Witness:** a committed pack shows public and hidden state, a real engine
   mutation, a named hidden-state reward, denied agent access and immutable state.
   Run direct and cache-loaded variants, two rows and at least two episodes.
   Item probes use qualified profiles without depending on the known initial
   item-appearance cache defect; report that exclusion explicitly.
6. **Identity:** hidden/exposed registry/item permission mutations move canonical
   variable/VFS identity and reject exact training/serving resume. Equivalent
   permission ordering leaves semantic hashes unchanged. Cold/cache policy,
   behavior and denials agree; missing/tampered metadata fails load/coherence checks.
7. **Evidence/gates:** bank a full parent hash/trace/reset baseline before edits;
   attribute every identity change and qualify direct-parent and frozen CPU paths.
   No frozen oracle source/tag or frozen-fixture edits. Live register/matrix/input
   manifests may change only for newly measured exact attributions, without widening
   historical allowances. Focused
   tests, fleet validation, lint/type/no-defaults and full local suite pass. Hosted
   acceptance requires terminal-success checks at the exact published head if
   publication is subsequently authorized. Local and hosted states stay separate.
8. **Independent acceptance:** criteria read individually against retained evidence,
   source/caller closure and a committed acceptance decision. Planning, implementation,
   local integration, publication, hosted CI and product learning are separate claims.

## Existing work and exclusions

Cut B lifetime, symbols and typed scope are regression gates. Empty exposure is
already fail-closed; private observation exclusion and hidden-expression execution
already exist. Historical triage tickets are not proof these remain unfixed.

Outside this package: owner-specific reads, observer/source coordinates, distance/
floor/brightness propagation (`hamlet-94e984ca53`), engine-confidential state,
shared-world/item isolation, held-item observation, item locality/capacity, item
appearance cache fidelity, effects-reset, terminal-lane accounting, new observation
types, BAC governance/cognition, Murk, UX overhaul, convergence or CUDA qualification.
No calendar deadline is introduced. Completing this slice does not complete PDR-0120's
dynamic counterpart or close a broad privacy issue whose owner-only contract is absent.
