# PDR-0069 — the declared presentation surface is a separate `presentation.yaml`, observer-only; the engine never sees it and no compiled hash moves

Date: 2026-08-17   Status: **accepted** (owner-chosen at the 2026-08-17 `/own-product` resume,
from three fully-specified options; the recommended one)
Author: Claude (standing product owner)
Owner sign-off: **yes** (*"Separate presentation.yaml, observer-only"*)

Related: `PDR-0025` (presentation is declared, not deleted; its reversal trigger is the constraint
this decision satisfies), `PDR-0023` (money units are nominal), `PDR-0045` (a name branch is a
privileged-Python site only if it executes), `PDR-0047` (the authoring-grammar ruling the queue
executes), `PDR-0058` (trigger 2 — the register may not grow twice without an entry going
terminal — was ARMED when this was decided), `PDR-0068` (the queue runs before the merge)
Tracker: `hamlet-0dd4ac24d9` (closed, `fb791193`), `hamlet-102db4c2e0` (filed: the dead
`AffordanceGraph.vue`)
Evidence: `src/townlet/config/presentation_config.py`, `src/townlet/demo/presentation.py`,
`tests/test_townlet/unit/demo/test_presentation.py::test_the_compiler_never_reads_presentation`,
`docs/config-schemas/presentation.md`

## Context

`hamlet-0dd4ac24d9` needed a *declared* opt-in surface for how a meter or affordance is shown
(`PDR-0025`: honest default, declared opt-in, never inferred). The recon settled two facts that
decided where it could live:

- **The frontend received nothing it could render honestly from.** `state_update.agent_meters`
  was name→raw-float only; no bounds, `range_type` or presentation was ever serialised, and the
  compiled `MeterInfo` does not carry bounds (they live only in the level's `BarsV2Config`). So
  the honest default itself needed a payload change, independent of any opt-in.
- **Where the opt-in lives determines whether a compiled hash moves.** `bars_hash` and
  `environment_hash` are `sha256(model_dump_json())` of the whole DTO with no exclusions, so a
  new key on `bars.yaml` meters or `environment.yaml` variables moves them for every pack.
  `bars_hash` is checkpoint-gated (`checkpoint_utils.py:130-138`): a presentation edit would
  reject checkpoints. Either home also meant a DIV-006 in the register — and `PDR-0058`
  trigger 2 was armed at growth #1, so a sixth entry would have fired it and forced the re-tag
  question. `cues` (in `environment.yaml`, compiled, `CuesCompiler` inert) had both problems
  plus the wrong shape (threshold-triggered signals, not value formatting).

## Options

1. **Separate pack-root `presentation.yaml`, read by the live-inference server only, never by
   the compiler.** No compiled hash moves; the engine stays unaware; the curriculum packs ship
   none (absence = honest default). — *chosen*
2. **A `presentation:` key on `bars.yaml` meters.** Moves `bars_hash` for every pack; a
   presentation edit rejects checkpoints; needs DIV-006; fires `PDR-0058` trigger 2.
3. **Wire it into `cues`.** Existing-but-inert compiler, wrong shape, moves `environment_hash`;
   needs DIV-006 as well.

## The call

**Option 1.** Presentation is a property of an *observer*, not of the universe: two observers
of the same compiled artifact may legitimately show it differently, and a checkpoint's validity
cannot depend on how a bar is coloured. So the file is pack-level (it travels with the pack) but
**observer-scoped**: `townlet.demo.presentation.load_presentation` reads it after the compile,
validates it *against* the compiled universe (an entry for a meter or affordance the universe
does not declare is a loud `PresentationError`), and forwards it on `connected` next to the new
`meters` payload (declared bounds, lethality, cascade edges per meter, compiled index order).

The compiler never opens it. Proven by test: compiling `configs/test/model_config` with and
without the file leaves `environment_hash`, `bars_hash`, `affordances_hash`, `vfs_hash`,
`observation_schema_hash`, `action_schema_hash` and `transition_graph_hash` identical. The only
thing that can move is the compiler's raw-YAML *cache key* — a cache effect, not provenance,
and it is stated in the schema doc.

Consequences accepted with the call: **no register entry** (nothing the oracle certifies moved;
the 16-cell matrix re-read at `fb791193` is `20260817-002157`, 16/16 `DIVERGED_AS_REGISTERED`,
exit 0, movers unchanged), and **`PDR-0058` trigger 2 stays armed at growth #1**, unfired.

## Rationale

`PDR-0025`'s reversal trigger is the whole argument: *"the frontend may read a declared format;
the engine must stay unaware. If a presentation spec starts affecting observations, rewards or
transitions, the surface is in the wrong layer."* Options 2 and 3 put presentation inside the
artifact whose hashes gate training continuity — that is presentation affecting the engine's
provenance, which is the trigger's shape one step removed. Option 1 is the only home where the
trigger cannot fire by construction.

The schema follows the house rules: `extra="forbid"` everywhere; a declared entry declares
*all* of its fields; the three format kinds are a discriminated union (`plain` / `percent` /
`currency`), and `symbol` exists only on `currency`. Absence of the file is not a default in the
No-Defaults sense — it is the absence of a decoration; every value the honest default renders
from is a *required* declaration in `bars.yaml`.

## What this does NOT claim

- It does not build a showcase pack. No shipped pack carries a `presentation.yaml`; the
  surface is exercised by tests and by the schema doc's example. Building or distributing a
  "locked" showcase is outward-facing and stays with the owner (`PDR-0025`, roadmap Later).
- It does not close `cues`. `CuesCompiler` remains constructed-and-never-called; that inert
  surface is unchanged and still counted.
- It does not make `presentation.yaml` a compiled artifact. If a second observer (a rebuilt
  recording/replay, an export bundle) wants it, it reads the same file through the same loader
  — it does not grow a name table of its own.

## Reversal trigger

Reopen if **any** of the following:

- **The engine or compiler starts reading `presentation.yaml`**, or any presentation field is
  found to alter an observation, reward, transition, or a compiled hash — `PDR-0025`'s trigger,
  now measurable by the hash-identity test above going red.
- **A second observer re-implements presentation by name** (a `name→icon` or `name→colour`
  table anywhere under `src/townlet/` or `frontend/src/` outside `presentation.yaml`'s loader).
  The surface exists to be shared; a duplicate means it is not reachable enough.
- **A showcase author cannot express a needed presentation from the file** and the proposed fix
  is a runtime special case rather than a schema widening. Widen the schema; never the runtime.
