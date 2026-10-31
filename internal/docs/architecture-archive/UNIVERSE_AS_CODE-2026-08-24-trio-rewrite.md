# Universe as Code (UAC)

Document date: 2026-08-24
Status: **Current** — replaces the v2.5 document (2025-11-03) wholesale; the old text
described `cascade_engine`, `affordance_engine`, `reward_model`, ageing/retirement and a
money convention that no longer exist (or never shipped). Git history preserves it.

This guide is deliberately thin: it defines what UAC *is*, maps the old vocabulary onto
the current subsystems, and routes to the authoritative reference docs. It does not
duplicate schemas — where this document and a reference doc disagree, the reference doc
(and above it, the source) wins.

## 1. What UAC is now

The compiled target has three major declarative subsystems:

| subsystem | question it answers | authored in | authoritative docs |
|---|---|---|---|
| **Strata** | *Where can things be?* — space itself: substrate type, topology, boundaries, distance metric, position encoding | `stratum.yaml` | `docs/architecture/substrate-system.md`, `src/townlet/config/stratum_config.py` |
| **UAC — Universe as Code** | *What exists, and how does it change?* — variables, observations, items, effects, affordances, actions, transitions, rewards, terminal conditions | everything else in the pack (see §3) | this doc as router; `docs/architecture/vfs.md`; `docs/config-schemas/` |
| **BAC — Brain as Code** | *How do agents think?* — network architecture, memory, cognition topology | `brain.yaml` today; the fuller BAC design is target-state with no code footprint yet | `docs/architecture/BRAIN_AS_CODE.md` (design intent, **not** a record of what shipped) |

Historically (v2.5) "Universe as Code" meant *strata + world config* as one blob. Strata
is now promoted out as its own subsystem — space is a different kind of declaration from
world rules, compiled by a different sub-compiler against a different DTO — and UAC is
the name for the third pillar: **the world-rules layer**. All three compile through the
Universe Compiler (`src/townlet/universe/compiler.py`, seven stages — see
`docs/UNIVERSE-COMPILER.md`) into one frozen, hash-carrying `CompiledUniverse`.

**UAC's ABI is VFS.** The Variable & Feature System is the typed
state/observation/transition contract that everything in UAC compiles down to: bars are
variables, observations are exposed variables behind an activity mask, effects and
affordances read and write variables, transitions are VTC programs over variables,
rewards (DAC) read variables. There is no second ontology underneath. In that precise
sense the old standalone "universe spec" is subsumed: UAC is the *authoring* layer, VFS
is its *type system and runtime*, and this guide is closer to a recipe book over VFS
than to an independent specification.

## 2. The contract: why "compiled" matters

A pack compiles to a `CompiledUniverse` carrying provenance hashes — `config_hash`,
`vfs_hash` (variables + observation + actions + transition graph), `drive_hash` (DAC).
These are the "same interfaces" contract:

- **Reproducibility** — the artifact pins exactly which world a checkpoint was trained
  in; resume refuses on hash mismatch.
- **Transfer** — the allocated observation width and global action vocabulary are
  constant across a pack's levels (superset + activity mask), which is what makes
  cross-level checkpoint transfer real.
- **Deployment (target)** — a trained policy is portable to any host that publishes the
  same declared telemetry (variables, bounds, normalization) and accepts the same action
  vocabulary at the same cadence. Fidelity lives *below* the interface: an agent trained
  against declared telemetry on a coarse substrate can, in principle, run against a
  high-fidelity simulation publishing the same manifest. The export path itself is not
  yet built (`hamlet-0cdb8a6d1a`).

Never quote observation-dimension literals in docs — ask the compiled artifact
(`observation_spec.total_dims` / `observation_activity.active_mask`); see CLAUDE.md.

## 3. Pack anatomy (the real layout)

Pack-level shared files plus per-level overrides — **not** flat `configs/<level>/`:

```
configs/<pack>/
├── stratum.yaml            # Strata: substrate, topology, boundaries  (shared)
├── environment.yaml        # UAC: VFS variable definitions            (shared)
├── vfs_profiles.yaml       # UAC: global/agent/item profile variables (REQUIRED, pack root)
├── actions.yaml            # UAC: global action vocabulary            (shared)
├── effects.yaml            # UAC: effect definitions                  (shared)
├── items.yaml              # UAC: item definitions                    (shared)
├── brain.yaml              # BAC: network architecture                (shared)
├── variables_reference.yaml  # UAC: optional static overlay (see gaps, §5)
└── levels/<level>/
    ├── bars.yaml           # UAC: meters, depletion, terminal conditions
    ├── affordances.yaml    # UAC: interactable world actions
    ├── drive.yaml          # UAC: DAC reward specification (REQUIRED per level)
    ├── training.yaml       # hyperparameters (not part of the world)
    └── curriculum.yaml     # vision + temporal switches
```

