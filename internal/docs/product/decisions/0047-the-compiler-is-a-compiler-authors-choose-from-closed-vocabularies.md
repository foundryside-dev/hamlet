# PDR-0047 — The compiler is a compiler: authors choose from closed, pre-approved vocabularies, and the declaration is authoritative

Date: 2026-08-15   Status: **accepted** (owner-made — this is an authoring-grammar ruling, which
`PDR-0016`'s first reversal trigger reserves for the owner)
Author: Claude (standing product owner)
Owner sign-off: **yes**, stated directly when asked to choose between two forks on
`hamlet-2fe1c34ebb`: *"it should work like a regular compiler, the author defines it from a list
of pre-approved types, scalings and so on"*.
Related: `PDR-0045` (the compiler is name-blind — this supplies the positive rule that one only
negates), `PDR-0016` (do not silently add a grammar kind), `PDR-0006` (the runtime must not know
what the game is), `PDR-0007` (an unbuilt option is not debt), the No-Defaults Principle in
`CLAUDE.md`
Tracker: `hamlet-2fe1c34ebb` (the fork this resolves), `hamlet-365e996511` (`range_type` — the
sibling this ruling also governs), `hamlet-60dd3c4b53` (closed; the recon that surfaced the fork)

## Context

`PDR-0045` established what the compiler must **not** do: infer meaning from a variable's name.
It did not say what the compiler should do **instead**, and that gap was live. Recon on
`hamlet-60dd3c4b53` (2026-08-15, `1478363e`) measured the consequence: `semantic_type` had
**three disagreeing vocabularies and no authority**.

1. **Declared** — `vfs/schema.py` (`ObservationField`, `VariableDef`) and three classes in
   `config/vfs_profiles_config.py`: `Literal["bars","spatial","affordance","temporal","custom"]`,
   **`default="custom"`**.
2. **Compiler-emitted** — `compilers/observation.py` hardcodes a literal per block, including
   **`"effects"`, which is not in the declared Literal at all**. Nothing catches it: the DTO
   field is `str | None`, so the authoring schema constrains authors and does not constrain the
   compiler.
3. **Inferred from the name** — the dead adapter's `position`/`meter`, matching neither. Deleted
   at `1478363e`.

And the declared surface was never consulted: every one of L1's eleven observation fields took
its value from the hardcoded per-block literal, and `grep -rn "semantic_type" configs/` returned
**three hits in the entire config tree**.

The fork put to the owner was (a) author declares and the compiler obeys, or (b) the compiler
derives it structurally and the declared field is deleted.

## The call

**(a), and the owner's phrasing generalises it well beyond this field.**

> *"It should work like a regular compiler, the author defines it from a list of pre-approved
> types, scalings and so on."*

That is a general rule for the authoring grammar, and it is worth stating as one, because it
resolves a class of questions rather than a single field:

1. **The vocabulary is closed and pre-approved.** The author picks from a defined set. This is
   how a type system works: the language fixes the types, the author chooses among them. An
   author may not invent a member, and the set is extended deliberately — by a decision, per
   `PDR-0016` — not by accident.
2. **The declaration is authoritative.** Where an author has declared, the compiler obeys. It
   does not override, re-derive, or second-guess. Combined with `PDR-0045`: it also never infers
   from a name.
3. **The compiler may generate, but only from the same closed set.** For fields the compiler
   itself emits (grid encoding, meters, affordance blocks), the compiler assigns the value —
   which is legitimate, because it is authoring that field, not overriding an author. But it
   draws from the *same* vocabulary. A value the schema forbids an author from writing is a
   value the compiler may not emit.
4. **"And so on" is load-bearing — this is not a `semantic_type` ruling.** The owner named
   *"types, scalings"*. The scaling case is already an open defect: `range_type`
   (`normalized`/`unbounded`/`integer`) is declared per meter in every pack and read by nothing
   (`hamlet-365e996511`), which is why an unbounded resource received a bounded minmax
   normalizer. That issue is now governed by this PDR and should be resolved to the same shape.

## The owner's example, and why it widens this beyond an enum

Asked what the pre-approved list means, the owner gave the case that defines the scope:

> *"Money might be an int between 1 and 100 capped for an individual, or it might be a log float
> that models a GDP multiplied by through sin(time)."*

**Both are `money`. Neither is more correct.** The compiler must build either from declared
parameters alone, and that is the positive form of `PDR-0045` — the negative rule said *don't
read the name*; this says *read these parameters instead*, and the parameter palette has to be
rich enough that both designs are expressible without Python.

So the "list of pre-approved types" is **not a tag enum**. It is a small type system whose members
are **parameterized**: a type (int, float), a domain (bounds, cap policy, per-entity vs global), a
scaling (linear, log, clipped), and — in the second case — a *dynamic*: a value driven by an
expression over other state and over time. `semantic_type` is one narrow instance of the pattern
that happened to be measured first; it is not the subject.

**Measured against this example, 2026-08-15 (`423b24d5`), after the owner pointed at
`docs/architecture/archive/vfs-current-implementation.md` and `docs/architecture/VFS.md` — and the
result overturned my first reading, which had the palette much poorer than it is:**

- **The scalings vocabulary already exists, is complete, and is wired.** `vfs.md` §9.2 specifies
  ten normalisation kinds — `none, minmax, zscore, cyclical_sin_cos, one_hot, binary, log_scaled,
  clipped_log_scaled, rank_scaled, masked_value` — and adds *"normalisation must be part of the
  observation schema hash"*. **All ten are declarable (`NormalizationSpec.kind`, a closed
  `Literal`) and all ten are implemented** in `vfs/observation_builder.py::apply_normalization`,
  which `environment/observation_encoder.py:114` calls in production since WS-1(e). **This is
  already the ruling, built.** `vfs.md` §9.2 *is* "the list of pre-approved scalings", and the
  log-float money's scaling is available today.
  > I first wrote here that log scaling was "implemented and unwired", carrying forward an older
  > `metrics.md` entry rather than reading source. It was wrong on both halves. Following the
  > owner's two pointers is what caught it — which is this session's own lesson landing for the
  > third time: **check the claim against the tree, including the claims in your own workspace.**
