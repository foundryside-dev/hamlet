# Townlet documentation — a map, with trust levels

> ⚠️ **Read this first: `docs/` is design intent, not a record of what shipped.**
>
> 573 markdown files live here. Roughly 90% were last touched in 2025-11 or 2026-05, before the
> current recovery work on `project-recovery`. Many describe subsystems that were designed,
> documented, marked "Approved for Implementation" or "✅ Implemented" — and never built.
>
> **Three rules:**
>
> 1. **Never cite a document here as evidence that something is implemented.** Check
>    `src/townlet/` first. A status line in a design doc is a statement of intent that was
>    never revisited.
> 2. **Where a document disagrees with the root `README.md`, the root README is right.** It is
>    current, honest about status, and carries the correct product framing.
> 3. **Absence here means nothing.** `src/townlet/oracle/`, the strangler rewrite, `items/` and
>    `effects/` have no coverage in `architecture/` at all.

---

## What Townlet is

A **rapid DRL experimentation framework for game designers**. An environment — variables,
observation layout, substrate topology, affordances, effects, items, reward function — is
written in YAML, compiled into one frozen hash-carrying `CompiledUniverse`, and executed
GPU-natively against torch tensors.

The point is **authoring**. The survival world in `configs/default_curriculum` is the
first-class demonstration of that idea, not the product.

Fuller framing: root [`README.md`](../README.md) and [`product/vision.md`](product/vision.md).

---

## Trust tiers

### ✅ Current — trust these

| path | what it is |
|---|---|
| [`product/`](product/) | Vision, roadmap, metrics, current state, and **42 numbered PDRs**. The live decision record. |
| [`oracle/`](oracle/) | The pinned oracle and its divergence register. Governs the strangler rewrite. |
| [`config-schemas/`](config-schemas/) | Config reference per file type. Closest thing to an authoring manual. |
| [`UNIVERSE-COMPILER.md`](UNIVERSE-COMPILER.md) | The seven-stage UAC pipeline. |
| [`architecture/vfs-current-implementation.md`](architecture/vfs-current-implementation.md) | VFS as built, with a source map. The model other docs should follow. |

### 🎯 Design intent — the target, not the present

These describe where the project is going. The designs are live; their **status lines are
false**. Read them for direction, never as evidence of code.

| path | reality check |
|---|---|
| [`architecture/BRAIN_AS_CODE.md`](architecture/BRAIN_AS_CODE.md), [`architecture/hld/02-brain-as-code.md`](architecture/hld/02-brain-as-code.md) | Both say "Approved for Implementation". `execution_graph` / `cognitive_topology` / `agent_architecture` return **zero grep hits** in `src/` and `configs/`. |
| [`architecture/UNIVERSE_AS_CODE.md`](architecture/UNIVERSE_AS_CODE.md) | Core idea shipped. Specifics did not: `cascades.yaml`, `reward_model`, `VectorizedTownletEnv`, and the all-values-in-`[0,1]` invariant are gone or never existed. |
| [`architecture/COMPILER_ARCHITECTURE.md`](architecture/COMPILER_ARCHITECTURE.md) | Design-era. Describes sub-compilers never wired (notably `CuesCompiler`), and sets a backwards-compatibility success criterion this project rejects. |
| [`architecture/hld/`](architecture/hld/) | 12-part HLD. The most complete statement of the target. See the review below before acting on it. |
| [`architecture/vfs.md`](architecture/vfs.md) | Design-era VFS spec, largely sound. Its §2.3 dimension table was false and is now corrected in place. |

Start here: [`architecture/REVIEW-2026-08-15-architecture-docs-and-hld.md`](architecture/REVIEW-2026-08-15-architecture-docs-and-hld.md)
— a verified doc-vs-code and doc-vs-doc audit of this whole tier.

### 📦 Historical record — dated, do not follow

Kept because git history and rationale are worth preserving. Not maintained, not corrected.

`plans/` · `bugs/` · `tasks/` · `research/` · `reviews/` · `investigations/` ·
`analysis/` · `arch-analysis-2026-05-16-1200/` · `audits/` · `decisions/` · `designs/` ·
`development/` · `diagrams/` · `examples/` · `implementation-status/` · `methods/` ·
`performance/` · `testing/` · `vfs/`

**253 of the 573 files are already inside `archive/`, `closed/` or `done/` subdirectories** —
i.e. explicitly dispositioned. The live surface is 320. `plans/` in particular is 179 files but
only **20** live.

### 🎓 Pedagogy

[`teachable_moments/`](teachable_moments/) — emergent behaviours and "interesting failures"
preserved as teaching material rather than immediately fixed. This is a property of the
framework, not the mission.

---

## Where to actually start

**Running something**
Root [`README.md`](../README.md), then [`manual/`](manual/) for the operational guides, then
[`config-schemas/`](config-schemas/) to change what runs. Levels live under
`configs/default_curriculum/levels/` — there are no flat `configs/<level>/` packs.

**Authoring a universe**
[`config-schemas/`](config-schemas/) is the reference. [`UNIVERSE-COMPILER.md`](UNIVERSE-COMPILER.md)
explains what happens to it. [`guides/`](guides/) has migration notes of varying vintage.

**Understanding the direction**
[`product/vision.md`](product/vision.md) → [`product/roadmap.md`](product/roadmap.md) →
[`product/decisions/`](product/decisions/). Then the HLD, read as intent.

**Changing the engine**
`src/townlet/` is the authority. [`oracle/ORACLE.md`](oracle/ORACLE.md) governs what you are
allowed to change without registering a divergence.

---

## Known traps

- **Two `PDR` numbering schemes.** [`product/decisions/`](product/decisions/) uses four digits
  (`PDR-0042`) and is the live series. [`decisions/`](decisions/) uses three (`PDR-002`), is
  from 2025-11, and is unrelated. A reference to "PDR-002" is ambiguous; "PDR-0002" is not.
- **Observation dimensions — the question is ambiguous, which is why every table disagrees.**
  The observation is a fixed **124-slot superset** with a per-level activity mask. *Allocated*
  width is 124 at every level (this is what makes obs width constant across grid sizes, enabling
  transfer learning). *Active* width has three values — 95 / 56 / 99 — matching the three real
  universes. Tables in this corpus quote one number without saying which, and several assume
  grid sizes no level can express. Read `observation_spec.total_dims` and
  `observation_activity.active_mask` off the compiled artifact. Both are also on their way out:
  the fixed-width scheme is being replaced by token observations.
- **`drive_as_code.yaml` does not exist.** The file is `drive.yaml`, per level. Grepping the
  wrong name returns zero hits and will falsely "confirm" whatever you were checking.
- **`configs/global_actions.yaml` and `configs/templates/` do not exist.** Both paths are cited
  by multiple documents. `actions.yaml` is pack-level.
- **`substrate.yaml` is `stratum.yaml`** in real packs.
- **The five curriculum levels are three universes.** `bars.yaml`, `affordances.yaml` and
  `drive.yaml` are byte-identical across all five; grid size is pack-level and unoverridable.

---

## Conventions for new documents

- **State status honestly, and date it.** "Approved for Implementation" with no date is how
  this corpus became untrustworthy.
- **Cite source paths, not claims.** `vfs-current-implementation.md` is the model: a source-map
  table and no dimension literals.
- **Never write a dimension, hash, or coverage number** you have not just measured — and say
  when you measured it.
- **Decisions go in [`product/decisions/`](product/decisions/)** as the next numbered PDR.
