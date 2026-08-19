# PRD-0001 methodology review — construct-validity lens

Reviewer: `product-decision-critic` agent on Fable, fresh context (reads the artifacts cold).
Dispatched 2026-08-18 at the owner's direction; delivered same day.
Adjudication: `PDR-0086`. Archived verbatim below (JSON findings block + prose sections).

---

# Red-Team: Construct Validity of the PRD-0001 Measurement Instrument

```json
{
  "summary": {"high": 2, "med": 3, "low": 3},
  "authority_boundary": "CLEAR",
  "findings": [
    {
      "severity": "high",
      "anti_pattern": "Construct substitution (vanity-metric variant: the number measures the easier thing)",
      "question": "did-it-work",
      "sheet": "product-metrics-and-experimentation.md",
      "location": "0001-trial-protocol.md §5; trials L/F/M/O authoring logs; metrics.md north-star row",
      "evidence": "Protocol §5 allows 'reading anything — source, docs, schemas'. Trial O's authoring log opens with 'Recon before authoring' citing src/townlet/effects/executor.py:228-231 by line number; Trial L passes only via depletion.passive: -1.0 (a negative drain repurposed as an incrementing timer) after the obvious declaration (recovery.natural) proved INERT; Trial M passes only after reading two engine config modules to rule out the actions surface. Every PASS but F is a second-surface pass found by source archaeology. The verdicts are then published in vision vocabulary: 'cooldown management is fully authorable'.",
      "failure_mode": "The metric as operationalized measures EXPRESSIBILITY — does at least one declarative path exist, findable by an expert with unbounded source access — while the vision claim it is cited against is AUTHORABILITY: a novice with no RL background does it 'trivially'. The instrument yields an upper bound (ceiling) on the claim, and the readings are being narrated as readings of the claim itself.",
      "remediation": "Reframe, don't rerun: label the metric 'zero-Python expressibility (expert ceiling)' and state authorability ≤ this in metrics.md. The data to close most of the gap already exists — each authoring log records HOW the winning surface was found; classify every PASS by discovery path (docs-reachable / error-message-guided / source-reading-required) and report that split alongside ABSENT/INERT/BLOCKED. See product-metrics-and-experimentation.md (decision-utility: a novice-authorability claim needs a reading a novice's failure could produce)."
    },
    {
      "severity": "high",
      "anti_pattern": "The acceptance gap, at facet granularity (pre-commitment binds evidence, not interpretation)",
      "question": "did-it-work",
      "sheet": "prd-and-acceptance-criteria.md",
      "location": "Trials F facet 3, L facet-reading preamble, M facet-reading preamble, O facet 3",
      "evidence": "F: corpus Spec says the item 'eventually breaks'; the executor's facet 3 accepts 'destroyed/removed OR its use is refused, whichever the pack declares' — and the authoring log then confirms no despawn/destroy command exists. Under the Spec's plain reading F is PARTIAL, i.e. headline FAIL — and F is the corpus's single predicted-PASS. L: 'per-affordance state' narrowed pre-authoring to 'two hand-declared meters is acceptable'. M: 'action' read as 'any agent-performable operation', pre-authorizing the affordance workaround after the actions surface was known-dead. O: artifact evidence accepted in 'whatever form it takes', and the pre-committed inspect check was substituted mid-trial (disclosed).",
      "failure_mode": "Facet enumeration is done by the same party that executes, minutes before authoring, holding total engine knowledge. The append-only rule prevents post-hoc editing but nothing constrains the granularity or Spec interpretation chosen at write time — and the four records show interpretation consistently resolving toward the passable form. One of the four headline PASSes (F) plausibly flips on this alone.",
      "remediation": "For the five remaining trials: have facet lists and Spec interpretations enumerated (or countersigned against the corpus Spec) by a session that will not execute the trial — the owner or a fresh instance — before authoring begins. Record F's 'breaks→stops-working' reading as an open adjudication question to the owner rather than a settled PASS input. See prd-and-acceptance-criteria.md (a criterion is falsifiable only if its interpreter cannot move it)."
    },
    {
      "severity": "med",
      "anti_pattern": "Predictor–executor identity: pre-registration doing narrative work, not prior work",
      "question": "did-it-work",
      "sheet": "product-metrics-and-experimentation.md",
      "location": "0001-corpus-FROZEN.md predictions; PDR-0082/0084 'prediction vs actual' sections",
      "evidence": "PDR-0082 admits the mismatch outright: 'predictions were made against the first surface an author would reach, not against the space of declared surfaces.' The trials then search the space. Given that mismatch, falsifications-toward-PASS are near-guaranteed wherever second surfaces exist — yet PDR-0084 narrates the aggregate falsification as 'the prediction machinery has been systematically pessimistic about the substrate', a positive substrate finding.",
      "failure_mode": "A prediction by the executor about its own future search is partly a prediction about search effort, not the substrate. Each falsification is ambiguous between 'substrate better than believed' and 'executor searches harder than the prediction assumed' — and the congratulatory reading is the one being written down. The pre-registration IS doing real work (falsifications are stated not smoothed; PDR-0078 removed the incentive to game the rate for bet acceptance; the draw excluded the two easiest ideas), but as a diagnostic prior on the substrate it is close to theatre.",
      "remediation": "Make falsifications diagnostic by pre-registering the SEARCH, not just the verdict: for the remaining trials, write down before authoring which surfaces will be tried and in what order (O's record shows this is natural to do). A PASS on a pre-named surface confirms; a PASS on an unlisted surface is scored as 'found by search', a separate line. Report the surface-level prediction record (first-reach predictions are running ~4-for-4 correct) alongside the headline record — that separation is the actual finding."
    },
    {
      "severity": "med",
      "anti_pattern": "Blind re-run design: undefined comparer, prediction anchoring, misattributed disagreement, low power",
      "question": "did-it-work",
      "sheet": "delivery-orchestration-and-acceptance.md",
      "location": "0001-trial-protocol.md §7; PRD criterion 3; PDR-0081 call 3",
      "evidence": "§7: the two trials are 'chosen by the comparer (whoever adjudicates)' — the comparer is nowhere defined, and all four executions to date are the standing agent, so the executor-doesn't-choose clause is currently void in practice. The blind executor reads the frozen corpus, which CONTAINS the predictions — blind to the verdict, anchored on the prediction. And the reject branch attributes ANY disagreement to 'the protocol is underspecified', when the four records show PASS verdicts hinge on finding a non-obvious second surface within one session (O's renew-effect construction): a blind executor who fails to conceive it returns FAIL through search variance, not protocol ambiguity.",
      "failure_mode": "Three distinct problems: (1) if the standing agent is comparer, it can select the two most mechanically reproducible trials (F is near-deterministic; O is not) — the reproducibility check checks the checkable; (2) 2-of-9 with an any-disagreement-kills branch is a smoke test, not a reproducibility measurement — at a 20% per-trial disagreement rate it catches a defect ~36% of the time, and when it does fire it cannot distinguish protocol underspecification from search-dependence; (3) a same-model expert re-run tests nothing about the novice construct in any case.",
      "remediation": "Owner (not the standing agent) selects the two, with at least one drawn from the falsified-prediction, second-surface passes (L, M, or O) — those are where reproducibility is actually in doubt. Add an adjudication step to §7 distinguishing 'executors read the protocol differently' (instrument defect) from 'executors found different surfaces' (a finding about search-dependence of the construct — which feeds finding 1). This is a critique of the acceptance design, not the sequencing; mechanics beyond that route to /program-management."
    },
    {
      "severity": "med",
      "anti_pattern": "Vanity-shaped interim reporting: executor-ordered trials make the running rate maximally favorable",
      "question": "did-it-work",
      "sheet": "product-metrics-and-experimentation.md",
      "location": "Trial F/M/O selection notes; metrics.md north-star row; commits 790dcb7e, 8954e604",
      "evidence": "Idea order is 'the executor's one degree of freedom' and the selection notes are explicit: M chosen partly because it is 'single-agent and compact' while multi-agent ideas 'risk a budget-limited record'. The easy half runs first by the executor's own stated criteria, and each checkpoint headlines the running number — commit subjects read 'north-star 3 of 3, split 0/0/0', metrics.md Trend shows '↑' on a metric its own caveat says has not published.",
      "failure_mode": "A running k-of-k over an easiest-first ordering can only look perfect early and is not a reading of anything; carrying it as the headline of five consecutive commits builds a '100% so far' narrative the final 9-trial number must then fight. Mitigations exist in the fine print (PDR-0084 notes the passes are all single-agent; the 'no reading publishes' caveat stands) — but the headline is doing the opposite of the fine print.",
      "remediation": "Report interim state as 'k of 9 settled, 9−k pending' rather than 'k of k', drop the Trend arrow until the denominator is exhausted, and stop putting the running rate in commit subjects. The final reading is immune to ordering; the interim narration is not."
    },
    {
      "severity": "low",
      "anti_pattern": "Decision-without-provenance: the construct's most load-bearing free parameter was defaulted, not decided",
      "question": "continuity of why",
      "sheet": "product-state-and-continuity.md",
      "location": "PDR-0081 (four design calls); protocol §5",
      "evidence": "PDR-0081 records four protocol design calls with rationale and reversal triggers — commit pinning, untracked files, session budget, BLOCKED semantics — but the allowance that defines what the metric measures ('reading anything — source, docs, schemas' by an executor who maintains the engine) appears in §5 with no PDR, no options considered, no reversal trigger. Contrast corpus idea B, which explicitly asks 'whether an author could reach it' — the question was visible at corpus time and never became a decision.",
      "failure_mode": "The expert-executor/full-source operationalization is the single choice finding 1 turns on, and there is no record that it was chosen over alternatives (docs-only authoring; discovery-path recording) rather than inherited from how Trials 001/002 happened to be run.",
      "remediation": "Write the PDR now, honestly dated: context (it defaulted), the call (expert ceiling, deliberately), and a reversal trigger (e.g. 'if the discovery-path split shows a majority of PASSes require source reading, the metric is relabeled and a docs-reachable row is added')."
    },
    {
      "severity": "low",
      "anti_pattern": "Instrument-integrity smell: a trial record drafted with invented content before execution",
      "question": "did-it-work",
      "sheet": "delivery-orchestration-and-acceptance.md",
      "location": "PDR-0084 'Rationale for accepting the verdict'",
      "evidence": "'the record was initially drafted with placeholder results and an invented authoring log; the error was caught and blanked before any authoring began'. Disclosed, and the pre-commitment held in substance.",
      "failure_mode": "The disclosure is to the instrument's credit, but it demonstrates the record-writing pipeline can produce a completed-looking record ahead of reality, and only the same executor's self-catch stood between that draft and the archive. With no independent comparer yet appointed (finding 4), self-catch is the only control in the loop.",
      "remediation": "Add to the TEMPLATE a rule the near-miss implies: no verdict-section text may exist before the corresponding command output does. Cheap, mechanical, and it converts the self-catch into a protocol property."
    },
    {
      "severity": "low",
      "anti_pattern": "Verification is expert-only: leg-(b) probes are hand-written Python against internal APIs",
      "question": "did-it-work",
      "sheet": "product-metrics-and-experimentation.md",
      "location": "F authoring log step 7; probe scripts in trial packs; F by-catch hamlet-6f27878731",
      "evidence": "Trial F's probe reads vfs_registry.item_vfs[vfs_index, item_profile_map[profile][var]] — internal registry indexing no author-facing surface exposes. Trial F also found docs/config-schemas/items.md wrong 'in three load-bearing places' and sailed past because the executor knows the real schema.",
      "failure_mode": "Legitimate for measurement (probes are instrumentation, not authoring) — but it means even VERIFYING that an authored mechanic works requires expert Python, and the stale-docs by-catch is direct evidence that the docs-only path a novice would walk is broken in ways the instrument is structurally unable to score. This is corroborating evidence for finding 1, filed separately because it is independently checkable.",
      "remediation": "No protocol change needed; count the docs by-catch as construct evidence, not just a docs bug — it belongs in the discovery-path split finding 1 proposes."
    }
  ]
}
```

