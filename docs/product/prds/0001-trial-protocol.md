# PRD-0001 — Trial protocol            Status: ACTIVE — mechanics dry-run passed 2026-08-18 (every §3/§6 command executed once against the live tree at `2c1275d6`; all outputs matched this document)

Instrument half 2 of 2. Governs every trial of the frozen corpus
(`0001-corpus-FROZEN.md`, SHA256
`48840cc3ae62e381e0a96a6e850e3cc2fd309081b00bcbd8974cd9d58de935d9`).
PRD: `0001-measure-the-authoring-claim.md`. Decisions: `PDR-0077`–`PDR-0080`.
Drawn trial set (PDR-0080): **B, D, E, F, J, K, L, M, O**. Held in pool: A, C, G, H, I, P.

**Who runs this:** any executor — the standing agent, the owner, or a fresh session. The
protocol assumes no memory of prior trials. Blind re-runs (criterion 3) add the rules in §7.

## 1. Definitions

- **Trial** — one attempt to author one corpus idea as a config pack, ending in a recorded
  verdict. One trial per working session.
- **Facet** — one separable capability the idea needs, enumerated from the idea's **Spec** and
  **Stresses** lines before authoring starts (§4).
- **Headline verdict** — binary PASS/FAIL per idea. PASS iff *every* facet is demonstrated with
  both legs (§6). 90%-authorable is FAIL — a novice author who must write Python has been
  stopped. Facet detail records the nuance; the headline does not.
