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

## 11. What updates when

The trial record is committed in the same session as the trial. `metrics.md`'s north-star row
is updated only at checkpoint, and only with: the rate so far, the stated denominator (9, minus
any voids, which are named), the ABSENT/INERT/BLOCKED split, and the per-trial commit pins.
The INERT escalation threshold is 3 (PRD criterion 5): at 3 or more INERT ideas, escalate to
the owner as a `vision.md` question — do not write the vision conclusion yourself.
