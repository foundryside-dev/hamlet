# Universe as Code (UAC)

Document date: 2026-08-24
Status: **Current** (reviewed 2026-08-24) — part of the six-document HLD set (PDR-0118).

Supersedes the archived UAC v2.5 document (2025-11-03) wholesale — the old text described
`cascade_engine`, `affordance_engine`, `reward_model`, ageing/retirement and a money convention
that no longer exist (or never shipped). Git history and `internal/docs/architecture-archive/` preserve it.

This guide is deliberately thin: it defines what UAC *is*, maps the old vocabulary onto the
current subsystems, states the current pack convention and the decided direction for it, and
routes to the authoritative reference docs. **It does not duplicate schemas.** Where this
document and a reference doc disagree, the reference doc — and above it, the source — wins.

`docs/config-schemas/` is the live reference tier. The 2026-08-24 recut (commit `c4e8bd58`)
swept it into the archive; it was restored on 2026-08-26 and is maintained. Trust a file there
unless it opens with its own staleness banner. Today `affordances.md`, `effects.md`,
`enabled_actions.md` and `items.md` carry one. (Corrected 2026-10-31: this note used to call the
whole directory archived and unmaintained.)

---

## 1. What UAC is now

The compiled target has three major declarative subsystems:

| subsystem | question it answers | authored in | authoritative doc |
| --- | --- | --- | --- |
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
are typed tokens over exposed state (no activity mask; that framing died at the 2026-08-26
token cut), effects and affordances read and write variables,
transitions are VTC programs over variables, rewards (DAC) read variables. There is no second
ontology underneath. In that precise sense the old standalone "universe spec" is subsumed: UAC
is the *authoring* layer, VFS is its *type system and runtime*, and this guide is closer to a
recipe book over VFS than to an independent specification. See `VFS.md`.

---

## 2. The contract: why "compiled" matters

A pack compiles to a `CompiledUniverse` carrying provenance hashes. The full declared-vs-enforced
picture is in `HLD.md` §5.2 — seventeen declared `*_hash` fields, ten hash stamps entering a
checkpoint, seven hard-compared by `assert_checkpoint_identity`. From UAC's side, the two that
matter most are `vfs_hash` (variables + observation + actions + transition graph) and
`drive_hash` (DAC); both are enforced.

What that buys:

- **Reproducibility** — the artifact pins exactly which world a checkpoint was trained in;
  resume refuses on hash mismatch, including across levels of the same pack.
- **Transfer** — rides on the token type schema (`token_type_schema_hash`), which is the
  same across universes, and on the pack's single global action vocabulary. The observation
  width (`TokenSpec.total_dims`) is per universe; there is no superset or activity mask
  (corrected 2026-10-31).
- **Deployment (target, not built)** — a trained policy is portable to any host that publishes
  the same declared telemetry (variables, bounds, normalization) and accepts the same action
  vocabulary at the same cadence. Fidelity lives *below* the interface. The export path itself
  is not yet built (`hamlet-0cdb8a6d1a`).

Never quote observation-dimension literals in docs — ask the compiled artifact
(`observation_spec.total_dims` / `observation_activity.active_mask`). See `HLD.md` §5.3.

---

## 3. Pack anatomy — the current convention

**Files are transport (declaration-store Cut A and Cut B, 2026-10-01; corrected here
2026-10-31).** The compiler discovers every `.yaml`/`.yml` document in the pack (subfolders
included, `.compiled` excluded) and identifies each one by its content, not its filename
(`townlet.universe.declarations.DeclarationStore`; full rules in
`docs/config-schemas/declarations.md`). A file's place decides only its scope: anything under
`levels/<level>/` is level scope, everything else is pack scope. The filenames below are the
shipped convention, not a manifest. `loaders/preflight.py` checks only that the pack directory
exists. It no longer lists required or forbidden files.

Pack-level declarations plus per-level declarations, **not** flat `configs/<level>/`. Shown with
the conventional filenames that `configs/default_curriculum` uses:

```
configs/<pack>/
├── experiment.yaml         # experiment:  pack identity / metadata              (required)
├── stratum.yaml            # stratum:     substrate, topology, boundaries       (required)
├── environment.yaml        # environment: meters, cascade/modulation graph,
│                           #              affordance registry                   (required)
├── variables.yaml          # variables:   the one registry-variable roster and
│                           #              item_profiles                         (required)
├── actions.yaml            # actions:     global action vocabulary              (required)
├── brain.yaml              # bare brain:  network / optimizer / loss            (required)
├── items.yaml              # items:       item catalog                          (optional)
├── effects.yaml            # bare effect_definitions                            (optional)
├── transition_rules.yaml   # bare transition_rules                              (optional)
└── levels/<level>/
    ├── bars.yaml           # bars:        meters, depletion, cascades, terminal bounds
    ├── affordances.yaml    # affordances: interactable world actions
    ├── drive.yaml          # drive:       DAC reward specification
    ├── training.yaml       # training:    hyperparameters (not part of the world)
    └── curriculum.yaml     # curriculum:  vision + temporal switches
```

