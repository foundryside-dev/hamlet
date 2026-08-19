# PDR-0086 — The three-lens methodology review is adjudicated: the instrument is relabeled an expert ceiling, Appendix A pre-registers the amendments, and Trial F's reading is owner-ruled

Date: 2026-08-18   Status: **accepted** (owner-decided in session on three explicit questions;
recording and execution autonomous within grant)
Author: Claude (standing product owner)
Owner sign-off: **yes**, on all three calls — (1) adopt amendment packages A + B; (2) Trial F
PASS stands with the gap captured; (3) the expert-executor construct was a DEFAULT, and a
novice-facing row is wanted alongside it

Related: `PDR-0077` (the bet), `PDR-0081` (the protocol this amends via Appendix A),
`PDR-0082`–`PDR-0085` (the four verdicts, all of which STAND), `PDR-0079` (whose INERT
escalation clause finding 2 shows to be structurally suppressed)
Tracker: `hamlet-83806979f7` (item destruction ABSENT — the F adjudication's captured gap),
`hamlet-bf42ac60b5` (raw item-slot observation emit), comment 167 on `hamlet-d76684f549`
(Trial O reset-leak evidence)
Artifacts: the three reviews archived verbatim at
`docs/product/assessments/2026-08-18-trial-methodology-review/` (construct-validity /
rl-practitioner / statistical-inference); protocol Appendix A
(`docs/product/prds/0001-trial-protocol.md` §12); construct preamble and two prospective rows
in `metrics.md`; post-verdict notes on the F and O records

## Context

After Trial O (`PDR-0085`), the owner directed a methodology review: three Fable reviewers —
a fresh-context construct-validity critic, a fresh-context deep-RL practitioner (who ran its
own probe against the O pack), and the standing session forked into an adversarial
statistical-inference reviewer. All three delivered the same day. Convergent core: **the
instrument is well-built and honestly run, but it certifies expert any-surface expressibility
while its name and narration claim novice authorability and (via the vision sentence)
trainability.** All three found the four verdicts clean within their actual construct; none
recommended voiding anything. Divergent contributions: the critic found the facet-
interpretation softening (F's "breaks" → "stops working") and the interim-reporting inflation;
the statistician found the INERT counter's structural zero-bias and the sampling-frame bounds
(9/9 ⇒ 95% lower bound ~0.66 even for the internal claim); the RL reviewer empirically
confirmed the O pack leaks across `env.reset()`, ties award everyone, a zero-credit bidder
keeps winning, and no trial has ever checked the reward surface.

## The calls (owner, in session)

1. **Adopt A + B.** Package A: prospective protocol amendments, pre-registered before trial
   five as Appendix A — facet countersigning by a non-executing party; search
   pre-registration; discovery-path annotation; the leg-(c) probe additions (reward
   assertion, double-reset, obs-bounds, boundary-case, N≥3, random-policy smoke) as a
   non-gating column; the record-integrity rule; the mixed-classification rule; blind re-run
   governance (owner picks the pair, ≥1 of {L, M, O}, comparer never the original executor,
   surface paths recorded; §7's reject branch unchanged). Package B: metric hygiene, immediate
   — construct preamble on the north-star row; "k of 9 settled" reporting; Trend arrow
   withheld until the denominator is exhausted; the INERT surface count published beside the
   idea counter; running rates out of commit subjects.
2. **Trial F: PASS stands, the gap is captured.** The owner's rule, verbatim: *"it's not a
   fail if it doesn't meet the lower standard, but it's a gap that needs to be captured."*
   F passed the standard the substrate can declare (at zero wear the effect stops firing);
   the Spec's higher standard — the item *breaks* — is un-declarable (no destroy/despawn
   command) and is now `hamlet-83806979f7` (ABSENT, WS-4). Adjudication note appended to the
   F record; the facet table untouched.
3. **The construct was a default, and the owner wants the novice row too.** The §5
   source-access allowance was inherited from how Trials 001/002 happened to run, never
   decided (the critic's decision-without-provenance finding — this PDR is the honestly-dated
   record it asked for). The expert-ceiling reading continues as the headline for this corpus
   (relabeled, preamble attached); a **novice-facing, discovery-path-annotated row** opens
   prospectively from trial five, with retro-derivation for L/F/M/O owed from the existing
   authoring logs.

## What was deliberately NOT done

- **No verdict was re-scored.** L, F, M, O stand. Nothing in any review justified a void.
- **The frozen corpus was not touched**, including its garbled pre-registration sentence
  (acknowledged in Appendix A.9 instead — that paragraph is pre-registration text and its
  prediction has already resolved against it).
- **The INERT escalation threshold was not moved** mid-flight (the statistician's own advice);
  the blind-spot is compensated by publishing the surface-level count, not by re-tuning the
  pre-committed clause.
- **§7's any-disagreement-kills reject branch was not weakened** — softening a reliability
  check after four passes is exactly the move a motivated instrument would make; the
  adjudication step added by A.8 informs diagnosis, not whether the branch fires.
- **The RL reviewer's F8 (unseeded spawn RNG) was adjudicated lower-severity than delivered**:
  `seed_all` seeds the global torch RNG, and bit-identical traces under seed were verified
  CPU+CUDA at the oracle tag. Annotated on the archived review rather than filed.

## Rationale

The reviews' sharpest shared point is asymmetric: an expert ceiling is still a real
instrument — its FAILs falsify the vision claim outright — but its PASSes must not be
narrated as the vision claim confirmed. Every adopted change is either prospective,
non-gating, or pure reporting; the pre-registered instrument's comparability across the nine
trials is preserved, which is what makes the eventual reading publishable at all. The
cheapest-fix bias throughout is deliberate: nothing adopted requires re-execution, unfreezing,
or a single line under `src/townlet/`.

## Reversal trigger

- If the retro-derived discovery-path split shows any of L/F/M/O actually reached its winning
  surface docs-first, the preamble's "0 of 4 docs-first" prior is corrected in place, dated.
- If trials five onward show the countersigned facet lists systematically diverging from what
  the executor would have written (three consecutive trials with reconciliation notes), the
  countersigning step graduates from procedural amendment to a PRD criterion at the next
  corpus revision.
- If a blind re-run fires §7's reject branch, this PDR's amendments do not soften the
  consequence: the instrument is not accepted and no reading publishes (unchanged from
  `PDR-0081`).
- `PDR-0085`'s publication gate is now DISCHARGED as to the review's existence — the review
  ran and no finding voided a verdict — but its substance persists in the preamble: a reading
  published without the construct preamble attached is a defect against this PDR.
