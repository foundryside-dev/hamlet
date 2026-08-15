# Roadmap — HAMLET / Townlet            Updated: 2026-08-16, twentieth checkpoint (`PDR-0061`: `multi_tick` and wraparound hours EXECUTE — the escalation trigger did **not** fire, the pack was the defect, not the engine; `PDR-0062`: the `slow` marker is removed and the default gate reading is honest, deselect 33 → 2; `PDR-0063`: the differential harness's self-comparison DISAGREES, so it currently certifies nothing — filed, deliberately not fixed; `PDR-0064`: a parameter the object cannot function without is required at binding. **No horizon change**) · prior: 2026-08-15, nineteenth checkpoint (`PDR-0058`: **THE MERGE TO `main` LANDED** at `07b26ed5`, both gates discharged first at `33bfff51` — and the owner ruled the bet's **exit was mis-stated**: the merge was an output, not the outcome. The Now bet continues with its exit restated as an outcome condition. `PDR-0059`: the gate hides 31 failures behind a marker, and closing that is the next unit. **No horizon change**) · prior: 2026-08-15, seventeenth checkpoint (`PDR-0048`: **merge gate 2 SATISFIED** — both gates now stand, both commit-scoped, and gate 2 is already owed again at merge; `PDR-0047`: the owner's authoring-grammar ruling gives the Next bet *"close the you-must-write-Python gaps"* its first decided unit. **No horizon change**) · prior: 2026-08-15, fifteenth checkpoint (`PDR-0043`: merge gate 1 — CI restoration — EXECUTED and in verifying; the measured gate set widened 4→6, all green locally; the first CI run in this branch's history fires on the owner's push. **No horizon change**) · prior: 2026-08-15, thirteenth checkpoint (`PDR-0041`: the FIRST KNOCKDOWN is COMPLETE — the substrate→observation-dim seam is cut, the harness adjudicated it end-to-end, and the strangler method is proven once. **No horizon change**) · prior: 2026-08-14, eleventh checkpoint (`PDR-0038`, `PDR-0039`: the owner cleared the whole escalation queue; the README is rewritten and ships branch-scoped; the merge to `main` gains two named gates, CI restoration and README re-verification. New Later bet: adopt wardline as hygiene) · prior: 2026-08-14 (`PDR-0035`–`PDR-0037`: the first knockdown unit is DECIDED — the substrate→observation-dim seam — and content 5's order is changed by a blocking finding in the harness. One Next bet narrowed by one item. **No horizon change**) · prior: 2026-08-13 (harness accepted, `PDR-0032`–`PDR-0034`) · prior: 2026-08-13 (oracle pinned, `PDR-0030`)

> Sequencing, WSJF / cost-of-delay, and dated forecasts are produced by
> /axiom-program-management. This file records bets as INTENT, not a delivery
> schedule. Do not compute WSJF here; hand the committed bet over for sequencing.

