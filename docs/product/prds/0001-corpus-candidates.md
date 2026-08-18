# PRD-0001 — Candidate pool for the NEXT corpus revision

**This file is not the corpus.** `0001-corpus-FROZEN.md` is frozen at 15 ideas
(SHA256 `48840cc3…8de935d9`); editing it voids every subsequent trial. This file collects
candidate ideas raised after the freeze, so they survive until a future corpus revision
(the corpus's own standing note: "a durable asset, not a one-shot" — re-freeze happens
after the current N=9 completes, if the owner chooses to run a second round).

Discipline for entries here: record the idea, source, origin, and any capability recon
already done — but **no pre-registered prediction**. Predictions are written at freeze
time, before any trial of that corpus runs; writing one now would be theatre.

---

## Q — Continuous day/night forcing: sin(tick) as a world driver

**Raised:** 2026-08-18, owner, in-session during Trial O's suite run.
**Spec.** A world signal varies continuously and periodically with time — e.g.
`sin(turn_number)` / `cos(turn_number)` driving light/temperature — and agent-relevant
dynamics (recovery rates, affordance payoffs) follow it smoothly, rather than flipping on
a discrete day/night flag.
**Source.** Owner-supplied. Real-world: diurnal forcing (insolation), circadian drivers.
**Stresses.** Time as an *input to declarative expressions* (not just the boolean
`active_temporal` / `day_length` machinery); trigonometric functions in the expression
language; a global signal consumed by per-agent dynamics.
**Recon (2026-08-18, at `a3318624`):** the effect expression schema already exposes
`elapsed_ticks` and `duration_remaining` — the *time input exists*. The function
vocabulary (`src/townlet/world/expression/functions.py`) has `tanh`, `sigmoid`,
`smoothstep`, `perlin_noise`, `simplex_noise`, aggregations (`max_all`, `argmax`, …) —
but **no `sin`/`cos`/`mod`**. As of today the trig facet looks ABSENT; a periodic signal
might be approximated (noise functions are not periodic; tanh compositions are not
either), which is exactly the kind of second-surface question a trial adjudicates.
Adjacent overlap: corpus idea C (two-process sleep) declares a circadian oscillator —
this candidate isolates the *oscillator itself* as the capability, which C assumes.

## R — Heliotropism: turning toward the rewarding vector in continuous space

**Raised:** 2026-08-18, owner, same session.
**Spec.** An agent in continuous 2-D/3-D space has an orientation, and earns more by
facing a particular direction than any other — the "solar panel tracking the sun" vibe.
With Q composed in, the sun moves and the agent must track it.
**Source.** Owner-supplied. Real-world: heliotropism (sunflowers), solar-panel tracking;
games: any facing/aim mechanic.
**Stresses.** The axis nothing in the frozen corpus touches: **agent orientation as
authorable state** (the corpus's A has velocity, but nothing has *heading* decoupled from
movement); continuous substrate under reward-relevant geometry; a DAC reward computed
from an *alignment* (dot product / angle to a target vector) rather than a distance —
`approach_reward` is the nearest shipped shape and it is scalar-distance-based.
**Recon (2026-08-18, at `a3318624`):** the continuous substrate quantizes movement into
direction actions (`continuous.py` builds `cos/sin`-derived unit vectors per action) but
keeps **no persistent orientation state** on the agent — position only. Orientation would
have to be authored as agent-scope VFS variables (a heading the agent rotates via
affordance/action writes), and the alignment reward as a DAC expression over it — whether
DAC's declared vocabulary can express a dot product against a moving target is the open
question a trial would settle. Composes with Q: Q supplies the moving sun, R the tracking.

---

*Next action carried by this file: none until the current N=9 + 2 blind re-runs complete.
At a corpus re-freeze, these enter the pool, get sources/axis buckets/predictions like any
other idea, and the draw protocol runs over the widened pool.*
