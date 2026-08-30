# Roadmap — HAMLET / Townlet        Updated: 2026-08-31 · forty-ninth checkpoint (`PDR-0132`)

> Sequencing, WSJF / cost-of-delay, and dated forecasts are produced by
> /axiom-program-management. This file records bets as INTENT, not a delivery
> schedule. Do not compute WSJF here; hand the committed bet over for sequencing.

> **Within Now, the order is open (`PDR-0019`, owner-stated).** The WS-0…WS-7 work streams are an
> **inventory, not a sequence**. One system is pinned at a time; the next is chosen on the
> strangler's selection criterion — *where does the runtime still know what the game is?* — not by
> stream number. Two constraints hold: one system at a time, and the work must be replacing,
> refactoring or fixing. Real blocking edges come from Filigree's current dependency graph; WS-7
> is now closed.

> **Bootstrap seed.** Now is derived from observed tracker + git state. Next/Later are derived
> from the three-pivot arc in `vision.md` and the HLD, and are **proposals awaiting the owner's
> DECIDE** — nothing below Now is committed. `docs/architecture/archive/ROADMAP.md` is a *different,
> stale* file (last updated 2025-10-30, "Phase 3 Complete") describing an engineering phase plan
> that predates the VFS/VTC/DAC era. This file does not supersede or edit it; retiring it is part
> of the Now bet.

> **Current checkpoint — 2026-08-31, `PDR-0132`:** no horizon change. Token work stays Now and
> now has five separately accepted milestones. The first executable unit deletes the inert
> observation-encoding surface and makes bounded positions canonical; compact replay remains
> behind both semantic repairs, followed by Unit 4 and Unit 5.

## Now  (committed, in-flight)

- **Strangler rewrite behind the compiled-universe contract** (`PDR-0006`) — the recovery
  execution model. Preserve behaviour against the pinned oracle, then replace one design-space
  unit at a time; differential tests answer “did behaviour change?” and WS-3 wiring tests answer
  “does the declaration do anything?”
  · **Delivered:** WS-1 is closed; WS-7 is closed as of 2026-08-31 after delivering determinism,
  oracle pinning, the differential harness, divergence register and the first seam cut. Its
  standalone P3 `--oracle-ref` hardening item remains visible under the recovery milestone.
  · **Current branch state:** the fourth merge is on `main` at `9efadd3c`; active work is
  `project-recovery-3`. The bet has not exited: the oracle is still required and WS-3/WS-4 are
  open.
  · **Critical path:** WS-6 `hamlet-5e39fcccb0` → WS-2 `hamlet-337b9e80fb` → WS-3
  `hamlet-1f89714685` → WS-4 `hamlet-15050f280a`.
  · **Exit:** retire the oracle only when every registered divergence is terminal, the harness
  verdict contract is trustworthy, and the authoring surface is protected by config-in /
  behaviour-out wiring tests (`PDR-0058`).
  · **Gates:** product-source pushes run the CI-equivalent local lint set; every merge still owes
  the source-verified README gate. The documentation rewrite remains gated on WS-4 even though its
  tracker item appears ready.
  · metric: terminal divergence register, wiring-test coverage, trustworthy CI conclusions
  · Updated: 2026-08-31 (`PDR-0131`)

> **Retired record, not active delivery:** the authoring-trial instrument is terminal for its
> corpus (`PDR-0111`). No rate publishes from it and redesign remains parked. Its only live
> sequencing consequence is the 2026-10-06 trial-pack disposition deadline before token unit 5.

- **Token-based observation engineering — IN SCOPE, owner-directed** (`PDR-0108`,
  `PDR-0114`, `PDR-0131`, `PDR-0132`; `hamlet-fa6bb6da4a`). Phase A, the declared attention choice and
  full token cut through unit 3 are landed. The open work is no longer "prove set_encoder".
  · **The 9.43× decision is re-ruled (`PDR-0131`, superseding `PDR-0126`).** At the default
  100,000-transition capacity, the current 1,132-float serialization spends 863.6 MiB on
  observation pairs versus 91.6 MiB before the cut. About 810 floats are immutable declaration
  context repeated per transition and another 204 are rank padding; compact live state is 118.
  · **Next implementation unit:** store immutable per-slot descriptors once in the compiled
  artifact; store only presence/live values/actual-rank coordinates in replay; reconstruct the
  fixed cross-substrate token schema at the network boundary. Delete the old transition ABI —
  no compatibility path.
  · **Acceptance:** L1 dynamic replay ≤120 floats; 100k observation pair ≤96,000,000 float32
  bytes; batch 256 viable; encoding <25% of `env.step`; Grid2D/Grid3D/aspatial transfer,
  visibility and reconstructed-input parity pinned. Unit 4's 79.19 IQM floor runs only after
  this ABI lands; unit 5 then migrates every shipped pack.
  · **Checkpointed sequence (`PDR-0132`):** canonical bounded positions
  (`hamlet-6a4a6596bd`) → meter `range_type` wiring (`hamlet-1e335e0363`) → compact ABI
  (`hamlet-1b1caf552a`) → Unit 4 engineering regression (`hamlet-25fc3fb955`) → Unit 5 shipped-pack
  migration (`hamlet-55b2826a02`). Compact waits on both semantic repairs even though those bugs
  remain independently startable. Each milestone needs terminal tracker evidence and a committed
  product checkpoint before its successor begins. Relational/message exposure and dynamic
  variables remain downstream, not silently folded into this unit.
  · metric: replay resident bytes, viable batch size, observation-encoding share, unit-4
  regression floor
  · Updated: 2026-08-31 (`PDR-0132`)

