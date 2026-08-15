# PDR-0054 — the meter type declaration and its normalizer are one cut, and this is the plan

Date: 2026-08-15   Status: **accepted** (design ruling within grant; the owner approved items 1
and 2 and asked explicitly for item 3 to be *planned* so it is not lost in churn)
Author: Claude (standing product owner)
Owner sign-off: **yes**, on the work order:

> *"1. yes approved, 2 yes 3, I don't want to lose this in the churn so make sure we have a
> concrete plan to fix the gap"*

Implements: `PDR-0053` part 1 (the (a) ruling), `PDR-0052` (underspecification is a compile
error, and the wiring comes first)
Related: `PDR-0045` (name-blind), `PDR-0047` (closed vocabularies), `PDR-0016` (bounds and
normalization are one feature), `PDR-0037` (register the divergence before the cut), `PDR-0051`
(Trial 002), `PDR-0049` (a defect counts only if it executes)
Tracker: `hamlet-fba56feca5` (item 1), `hamlet-3d3039f340` (items 2+3), `hamlet-365e996511`
(subsumed), `hamlet-1dba1910c0` (closed, `bf0f2fe4`)

---

## Finding first: items 2 and 3 are one cut, not two

The owner approved item 2 (`range_type` becomes the complete type declaration) and asked for a
plan for item 3 (8 of 10 normalisation kinds unreachable). **They cannot land separately.**

`range_type` is today accepted, hashed into `environment_hash`, and drives nothing
(`PDR-0051` measured it). Item 2 alone would let an author write a meter type naming
`log_scaled` while `_meter_normalization` keeps returning one `minmax` spec for the whole block.
That is *precisely* taxonomy shape #5 from `PDR-0053` — **silent discard: declaration accepted
then dropped** — and shape #6 would survive untouched. We would author, deliberately, the exact
defect `hamlet-3d3039f340` exists to remove.

**So the plan below covers both as a single cut.** Item 1 (`hamlet-fba56feca5`) is genuinely
separable and lands first, because it touches a different surface and supplies a primitive the
cut wants.

This is flagged, not gated: proceeding on the owner's approval of item 2, since item 3's
implementation is the only honest way to deliver item 2. If the owner wants item 3 held, item 2
must be held with it.

---

## Ruling 1 — `obs_meters` splits into one observation field per meter

**The root defect is not the normalizer. It is that `obs_meters` is N variables jammed into one
field.** `compilers/observation.py` emits a single `ObservationField(name="obs_meters",
dims=meter_count)` and `_meter_normalization` gives it one `NormalizationSpec`. Per-meter
*parameters* already work (`min`/`max` are lists); per-meter *kind* cannot, by construction.

Two candidate fixes were weighed:

| | approach | verdict |
|---|---|---|
| **A** | split into one field per meter, each with its own spec | **chosen** |
| **B** | keep one field, give it a *list* of specs applied column-wise | rejected |

**A is chosen on three pieces of in-tree evidence, not on taste:**

1. **The bars block survives for free.** `build_activity` groups by
   `group_name = field.semantic_type or "custom"` (`compilers/observation.py:324`) and
   `ObservationActivity.group_slices` is already `{"bars": slice(0, 8)}`. N contiguous fields
   each carrying `semantic_type="bars"` produce the *same* group slice. Nothing downstream that
   wants "the bars block" loses it.
2. **It deletes a name-branch instead of preserving one.** `agent/networks.py:191` reads
   `elif field.name == "obs_meters": self._meters_slice = ...` — the literal-name shape
   `PDR-0045` names as the hardest defect to spot. Under A it becomes
   `observation_activity.group_slices["bars"]`, which is a *declared* property. Under B the
   branch stays and gets a composite spec bolted beside it.
3. **Only A can express the width-changing kinds honestly.** `cyclical_sin_cos` (2×) and
   `one_hot` (→ `categories`) change a value's observed width. A field's `dims` is the unit the
   encoder checks against (`observation_encoder.py:115`). Per-meter fields each declare their
   own `dims`; a single block field would need a width that is the sum of per-column widths with
   no per-column accounting anywhere.

**Reversal trigger for ruling 1:** reverse to B if splitting is measured to change the compiled
observation *ordering* in a way `group_slices` cannot re-assemble — i.e. if any consumer needs
the meter block to be a single `ObservationField` object rather than a contiguous span.

---

## Ruling 2 — `range_type` becomes a discriminated union tagged by the VFS kind name

Per `PDR-0053`(a): a closed, **parameterized** vocabulary where each member fully determines its
own required parameters, and omitting them is a compile error.

**The tag is the VFS kind name itself.** No translation layer, because a translation layer is
where a member learns to lie (`PDR-0047` rule 1; `hamlet-1dba1910c0` was exactly that). Members
and their parameter sources:

| `range_type.kind` | parameters | source |
|---|---|---|
| `minmax` | `min`, `max` | **`bars.yaml` bounds** (`PDR-0016`: the declaration that ceilings the runtime also scales the observation) |
| `log_scaled` | `min`, `max` | `bars.yaml` bounds |
| `clipped_log_scaled` | `min`, `max` | `bars.yaml` bounds |
| `zscore` | `mean`, `std` | declared inline, **required** |
| `cyclical_sin_cos` | `period` | declared inline, **required** |
| `one_hot` | `categories` | declared inline, **required** |
| `binary` | `threshold` | declared inline, **required** |
| `masked_value` | `mask_value`, `fill_value` | declared inline, **required** |
| `rank_scaled` | *(none)* | — |
| `none` | *(none)* | — |

> ⚠️ **Corrected during W1, same day, by pointer — the table above says TEN and it is now
> NINE.** Implementing ruling 3 exposed that adding `clip` as a parameter while leaving
> `clipped_log_scaled` as a *member* would author `PDR-0053` taxonomy shape #3 — two members,
> one behaviour — by hand, in the change whose purpose is removing that shape. So
> `clipped_log_scaled` was deleted: `log_scaled` + `clip: true` is exactly what it did.
> `docs/architecture/vfs.md` §9.2 had carried the tell all along, passing `clip: true` to a
> kind whose name already implied it. Drop the `clipped_log_scaled` row; `log_scaled` keeps
> `min`/`max` from bars bounds and gains a required `clip`. The count is the only thing that
> changes — every kind remains reachable, which is the ruling's actual claim.

Ten members, ten kinds, nothing unreachable. `none` is admitted here **only** because a meter's
value may legitimately already be in observation units; it is an explicit author choice, not the
absence of one, which is what `PDR-0052` forbids.

Two stated assumptions rather than another round of deliberation:

- **The field keeps the name `range_type`.** It is the owner's word and `PDR-0053` uses it. The
  semantics shift — old members (`normalized`/`unbounded`/`integer`) described a *value range*,
  new ones describe an *encoding*. Recorded here so the shift is visible; rename is cheap later
  and is not worth a round now.
- **The three old members are deleted, not mapped.** Zero-backcompat. Every meter in every pack
  is rewritten explicitly. `unbounded` is *not* silently translated to `log_scaled` — that
  translation is a hidden default and would re-create shape #4.

**Reversal trigger for ruling 2:** reverse to `PDR-0052`'s option (b) — a separate required
`normalization` field beside `range_type` — if a meter turns out to need two independent type
facts that force a member per combination (`PDR-0053`'s own trigger, restated because this is
where it would fire).

---

## Ruling 3 — item 1 lands first, as a parameter, not a member

`hamlet-fba56feca5` (approved): there is no plain clamping normalizer. Implement as
**`clip: bool` on the `minmax` kind**, not a new `clipped_minmax` member — the PDR-0053
precedent of parameterized members over member proliferation, and the recommendation already
recorded on the issue.

It lands first because it touches a different surface (`NormalizationConfig` /
`environment.yaml` `variables[]`) and because ruling 2's `minmax` member will want the
parameter. `NormalizationSpec` already carries `None`-defaulted optional parameters per kind, so
this pattern is in-tree precedent and No-Defaults is not re-litigated for it: the *kind* is
required, its parameters are required-for-that-kind.

---

## The named work — including the two width couplings that were nearly missed

Splitting the meter block breaks an assumption that is currently invisible because no
width-changing kind is reachable: **observed bars width == meter count**. It is load-bearing in
three places, and each is real work, not "handling":

1. **`population/vectorized.py:385`** passes `num_meters=env.meter_count` into the network
   factory, and `agent/networks.py:143` builds `nn.Linear(num_meters, 32)` from it. That is the
   *observation* encoder taking its input width from a *state* count. It must take the compiled
   bars-block width (`group_slices["bars"]`).
2. **`agent/networks.py:235`** falls back to `obs.new_zeros((batch_size, self.num_meters))` —
   same conflation, same fix.
3. **`environment/observation_encoder.py:241`** asserts
   `env.meters.shape == (num_agents, meter_field.dims)`. `env.meters`
   (`vectorized_env.py:335`) is the state tensor and **stays one column per meter** — correct.
   What must change is that the per-meter *source* VFS variable is 1-wide while the per-meter
   *field* may be wider. `build_vfs_variables` currently derives the source `VariableDef` width
   from `field.dims`, conflating pre- and post-normalization width. Split them.

Work items, in order:

