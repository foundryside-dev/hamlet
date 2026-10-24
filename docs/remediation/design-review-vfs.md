# VFS design review: first principles

Written 2026-10-24 against `fix/compiler-effects-remediation` at `a79f4551`, after VFS WP1-WP8
landed and round 2 (`review-2026-10-24/findings_vfs_round2.md`) proposed WP9-WP17. Read-only; a
design review, not a bug hunt: round-2 F and S numbers are cited, never re-reported. Evidence:
the four VFS config-schema docs, `VFS.md`, the token design, the 32 `variables.yaml` (eight read in
full), `src/townlet/vfs/*`, the two VFS DTOs, `compilers/vfs.py`, `token_spec.py`,
`token_publishers.py`, `vectorized_env.py` (`reset`, `step`), `effects/context.py`, `bars_v2_config.py`.

## Summary for the owner

The VFS has one good idea at its centre: a variable is a name plus declared parameters, every
consumer resolves it through one compiled symbol table, and the policy sees it as a token whose
identity is the declaration. That idea is sound and should not be reopened. What sits around it
is a declaration surface with roughly 25 author-facing concepts for a job that needs about eight,
a second state ontology (meters) that duplicates the first, three scopes with no consumer, and a
batch model the spec never stated. The five changes, in the order I would make them:

| # | change | one-line reason |
|---|---|---|
| 1 | Rule the batch as N independent worlds, give every non-agent scope a world axis, and delete `agent_private`, `pair`, `message` | It is the only open decision that changes what a policy learns (F4), and today it leaks across lanes in four scopes, not one |
| 2 | One spelling and one resolver: a variable is `x` in its own row, `target.x` for a second entity; the `vfs.`, `bar.`, `env.`, `self.`, `global.vfs.`, `agent.vfs.` prefixes go | Five consumers, five grammars, two of which compile and crash (S5, F6); the web form cannot be built on a surface where the right spelling depends on the file |
| 3 | A meter is a pointer to a variable, never its own thing: `bars.yaml` becomes a level-scoped binding `{variable: energy, depletion: {...}, recovery: ..., lethal_min: ...}` that names any declared variable (stateful, expression-derived such as time of day from `tick`, or a constant with `mutable: false`) and supplies the survival-role parameters, admitted only where the target can carry them (depletion needs a mutable stateful target; a derived or constant target binds with none); the variable owns identity, storage, `bounds` and what happens when they break, `initial`, exposure and the token. The `meters` section of `environment.yaml`, the `bar.` spelling, the `meter` token type, meter `bounds`/`lethal_*`/`initial` and the cascade DTOs go; cascades become rules | Owner ruling (2026-10-24, in session): VFS is the only system for storing variables and features; bars were always meant to be a pointer. This is the project's own role-binding pattern (`money_bar: str` in DAC) applied to the survival role. Today meters are a parallel ontology shimmed into the symbol table (`vtc_write_targets`, `meter=True`), which is why one state has two names everywhere and why hunger and thirst are refused (S3) |
| 4 | Collapse the declaration to nine fields: `id`, `scope`, `type`, `lifetime`, `bounds`, `initial`, `observed`, `mutable`, and an optional `expression`. `bounds` is `{min, max, on_min, on_max}`; each policy is one of `end_experiment`, `end_agent_error`, `end_agent_fail`, `end_agent_success`, `cap`, `reset_to: <value>` (owner, 2026-10-24) | `readable_by`, `semantic_type`, `normalization`-iff-exposed and the three-field initializer are two spellings of one fact each; the form asks nine questions and emits a complete explicit declaration, so no-defaults survives |
| 5 | Make expressions a synchronous dataflow: admit `prev(x)` as the one history primitive, admit action and interaction events as inputs, inline expression variables into write conditions, refuse writes to expression-owned targets | Accumulators and "time since" become one declaration instead of three families (S9), the one-tick lag rule disappears (S4), and the dead history pipeline (F9) is replaced rather than deleted |

Change 3 is also the answer to the brief's two-audience question. A meter is a convenience
layer over a raw variable: the web form's primitive is the meter binding (point at a variable,
give it rates), the practitioner's primitive is the variable itself (bounds and breach policy,
expression, lifetime, exposure), and the first is defined entirely in terms of the second, so
there is one state model with two entry points rather than two state models. A new user never
has to open `variables.yaml` for a survival meter; a practitioner never has to go through
`bars.yaml` to get at one. That is the reason meters keep a declaration of their own.

Do 1 before anything in WP15, 2 before WP12's shape proofs are written (they are written against
the resolver), 3 immediately after 2 because the fold rides the resolver, 4 and 5 together since
the DTO changes once. Change 3 is the largest: it moves `token_type_schema_hash` once (the
`meter` type leaves the roster and its signature becomes the `variable_element` dynamics
block), retires DAC's `bar:` references in favour of `variable:`, and ends the oracle's authority
over bar behaviour. Under zero backwards compatibility all three are free; the risk document is
right that every lock reopens on it, which is the argument for doing it early, not late.

