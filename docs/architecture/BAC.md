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
| `architecture` | `ArchitectureConfig` (+ `FeedforwardConfig`, `RecurrentConfig`/`LSTMConfig`/`CNNEncoderConfig`/`MLPEncoderConfig`, `DuelingConfig`/`DuelingStreamConfig`, `TokenSetConfig`/`SetAggregatorConfig`) | network family and its shape |
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
`src/townlet/population/vectorized.py:405` — `VectorizedPopulation._build_network` — which
dispatches on `arch.type` into `NetworkFactory` (`src/townlet/agent/network_factory.py`). The
same helper builds both the online and the target network.

| `type` | built by | produces |
| --- | --- | --- |
| `feedforward` | `NetworkFactory.build_feedforward` | an `nn.Sequential` MLP assembled from `hidden_layers` / `activation` / `dropout` / `layer_norm` |
| `recurrent` | `NetworkFactory.build_recurrent` | `RecurrentSpatialQNetwork` (CNN vision encoder + LSTM) |
| `dueling` | `NetworkFactory.build_dueling` | `DuelingQNetwork` |
| `token_set` | `NetworkFactory.build_token_set` | `TokenSetQNetwork` |

For `token_set`, the factory passes the compiled `TokenSpec` directly. `TokenSetQNetwork`
sets its input width from `TokenSpec.total_dims` and rejects every forward input whose width
differs. Flat and dueling networks are sized from the environment's compiled observation width.

### 2.3 The network classes, and which are reachable

`src/townlet/agent/networks.py` declares **five** classes:

| class | line | selectable from `brain.yaml`? |
| --- | --- | --- |
| `SimpleQNetwork` | 19 | **No.** `type: feedforward` builds an equivalent `nn.Sequential` inline; this class is not instantiated anywhere in `src/`. Referenced only by a docstring in `exploration/rnd.py:72` ("Matches SimpleQNetwork architecture for consistency") and by tests. |
| `RecurrentSpatialQNetwork` | 58 | Yes — `type: recurrent`. |
| `DuelingQNetwork` | 307 | Yes — `type: dueling`. |
| `TokenSetQNetwork` | 440 | Yes — `type: token_set`. |
| `StructuredQNetwork` | 631 | **No.** Group-encoders-per-semantic-group network, exercised by `tests/test_townlet/unit/agent/test_structured_qnetwork.py`; no `ArchitectureConfig.type` value reaches it. |

`StructuredQNetwork` is production-dead: it has no authoring door, and the legacy grouped
observation artifact its constructor expects no longer exists. It is not a current architecture.

> **Never write an observation-dimension literal.** Layer shapes are read from
> `src/townlet/agent/networks.py`; observation width comes only from the compiled artifact
> (`observation_spec.total_dims`; see `HLD.md` §5.3). The docstring example in
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

- LSTM hidden state resets at episode start, persists during rollout, and resets per transition
  in batch training.
- Gradient clipping is applied via `torch.nn.utils.clip_grad_norm_` at
  `max_norm=self.max_grad_norm` (`population/vectorized.py:979,1057`). That threshold is a
  **declared training hyperparameter**, `max_grad_norm` in `training.yaml`
  (`config/training_v2_config.py:229`) — not a hardcoded engine constant. CLAUDE.md's "10.0"
  is a pack value, not a framework fact.
- On a recurrent architecture, `use_double_dqn: true` costs **one extra single-step forward
  pass** per update, not a third unroll. Verified 2026-08-24 against
  `population/vectorized.py:879-939`: both variants run two full sequence unrolls (online for
  Q-predictions, target for Q-targets) plus a target boundary forward; Double DQN adds one
  online boundary forward under the online net's final hidden state (`:896-904`), and action
  selection deliberately **reuses PASS 1's online unroll** — the code comments "a third unroll
  would recompute the same trajectory" (`:910-914`). `docs/config-schemas/training.md`
  (archived 2026-08-24)'s "~50% overhead (3 forward passes vs 2)" and CLAUDE.md's "3 vs 2"
  restatement do not match the current update path and overstate today's cost.

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
  `src/townlet/population/vectorized.py:405` (selection)
- **Provenance**: `src/townlet/universe/compiled.py` (`brain_hash`, `pack_brain_hash`),
  `src/townlet/training/checkpoint_utils.py` (`assert_checkpoint_identity`)
- **Token migration**: `docs/superpowers/specs/2026-08-22-token-observation-representation-design.md`
- **Architecture context**: `HLD.md` (the trio and the provenance contract), `UAC.md`, `VFS.md`
- **Design history (status lines false, design content useful)**:
  `archive/BRAIN_AS_CODE-2026-live.md`, `archive/BRAIN_AS_CODE.md`,
  `archive/hld/02-brain-as-code.md`
- **Status**: `README.md` §"Delivered, and intended" — authoritative over this document
