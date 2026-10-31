# PRD-0001 methodology review — statistical-inference lens

Reviewer: Fable fork of the standing session, directed adversarial (full context, attacking
its own instrument). Dispatched 2026-08-18 at the owner's direction; delivered same day.
Adjudication: `PDR-0086`. Archived verbatim below.

---

Directive restated: adversarial statistics/experimental-inference review of the PRD-0001 instrument (corpus, draw, protocol, four completed trials, north-star row) — what does the reading actually license, why are the predictions miscalibrated, and where do the decision rules mislead.

I re-read `0001-measure-the-authoring-claim.md`, `0001-corpus-FROZEN.md` (draw protocol + all Predict lines), the L/F/M/O trial records, and the metrics north-star row.

# Review: PRD-0001 instrument — findings, severity-ranked

## 1. HIGH — Construct validity: the instrument measures *expert any-surface expressibility*, not the *novice authorability* the metric is named for

The north-star is "Zero-Python **authoring** rate," and `vision.md`'s standard is the novice author. But every one of the four PASSes was produced by a substrate expert reading engine source to find a surface that works: L found `depletion.passive: -1.0` only after the obvious declaration (`recovery.natural`) proved INERT and after reading `capability_config.py`; M knew to reach for event-trace meters after establishing custom actions are structurally empty; O read `executor.py`/`collections.py` to discover `for_each: all_agents` and the scope hardcode before writing a line of YAML. Three of four passes ride a *second* surface located via source archaeology; arguably zero of four passed on the surface an outside author would reach first. A skeptic can truthfully say: "the novice-authorability metric was scored by the substrate's own builder, who needed the source code four times out of four." The number is real; the label invites over-claim.

**Cheapest fix (no unfreeze, no voids):** an interpretation preamble bound to every published reading stating the construct ("expert executor, any declarative surface, session budget, pinned commit"), plus a secondary count *derivable from the existing records with no new trials*: per idea, (i) did the PASS require consulting `src/` to find the winning surface, and (ii) did the first-reached surface work. Pre-register that annotation now, before trial five, so it covers the remainder prospectively.

## 2. HIGH — The INERT escalation clause is structurally biased toward zero and can likely never fire

Criterion 5 counts **ideas that miss with an INERT facet** (threshold 3). But the four trials show the standing pattern: the executor hits a live INERT surface, finds a workaround, the idea PASSes, and the counter stays 0. Four trials in, the by-catch register already holds real INERT/dead surfaces — `recovery.natural` (declared-required everywhere, read nowhere), `CapabilityConfig` (purpose-built cooldown surface reachable from no YAML), effect `scope: global` (validated, silently spawned agent-scoped) — and the escalation counter reads **0**. The clause exists to detect "the substrate says yes and means no"; the evidence shows the substrate *does* say yes-and-mean-no on first surfaces, and the counter is blind to it precisely when the executor is good at workarounds. The better the executor, the safer the vision question looks — an instrument whose alarm is suppressed by the skill of its operator.

**Cheapest fix:** do not move the pre-committed threshold mid-flight. Instead publish the **INERT by-catch count** beside the idea-level counter in every reading (it is already in the tracker; this is one sentence in the metrics row), and record a PDR noting the clause's blind spot so the owner reads "INERT ideas: 0" alongside "INERT surfaces encountered: 2 in 4 trials."

## 3. MEDIUM-HIGH — Sampling frame: the corpus represents substrate-aware idea generation, and the widest claim a 9/9 supports is narrower than the metric's phrasing

The 15 ideas were generated in one session by two parties who both know the substrate deeply. The anti-bias machinery (named external sources, origin labels, mechanical stratified draw, pre-registration) defends against *pool-to-set* cherry-picking and post-hoc scoring — it cannot defend against the **pool itself** being drawn from the space of mechanics thinkable in this substrate's ontology (meters, affordances, effects, positioned agents). The bucket taxonomy is endogenous too: seven axes defined by the corpus author around the ideas that existed, with social-economic holding 5 of 15. The corpus does contain ontology-breakers (B's entity-that-is-not-a-position, A's physics) — but note the four *completed* trials all sit inside the meter/affordance/effect comfort zone; the ontology stress is concentrated in what remains. The PRD discloses this joint honestly ("residual selection bias is the number's weakest joint"), which is to its credit — but the disclosure lives in the PRD while the number will live in the metrics row.

**Widest supportable claim from 9/9:** "of mechanic ideas conceived by this owner and agent, anchored to well-known external sources and sized to a one-session pack, all nine were expressible zero-Python by an expert at the pinned commits." Not "a representative new mechanic idea authors zero-Python with ~90% probability." And the binomial arithmetic bounds even the internal claim: 9/9 gives a 95% Clopper-Pearson lower bound of ~0.66; 8/9 gives ~0.52. **Fix:** carry the frame statement into the published reading; for the next corpus revision (the candidates file is the vehicle), add a stratum of ideas taken verbatim from a substrate-naive published source (e.g., a standard game-mechanics taxonomy) — cheap and it directly attacks this bias.

## 4. MEDIUM — Prediction miscalibration: the mechanism is (a) first-surface vs any-surface, concretely instantiated as (b) underweighting the effects command language