- **W1** `NormalizationSpec` gains `clip: bool` on `minmax`; `apply_normalization` clamps when
  set; `NormalizationConfig.method` exposes it. Test: declaring the clamp on `[0,1]` and feeding
  `[-5, 7]` returns `[0, 1]` — the test `hamlet-1dba1910c0` could not write.
- **W2** `MeterConfig.range_type` becomes the discriminated union above, `extra="forbid"` on
  every member, missing parameters raise at parse time with the meter named.
- **W3** `compilers/observation.py` emits one `ObservationField` per meter
  (`semantic_type="bars"`, contiguous, `dims` = the kind's output width), each with its own
  `NormalizationSpec` built from `range_type` + `bars.yaml` bounds. `_meter_normalization` is
  deleted, not adapted.
- **W4** `build_vfs_variables` gives each meter a 1-wide source variable; field `dims` carries
  the post-normalization width.
- **W5** `observation_encoder.py::_sync_meter_observation_to_vfs` writes per-meter sources; the
  `obs_meters` literal-name lookups go.
- **W6** `networks.py` / `network_factory.py` / `population/vectorized.py` take the bars width
  from `group_slices["bars"]`; the `field.name == "obs_meters"` branch is deleted.
- **W7** Every meter in every shipped pack declares its `range_type` explicitly (8 meters ×
  `default_curriculum`, plus every other pack — `configs/L5_multi_agent`, `configs/test/*`,
  `configs/aspatial_test`, `configs/trial002_money_log_gdp`).
- **W8** `hamlet-365e996511` closes as subsumed: `range_type` is no longer inert by construction.

---

## Oracle sequencing — one divergence entry, not three

All of W1–W7 move `observation_schema_hash`, and W2/W7 change the `environment.yaml` schema
itself. `PDR-0037` order applies: **register before the cut.**

**One entry in `docs/oracle/known-divergences.md` covering the whole normalization-vocabulary
programme**, because the frozen fixture sits at the old schema for the entire duration
regardless — three entries would describe three moments of one continuous divergence.

This is the first real use of the machinery built at `49bdf28e`, and the procedure is the one
`oracle_fixtures/README.md` already states: *"If it **is** a schema change, leave the fixture at
the old schema, set `pack_divergence` on the affected cells, and register the entry."* So:

- `oracle_fixtures/*/environment.yaml` stays at the **old** `range_type` schema, deliberately.
- Every matrix cell reading a pack whose `environment.yaml` changed gets `Cell.pack_divergence`
  set — under `matrix.py`'s hardcoded pack list that is all `default_curriculum` cells and any
  `div003_*` fixture pack whose environment file moves.
- The declared *input* delta does not bless the resulting *output* delta. If comparison then
  reports an observation-schema difference, that is a second decision and gets its own
  `known-divergences.md` entry.

---

## Acceptance — the ticket's two legs, unchanged

From `hamlet-3d3039f340`, both required:

1. `configs/trial002_money_log_gdp` compiles with **zero `src/townlet/` diff**, and
2. the compiled bars spec reports `log_scaled` for `money`, and the observed value at
   `money=1000` is **0.5**, not `0.000999`.

Leg 1 alone is how this state arose; a schema change that admits `log_scaled` without changing
what the compiler emits passes leg 1 and fails leg 2. Plus:

3. A pack declaring a width-changing kind on a meter (`cyclical_sin_cos`) compiles, and
   `observation_spec.total_dims` grows by exactly one — proving the width couplings above are
   genuinely broken and not merely bypassed.
4. `grep -rn 'obs_meters' src/townlet/` returns zero hits.
5. Oracle matrix exits 0 with the divergence declared; `validate_compiler_cli.py` green across
   every pack.

---

## Consequences

1. **Item 2 cannot be delivered without item 3.** Stated to the owner rather than resolved
   silently.
2. **`hamlet-365e996511` is closed by this work**, not scheduled beside it.
3. **The bars block stops being special.** After W6 the engine no longer knows a variable named
   `obs_meters` exists; it knows there is a `bars` semantic group, which is declared.
4. **The ten kinds become an authoring surface, not an implementation detail.** `vfs.md` §9.2
   stops being a list of things the runtime can do and no pack can ask for.

## Reversal triggers

- **Ruling 1** — reverse to the composite-spec approach if any consumer needs the meter block as
  one `ObservationField` object rather than a contiguous span.
- **Ruling 2** — reverse to `PDR-0052` option (b) on combinatorial blow-up of members.
- **Ruling 3** — reverse `clip: bool` to a `clipped_minmax` member if a second boolean parameter
  appears on `minmax`, because at two flags the member is a union in disguise.
- **The whole plan** — if W3 cannot delete `_meter_normalization` outright and instead grows a
  second path beside it, stop: that is the dual-path shape this repo forbids, and it means the
  split was not the root fix.
