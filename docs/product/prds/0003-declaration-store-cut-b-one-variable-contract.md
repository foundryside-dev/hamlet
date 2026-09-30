# PRD-0003 — Declaration-store Cut B: one variable contract

Status: implementation locally qualified; integration and hosted acceptance pending.
Execution authorized by John ("please plan and execute B"); delivery checkpoint: PDR-0150.
Prepared: 2026-10-01 Australia/Canberra. Baseline: `599cad15706ac8824c3f8e38276da6440c4816a3`.
Scope authority: PDR-0117, PDR-0121, PDR-0147; Cut A accepted by PDR-0149.
Implementation: `hamlet-89cae04b5e`; included defect: `hamlet-33e520cebd`.

## Outcome and contract

Every authored world-state variable uses one typed declaration, independent of transport
filename. The three historical authoring surfaces are deleted, not translated by a runtime
compatibility reader. A required pack-scope `variables` declaration contains explicit
`version`, `evaluation_mode`, `debug_logging`, `extents`, `item_profiles` (named schema groups,
including empty groups), and `declarations`.

Each declaration explicitly states `id`, `scope`, `type`, `lifetime`, `semantic_type` and
`exposed_to`, plus its initialization and any expression. `profile` qualifies item variables
only. The type vocabulary uses runtime `scalar`, booleans, vectors, references and tensors;
profile `float`/`int` and the environment's old `vector` shorthand are not additional spellings.
Scalar storage is float32; expression numeric types map to that storage explicitly.
An explicit reference null means the declared unbound initial value. Exposure requires bounded
normalization; unexposed normalization is refused. Unsupported scope/shape/expression combinations
are refused before execution. Item storage retains its supported scalar-like types and episode
lifetime; admitting a common DTO does not promise tensor or expression item execution.

Existing configuration is converted explicitly, preserving its initial values, lifetime choices,
expression inputs and exposure. Registry descriptors use one fixed engine access policy; new
`readable_by`/`writable_by` declarations are refused and remain PDR-0120 work. Old overlay role
metadata is removed deliberately; the schema movement must be attributed. Internal runtime
profile products may remain because they are execution products rather than authoring surfaces.

Every declared variable enters the same symbol/type inventory. Unqualified registry IDs are
unique across scopes; item variables use profile-qualified identity. Collisions name both source
origins. Reference resolution must no longer omit variables formerly authored as overlays.

`SlotBinding.scope` is required and typed: variable tokens carry their actual scope, other token
bindings carry explicit null. Publisher dispatch uses scope, not `filler_ref` string shape.
The ref remains the identity used to locate a variable or item-profile element. Cache load requires
scope and canonical coherence; old artifacts fail through an exact schema version change.

## Acceptance criteria

1. One authoring model: historical environment-variable, profile-variable and overlay declaration
   routes are removed. Every surviving pack and executable fixture uses the canonical contract;
   old payloads fail loudly with path/line. No aliases, migration readers or fallback paths.
2. State semantics: explicit initialization, tick/episode/persistent lifetime, derived global/agent
   values and static writes survive compile and cache roundtrip. Reset and step witnesses establish
   the declared lifetime behavior. Item limitations are explicit validation refusals.
3. Symbols: every canonical registry/item declaration is registered under its correct identity.
   Previously unreachable overlay variables resolve through named references; a configured write
   and reward consumer witness establishes behavior for supported runtime scopes. Unknown references
   and cross-source collisions fail with provenance. Close hamlet-33e520cebd only with this evidence.
4. Observation scope: mixed global/agent/item tokens publish correctly before and after persistence;
   dotted registry IDs are not misclassified as items. Unknown item profiles, scope mismatch, missing
   scope and corrupt bindings refuse. Private and otherwise unsupported exposure stays refused.
5. Attribution: a committed 31-case hash and state baseline precedes source edits. Compare the entire
   hash inventory, observations/actions/rewards/reset state against that baseline. Register all
   measured identity changes in a new DIV entry; bisect any layout/environment movement as PDR-0147
   requires. Frozen-oracle CPU matrix also passes without edits to the oracle or frozen fixtures.
6. Gates: focused regressions, pack construction/step, CLI fleet, Ruff, Black, mypy, no-defaults with
   unchanged whitelist, and full local pytest pass. Hosted checks on the pushed implementation tip
   must be terminal-success before calling hosted acceptance passed.
7. Hygiene: current authoring/compiler/VFS references teach the canonical model, internal products
   have explicit owners, and removed callers/tests are updated or deleted. No compatibility debt.
8. Checkpoint: an independent review reads criteria individually; acceptance evidence and a committed
   PDR distinguish implementation, local integration, feature push, CI and broader product outcomes.

There is no new calendar promise in this PRD. Completion is evidence-gated; the Cut A calendar
extension does not silently introduce or extend a deadline for B.

## Exclusions

No new access-role authoring or epistemic/privacy design, compiler graph tiers, incremental
compilation, shared-world redesign, Murk migration, BAC cognition, UI overhaul or convergence
campaign. Existing effects-reset, terminal-lane, held-item observation and item-appearance cache
bugs remain separately tracked. Item-binding persistence tests qualify token identity, not the
separately known initial item-spawn cache defect.
