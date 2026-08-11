# Roadmap — HAMLET / Townlet            Updated: 2026-08-11 (PDR-0017) · prior: 2026-08-11 (PDR-0006, PDR-0008, PDR-0009)

> Sequencing, WSJF / cost-of-delay, and dated forecasts are produced by
> /axiom-program-management. This file records bets as INTENT, not a delivery
> schedule. Do not compute WSJF here; hand the committed bet over for sequencing.

> **Bootstrap seed.** Now is derived from observed tracker + git state. Next/Later are derived
> from the three-pivot arc in `vision.md` and the HLD, and are **proposals awaiting the owner's
> DECIDE** — nothing below Now is committed. `docs/architecture/ROADMAP.md` is a *different,
> stale* file (last updated 2025-10-30, "Phase 3 Complete") describing an engineering phase plan
> that predates the VFS/VTC/DAC era. This file does not supersede or edit it; retiring it is part
> of the Now bet.

## Now  (committed, in-flight)

- **Strangler rewrite behind the compiled-universe contract** — freeze the current system as an
  **oracle**, then knock down and rebuild one *design-space unit* at a time against it, keeping the
  provenance spine and re-earning the rest through a differential harness. The owner returned from
  six months of intermittent attention to a codebase they described as *"best we could do at the
  time, but uneven and lumpy in places that didn't get an extra quality pass."* The maturity
  assessment returned REPAIR for all 8 subsystems, but `PDR-0006` supersedes that *execution model*
  (the assessment's instrument was biased toward REPAIR, and the spec is as spotty as the code):
  the oracle dissolves the specification bottleneck for preserved behaviour, so spec-writing
  collapses onto genuinely **new** surface only.
  · tracker: milestone `hamlet-1ade187dcc`, work streams **WS-0…WS-7** with the dependency graph
  wired. **WS-7** (`hamlet-e3af412673`) is the enabling stream — determinism, oracle tag,
  differential harness, known-divergences register, per-unit seam cutting — and gates every
  knockdown. **WS-3** is reshaped into the differential harness and becomes the program's central
  artifact.
  · metric: **Subsystem maturity established** ✅ 8 of 8; now guarded by **Provenance integrity**
  (BREACHED, `PDR-0008`), **Declared-but-inert config surfaces** (~40 → 0), **Documentation truth**
  (≥14 false claims → 0) and **Gates green** (1 of 4 → 4 of 4)
  · **PDR-0002** gated the assessment · **PDR-0004** adopts the dispositions · **PDR-0005** sets the
  triage rule (**wire, not delete**) · **PDR-0006** chose the strangler · **PDR-0008** verified
  WS-1 by execution and reordered it
  · ready now, no prerequisites: **WS-1** (`hamlet-67ffbd282a`, P0 — now four *executed* defects
  plus two new provenance issues, `hamlet-ae6601e463` and `hamlet-1029f99f4b`; it gates the oracle
  freeze), **WS-6** (`hamlet-5e39fcccb0`, head of the critical path) and **WS-0**
  (`hamlet-8eeaba1461`)

  The 2026-05-16 architecture-gap milestone `hamlet-7a932c4e40` is annotated **superseded in
  scope**; its three open children were reparented into WS-0 / WS-3 / WS-5 with their scope
  corrected.

## Next (shaped, decreasing certainty)

- **Measure the authoring claim** — define the N-idea corpus and the trial protocol that turns the
  north-star from `UNMEASURED` into a number. Until this exists, no bet can be accepted on
  authorability grounds and the central thesis is untested opinion.
  · tracker: not yet filed · metric: north-star **Zero-Python authoring rate**

- **Close the "you must write Python" gaps — WS-4, the actual product work.** The assessment's
  authorability ledger replaced the earlier guess (substrate topology as sole holdout) with a real
  list, and it is longer than hoped: **Config-surface coverage is ~2 of 7, not 6 of 7.** VTC
  action-writes have no YAML path at all; custom actions are structural no-ops; 3 of 4 effect
  scopes are inert; curriculum stages are a Python literal capped at 6 meters.
  · tracker: `hamlet-15050f280a` (WS-4), blocked by WS-1 and WS-3
  · metric: input **Config-surface coverage** (~2 of 7 → 7 of 7)
  · largest single win: populate `RuntimeAction.reads/writes` from config — the entire 11-mode
  composition engine already exists and is tested; only the YAML door is missing
  · note: `hamlet-030f2ce0aa` (EnvFactory) is *not* this bet, but its framing here is **corrected
  by `PDR-0006`** — under a strangler, changeability *is* the enabling constraint, so seam-cutting
  is strategic rather than incidental. Per `PDR-0006` §2b it is nonetheless cut **per knockdown
  unit inside WS-7**, not as an up-front global gate, so it stays out of this bet.
  · added `PDR-0009`: **per-level `architecture` is unauthorable** (`hamlet-0d0115383e`) — no pack
  can express the documented MLP→LSTM progression. Sequenced *after* WS-1(b)/(c), because enabling
  recurrent authoring before the recurrent training path is fixed would ship an option whose
  observable behaviour is wrong.

- **Prove generality — substrate axis DONE, domain axis outstanding.** `PDR-0003` obligation B.
  The **"Sims in six dimensions"** witness passed on 2026-08-11 (one file, ~6 lines, zero
  `src/townlet/` changes; compiles, resets, 50 steps; action vocabulary auto-expands to
  `DIM0_NEG…DIM5_POS`). See `metrics.md` → Trial 001. Still wanted: a **domain**-varying witness
  sharing no vocabulary with Townlet Town. Existing non-Town packs are candidates of unverified
  depth.
  · tracker: not yet filed · metric: north-star **Zero-Python authoring rate (world)** (1 of 1)
  · unblocks the 6-D demo's only caveat: TASK-009 ND-POMDP, folded into WS-4

- **Close the demo's privileged-Python paths** — enforce the dogfooding rule so Townlet Town is
  authored through the same door as any user. Cheapest honest read on the central claim, and
  measurable today. `PDR-0003` obligation A.
  · tracker: not yet filed — scope from the assessment's authorability ledger
  · metric: input **Demo dogfooding — privileged-Python count** (→ 0)

- **Brain as Code, Layer 1 + Layer 3** — the behaviour contract (ethics, panic, personality) and
  the think-loop execution graph. This is the half of the vision that is specified in the HLD and
  not built; it is what makes the *mind* authorable rather than just tunable.
  · tracker: `docs/tasks/TASK-005-BRAIN-AS-CODE.md` (spec, unfiled) · metric: input
  **Config-surface coverage** extended to cognition
  · known debt: `docs/bugs/JANK-08` — declared brain flags unused by training logic (declared-but-
  inert config is the worst failure mode for a declarative product)

## Later (directional bets, no order, no dates)

- **BAC as a first-class compiled artefact** — brain and universe through one standard
  experimental compiler, symmetric hashing and provenance, so an experiment is a single
  content-addressed pair.
- **Governance axis of the HLD success criteria** — tick-level proof, checkpoint replay, lineage
  rules, chain-of-custody. Currently the least-served of the three axes.
- **The authoring surface itself** — whatever makes writing a universe feel like writing a game
  rather than editing YAML by hand (templates, scaffolding, validation feedback, live preview).
  Directional only; unshaped. This is where "writing a game as experience" stops being an
  architecture claim and becomes a user experience.
- **Re-enable episode recording and replay** — deferred, not rejected. The implementation is being
  deleted in WS-2 (unreachable at three points, 9 months stale), but the *capability* was real and
  advertised: episode capture, real-time replay, export for teaching and demo material. It serves
  `PDR-0003`'s tech-demo obligation — showing what agents actually do is how the demo makes its
  "powerful example" claim. Intent captured before deletion by `hamlet-16ae192d42`; rebuild against
  the compiled-universe contract rather than restoring. `PDR-0007` reading: an option not yet
  enabled.
  · tracker: `hamlet-16ae192d42` (capture) · metric: none yet

- **Token-based observation encoding, and whether the observation shape is a game-engine fact**
  — the fixed 124-dim vector with its fixed 14-affordance vocabulary is a hardcoded statement
  about one universe. Owner-raised (*"move to embedded transformers"*), captured rather than
  started. Notable: the token encoder ALREADY EXISTS (`SetEncoderQNetwork`, authorable as
  `architecture.type: set_encoder`) and is used by zero of 21 packs — so the first unit is
  proving it works, not adding attention. Separates cleanly into **structure** (tokens kill the
  fixed vocabulary — real strangling) and **scale** (magnitude belongs to the declared
  normalization surface, which `PDR-0016` wires now). Sequenced after the oracle freeze and
  after the HLD-vs-implementation divergence map, because it is a "what should a well-implemented
  version look like" question and that map is what answers those.
  · tracker: `hamlet-fa6bb6da4a` (blocked by `hamlet-0d0115383e`) · `PDR-0017` · metric:
  Config-surface coverage, Declared-but-inert config surfaces

- **External adoption readiness** — the secondary audience (other RL researchers / OSS users)
  becomes real only after the authoring claim is measured and the docs are true. Deliberately
  last; note that anything user-facing here crosses the authority boundary and needs owner
  sign-off.