## Executive summary

The instrument is far better than typical practice — frozen hashed corpus, mechanical draw that excluded the executor's two easiest picks, two-leg verdicts with a real INERT taxonomy, falsifications stated rather than smoothed, reversal triggers on every PDR. But it is a good instrument for a **different construct than the one it is being narrated as measuring**: it establishes *expressibility* (an expert with full source access can find some declarative path) and publishes in the vocabulary of *novice authorability* ("fully authorable", against a vision claim whose operative words are "trivially" and "no RL engineering background"). The one change that removes the most blast radius is a reframe plus one cheap addition: label the metric an expert ceiling, and classify every PASS by discovery path — the authoring logs already contain the data. The second-largest risk is that facet interpretation is executor-owned and demonstrably softened at least once in a verdict-relevant way (F's "breaks" → "stops working").

## Authority-boundary verdict

**CLEAR.** No irreversible or outward-facing action is taken or scheduled without a gate. Commits/pushes are on `project-recovery-2` within the PDR-0046 grant; the escalation clause (INERT ≥ 3 → owner) is correctly reserved and untriggered; the vision conclusion is explicitly not being written by the agent. One watch item, below the finding bar: PDR-0084's "the prediction machinery has been systematically pessimistic about the substrate" is directional commentary on the vision claim accumulating in the record without the owner having adjudicated the construct question in finding 1 — keep that commentary out of anything outward-facing (README, release notes) until the reframing is settled.

