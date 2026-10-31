# Variables: the canonical declaration contract

Declaration-store Cut B replaces the environment-variable, VFS-profile and static-overlay
languages with one required pack-scope `variables` declaration. A filename such as
`variables.yaml` is a convention; content identifies the declaration. See
[discovery and source provenance](declarations.md).

```yaml
variables:
  version: '1.0'
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

- **Scope:** `global`, `agent`, `item` or `affordance` — four scopes. Storage scope and
  observation support are separate contracts. No scope takes an authored extent, so the
  declaration has no `extents` block: `affordance` rows are the level's affordance count,
  the only authority, and a declaration carrying `extents` (empty or not) fails at parse
  as an extra field. Privacy is not a scope: an `agent` variable
  with `readable_by: [engine]` and `exposed_to: []` is private and keeps every consumer.
  The `zone`, `group`, `pair`, `message` and `agent_private` scopes are deleted, and a
  declaration naming one fails validation.
- **Type:** `scalar` (float32 storage), `bool`, supported fixed/dynamic vectors,
  references or tensors. There are no authored `float`, `int` or
  generic `vector` aliases. Tensor shapes and dynamic vector dimensions are explicit.
- **Lifetime:** `tick` resets before each step; `episode` resets with the environment;
  `persistent` retains state across episode resets, and the demo checkpoint saves it:
  checkpoint resume and live serving restore the saved value (tick and episode state is
  not saved; a resume starts a fresh episode). Authors choose this independently
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
  value, which is also the history seed a `lag` of it reads before the episode has history
  ([history operators](#history-operators)). Dependencies are resolved and ordered before
  execution; a cycle refuses unless a `lag` read closes it. Scalar expressions use
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

**The batch is N independent single-agent worlds** (owner ruling S1, 2026-10-25). Each
row of the environment batch is its own world with one agent in it; no two agents share a
world. So there is no scope relating two agents: `pair` and `message` (and the
`append_event` composition that filled a message buffer) are deleted, because in a
one-agent world a pair has no partner and a message no addressee. `global` is world state,
one value per world (VFS WP13). The world axis is engine-internal: an author declares
`scope: global` and reads it as one scalar (or one declared payload) in their world, and the
expression shape proof still treats it so: a global expression may not read agent state, and
an action write may not target a global. At runtime every reader and writer addresses its own
world's row:

- an affordance or item interaction writes the interacting agent's world; every effect lives in one world (its agent's, its item's, or for a
  global- or affordance-scoped effect the world whose event spawned it) and writes that
  world's row only (`docs/config-schemas/effects.md`); a world whose agent is done writes
  nothing, by rule or by effect;
- a transition rule advances each world's global while that world's agent is active;
- global and agent profile expressions read their own world's globals;
- each world's observation publishes its own row, and the reward reads its own row;
- persistent-lifetime save and restore carry every world's row.

The engine `tick` is a global like any other: all worlds step in lockstep, so the engine
writes the same instant into every row. Episode resets are batch-wide for the same reason:
every world's episode- and tick-lifetime state is re-initialized together. Items are per world
too (their own spawns, state and arena rows; see [items](items.md)), so an item spawn predicate
is evaluated per world: each world spawns when it holds for that world's values.

`affordance` state is per world too: one row per affordance in each world (storage
`[worlds, affordances, ...]`, the world axis engine-internal as for `global`). An occupancy
claim writes its own world's row of the action's source affordance, so a world's claim never
contends with another world's (a world has one agent, so there is no "lower index wins"); a
transition rule on affordance state advances a world's rows while that world's agent is
active, and may read a global, which is its own world's value spread along that world's
affordance rows. An affordance rule still may not read agent state. An effect cannot name
affordance state (it is not in the effect schema), and an affordance variable has no
observation publisher. Persistent save and restore carry every world's rows.

**References stay in their world.** An `agent_ref` in world w holds world w's agent or null
(-1), and an `item_ref` an item row of world w or null: every write is checked, in every
scope, in the item arena and on restore, and a violation is an engine defect. A constant
reference is every world's value, so it is refused at compile: a reference `initial_value`
other than null/-1 (at the declaration's `file:line`) and a constant write expression other
than -1 (`VTC-WRITE-TYPE`). A transition write into a reference must be provably world-local,
by a syntactic rule: -1, `agent_id` (into an `agent_ref` only), a read of a reference of the
target's type, or `where(...)` / if-then-else choosing between those. Anything else, such as
`agent_id * 0`, can name another world's row and refuses at compile (`VTC-WRITE-TYPE`).
Under S1 an `agent_ref` is a nullable self-pointer (bind it with `agent_id`); there is no
traversal spelling (`x.vfs.y`, `x.bar.y`): the referenced agent is the world's own, read by bare
id and `bar.<m>`.

`gather(values, index)` and `scatter(base, index, update)` index the element axis of a
vector or `tensor1d` inside one world's value; a scalar argument (a meter, a scalar
variable) has no element axis and is refused at type check, since its only row axis is
the batch of independent worlds.

**Non-goal: cross-world quantities.** There is no spelling for a value that reduces over
worlds (a batch-wide total, mean or maximum of a global or agent variable). Under S1 such a
value would leak one world's events into another world's observation or reward, so its
absence is the contract, not a gap. A multi-agent world will be a new declared parameter
(agents per world), not a reinterpretation of `global`.

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

Global/agent registry observation supports float32-backed scalar, floating vector and tensor
state. Registry booleans, integer vectors and references cannot be
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
| Command pipelines (effects, interactions) | Global/agent variables by bare id, meters as `bar.<m>`, the bound item's state as `item.<x>` |
| Item spawn predicates | Global/agent variables by bare id, meters as `bar.<m>` |

Symbol registration alone does not supply affordance-state reductions or arbitrary tensor
operations to a consumer. Command expressions must satisfy that consumer's type contract.

## Transition phases and evaluation order

Action writes (`actions.custom_actions[].writes`) and transition rules
(`transition_rules[]`) name a `phase`. The phase graph is closed and is
exactly the schedule `step()` executes, in this order:

1. `ingest_actions`, `advance_global_time`, `compute_action_legality_masks`,
   `apply_movement_and_wait_costs`, `resolve_affordance_access_and_occupancy`,
   `apply_action_costs`, `advance_interaction_progress`, `apply_action_effects`,
   `apply_completion_bonuses` — run together, with the tick's actions, after the action
   executor.
2. `apply_passive_depletion`, then `apply_threshold_cascades`; then scheduled effects tick.
3. `apply_transition_rules`, `clamp_and_validate`.
4. Global then agent expressions are evaluated (see below).
5. `evaluate_terminal_conditions`.

An action write is admitted only in group 1, the phases that run with the tick's actions.
A write scheduled at any later phase is refused at compile with its `actions.yaml`
`file:line`; an unknown phase name is refused the same way for action writes and
transition rules.

An action write applies to the acting agent's row, so its target's declared scope must
have one row per agent: a meter bar, or a variable of scope `agent`. The one exception is
an affordance occupancy claim: an action that declares
`source_affordance` may write an `affordance`-scoped variable with composition
`claim_if_free` or `capacity_claim` at `resolve_affordance_access_and_occupancy`, which
writes that affordance's row in the acting agent's world. A claim composition is an
occupancy claim only: on any other target it is refused. Any other target (`global`, `item`, or an
`affordance` variable outside that form) is refused at compile with the variable, its
declared scope and the write's `actions.yaml` `file:line`. Whether a pack compiles never
depends on `num_agents`. A transition rule applies at any phase of the graph. Rewards are not a
transition phase: they are computed by the drive (DAC) after the transition.

A write's expression and condition are shape-proved as well as type-checked. A read has
its scope's shape: `agent` variables, meters and `agent_id` are one per agent,
`affordance` is one per affordance (in the reading world), `global` is scalar. Values of two different shapes do
not combine. The result must fit the target: an action write and its condition take
scalar or agent-shaped values; a transition-rule write to a `global` target takes scalars
only, to `agent` scalar or agent-shaped values, and to `affordance` scalar or
affordance-shaped ones. A misfit refuses at compile (`VTC-WRITE-TYPE`) with the write's `file:line`.

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
lifetime, like `tick` itself.

An action write or transition rule that reads an expression variable reads the
expression evaluated on the state the write sees, not a stored value: the compiler
substitutes the expression (recursively, through every expression variable it reads)
into the write's expression and condition. A write gated on `rich: bar.money > 0.1` sees
`rich` true on the tick an earlier phase raised `money`, whatever `rich`'s lifetime. The
one exception is an expression that calls a history operator (`lag`, `delta`, ...), which
needs the history rings only the profile evaluator keeps (an expression variable may not call
`elapsed_ticks` or a position function at all: the profile compiler refuses them): it is not inlined, and a write reads its stored value, the one
evaluated at the end of the previous step (or by `reset()`), which the observation the
action was chosen on showed. A `tick`-lifetime one has no stored value while the
transition phases run, so a write or rule reading it refuses at compile
(`VTC-WRITE-TYPE`). A write may not call such a function itself: name the quantity as an
expression variable and read it. Hashes: the write keeps its authored text as identity,
and the expression enters `vfs_hash` through the expression schema hash.
A variable that carries an `expression` is owned by it: an action write, transition-rule
write or command-pipeline write (effect, affordance interaction, item hook) that targets it
would be overwritten by evaluation, so it refuses at compile (`UAC-STATIC-WRITE`) at the
write's `file:line`, naming the expression variable's declaration `file:line`.

## History operators

`lag`, `delta`, `moving_average`, `ema`, `rate_of_change`, `rising_edge` and
`falling_edge` read the past of a value. They run in global and agent variable expressions
only: an action write, a transition rule, an effect or a spawn predicate keeps no history,
so name the quantity as an expression variable and read that. Writes, rules, effects,
interactions and spawn predicates refuse a history operator at compile, by one predicate on
the function registry (every function whose `requires` names temporal history).

- **What they read.** The first argument names a value: a variable (`lag(public_state, 1)`),
  the clock `tick`, or a meter (`delta(bar.energy)`). A computed argument
  (`rising_edge(tick > 1.0)`) has no history and refuses at compile; declare the predicate
  as its own (bool) variable and apply the operator to it. Depths and windows are integer
  literals in 1..256 and `ema`'s alpha a literal in `(0, 1]`; anything else refuses at
  compile (`VFS-PROFILE-COMPILE`). The result has the argument's shape and type rules, so a
  global expression still cannot read an agent variable, even through `lag`.
- **One sample per instant.** After every expression of an instant has evaluated (reset's
  instant 0, then once per step), the engine records the committed value of each value
  some operator reads. `lag(x, n)` at instant t is x at instant t − n. Every other operator
  is defined through it: `delta(x) = x − lag(x, 1)`,
  `rate_of_change(x, w) = (x − lag(x, w)) / w`, `moving_average(x, w)` the mean of
  `x, lag(x, 1), …, lag(x, w − 1)`, `rising_edge(f) = f and not lag(f, 1)`,
  `falling_edge(f) = not f and lag(f, 1)`, and `ema(x, a) = a·x + (1 − a)·ema` of the
  previous instant.
- **Before the history exists.** History starts at each episode with every slot holding the
  value the argument had when the episode began, before instant 0 evaluated: a meter's
  initial value, a static variable's initial value, an expression variable's declared
  `initial_value` (not its first evaluation), and the clock's 0. So `lag(x, n)` before n
  instants exist is that value, `delta(bar.energy)` is 0 at instant 0, and the running
  `ema` starts from it. Never an undocumented zero.
- **Self-reference.** A `lag` read is not a dependency edge: it reads the recorded past,
  which no evaluation order of this instant can change. So a variable may read itself, or
  close a cycle, through `lag` and through nothing else; a self-reference or cycle through
  any other read (including `delta`, `ema`, `moving_average`, `rate_of_change` and the
  edges, which also read the current value) refuses as a circular dependency. A
  "time since" mechanic is one declaration, and its `initial_value` seeds the count:

  ```yaml
  - id: time_since_last_sleep          # configs/L5_multi_agent
    scope: agent
    lifetime: episode
    initial_value: -1.0                # lag at instant 0 is -1.0, so the first tick reads 0
    expression: where(delta(bar.energy) > 0.0, 0.0, lag(time_since_last_sleep, 1) + 1.0)
  ```
- **Lifetime and reset.** History is episode-scoped for every lifetime: `reset()` discards it
  and instant 0 starts it again from the episode-start values. A `persistent` variable's
  episode-start value is the value it carried across the reset, so `lag(p, 1)` at an
  episode's instant 0 is exactly the previous episode's last value (an accumulator
  `p: lag(p, 1) + 1.0` continues), while every deeper lag of `p` reads that same carried
  value until the episode has that much history; the previous episode is not history.
- **Resume.** Checkpoints are written between episodes and resume starts with `reset()`, so
  the persistent snapshot alone reproduces history exactly; history is not checkpointed.
- **Done worlds.** A world whose agent is done is frozen: its history does not advance (its
  expressions keep evaluating, over that frozen history).
- **Identity.** The compiled artifact carries `vfs_history_spec`, the history depth of every
  value read; it is derived from the expressions, whose canonical form (operator, literal
  depths, windows and alphas) is part of `vfs_hash`, so changing a `lag` depth refuses resume.

## One spelling per reference

Every consumer resolves a reference through one resolver (`townlet.vfs.namespace`, VFS
round-2 S5), so a variable is written the same way in a variable expression, an action write,
a transition rule, an effect, an affordance or item interaction and an item spawn predicate:

| reference | spelling | where |
| --- | --- | --- |
| a registry variable | `x` (its bare id) | everywhere; read in this world by its declared scope (S1) |
| a meter | `bar.<name>` | everywhere, including an action write's or rule's `variable_id` |
| the bound item's state | `item.<name>` | item interactions, item-scoped effects, inventory loops |
| the engine clock | `tick` | everywhere |
| the acting agent's row | `agent_id` | action writes and transition rules |
| an active effect's locals | `intensity`, `elapsed_ticks`, `duration_remaining` | effects |

Under S1 a world has one agent, so `self.`/`target.`/`global.` carry no information; an item
is the only second entity a context can have, and `item.` names it. Every other spelling
(`vfs.x`, `self.vfs.x`, `target.vfs.x`, `global.vfs.x`, `agent.vfs.x`, `self.bar.m`,
`target.bar.m`, a bare meter name, `temporal.*`, `env.*`) refuses at compile with the one
spelling to write, at the author's `file:line`. A variable id contains no `.`: a dotted name is
a qualified reference. DAC role fields keep their typed form (`variable: x`, `bar: m`). A
refusal in a variable's own expression is located at that variable's declaration.

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
