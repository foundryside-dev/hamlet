# PDR-0051 — Trial 002 ran: the owner's two money designs are 3-for-4 authorable, the predicted failure was falsified, and the real gap is that a meter cannot carry its own normalizer

Date: 2026-08-15   Status: **accepted** (within grant — records a measurement and re-scopes two
open issues; no `src/townlet/` code changed, which is the trial's own acceptance criterion)
Author: Claude (standing product owner)
Executes: `PDR-0047`'s falsifiable acceptance test — *"author both of the owner's money designs
as config, in a pack, with zero lines changed under `src/townlet/`"*
Corrects: `PDR-0047`'s predicted outcomes — **by pointer, not overwrite** (the `PDR-0020`
practice). The ruling itself is owner-made and untouched.
Related: `PDR-0045` (the compiler is name-blind), `PDR-0049` (a defect counts only if it
executes — this PDR is its mirror), `PDR-0016` (bounds + normalization are one feature),
`PDR-0037` (register before the cut), `PDR-0019` (the knockdown criterion)
Tracker: `hamlet-365e996511` (`range_type` inert — re-scoped and now measured),
`hamlet-2fe1c34ebb` (`semantic_type` authority — unchanged), plus two issues filed by this PDR
Artifacts: `configs/trial002_money_int_capped/`, `configs/trial002_money_log_gdp/` (each carries
a README with the full measurement and a reproduction command)

## Context

`PDR-0047` recorded the owner's authoring-grammar ruling — *"it should work like a regular
compiler, the author defines it from a list of pre-approved types, scalings and so on"* — and,
asked what that meant concretely, the owner supplied the case that set the scope:

> *"Money might be an int between 1 and 100 capped for an individual, or it might be a log float
> that models a GDP multiplied by through sin(time)."*

`PDR-0047` turned that into a falsifiable test rather than a design, and predicted the outcome so
the test could disprove it: **money A** fails on the missing integer type; **money B** fails on
the absent bar-level expression binding. It also said, in terms: *"Run the trial before
building… roughly one inferred gap in three does not survive contact with the tree."*

## What was done

Two packs forked from `configs/simple` at `07b26ed5`, each differing from that pack **only in
`money`**, so every observed difference is attributable to the money declaration. Both designs
were then pushed until they either worked or failed with a specific error, and each claim was
checked in **two legs**:

1. Does it compile with zero `src/townlet/` diff?
2. **Is the declared parameter observable in the compiled artifact or the encoded observation?**

Leg 2 is the trial. This codebase's dominant failure shape is declared-accepted-inert, so leg 1
alone would have reported a false pass on the single most important finding below.

`git diff --stat src/townlet/` is empty. The acceptance criterion was met literally.

## Result — 3 of 4 halves are authorable, and the predicted failure was the wrong one

| design | half | verdict |
|---|---|---|
| A — int 1..100, capped | domain (bounds, cap) | ✅ **authorable** — bounds reach the normalizer; writing `500.0`/`-20.0` clamps to `100.0`/`1.0` |
| A — int 1..100, capped | type (integer) | ❌ **declared, accepted, inert** |
| B — log float, GDP × sin(time) | dynamic (the sin(time) process) | ✅ **authorable** — matches the closed form exactly for 27 ticks |
| B — log float, GDP × sin(time) | scaling (log observation) | ❌ **declared, accepted, silently discarded** |

**1. `PDR-0047`'s money-B prediction is falsified.** It predicted failure on "the absent
bar-level expression binding." The binding exists — not on the bar, but through `effects.yaml`
(`on_tick: modify bar.money = 1000.0 * (2.0 + phase_sin(elapsed_ticks, 24.0))`) spawned from an
affordance `interactions.on_start`. Money traces `1000·(2 + sin(2πk/24))` for 27 consecutive
ticks, exact at every tick. **The most doubted half of the owner's example is the half that
works today, in config, with no Python.**

Two real constraints surfaced on the way, both via *honest, listing* compiler errors — the good
failure mode, worth naming as such: (i) there is **no world clock** in the effect expression
scope (`tick` is not a variable; `elapsed_ticks` is effect-lifetime-local), and (ii) there is
**no episode-start hook** — `EffectManager.spawn_effect` has exactly one production caller,
inside effect execution itself, so a world process must be bootstrapped by an agent walking onto
a tile.

**2. `range_type` is not merely unread — it is provably inert.** Switching *every* meter from
`normalized` to `integer` and changing nothing else leaves **all five provenance hashes
byte-identical** and `total_dims` unchanged. The literal `integer` survives in exactly one place
in the compiled universe — the echoed raw config — and in no derived artifact. At runtime
`vectorized_env.py:335` allocates `self.meters` as `torch.float32` unconditionally, and a bar
declared `integer` holds `33.33300018310547` without complaint. The DTO says so itself
(`environment_config.py:27`: *"Metadata only for UI; does not affect obs_dim."*).