**On the owner's question, whether non-VFS variables were put back because fixing VFS was
harder.** The git record says the original VFS had meters as variables and the v2.1 compiler
wiring took them out nine days later, without a stated reason; section 9 has the commits. Every
round since has tightened the resulting shim rather than removing it: `bar.<name>` admitted as a
second spelling in VTC writes (`vtc.py:421-441`), a meter-name collision refused at the symbol
table (`SYMBOL_METER_COLLISION`), `range_type` on the meter mirroring VFS normalization kinds
(`environment_config.py:79-117`), DAC with `bar:` and `variable:` as parallel references, a
hand-built `meter` token signature instead of a variable descriptor. Each was the smaller change
at the time. Together they are the dual ontology this review names as change 3.

What should not change: the closed expression DSL with a compile-time type checker; the single
roster with files as transport; `extra="forbid"` and no defaults; the three lifetimes; the frozen
access-policy snapshot in the registry; the token model (fixed payload widths, identity by
declaration, presence-led rows, POMDP as a filter); the phase graph as the executed schedule
(kept internal); hashes gating resume; `period_of` for the clock. Section 8 says why. The
in-flight WP9-WP12 (clock truth, hash coverage, visibility mask, shape proofs) are unaffected by
any of this and should land as planned.

## 1. Concept inventory

What an author of `variables.yaml` plus its consumers must hold today, and for whom it earns its
place. P = practitioner, N = new user.

| concept | values today | load-bearing for | verdict |
|---|---|---|---|
| scope | `global`, `agent`, `agent_private`, `item`, `pair`, `affordance`, `message` | P, N (for `world`/`agent`/`item`) | keep 4: `world`, `agent`, `item`, `affordance`; `pair` returns when agents-per-world is declarable |
| type | 17 literals (`scalar`, `bool`, 4 fixed vectors, 2 N-vectors, 4 refs, 4 tensors, `message_token`) | P | collapse to `scalar`, `bool`, `ref`, `vector {dims}`, `tensor {shape}` |
| lifetime | `tick`, `episode`, `persistent` | P, N | keep; refuse `tick` on an expression variable (F10) |
| initializer | `initial_value`, `initial_value_mode`, `initial_value_params` | P | one field `initial`: a literal, or `{mode, ...params}` |
| expression | optional DSL string, global/agent only | P, N | keep; this is the practitioner's power |
| exposure | `exposed_to: [] \| [agent]` | P, N | one boolean `observed` |
| readable_by | `[engine]` or `[engine, agent]` | neither | delete: agent-readable-unexposed has no consumer; it duplicates exposure |
| writable_by | `[engine]` or `[]` | P (as an immutability assertion) | rename to a required `mutable: true \| false`; it is PRD-0004's witness, so keep the bit, and keep it required so no-defaults holds |
| semantic_type | `temporal`, `custom` | neither | delete: one descriptor bit and a clock detector that `expression: tick` plus cyclical range already identifies |
| normalization | 9 kinds, required iff exposed | P, N | fold into `bounds` on the variable: min, max, breach policy, normalization and descriptor are one fact (PDR-0016 already did this for meters) |
| write composition | 11 modes | P | keep 5: `set`, `add`, `mul`, `min`, `max`, plus `claim` for occupancy; `clamp`, `priority_write`, `last_write_wins`, `append_event` go |
| write fields | `variable_id`, `expression`, `condition`, `composition`, `phase`, `priority`, `clamp`, `telemetry_label` | P (4 of 8) | keep `variable`, `expression`, `when`, `composition`; derive the rest |
| transition phase | 14 names authored on writes and rules | neither | internal; a write's family picks its phase |
| transition rule | `id`, `kind`, `phase`, `reads`, `condition`, `writes[]`, `priority` | P (`id`, `when`, `writes`) | `kind`, `reads`, `effect`, `phase` go (S8); family renamed `rules` |
| item profile | `item_profiles: [food]`, `profile: food`, `vfs_profile: food` | P | three names for one edge; declare state on the item type |
| access roles | `engine`, `agent` | neither | roles were the design intent of VFS.md §5.3; two fixed values are not a role system |
| identity rule | descriptor signature equality refuses | P (token brains) | keep for permutation-invariant brains; add declared dynamics; skip for flat brains (S3) |
| hashes | `variable_schema_hash`, `observation_schema_hash`, `action_schema_hash`, `transition_graph_hash`, `vfs_hash`, `layout_hash`, `token_type_schema_hash` | P (resume) | keep; add expression text (F5); never author-facing |
| extents | `num_message_slots` | neither | goes with `message` |
| ambient names | `tick` | P, N | keep; add events (section 5) |

Two spellings of one idea, confirmed in source:

- `agent_private` versus `readable_by: [engine]` + `exposed_to: []`: the scope is a second
  override of the role list (`registry.py:645`) and does strictly less (S2).
- `semantic_type: temporal` versus `expression: tick` + `cyclical_sin_cos`: the clock detector
  needs all three (`universe/declarations.py`), so the first is redundant.