## 4. Concept map: v2.5 vocabulary → current subsystem

| v2.5 chapter said | where it actually lives now | reference |
|---|---|---|
| meters/bars, depletion, "physics are data" | VFS variables + VTC programs (`VTCPassiveDepletionProgram`, `VTCBoundsClampProgram`) | `docs/config-schemas/bars.md`, `vfs.md` §11–13 |
| `cascades.yaml`, cross-meter dynamics, modulations | VTC (`VTCThresholdCascadeProgram`, `VTCModulationProgram`) | `vfs.md` §14 |
| terminal conditions, end-of-life | `VTCTerminalConditionProgram`; scoring → DAC | `vfs.md`, `docs/config-schemas/drive_as_code.md` |
| affordances, costs, effects, multi-tick | `affordances.yaml` + VTC action writes, occupancy, interaction progress | `docs/config-schemas/affordances.md`, `effects.md` |
| `reward_model`, episodic scoring | **deleted** → DAC (`drive.yaml`, compiled to GPU graphs, `drive_hash`) | `docs/config-schemas/drive_as_code.md` |
| observability levels | VFS observation spec: exposure + normalization + activity mask | `vfs.md` §8, `docs/config-schemas/vfs-profiles.md` |
| time of day, action masks | `curriculum.yaml` temporal switches + VTC affordance gates | `docs/config-schemas/enabled_actions.md` |
| grid, positions | **Strata** (promoted out of UAC) | `docs/architecture/substrate-system.md` |
| money ≈ $100 at 1.0, clamped | **dead** — the [0,1] clamps were removed in WS-1(e); money is a bounded variable like any other | `docs/config-schemas/bars.md` |
| ageing, retirement, Bed/Job/Hospital/Bar set | never shipped; the shipped demonstration pack is `configs/default_curriculum` (14 affordances) | CLAUDE.md "State Representation" |
| expression snippets in YAML | the closed, typed expression language | `docs/config-schemas/expressions.md` |

Two v2.5 principles survive unchanged and remain the point: **physics are data; values
are data.** The no-defaults principle (`extra="forbid"`, no hidden behavioral defaults)
and the never-branch-on-a-variable's-name rule (PDR-0045) are their modern enforcement.

## 5. Honest status — where the doors are missing

UAC's mechanics are substantially built and verified; the gaps cluster at authoring
doors. The full line-level audit is
`docs/architecture/REVIEW-2026-08-24-vfs-implementation-vs-spec.md`; headline gaps:

- **Access control / hidden state has no authoring surface** — `readable_by`/
  `writable_by` are compiler-hardcoded on both required surfaces, `exposed_to` fails
  open, and the observation path bypasses the checked accessor. Privacy mechanics are
  unauthorable today (several tickets; one systemic fix).
- **`variables_reference.yaml` variables never reach the compiler symbol table** — the
  pair/affordance/zone/group/message scopes allocate storage no effect, affordance, or
  drive can reference (`hamlet-33e520cebd`).
- **`lifetime` is hardcoded** on both required surfaces (environment.yaml → always
  `tick`; profiles → `persistent`/`episode`) — no author-declared counters/accumulators.
- A handful of **compile-green / crash-at-step-1 seams** (modulation `condition:`,
  three social-residue composition modes, zero-affordance packs, `num_agents`-shaped
  global tensors).

When extending this guide with recipes, only add recipes that compile *and run* against
the shipped engine — a recipe that demonstrates an open gap belongs in the review doc or
the tracker, not here.

## 6. Reference index

- Compiler: `docs/UNIVERSE-COMPILER.md`; CLI `python -m townlet.universe {compile,inspect,validate}`
- VFS (the ABI): `docs/architecture/vfs.md`, `docs/architecture/vfs-current-implementation.md`
- Strata: `docs/architecture/substrate-system.md`
- Schemas (one per authoring surface): `docs/config-schemas/` — affordances, bars,
  brain, drive_as_code, effects, enabled_actions, expressions, items, presentation,
  training, transition_rules, variables (⚠ stale, 2025-11), vfs-profiles
- Oracle discipline (what behaviour is frozen): `docs/oracle/ORACLE.md`,
  `docs/oracle/known-divergences.md`