- **ABSENT** — no declarative surface can express the facet. Not debt (`PDR-0007` "not yet
  enabled"). Routes to WS-4 as a feature.
- **INERT** — a surface exists, validates/compiles, and produces no observable effect: leg (a)
  passes while leg (b) fails. This is debt, the worst kind for a declarative product
  (`range_type`, Trial 002, is the type specimen). Routes as a defect.
- **BLOCKED** — declarable in principle but refused loudly: parse/compile error, crash,
  documented rejection *of the idea's declaration itself*. A loud error naming a mistake in
  *your pack* is not BLOCKED — fix the pack and continue.

## 2. Standing rules (all phases)

- **Never edit `src/townlet/`.** The claim under measurement is a zero-`src/townlet/`-diff
  claim; an instrument that touches it cannot measure it.
- **Never edit the frozen corpus.** Any edit voids every subsequent trial (PRD criterion 1
  reject branch).
- **File, never fix.** Every gap found is filed to the tracker and routed WS-4 (§8). Repairing
  one inside a trial contaminates the reading (PRD non-goal 1).
- **Pin everything.** A verdict without a commit pin is not a verdict.

## 3. Preflight (every trial; paste every output into the trial record)

| # | check | command | required result |
|---|-------|---------|-----------------|
| P1 | corpus unchanged | `sha256sum docs/product/prds/0001-corpus-FROZEN.md` | exactly `48840cc3ae62e381e0a96a6e850e3cc2fd309081b00bcbd8974cd9d58de935d9` — else STOP, trial VOID |
| P2 | idea is drawn | idea letter ∈ {B, D, E, F, J, K, L, M, O} | yes — else STOP (held-pool ideas are not trialed under this reading) |
| P3 | prediction exists | the idea's `**Predict:**` line in the frozen corpus | present — else STOP, verdict would be void (PRD criterion 2) |
| P4 | tree clean | `git status --porcelain src/townlet/` | empty — else STOP (a pre-existing diff makes leg (a) unattributable) |
| P5 | commit pin | `git rev-parse HEAD` and `git branch --show-current` | recorded in the trial record |
| P6 | record created | copy `docs/product/trials/0001/TEMPLATE.md` → `docs/product/trials/0001/<X>-<YYYYMMDD>.md` (blind: `<X>-blind-<YYYYMMDD>.md`) | exists before authoring starts |

## 4. Facet enumeration (before authoring — this is the pre-commitment)

Read the idea's **Spec** and **Stresses** in the frozen corpus. Write into the trial record,
BEFORE authoring starts:

1. The facet list — every separable capability the Spec requires. (Example shape, idea F "Tool
   durability": *an item carries a wear state; use decrements it; at zero the item stops
   working or breaks; wear is observable to the agent.*)
2. Per facet, the **leg-(b) evidence you will accept**: which compiled-artifact fact, encoded
   observation, or stepped behavior would demonstrate it. Name the check concretely
   (e.g. "`inspect --format json` shows an observation field for the wear variable",
   "stepping the env N times with USE decrements the value read back at the compiled offset").
3. The corpus's predicted verdict, copied verbatim.

The facet table is append-only once authoring starts: a discovered facet may be *added* with a
dated note, but no facet or accepted-evidence entry may be edited or removed.

## 5. Authoring phase

**Allowed:** creating/editing files under `configs/<trial-pack>/` (a fresh pack; copying an
existing pack as a starting point is fine and is recorded); reading anything — source, docs,
schemas, error messages; compiling, validating, inspecting, and running as often as wanted.

**Forbidden:** edits under `src/townlet/`; edits to the frozen corpus; edits to any pack a test
references; consulting prior trial records when running blind (§7).

**Budget and stopping rule.** One working session. Stop when:
- (a) every facet is demonstrated → verdict PASS; or
- (b) a facet is established un-authorable — you can state *why* against the schema/compiled
  artifact — → classify it (§6) and continue to the next facet until all are settled; or
- (c) the session budget is exhausted → classify each unsettled facet at its furthest
  established point and mark the record **budget-limited**.

## 6. Verdict (both legs, every trial, no exceptions — PRD criterion 4)

**Leg (a) — zero engine diff.** Run and paste both:
```
git diff --stat -- src/townlet/
git status --porcelain src/townlet/
```
Both must be empty. An untracked file under `src/townlet/` is a change. A leg-(a)-only pass is
recorded as FAIL, never partial credit.

**Leg (b) — the declared thing is observable.** Per facet, execute the accepted-evidence check
pre-committed in §4 and paste the command plus the relevant excerpt. Standard probes:
- compile: `UV_CACHE_DIR=.uv-cache uv run python -m townlet.universe validate configs/<pack> --primary-level <level>` (exit 0)
- artifact: `UV_CACHE_DIR=.uv-cache uv run python -m townlet.universe inspect configs/<pack> --primary-level <level> --format json`
- runtime: a short probe — compile, `env.reset()`, step, read the observation at the compiled
  offset or observe the behavioral effect. Probe scripts live in the trial pack directory or the
  trial record, never under `src/townlet/`.

**Classification decision tree, per failing facet:**
1. Can any declared surface express it at all? No → **ABSENT**.
2. It can be declared and validates/compiles — does leg-(b) evidence show the declared effect?
   No observable effect → **INERT**.
3. The declaration itself is refused loudly (and the refusal is about the idea, not a pack
   mistake) → **BLOCKED**.

**Record against prediction.** Copy predicted vs. actual. A falsified prediction — in either
direction — is a finding and is stated, not smoothed over (`PDR-0047` is the precedent).

## 7. Blind re-run (criterion 3; 2 of the 9 by 2026-10-06)

- Chosen by the comparer (whoever adjudicates), not by the original executor.
- Fresh session. Inputs: this protocol, the frozen corpus, and the repo at the first run's
  pinned commit — use `git worktree add /tmp/trial-<X> <pin>` so the substrate is identical;
  running at a different commit conflates protocol reproducibility with substrate drift.
- The blind executor must not open `docs/product/trials/` or any prior verdict.
- Produces its own full record (`<X>-blind-<YYYYMMDD>.md`), then a third step compares
  **headline verdict and per-facet classifications**. Any disagreement → the protocol is
  underspecified, the instrument is NOT accepted, and no north-star reading is published
  (PRD criterion 3 reject branch).

## 8. Gap filing (file, never fix)

Per gap: `filigree create` (or the MCP tool) with a title naming the facet and the
classification, routed to WS-4 (blocked-by/parent per tracker convention), labeled
`prd-0001-trial`. Record every filed ID in the trial record. INERT findings are defects;
ABSENT findings are features; BLOCKED findings cite the loud error verbatim.

## 9. Pack disposition (criterion 7 — the measurement leaves no litter)

Every trial pack, pass or fail, is **promoted to a regression fixture** (referenced by at least
one test — precedent: `configs/trial002_money_*` ← `test_meter_bounds_runtime.py`) **or
deleted**, by 2026-10-06. The disposition and its date go in the trial record. An orphan pack on
that date breaches the `Pre-release hygiene` guardrail and rejects the bet.

## 10. Guardrails per trial commit (criterion 6)

Trial packs live under `configs/` and are reached by the config-validation CI gate. Before any
commit that adds or edits a trial pack: run the validate command on the pack (§6) and
`UV_CACHE_DIR=.uv-cache uv run pytest` (the default suite deselects nothing, `PDR-0062`); CI
runs the full gate set on push. A red gate stops the commit, not the trial — the trial's
verdict stands independently of when its record lands.

## 11. What updates when (§12 appendix follows)

The trial record is committed in the same session as the trial. `metrics.md`'s north-star row
is updated only at checkpoint, and only with: the rate so far, the stated denominator (9, minus
any voids, which are named), the ABSENT/INERT/BLOCKED split, and the per-trial commit pins.
The INERT escalation threshold is 3 (PRD criterion 5): at 3 or more INERT ideas, escalate to
the owner as a `vision.md` question — do not write the vision conclusion yourself.

## 12. Appendix A — 2026-08-18 amendments (`PDR-0086`, owner-approved, PRE-REGISTERED before trial five)

Adopted from the three-lens methodology review
(`docs/product/assessments/2026-08-18-trial-methodology-review/`). **Scope rule:** everything
here applies prospectively to trials five onward. Nothing here re-scores L, F, M, or O; their
verdicts stand as recorded. Additions marked *(non-gating)* are recorded columns/annotations
that do NOT enter the headline PASS/FAIL for this corpus — they may gate only from a future
corpus revision. Blind re-runs of the four completed trials use the protocol text **as of the
first run's pinned commit** (i.e. without this appendix); blind re-runs of trials five onward
use the text as of their own first run's pin.

### A.1 Facet countersigning (gating, procedural)

Before authoring begins, the facet list and its leg-(b) accepted evidence are enumerated by a
party that will NOT execute the trial — the owner, or a dispatched fresh agent given only the
frozen corpus entry and this protocol (no executor input, no engine-source access required of
it). The executor adopts the countersigned list, or reconciles differences in a dated note
BEFORE authoring starts. Rationale: pre-commitment previously bound evidence but not
interpretation, and interpretation was executor-owned at maximum-knowledge time.

### A.2 Search pre-registration (gating, procedural)

Before authoring, the executor writes into the record the surfaces it intends to try, in
order. A PASS on a listed surface confirms the search plan; a PASS on an unlisted surface is
annotated **"found by search"**. This separates the two records the first four trials
conflated: first-reach predictions (running ~4-for-4 correct) and any-surface verdicts.

### A.3 Discovery-path annotation *(non-gating)*

Every PASS records, per winning surface: **docs-reachable / error-message-guided /
source-reading-required**, plus whether the first-reached surface worked. To be derived
retroactively for L/F/M/O from their authoring logs (no re-execution). This is the data for
the prospective novice-authorability row in `metrics.md` (`PDR-0086` construct decision).

### A.4 Probe additions — the leg-(c) column *(non-gating for this corpus)*

Each trial's probe additionally records a **"trains-without-incident"** column from:
- **Reward assertion**: capture the reward vector from `env.step()` at one tick where a
  declared `drive.yaml` component must move it, and assert the delta. (No trial had ever
  leg-(b)-checked the reward surface; by the protocol's own INERT logic that was an open
  false-pass class.)
- **Double-reset facet**: after `env.reset()`, re-run the probe's first assertion block —
  every mechanic state must be back at its declared initial unless the pack declares
  persistence. (Trial O's auction effect and global VFS scratch survive reset —
  `hamlet-d76684f549`, comment 167.)
- **Obs-bounds loop**: every observation component within its declared normalization range
  across the probe run.
- **Boundary-case rule**: any comparison/branch facet pre-commits and probes its boundary
  case (equality, zero, saturation).
- **N≥3 rule**: any mechanic with cross-agent resolution carries at least one probe case
  with three or more agents (N=2 hides ordering and aggregation bugs).
- **Random-policy smoke**: ~5 episodes under a random policy (or one `DemoRunner` run with
  the pack's own `training.yaml` at reduced `max_episodes`): no exception, rewards finite
  and non-constant, episodes terminate.
- **Reward-relevance note** *(recorded, never gating)*: do the mechanic's state variables
  appear in any reward component? ("No" is a legitimate authoring choice and a fact the
  record states.)

### A.5 Record integrity (gating, procedural)

No verdict-section text may exist in a record before the corresponding command output does.
(Converts the Trial M near-miss self-catch into a protocol property.)

### A.6 Mixed-classification rule (clarification, previously unspecified)

An idea failing on multiple facets with mixed classes reports every facet's class; for the
idea-level split and the INERT escalation counter, the idea counts as INERT if ANY failing
facet is INERT (conservative in the direction the escalation clause exists to protect).

#### A.6.1 Precedence completion (owner-ruled 2026-08-20, pre-registered before the first blind re-run)

A.6 as written rules only the INERT tiebreak and is silent on an idea whose failing facets carry
no INERT — exactly Trial K (F1 ABSENT, F7 BLOCKED on the named surface and ABSENT for the
capability). The gap was escalated rather than self-adjudicated at the thirty-fifth checkpoint
(`PDR-0092`) and the owner ruled the full ordering:

> **INERT > BLOCKED > ABSENT.** The idea's bucket is the most severe class among its failing
> facets. A facet carrying two classes contributes its most severe one.

Rationale, in the same direction A.6 already argued: INERT is the worst because the substrate
lies to the author; BLOCKED is next because a declared surface refuses; ABSENT is least because
an unbuilt surface is a build list, not a lie. The rule is deliberately **mechanical** — it is
applied by reading the facet table, never by judging which failure was "decisive" — so a blind
re-run derives the same bucket from the same facet classifications. The counter-argument was
heard and rejected on that ground: a decisive-facet rule would have bucketed K ABSENT and would
have made bucketing an executor judgment call.

**Effect on the current corpus: Trial K counts BLOCKED** (F7's most severe class), and the
idea-level split reads **0 ABSENT / 0 INERT / 2 BLOCKED** over six settled. The INERT escalation
counter is unaffected — it stays at 0 either way, which is why this ruling could be taken without
touching the escalation clause. Trial B's existing BLOCKED bucket is unchanged and consistent
with the rule.

### A.7 Reporting discipline (immediate, also applies to the current corpus)

Interim state is reported as **"k of 9 settled, 9−k pending"**, never "k of k"; the
`metrics.md` Trend arrow is withheld until the denominator is exhausted; the running rate
stays out of commit subjects. Every reading publishes the **INERT surface count** (by-catch
INERT/dead surfaces encountered during trials) beside the idea-level INERT counter, because
the idea-level counter is structurally suppressed by executor workaround skill. Every
published reading carries the construct preamble (`metrics.md` north-star row).

### A.8 Blind re-run governance (amends §7's silence, not its reject branch)

The OWNER selects the two re-run trials (not the standing agent), including at least one
second-surface-dependent PASS (L, M, or O); the comparer is the owner or an owner-appointed
fresh agent, never the original executor. The comparison records the **surface path** taken,
not only the verdict — same headline via a different surface is recorded as a
search-dependence finding even when verdicts agree. §7's reject branch is UNCHANGED: verdict
or classification disagreement still rejects the instrument; the recorded diagnosis
(protocol ambiguity vs search variance) informs what is rebuilt, not whether the branch
fires. If O is chosen, the comparer is pre-briefed that the first run's facet 4 never
exercised the tie case.

### A.9 Acknowledged, deliberately not edited

The PRD's aggregate-prediction paragraph contains a garbled mid-edit sentence (an editing
artifact in pre-registration text — acknowledged here rather than edited, since the
falsification it pre-registered has already resolved against it). The Trial F "breaks →
stops-working" facet reading was adjudicated by the owner 2026-08-18: **PASS stands against
the declarable standard; the un-declarable higher standard (item destruction at zero wear)
is a captured ABSENT gap** (`hamlet-83806979f7`), per the owner's rule: *"it's not a fail if
it doesn't meet the lower standard, but it's a gap that needs to be captured."*
