# Townlet — High-Level Design

Document date: 2026-08-24
Status: **Current** — first draft of the six-document HLD (PDR-0118, owner-amended to six);
pending review pass.

This is the top of the architecture tree. It is the reset artifact after the 2026 recovery:
the prior `docs/architecture/` corpus (~16 top-level documents plus an `hld/` tree, most of it
design-era 2025-11 carrying false "Approved for Implementation" status lines) was archived
wholesale to `docs/architecture/archive/`. **The archive is history, not record.** Where this
document and an archived one disagree, this one wins; where this document and `README.md`
disagree, README wins; where either disagrees with `src/townlet/`, the source wins.

---

## 1. What Townlet is

Townlet is **a rapid DRL experimentation framework for game designers**. A deep
reinforcement-learning substrate expressed as configuration: an environment — variables,
observation layout, substrate topology, affordances, effects, items, reward function, network
architecture — is written in YAML, compiled into one frozen hash-carrying `CompiledUniverse`,
and executed GPU-natively against torch tensors.

**The point is authoring.** Someone with an idea for a mechanic should be able to turn it into a
running, trainable, reproducible RL environment by writing config — no environment subclass, no
observation-tensor plumbing, no reward-function code. Every subsystem in this document exists to
move a category of "you must write Python for this" into "you can declare this."

**The design test**: *can a designer express this in a config pack?* If the answer is "only by
editing Python", that is a product defect, not a shortcut — and it is the defect worth fixing,
not the symptom that surfaced it. Prefer declarative surface over engine special-casing, even
when the special case is smaller. Corollary (PDR-0045): **never branch on a variable's name.**
The engine holds a *role*; the author binds the *referent*. `drive_as_code.py` declaring
`money_bar: str` as required-with-no-default is the in-tree model of that rule.

The survival world in `configs/default_curriculum` — eight meters, fourteen affordances, one 8×8
grid — is the **first-class demonstration of the idea, not the product**. Its content must not
harden into the framework.

---

## 2. The three compiled subsystems

The compiled target has three major declarative subsystems, distinguished by the question each
answers. All three compile through one pipeline into one artifact.

| subsystem | question | authored in (current convention) | doc |
|---|---|---|---|
| **Strata** | *Where can things be?* — space itself | `stratum.yaml` | `STRATA.md` |
| **UAC** — Universe as Code | *What exists, and how does it change?* | the rest of the pack | `UAC.md` |
| **BAC** — Brain as Code | *How do agents think?* | `brain.yaml` | `BAC.md` |

Historically (UAC v2.5, 2025-11) "Universe as Code" meant *strata + world config* as one blob.
Strata is now promoted out as its own subsystem — space is a different kind of declaration from
world rules, compiled against a different DTO — and UAC names the world-rules layer.

**UAC's ABI is VFS.** The Variable & Feature System is the typed state / observation /
transition contract that everything in UAC compiles down to: bars are variables, observations
are exposed variables behind an activity mask, effects and affordances read and write variables,
transitions are VTC programs over variables, rewards read variables. There is no second ontology
underneath. See `VFS.md`.

---

## 3. Strata — the space subsystem (summary)

**Full treatment: `STRATA.md`.** Strata declares space itself: which substrate family exists
(`grid` — 2D `square` or 3D `cubic`; `gridnd`; `continuous`; `continuousnd`; `aspatial`), how
cells connect, what happens at the edges (`clamp` / `wrap` / `bounce` / `sticky`), how distance
is measured (`manhattan` / `euclidean` / `chebyshev`), and how position enters the observation
(`relative` / `scaled` / `absolute`). It is authored once per pack in `stratum.yaml`
(`SubstrateConfig` / `StratumConfig` in `src/townlet/config/stratum_config.py`), read only from
the pack root, and therefore shared by every level — which is exactly what makes allocated
observation width identical across a pack's levels, and cross-level checkpoint transfer real.

Two seams matter at this altitude, and both are *composed* rather than constant. The **action
vocabulary** is substrate movement actions (a function of substrate type *and* declared
parameters such as `diagonals`) plus custom actions from `actions.yaml`, under a fixed ordering
contract — movement, then `INTERACT` at `[-2]`, then `WAIT` at `[-1]`. The **observation
seam** is the five-member shape contract on `SpatialSubstrate` (`src/townlet/substrate/base.py`):
the compiler asks the substrate instance for every spatial width and derives none itself.
`STRATA.md` carries the substrate family table, the three POMDP gates, the corrections to
CLAUDE.md's action-count and POMDP-support tables, and the one live TODO-VERIFY.

---

## 4. UAC and BAC in one paragraph each

