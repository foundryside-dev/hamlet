# PDR-0076 — the compiled observation field says WHO FILLS IT (a typed `feature`), and the runtime, the network and the demo dispatch on that — never on the field's name; the discriminator lives on the DTO only, so no hash moves and the oracle reads the cut as invisible

Date: 2026-08-17   Status: **accepted** (owner-chosen at the 2026-08-17 `/own-product` resume as
the session's first unit — *"WS-4 unit 4: name-sync discriminator"* — from four options; the
design inside it is autonomous, within grant, the class of `PDR-0054`/`PDR-0066`/`PDR-0075`)
Author: Claude (standing product owner)
Owner sign-off: **yes**, on the unit; the placement call below is the agent's and is reported here.

Related: `PDR-0075` (named this as "the general fix" for the sibling name-syncs — a *typed
feature discriminator on the compiled field*; this executes it), `PDR-0045` (name-blind runtime),
`PDR-0047` (closed vocabularies; the compiler is held to the set an author is), `PDR-0066` (a
declaration that can reach nothing is removed, not defaulted — the same rule kept the discriminator
OFF the hash-bearing mirror), `PDR-0069` (precedent: a unit that moves no hash gets no register
entry), `PDR-0056` (hash movers are measured, not predicted), `PDR-0019` (one system at a time)
Tracker: `hamlet-39e1fe3c6d` (filed and claimed this session; closes at the commit)
Register: **no entry** — measured invisible (below)
Evidence: `src/townlet/universe/dto/observation_feature.py`,
`src/townlet/universe/dto/observation_spec.py::ObservationField.feature`,
`src/townlet/environment/observation_encoder.py::_FEATURE_PUBLISHERS`,
`src/townlet/agent/networks.py::recurrent_vision_window_side`,
`tests/test_townlet/unit/universe/test_observation_feature_discriminator.py`,
harness run `20260817-111409` (CPU + CUDA, exit 0)

## Context — the same shape, nine more times

Unit 3 (`PDR-0075`) deleted the runtime's `obs_vfs` name branch and said, of the siblings: *"the
same shape; the general fix is a typed feature discriminator on the compiled field; separate
unit."* The recon at `5e5a60e8` found the shape at every remaining site:

- `environment/observation_encoder.py` — **nine** `_sync_*_observation_to_vfs` steps, each
  `next(f for f in fields if f.name == "obs_<x>")`; the meter step **parsed the meter's name back
  out of the field's name** (`meter_name_from_observation_field`, a prefix strip); the affordance
  step matched `{"obs_affordance_at_position", "obs_affordances"}` — the second a dead alias no
  compiler has emitted since the v2.1 spec.
- `agent/networks.py:206-212` — `RecurrentSpatialQNetwork` located the window / position /
  affordance / temporal slices by literal name (the bars slice was already name-blind, `PDR-0054`).
- `demo/runner.py:442` and `demo/live_inference.py:384` — the vision window side derived from a
  field literally called `obs_local_window`, the same square-root math duplicated in both.
- `universe/compilers/observation.py::build_vfs_variables` — decided "is this an engine feature
  or an authored variable" by **set-membership of the field's name** in the authored-variable
  name sets; source widths keyed by the meter field's name.

None of these is a *domain* fact (`money`, `energy`) — they are the framework's own block names —
but the mechanism is identical: a string the compiler chose is a switch the runtime throws. Rename
the block and nine things break silently. That is what makes it the `PDR-0045` shape and not
cosmetics.

## The call

**One closed vocabulary, `townlet.universe.dto.observation_feature.ObservationFeature`, and a
required `feature` on the compiled `ObservationField` DTO** — `variable` (registry-owned: an
`environment.yaml` variable or an exposed global/agent profile variable, read by declared scope)
and the nine engine-published members `grid_encoding`, `local_window`, `position`, `velocity`,
`meter`, `affordance_at_position`, `effects`, `temporal`, `item_slots`. **A `meter` field carries
the meter's name in `feature_ref`**; no other feature may carry one (the DTO refuses both
directions). No default, anywhere.

Then every consumer dispatches on it:

- The encoder's nine steps become one loop over the compiled fields and **one table**,
  `_FEATURE_PUBLISHERS`, keyed by the vocabulary's own literals — one publisher per
  engine-published member, `variable` deliberately absent, an unknown member a loud error at the
  first observation. Each publisher receives the *field* and publishes under `field.name` — the
  name flows through as data, and nothing compares it to anything. The meter publisher maps
  `field.feature_ref` to a state column; `meter_name_from_observation_field` is **deleted**.
- `RecurrentSpatialQNetwork` locates its blocks with `get_single_field_by_feature(...)`; the
  `obs_affordances` alias is gone. `test_network_factory` now names its window
  `a_window_by_any_other_name`, its position `where_am_i` and its affordance block
  `what_is_under_me` — on purpose, so a name-branch cannot come back without failing it.