- `bar.energy` versus `energy`: `vtc_write_targets` registers a meter as an agent-scoped scalar
  with `meter=True` so both spellings resolve (`vtc.py:421-441`); profile expressions accept only
  `bar.energy`; a variable id equal to a meter name is refused (`SYMBOL_METER_COLLISION`).
- `item_profiles` / `profile` / `vfs_profile`: one binding, three declarations.

Smallest set that keeps the practitioner's power: `id`, `scope` (4), `type` (5), `lifetime` (3),
`bounds`, `initial`, `expression` (optional, with `prev` and events), `observed`, `mutable`
(required boolean); writes with `variable`, `expression`, `when`, `composition` (5+1); rules with
`id`, `when`, `writes`. That is 9 declaration fields and 3 rule fields, down from 17 and 7. The
form asks: what is it called, who has one, what kind of value, when does it reset, what range,
where does it start, what happens when it breaks its bounds, how does it change, does the agent see it, can anything change it.

## 2. The core model

Today: typed state, plus pure expressions evaluated once per tick after `clamp_and_validate`,
plus imperative writes at 14 named phases, plus token publication. The split between expressions
and writes produces three things an author meets: the one-tick lag rule (`variables.md`
"Transition phases"), the refusal (missing today, F11) of writes to an expression-owned variable,
and the impossibility of an accumulator without a transition rule (S9, cycle refused at
`profiles.py:111-128`).

Three candidate models:

| model | buys | costs |
|---|---|---|
| A. Current hybrid | locality: an affordance's writes live on the affordance; composition across writers in one phase | two semantics for one variable; lag rule; accumulators need three families; phases author-visible |
| B. Synchronous dataflow: every variable is an expression over previous state and this tick's events | one semantics; accumulators and clocks are one line; dependency order proves acyclicity with `prev` as the only back-edge; nothing to phase | economics scatter: `money` would carry every affordance's price in one expression, which destroys the authoring locality that makes affordances legible; occupancy contention is not an expression |
| C. Everything is a phased write; "expressions" are writes at the last phase | one executor | nothing is pure, so no dependency sorting, no shape proof by construction, and the author owns phase order explicitly |

Recommendation: B for state, A's writes kept only where locality or contention demands them.
Concretely: a variable is owned by exactly one of {an `expression`, a set of writers}; the
compiler refuses the other (makes F11 loud). Expressions may read `prev(x)` for any variable
including themselves (the lag-only self-edge of S9), and may read events (`did(ACTION)`,
`completed(AFFORDANCE)`, `started(AFFORDANCE)`), so a counter is
`where(completed(SLEEP), 0, prev(t_since_sleep) + 1)`. Writes keep their place at affordances,
actions, items and rules, and may reference expression variables by compile-time inlining
(S4): a write condition `rich` means `money > 0.1` evaluated on the state the write sees. The
observed value of `rich` is then the post-write one. That is two readings of one name, but they
are the two an author expects (the condition on what I saw, the observation on what resulted),
and it deletes the lag rule from the spec. Phase names leave the authoring surface entirely: an
action write runs with the action, an affordance write runs at the interaction, a rule runs
once per tick after passive dynamics. The graph stays as the internal schedule.

## 3. Batch and world model

Ruling: `num_agents` is a batch of W independent worlds with A agents each; A = 1 today; A
becomes declarable at pack scope, because how many agents share a world is a world fact every
level inherits. `experiment` is the only pack-scope declaration about the run and today carries
only a name and metadata (`experiment_config.py:29-39`); `training.yaml`'s `population.size` is
the per-level batch width, not the world shape, and must stay separate from it. This
is what `token_spec.py:1294-1301` has said in a docstring since the token cut, what DQN over
eight lanes assumes, and what the second-opinion review recommended. The spec never wrote it
down (S1). The alternative, one shared world, makes every shipped pack's eight lanes one town,
which no reward or terminal was designed for.

Consequences per scope and structure:

| scope / structure | today | under the ruling |
|---|---|---|
| `global` | shape `()`, one slab, broadcast to every lane (`registry.py:350-353`, `token_publishers.py:893`) | rename `world`, shape `[W]`; `tick` stays world-scoped and is uniform by construction |
| `agent` | `[W*A]` | unchanged (`[W, A]` flattened); expressions and writes address the row |
| `agent_private` | `agent` with a silent role override | deleted (S2); privacy is `observed: false` |
| `pair` | `[N, N]` across all lanes | `[W, A, A]`; refused at compile while A = 1, because it has no non-diagonal entry |
| `message` | `[N, slots]`, self-addressed, unreadable (F8) | deleted until communication is designed (S6) |
| `affordance` | `[F]`, one row per affordance shared by every lane (`_scope_prefix_shape`) | `[W, F]`; today a `claim_if_free` by lane 3 blocks lane 5, the same shape as F4 and unreported because occupancy was never run |
| items | one `ItemManager`, `max_items_in_world` shared (`vectorized_env.py:868-873`) | per-world item pools: an apple picked up in lane 3 must still exist in lane 5 |
| strata | one grid, one affordance layout per reset for all lanes | fine as W copies of one map; the capacity check `len(affordances) + num_agents` (`vectorized_env.py:1600`) becomes `+ A` |
| multi-agent level | `L5_multi_agent` declares pair and affordance state nothing writes (F14) | `agents_per_world: 2` in `experiment`; agent token capacity 1; `pair` becomes legal; the L5 pack is rewritten against that or deleted |