- **The expression grammar is strong and wired.** `world/expression/functions.py` registers ~55
  functions including `phase_sin` / `phase_cos`, `sigmoid`, `tanh`, `smoothstep`, `clamp`,
  `normalize`, `threshold`, `where`, `normal_dist`, `perlin_noise`; `effects/compiler.py` parses
  and type-checks them. *"Multiplied through sin(time)"* is not a missing function.
- **So the gaps are narrower and more specific than "the palette is too small".** Three, and each
  is a *binding* or *selection* gap rather than a missing capability:
  1. **Selection.** `range_type` (`normalized` / `unbounded` / `integer`) is declared per meter in
     every pack and read by **nothing** (`hamlet-365e996511`), so nothing maps *"this variable is
     unbounded"* onto the log family; an unbounded resource got a bounded minmax normalizer. The
     author can still name the kind explicitly — the automatic mapping is what is absent.
  2. **No integer type.** Bars are float tensors. "An int between 1 and 100" is expressible as a
     *range* and not as a *type*.
  3. **No expression slot on a bar.** In `bars.yaml` a meter declares `initial`,
     `depletion.{passive,move,interact}`, `recovery.natural`, `bounds.{…}` — and nothing else.
     A value driven by a declared expression over time has no authoring surface at the bar level,
     even though the functions exist and the effects path compiles expressions. Grammar present,
     binding absent — the inert-surface shape again.
- **`vfs-current-implementation.md` states the motive independently, and from the research side:**
  it names *"agents can learn labels such as `hunger` or `shop` instead of learning the underlying
  causal structure"* as one of three failure modes VFS exists to prevent, and carries a
  generalisation harness (`townlet.vfs.generalisation`) plus the `set_encoder` path *"for
  experiments where names and labels change but causal structure stays comparable"*. **Name-blindness
  is not only a framework-hygiene rule — it is a stated experimental requirement.** `PDR-0045`
  and this PDR are the compiler-side obligation of a property the research design already assumes.

**This yields a falsifiable acceptance test for the work, and it is better than any count:**
*author both of the owner's money designs as config, in a pack, with zero lines changed under
`src/townlet/`.* That is Trial 002, a direct sibling of Trial 001 and a second reading on the
north-star "Zero-Python authoring rate" — and unlike a subsystem count it fails loudly and
specifically. The measurement above predicts the outcome: **money A** (int, 1–100, capped) fails
on the missing integer type and passes on everything else; **money B** (log float over a
time-varying aggregate) has its scaling and its `phase_sin` available and fails on the absent
bar-level expression binding. Both failures are bindings, not capabilities, which is the cheapest
kind of gap this project has found in months.