Constraints worth stating because they are easy to get wrong:

- **Required means a required declaration, not a required file.** The required pack families
  are `experiment`, `stratum`, `environment`, `actions`, `brain` and `variables`. Every level
  requires `curriculum`, `bars`, `affordances`, `drive` and `training`
  (`REQUIRED_PACK` / `REQUIRED_LEVEL` in `universe/declarations.py`). A missing one, a duplicate
  one (with both `file:line` origins), or an unknown shape is a compile error.
- **Scope is enforced.** A pack-only family found under `levels/<level>/` (for example
  `variables`, `stratum`, `effects` or `items`) is refused with `DECLARATION_SCOPE`. The only
  level-scope optional families are a complete brain override and an item-appearance list.
- **Variables are declared once.** The single `variables:` declaration replaces the deleted
  `vfs_profiles.yaml` and `variables_reference.yaml` languages and the old variables in
  `environment.yaml` (Cut B). Its contract is `docs/config-schemas/variables.md`. An old
  payload fails at compile. There is no filename reader, alias or translation.
- There is **no** `configs/global_actions.yaml` and **no** file named `drive_as_code.yaml` in any
  shipped pack. Both paths appear in archived docs; a grep for either returns zero hits and will
  falsely "confirm" whatever you were checking.

Schemas for each declaration: `docs/config-schemas/`. Do not restate them here.

---

## 4. Files are transport; declarations are the unit (PDR-0117)

**Decided — accepted, owner-directed, 2026-08-24. Implemented 2026-10-01** by
declaration-store Cut A (content discovery, scope, merge and origins) and Cut B (one canonical
`variables` declaration); see §3 and `docs/config-schemas/declarations.md`. The text below is
the decision record. Source:
`internal/docs/product/decisions/0117-files-are-transport-declarations-are-the-unit.md`.

The 16-filename mandate is hardcoded across roughly nine compiler modules (parse/preflight plus
error strings). The 2026-08-24 VFS audit showed the sharpest cost: **three separate files declared
variables** — `environment.yaml`, `vfs_profiles.yaml`, `variables_reference.yaml` — with
divergent hardcoded `lifetime` and access semantics (resolved by Cut B: one `variables`
declaration, explicit lifetime and access on every variable). That is a defect class created by the split
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
| --- | --- | --- |
| meters/bars, depletion, "physics are data" | VFS variables + VTC programs (`VTCPassiveDepletionProgram`, `VTCBoundsClampProgram`) | `docs/config-schemas/bars.md`, `VFS.md` §11–13 |
| `cascades.yaml`, cross-meter dynamics, modulations | VTC (`VTCThresholdCascadeProgram`, `VTCModulationProgram`) | `VFS.md` §14 |
| terminal conditions, end-of-life | `VTCTerminalConditionProgram`; scoring → DAC | `VFS.md`, `docs/config-schemas/drive_as_code.md` |
| affordances, costs, effects, multi-tick | `affordances.yaml` + VTC action writes, occupancy, interaction progress | `docs/config-schemas/affordances.md`, `docs/config-schemas/effects.md` (both carry staleness banners) |
| `reward_model`, episodic scoring | **deleted** → DAC (`drive.yaml`, compiled to GPU graphs, `drive_hash`) | `docs/config-schemas/drive_as_code.md` |
| observability levels | compiled `TokenSpec`: declared exposure + normalization; `active_vision: partial` zeroes out-of-range spatial tokens without changing the width | `VFS.md` §8, `docs/config-schemas/variables.md` (current Cut B contract) |
| time of day, action masks | `curriculum.yaml` temporal switches + VTC affordance gates | `docs/config-schemas/enabled_actions.md` (carries a staleness banner) |
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

Modifier, extrinsic, intrinsic and shaping vocabularies:
`docs/config-schemas/drive_as_code.md`.

---

## 6. Honest status — where the doors are missing

UAC's mechanics are substantially built and verified; the gaps cluster at authoring doors. The
full line-level audit is
`internal/docs/architecture-archive/REVIEW-2026-08-24-vfs-implementation-vs-spec.md`; its **Headline** and
**Top gaps** sections are the source of truth. Read them rather than a restatement. The headline
shape: *the mechanics are built; the doors are missing.*

