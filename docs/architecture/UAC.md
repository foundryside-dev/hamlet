# Universe as Code (UAC)

Document date: 2026-08-24
Status: **Current** — first draft of the six-document HLD (PDR-0118, owner-amended to six);
pending review pass.

Supersedes the archived UAC v2.5 document (2025-11-03) wholesale — the old text described
`cascade_engine`, `affordance_engine`, `reward_model`, ageing/retirement and a money convention
that no longer exist (or never shipped). Git history and `docs/architecture/archive/` preserve it.

This guide is deliberately thin: it defines what UAC *is*, maps the old vocabulary onto the
current subsystems, states the current pack convention and the decided direction for it, and
routes to the authoritative reference docs. **It does not duplicate schemas.** Where this
document and a reference doc disagree, the reference doc — and above it, the source — wins.

---

## 1. What UAC is now

The compiled target has three major declarative subsystems:

| subsystem | question it answers | authored in | authoritative doc |
|---|---|---|---|
| **Strata** | *Where can things be?* — substrate type, topology, boundaries, distance metric, position encoding | `stratum.yaml` | `STRATA.md`; `src/townlet/config/stratum_config.py` |
| **UAC — Universe as Code** | *What exists, and how does it change?* — variables, observations, items, effects, affordances, actions, transitions, rewards, terminal conditions | everything else in the pack (§3) | this doc as router; `VFS.md`; `docs/config-schemas/` |
| **BAC — Brain as Code** | *How do agents think?* — network architecture, optimizer, loss; and as target state, behaviour contract and think-loop graph | `brain.yaml` | `BAC.md` |

Historically (v2.5) "Universe as Code" meant *strata + world config* as one blob. Strata is now
promoted out as its own subsystem — space is a different kind of declaration from world rules,
compiled against a different DTO — and UAC is the name for the third pillar: **the world-rules
layer**. All three compile through the Universe Compiler
(`src/townlet/universe/compiler.py`, seven stages — see `COMPILER.md`) into one frozen,
hash-carrying `CompiledUniverse`.

**UAC's ABI is VFS.** The Variable & Feature System is the typed state / observation /
transition contract that everything in UAC compiles down to: bars are variables, observations
are exposed variables behind an activity mask, effects and affordances read and write variables,
transitions are VTC programs over variables, rewards (DAC) read variables. There is no second
ontology underneath. In that precise sense the old standalone "universe spec" is subsumed: UAC
is the *authoring* layer, VFS is its *type system and runtime*, and this guide is closer to a
recipe book over VFS than to an independent specification. See `VFS.md`.

---

## 2. The contract: why "compiled" matters

A pack compiles to a `CompiledUniverse` carrying provenance hashes. The full declared-vs-enforced
picture is in `HLD.md` §5.2 — sixteen declared `*_hash` fields, eight stamped into a checkpoint,
seven hard-compared by `assert_checkpoint_identity`. From UAC's side, the two that matter most
are `vfs_hash` (variables + observation + actions + transition graph) and `drive_hash` (DAC);
both are enforced.

What that buys:

- **Reproducibility** — the artifact pins exactly which world a checkpoint was trained in;
  resume refuses on hash mismatch, including across levels of the same pack.
- **Transfer** — the allocated observation width and the global action vocabulary are constant
  across a pack's levels (superset + activity mask), which is what makes cross-level checkpoint
  transfer real.
- **Deployment (target, not built)** — a trained policy is portable to any host that publishes
  the same declared telemetry (variables, bounds, normalization) and accepts the same action
  vocabulary at the same cadence. Fidelity lives *below* the interface. The export path itself
  is not yet built (`hamlet-0cdb8a6d1a`).

Never quote observation-dimension literals in docs — ask the compiled artifact
(`observation_spec.total_dims` / `observation_activity.active_mask`). See `HLD.md` §5.3.

---

## 3. Pack anatomy — the current convention

⚠️ **This is the current convention: what the shipped compiler expects today, not a mandate that
will hold.** PDR-0117 (§4) decided that filenames become authoring convention rather than
semantics. Until discovery-merge lands, these names are load-bearing and the compiler's
preflight (`src/townlet/universe/loaders/preflight.py`) enumerates them.

Pack-level shared files plus per-level overrides — **not** flat `configs/<level>/`:

```
configs/<pack>/
├── experiment.yaml         # pack identity / experiment metadata            (required)
├── stratum.yaml            # Strata: substrate, topology, boundaries        (required, shared)
├── environment.yaml        # UAC: VFS variable definitions                  (required, shared)
├── vfs_profiles.yaml       # UAC: global/agent/item profile variables       (required, pack root)
├── actions.yaml            # UAC: global action vocabulary                  (required, shared)
├── brain.yaml              # BAC: network / optimizer / loss                (required, shared)
├── items.yaml              # UAC: item definitions                          (required, pack root)
├── effects.yaml            # UAC: effect definitions                        (optional, pack root)
├── action_labels.yaml      # UAC: action terminology preset                 (optional, shared)
├── variables_reference.yaml  # UAC: optional static overlay (see §6)        (optional, shared)
└── levels/<level>/
    ├── bars.yaml           # UAC: meters, depletion, terminal conditions
    ├── affordances.yaml    # UAC: interactable world actions
    ├── drive.yaml          # UAC: DAC reward specification (REQUIRED per level)
    ├── training.yaml       # hyperparameters (not part of the world)
    └── curriculum.yaml     # vision + temporal switches
```

Two constraints worth stating because they are easy to get wrong:

- **`vfs_profiles.yaml` and `effects.yaml` are pack-root only.** Preflight's
  `forbidden_level_files` list (`loaders/preflight.py:55`) names exactly those two; either one
  found in a level directory raises `SCOPING_FORBIDDEN_LEVEL_FILE`. Separately,
  `required_experiment_files` (`preflight.py:54`) is `["vfs_profiles.yaml", "items.yaml"]` —
  both must exist at the pack root or preflight raises `SCOPING_MISSING_EXPERIMENT_FILE`. (The
  later YAML-syntax pass skips a missing `items.yaml`, but scoping preflight runs first, so the
  file is required in practice.)
- **`variables_reference.yaml` is optional**, not required. `configs/default_curriculum` has
  none; `configs/L5_multi_agent` does. The older "all packs MUST include it" claim is false.
- There is **no** `configs/global_actions.yaml` and **no** file named `drive_as_code.yaml` in any
  shipped pack. Both paths appear in archived docs; a grep for either returns zero hits and will
  falsely "confirm" whatever you were checking.

Schemas for each surface: `docs/config-schemas/`. Do not restate them here.

---

## 4. Files are transport; declarations are the unit (PDR-0117)

**Decided — accepted, owner-directed, 2026-08-24. Not yet implemented.** Source:
`docs/product/decisions/0117-files-are-transport-declarations-are-the-unit.md`.

The 16-filename mandate is hardcoded across roughly nine compiler modules (parse/preflight plus
error strings). The 2026-08-24 VFS audit showed the sharpest cost: **three separate files declare
variables** — `environment.yaml`, `vfs_profiles.yaml`, `variables_reference.yaml` — with
divergent hardcoded `lifetime` and access semantics. That is a defect class created by the split
itself. Filenames carry no information the content does not already carry: No-Defaults plus
`extra="forbid"` make every declaration self-identifying.

Owner framing, recorded: *"whatever files are available, we'll compile into a single profile."*
Authors get their own domain model — `ship.yaml`, `weather.yaml`, `economy.yaml`, one file per
designer-facing concept spanning our subsystem taxonomy — and proper subfolder support makes
packs compose (mixins, mod-packs).

The five calls:

1. **Discovery replaces the manifest.** The compiler globs the pack (subfolders included), parses
   every YAML document against the closed typed schemas, and merges into one compiled profile.
   Filenames become authoring convention, never semantics.
2. **"Required file" becomes "required declaration"** — e.g. every level must declare exactly one
   `drive` block. The requirement was always about the declaration.
3. **Override/merge is by declared id, not by file shadowing**, with **loud collision refusal**:
   a compile error naming both declaring files. This matches the house fail-loud style.
4. **Determinism preserved**: canonical merge order (sorted paths) so `config_hash` stays stable;
   per-declaration file:line provenance must survive into diagnostics.
5. **Sequencing**: its own unit after the token-observation migration; it pairs naturally with the
   variable-surface unification the audit demands, since both land in the same compiler front end.

Reversal trigger: if discovery-merge measurably degrades compile-error quality (authors cannot
tell where a refused declaration came from) and per-declaration provenance cannot fix it,
reinstate a thin required manifest (`pack.yaml` index) — **not** the 16-filename mandate.

The compiler-side implications are noted in `COMPILER.md` §Forward.

---

## 5. Concept map: v2.5 vocabulary → current subsystem