## Answers to the five questions

**1. Does the operationalization measure the claim?** No — it measures an upper bound on it. The gap is **not fatal to the instrument** (expressibility is a genuine necessary condition; a FAIL here falsifies the vision claim outright, which is real epistemic value) but **fatal to the label** if the final reading publishes as a reading of "a novice can do this trivially." Verdict: **acceptable-with-reframing, and partially fixable inside the current run** — discovery-path classification of existing and future PASSes needs no re-execution, and second-party facet countersigning can start at trial five. The asymmetry to state in the reframe: this instrument's FAILs are strong evidence (if the expert can't express it, the novice can't); its PASSes are weak evidence for the vision claim (L's pass runs through a negative-drain hack found only after the obvious surface proved inert; O's pass is an engine-internals construction citing `executor.py` line numbers).

**2. Is the pre-registration doing epistemic work?** Some, and not the work it appears to. Real work: it locked the narrative before execution (four falsifications stated plainly — a motivated instrument would have smoothed at least one), and PDR-0078's decoupling removed the incentive to game the rate for bet acceptance. Hollow work: PDR-0082 concedes the predictions scored the *first-reach surface* while trials search the *whole space*, which makes toward-PASS falsifications structurally likely and uninformative about the substrate — yet the aggregate falsification is written up as a substrate finding. The diagnostic fix is to pre-register the search (surfaces, in order) so first-reach predictions and space-search verdicts stop being conflated; note the first-reach predictions are actually running ~4-for-4 *correct*, which is the sharper and less congratulatory finding the current framing buries.