- The two demo sites call **one** helper, `recurrent_vision_window_side(observation_spec)`, that
  finds the window by feature; the square-root assumption sits beside the `Conv2d` encoder that
  makes it, and says so.
- `build_vfs_variables` skips `feature == "variable"` and sizes `feature == "meter"` sources at 1;
  the name sets and the `compiled_vfs_profiles` parameter it needed for them are gone.
- `COMPILED_SCHEMA_VERSION` 1.16 → 1.17 (a pre-cut cache would deserialize into a DTO that now
  requires `feature`; the bump makes that the "recompile the pack" error).

**Placement — the DTO only, not the hash-bearing VFS mirror.** This is the decision inside the
decision. The mirror (`vfs/schema.py::ObservationField`, the thing `observation_schema_hash`
covers) describes *how a field is exposed*: id, source variable, shape, normalization, semantic
group, curriculum activity. The feature describes *who fills the source variable each tick* —
engine plumbing. Nothing about exposure changes when the runtime learns which encoder fills a
field, so the discriminator does not belong in the ABI, is not in the field UUID payload
(`test_feature_is_not_part_of_the_field_identity` pins that two fields differing only by feature
share a UUID), and moves no provenance hash. `PDR-0066`'s rule cuts the same way from the other
side: a declaration on the mirror that no consumer of the mirror reads would be a declaration
that reaches nothing. There is also a strategic reason not to pretend otherwise: the oracle moved
forward *this morning* (`PDR-0074`) precisely because hash-only suppression had reached its
ceiling; a full-matrix hash-only DIV-007 for a plumbing change would have put 20/20 straight back
to `DIVERGED_AS_REGISTERED` and undone exit condition 2's reading for nothing.

## Measured (`PDR-0056`) — the prediction held exactly

Full 20-cell matrix, CPU + CUDA, against `oracle-2026-08-17` at `4222a917`, run
`20260817-111409`, **exit 0**: **16 `AGREE`** (five `default_curriculum` levels + three
`configs/differential/` packs × two devices, streams and every hash byte-identical) and the **four
DIV-006 cells `DIVERGED_AS_REGISTERED`, hash-only, exactly `observation_schema_hash` /
`variable_schema_hash` / `vfs_hash`** — and, checked against the pre-unit-4 run
`20260817-091351`, every one of those three hashes has the **same new-side value and the same
old-side value** as at unit 3. Unit 4 moved nothing on any side of any cell. **No register entry**
(the `PDR-0069` precedent: a unit the harness cannot see is not a divergence).

Gates at the cut, locally, all five Lint checks plus Config Validation: `ruff` ✅ `black` ✅
`mypy` ✅ `no_defaults_lint` ✅ (it caught one ternary-as-default in the meter publisher; fixed
by stating the invariant as a guard instead) `validate_compiler_cli` ✅. **Full suite at the cut: 3281 passed / 16 skipped / 0 failed**
(bare `uv run pytest`, nothing deselected; 3260 before — the 21 new tests in
`test_observation_feature_discriminator.py`).

## What this deliberately leaves

- **The recurrent encoder's square-window assumption** — `recurrent_vision_window_side` raises on
  a non-square window, which a cubic partial-vision substrate would produce
  (`configs/differential/div003_cubic_partial` exists; whether any pack pairs it with the
  recurrent architecture is unmeasured). That is a game-engine fact of the *network*, not of the
  observation, and it is a different system (`PDR-0019`). Noted, unfiled — file it if a pack hits it.
- **`vectorized_env.py:932`** names `obs_effects` in an error message string; a message, not a
  branch. Left.
- **The `obs_meter_` prefix** stays as the compiler's *naming* convention and its collision guard
  (`_assert_meter_ids_are_disjoint`) stays — a name must still be unique; what is gone is anything
  *reading* the prefix back.
- `exposed_to` defaulting to `["agent"]` when empty in the three profile validators — still
  unfiled from `PDR-0075`; still WS-4's.

## Reversal trigger

- If a future engine feature needs to be found by name after all — i.e. someone writes
  `field.name == "obs_..."` in `src/townlet/` outside the compiler's emit sites —
  `test_no_observation_consumer_carries_a_field_name_literal` fails; the answer is a new
  vocabulary member and a new publisher, not an exemption in the test.
- If a consumer of the VFS *mirror* (a checkpoint validator, the harness, an external tool)
  turns out to need the feature, the placement call was wrong: move it onto the mirror as a
  hash-moving cut with its own register entry, measured. Nothing in the tree needs it today.
- If the four DIV-006 cells had shown any hash other than the three registered, or any of the
  sixteen had left `AGREE`, this PDR would not have been written — the run would have been the
  finding.