**Run the trial before building.** It costs a pack and an afternoon, it converts three inferred
gaps into three measured ones, and — on this session's evidence — roughly one inferred gap in
three does not survive contact with the tree.

> ⚠️ **TRIAL 002 RAN, 2026-08-15. The predicted outcomes above are corrected by `PDR-0051`** —
> by pointer, not overwrite; the original text stands so the error is legible. **The ruling
> itself is owner-made, was tested by the trial, and survives it** — every failure found was a
> binding or selection gap, never a missing capability, and the first reversal trigger did not
> fire. What was wrong was the prediction:
>
> - **Money B's predicted failure is falsified.** *"Fails on the absent bar-level expression
>   binding"* — the binding exists, through `effects.yaml` (`on_tick: modify bar.money`) spawned
>   from an affordance `interactions.on_start`. Money traces `1000·(2 + sin(2πk/24))` exactly for
>   27 ticks, in config, zero Python. The most doubted half of the owner's example is the half
>   that works today.
> - **Money A's predicted failure is right about the symptom and understated.** `range_type` does
>   not merely fail to select a scaling — switching *every* meter `normalized` → `integer` moves
>   **none of the five provenance hashes**, and the runtime holds `33.333` in a bar declared
>   `integer`.
> - **"The scalings vocabulary already exists, is complete, and is wired" is true of the runtime
>   and false of the bar authoring path.** All ten kinds are implemented — but
>   `_meter_normalization` emits **one** `minmax` spec for the *entire meter block*, so eight of
>   the ten are unreachable for bars whatever a pack declares. The gap is bigger and more
>   structural than "no log for money", and it is not a `money` problem at all.
>
> Packs: `configs/trial002_money_int_capped/`, `configs/trial002_money_log_gdp/`.

## Consequences

**1. `default="custom"` goes.** A behavioural parameter that feeds a provenance hash and drives
the group slices is exactly what the No-Defaults Principle forbids defaulting. Under rule 2 a
default is worse than untidy: it manufactures a declaration the author never made, and the
compiler then treats it as authoritative. Note the cost honestly — it is a breaking change for
every pack that omits the field, which today is nearly all of them. That is the intended
direction (`CLAUDE.md`: old configs should fail loudly), not an obstacle.

**2. `"effects"` must be admitted or removed.** It is currently emitted by the compiler and
forbidden to authors. Under rule 3 that state is not permissible either way round. Admitting it
is a vocabulary extension and needs a decision; removing it means mapping those fields onto an
existing member.

**3. This is hash-moving, so it takes the `PDR-0037` order.** `semantic_type` is concatenated
into `compute_observation_field_uuid`'s SHA256 payload, so changing what it holds moves
observation field UUIDs and the observation schema hash for every pack. Register entry first,
verified against the oracle at the tag, **then** the cut — not a drive-by edit. The first
knockdown (`PDR-0041`) is the worked example.

**4. It is a knockdown unit on `PDR-0019`'s criterion.** *Where does the runtime still know what
the game is?* — a compiler that assigns semantic classes by hardcoded per-block literals while
ignoring the author's declaration is the framework/instance boundary breached inside the
compiler. This is a candidate for the next unit, not a side fix.

**5. The counter-example to build toward already exists in-tree.** `config/drive_as_code.py:500`
declares `money_bar: str` **required, no default**, resolved at `dac_engine.py:721`: the engine
holds the *role*, the author binds the *referent*. That is rules 1–2 working correctly today.

## Reversal trigger

- **Reverse if the closed vocabulary cannot express a real authored universe.** If an author's
  legitimate variable has no honest member to choose, the ruling has produced the
  `semantic_type=None` problem again under a new name. The fix would be extending the set (a
  decision), but two such cases in a row means the closed-vocabulary model is wrong for this
  field and it should be derived structurally after all — fork (b), revisited.
- **Reverse if making the field required blocks more than it reveals.** If the breaking change
  produces a wave of mechanical pack edits that carry no authoring intent — every pack writing
  the same value because there is only one sensible choice per field kind — then the field is
  structural, not authored, and (b) was right.
- **Re-open the scope** if "types, scalings and so on" turns out to cover surfaces where a closed
  vocabulary is genuinely inappropriate (a continuous parameter, say). The rule as written is
  about *enumerated* choices; it should not be stretched into a claim about every declared value.