**3. Is facet pre-commitment strong enough?** No. It binds *evidence* per facet (genuinely — the anti-conflation notes in L and M are executor-imposed hardenings that cut against passability, and the append-only discipline held), but it does not bind *interpretation* or *granularity*, and both are chosen by the executor at maximum-knowledge time. Concrete softenings in the records: F's disjunctive facet 3 written by a party who then documents that no destroy command exists (plausibly flips the corpus's only predicted-PASS to headline FAIL); L's "two meters is acceptable per-affordance"; M's "action = any operation"; O's "whatever form it takes" plus a disclosed mid-trial evidence-command substitution. One PASS in four resting on an interpretation call is enough to move a 9-trial rate by a full step.

**4. Does the blind re-run test what it claims, and is 2-of-9 enough?** It tests protocol reproducibility *within the expert-executor class*, which is worth having, but: the comparer is undefined and currently indistinguishable from the executor (selection hole); the blind executor reads the corpus and therefore the predictions (anchor); and the any-disagreement-kills branch attributes to protocol underspecification what may be search variance — a blind O run that never invents the renew-effect trick returns FAIL honestly. 2-of-9 is adequate only as a smoke test; as stated it combines low detection power with a false-alarm mode the design doesn't acknowledge. The fixes are governance, not redesign: owner picks the pair, at least one from {L, M, O}, and §7 gains an adjudication step separating ambiguity from search-dependence.

**5. Catalog fits.** Construct substitution (a vanity-metric variant: the number that can be read measures the easier thing) — finding 1. Acceptance-gap at facet granularity — finding 2. Interim-reporting inflation via executor-chosen ordering — finding 5. Decision-without-provenance on the source-access parameter — finding 6. **Not** present: the build trap (this bet is the repair of a correctly-diagnosed one), HiPPO capture, roadmap-as-promise, autonomy overreach, or strategy drift — the PDR trail 0077–0084 is exemplary provenance, every decision carrying options, rationale, and reversal triggers. One standing trigger to watch, not score: PDR-0079's third reversal trigger (ABSENT findings unactioned within two checkpoints = "just a gap" quietly becoming debt) now has seven-plus by-catch items accruing against it across four trials.

