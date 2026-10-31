# Townlet documentation

Start with the root [README](../README.md) for what Townlet is and how to run it. This page
says where everything else is and how far to rely on it.

> **Source code is the authority.** Townlet is mid-rewrite and some documents describe designs
> that are only partly built. When a document and `src/townlet/` disagree, the code is right, and
> where a document disagrees with the root README, the README is right. Several reference pages
> open with a dated banner listing what is known to be out of date; read it before the body.
>
> The six documents in [architecture/](architecture/) are the architecture of record, and the
> code is being brought into line with them. Older design documents that had drifted have been
> removed from the published tree; they remain in git history.
>
> Some pages cite paths under `internal/` (archived designs, plans and product decision records).
> That folder is not published. Recover it with
> `git checkout a800da6a -- internal && git rm -r -q --cached internal`.

## By task

| I want to… | Read |
| --- | --- |
| Run training and the live viewer | [manual/UNIFIED_SERVER_USAGE.md](manual/UNIFIED_SERVER_USAGE.md) |
| Write or change a config pack | [config-schemas/](config-schemas/), starting with [declarations.md](config-schemas/declarations.md) and [variables.md](config-schemas/variables.md) |
| See worked substrate examples | [examples/](examples/) |
| Understand how the system fits together | [architecture/HLD.md](architecture/HLD.md) |
| Change engine behaviour safely | [oracle/ORACLE.md](oracle/ORACLE.md) and the [divergence register](oracle/known-divergences.md) |
| Understand where the project is going | [vision.md](vision.md) |

## Directory guide

| Directory | Contents | Reliability |
| --- | --- | --- |
| [architecture/](architecture/) | Six-document design set: [HLD](architecture/HLD.md), [compiler](architecture/COMPILER.md), [spatial substrates](architecture/STRATA.md), [universe as code](architecture/UAC.md), [brain as code](architecture/BAC.md), [variables](architecture/VFS.md) | Reviewed against source in August 2026. |
| [config-schemas/](config-schemas/) | Reference for each declaration family | Current, except pages carrying a staleness banner. The DTOs in `src/townlet/config/` are authoritative. |
| [design/](design/) | Design specs for the differential harness and token observations | Accepted designs that the code cites. |
| [manual/](manual/) | Operator guides: training and the live viewer, TensorBoard, recording, replay, video export, POMDP support | The training guide and POMDP reference are current. The recording, replay, video and TensorBoard guides carry a banner listing what is out of date. |
| [examples/](examples/) | Substrate configuration examples | Current. |
| [oracle/](oracle/) | Rules for the frozen reference implementation, the register of accepted differences, and the frozen evidence inputs that scripts and tests compare against | Current and enforced by tests. |
| [remediation/](remediation/) | The active compiler, VFS, strata and effects remediation programme and its review records | Working records for in-flight work; `STATUS.md` there is the entry point. |
| [teachable_moments/](teachable_moments/) | Emergent behaviours and "interesting failures" kept as teaching material | Re-verified against source; read its README first. |

## Common traps

- **Never copy an observation width or action count from a document.** Ask the compiled
  artifact: `UniverseCompiler().compile(...).get_level(...).token_spec.total_dims`. Every literal
  written down so far has gone stale.
- **The reward file is `drive.yaml`**, one per level. `drive_as_code.yaml` does not exist.
- **`configs/global_actions.yaml` and `configs/templates/` do not exist.** `actions.yaml` lives at
  pack level.
- **`substrate.yaml` is called `stratum.yaml`** in real packs.
- **The five default curriculum levels are three distinct universes.** `bars.yaml`,
  `affordances.yaml` and `drive.yaml` are identical across all five, and grid size is set once
  per pack.

## Writing new documents

- Date any status claim, and say what you checked it against.
- Cite source paths rather than restating behaviour that will change.
- Do not write a dimension, hash or coverage figure you have not just measured.
- [vision.md](vision.md) condenses the product record. References to `PDR-NNNN` are numbered product decision records. They are kept in git history
  rather than the published tree.