Summarised only far enough to route:

- **Access control / hidden state has no authoring surface.** `readable_by` / `writable_by` are
  compiler-hardcoded on both required surfaces, `exposed_to` fails open (omitted *and* explicitly
  `[]` both rewrite to `["agent"]`), and the observation path bypasses the checked accessor.
  Privacy mechanics are unauthorable today while appearing authorable — one systemic gap wearing
  about six ticket numbers. *(Superseded: every variable in the one `variables` declaration now
  declares `readable_by`, `writable_by` and `exposed_to`; the registry checks them and the
  `variable_element` publisher reads through `authorize_read`. See `VFS.md` §6.)*
- **`variables_reference.yaml` variables never reached the compiler symbol table** — the
  pair / affordance / zone / group / message scopes allocate storage that no effect, affordance
  or drive can reference (`hamlet-33e520cebd`). Five of nine scopes are unreachable declaratively. *(Superseded 2026-10-31: `variables_reference.yaml` is deleted (Cut B) and every declared variable enters the symbol table; zone, group, pair, message and agent_private are deleted; the scopes are global, agent, item and affordance.)*
- **`lifetime` is hardcoded** on both required surfaces (environment.yaml → always `tick`;
  profiles → `persistent` / `episode`), so no author-declared counters or accumulators exist.
  *(Superseded: every variable declares `lifetime` (`tick`, `episode` or `persistent`) in the
  `variables` declaration; see `docs/config-schemas/variables.md`.)*
- A handful of **compile-green / crash-at-step-1 seams**: VTC modulation `condition:`, three of
  the transition-rule write composition modes, zero-affordance packs, and `num_agents`-shaped global
  tensors. These violate the project's own fail-loud-at-compile discipline. *(Partly superseded
  2026-10-31: the modulation surface in the affordances declaration carries no `condition` and
  the compiler fixes the composition, so that seam is unreachable from a pack. The two occupancy
  claims on a transition-rule write fail at parse, and the rest compile and run. See `VFS.md`
  §14.4 and §16.3.)*

Note that the first three are all instances of the split-variable-surface problem PDR-0117
names — which is why the audit and PDR-0117 point at the same compiler front end. Declaration-store
Cuts A and B (2026-10-01) resolved all three.

**When extending this guide with recipes, only add recipes that compile *and run* against the
shipped engine.** A recipe that demonstrates an open gap belongs in the audit doc or the tracker,
not here.

### Future direction: declared propagation (proposed 2026-08-24 — not designed, not built)

**Everything in this sub-section is proposal — zero implementation exists.** The owner proposes
making observability itself a UAC/VFS declaration: **observation gates** — a declared
per-(observer, source) predicate that masks what reaches an agent's observation. Example shape:
vision range defined as an expression over a `brightness` variable on a continuous plane,
latched to zero everywhere except the observer's current floor. Under that model, today's fixed
`vision_range` / POMDP window becomes one special case of a declared propagation function.
Honestly placed: this is the *dynamic* counterpart of the static epistemic-access surface
(`exposed_to` / `readable_by`), which today has its own open gaps (§6 above — the 2026-08-24
VFS audit's systemic finding). Token observations, with their per-token presence bits, are the
natural carrier, so any design here follows the token migration rather than preceding it.

---

## 7. Reference index

- **Compiler**: `COMPILER.md`; CLI `python -m townlet.universe {compile,inspect,validate}`
- **VFS (the ABI)**: `VFS.md`; implementation map in
  `archive/vfs-current-implementation.md` (accurate per the 2026-08-24 audit on everything
  checked **except** its access-control and `agent_private` claims — see §6)
- **Strata**: `STRATA.md`; history in `archive/substrate-system.md`
- **Brain**: `BAC.md`, `docs/config-schemas/brain.md`
- **Schemas** (one per declaration family): `docs/config-schemas/` — the live reference
  tier (restored 2026-08-26; `affordances.md`, `effects.md`, `enabled_actions.md` and
  `items.md` open with staleness banners) — affordances, bars, brain, declarations,
  drive_as_code, effects, enabled_actions, expressions, items, presentation, training,
  transition_rules, variables
  (⚠ stale, 2025-11), vfs-profiles
- **Oracle discipline** (what behaviour is frozen): `docs/oracle/ORACLE.md`,
  `docs/oracle/known-divergences.md`
- **Status**: `README.md` — authoritative over this document where they disagree