## Routed-out items

- Sequencing of the remaining five trials plus two blind re-runs against the 2026-10-06 window, and the pack-disposition clock (four packs OUTSTANDING) → `/program-management`. Noted, not critiqued here: four multi-agent trials plus two blind runs in ~7 weeks at one-session-each is the schedule risk that could trip PDR-0077's first reversal trigger.
- The engine defects the trials by-caught (`recovery.natural` inert, `scope: global` silently rebound, zero-affordance crash) → already correctly routed WS-4; no product critique owed.

## Re-review triggers

Re-run this critique when: (a) the metric row is reframed (or the owner declines to reframe — either is a decision worth a PDR); (b) the first blind re-run completes — its record is the first evidence about findings 3 and 4 that isn't self-reported; (c) the first multi-agent trial (D, E, J — O is done) lands, which is where the interim-inflation concern either dissolves or compounds; (d) before any reading is published anywhere outward-facing.

## Confidence Assessment

**Overall: High** for findings grounded in document text (1, 2, 5, 6, 7 — the evidence is quoted from the artifacts); **Moderate** for findings 3 and 4's forward-looking components (whether a blind executor would actually diverge on O is a prediction, not an observation). All requested artifacts were available and read in full: vision.md, PRD-0001, the ACTIVE protocol, the frozen corpus, all four trial records, the metrics.md north-star row, and PDRs 0077–0084. Nothing material was inferred to fill gaps; the one inference made explicit is that "the comparer" in protocol §7 defaults to the standing agent — nothing in the documents appoints anyone else, and all four executions to date are the standing agent. I did not independently re-run probes or verify the trial packs compile; the critique takes the recorded command outputs as genuine, which is consistent with their internal cross-references (pins, commit hashes, filed tracker IDs).

## Risk Assessment

- **Finding 1 (high)** threatens *did-it-work* at the product's root: the one number built to falsify the central claim would, as labeled, be unable to be falsified by the failure mode the vision actually names (a novice stopped). Reversible cheaply now (a label and a split); nearly irreversible after the reading publishes into README/announcement territory, because a retracted headline number costs more than an honest ceiling ever would.
- **Finding 2 (high)** threatens *did-it-work* arithmetically: one interpretation call plausibly moves the final rate one full step of nine, and the standing bar is 8-of-9 — a single softened facet is the entire budget. Reversible for F by owner adjudication of the "breaks" reading before the final reading; the remaining five trials are fully protectable.
- **Findings 3–5 (med)** threaten the *credibility* of the reading rather than its existence: each is the kind of joint a skeptical outside reader finds in minutes, and the corpus's own text ("a reader who distrusts the number should start here") invites exactly that reader.
- **Authority boundary:** no exposure; the escalation clause is well-built and the agent has kept the vision conclusion out of its own mouth.

## Information Gaps

- **The owner's intended construct.** Whether "expert ceiling with source access" was the owner's deliberate operationalization or a default is the pivot for finding 6 and the framing of finding 1 — no document records it either way. Highest-value gap; one question to the owner closes it.
- **Who will comparer/blind-run duty fall to.** Finding 4's severity drops if an independent comparer was always intended and simply not yet written down.
- **The `PDR-0081` plan document** (`docs/plans/2026-08-18-trial-protocol.md`) was not read; it could contain the source-access reasoning finding 6 says is missing. If it does, finding 6 downgrades to "provenance exists but is not in the PDR chain."
- **Tracker state** for the seven by-catch items was not queried; PDR-0079's third reversal trigger cannot be scored without it.

## Caveats

This is a static critique of the instrument's artifacts, not a re-execution of it: I did not compile the trial packs, run the probes, or attempt any trial myself, so I cannot rule out that a genuinely docs-only path exists for L, M, or O that the executor happened not to need — which would weaken finding 1's evidence base (though not its labeling point). Predictions about blind-run divergence (finding 4) are exactly the kind of claim the blind runs exist to test; treat mine with the same skepticism this report applies to the corpus's. The critique audits the product-measurement discipline only — trial sequencing and window risk are `/program-management`'s, the engine defects found are WS-4's, and per this agent's contract I have named what would close each gap but designed nothing: every remediation is a decision for the owner or the standing agent to take, with a PDR, or decline, with one.
