# Brain as Code (BAC)

Document date: 2026-08-24
Status: **Current** (reviewed 2026-08-31) — part of the six-document HLD set (PDR-0118).

> **Status discipline, stated up front because this document's predecessors failed it.**
> The archived `BRAIN_AS_CODE.md` and `hld/02-brain-as-code.md` both carry
> *"Status: Approved for Implementation"*. That line is **false**. The identifiers those
> documents specify — `execution_graph`, `cognitive_topology`, `agent_architecture` — return
> **zero grep hits across `src/` and `configs/`** (re-verified 2026-08-24). This document keeps
> "what exists" and "what is designed" in separate sections and never merges them.

---

## 1. What BAC is

BAC is the third compiled subsystem. Where **Strata** declares *where things can be*
(`STRATA.md`) and **UAC** declares *what exists and how it changes*, BAC declares **how agents
think** — and declares it, rather than coding it.

The premise is the same one that drives the rest of the framework: an agent's mind should be
inspectable, diffable, and swappable as configuration, so that a designer can change what kind
of entity is in the simulation without editing Python, and so that a run's cognition is
reproducible and reviewable after the fact. The design test applies unchanged: *can a designer
express this in a config pack?*

BAC does not compile to an artifact of its own. The brain rides **inside** the
`CompiledUniverse` as a validated `BrainConfig` plus a `brain_hash`. (`CompiledBrain` exists
only in archived documents — README states this plainly, and README is authoritative here.)

---

## 2. What exists today

Verified in `src/townlet/` on 2026-08-31. This is the **realized slice**: network, optimizer,
loss, replay and Q-learning hyperparameters. README calls it "brain-as-code, layer 2" — see §3
for the layer framing.

### 2.1 The authoring surface

`brain.yaml`, at the pack root, shared across a pack's levels (a level may override it —
see §2.4). The DTO is `BrainConfig` in `src/townlet/config/brain_config.py`, with
`ConfigDict(extra="forbid")` throughout: stray keys fail at parse time, and behavioral
parameters carry no hidden defaults.

Declared sub-configs, in source order:

| block | DTO | declares |
| --- | --- | --- |
| `architecture` | `ArchitectureConfig` (+ `FeedforwardConfig`, `RecurrentConfig`/`LSTMConfig`, `DuelingConfig`/`DuelingStreamConfig`, `TokenSetConfig`/`SetAggregatorConfig`) | network family and its shape |
| `optimizer` | `OptimizerConfig`, `ScheduleConfig` | optimizer type, learning rate, betas/eps, weight decay, LR schedule |
| `loss` | `LossConfig` | loss function |
| `q_learning` | `QLearningConfig` | gamma, target-update frequency, `use_double_dqn` |
| `replay` | `ReplayConfig` | capacity, prioritized (PER) vs uniform |

Field-level reference: `docs/config-schemas/brain.md`. Do not restate it here.

### 2.2 Architecture selection

`ArchitectureConfig.type` is a **closed literal of four values**:
`feedforward` | `recurrent` | `dueling` | `token_set`. A model validator enforces that the
matching sub-config is present, so `type: recurrent` with no `recurrent:` block is a parse
error rather than a runtime surprise.

Selection is **not** in the DTO. It happens at
`src/townlet/population/vectorized.py:876` — `VectorizedPopulation._build_network` — which
dispatches on `arch.type` into `NetworkFactory` (`src/townlet/agent/network_factory.py`). The
same helper builds both the online and the target network.

| `type` | built by | produces |
| --- | --- | --- |
| `feedforward` | `NetworkFactory.build_feedforward` | an `nn.Sequential` MLP assembled from `hidden_layers` / `activation` / `dropout` / `layer_norm` |
| `recurrent` | `NetworkFactory.build_recurrent` | `RecurrentTokenQNetwork` (shared token-set encoder + LSTM + Q-head) |
| `dueling` | `NetworkFactory.build_dueling` | `DuelingQNetwork` |
| `token_set` | `NetworkFactory.build_token_set` | `TokenSetQNetwork` |