**UAC** is the world-rules layer: variables and their bounds and normalization, observation
exposure, items, effects, affordances and their costs and multi-tick semantics, the action
vocabulary, compiled transitions (VTC), terminal conditions, and rewards. It compiles to VFS.
**DAC** — Drive as Code, the declarative reward system authored in each level's `drive.yaml` and
executed by `DACEngine` (`src/townlet/environment/dac_engine.py`) — is a UAC surface, not a
fourth subsystem: it reads VFS variables, compiles to GPU computation graphs, and carries its
own `drive_hash`. Full treatment: `UAC.md`; reward vocabulary:
`docs/config-schemas/drive_as_code.md`.

**BAC** is the brain layer: network architecture, optimizer, loss, replay, and — as target state
— the behaviour contract and the declarative think-loop graph. Only the network/optimizer/loss
slice exists today (`brain.yaml` + `BrainConfig`); the fuller design has **zero code footprint**.
`BAC.md` states which is which, and is disciplined about it.

---

## 5. The Universe Compiler and the provenance contract

### 5.1 One artifact

`src/townlet/universe/compiler.py` runs a seven-stage pipeline — parse → symbol table → resolve
→ cross-validate → metadata → optimization → emit/cache — assembling Strata, UAC and BAC into
one frozen `CompiledUniverse`. **Nothing reads YAML past compile time**: the runtime is
instantiated from the artifact via `CompiledUniverse.create_environment(...)` →
`VectorizedHamletEnv.from_universe(...)`. Details, error codes, CLI and cache semantics:
`COMPILER.md`.

`compile()` requires an explicit `primary_level`; implicit selection raises — and so does the
CLI, which requires `--primary-level` on every subcommand taking a config directory.
`CompiledUniverse` is single-level by construction: `get_level` / `to_level` navigate and
`all_levels` is a dict field; there is no `.levels` mapping, and the cache holds one artifact
per level (`.compiled/universe-<level>.msgpack`).

### 5.2 Declared hashes vs. enforced hashes

The artifact carries **sixteen declared `*_hash` fields** (`src/townlet/universe/compiled.py`).
That is not the same as sixteen enforced ones, and the distinction is the architectural content:

- **Enforced.** One shared gate, `assert_checkpoint_identity`
  (`src/townlet/training/checkpoint_utils.py`), is called by both the training-resume path
  (`demo/runner.py`) and the serving path (`demo/live_inference.py`). Eight hash fields are
  stamped into a checkpoint; **seven are hard-compared** — `vfs_hash`, `drive_hash`, the
  effective `brain_hash`, and the four per-level content hashes — alongside observation dim,
  action count, observation-field UUIDs and `primary_level`. A checkpoint therefore refuses to
  load into a universe it does not match, *including a different level of the same pack*.
- **Computed but not enforced, recorded rather than hidden.** `observation_schema_hash` is
  stamped and never compared. The five pack-level hashes (`experiment`, `stratum`,
  `environment`, `actions`, `items`) are computed and serialized and read by no checkpoint
  consumer — only the differential harness reads them, as a provenance diff between two
  compiles. This is `DIV-001` in `docs/oracle/known-divergences.md`.
- `config_hash` (with `provenance_id`: compiler version, git sha, python/torch/pydantic
  versions) is the **cache** fingerprint, not the checkpoint gate. `brain_hash` is the SHA256 of
  the primary level's *effective* brain config after overrides — level-scoped, like
  `drive_hash`; `pack_brain_hash` differing from it means the level declared its own brain.

