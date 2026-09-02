# Vision — HAMLET / Townlet

> **Status: ENDORSED by the owner, 2026-08-11.** Explicitly confirmed after review, so this
> document is authoritative — not a bootstrap draft. Changing it from here is a vision change and
> escalates under the authority grant below.
>
> **Amendment log** (a vision change requires owner sign-off; each entry names the PDR that carries
> the provenance):
> - *2026-08-11* — added the anti-goal **"A carrier of technical debt — at all, until 1.0"**.
>   Escalated by `PDR-0012`, approved by the owner (*"yes, put it into the vision — it's absolutely
>   load bearing"*), recorded as `PDR-0013`. No other section changed; the authority grant is
>   untouched.
> - *2026-08-13* — added **the prototyping modeller** to *Who it serves*. Escalated by `PDR-0024`,
>   approved by the owner **with the audience widened** beyond game devs (*"anyone interested in
>   game dev, simulations, or modelling the real world in an abstract way"*). Recorded in
>   `PDR-0024`'s Resolution. The authority grant is untouched.
> - *2026-08-14* — corrected the **public-repo URL** in the authority-grant note below from
>   `github.com/tachyon-beep/hamlet` to `github.com/foundryside-dev/hamlet`. Measured: the old
>   path redirects to the new one and **both report `PUBLIC`**, so the grant's reach is
>   unchanged. Offered at the 2026-08-14 grant re-confirmation and approved by the owner in the
>   same session; recorded as `PDR-0038`. Factual correction only — no section's meaning
>   changes and the authority grant itself is untouched.
> - *2026-08-15* — corrected the authority grant's **`Last reviewed` stamp** from `2026-08-11`
>   to `2026-08-15`, and stated the two intervening re-confirmations (2026-08-14, and again at
>   the 2026-08-15 `/own-product` resume) explicitly. The grant's **scope is unchanged** — same
>   autonomous list, same escalation taxonomy — so this is a factual correction of a stale
>   review date, not a vision change. The debt had been carried since 2026-08-14 as "fix at the
>   next approved touch"; offered and approved at the 2026-08-15 grant re-confirmation, the same
>   pattern `PDR-0038` set. Provenance PDR recorded at that session's checkpoint.
> - *2026-08-16* — corrected the authority grant's **`Last reviewed` stamp** from `2026-08-15`
>   to `2026-08-16`. The owner re-confirmed the grant unchanged at the first 2026-08-16 resume
>   without a `vision.md` touch being approved (so the stamp was left, per the 2026-08-15 rule:
>   corrected only at an approved touch); at the second 2026-08-16 resume the owner confirmed
>   the grant again **and approved this correction**. Scope unchanged — same autonomous list,
>   same escalation taxonomy, `PDR-0046` still governs the push. Factual correction, not a
>   vision change. Provenance PDR recorded at this session's checkpoint.
> - *2026-08-19* — corrected the authority grant's **`Last reviewed` stamp** from `2026-08-16`
>   to `2026-08-19`, and restated the intervening re-confirmations. The owner re-confirmed the
>   grant unchanged at each `/own-product` resume between those dates without a `vision.md` touch
>   being approved (so the stamp was left, per the 2026-08-15 rule: corrected only at an approved
>   touch); at the 2026-08-19 resume the owner confirmed the grant again **and approved this
>   correction**, choosing it explicitly over carrying the debt a third time. Scope unchanged —
>   same autonomous list, same escalation taxonomy, `PDR-0046` still governs the push. Factual
>   correction, not a vision change. Provenance PDR recorded at this session's checkpoint.
> - *2026-08-20* — **the authority grant is WIDENED, the first scope change since it was granted
>   on 2026-08-11.** The autonomous list gains *"commit and push `project-recovery*` branches —
>   checkpoint commits included"*, superseding `/product-checkpoint`'s blanket no-push rule for this
>   product. Owner-approved in-session, verbatim: *"you can extend the grant to include pushing, I
>   don't actually have an opinion on this."* Because that consent is explicitly indifferent rather
>   than considered, the widening was taken at its **narrowest defensible reading** — it covers the
>   `project-recovery*` branches only, and does **not** touch pushes to `main`, tags, releases, or
>   anything outward-facing. The merge to `main` remains the boundary and still gates on
>   `PDR-0039`. Recorded as `PDR-0099`, which also states what would make this widening wrong.
>   Every earlier amendment-log entry was a factual correction; this one changes scope, so it is
>   marked as such. The `Last reviewed` stamp was corrected from `2026-08-19` to `2026-08-20` at
>   the same approved touch, discharging the debt `PDR-0093` carried — the pattern `PDR-0038` set.
> - *2026-08-20* (third entry that day) — **the merge to `main` is no longer the boundary; it is
>   AUTONOMOUS.** Follows directly from `PDR-0100`: once publication means declaring 1.0, the ground
>   on which the merge escalated disappeared, and the owner ruled the merge autonomous rather than
>   leaving it gated on an unstated reason (*"Autonomous — run gate 2 and merge now"*). `PDR-0039`
>   gate 2 survives unchanged in substance but changes in KIND — from an escalation the agent waits
>   on to a quality gate the agent executes. This is a **scope change**, the second of the day.
>   Recorded as `PDR-0101`. Still escalated: declaring 1.0, announcement, tags/releases,
>   vision/strategy/grant changes, data deletion.
> - *2026-08-20* (second entry that day) — **"public release" is owner-DEFINED, and the definition
>   is narrower than this document had assumed.** Publication means *publishing a product* —
>   a coherent product offering, i.e. **declaring 1.0** — not code being visible on the internet.
>   Owner's words: *"I call publication declaring 1.0 - not makinmg content availabile on the
>   internet"* and *"publication => publishing a product and right now we don't have a coherent
>   product offering, just code"*. The grant's specifics note had cited the repo's public status as
>   what gave the release clause teeth; that was the standing agent's inference, never the owner's,
>   and it is **corrected, not annotated**, because it had been shaping how conservatively the agent
>   behaved — including the rationale written into `PDR-0099` an hour earlier. *Announcement*
>   remains a separate limb and still escalates. Recorded as `PDR-0100`. Scope of the autonomous
>   list is unchanged by this entry; what changed is the **meaning** of one escalation term.
> - *2026-08-13* — re-tagged the **tech-demo demonstrator claim** as delivery intent: "Low Energy
>   Delirium" was never implemented (*"the idea outran the codebase and we pivotd a few times"*),
>   and Townlet Town is **one of several tech demos** to be provided at the end. Escalated by the
>   2026-08-12 checkpoint, resolved by the owner, recorded as `PDR-0026`. The ambition, the
>   dogfooding rule, and both demo claims are unchanged.
>
> - *2026-08-22* — corrected the authority grant's **`Last reviewed` stamp** from `2026-08-20`
>   to `2026-08-22`, and stated the intervening re-confirmations explicitly: the owner
>   re-confirmed the grant unchanged twice on 2026-08-22 before this touch (at the fortieth- and
>   forty-first-checkpoint resumes, each time choosing to carry the stamp debt — the `PDR-0093`
>   shape), and at this session's `/own-product` resume confirmed the grant again **and approved
>   this correction**, choosing it explicitly over carrying the debt a third time. Scope
>   unchanged — same autonomous list (including the `PDR-0099` push and `PDR-0101` merge
>   widenings), same escalation taxonomy. Factual correction, not a vision change. Provenance
>   PDR recorded at this session's checkpoint.
> - *2026-08-24* — sharpened **the prototyping modeller** in *Who it serves* with the owner's
>   train-here-deploy-there articulation: the interface is the **declared telemetry manifest +
>   action vocabulary**, fidelity lives below it (the naval example, quoted verbatim); engine
>   bindings named as acknowledged future scope; the export path (`hamlet-0cdb8a6d1a`) named
>   vision-load-bearing and sequenced after the token migration. Content is the owner's own
>   in-session statements, recorded as `PDR-0119`; incorporation **approved by the owner
>   explicitly** at the forty-third checkpoint ("yes that's approved"). The authority grant is
>   untouched.
> - *2026-08-31* — corrected the authority grant's **`Last reviewed` stamp** from `2026-08-22`
>   to `2026-08-31`. The owner explicitly confirmed the grant in this session; its scope is
>   unchanged — same autonomous list, same escalation taxonomy, including the `PDR-0099` push
>   and `PDR-0101` merge widenings. This is a factual review-stamp correction, not a vision or
>   grant change. Recorded with the ownership reconciliation in `PDR-0131`.
> - *2026-09-02* — corrected the authority grant's **`Last reviewed` stamp** from `2026-08-31`
>   to `2026-09-02`. At this session's `/own-product` resume the owner confirmed the grant and
>   **approved this correction explicitly** ("Confirmed, update stamp"). Scope unchanged — same
>   autonomous list (including the `PDR-0099` push and `PDR-0101` merge widenings), same
>   escalation taxonomy. One mechanism note, not a scope change: the harness permission
>   classifier blocked the autonomous merge twice this session and the owner granted it via
>   `/permissions` (`PDR-0146`). Factual review-stamp correction, not a vision or grant change.
>   Provenance: `PDR-0146`.
> - *2026-08-20* (fourth entry that day) — corrected the
>   authority grant's **Status paragraph**, which still claimed the scope was *"unchanged from the
>   2026-08-11 grant"* and *"scope identical every time"*. Both clauses were falsified the previous
>   day by `PDR-0099` and `PDR-0101`, the first two scope changes the grant has ever taken. The
>   `Last reviewed` stamp had been corrected at that touch; the prose had not, so the Status line
>   contradicted both the amendment log above it and the autonomous list immediately below it —
>   which already granted push and merge. Found at `/own-product` ORIENT, offered at the grant
>   re-confirmation, and **approved by the owner in the same exchange**, chosen over carrying it as
>   stamp-style debt. Factual correction only: **no scope moves**, the autonomous list and the
>   escalation taxonomy are untouched. Provenance PDR recorded at this session's checkpoint.
>
> Drafted 2026-08-11 from observed repo, git history, and tracker state. Tags are retained as
> provenance of how each claim was established: **[stated]** = given directly by the owner;
> **[verified-from-source]** = established by reading the tree; **[assumption]** = inferred. The
> remaining `[assumption]` tags are *subordinate details* — the purpose, audience, tech-demo role,
> and pivot arc are all owner-endorsed.

## Purpose

> **The pivot, in one line: from *game as experience* to *writing a game as experience*.** **[stated]**
>
> The thing the user does for fun is no longer playing the simulation — it is **authoring** it.
> Every design decision is judged by whether it makes the act of writing a world (and a mind)
> more expressive, more immediate, and more legible. The simulation is the output; the authoring
> is the product.

Townlet is a **DRL substrate as code**: a declaratively-specified reinforcement-learning
environment where the *entire universe* — variables, observation spec, substrate topology,
affordances, effects, items, reward function, and curriculum — is expressed in YAML, compiled
into a frozen content-addressed `CompiledUniverse`, and executed GPU-natively against torch
tensors. **[stated]**

The change it exists to make, stated at full strength: **someone with a cool idea for a game
system, mechanic, or interaction can turn it into a working DRL gym trivially.** Not "students
learn RL by playing a game" — *authoring* is the product. The barrier between "I wonder what
agents would do with this mechanic" and a running, trainable, reproducible environment should
collapse to writing config. No Python, no environment-class subclassing, no observation-tensor
plumbing, no reward-function code. **[stated]**

That is what the machinery underneath is *for*. The universe compiler, VFS (declarative variable
and feature system), VTC (compiled transition programs), and DAC (declarative reward functions)
are not architectural elegance for its own sake — each one exists to move a category of "you must
write Python for this" into "you can declare this." The **preset grammar of problems** — a family
of RL tasks sharing one action/observation vocabulary — is the expressive range a novice author
gets for free, and the reason checkpoints transfer across universes at all. Provenance hashes make
every authored universe traceable to the exact run it produced. **[stated]**

### The three-pivot arc (where this is going)

The architecture is the vision made concrete. Read in order, the major pivots describe one
destination: **both halves of an experiment — the world and the mind — are declarative, compiled
by one standard compiler, content-addressed, and replayable.** The three pivots and this
destination are **[stated]**; the per-pivot status below is **[verified-from-source, 2026-08-11]**
— a bootstrap reading of the tree, not the owner's assessment, and explicitly subject to the
maturity assessment that is now the Now bet.

1. **Universe as Code (UAC)** — the world is config, not Python: meters, cascades, affordances,
   effects, items, substrate topology, terminal conditions, rewards. *Largely shipped* (compiler,
   VFS, VTC transition schedule, DAC). **[verified-from-source]**
2. **Brain as Code (BAC)** — the *agent's mind* is config: a behaviour contract, module
   architecture, and a think-loop execution graph, per `docs/architecture/archive/hld/02-brain-as-code.md` (archived 2026-08-24; current treatment: `docs/architecture/BAC.md`).
   *Partially shipped* — Layer 2 (network architecture, optimizer, loss, replay, Q-learning
   variants) is live and rich in `brain.yaml` + `brain_config.py` + the factory modules. Layer 1
   (cognitive topology: behaviour contract, ethics, panic, personality) and Layer 3 (think-loop
   DAG with governance ordering) are **not implemented**. **[verified-from-source]**
3. **One standard experimental compiler** — UAC and BAC pass through the same nine-stage pipeline
   to a single frozen, content-addressed `CompiledUniverse` carrying 7+ provenance hashes, with
   run bundles, exact resume semantics, and chain-of-custody. *Shipped for UAC; BAC participates
   via `brain_hash` but is not yet a full first-class compiled artefact alongside the universe.*
   **[verified-from-source]**

**Caveat on all three status calls:** "shipped" here means *present and wired*, not *mature*.
The owner reports the project came out of six months of intermittent attention and is buggy,
underspecified, and unfinished in places. Presence is not maturity — establishing the difference
is exactly what the Now bet exists to do.

The HLD's three-axis success test (`hld/10-success-criteria.md`) is the honest bar and is adopted
here: **technical** (snapshot discipline, checkpoint provenance, telemetry), **pedagogical**
(YAML-only reasoning, controlled ablations), and **governance** (tick-level proof, checkpoint
replay, lineage, chain-of-custody). All three must hold — "we built a neural net" is not success.

### Townlet Town is the first-class tech demo, not a demoted mission

Its origin was pedagogical — "trick students into learning graduate-level RL by making them think
they're just playing The Sims," still the stated mission in `README.md`, `CLAUDE.md`, and
`pyproject.toml`. The correct reading of what changed is **not** that pedagogy was demoted: *"we
promoted the world around it — it's gone from being 'the product' to being 'the first-class tech
demo of the product'."* **[stated]**

That distinction is load-bearing, and "first-class" is the operative word. The Sims-flavoured
survival universe (Townlet Town, its curriculum levels, and its "interesting failures" like Low
Energy Delirium) is the flagship demonstrator of the substrate: the proof that the thing works,
the artefact you show someone, and the widest existing exercise of the grammar's expressive range.
It carries real quality obligations and is maintained to them. It is not legacy, not a sample, and
not something recovery is free to let rot.

**Status of the demonstrator claim (owner-resolved 2026-08-13, `PDR-0026`):** the paragraph above
is **delivery intent, not a description of the shipped packs**. "Low Energy Delirium" has never
been implemented — the five shipped levels are three undifferentiated universes (`PDR-0018`) —
because *"the idea outran the codebase"* across several pivots; the project never finished it.
Townlet Town is **one of several tech demos to be provided at the end**; authoring its curriculum
for the first time is `hamlet-e979f2ba37`. The ambition stands; the tense was wrong. **[stated]**

**The demo makes two claims at once**, and this is its actual specification: *"this is a powerful
example of what you can make — **but you can also make anything else you can think of**."*
**[stated]**

Those two claims pull against each other, and the tension is the design constraint:

- **Claim 1 — power.** The demo must be genuinely impressive and non-trivial. Something a person
  sees and *wants*. A thin demo makes the substrate look like a toy.
- **Claim 2 — generality.** The demo must simultaneously prove it is **not special** — that the
  substrate is not secretly built around it. The moment the demo is impressive *because* it was
  special-cased, claim 1 is bought by destroying claim 2, and the product's promise dies with it.

Nearly every impressive demo in software resolves this tension by cheating toward claim 1. This
one may not.

**Obligation A — the dogfooding rule (serves claim 2).** A first-class tech demo only proves
anything if it was built the way a user would build it. **Townlet Town must be authored through
the same door as everyone else**: expressed in config, compiled by the standard compiler, with no
privileged Python path a novice author would not have. Any place the demo reaches for Python that
an outside author could not reach for is, by definition, an **authorability gap** — and it is the
most diagnostic kind, because it is a gap the project has already proven it cannot live without.
This makes the demo a permanent, running test of the central claim rather than a showcase that
flatters it.

**Obligation B — generality needs a second witness (also serves claim 2).** One universe, however
honestly authored, cannot demonstrate "anything else you can think of" — it can only fail to
contradict it. Proving generality requires further universes that vary one axis of the grammar
while holding the rest fixed.

**First witness found and verified, 2026-08-11: "Sims in six dimensions."** The owner's proposed
demo — take the Sims universe and re-substrate it into a 6-D world — was executed end-to-end.
**One file, ~6 lines of `stratum.yaml`, zero lines changed under `src/townlet/`.** It compiles,
resets, and steps; agents carry 6-D positions; the action vocabulary auto-expands from the
dimensionality to `DIM0_NEG … DIM5_POS` plus the domain actions; and the entire Sims domain — bars,
affordances, items, effects, rewards, curriculum — carries over untouched. Full detail and the one
real caveat (gridnd has no partial-vision support) in `metrics.md` → Trial 001.

This is a *better* witness than a from-scratch dissimilar universe would have been: holding the
domain fixed and varying only the substrate isolates exactly the thing being demonstrated. A
**domain-varying** witness is still wanted as the second axis; the existing non-Town packs
(`aspatial_test`, `L5_multi_agent`, `simple`, `reference`) are candidates of unverified depth.
**[assumption]**

The learner, correspondingly, is now an **author** rather than a player being tricked — but the
pedagogical value is undiminished by the promotion of everything around it.

## Who it serves

- **Primary:** the sole researcher/builder (John) — Townlet is the substrate their own experiments
  run on. Its first duty is to be trustworthy and fast to iterate for one expert user. **[stated]**
- **Secondary:** other RL researchers and OSS users who would adopt the substrate to express their
  own problem grammars. Served, but not at the primary's expense — no adoption-driven API freezing
  while the substrate is still being shaped. **[stated]**
- **The aspirational end-user (what success looks like, not who is served today):** the *novice
  author* — someone with a game-mechanic idea and no RL engineering background, who can express it
  as a universe and watch agents attack it. Every authoring barrier that requires Python is a
  defect against this user. They are not a current user; they are the standard the substrate is
  judged by. **[stated]**
- **The prototyping modeller (core use case; served at release, `PDR-0024`, sharpened
  `PDR-0119`):** anyone interested in game development, simulation, or modelling the real world
  in an abstract way, who wants a trained agent for a system of their own. They author a
  *simplified* version of their scenario here, train against it, and **leave with a model and an
  interface contract** they can code against in their own engine or pipeline. Where the novice
  author's journey ends inside HAMLET, this one ends outside it: HAMLET is the harness, not the
  destination. Every barrier between "it trains here" and "it runs in my system" is a defect
  against this user. **[stated]**
  **The contract is the declared telemetry, and fidelity lives below it (`PDR-0119`, owner,
  2026-08-24):** the interface a trained policy carries is the declared variable manifest
  (bounds and normalization included) plus the declared action vocabulary at its cadence — never
  the substrate. Train an agent to sail a ship on a coarse 2D surface and drop it into a
  high-fidelity naval simulation: *"the agent is seeing the same telemetry so it works
  seamlessly."* The compiled hashes are what make "same interfaces" checkable rather than
  hopeful. Engine bindings (Unreal, Unity, Godot) are acknowledged future scope, provided "when
  we're in a position where it's needed"; the export path (`hamlet-0cdb8a6d1a`) is
  vision-load-bearing and sequenced after the token migration, so it exports against the token
  ABI rather than the raster being retired. **[stated]**
- **Also served (downstream, not driving):** students and instructors using the pedagogical
  curriculum levels as a teaching artefact — now as *authors* rather than as players. Townlet Town
  serves them as the **first-class tech demo** (see Purpose): maintained to demonstrator standard,
  not left to rot, and bound by the dogfooding rule.
- **Explicitly not:** teams wanting a production RL training platform, an agent-serving runtime,
  or a general-purpose Gym-compatible environment zoo. Townlet optimises for expressiveness,
  authorability, and provenance over generality and stability.

## Anti-goals (what it refuses to be)

These are drawn verbatim from `CLAUDE.md` / `AGENTS.md` and the 2026-05-16 architecture report —
they are already binding project commitments, not new inventions.

- **Backwards compatible.** Pre-release, zero users, zero downloads. No fallbacks, no deprecation
  warnings, no migration paths, no "support both old and new." Old configs and checkpoints must
  fail loudly, not be accommodated. A compatibility shim is a defect.
- **A carrier of technical debt — at all, until 1.0 is declared.** *"I have a strict 'no tech debt'
  policy, until we declare 1.0 we aren't carrying tech debt **not even for RL work** — when we feel
  like we have something worth testing then we'll freeze and test properly."* **[stated]** The
  second clause is the load-bearing one: the exemption that research and ML codebases almost
  universally grant themselves — *it's only experimental code* — **does not exist here**. Nor does
  the deferral argument that a defect is currently unreachable; broken-but-unreached is still
  broken. The owner's worry states the cost concretely: *"I don't want to have 20 or 30 data
  migration pathways in our code base before we even have a single user."* Each one is defensible
  alone; the twentieth is the codebase. This anti-goal **generalises** the one above — backwards
  compatibility is the specific debt this project is most prone to, but the refusal is not limited
  to it. Debt is what is wired *wrong*: failing gates, declared-but-inert config surfaces,
  computed-but-unconsumed outputs, known-wrong docs, duplicate live-but-weaker code paths. It is
  **not** what is merely *absent* (an unbuilt option is `PDR-0007`'s "not yet enabled"), and it is
  **not** the "interesting failures" the anti-goal below protects — this refusal must never be
  cited to delete those. Rationale, edge cases, and the interaction with `PDR-0007`: `PDR-0012`,
  `PDR-0013`.
- **A producer of production-ready agents.** The goal is understanding and teachability, not SOTA
  policies or benchmark scores.
- **A bug-fixer of interesting failures.** Reward hacking and pathological emergent strategies
  (e.g. "Low Energy Delirium") are *artefacts to preserve and document*, not defects to patch out.
- **Implicitly defaulted.** The no-defaults principle holds: every behavioural parameter is
  explicit in config. Hidden defaults produce non-reproducible universes.
- **Two codebases.** `src/hamlet/` is obsolete legacy. Work happens only in `src/townlet/`.
- **Domain-aware in the runtime.** `VectorizedHamletEnv` must not name or branch on experiment
  semantics (trust, obligation, reputation, social residue). Domain meaning lives in compiled
  artefacts; the runtime stays experiment-agnostic. This is the load-bearing invariant of the
  substrate-as-code thesis.

## Authority grant

Granted by: John Morrissey (qacona@gmail.com)     Last reviewed: 2026-09-02
Review cadence: monthly, or on any vision change
Status: **CONFIRMED unchanged** by the owner on 2026-09-02. **The scope is NO LONGER identical
to the 2026-08-11 grant** — it was widened
twice on 2026-08-20, by `PDR-0099` (push `project-recovery*`) and `PDR-0101` (merge to `main`).
This paragraph previously read *"unchanged from the 2026-08-11 grant … scope identical every
time"*, which those two amendments had made false: the `Last reviewed` stamp was corrected at the
2026-08-20 touch but this prose was not, leaving the Status line contradicting both the amendment
log above it and the autonomous list directly below it. Corrected at the next approved touch, the
pattern `PDR-0038` and `PDR-0088` set. Re-confirmations before the widening (2026-08-14, the
2026-08-15 resume, twice on 2026-08-16 — the first that day preceding the stamp correction, per
the amendment log — and at each `/own-product` resume since, most recently at the 2026-08-19
resume that approved that stamp correction) were all scope-identical, and that enumeration is
preserved here deliberately — only the two false clauses were removed, not the provenance trail
the amendment log exists to carry. The 2026-08-20 confirmations are the first that are not
scope-identical. Read together with `PDR-0046`, `PDR-0099`, `PDR-0100` and `PDR-0101`: the agent may commit and
push `project-recovery*` **including checkpoint commits**, and **merge to `main`**, without
asking. `PDR-0039` gate 2 (the unconditional README re-verification, by method — sweep, draft from
verified facts, adversarial pass — never a re-read) is owed at **every** merge and is executed by
the agent, not waited on. **The merge is no longer the boundary.** What remains escalated:
declaring **1.0** / publishing a product offering (`PDR-0100`), *announcement* — telling people —
tags and releases, vision/strategy/grant changes, and data deletion.

Autonomous within strategy — the agent MAY, without asking:
  prioritize the backlog, write PRDs, dispatch delivery, accept against
  criteria, reprioritize, kill a failing bet per metrics.md,
  commit AND PUSH `project-recovery*` branches — checkpoint commits
  included (`PDR-0099`; supersedes `/product-checkpoint`'s blanket no-push
  rule for this product only),
  and **MERGE `project-recovery*` into `main`** (`PDR-0101`) — which still
  owes `PDR-0039` gate 2 unconditionally, now read as a QUALITY gate the
  agent executes rather than an escalation the agent waits on.

Escalate BEFORE acting — the agent MUST get owner sign-off for:
  changing this vision/strategy/grant, public release or announcement,
  deprecating a feature users depend on, pricing/commercial change,
  data deletion, anything touching an external party.
  (Taxonomy + rationale: product-ownership-operating-model.md.)

**Note on this product's specifics:** because Townlet is pre-release with zero users, the
"deprecating a feature users depend on" clause is currently near-vacuous — deleting code is
explicitly encouraged by `CLAUDE.md`. The clauses with real teeth here are *vision/strategy
change*, *announcement*, and *data deletion* — which for this product includes deleting `runs/`,
checkpoints, or recorded episodes that are experimental evidence.

**What "public release" means here — owner-defined 2026-08-20 (`PDR-0100`), and it is NARROWER
than this document previously assumed.** Publication means **publishing a product**: putting out a
coherent product offering for someone to adopt, which for this project means **declaring 1.0**.
The owner's words: *"I call publication declaring 1.0 — not making content available on the
internet"*, and *"publication => publishing a product and right now we don't have a coherent
product offering, just code."*

It follows that **code being visible on the internet is not publication.** The repository being
public at `github.com/foundryside-dev/hamlet`, pushing branches, and merging to `main` are not
release events under this grant — there is no product offering yet to release, only code. This
paragraph previously cited the repo's public status as what gave the release clause "real teeth";
that reading was the standing agent's, not the owner's, and it was **wrong**. It is corrected here
rather than left as a footnote, because it had been actively shaping how conservatively the agent
behaved.

*Announcement* is a separate limb and still escalates on its own: it covers **telling people** —
a blog post, a social post, a forum or mailing-list message, a submission to an aggregator — and
is about outward communication to external parties, not about whether code is readable. The
tech-debt anti-goal above is already scoped *"until 1.0 is declared"*, so this definition puts the
release clause on the same milestone the rest of the vision already turns on.