| v2.5 chapter said | where it actually lives now | reference |
|---|---|---|
| meters/bars, depletion, "physics are data" | VFS variables + VTC programs (`VTCPassiveDepletionProgram`, `VTCBoundsClampProgram`) | `docs/config-schemas/bars.md`, `VFS.md` §11–13 |
| `cascades.yaml`, cross-meter dynamics, modulations | VTC (`VTCThresholdCascadeProgram`, `VTCModulationProgram`) | `VFS.md` §14 |
| terminal conditions, end-of-life | `VTCTerminalConditionProgram`; scoring → DAC | `VFS.md`, `docs/config-schemas/drive_as_code.md` |
| affordances, costs, effects, multi-tick | `affordances.yaml` + VTC action writes, occupancy, interaction progress | `docs/config-schemas/affordances.md`, `effects.md` |
| `reward_model`, episodic scoring | **deleted** → DAC (`drive.yaml`, compiled to GPU graphs, `drive_hash`) | `docs/config-schemas/drive_as_code.md` |
| observability levels | VFS observation spec: exposure + normalization + activity mask | `VFS.md` §8, `docs/config-schemas/vfs-profiles.md` |
| time of day, action masks | `curriculum.yaml` temporal switches + VTC affordance gates | `docs/config-schemas/enabled_actions.md` |
| grid, positions | **Strata** (promoted out of UAC) | `STRATA.md`; `archive/substrate-system.md` for history |
| money ≈ $100 at 1.0, clamped | **dead** — the `[0,1]` clamps were removed in WS-1(e); money is a bounded variable like any other | `docs/config-schemas/bars.md` |
| ageing, retirement, Bed/Job/Hospital/Bar set | never shipped; the shipped demonstration pack is `configs/default_curriculum` (14 affordances) | `CLAUDE.md` "State Representation" |
| expression snippets in YAML | the closed, typed expression language | `docs/config-schemas/expressions.md` |

Two v2.5 principles survive unchanged and remain the point: **physics are data; values are
data.** The no-defaults principle (`extra="forbid"`, no hidden behavioral defaults) and the
never-branch-on-a-variable's-name rule (PDR-0045) are their modern enforcement.

### DAC is a UAC surface

Drive as Code is not a fourth subsystem. Reward logic lives in each level's `drive.yaml`, is
compiled by the Universe Compiler, and is executed by `DACEngine`
(`src/townlet/environment/dac_engine.py`) as GPU computation graphs. It reads VFS variables like
everything else in UAC, and carries its own enforced `drive_hash`. The `RewardStrategy` classes
and `training.yaml: reward_strategy` were deleted outright, not dual-pathed.

```
total_reward = extrinsic + (intrinsic × effective_intrinsic_weight) + shaping
where effective_intrinsic_weight = base_weight × modifier₁ × modifier₂ × …
```

Modifier, extrinsic, intrinsic and shaping vocabularies: `docs/config-schemas/drive_as_code.md`.

---

## 6. Honest status — where the doors are missing

UAC's mechanics are substantially built and verified; the gaps cluster at authoring doors. The
full line-level audit is
`docs/architecture/archive/REVIEW-2026-08-24-vfs-implementation-vs-spec.md`; its **Headline** and
**Top gaps** sections are the source of truth. Read them rather than a restatement. The headline
shape: *the mechanics are built; the doors are missing.*

Summarised only far enough to route:

- **Access control / hidden state has no authoring surface.** `readable_by` / `writable_by` are
  compiler-hardcoded on both required surfaces, `exposed_to` fails open (omitted *and* explicitly
  `[]` both rewrite to `["agent"]`), and the observation path bypasses the checked accessor.
  Privacy mechanics are unauthorable today while appearing authorable — one systemic gap wearing
  about six ticket numbers.
- **`variables_reference.yaml` variables never reach the compiler symbol table** — the
  pair / affordance / zone / group / message scopes allocate storage that no effect, affordance
  or drive can reference (`hamlet-33e520cebd`). Five of nine scopes are unreachable declaratively.
- **`lifetime` is hardcoded** on both required surfaces (environment.yaml → always `tick`;
  profiles → `persistent` / `episode`), so no author-declared counters or accumulators exist.
- A handful of **compile-green / crash-at-step-1 seams**: VTC modulation `condition:`, three of
  eleven social-residue composition modes, zero-affordance packs, and `num_agents`-shaped global
  tensors. These violate the project's own fail-loud-at-compile discipline.

Note that the first three are all instances of the split-variable-surface problem PDR-0117
names — which is why the audit and PDR-0117 point at the same compiler front end.

**When extending this guide with recipes, only add recipes that compile *and run* against the
shipped engine.** A recipe that demonstrates an open gap belongs in the audit doc or the tracker,
not here.

---

## 7. Reference index

- **Compiler**: `COMPILER.md`; CLI `python -m townlet.universe {compile,inspect,validate}`
- **VFS (the ABI)**: `VFS.md`; implementation map in
  `archive/vfs-current-implementation.md` (current as of 2026-08-23 on everything checked
  **except** its access-control and `agent_private` claims — see §6)
- **Strata**: `STRATA.md`; history in `archive/substrate-system.md`
- **Brain**: `BAC.md`, `docs/config-schemas/brain.md`
- **Schemas** (one per authoring surface): `docs/config-schemas/` — affordances, bars, brain,
  drive_as_code, effects, enabled_actions, expressions, items, presentation, training,
  transition_rules, variables (⚠ stale, 2025-11), vfs-profiles
- **Oracle discipline** (what behaviour is frozen): `docs/oracle/ORACLE.md`,
  `docs/oracle/known-divergences.md`
- **Status**: `README.md` — authoritative over this document where they disagree
