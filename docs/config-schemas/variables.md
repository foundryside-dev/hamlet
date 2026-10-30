# Variables: the canonical declaration contract

Declaration-store Cut B replaces the environment-variable, VFS-profile and static-overlay
languages with one required pack-scope `variables` declaration. A filename such as
`variables.yaml` is a convention; content identifies the declaration. See
[discovery and source provenance](declarations.md).

```yaml
variables:
  version: '1.0'
  extents: {}
  item_profiles: [default_item]
  declarations:
  - id: day_phase
    scope: global
    type: scalar
    lifetime: episode
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

- **Scope:** `global`, `agent`, `agent_private`, `item`, `pair`, `affordance`, or
  `message`. Storage scope and observation support are separate contracts. `message`
  requires `extents.num_message_slots`; no other scope takes an extent. `affordance` rows
  are the level's affordance count, the only authority: there is no `num_affordances`
  extent, and an `extents` block that declares one fails as an extra field. There is no
  `zone` or `group` scope: both were storage with no publisher and no write path, and were
  deleted (an old declaration fails validation).
- **Type:** `scalar` (float32 storage), `bool`, supported fixed/dynamic vectors,
  references, tensors or `message_token`. There are no authored `float`, `int` or
  generic `vector` aliases. Tensor shapes and dynamic vector dimensions are explicit.
- **Lifetime:** `tick` resets before each step; `episode` resets with the environment;
  `persistent` retains state across episode resets. Authors choose this independently
  of filename or scope, subject to item-arena restrictions below.
- **Initialization:** an explicit `initial_value`, or a supported tensor
  `initial_value_mode`. Reference null is an explicitly unbound value. Omitting a
  reference initial value is not the same as declaring null. A lifetime reset re-runs
  the declared initializer: a literal and the deterministic modes (`zeros`, `ones`,
  `eye`) restore the same value; `random_normal` and `random_uniform` draw afresh on
  every reset of the variable's lifetime from torch's global RNG, the stream
  `seed_all` seeds, so a run is reproducible per seed rather than frozen to its first
  draw. `shape`, `initial_value`, `initial_value_mode` and `initial_value_params` all
  enter `variable_schema_hash`.
- **Expression:** optional for global/agent variables; it must have an explicit initial
  value. Dependencies are resolved and ordered before execution. Scalar expressions use
  the expression DSL's numeric types; they do not promise integer registry storage.
  The compiler proves output shape: global scalar/bool expressions produce a scalar,
  agent scalar/bool expressions produce an agent batch. An agent expression may read
  any global variable by bare name; the global profile evaluates before the agent profile
  each tick, so an agent expression sees this tick's global value. A global expression may
  not read agent state (scope widening); it refuses at compile. A variable id may not
  equal a meter name; the compiler refuses it at the symbol table with both origins
  (`SYMBOL_METER_COLLISION`). Vector/tensor expression outputs
  and functions without a qualified shape refuse. A constant belongs in initialization.
- **Exposure:** an empty list means hidden. Exposed variables require a supported bounded
  `normalization`; normalization on a hidden variable is refused. Exposure does not confer
  new privacy guarantees.
- **Semantic type:** `temporal` or `custom`. An exposed variable's token descriptor carries
  it as a one-hot; a global `temporal` variable with `expression: tick` and a cyclical
  normalization is the pack's clock. The former members `bars`, `spatial`, `affordance` and
  `effects` named groups of the deleted grouped observation vector and fail validation.

Tensor modes `zeros`, `ones` and `eye` can lower to exact declared literals for token
identity. Exposed random initializers are refused because token identity needs an exact
literal initial value and a random draw has none. Irrelevant, conflicting or malformed
initialization parameters fail validation.

**Token identity and the brain.** An exposed variable's token identity is its declared
descriptor: scope, semantic type, normalization kind and bounds, dtype, lifetime, declared
initial value, element count and tensor shape — never its name or slot. Two exposed
variables equal in every one of those are one token to a permutation-invariant encoder, so
when the level's effective brain is `token_set` or `recurrent` (both pool through
`TokenSetEncoder`) the compiler refuses the pair with `[TOKEN-IDENTITY]` at the second
declaration's `file:line`, naming the first. A flat brain (`feedforward`, `dueling`) reads
slots by position and compiles the same pack unchanged. The same rule, under the same brain
gate, covers deployed affordances on an aspatial substrate (interaction type, duration,
opening hours, reachable meter writes; with position lanes two affordances differ by where
they are every episode, and an affordance outside `enabled_affordances` is padding) and
observable catalogued effects (scope, duration, reapply policy — not what the effect writes;
an `observable: false` effect is never published). Every other token-spec refusal —
exposure rules (`[TOKEN-EXPOSURE]`), item or effect capacity (`[TOKEN-CAPACITY]`), and
declared parameters that cannot enter a token (`[TOKEN-SPEC]`) — is a stage-7
`CompilationError` located at the subject declaration, never a bare `ValueError`.

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

Expressions are evaluated mark-and-sweep: each tick the compiler-derived marks and their
in-profile dependencies are evaluated in dependency order, and a static input is read at its
current runtime value, never its declared literal. There is no evaluation-mode or
debug-logging setting; a `variables` declaration carrying `evaluation_mode` or
`debug_logging` fails validation as an extra field.

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

## Transition phases and evaluation order

Action writes (`actions.custom_actions[].writes`) and transition rules
(`transition_rules.social_residue[]`) name a `phase`. The phase graph is closed and is
exactly the schedule `step()` executes, in this order:

1. `ingest_actions`, `advance_global_time`, `compute_action_legality_masks`,
   `apply_movement_and_wait_costs`, `resolve_affordance_access_and_occupancy`,
   `apply_action_costs`, `advance_interaction_progress`, `apply_action_effects`,
   `apply_completion_bonuses` — run together, with the tick's actions, after the action
   executor.
2. `apply_passive_depletion`, then `apply_threshold_cascades`; then scheduled effects tick.
3. `apply_social_residue_effects`, `clamp_and_validate`.
4. Global then agent expressions are evaluated (see below).
5. `evaluate_terminal_conditions`.

An action write is admitted only in group 1, the phases that run with the tick's actions.
A write scheduled at any later phase is refused at compile with its `actions.yaml`
`file:line`; an unknown phase name is refused the same way for action writes and
transition rules.

An action write applies to the acting agent's row, so its target's declared scope must
have one row per agent: a meter bar, or a variable of scope `agent`, `agent_private` or
`message`. The one exception is an affordance occupancy claim: an action that declares
`source_affordance` may write an `affordance`-scoped variable with composition
`claim_if_free` or `capacity_claim` at `resolve_affordance_access_and_occupancy`, which
writes that affordance's row. Any other target (`global`, `pair`, `item`, or an
`affordance` variable outside that form) is refused at compile with the variable, its
declared scope and the write's `actions.yaml` `file:line`. Whether a pack compiles never
depends on `num_agents`. A transition rule applies at any phase of the graph. Rewards are not a
transition phase: they are computed by the drive (DAC) after the transition.

A write's expression and condition are shape-proved as well as type-checked. A read has
its scope's shape: `agent`/`agent_private` variables, meters and `agent_id` are one per
agent, `pair` is agent × agent, `message` is agent × slot, `affordance` is one per
affordance, `global` is scalar. Values of two different shapes do not combine. The result must
fit the target: an action write takes scalar or agent-shaped values (a non-`append_event`
write to a `message` buffer takes a message-shaped one), and its condition is scalar or
agent-shaped; a transition-rule write to a `global` target takes scalars only, to `pair`
scalar or pair-shaped values, to `agent`/`agent_private` agent-shaped ones, to `message`
agent- or message-shaped ones, and to `affordance` affordance-shaped ones.
An agent-shaped value into a `pair` target is refused, because the language cannot yet say
which pair axis it belongs to. The one admitted mix is inside a pair target's condition:
`observer_mask and chosen_action == STEAL` gates `v[i, j]` by agent j's value. A misfit
refuses at compile (`VTC-WRITE-TYPE`) with the write's `file:line`.

Expressions are evaluated once per instant, after every transition phase that writes VFS
state (action writes, scheduled effects, transition rules) and after
`clamp_and_validate`, so an expression always reads this tick's writes and clamped bars.
The observation describes the state the next action is taken in: within a step the
action, its transitions and effects run at instant k (engine `tick` = k); the clock then
advances to k+1, and expressions, terminal conditions, item respawn predicates and the
observation all see k+1, as does the hour that gates the next action's opening hours.
`reset()` runs the same tail at instant 0, evaluating expressions before the initial item
spawn and the first observation, so no expression ever shows its declared literal or a
previous episode's value. An expression derived from `tick` is therefore `episode`
lifetime, like `tick` itself. The converse is one tick behind: an action write or
transition rule that reads an expression variable sees the value evaluated for the instant
its action is taken in, at the end of the previous step (or by `reset()`).
A variable that carries an `expression` is owned by it: an action write, transition-rule
write or command-pipeline write (effect, affordance interaction, item hook) that targets it
would be overwritten by evaluation, so it refuses at compile (`UAC-STATIC-WRITE`) at the
write's `file:line`, naming the expression variable's declaration `file:line`.

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