For `token_set` and `recurrent`, the factory passes the compiled `TokenSpec` directly. Both use
`TokenSetEncoder`, whose per-type projections and declared set aggregator produce one pooled
embedding per frame. `TokenSetQNetwork` sends that embedding directly to a Q-head;
`RecurrentTokenQNetwork` encodes `[batch * sequence]` frames, makes one LSTM call over the pooled
sequence, and applies its Q-head to each recurrent output. Flat and dueling networks are sized
from the compiled flat observation width.

### 2.3 The network classes, and which are reachable

The network module exposes these relevant classes:

| class | selectable from `brain.yaml`? |
| --- | --- |
| `SimpleQNetwork` | **No.** `type: feedforward` builds an equivalent `nn.Sequential` inline. |
| `DuelingQNetwork` | Yes — `type: dueling`. |
| `TokenSetEncoder` | **No.** Shared implementation used by both token-native Q-networks. |
| `TokenSetQNetwork` | Yes — `type: token_set`. |
| `RecurrentTokenQNetwork` | Yes — `type: recurrent`. |
| `StructuredQNetwork` | **No.** It has no `ArchitectureConfig.type` authoring door. |

`StructuredQNetwork` is production-dead: it has no authoring door, and the legacy grouped
observation artifact its constructor expects no longer exists. It is not a current architecture.

> **Never write an observation-dimension literal.** Layer shapes are read from
> `src/townlet/agent/networks.py`; observation width comes only from the compiled artifact
> (`token_spec.total_dims`; see `HLD.md` §5.3). The docstring example in
> `network_factory.py:build_feedforward` contains stale dimension literals — treat it as an
> illustration of the call shape, not as a fact about any pack.

### 2.4 Provenance

`brain_hash` is the SHA256 of the **primary level's effective brain config** — after
`apply_training_overrides` — not of `brain.yaml`. It is level-scoped, exactly like `drive_hash`.
`pack_brain_hash` is the pack-root brain's hash; **`pack_brain_hash != brain_hash` means this
level declared its own `brain.yaml`**, and `CompiledUniverse` exposes that as an explicit
lineage-fork predicate (`compiled.py:218`, PDR-0027).

`brain_hash` is one of the eight hashes `assert_checkpoint_identity` hard-compares, so a
checkpoint refuses to load into a universe whose effective brain differs. See `HLD.md` §5.2 and
`docs/config-schemas/brain.md` §"Checkpoint Provenance:
brain_hash".

### 2.5 Runtime notes

T15 local source correction, 2026-11-02: these learner notes were checked against five complete
implementation files: `population/vectorized.py`, `config/training_v2_config.py`,
`config/bac_options.py`, `training/q_targets.py` and `scripts/check_episode_lanes.py`.
[BAC status](../remediation/bac/STATUS.md) records qualification and outstanding gates. This
bounded correction does not refresh the document-wide historical review stamp or unrelated
schema/compiler/network/provenance claims.

- Rollout hidden state persists until episode completion/reset. Replay training starts each
  sampled unit at zero hidden state and carries a graph-connected online current-prefix through
  its real observations. Target prefixes are separate and advance under no-grad. Each successor
  branch uses that row's exact stored successor and its own network's after-current-prefix
  state; all bootstrap evaluations run under no-grad, online branch hidden tensors are detached,
  and returned branch states never advance the current prefixes. Padding is excluded. Double
  DQN adds an online successor forward per real timestep in each length group
  (`VectorizedPopulation._recurrent_predictions`, `population/vectorized.py:675`).
- Vanilla and Double DQN targets use recorded successor legality, rather than the current
  environment's masks. Vanilla takes the legal target maximum; Double selects with legal online
  Q and evaluates with target Q. Non-bootstrap successor values are exactly zero. With gamma
  zero the target helper returns finite canonical rewards without reading Q entries for
  successor selection; metadata validation and population network forwards still run. On
  bootstrapped rows every legal selector entry and the selected target entry must be finite;
  illegal or unused terminal nonfinite outputs do not enter target arithmetic
  (`training/q_targets.py:19`, `population/vectorized.py:675,715`).