⚠️ Several summaries (including CLAUDE.md's) present the contract as the tidy triple
`config_hash` / `vfs_hash` / `drive_hash`. That is a useful shorthand and a false inventory.
Quote the enforced set, or point here.

### 5.3 Why the contract matters

1. **Reproducibility.** The artifact pins exactly which world a checkpoint was trained in.
   Resume refuses on hash mismatch rather than silently loading a policy into a different world.
2. **Cross-level transfer.** Observation is a fixed-width **superset with a per-level activity
   mask**: *allocated* width (`observation_spec.total_dims`) is identical at every level of a
   pack, *active* width (`sum(observation_activity.active_mask)`) varies, and inactive slots are
   held at zero rather than removed. POMDP does not shrink the tensor — it zeroes the
   grid-encoding block and activates the local-window block. Combined with a global action
   vocabulary, that is what makes checkpoint transfer between levels real rather than aspirational.
3. **Deployment (target, not built).** A trained policy should be portable to any host that
   publishes the same declared telemetry — variables, bounds, normalization — and accepts the
   same action vocabulary at the same cadence. Fidelity lives *below* the interface: an agent
   trained against declared telemetry on a coarse substrate can in principle run against a
   high-fidelity simulation publishing the same manifest. **The export path is not yet built**
   (tracker `hamlet-0cdb8a6d1a`).

> **No dimension literals.** "Observation dim" is two quantities (allocated vs. active), and
> conflating them is what corrupted every dimension table in the old corpus. Never write either
> number in a document — ask the compiled artifact:
> ```python
> u = UniverseCompiler().compile(Path("configs/default_curriculum"),
>                                primary_level="L1_full_observability")
> u.observation_spec.total_dims            # allocated
> sum(u.observation_activity.active_mask)  # active
> ```
> `ObservationActivity` (`src/townlet/universe/dto/observation_activity.py`) also carries
> `group_slices` (bars / spatial / affordance / temporal / custom) and `active_field_uuids`.

---

## 6. Files are transport; declarations are the unit

**Decided, not yet implemented** (PDR-0117). The pack layout today mandates 16 distinct
filenames, hardcoded across the compiler's parse/preflight front end and its error strings.
Filenames carry no information the content does not already carry: No-Defaults plus
`extra="forbid"` make every declaration self-identifying.

The direction: the compiler globs the pack (subfolders included), parses every YAML document
against the closed typed schemas, and merges into one compiled profile — "whatever files are
available, we'll compile into a single profile." Filenames become authoring **convention**,
never semantics. "Required file" becomes "required declaration". Merge and override are by
declared id with loud collision refusal naming both declaring files. Determinism is preserved by
canonical merge order (sorted paths) so `config_hash` stays stable, and per-declaration
file:line provenance must survive into diagnostics.

Until that lands, `UAC.md` §3 documents the current filename convention as what the shipped
compiler expects, and `COMPILER.md` marks the front end as the surface slated to change.

---

## 7. Document map

| document | covers |
|---|---|
| `HLD.md` (this) | product framing, the trio, the compiler-and-provenance contract |
| `STRATA.md` | space: substrate families, topology, boundaries, distance, the action and observation seams |
| `UAC.md` | world rules: the authoring layer over VFS, pack anatomy, concept map, gaps |
| `VFS.md` | the ABI: variables, scopes, access control, observation spec, VTC |
| `BAC.md` | the brain: what exists today vs. design target, honestly separated |
| `COMPILER.md` | the seven-stage pipeline, validation, caching, CLI, troubleshooting |

Supporting, and authoritative in their lanes:

- `docs/config-schemas/` — one reference per authoring surface (affordances, bars, brain,
  drive_as_code, effects, enabled_actions, expressions, items, presentation, training,
  transition_rules, variables ⚠ stale 2025-11, vfs-profiles). **Schemas live here, not in the
  HLD set.**
- `docs/oracle/ORACLE.md`, `docs/oracle/known-divergences.md` — what behaviour is frozen, and
  every accepted difference. The oracle never mutates; a diff against it is a defect in the
  rebuild unless the register says otherwise. Never edit anything under `.oracle/`.
- `README.md` — current, honest status. **Authoritative over any document in this set** on
  what ships.
- `docs/product/vision.md`, `docs/product/decisions/` — product framing and decision record.
- `docs/architecture/archive/` — the pre-2026-08-24 corpus. Historical record; internal links
  may dangle. Cite for history, never as evidence that something is implemented.

---

## 8. Honest status

`README.md` §Status is the canonical version of this section; what follows is the architectural
shape of the gaps.

**Built and verified.** A YAML pack compiles to a frozen hash-carrying artifact; that artifact
drives the vectorized torch environment; reward functions are config with no Python reward
classes left to subclass; VFS access control is enforced at runtime where it runs; the training
entry point runs end to end. The 2026-08-24 line-level audit
(`archive/REVIEW-2026-08-24-vfs-implementation-vs-spec.md`) found ~48 spec claims IMPLEMENTED
with file:line evidence, and **nothing audited was entirely absent**.

**The recurring shape: the mechanics are built; the doors are missing.** That audit's Headline
and Top-gaps sections are the source of truth for honest status — read them rather than a
restatement. The one systemic story: declared epistemic state has no working authoring door.
`readable_by` / `writable_by` are compiler-hardcoded on both required surfaces, `exposed_to`
fails open, the observation path bypasses the checked accessor, and the one file where an author
*could* declare access and the pair/affordance/zone/group/message scopes
(`variables_reference.yaml`) never enters the compiler symbol table. Every privacy /
hidden-state / social-inference mechanic VFS presents as its payoff is currently unauthorable
while appearing authorable. It is one gap wearing about six ticket numbers and should be fixed
as one design unit.

**Intent, not built** (from README, stated plainly because older docs blur the line): BAC layers
1 and 3; one standard compiler for both halves of an experiment (`CompiledBrain` exists only in
docs); a second demonstrator that varies the domain rather than the substrate; the "Low Energy
Delirium" reward-hacking lesson (no shipped level declares the multiplicative reward it depends
on); the deployment/export path (`hamlet-0cdb8a6d1a`); and PDR-0117 discovery-merge.

**A note on CI.** The gates that hold on `project-recovery*` branches are run locally, by hand —
no workflow has ever run on `project-recovery` (filigree `hamlet-2100105c9a`). `main` carries the
recovery and its nightly is green; between merges `main` trails the branch by design.
