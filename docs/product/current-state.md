# Current State — HAMLET / Townlet        Checkpoint: 2026-08-11 · third checkpoint

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

- ⚠️ **THE CURRICULUM WAS TUNED WHILE HALF ITS ECONOMY WAS INERT — who re-authors the packs?**
  Task 3 measured a **35–58%** drop in interactions that used to complete; task 3a revives the
  money economy on top of that. The packs' balance was never tested at declared values. Per
  `PDR-0015`'s reversal trigger, if L1 training collapses the fix is **not** to re-cap money or
  re-inert the costs — it is to re-author the packs. That is a curriculum decision, not WS-1's.
- ⚠️ **WHEN DO WE STOP ADDING TO WS-1 AND FREEZE?** WS-1 has grown 7 → 10 units. Each addition
  was justified individually and none was optional under `PDR-0012`. `PDR-0014`'s reversal
  trigger 2 (*"the bounds wiring materially delays the oracle freeze"*) is **approaching, not
  definitively tripped** — flagged here so the next DECIDE acts on it deliberately.
- ⚠️ **THE "LOW ENERGY DELIRIUM" TEACHING CLAIM IS NOW UNVERIFIED.** The L0_0-vs-L0_5
  comparison is a documented pedagogical centrepiece and it does not carry across `30c433e3`.
  Any teaching claim resting on pre-today runs needs re-measuring.
- **Design fork inside `PDR-0009`** — per-level `architecture` override, or make `brain.yaml`
  level-overridable the way `training.yaml` is? Now has two consumers (`PDR-0017`). Decide
  before implementing.
- **README push** remains the owner's call; drafting and committing locally is endorsed.

Closed: the poisoned-cache hazard (WS-1(a) landed); CUDA blocked (was an unused dependency);
*"what is the real test coverage?"* (**81%**, `PDR-0010`).

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

Do not re-litigate `PDR-0006` (strangler), `PDR-0007` (universality), `PDR-0014`/`PDR-0015`
(bounds scope) or `PDR-0016` (bounds+normalization together) — all decided on measured evidence.
Read `vision.md` first: it is ENDORSED, and changing it escalates.