- Scheduled learning requires retained eligible-transition warmup AND backend sampleability.
  Authored `min_size` is positive and no greater than capacity; the explicit construction seam
  accepts a nonnegative threshold. Batch size may exceed warmup. Recurrent warmup counts
  retained transitions while sampling counts actual windows/contexts. Successive PER needs B
  distinct units; replacement laws and accepted uniform sequence adapters can draw B from fewer
  positive-support units. Fixed-full windows must exist; pending episode collectors do not count
  as retained replay. The population logs changed unready diagnostics. Backend cardinality and
  archive semantics retain their separately verified replay-owner contracts
  (`config/training_v2_config.py:102`, `population/vectorized.py:654,715`).
- Recurrent loss averages selected real rows within each unit, applies its detached returned
  weight once, then averages units. Anchor prefixes remain context. Priority feedback uses
  stable unit IDs and the loss mask. TD telemetry instead reports the unweighted mean absolute
  residual over all sampled real rows: both detached operands are promoted to float64 before
  subtraction; padding is excluded. Beta advances per actual vector tick before sampling,
  including warmup/unscheduled ticks. Scheduler and target-copy cadence advance with successful
  optimizer updates (`population/vectorized.py:643,729`). Gradient clipping uses the declared
  `training_loop.max_grad_norm` (`config/training_v2_config.py:212`) via
  `torch.nn.utils.clip_grad_norm_(..., max_norm=self.max_grad_norm)`
  (`population/vectorized.py:762`).
- Full-N Q/mask/state transport remains the population invariant. Production rollout supplies
  full-population Q; selection checks bool eligibility/mask geometry and device relative to that
  Q tensor and refuses eligible rows without legal actions. For K>0 it calls the configured
  provider once with aligned eligible Q/mask/state rows and epsilons, checks the returned
  int64[K] shape/device, then scatters into full-N transport. K=0 skips the provider. Inactive
  entries retain unmasked argmax and inactive recurrent hidden state is preserved
  (`population/vectorized.py:998,1015`).
  The standalone lane checker observes full-N Q/actions and successful actual flat
  `push_recorded` admission; its recipes use a scripted selector and do not independently
  qualify genuine-provider selection (`scripts/check_episode_lanes.py:605,641,725`).
- `VectorizedPopulation.for_training` requires resolved replay policy, an explicit owned RNG,
  minimum, horizon/derivation and tick. The unchanged constructor defers learner-only setup
  until actual training and preserves inspection/serving roles. Binding distinguishes pristine
  constructor state from loaded/owned replay; empty occupancy alone cannot authorize reseeding
  or discarding history. Raw POP6 restore deep-copies optimizer state before installation and
  preserves compatible current captured replay/clocks. Approved historical Option A retains
  old maskless artifacts/history for archive/query/export and starts qualified replay fresh;
  archive rows cannot satisfy warmup. This scoped restore does not qualify full native10/7
  continuation/resource/RNG atomicity (T24/T25), natural runner `for_training` propagation
  (T16), private-curiosity isolation/X02 or ICM ENV reward/update integration (T18e/T18f)
  (`population/vectorized.py:204,595,2011,2033`).

---

## 3. The design target — not built

Everything in this section is **target state with zero code footprint**. It is preserved because
it remains the direction, not because it shipped. Sources:
`archive/BRAIN_AS_CODE-2026-live.md`, `archive/hld/02-brain-as-code.md`. Their status lines are
false; their design content is worth keeping.

The design is **three layers**, lining up with three audiences — people who care what the agent
is *allowed* to do, people who care how it is *built*, and people who care how it *thinks, step
by step*:

### Layer 1 — cognitive topology ("the character sheet") — **not built**

The public-facing definition of the agent as a character: the layer a policy reviewer or an
instructor signs off on. Declares the behaviour contract in human terms — which cognitive
faculties are enabled (perception, world model with a rollout depth, social model, hierarchical
policy with a meta-controller period), personality dials (greed, agreeableness, curiosity,
neuroticism), **panic thresholds** (below which emergency behaviour overrides the normal
planner), **compliance** (a hard `forbid_actions` veto list plus penalized actions), and
introspection settings (whether the agent publishes *why* it chose a goal, for glass-box UI).

The point of the layer: panic stops being a magic mystery in code and becomes a parameter in a
file you can read; a safety policy literally binds behaviour; and "what kind of entity did you
just put in my sim?" has a plain-language answer.

**Status: not built.** `cognitive_topology` returns zero hits in `src/` and `configs/`.

