# PRD-0001 — Measure the authoring claim: the frozen corpus and the trial protocol            Status: ready-for-planning

Decision: `PDR-0077` (the owner chose this bet at the 2026-08-17 resume; the PDR is recorded at
this session's checkpoint, so the provenance is owed, not missing)
Bet (`roadmap.md`): **Next → promoted to Now** at this session's `DECIDE` — a reprioritization
within the authority grant, recorded as roadmap intent at checkpoint. It runs *alongside* the
strangler bet, not instead of it.
Target metric (`metrics.md`): north-star — **Zero-Python authoring rate (world)**
Corpus: **`0001-corpus-FROZEN.md`, frozen 2026-08-17**
SHA256: `48840cc3ae62e381e0a96a6e850e3cc2fd309081b00bcbd8974cd9d58de935d9`
Protocol: **`0001-trial-protocol.md`, ACTIVE 2026-08-18** — criterion 3's blind re-runs run
against this document and the corpus, nothing else.
Tracker: `hamlet-5fa1f7bfc0`

> **Amended 2026-08-17, before any trial ran** — the only legitimate window to move a
> pre-committed target. Two changes, both owner-decided: (1) `N = 5 → N = 9` after the owner
> riffed the seed corpus, date `2026-09-15 → 2026-10-06`; (2) **≥80% is no longer this bet's
> pass/fail.** The original wording conflated *does the instrument work* with *does the substrate
> score well*, which would have made an honest instrument reporting bad news look like a failed
> bet — and rewarded picking an easy corpus, the exact gaming this design exists to prevent.
> The bet is now accepted on the instrument; ≥80% is the standing bar on the metric.
>
> **Third amendment, same session, owner steer** — *"it's not necessarily a huge problem if there's
> a gap, it's just a gap."* Correct, and the scoring did not reflect it: a binary FAIL lumped
> *no surface exists* together with *a surface exists and lies*. Criterion 4 now classifies every
> miss ABSENT / INERT / BLOCKED, and the escalation clause in criterion 5 retargets from the raw
> rate onto the INERT count.

## Problem

**Who.** The primary user (John, the researcher this substrate serves) and, standing behind him,
the aspirational **novice author** — the person with a mechanic idea and no RL engineering
background whom `vision.md` names as *"the standard the substrate is judged by."*

**The problem.** The product's central claim — *someone with a cool idea for a game system can
turn it into a working DRL gym trivially* — **cannot currently be tested, only argued.** Two
trials have run and neither produces a rate: Trial 001 scored a whole idea (`1 of 1`), Trial 002
scored halves (`3 of 4`), and the two numbers are **incomparable to each other** because no
scoring unit was ever defined. There is no denominator, so there is no fraction; `metrics.md`
says so itself — *"still not a rate: the corpus is undefined."* The consequence is not academic:
every bet that claims to serve authorability is accepted on argument, and the one number that
could falsify the thesis has never been readable.

**Desired outcome.** A **defensible rate with a stated denominator**, produced by a protocol
someone other than its author can re-run and get the same verdicts from — so that "the substrate
is authorable" becomes a claim that can be *wrong*.

**Why now.** Twenty-six checkpoints have landed WS-4 units against an *input* metric
(`Config-surface coverage`) while the north-star sat unread, and this bet has carried
*"tracker: not yet filed"* at the top of Next for the whole of it. Shipping units against a proxy
while the outcome metric stays unreadable is the build trap in its exact textbook shape. The
instrument is what stops it.

## Success metric (the signal the bet paid off)

**Zero-Python authoring rate (world)** — of the frozen corpus, the fraction of ideas expressible
as a config pack alone with **zero lines changed under `src/townlet/`**.

- **BASELINE:** *not a rate.* Two hand-run existence proofs on different, undeclared scoring
  units (Trial 001 `1 of 1` whole-idea; Trial 002 `3 of 4` facets). No denominator, not
  reproducible, not comparable.
- **This bet's success:** the metric becomes **readable** — a first defensible reading over the
  frozen N=9 corpus, with its denominator and scoring unit stated, by **2026-10-06**.
- **The standing bar on the metric (not this bet's gate):** **≥ 80% — 8 of 9** (7 of 9 is 77.8%
  and misses). This is what the substrate is measured against over time; the first run
  establishes where it actually stands.
- **Every reading reports the ABSENT / INERT / BLOCKED split alongside the rate.** The fraction on
  its own is not the finding; the split is what says whether a miss is a build item or a defect.

**Pre-registered aggregate prediction, recorded 2026-08-17 before any trial:** over the drawn
nine I expect **1, possibly 2, to pass** — F, and at best K's pressure facet — against a standing
bar of 8. Over the full 15-idea pool I expected 2–3. The draw landed harder than the pool; that is
chance doing its job, not a thumb on the scale on the binary headline unit (F and H, possibly A). Recording this makes my own read
falsifiable alongside the substrate's, and if the first reading lands far above it, the corpus is
the first thing to doubt.

## Acceptance criteria (falsifiable)

1. **INSTRUMENT — the corpus is frozen before it is used. ✅ MET 2026-08-17**, a week early. A
   pool of **15** headline ideas is frozen in `0001-corpus-FROZEN.md` at SHA256
   `48840cc3…8de935d9`, and the trial set of **N = 9** was drawn mechanically from it (record
   below). Each idea states its **named external source**, its **origin** (agent-drafted /
   owner-riffed / owner-supplied), its axis bucket, and its pre-registered prediction: each states its **named external source**,
   each records its **origin** (agent-drafted / owner-riffed / owner-supplied), and the file is
   committed and content-hashed before any trial executes. Idea **B is one entry**, scored on the
   5-D warehouse variant, with B1/B3 recorded as diagnostic facets — three variants of one source
   must not inflate the denominator's apparent diversity.
   *Reject branch:* a trial run against an unfrozen corpus, or one edited after any trial began,
   is **void** — it enters neither numerator nor denominator, and the reduced denominator is
   stated in the reading.

2. **INSTRUMENT — every trial is pre-registered.** For each idea, a **predicted verdict**
   (authorable yes/no, and which facets are predicted to fail) is written into the frozen corpus
   **before** that trial executes. This is Trial 002's own discipline made general: `PDR-0047`
   predicted two failures, the trial **falsified one of them**, and that is precisely what made it
   evidence rather than a demonstration.
   *Reject branch:* a verdict recorded without a prior prediction is **void** and reported as
   void, with the denominator reduced accordingly.

3. **INSTRUMENT — the protocol is reproducible by a second executor.** By **2026-10-06**, **2 of
   the 9** trials are re-run blind (a fresh session with the protocol and the corpus, without
   access to the first run's verdicts) and reproduce the **same verdict on both**.
   *Reject branch:* any verdict disagreement → the protocol is underspecified, the instrument is
   **not accepted**, and no north-star reading is published from it.

4. **METHOD — both legs, every trial, no exceptions.** A trial passes only when **both** are
   recorded: (a) `git diff --stat src/townlet/` is **empty**, and (b) the declared thing is
   **observable** in the compiled artifact or the encoded observation. Leg (b) is not optional
   politeness — Trial 002 found `range_type` *declared, accepted, and provably inert*, which leg
   (a) alone would have scored as a **false pass** on the single most important finding of that
   trial.
   *Reject branch:* a leg-(a)-only pass is recorded as **FAIL**, not as partial credit.

   **Every non-PASS verdict is classified**, because a miss is not one thing:
   - **ABSENT** — no declarative surface exists. This is `PDR-0007`'s *"not yet enabled"*. It is
     explicitly **not** debt: `vision.md`'s anti-goal names what is wired *wrong*, not what is
     merely absent. Routes to WS-4 as a feature.
   - **INERT** — a surface exists, validates, and does nothing observable: leg (a) passes while
     leg (b) fails. This **is** debt, it is the worst failure mode for a declarative product, and
     it is exactly what Trial 002 found in `range_type`. Routes as a defect.
   - **BLOCKED** — declarable in principle, fails loudly (compile error, crash, unreachable). The
     loudness is the good news; `Failure loudness` is its metric.

   A reading of 3 of 9 whose misses are ABSENT describes a young substrate with a build list. The
   same 3 of 9 whose misses are INERT describes a substrate that tells authors *yes* and means
   *no*. Same number, different product — and the bare fraction cannot tell them apart.

5. **READING — the metric becomes readable.** By **2026-10-06** the `metrics.md` north-star row
   carries a rate over the frozen corpus, stating its denominator, its scoring unit (binary
   headline per idea, facet detail underneath), and the commit each trial ran against.
   *Reject branch:* no defensible reading by that date → **the bet is rejected** and a follow-up
   PDR records why. **A reading below ≥80% does NOT reject this bet** — the instrument did its
   job; the number is the finding, and every gap it names routes to WS-4.
   *Escalation clause — retargeted onto INERT, not the rate:* **3 or more** of the corpus's ideas
   failing with an INERT facet is escalated to the owner as a question about `vision.md`'s central
   claim, because that is the substrate telling authors *yes* and meaning *no*. **A low rate whose
   misses are ABSENT does not escalate** — it is a roadmap, not a crisis. I do not write the vision
   conclusion myself; a vision change is outside the grant.

6. **GUARDRAIL — `Gates green` must not degrade.** The trial packs live under `configs/` and are
   reached by the config-validation gate; the full suite and all gates stay green at every commit
   of this bet, on the same hides-nothing basis `PDR-0059` established.
   *Reject branch:* breached → the bet is **rejected even if criterion 5 passes**.

7. **GUARDRAIL — `Pre-release hygiene` (target 0) must not degrade.** Every trial pack, pass or
   fail, is either promoted to a regression fixture or deleted by **2026-10-06**. The measurement
   does not get to leave litter behind, and the anti-goal *"a carrier of technical debt — at all,
   until 1.0"* has no research exemption.
   *Reject branch:* orphan trial packs outstanding on that date → guardrail breached.

## Draw record (auditable — re-run it and check)

**Pool:** 15 ideas, frozen at SHA256 `48840cc3ae62e381e0a96a6e850e3cc2fd309081b00bcbd8974cd9d58de935d9`.
**Seed:** that digest as an integer — a pure function of the frozen file, chosen by nobody.
**Method:** buckets in alphabetical order, one idea drawn from each (the per-axis floor), then two
more from the remainder. Protocol and buckets are in the frozen corpus itself.

| step | result |
|---|---|
| per-bucket floor | action-structure **M** · contention **O** · environmental **K** · items **F** · physical **B** · social-economic **E** · temporal **L** |
| two free draws | **D**, **J** |
| **trial set (N = 9)** | **B, D, E, F, J, K, L, M, O** |
| held in pool | A, C, G, H, I, P |

**The draw is harder than the pool, and it excluded both ideas I predicted would pass most
easily** — H (queueing) and A (momentum) are both held back, while four of my five FAIL
predictions were drawn in. Had I chosen the nine, I would not have chosen these. That is the
mechanism working as designed, and it is the single strongest thing this instrument can say about
its own honesty.

**Consequence to expect:** a first reading near **1 of 9 (11%)** against a standing bar of 8 of 9.
Under criterion 4's taxonomy most of those misses should classify **ABSENT** — surfaces nobody has
built — which is a build list, not a crisis. The escalation clause watches the **INERT** count, and
I predict 1–2 (L, possibly M), below its threshold of 3. If INERT comes back at 3 or more, that
prediction failed and the vision question goes to the owner.

## Non-goals (this bet)

- **Fixing anything the corpus finds.** This bet *discovers and measures*. Each gap is filed and
  routed to WS-4; repairing one inside this bet would contaminate the reading it is taking.
- **Retro-scoring Trials 001 and 002 into the denominator.** They were not pre-registered against
  this scoring unit and their answers are already known. They inform the protocol; they do not
  enter the fraction.
- **The mind axis (BAC).** `metrics.md` separates world-authoring from mind-authoring on purpose,
  so one failing half cannot hide behind the other. Unchanged here.
- **Export cost.** The prototyping modeller's metric is its own row and its own bet.
- **Automation.** At N=9, hand-run against a written protocol is sufficient. A trial harness is a
  solution to a problem this bet has not yet demonstrated.

## Constraints & guardrails

- **The instrument must not require engine changes to operate.** A measurement that needs
  `src/townlet/` edits cannot measure a zero-`src/townlet/`-diff claim.
- **Each trial pins the commit it ran against.** The substrate moves underneath the corpus while
  WS-4 lands units; a verdict without a commit is not a verdict.
- **Source diversity is mandatory**, and is the corpus's defence against a shaped pool: every idea
  names an external source, and sources must be genuinely varied rather than variations on one
  theme. B's three variants are one source and are scored as one entry for exactly this reason.
- `Gates green` and `Pre-release hygiene` are the two guardrails, per criteria 6 and 7.

## Open questions / assumptions

- **Residual selection bias is the number's weakest joint.** The owner's *"I draft, you riff"*
  is materially better than draft-and-veto — a veto only subtracts from a pool I shaped, while a
  riff can add the idea I failed to think of, and it did: 2 of 9 ideas are owner-supplied and 3
  more owner-riffed. The per-idea origin record is what lets a skeptical reader check this rather
  than take it on trust.
- **The substrate drifts under the corpus.** If a late trial passes only because an intervening
  WS-4 unit landed, the reading is a blur unless stated per trial. A ~7-week window is longer than
  the original 4; the per-trial commit pin (above) is what keeps it readable, and if WS-4 lands
  something large mid-window that is a fact for the reading, not a spoiler for it.
- **At N=9, ≥80% means 8 of 9 — a single failure is nearly the whole budget** against a corpus I
  predict will fail 6 or 7 of them. That gap between bar and expectation is intentional now that
  the bar no longer gates the bet: it measures distance to the claim rather than grading the work.
- **My own framing needed this correction more than the document did.** I had been reading a
  predicted 2–3 of 9 as bad news. Under the taxonomy most of those misses are ABSENT — B, D's
  transfer half, E — which for a pre-1.0 substrate mid-strangler is a build list, not an
  indictment. The reading to actually watch is the INERT count, and I currently predict it is
  **low**, because the strangler has been converting inert surfaces into live ones for
  twenty-six checkpoints. If INERT comes back high, that prediction is the one that failed.
- **Binary scoring reads 0 for ideas that are 90% authorable.** Deliberate — a novice author who
  must write Python has been stopped — but facet detail is recorded so the loss is visible.
- **Idea I overlaps the dropped "shop hours" seed's known gap** (no world clock in effect
  expression scope). Kept on purpose: it reaches that gap through a mechanic someone actually
  wants, which is a far stronger argument for fixing it than a synthetic probe.
- The `PDR-0077` deciding this bet is written at checkpoint; until then this PRD's provenance is
  owed.

## Handoff

- **Top item → `/axiom-planning`:** *the instrument* — the written trial protocol plus the frozen,
  pre-registered N=9 corpus artifact. Not the trials; they are the instrument's output and are
  sequenced after it exists.
- **`/axiom-solution-architect`: not routed, deliberately.** This bet produces a protocol document,
  a corpus file, and trial packs under `configs/`. There is no component design and no ADR to
  make; routing it anyway would be ceremony.
- **`/axiom-program-management`:** owns sequencing against the WS-4 queue and any dated forecast.
  **2026-10-06 is the falsification window, not a delivery commitment** — the date by which the
  reading must exist for the bet to be judged.
- **Tracker:** `hamlet-5fa1f7bfc0` (P1 task, parent milestone `hamlet-1ade187dcc`), filed
  2026-08-17.