Diagnosis against the record: all three falsified predictions (L, M, O) named *real* gaps — the predicted-missing surfaces genuinely are missing or inert (all filed as by-catch). The predictions failed because they scored **first-surface reachability** while the protocol scores **any-surface reachability**, and the gap between the two is almost entirely one subsystem: the general-purpose effects command language (`modify`/`if`/`for_each`/`reduce` over the full meter+VFS state) rescued every falsified trial. (c) — "the corpus sits in the sweet spot" — is not the operative mechanism for these four: the ideas hit real gaps and passed anyway. So the ledger is not wrong about the substrate's holes; it is a map of named, purpose-shaped surfaces, and the substrate's measured authorability is substantially *the expressive power of one escape hatch*.

**Implication for the remaining five:** the structural predicted-FAILs for D/E/J deserve a Bayesian discount, because O already falsified their shared sub-premises in principle — cross-agent writes *are* declarable (O's clearing effect writes other agents' meters), simultaneous collection works, durable shared world state is emulable via global VFS. The genuinely untested structural claims now reduce to: inter-inventory item transfer (D, J), per-agent heterogeneous action sets and `agent_private` liveness (E), zone/equip mitigation (K), and the one true ontology mismatch — B's entity-as-set-of-cells, which no command vocabulary patches. If the remaining trials also pass via increasingly baroque effects-language emulations, the reading must say so (finding 1's annotation captures this); "authorable" and "emulable by an expert in the escape hatch" are different products.

## 5. MEDIUM — The 8-of-9 bar has coin-flip operating characteristics near the threshold

At N=9, one idea is 11.1 points. A substrate whose true per-idea rate is exactly 0.8 *misses* the bar 56% of the time (P(X≥8 | p=0.8) ≈ 0.44); at true p=0.9 it still misses 23% of the time. `PDR-0078` already defused the worst use (the bar no longer gates the bet), but the metrics row still renders "≥80% — 8 of 9 by 2026-10-06" in a way that reads as pass/fail. **Fix:** publish the fraction, the split, and a one-line width caveat ("N=9: one idea moves the rate 11 points"); treat the corpus's standing note — the same 15 ideas re-scored after WS-4 lands — as the real signal (trend), not the single reading against the bar.

## 6. MEDIUM — The blind re-run checks reliability between *correlated* executors and is quietly weakest exactly where the instrument is strongest

What it detects: protocol/corpus ambiguity, verdict-derivation error, and surface-finding luck — note L's blind re-run could *legitimately* disagree (a blind executor who never finds the negative-depletion trick scores L INERT), which would be the check working. What it cannot detect: shared bias. Both executors are Claude agents with the same training, reading the same Spec text and the same source tree — correlated facet-enumeration and identical workaround-finding pass the check while telling you nothing about validity (finding 1). Also underspecified: who the comparer is (in practice the standing agent risks being executor, comparer, and adjudicator), and nothing requires the two chosen re-runs to include a hard case. **Cheapest strengthening:** the owner picks the two trials; at least one is a second-surface-dependent PASS (L or O), not F; and the comparison records the *surface path*, not just the verdict — same headline reached via a different surface is a protocol-looseness finding even when the verdicts agree.

## 7. LOW — Two specification loose ends

(i) An idea missing on multiple facets with mixed classes (one ABSENT + one INERT) has no stated rule for the idea-level classification that feeds the split and the escalation counter — unexercised so far, cheap to clarify in a dated appendix. (ii) The protocol is ACTIVE but not frozen; criterion 3 says blind re-runs run "against this document." Any protocol edit between a first run and its blind re-run contaminates criterion 3 — the appendix should state that blind re-runs use the protocol text as of the first run's pin. (iii) Cosmetic: PRD line 71-75 contains a garbled mid-edit sentence in the aggregate-prediction paragraph ("…that is chance doing its job, not a thumb on the scale on the binary headline unit (F and H, possibly A)") — an editing artifact worth acknowledging since that paragraph *is* the pre-registration text.

## Q5 answered directly

**Most damaging valid criticism:** publishing "8 of 9 by 2026-10-06" under the name "Zero-Python authoring rate" claims novice authorability while the evidence is expert any-surface expressibility, scored by the substrate's own builder who consulted engine source in every trial. It flips the headline's meaning, and it is entirely true.
**Cheapest defusal:** the finding-1 package — construct preamble on the reading + the source-consultation/first-surface annotation derived from the four existing authoring logs, pre-registered before trial five. No corpus edit, no voided trials, roughly an hour of work.

---

**Confidence:** High on findings 1, 2, 4 (directly evidenced by the four records and the by-catch register); Medium-high on 3 (the bias is structural and partially disclosed; its *magnitude* is unmeasurable from inside); High on the arithmetic in 5; Medium on 6 (depends on who actually runs the blind sessions).

**Risk if ignored:** the first published reading gets quoted as "the substrate is ~90% novice-authorable," the INERT counter's silence gets read as "the substrate never lies to authors," and both claims are one skeptical reader away from a public correction on a repo that is already public.

**Information gaps:** I did not re-derive the draw (seed → sequence) computationally; I could not assess how a genuinely substrate-naive author performs (no such trial exists — that is finding 1's point); F's authoring log was reviewed via its PDR/metrics summaries rather than line-by-line.

**Caveats:** I built and ran this instrument; the review compensates by attacking, but shared-author blind spots may remain — finding 6's correlated-executor critique applies to this review too. Nothing here voids the four verdicts: within its actual construct (expert, any-surface, pinned commit), the 4-of-4 reading is clean, pre-registered, and honestly recorded — the findings are about what it *licenses*, not whether it happened.