### Layer 2 — agent architecture ("the engineering blueprint") — **partially real**

Module implementations, network types, interface contracts, pretraining. This is the layer the
realized slice in §2 belongs to: `brain.yaml` is a narrow, flat form of it — one network, one
optimizer, one loss — with no module registry, no per-module interface contracts, and no
composition of named cognitive modules.

**Status: the network/optimizer/loss surface is real; the module-registry design is not.**
`agent_architecture` returns zero hits.

### Layer 3 — execution graph ("the think loop") — **not built**

The think-loop DAG: which modules run in which order each tick, wired by symbolic bindings, with
governance ordering made explicit (panic evaluated before ethics, ethics before action
emission). An `EthicsFilter` sits in the module registry like any other module, with the job of
enforcing Layer 1's contract.

The archived design also specifies a **cognitive hash** over all three layers, a run-bundle
layout carrying the three YAML files beside `universe_as_code.yaml`, and factory/executor
modules (`agent/factory.py`, `agent/graph_agent.py`, `agent/graph_executor.py`).

**Status: not built.** `execution_graph` returns zero hits; none of those modules exist.

### What "not built" costs, concretely

Today a designer can change the *shape* of the network but not the *shape of the thinking*.
Anything resembling a behaviour contract, a panic override, an action veto, or a multi-module
think loop is Python-editing work — which, by this project's own design test, is the defect
worth naming rather than a shortcut.

---

## 4. The bridge: token observations

The current observation is a compact fixed-capacity serialization of typed tokens.
`TokenSetQNetwork` consumes the compiled `TokenSpec`, expands one type at a time with static
context at the network boundary, projects each type, and pools the mixed set with the declared
`mean` or `attention` aggregator. `StructuredQNetwork` still has no authoring door (§2.3).

The **token-observation migration** that established this representation is specified in:
`docs/superpowers/specs/2026-08-22-token-observation-representation-design.md` — approved
(PDR-0114, with a no-tech-debt rider), units 1 and 2 banked (PDR-0115, PDR-0116). It defines a
token type system, a compiled `TokenSpec` artifact, runtime encoding with an explicit visibility
filter, network consumption, and the transfer/provenance/oracle consequences. Read the spec;
this document does not restate it.

Two consequences matter for BAC:

1. **Explicit, required exposure.** The migration makes observation exposure per-variable and
   explicit — which is the natural vehicle for fixing the systemic access-control gap named in
   `HLD.md` §8, and therefore the prerequisite for a Layer 1 that can meaningfully declare what
   an agent is allowed to *perceive*.
2. **Structured input makes structured cognition worth declaring.** Once observations arrive as
   typed tokens, an attention or set-based policy stops being an equivalent reparameterization
   of a flat MLP and starts being a genuinely different mind — at which point declaring the
   architecture, rather than the layer sizes, earns its authoring surface.

PDR-0117 (files are transport, declarations are the unit) sequences *after* the token migration
and applies to `brain.yaml` like every other pack file: BAC declarations will be discovered and
merged by declared id rather than found at a mandated filename. See `UAC.md` §4.

---

## 5. References

- **Schema**: `docs/config-schemas/brain.md` (archived 2026-08-24; content may be
  stale) — the field-level reference for `brain.yaml`
- **Source**: `src/townlet/config/brain_config.py` (DTOs), `src/townlet/agent/networks.py`
  (network classes), `src/townlet/agent/network_factory.py` (construction),
  `src/townlet/population/vectorized.py:876` (selection)
- **Provenance**: `src/townlet/universe/compiled.py` (`brain_hash`, `pack_brain_hash`),
  `src/townlet/training/checkpoint_utils.py` (`assert_checkpoint_identity`)
- **Token migration**: `docs/superpowers/specs/2026-08-22-token-observation-representation-design.md`
- **Architecture context**: `HLD.md` (the trio and the provenance contract), `UAC.md`, `VFS.md`
- **Design history (status lines false, design content useful)**:
  `archive/BRAIN_AS_CODE-2026-live.md`, `archive/BRAIN_AS_CODE.md`,
  `archive/hld/02-brain-as-code.md`
- **Status**: `README.md` §"Delivered, and intended" — authoritative over this document