> **Within Now, the order is open (`PDR-0019`, owner-stated).** The WS-0…WS-7 work streams are an
> **inventory, not a sequence**. One system is pinned at a time; the next is chosen on the
> strangler's selection criterion — *where does the runtime still know what the game is?* — not by
> stream number. Two constraints hold: one system at a time, and the work must be replacing,
> refactoring or fixing. Real blocking edges (WS-1 gates WS-7) are unaffected.

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
  knockdown. The **differential harness is BUILT and ACCEPTED** (`PDR-0032`/`PDR-0033`,
  `d54ad7df`, `src/townlet/oracle/`): oracle worktree vs working tree, same pack + seed,
  provenance-hash pre-check then byte-exact trace comparison; mutation-verified red.
  · **The first knockdown is COMPLETE (`PDR-0041`, `b7574132`, 2026-08-15): the
  substrate→observation-dim seam is cut.** The compiler asks the substrate instance for
  every observation dim (five-member contract on `SpatialSubstrate`, parity-pinned against
  the encoders); the three registered crashing configs run; the full 16-cell matrix exits 0
  on CPU and CUDA with all six DIV-003 cells `DIVERGED_AS_REGISTERED` and every standing
  cell byte-exact AGREE. The strangler method — register, bind, cut, adjudicate — has now
  run end-to-end once, which is what `PDR-0035` chose this unit to prove. The unit as
  decided, kept for provenance:
  the contract by which the compiler learns a substrate's observation shape. Not the
  `substrate/` package (the crashes are the compiler's; that boundary would leave all four
  intact) and not the one-line repair. Chosen on `PDR-0019`'s criterion: the compiler switches
  on `substrate.type` strings at `compilers/observation.py:64-76` and `:135-145`, while
  `:146-155` **already asks the substrate instance** for `continuous`/`continuousnd` — the
  right pattern, in the same function, applied to 2 of 5 types.
  · **Content 5's `PDR-0037` order (harness → DIV-003 → matrix cells → cut) is EXECUTED IN
  FULL**: step 1 at `9a75b581` (`PDR-0040`), steps 2–4 at `b7574132` (`PDR-0041`). The
  register's discipline held the whole way — oracle behaviour re-verified at the tag before
  the entry was written, cells landed `NEW_SIDE_ERROR` honestly pre-cut, and flipped only
  when the rebuild actually ran.
  · **`PDR-0034` corrects a claim this bullet used to carry.** WS-3 is **NOT** reshaped into the
  differential harness. The harness asks *did old and new behave the same?* — a surface inert on
  **both** sides yields identical traces and correctly reports AGREE, so inertness is invisible
  to it by construction. WS-3 (`hamlet-1f89714685`) remains the **wiring-test** mandate — change
  a YAML value, assert runtime behaviour changed — still `open`, still blocking WS-4, and still
  the answer to *why six consecutive declarative features shipped inert*. The two instruments are
  complementary: **differential = did behaviour change; wiring = does the declaration do
  anything.**
  · metric: **Subsystem maturity established** ✅ 8 of 8; now guarded by **Provenance integrity**
  (all 3 breaches CLOSED 2026-08-13 — row goes green when the two filed gaps enter WS-7's
  register, `PDR-0028`), **Declared-but-inert config surfaces** (baseline ~40; post-assessment
  7 found / 2 closed), **Documentation truth** (≥14 false claims → 0) and **Gates green**
  (**GREEN as of 2026-08-16, over a suite that finally runs what it claims** — all 31 repaired
  and the `slow` marker removed after being measured against a clock and found false; deselect
  falls 33 → 2. The residual 2 are `test_differential_harness.py`, filed `hamlet-6f98e38a36`,
  and are stated rather than banked: **the harness's self-comparison disagrees, so the
  instrument the strangler is measured with currently certifies nothing** — `PDR-0062`,
  `PDR-0063`)
  · **WS-1 is COMPLETE and CLOSED** (`PDR-0029`, 2026-08-13, `e8ad4985`): all ten frozen units
  landed, tree green at every commit, batch gate 2981/0. The `PDR-0028` fence held — nothing
  entered after the freeze. Routing rule stands for new findings: WS-7's register or WS-4.
  · **PDR-0002** gated the assessment · **PDR-0004** adopts the dispositions · **PDR-0005** sets the
  triage rule (**wire, not delete**) · **PDR-0006** chose the strangler · **PDR-0008** verified
  WS-1 by execution and reordered it
  · ready now, no prerequisites: **WS-7** (`hamlet-e3af412673`, P0 — unblocked by WS-1's close;
  the known-divergences register is its FIRST artifact, `PDR-0028` reversal trigger), **WS-6**
  (`hamlet-5e39fcccb0`) and **WS-0** (`hamlet-8eeaba1461`). WS-1 (`hamlet-67ffbd282a`) closed
  2026-08-13.

  · **THE EXIT IS RESTATED — the merge is NOT the exit (`PDR-0058`, owner-ruled, 2026-08-15).**
  This bullet used to say *"the merge to `main` is the bet's exit."* The merge landed at
  `07b26ed5` (PR #32, by the owner, both gates discharged first at `33bfff51`) while the strangler
  had cut **two** units, WS-0/3/4/5/6 were all open, and `Config-surface coverage` read ~2 of 7 —
  so the recorded exit fired without the bet being finished. The owner's ruling: the merge was an
  **output**, not the outcome. **The Now bet exits when the pinned oracle can be RETIRED**, on
  three conditions that must be *read*, not asserted: (1) every entry in
  `docs/oracle/known-divergences.md` is terminal — closed by an adjudicated rebuild, or accepted
  as permanent with its own PDR; (2) the harness's verdict vocabulary is re-earned or its
  successor recorded (`PDR-0056` put this on the clock — `AGREE` is currently unreachable
  matrix-wide); (3) `Gates green` is read on a suite that hides nothing (`PDR-0059`) —
  **substantially advanced 2026-08-16 but NOT met: deselect is down 33 → 2 and all 31 hidden
  failures are repaired and gated, but 2 remain hidden (`hamlet-6f98e38a36`), and condition (3)
  says *nothing*, not *nearly nothing*.** Note those 2 also bear on condition (2): the harness
  whose vocabulary must be re-earned is currently failing its own self-comparison (`PDR-0063`).
  **Merging is
  a publication step that may happen any number of times inside the bet**, each time owing
  `PDR-0039`'s unconditional re-sweep — **13 commits already sit ahead of `main`, so the next
  merge owes it now.** And the authorability threshold (`Config-surface coverage` 7 of 7) is
  explicitly **NOT** this bet's exit — that is WS-4, in *Next*. Conflating the two is what
  produced the mis-statement.

  · **The two named gates, and how they now stand** (`PDR-0039`, owner:
  *"hopefully we'll recover before we push back to main"*). (1) **CI restoration**
  (`hamlet-2100105c9a`, P1) — no workflow has ever run on this branch and nothing has passed since
  2025-11-28, so merging would put 145 unvalidated commits on the default branch; sequenced before
  the merge, after the current knockdown. (2) **README re-verification** by the same method that
  produced it, not a re-read — its rough-edges and CI sections describe conditions the recovery
  intends to *fix*, and merging them unchanged converts honest status into stale claims on `main`.

  · **BOTH GATES WERE DISCHARGED AT THE MERGE, and gate 2 is already owed again (`PDR-0058`,
  2026-08-15).** `33bfff51` executed both conditions before PR #32: the nightly cron **restored**
  (so `PDR-0043` reversal trigger 2 did **not** fire) and gate 2 **re-swept at the merge commit**
  per `PDR-0039`, finding *five more* stale README claims in four commits. `PDR-0043` trigger 2 is
  discharged, not lost. **Gate 2 re-fires at the NEXT merge, unconditionally** — 13 commits sit
  ahead of `main` already. The first scheduled run of the restored nightly then failed
  (`PDR-0059`) — the deferral paid off immediately by surfacing 31 hidden failures. Historical
  reading below, superseded by this bullet and by `PDR-0058`:

  · **BOTH GATES ARE NOW SATISFIED, and both are commit-scoped (`PDR-0048`, 2026-08-15).**
  Gate 1 closed on remote evidence at `dd94e122` (first CI runs in the branch's history, all
  three green). Gate 2 — README re-verification **by method** — executed at `1b25c99d`: ten
  claims had gone stale in one day, every one because the recovery *fixed* the thing being
  described, and the adversarial pass caught one defect in the new draft as well. **Neither gate
  is banked.** `PDR-0039` fires the re-verification *at the merge, unconditionally*, and three
  commits have landed since `1b25c99d`, so gate 2 is already owed again. The merge itself
  remains the owner's decision (`PDR-0046`: publication is not undone by pushing again), and the
  checklist still inherits `PDR-0043` trigger 2 — restore the nightly cron at merge or record
  the PDR that kills it. **No horizon change.**

  · **Gate 1 status (`PDR-0043`, 2026-08-15): EXECUTED, in verifying.** Inputs fixed first per
  the issue's own ordering (two drifted packs repaired; the previously-unknown second failing
  gate `no_defaults_lint` adjudicated); three workflows now fire on push to this branch; the
  nightly cron is deleted and the Full Test Suite parked `disabled_manually` until the merge
  (on-demand via dispatch). `hamlet-2100105c9a` closes on the first green run after the owner's
  push. **The merge checklist inherits `PDR-0043` reversal trigger 2**: the merge must restore
  the nightly (or record the PDR that kills it) — merging without it converts a deliberate
  deferral into silent capability loss.

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
  · **narrowed by one item, `PDR-0035`:** *delegate substrate observation dims to the substrate
  instance* (assessment line 227) is subsumed by WS-7's first knockdown and no longer waits on
  WS-3 — the knockdown carries its own instrument. Exactly one item moves; every other
  ledger item stays here and stays behind WS-3 (`PDR-0034` unchanged).
  · largest single win: populate `RuntimeAction.reads/writes` from config — the entire 11-mode
  composition engine already exists and is tested; only the YAML door is missing
  · note: `hamlet-030f2ce0aa` (EnvFactory) is *not* this bet, but its framing here is **corrected
  by `PDR-0006`** — under a strangler, changeability *is* the enabling constraint, so seam-cutting
  is strategic rather than incidental. Per `PDR-0006` §2b it is nonetheless cut **per knockdown
  unit inside WS-7**, not as an up-front global gate, so it stays out of this bet.
  · added `PDR-0009`: **per-level `architecture` is unauthorable** (`hamlet-0d0115383e`) — no pack
  can express the documented MLP→LSTM progression. Sequenced *after* WS-1(b)/(c), because enabling
  recurrent authoring before the recurrent training path is fixed would ship an option whose
  observable behaviour is wrong. **Fork RESOLVED by `PDR-0027`** (owner, 2026-08-13): `brain.yaml`
  becomes level-overridable the way `training.yaml` is, PLUS a lineage-legibility acceptance
  criterion — a brain override forks the lineage, and the fork must be stated at load, never
  discovered at runtime.

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