Scopes after the ruling: `world`, `agent`, `item`, `affordance`, with `pair` gated on A > 1.
Four for the form, five for the practitioner. The ruling is a storage-shape change in the
registry, the publishers, the VTC write paths and the effects context, so it should be made
once, before WP12 writes shape proofs against the current shapes.

## 4. Observation surface

The token model is the right contract for both audiences, for a reason the spec states and the
new user never has to learn: the form author declares `observed: true` and the compiler owns the
rest. Fixed payload widths, per-universe capacities and identity by declaration are what make
`token_type_schema_hash` identical across a 2-D grid and an aspatial world; nothing here should
be reopened.

Where the identity rule helps: two exposed variables that are genuinely the same declaration
would alias under mean pooling for every weight setting (token design §1, DRL round 2). Where
it fights the author: hunger and thirst, both agent scalars in [0, 1] starting at 1.0, are
refused, and the message at `token_spec.py:1107` says to change `semantic_type`, `lifetime`,
normalization range or initial value. That is "alter behaviour to satisfy the compiler", the
sharpest example in the subsystem of a refusal failing the new-user half. Two fixes, both
needed: gate the check on a permutation-invariant brain (a `dueling` net distinguishes slots by
position and does not need it), and put declared dynamics into the descriptor, as meter
signatures already carry depletion rates. Under change 3 the two meters-as-variables would
differ by their declared passive rate, a bounded behaviour-bearing feature, which is what token
ruling 2 admits; an expression hash would be a name by another route and belongs in `vfs_hash`
(F5), never in a payload. Add a learned tag only as the last resort the design already names
(reversal trigger 4).

Normalization and exposure belong on the variable, not on a separate observation declaration.
A second declaration is a second place for one fact and a second file for the form to write.
What the form needs instead is a read-only "what the agent sees" panel projected from the
`observed` bits and the compiled census. Make `bounds` part of the numeric types rather than a
conditional field: it serves clamp, normalization, the descriptor and the identity check, and
it removes the "normalization iff exposed" rule, which refuses in both directions today.

## 5. Expression language and its spellings

The one spelling: a bare name is the subject's own state. In an agent expression, an action
write, an affordance or agent effect and a reward reference, `energy` and `reputation` resolve
to this agent's meter row and this world's variable. In a dyadic context (an item hook, a pair
rule, a targeted effect) `target.x` names the second entity. `item.x` names the item's own
state inside an item hook. No `vfs.`, `bar.`, `env.`, `self.`, `global.vfs.`, `agent.vfs.`
prefixes; they encode storage, and the round-2 table shows two of them compile and crash.

The one resolver: `ExpressionSchema.for_context(kind)` built from the compiler symbol table,
returning name to (type, shape) for `agent_row`, `world`, `item`, `pair` and `spawn`, used by
every type checker and every runtime context. Today `_write_expression_schema`,
`VFSProfileCompiler.compile_profile`, `_build_spawn_condition_schema` and the effects context
each build their own (S5); the spawn schema advertises `env.X`, bare meters and `temporal.*`
that the runtime context does not serve (F6).

Temporal history: yes, but one primitive. Admit `prev(x)` (the value at the end of the previous
tick) and `lag(x, n)` with a literal `n` so the buffer is compile-time sized, collected from both
profiles. Delete `delta`, `ema`, `moving_average`, `rate_of_change`, `rising_edge`,
`falling_edge` as functions: each is one line over `prev` (`ema` is
`a*x + (1-a)*prev(ema)`, a self-edge the lag rule admits). This replaces the dead pipeline (F9)
with the smallest thing that makes S9 one declaration.

Events: yes. `did(ACTION)`, `started(AFF)`, `completed(AFF)` as agent-row booleans, and
`world`-scope reductions `count_completed(AFF)`. The engine already has `successful_interactions`
in `step()`; it is a dict of Python ints today and would become a `[W*A, F]` bool tensor. With
events in the language, the accumulator case needs no transition rule and no affordance write.

## 6. Authoring ergonomics for a web front end

### (a) A hunger meter that depletes and is restored by eating

Today a hunger meter is not a VFS variable. It is declared in `environment.yaml` (name,
`range_type`), `levels/<L>/bars.yaml` (initial, three depletion rates, recovery, four bounds
fields) and `levels/<L>/affordances.yaml` (EAT: `interaction_type`, costs, opening hours,
deployment, five interaction stages, `modify: target.bar.satiation`), with cascades split
between `environment.yaml` (graph) and `bars.yaml` (parameters). Three files, about 35 lines,
two of them per level. If the new user instead reaches for `variables.yaml`:

```yaml
- id: hunger            # 12 fields; semantic_type, readable_by, writable_by carry no information
  scope: agent
  type: scalar
  lifetime: episode
  semantic_type: custom
  readable_by: [engine, agent]
  writable_by: [engine]
  exposed_to: [agent]
  initial_value: 1.0
  normalization: {kind: minmax, min: 0.0, max: 1.0, clip: true}
```

plus a `transition_rules.yaml` rule (`id`, `kind`, `phase`, `reads`, `condition`, one write with
`variable_id`, `expression`, `composition`, `condition`, `clamp`, `effect`) for the passive
drain, plus `modify: target.vfs.hunger` on EAT. Three declarations in three files, and strictly
worse than the meter: no lethality, no cascade, no `depletion.move`. Refusals they can hit: id
equal to a meter name; `normalization` missing or present on the wrong side of `exposed_to`;
`minmax` without `clip`; `readable_by` without `engine`; an unknown phase; `vfs.hunger` in the
rule expression refused while `hunger` works; indistinguishable from any other [0, 1] agent
scalar starting at 1.0. Target surface:

```yaml
# variables.yaml (pack scope): the state, its bounds, and what a breach means
- id: hunger
  scope: agent
  type: scalar
  lifetime: episode
  bounds: {min: 0.0, max: 1.0, on_min: end_agent_fail, on_max: cap}
  initial: 1.0
  observed: true
  mutable: true
# levels/<L>/bars.yaml (level scope): a pointer plus the survival-role rates
- variable: hunger
  depletion: {passive: 0.008, move: 0.01, interact: 0.0}
  recovery: 0.0
```

with EAT's `modify: hunger` unchanged in the affordance. One declaration of state and one
binding; the binding carries nothing the variable already owns (no `name`, `initial`,
`bounds`, `lethal_*`, `range_type`), so there is nothing to keep in sync. Per-level tuning of
rates, the one real reason `bars.yaml` is level-scoped, survives. Cascades are rules over the
same variables. The breach policy is checked once, at the slot `clamp_and_validate` occupies
today, after every write of the tick: `cap` and `reset_to` rewrite storage; `end_agent_*` feed
the terminal step with the outcome class (`fail`, `success`, or `error`, which episode-lane
accounting excludes from learning statistics); `end_experiment` raises to the runner. `cap` and
`reset_to` are refused on an expression-owned target, whose stored value must equal its
expression; its bounds serve normalization and the `end_*` policies only.

### (b) Ticks since the agent last slept, exposed to the policy

Today: a variable (12 fields, `lifetime: episode`), a `+1` transition rule (7 rule fields, 6
write fields) and `modify: target.vfs.t_since_sleep` with value `0` on SLEEP. `L5_multi_agent`
declares this variable with `lifetime: tick` and nothing writes it (F14). Refusals: writing it as
`expression: t_since_sleep + 1` is a cycle; `lag(...)` is refused (F9); `tick` lifetime resets it
every step so the rule's `+1` is all it ever shows. And one defect no file reveals: affordance
effects run inside `_execute_actions` (`action_executor.py:202`) and the rule runs at
`apply_social_residue_effects`, so the tick the agent sleeps writes 0 then 1; the observed
counter is never 0. Target surface:

```yaml
- id: t_since_sleep
  scope: agent
  type: scalar
  lifetime: episode
  range: [0, 100]
  initial: 0
  observed: true
  expression: where(completed(SLEEP), 0, prev(t_since_sleep) + 1)
```

One declaration, one file, no ordering question.

### (c) Town-wide reputation raised when any agent works, visible to all

Today: a `global` scalar (12 fields) plus `modify: vfs.reputation` with
`value: vfs.reputation + 0.1` on WORK's `on_start`. It compiles, and every one of the eight
lanes observes and is rewarded for every other lane's work (F4). The spelling is `vfs.` in an
affordance effect, `global.vfs.` in an effect definition, and bare in a reward
(`variable_bonuses: [{variable: reputation, weight: 1.0}]`). Two declarations plus the reward
reference, across three files. An attempt to write it as a global expression over agent state
is refused as scope widening. Target surface:

```yaml
- id: reputation
  scope: world
  type: scalar
  lifetime: episode
  range: [0.0, 10.0]
  initial: 0.0
  observed: true
  expression: min(10.0, prev(reputation) + 0.1 * count_completed(WORK))
```

Per world by construction; the reward references `reputation`.

### (d) Practitioner: a two-agent trust relation updated by interactions, read by the reward

Today: `pair` scalar declared (L5 does); a rule can write it, but nothing names the other agent
of the pair, so an agent-shaped value lands down the column, diagonal included (F7); no reward
reduction accepts pair state ("has no ordinary reward reduction"); no publisher; and under
independent worlds the N by N matrix spans lanes. Target surface:

```yaml
experiment: {agents_per_world: 2}
- id: trust
  scope: pair
  type: scalar
  lifetime: episode
  range: [0.0, 1.0]
  initial: 0.5
  observed: false
  expression: clamp(prev(trust) + 0.1 * completed_with(HELP, target) - 0.05 * completed_with(STEAL, target), 0, 1)
```

with the reward declaring its reduction explicitly: `{variable: trust, reduce: mean_over_target}`.
`target` is bound inside a pair expression to the column agent. This needs change 1 (A > 1), the
resolver and events of change 2 and 4, and a reduction vocabulary on the DAC side. It is the
first mechanic that justifies keeping `pair` at all; until a pack needs it, the scope should be
refused, not stored.

### (e) Practitioner: a partially observed item with internal state

Today: an item type in `items.yaml` with `vfs_profile: medical`; `item_profiles: [medical]` and
a `profile: medical` variable in `variables.yaml` (12 fields, `lifetime: episode` forced);
hooks spell its state `self.vfs.durability` while agent effects spell `target.vfs.x`; a spawn
rule's `when` admits `env.X`, bare meters and `temporal.is_night` that crash at reset (F6); and
under `active_vision: partial` the state row stays present when the item token is hidden (F3).
Target surface: the item type is the profile, and state is declared on it.

```yaml
item_types:
- id: medkit
  state:
    durability: {type: scalar, range: [0, 100], initial: 100, observed: true}
  on_use:
  - modify: target.health
    value: target.health + 0.5
  - modify: item.durability
    value: item.durability - 10
```

The compiler lifts `medkit.durability` into the symbol inventory, so "all variables enter the
symbol table" still holds; the three-name binding disappears; visibility comes from one per-slot
mask shared with the item token (WP11).

## 7. What to delete, what to add, what to rename

Deletions first, each with what it costs a practitioner and what it buys a new user.

| # | action | why | cost to practitioner | gain for new user |
|---|---|---|---|---|
| D1 | delete `agent_private` | dominated by `observed: false` (S2); silent role override at `registry.py:645` | none | one fewer scope, one way to hide state |
| D2 | delete `message`, `num_message_slots`, `message_token`, `append_event` | storage with no reader, no addressee, hardwired sentinel (F8, S6) | none today; communication returns as a designed feature | two fewer concepts, no extent block |
| D3 | refuse `pair` while agents-per-world is 1 | no partner binding, no reader, spans worlds (F7, S7) | deferred, not lost; returns with change 1 | no scope that cannot work |
| D4 | delete `readable_by` | two fixed values; the one it adds beyond exposure has no consumer | one PRD-0004 acceptance row (`readable_unexposed` in the `static_epistemic_access` witness) and a DIV-015 re-baseline | one fewer field, no "engine read required" refusal |
| D5 | delete `semantic_type` | one descriptor bit plus a clock detector that two other facts already identify | descriptor loses one bit; declared dynamics (A5) separate more than it did | one fewer field with a meaningless `custom` answer |
| D6 | delete `kind`, `reads`, `effect`, authored `phase` from rules; delete `reads` from actions | inert or unchecked (S8); `vtc.py:1649-1672` still crashes at step on three compositions the DTO admits | the telemetry label is derived from `id` | rule is `id`, `when`, `writes` |
| D7 | delete `clamp`, `priority_write`, `last_write_wins`, `append_event` compositions; `priority`, `telemetry_label`, `phase` from writes | clamp is the `cap` breach policy on `bounds`; priority is declaration order; two modes have never had a use; `vtc.py:664` raises on unimplemented modes | none observed in any pack | a write is four fields |
| D8 | delete the authored phase vocabulary | 14 names, of which an author legitimately needs zero; the family picks the phase | ordering control, which today is also invisible (walkthrough b) | no phase refusals |
| D9 | delete `delta`, `ema`, `moving_average`, `rate_of_change`, `rising_edge`, `falling_edge` | sugar over `prev`; all dead today (F9) | one line each to re-express | smaller function table |
| D10 | delete `temporal.is_night`, `temporal.day_progress`, `temporal.time_of_day` from the spawn schema | engine constants of a game fact (F14), unreachable at runtime | none | no namespace that compiles and crashes |
| D11 | delete the 17-member type vocabulary in favour of 5 | `vec2i` versus `vecNi dims: 2` is one type; refs are ints with a sentinel | none | one type question |
| A1 | add `agents_per_world` to `experiment`; world axis on `world`, `affordance`, items | change 1 | enables multi-agent packs honestly | nothing to learn until needed |
| A2 | add `bounds: {min, max, on_min, on_max}` to numeric types where bounds make sense; an unbounded numeric declares `bounds: null` explicitly (no-defaults form) and is refused at exposure, which already certifies boundedness; `bool` and refs carry no `bounds` field; policies `end_experiment`, `end_agent_error`, `end_agent_fail`, `end_agent_success`, `cap`, `reset_to: <value>` | one fact, four homes today (meter `bounds` and `lethal_*`, per-write `clamp`, `VTCBoundsClampProgram`, exposure `normalization`); the breach policy replaces `VTCTerminalConditionProgram`'s meter sources and gives a declared `error` outcome class | none; already required at exposure, and terminal conditions become authorable on any variable | no conditional field; "what happens when it breaks" is one question on the form |
| A3 | add `prev(x)`, `lag(x, n)` with lag-only self-edges | S9, F9 | accumulators in one line | counters without rules |
| A4 | add events `did`, `started`, `completed`, `completed_with`, `count_completed` | walkthroughs b, c, d | one declaration per mechanic | the form's "how it changes" question has an answer |
| D12 | delete the `meters` section of `environment.yaml`, meter `name`/`initial`/`bounds`/`range_type`, `CascadeParamConfig`, the `meter` token type and DAC's `bar:` reference | owner ruling: a meter is a pointer to a variable; everything a meter declares that the variable also declares is a second copy | the oracle's bar streams are re-baselined once; `default_curriculum` is rewritten (eight variables, eight bindings, five cascade rules) | one kind of thing to declare, one place to look for a value |
| A5 | make `bars.yaml` a binding (change 3): `{variable, depletion, recovery, lethal_min, lethal_max}` per entry, level-scoped, pointing at any declared variable (stateful, expression-derived, or constant); role parameters refused at compile when the target cannot carry them (depletion on an expression-owned or `mutable: false` target); the binding's dynamics signature enters that variable's `variable_element` descriptor | the survival role as a declared binding, the DAC `money_bar` pattern | meters stop being special; per-level rate tuning survives; the descriptor carries behaviour, so S3 resolves | hunger is one variable and one short binding |
| A6 | add expression text and `semantic` facts to `vfs_hash` (WP10) | F5 | honest resume | none visible |
| R1 | rename `global` to `world` | the ruling makes it per world; `global` reads as batch-wide | one find-and-replace | matches the mental model |
| R2 | rename `exposed_to: [agent]` to `observed: true` | one role, one bit | none | boolean |
| R3 | rename `writable_by` to a required `mutable: true \| false` | the assertion is useful; the role list is not | none | one required bit instead of a role list |
| R4 | rename `social_residue` family to `rules`; `transition_rules.yaml` convention stays | it is the general per-tick dynamic | none | the name says what it does |
| R5 | rename `initial_value` / `_mode` / `_params` to `initial` | one field | none | one field |
| R6 | rename `vfs_profile` / `profile` / `item_profiles` to state declared on the item type | walkthrough e | none | no indirection |

