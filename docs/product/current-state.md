# Current State — HAMLET / Townlet        Checkpoint: 2026-08-12 · third checkpoint, amended

## The bet right now

**Strangler rewrite behind the compiled-universe contract** (`PDR-0006`) — freeze the current
system as an oracle, then knock down and rebuild one design-space unit at a time against it.
Guarded by **Provenance integrity**, which was BREACHED in three places and is now **1 of 3
closed**.

The owner's framing of what the strangler is *for*, recorded 2026-08-11: *"the original 'game
engine' needs to be strangled out by the engine engine"* — VFS and the dynamic engine parts are
the guiding star, not `health = 0..100`. That converts the strangler from an ordering question
into a **selection criterion**: strangle wherever the runtime still knows what the game is.

## In flight

Recovery milestone **`hamlet-1ade187dcc`**, work streams WS-0…WS-7.

- **WS-1** `hamlet-67ffbd282a` (P0, claimed, `fixing`) — **4 of 10 units landed, tree green at
  every commit.** Grew 7 → 10 units across two reviews (`PDR-0015`, `PDR-0016`).
  Order: ~~gates(1)~~ → ~~a(2)~~ → ~~d(3)~~ → **3a ← next** → new1(4) → new2(5) → b(6) → c(7)
  → close(8), plus sibling `3b` (`hamlet-88acec4bb5`) after 3a and before the freeze.
- **WS-7** `hamlet-e3af412673` (P0) — the strangler's enabling stream. Blocked by WS-1.
- **WS-6** `hamlet-5e39fcccb0`, **WS-0** `hamlet-8eeaba1461` — ready, untouched.
- **WS-4** gained `hamlet-f46e2b381a` (`clamp_and_validate` declared-but-empty) and
  `hamlet-fa6bb6da4a` (token observations, blocked by `hamlet-0d0115383e`).

## Open questions / blocked-on-owner

- ⚠️ **`vision.md`'s FLAGSHIP DEMONSTRATOR IS NOT IMPLEMENTED — does that change the vision, or
  the packs?** `vision.md:94` calls "Low Energy Delirium" *"the flagship demonstrator of the
  substrate: the proof that the thing works."* Measured 2026-08-12 (`PDR-0018`): `L0_0` and
  `L0_5` `drive.yaml` are **byte-identical**, both `constant_base_with_shaped_bonus`, and **no
  shipped level declares a `multiplicative` extrinsic** — the contrast the lesson needs has never
  existed. `vision.md` is ENDORSED and was **not** touched. This is the owner's call.
- ⚠️ **WHEN DO WE STOP ADDING TO WS-1 AND FREEZE?** WS-1 has grown 7 → 10 units. Each addition
  was justified individually and none was optional under `PDR-0012`. `PDR-0014`'s reversal
  trigger 2 (*"the bounds wiring materially delays the oracle freeze"*) is **approaching, not
  definitively tripped**. `PDR-0018` removes the largest reason to go slowly — there is no
  calibrated behaviour at risk — so the argument now leans toward freezing sooner.
- **Design fork inside `PDR-0009`** — per-level `architecture` override, or make `brain.yaml`
  level-overridable the way `training.yaml` is? Now has **three** consumers (`PDR-0017`,
  `PDR-0018`). A level cannot currently vary its grid *or* its brain, which bounds what any
  curriculum can express. Decide before implementing.
- **README push** remains the owner's call; drafting and committing locally is endorsed.
- **Open, not blocking** — the five shipped levels are **three universes**, a thin coverage set
  for WS-3's differential harness. An input to WS-3 scoping; does **not** reopen `PDR-0006`.

Closed: the poisoned-cache hazard (WS-1(a) landed); CUDA blocked (was an unused dependency);
*"what is the real test coverage?"* (**81%**, `PDR-0010`); *"who re-authors the packs?"* —
**premise was false** (`PDR-0018`), the packs were never tuned, so there is nothing to re-author;
authoring one for the first time is filed as `hamlet-e979f2ba37` (WS-4, downstream of the freeze).

## What this checkpoint did

- **Landed 4 of 10 WS-1 units** — gates (`c2f61beb`), cache identity (`22b7616d` + `cf122ff1`),
  declared costs gate (`30c433e3`) — plus an unplanned dependency remediation (`e082afd5`).
  Full suite **2939 passed, 0 failed**; all four gates green.
- **Recorded `PDR-0015`, `PDR-0016`, `PDR-0017`.** 0015: `PDR-0014`'s bounds site list was an
  undercount and wiring the four sites it named would have changed *nothing*. 0016: bounds and
  the VFS normalization surface are one feature and land together (owner-approved). 0017: the
  token-observation direction is recorded, not started.
- **Moved two guardrails for the first time since May** — Gates green **1 of 4 → 4 of 4**, and
  Provenance integrity **1 of 3 breaches closed**. Also first movement on Config-surface
  coverage, and the first Pre-release hygiene recount since 2026-05-16.
- **Used adversarial verification twice, and it paid both times** — it caught a real miss in my
  own task 2 fix (`metadata_for_level`, found independently by two agents), and recon before
  task 3a overturned **four** of its spec's claims including three wrong red-baseline literals.

## Next session, start here

**Implement task 3a** — `bars.*.bounds` **and** the VFS observation normalization, together
(`PDR-0016`). Read plan **§0.2 first** — it overrides §0.1 and §0, and its corrections are
load-bearing:

1. The site that actually binds is `vfs/vtc.py:2384` (passive depletion, `composition="overwrite"`,
   every tick, every meter). Wiring only the four clamps `PDR-0014` named changes **nothing**.
2. **Three of four "red today" literals in the spec are wrong** — real reds are `0.990000`, not
   `1.000000`. An implementer writing `1.0` will see `0.99` and "fix" a working harness.
3. `find configs -name '*.msgpack' -delete` before **every** measurement, red and green —
   provenance uses `git rev-parse HEAD` and ignores dirty state.
4. No second `COMPILED_SCHEMA_VERSION` bump (D1 holds; task 2 owns the only one).

Then the normalization half needs **its own adversarial pass** — it touches every observation,
a wider blast radius than the bounds half.

**A recurring lesson, now seen three times — carry it into tasks 4 and 5, which both add fields
to exactly this kind of structure:** grep finds *the shape of a call*, not the set of places a
value is produced. `grep torch.clamp(` missed compile-time tuple literals. `grep
UniverseMetadata(` missed a `dataclasses.replace()`. A grep against a *documented* filename
(`drive_as_code.yaml`) returned zero hits and falsely confirmed a claim, because every pack
actually uses `drive.yaml`. **Enumerate producers, not call shapes.**

**A fourth instance, in a new costume (`PDR-0018`): a name is not evidence of the thing it names.**
Five directories named for five pedagogical stages contained three universes; I escalated a
question premised on their being tuned without running the one `diff` that refutes it. Before
escalating on a property of an artifact, verify the artifact has that property.

Do not re-litigate `PDR-0006` (strangler), `PDR-0007` (universality), `PDR-0014`/`PDR-0015`
(bounds scope) or `PDR-0016` (bounds+normalization together) — all decided on measured evidence.
Read `vision.md` first: it is ENDORSED, and changing it escalates.