- **Model + interface-contract export** — a trained agent leaves HAMLET and runs in someone
  else's engine or pipeline. Serves **the prototyping modeller** — game dev, simulation, and
  abstract real-world modelling (`PDR-0024` **accepted with alteration** 2026-08-13; audience
  widened by the owner beyond game devs; `vision.md` amended). Half of it already exists: the
  "interface contract" is the observation/action schema and its hashes, which WS-1 has been
  hardening. The other half — a standalone model, decoupled from the training stack — is designed
  and unbuilt (`TASK-008`, *Planned* since 2025-11-05, needs re-specifying under `PDR-0012`;
  `hamlet-0cdb8a6d1a`). Sequence after the oracle freeze: the contract must be stable before it
  is handed to anyone.
- **The tech-demo suite at release** — what *"one of several tech demos we'll provide at the
  end"* means concretely (`PDR-0026`, owner-resolved). Obvious members already on the board:
  Townlet Town with the LED contrast actually authored for the first time (`hamlet-e979f2ba37`),
  the "Sims in six dimensions" substrate witness (Trial 001, passed), and the still-wanted
  domain-varying witness. Townlet Town remains first-class among them (`PDR-0003` unchanged).
  Intent only; anything distributable is outward-facing and gates to the owner.
- **The "locked" showcase experiment** — a distributable, frozen artefact for sharing a design:
  *"look at this cool thing I designed."* Distinct from the oracle freeze (internal reference) and
  from model export (a model for someone else's engine). This is the one place prettified
  presentation is appropriate — currency rendered as currency — because the audience is looking at
  a designed artefact, not learning what the substrate is (`PDR-0025`). Intent only; building or
  distributing one is outward-facing and gates to the owner.
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

- **Adopt wardline as a hygiene activity** — declare real trust boundaries in `src/townlet/`
  so a taint gate can actually fail, then re-instate the agent instruction. Owner-stated
  intent, 2026-08-14: *"we'll adopt wardline as a hygiene activity later on."* The mandated
  gate was **deleted** from `CLAUDE.md`/`AGENTS.md` this session (`PDR-0038`) because it was
  unfalsifiable — 0 boundaries across 1555 functions, no decorators, not even a dependency, so
  no code change could make it fail. Deferred capability under `PDR-0007`, not a rejection: the
  `wardline-gate` skill and the `weft.toml` references are deliberately left in place because
  they are what adoption will need. Intent only, unshaped.
  · tracker: `hamlet-f894ade20a` (closed as deleted-with-intent-captured) · metric: guardrail
  **Gates green** — a fifth gate becomes real only when `--fail-on-inert` can pass

- **External adoption readiness** — the secondary audience (other RL researchers / OSS users)
  becomes real only after the authoring claim is measured and the docs are true. Deliberately
  last; note that anything user-facing here crosses the authority boundary and needs owner
  sign-off.