**3. The real scaling gap is structural and larger than "no log for money."** All ten `vfs.md`
§9.2 normalisation kinds are implemented and reachable at runtime — `PDR-0047` was right about
that. But `universe/compilers/observation.py::_meter_normalization` returns **one**
`NormalizationSpec(kind="minmax", …)` for the *entire meter block*, chosen by the compiler from
declared bounds. So **no meter can carry a per-meter normalizer, and eight of the ten kinds are
unreachable for bars no matter what any pack declares.** A meter cannot declare normalization
directly either — `environment.yaml` `meters[]` is `extra="forbid"` and rejects the key.
Declaring it on the VFS side validates and compiles green, and is then silently discarded.

The consequence is not cosmetic. With `bounds [1, 1e6]`, the observed money value is linear to
six decimal places, so the whole operating range 1 → 100,000 is crushed into `[0, 0.0999]` —
**the agent is effectively blind to money**, which is the exact failure log scaling exists to
prevent. `PDR-0016` said bounds and normalization are one feature; this is that coupling turning
into a defect once the bounds get wide.

**4. A bug found by verifying rather than by the work** (the `PDR-0049` pattern, second
occurrence): **effects survive `env.reset()`.** Money correctly resets to its declared `initial`,
but the effect keeps ticking across the episode boundary with `elapsed_ticks` continuing — one
WAIT after a reset yields tick 1 of the *previous* episode's cycle. Episode state leaks forward,
which corrupts training independently of anything in this trial.

## Rationale — what the trial bought, and what it would have cost not to run it

The `PDR-0047` estimate was "roughly one inferred gap in three does not survive contact with the
tree." The realised rate was **one in two**: of the two predicted failures, one was wrong about
the mechanism and the other was right about the symptom but wrong about the scope — "no log
scaling for money" is really "no per-meter normalizer for any meter."

Had the work been built to the prediction, it would have added a bar-level expression slot that
duplicates a working effects path, and a money-specific log option that leaves the other seven
kinds unreachable. **Both would have been shipped, both would have been defensible, and neither
would have been the fix.** That is the concrete return on running a trial before building, and it
is the reason to keep doing it rather than a nice thing that happened once.

The trial also gives `PDR-0047`'s ruling its first real test and the ruling **survives it**: in
every one of the four halves, the failure is a *binding or selection* gap, never a missing
capability and never a case where a closed vocabulary was the wrong model. The first reversal
trigger ("the closed vocabulary cannot express a real authored universe") did not fire.

## Consequences

**1. `hamlet-365e996511` is re-scoped and upgraded from inferred to measured.** It was
"`range_type: unbounded` is inert." It is now: *`range_type` moves nothing at all — five hashes,
zero — and the meter block admits exactly one compiler-chosen normalizer.* The selection fix
(map `unbounded` → a log family) is downstream of the structural one; per-meter normalizer
support has to exist before anything can select into it.

**2. Two issues filed by this PDR**, both measured, both with reproductions in the pack READMEs:
per-meter normalization, and effects surviving episode reset.

**3. Reading `PDR-0047`'s "the scalings vocabulary is already built" claim correctly.** It is
true of the *runtime* and false of the *bar authoring path*. Both halves matter and the PDR only
recorded the first; this is the distinction leg 2 exists to force.

**4. The knockdown target sharpens (`PDR-0019`).** *Where does the runtime still know what the
game is?* — a compiler that picks one normalizer for every meter, ignoring both the author's
declaration and the declared range kind, is the framework/instance boundary breached inside the
compiler, the same shape `PDR-0047` found in `semantic_type`. These are one unit, not two.

**5. Hash-moving work ahead takes the `PDR-0037` order.** Per-meter normalization changes
`obs_meters`'s spec and therefore the observation schema hash for every pack: register entry
first, verified against the oracle at the tag, then the cut.

**6. The two packs stay in-tree** as the regression fixture. They are ~10 lines of delta each
against `configs/simple` and they fail loudly and specifically the moment either gap closes.

## Reversal trigger

- **Re-run the trial** if either gap is closed, and require both legs again. A fix that makes
  `range_type: integer` accepted but still float-backed, or that admits `log_scaled` in the
  schema without changing what `obs_meters` emits, passes leg 1 and fails leg 2 — which is
  exactly how this state arose.
- **Reverse the "one unit" framing in consequence 4** if per-meter normalization turns out to
  need a different mechanism from `semantic_type`'s authority fix. Bundling is a convenience,
  not a finding.
- **Reverse consequence 6** if the trial packs start being maintained as content rather than
  used as a fixture — if they acquire meters, affordances or levels beyond the money delta, they
  have stopped being a measurement and should be deleted.
- **Escalate to the owner rather than deciding** if closing the meter-normalizer gap requires
  choosing which of the ten kinds a meter gets by default. Under `PDR-0047` rule 2 and the
  No-Defaults Principle there should be no default — but "every pack must now declare a
  normalizer per meter" is a breaking change to every shipped pack, and `PDR-0047`'s second
  reversal trigger reserves exactly that judgement.
