# PDR-0080 — the corpus freezes at fifteen and the trial set is DRAWN, not chosen: seed = the corpus's own content hash

Date: 2026-08-17   Status: **accepted** (owner-decided from four options: stratified random draw of
9, seed recorded)
Author: Claude (standing product owner)
Owner sign-off: **yes**

Related: `PDR-0077` (the bet), `PDR-0078` (why a flattering corpus was tempting and no longer is),
`PDR-0051` (pre-registration)
Tracker: `hamlet-5fa1f7bfc0`
Artifacts: `docs/product/prds/0001-corpus-FROZEN.md`, SHA256
`48840cc3ae62e381e0a96a6e850e3cc2fd309081b00bcbd8974cd9d58de935d9`

## Context — over-supply turned a scheduling problem into a stronger claim

The owner's riffing grew the corpus to **15** ideas against a trial budget of roughly one session
each. The obvious move — cut to 9 — reintroduces exactly the selection bias the origin-tracking was
built to close: *someone has to choose which nine*, and whoever chooses can lean toward winnable
ideas without meaning to.

## Call

**All 15 freeze as the pool.** The trial set is **drawn mechanically**:

- **Seed** = `int(sha256(<frozen corpus bytes>), 16)` — a pure function of the file, chosen by
  nobody, re-runnable by anyone holding it.
- **Stratified**: seven axis buckets in alphabetical order, one idea drawn from each (the per-axis
  floor, so chance cannot return five social-economic ideas), then two more from the remainder.
- **N = 9**: **B, D, E, F, J, K, L, M, O**. Held in pool: A, C, G, H, I, P.

## Rationale

The draw's first act was to validate itself: **it excluded both ideas the agent predicted would
pass most easily** (H queueing, A momentum) and drew in four of five FAIL predictions. Had the
agent chosen, it would not have chosen these. That is the mechanism doing precisely the job it was
introduced for, and it is the strongest statement the instrument can make about its own honesty.

Freezing all 15 rather than 9 also makes the corpus a **durable, re-runnable asset**: read the same
ideas again after further WS-4 units land and the number is comparable to today's — the first real
content `metrics.md`'s Trend column has ever had.

Residual, stated rather than hidden: the stratification is what bounds bias; the seed only orders
picks *within* buckets, and the agent wrote much of the hashed text.

## Reversal trigger

- **If the frozen corpus is edited after any trial begins**, that trial is void (PRD-0001
  criterion 1) and the draw must be re-run against the new hash — the whole record is
  reconstructed or discarded.
- **If the drawn nine prove unrunnable** (two or more cannot be attempted at all), the draw is
  re-run from the pool with the exclusion recorded, rather than hand-substituted.
- **If a future reading over the same corpus is not comparable** to this one — because the scoring
  unit or the protocol moved — the Trend claim is void and the corpus stops being an asset.