## Next (shaped, decreasing certainty)

- **The declaration-store compiler unit — PDR-0117 + variable-surface unification, one
  unit, after the token cut.** Pack filenames become convention (discovery/merge-by-id
  with loud collision refusal, canonical ordering, "required file" → "required
  declaration"); the three variable-declaration surfaces (`environment.yaml`,
  `vfs_profiles.yaml`, `variables_reference.yaml`) collapse to one declaration semantics
  — the compiler's largest validation tangle and VFS's worst authoring gap are the same
  defect (`PDR-0121` assessment). SourceMap file:line provenance already wired
  (`hamlet-af929afa06`); parked items from that cleanup land here. Explicitly NOT built:
  orchestrator tiers, sub-compiler graph engine, incremental compilation.
  · tracker: `PDR-0117`, `hamlet-af929afa06` (parks), `hamlet-33e520cebd` (symbol-table
  half) · metric: Config-surface coverage · Added: 2026-08-24 (`PDR-0117`, `PDR-0121`)

- **The epistemic-access unit — give declared epistemic state its doors, after the token
  cut.** The 2026-08-24 audit's systemic gap as one design: authoring fields for
  `readable_by`/`writable_by` on the required surfaces, `exposed_to` fails CLOSED, the
  observation path reads through the checked accessor (the `get_agent` bypass dies —
  `hamlet-83a043a9b9`), roles actually passed at call sites (`hamlet-1a520475f4`),
  `lifetime` author-declared (`hamlet-4597fd5d04`, `hamlet-0268336cd1`). Designed with
  awareness of the owner's **declared-propagation** proposal (observability as a
  per-(observer, source) expression — vision range from brightness, latched by floor) so
  static doors and dynamic gates land as one epistemic design; token presence bits are
  the natural carrier.
  · tracker: `PDR-0120`, propagation feature ticket, `hamlet-d97b4d6b4a`,
  `hamlet-c78fbf32a3` · metric: Declared-but-inert config surfaces · Added: 2026-08-24
  (`PDR-0120`)

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
  · **unit 4 LANDED (`PDR-0076`, `ebd16fce`, 2026-08-17): every compiled observation field
  declares its `feature` from one closed vocabulary (`variable` + nine engine-published members;
  `meter` fields name their meter), and nothing in `src/townlet/` outside the compiler's own emit
  sites compares an observation field's name to a literal — the encoder is one loop and one
  publisher table, the recurrent network finds its blocks by feature under any name, the demo has
  one window helper.** `hamlet-39e1fe3c6d` closed. The discriminator lives on the DTO, not the
  hash-bearing mirror, so the harness read the cut as invisible (16 `AGREE` + 4 DIV-006 unchanged)
  and the register did not grow. Next candidates in this queue: the `exposed_to` hidden default in
  the profile validators (unfiled), `hamlet-1ad6383186` (item layout), `hamlet-7cd887c9e5`
  (reference pack rot).
  · **unit 3 LANDED (`PDR-0075`, `8c5fa2c8`, 2026-08-17): every exposed global/agent VFS profile
  variable is its own observation field, named after the variable, in its declared scope, carrying
  the author's `semantic_type` (required, closed vocabulary, `bars` reserved, collisions a compile
  error); the item slots are ONE compiler feature `obs_item_slots`; the runtime reads every field
  by declared scope — the `obs_vfs` name branch is deleted.** `hamlet-f0ed709ecf` closed. Item
  variables carry no `semantic_type` on purpose (a declaration that can reach nothing is removed,
  `PDR-0066`); the item-layout question is `hamlet-1ad6383186`. Sibling primitive name-syncs
  (`obs_grid_encoding`, `obs_temporal`, `obs_affordance_*`, `obs_effects`, now `obs_item_slots`)
  are the same shape and the next candidate in this queue.
  · **unit 2 LANDED (`PDR-0069`/`PDR-0070`, `fb791193`, 2026-08-17): presentation is declared
  (`presentation.yaml`, observer-only), honest by default (declared bounds, no `%`/`$`), never inferred —
  every live name-branch in server and frontend gone; `hamlet-0dd4ac24d9` closed.** Next in the queue:
  `hamlet-f0ed709ecf` — but read `PDR-0068`'s trigger first: 26 commits sit ahead of `main`.
  · **first two units under `PDR-0047` LANDED (`PDR-0066`, `a2f349d7`, 2026-08-16):** the
  `semantic_type` vocabulary has one definition and the author's declaration reaches the compiled
  field for `environment.yaml` variables; `interaction_type` is required from one vocabulary.
  Follow-up filed inside this bet: `hamlet-f0ed709ecf` — split the `obs_vfs` block into
  per-variable fields (vfs.md §8.1) so profile variables can declare their group and the
  runtime's `obs_vfs` name branch dies. Next in the queue: `hamlet-0dd4ac24d9` (presentation
  hardcoded by variable name).
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
  · known debt: `docs/bugs/JANK-08-population-structured-and-dueling-flags-unused-in-training-logic.md`
  — declared brain flags unused by training logic (declared-but-
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
  **2026-08-17: the declared surface it needs now EXISTS** — `presentation.yaml` (`PDR-0069`), currency
  formatting is one `format: {kind: currency, …}` away for a showcase pack; the curriculum packs
  ship none. Building the pack itself is unchanged: outward-facing, owner's call.
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
