# Variables: the canonical declaration contract

Declaration-store Cut B replaces the environment-variable, VFS-profile and static-overlay
languages with one required pack-scope `variables` declaration. A filename such as
`variables.yaml` is a convention; content identifies the declaration. See
[discovery and source provenance](declarations.md).

```yaml
variables:
  version: '1.0'
  evaluation_mode: mark_and_sweep
  debug_logging: false
  extents: {}
  item_profiles: [default_item]
  declarations:
  - id: day_phase
    scope: global
    type: scalar
    lifetime: persistent
    semantic_type: temporal
    initial_value: 0.0
    expression: tick
    readable_by: [engine, agent]
    writable_by: [engine]
    exposed_to: [agent]
    normalization:
      kind: cyclical_sin_cos
      period: 24
```

The clock is declared once. A level can use `day_length: {period_of: day_phase}`;
it cannot redeclare the same period as a numeric day length.

## Required variable meaning

Every variable declares its `id`, `scope`, `type`, `lifetime`, `semantic_type` and
`readable_by`, `writable_by` and `exposed_to`. IDs identify registry state globally. Item state additionally declares
`profile`, identifying a name in the explicit `item_profiles` catalog. An empty catalog
entry remains a valid schema group for item types with no state variables.

- **Scope:** `global`, `agent`, `agent_private`, `item`, `pair`, `affordance`, `zone`,
  `group`, or `message`. Storage scope and observation support are separate contracts.
- **Type:** `scalar` (float32 storage), `bool`, supported fixed/dynamic vectors,
  references, tensors or `message_token`. There are no authored `float`, `int` or
  generic `vector` aliases. Tensor shapes and dynamic vector dimensions are explicit.
- **Lifetime:** `tick` resets before each step; `episode` resets with the environment;
  `persistent` retains state across episode resets. Authors choose this independently
  of filename or scope, subject to item-arena restrictions below.
- **Initialization:** an explicit `initial_value`, or a supported tensor
  `initial_value_mode`. Reference null is an explicitly unbound value. Omitting a
  reference initial value is not the same as declaring null.
- **Expression:** optional for global/agent variables; it must have an explicit initial
  value. Dependencies are resolved and ordered before execution. Scalar expressions use
  the expression DSL's numeric types; they do not promise integer registry storage.
  The compiler proves output shape: global scalar/bool expressions produce a scalar,
  agent scalar/bool expressions produce an agent batch. Vector/tensor expression outputs
  and functions without a qualified shape refuse. A constant belongs in initialization.
- **Exposure:** an empty list means hidden. Exposed variables require a supported bounded
  `normalization`; normalization on a hidden variable is refused. `semantic_type` uses
  the closed semantic vocabulary. Exposure does not confer new privacy guarantees.

Tensor modes `zeros`, `ones` and `eye` can lower to exact declared literals for token
identity. Exposed random initializers are refused because they have no exact static reset
identity. Irrelevant, conflicting or malformed initialization parameters fail validation.

## Item state and supported consumers

Item declarations use the same model, with `scope: item`, a declared `profile`,
`lifetime: episode`, scalar/bool/reference literal state and an explicit semantic type.
The current item arena does not execute expressions, vectors, tensors or alternate
lifetimes. Those declarations fail validation instead of being silently accepted.

Global/agent registry observation supports float32-backed scalar, floating vector, tensor
and message-token state. Registry booleans, integer vectors and references cannot be
exposed by the current publisher and fail compilation. Item booleans/references use its
float-backed arena and remain supported. Ordinary named reward inputs require scalar or
boolean global/agent state; other scopes/shapes need a separately implemented reduction.

The `eager` evaluator requires non-null literal initialization for global/agent state
and rebuilds static expression context from those literals. Null
references and initializer modes in global/agent profiles therefore require `mark_and_sweep`.
Expressions depending on eager agent statics must still prove a batched output; an agent
static dependency alone supplies no batch axis. Unsupported combinations refuse early.

Global/agent registry variables and item-profile variables have token publishers. Other
storage scopes do not acquire an observation publisher simply by entering the symbol table.
Unsupported exposure fails explicitly; private registry state must not reach ordinary
observation rows. Existing held-item visibility and item-state locality limitations are
separate runtime work, not repaired by this declaration cut.

Supported consumer boundaries are explicit:

| Consumer | Accepted variable input |
| --- | --- |
| Registry observation | Global/agent float32-backed state with bounded normalization |
| Item observation | Profile-qualified scalar/bool/reference arena state |
| Ordinary reward input | Global/agent scalar or boolean state |
| Global effects | `vfs.X` or `global.vfs.X` in its typed schema |
| Agent/private effects | `vfs.X` or `target.vfs.X` in its typed schema |

Symbol registration alone does not supply pair-state reductions or arbitrary tensor
operations to a consumer. Command expressions must satisfy that consumer's type contract.

## Resolution, access and artifacts

Every variable enters the compiler's canonical symbol inventory, including variables formerly
accepted only as overlays. Item symbols are profile-qualified. Duplicate identities are
refused with both source origins; unknown references name the consumer's source location.

Static epistemic access (PRD-0004) requires explicit role lists on every declaration.
Readers are `engine` and optionally `agent`; engine read is required. Writers are
`[engine]` or `[]`. Exposure is `[]` or `[agent]`, and agent exposure requires agent
read permission. Unknown/duplicate roles and missing fields fail with source provenance.
Agent-readable unexposed state and engine-only hidden state are valid.

`writable_by: []` makes a literal runtime-immutable. Private allocation and the declared
reset lifecycle still initialize it. Expressions and known action/social/effect/item-hook
write targets require engine write permission during compilation, including conditional
writes. Runtime APIs also check attempted writes, even if the value is unchanged.
Item `initial_state` is not an authored command/appearance field; constructed runtime
spawn overrides are checked as writes before allocation.

The runtime snapshots validated roles once. `get`, `set`, `get_global`, `get_agent`,
`read_item` and `write_item` require explicit actors; `set_engine_value` has a fixed,
checked engine actor. Item access requires a live row with the matching qualified
profile. Returned values do not expose a mutable storage view. Publisher binding plans
check the same immutable policy authority before batched gathers.

Hidden state can affect a reward without appearing in direct policy observations.
This is static role access, not item ownership, spatial privacy or confidentiality
against Python code holding internal tensors. Deliberately public outputs or rewards
can reveal hidden inputs. There is no information-theoretic noninterference claim.

Registry and qualified item policies, including hidden ones, contribute to variable/VFS
semantic identity. Permission order is irrelevant. Artifacts require schema 1.29 and
coherent declaration/profile/hash metadata. Exact checkpoint resume and serving reject
a changed policy before applying weights; deliberate transfer remains separate.

Compiled variable token bindings carry required typed scope. Publisher dispatch uses that
scope; the reference string identifies the variable/element and does not select its storage.
Serialization preserves scope and checks the canonical binding against the declaration.
Old compiled artifacts fail the exact artifact schema check.

The removed authoring shapes are errors: `environment.variables`, bare static overlays,
`global_profile`/`agent_profile` variable catalogs and the old VFS-profile catalog language
have no reader, alias or automatic translation. Convert source declarations explicitly.

## Acceptance boundary

This language closes declaration and resolution contracts. It does not establish that every
world mechanic, cognitive capability or scenario learns successfully. Cut B measurements and acceptance status, with their limits, are recorded in the product acceptance evidence.