## 8. Where the current spec is fine

State these so the next sprint does not relitigate them.

- One roster, files as transport, discovery by content, duplicates refused with both origins.
  The declaration-store cut was the right move and it works.
- The closed expression DSL with a registry-generated function table, a compile-time type
  checker and a shape proof. Keep it; extend the proof to writes (WP12) rather than inventing a
  second checker.
- `extra="forbid"` and no defaults everywhere. Fewer required fields is the goal; an optional
  behavioural field is not.
- The three lifetimes with the registry's scope-blind reset. Correct where they run.
- The frozen access-policy snapshot and checked accessors. Even after `readable_by` goes, the
  mechanism that refuses an authored write to a `mutable: false` variable at compile with
  `file:line` is the right shape for every refusal in the system.
- The token model: fixed payload widths, per-universe capacities, presence-led rows, identity by
  declared payload, POMDP as a visibility filter that does not reshape the tensor. The transfer
  hash being identical across substrates is the result that justifies all of it. Change 3
  removes the `meter` type from the roster; that is one hash move, not a model change.
- The phase graph as the executed schedule, hashed. Keep it as the engine's internal truth; stop
  exposing its names to authors.
- `period_of` for the clock, and `tick` as the one ambient temporal primitive.
- Refusals with codes, stages and `file:line`. The token-spec refusals should join this shape
  (F12), not the other way round.
- Hash-gated resume. Add what is missing (F5, F13); do not weaken the gate.

## 9. Provenance: meters were VFS variables in the original design

The owner asked whether meters were taken out of VFS because leaving them in was harder. The
record, from `git log` and the archived plans:

| date | commit | what it did |
|---|---|---|
| 2025-11-07 | `e8d43e22`, `a226d186`, `90ad6fb5` (TASK-002C, Cycles 1-6) | VFS lands. Every level ships a `variables_reference.yaml` declaring `energy`, `health`, `satiation`, `money`, `mood`, `social`, `fitness`, `hygiene` as `scope: agent`, `type: scalar`, `lifetime: episode` variables beside `position`, `grid_encoding`, `time_sin`, `time_cos`. The file header calls them "temporary reference variables (Cycle 0.2), scaffolding for dimension validation" |
| 2025-11-07 | `74792b4e` "Integrate VFS into VectorizedHamletEnv, remove legacy ObservationBuilder" | The env requires `variables_reference.yaml` and writes every meter into the registry each step (`self.vfs_registry.set(meter_name, self.meters[:, idx], writer="engine")`). Meters are VFS variables at runtime, with `self.meters` still the authority |
| 2025-11-07 | `3696562a` "Cycle 7 COMPLETE" | The plan's Cycle 7 was to replace the reference files with a permanent `configs/templates/variables.yaml` whose example declares `energy` with `writable_by: ["actions", "engine"]`, that is, a meter as an action-written variable. The commit instead "clarified reference variables as test infrastructure (not temporary scaffolding)" and kept them |
| 2025-11-15 | `4f52de35` | The flat packs, reference files included, move to `configs_archive/` for the v2.1 migration |
| 2025-11-16 | `a4eff57d` "finalize v2.1 compiler/runtime wiring" (one-line message, no rationale) | Deletes the `variables_reference` load and the per-meter registry sync from the env. Meters become `obs_<meter>` fields the compiler emits from the `environment.yaml` meter vocabulary; VFS variables become a separate `environment.variables` list (`deficit_energy`, `time_since_last_eat`) under v2.1 Decision 9, "vocabulary in `environment.yaml`, computation in VFS" |
| 2025-11-23 | `VARIABLE_SUBSYSTEM.md` (vfs_uplift) | Still states the design: "standard system variables are auto-generated from substrate, bars, and affordances: meters: energy, health, ...", with examples reading `bar["energy"]` |
| 2026-05-15 | `VFS.md` §15.1 | "Bars are variables, not the whole ontology", with `energy` as the §4.1 example variable |
| 2026-08-22 | token design §1 | Meters get their own `meter` token type with a hand-built signature; `variable_element` gets the descriptor block. The split is now in the observation ABI |
| 2026-08-24 | `UNIVERSE_AS_CODE` trio rewrite | Maps "meters/bars, depletion, physics are data" to "VFS variables + VTC programs", still describing meters as variables |
| 2026-10-24 | VFS WP4 (`e90a85a4`) | A variable id equal to a meter name is refused at the symbol table: the two namespaces are now enforced as disjoint |

So: meters entered VFS on day one, by design and at runtime; the plan's own permanent template
declared a meter as an action-written variable; the v2.1 compiler migration removed the runtime
path nine days later with no recorded reason while every design document kept saying meters are
variables; and the last ten months built around the removal. The owner's reading is the one the
record supports, with one sharpening the owner supplied in session: a bar was never meant to
be its own thing, only a pointer to a variable. Change 3 is restoration of the original design
in that form: the variable is the state, the meter binding is a level-scoped role over it.

## 10. The convenience layer, evaluated, and its systems-thinking extension

A meter, stripped of the game, is a bounded stock with three flows (per-tick drain,
action-conditioned drain, recovery), a constraint with a consequence, exposure, and a reward
role. Every item on that list is a VFS primitive under changes 3 to 5, so the meter binding is a
macro over primitives the compiler already proves and hashes. That is the strongest position a
convenience layer can hold: it cannot drift from the core, and any pack can hand-expand it,
which is the test that it is a layer and not a type. Three weaknesses to design around: the
binding's own vocabulary must not smuggle game facts back in (`depletion.move` assumes a
substrate with movement; speak in `did(<action class>)`); the binding's rates should be
expressions, not constants only, so a designer who needs "cold makes hunger fall faster" has a
slope and not a cliff down to raw rules; and the compiler owes the designer a per-stock ledger
(every flow in and out, with `file:line`), because locality spreads one stock's behaviour over
four files by design.

The extension is to make the stock-and-flow reading explicit. Stock = variable; flow = one
`{into | out_of, rate: <expr>, when: <event or condition>}` form that writes, rules, meter
depletion and cascades all lower to; converter = expression variable; constraint = `bounds` with
breach policy; event = `did`/`completed`/breach; delay = one `delay(x, n)` that `prev`, `lag`
and effect durations lower to; boundary = scope. Two primitives VFS lacks and economies and
societies need: a paired `transfer: {from, to, amount}` between stocks, conservation by
construction; and world-scope `invariants:` with the same breach policies as `bounds`. From the
declarations the compiler can emit the stock-flow graph and refuse a reinforcing loop on an
unbounded stock. These patterns are the F in VFS (owner, 2026-10-24): variables are the raw infrastructure,
features are the helpers over them for authors who do not want to write their own expressions
and rules. `meter`, `resource`, `timer`, `cycle`, `pool`, `relation`, `capacity` are features,
each a macro over the same primitives, each the web form's vocabulary, each expandable by hand.
VFS.md §4.2 still lists `FeatureDef` as a future extension and the token cut reused the word
for a payload column (`ObservationFeature`, `DESCRIPTOR_BLOCK_FEATURES`); rename those to
`payload field` so the layer gets its name back. Meadows' leverage points then read the pack:
rates (curriculum tuning) are the weakest intervention, `bounds` are buffer sizes, rules are
flow structure, effects are delays, exposure is the information flow (what L2 changes), reward
is the system's goal.
