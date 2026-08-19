# PRD-0001 Trial Protocol Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Write the reproducible trial protocol — the second half of PRD-0001's measurement
instrument — so that a second executor can run any of the nine drawn trials blind and reproduce
its verdict.

**Architecture:** Pure documentation deliverable, three files: the protocol
(`docs/product/prds/0001-trial-protocol.md`), a per-trial record template
(`docs/product/trials/0001/TEMPLATE.md`), and a one-line pointer added to PRD-0001. No code, no
`src/townlet/` changes (the instrument must not require engine changes to operate — PRD-0001
constraint). Verification is by execution: every command the protocol documents is run once in a
dry-run task and the documented expected output corrected to match reality.

**Tech Stack:** Markdown; verified CLI surface `python -m townlet.universe {validate,inspect}`;
`sha256sum`; git; filigree CLI.

**Prerequisites:**
- Branch `project-recovery-2`, working tree clean. Docs-only work; no worktree needed (deviation
  from the skill's worktree default, consistent with 27 checkpoints of session convention on this
  branch).
- `uv sync --extra dev --extra recording` already done; `UV_CACHE_DIR=.uv-cache` for uv commands.
- Corpus frozen and verified this session: `sha256sum docs/product/prds/0001-corpus-FROZEN.md`
  = `48840cc3ae62e381e0a96a6e850e3cc2fd309081b00bcbd8974cd9d58de935d9`.

**Verified facts this plan is built on (checked 2026-08-18):**
- `uv run python -m townlet.universe validate --help` → takes `config_dir` positional +
  required `--primary-level`.
- `inspect` takes an artifact path **or** a config dir with `--primary-level`, and
  `--format {table,json}`.
- Corpus per-idea structure: **Spec / Source / Stresses / Predict / Origin** — pre-registration
  (criterion 2) is already present per idea; the protocol enforces *checking* it, not creating it.
- `configs/trial002_money_int_capped` and `configs/trial002_money_log_gdp` are referenced by
  `tests/test_townlet/integration/test_meter_bounds_runtime.py` — the promoted-to-fixture
  disposition precedent for criterion 7.
- Drawn set: **B, D, E, F, J, K, L, M, O** (PDR-0080); held: A, C, G, H, I, P.

**Design decisions (recorded here so the reviewer/executor doesn't re-derive them):**
1. **Blind re-runs execute at the first run's pinned commit**, in a `git worktree`. Criterion 3
   tests *protocol reproducibility*; running at a different commit would conflate that with
   substrate drift. The per-trial commit pin exists exactly to make this possible.
2. **Facet enumeration is pre-committed per trial**: before authoring starts, the executor writes
   the facet list (from the idea's Spec + Stresses) and, per facet, the leg-(b) evidence they will
   accept. Without this, "observable" is executor judgment and criterion 3 fails on vocabulary.
3. **Leg (a) checks untracked files too**: `git diff --stat -- src/townlet/` misses a *new* file
   under `src/townlet/`; the protocol adds `git status --porcelain src/townlet/` (must be empty).
   Faithful strengthening of PRD criterion 4's intent ("zero lines changed").
4. **A compile error naming a real authoring mistake is not BLOCKED** — fix the pack and continue.
   BLOCKED means the *idea's declaration itself* is refused loudly. Prevents mis-scoring typos as
   substrate failures.
5. **Effort budget: one working session per trial, with a stopping rule.** A protocol without a
   stopping rule is not reproducible — one executor simply tries harder.

---

### Task 1: Write the trial protocol document

**Files:**
- Create: `docs/product/prds/0001-trial-protocol.md`

**Step 1: Write the file with exactly this content**

```markdown
# PRD-0001 — Trial protocol            Status: DRAFT until the mechanics dry-run passes

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
```

**Why this content:** every PRD criterion (1–7) maps to a numbered section; the four design
decisions from the plan header are §7 (pinned-commit blind runs), §4 (pre-committed facets),
§6 leg (a) (untracked check), §6 tree (BLOCKED vs pack mistake). Status is DRAFT until Task 3's
dry-run verifies every command.

**Step 2: Commit**

```bash
git add docs/product/prds/0001-trial-protocol.md
git commit -m "product: the trial protocol exists in DRAFT — preflight, pre-committed facets, two-leg verdict, ABSENT/INERT/BLOCKED tree, pinned-commit blind re-runs (PRD-0001 top item, hamlet-5fa1f7bfc0)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

**Definition of Done:**
- [ ] File exists with all 11 sections
- [ ] Every PRD acceptance criterion 1–7 is enforced by a named section
- [ ] Committed

---

### Task 2: Trial record template

**Files:**
- Create: `docs/product/trials/0001/TEMPLATE.md`

**Step 1: Write the file with exactly this content**

```markdown
# Trial <X> — <idea title from corpus>            <YYYY-MM-DD> · <executor> · blind: <no | yes, of <X>-<YYYYMMDD>>

## Preflight (protocol §3 — paste outputs)

- P1 corpus hash: `<paste>` — MATCH / MISMATCH(VOID)
- P2 drawn: <X> ∈ {B,D,E,F,J,K,L,M,O} — yes
- P3 prediction present: yes — quoted in §Facets below
- P4 `git status --porcelain src/townlet/`: `<paste — must be empty>`
- P5 commit pin: `<sha>` on `<branch>`
- P6 this record created before authoring: yes

## Facets (pre-committed BEFORE authoring; append-only after)

Corpus prediction, verbatim: **<paste Predict line>**

| # | facet | leg-(b) evidence accepted | result | classification |
|---|-------|---------------------------|--------|----------------|
| 1 | <capability> | <concrete check> | PASS / FAIL | — / ABSENT / INERT / BLOCKED |

## Authoring log (brief — what was tried, in order; pack path)

Pack: `configs/<pack>/` (started from: <scratch | copy of <pack>>)

## Verdict

**Leg (a):**
```
$ git diff --stat -- src/townlet/
<paste>
$ git status --porcelain src/townlet/
<paste>
```

**Leg (b), per facet:** (command + relevant excerpt each)

**Headline: PASS / FAIL** (binary; PASS iff every facet passed both legs)
Budget-limited: <no | yes — unsettled facets classified at furthest established point>

**Prediction vs. actual:** <one sentence; falsifications stated plainly>

## Gaps filed

| facet | classification | tracker ID |
|---|---|---|

## Pack disposition (protocol §9; deadline 2026-10-06)

<promoted to fixture — test path | deleted at <sha> | OUTSTANDING>
```

**Step 2: Commit**

```bash
git add docs/product/trials/0001/TEMPLATE.md
git commit -m "product: per-trial record template — preflight pastes, pre-committed facet table, two-leg verdict, disposition (PRD-0001)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

**Definition of Done:**
- [ ] Template mirrors protocol §§3–9 one-to-one
- [ ] Committed

---

### Task 3: Mechanics dry-run — execute every protocol command, correct the doc to reality

**Files:**
- Modify: `docs/product/prds/0001-trial-protocol.md` (only where reality disagrees; flip
  Status DRAFT → ACTIVE at the end)

**Step 1: Run every preflight and probe command against existing state**

```bash
sha256sum docs/product/prds/0001-corpus-FROZEN.md
git status --porcelain src/townlet/
git rev-parse HEAD && git branch --show-current
UV_CACHE_DIR=.uv-cache uv run python -m townlet.universe validate configs/default_curriculum --primary-level L1_full_observability
UV_CACHE_DIR=.uv-cache uv run python -m townlet.universe inspect configs/default_curriculum --primary-level L1_full_observability --format json | head -40
```

Expected: hash matches the frozen digest; porcelain empty; validate exits 0; inspect emits JSON.
This is a *mechanics* rehearsal only — no corpus idea is authored (rehearsing a drawn idea would
unblind it; rehearsing a held idea burns a spare for nothing).

**Step 2: Correct the protocol where any documented command or expected output is wrong**

Amend in place; note nothing if nothing diverged.

**Step 3: Flip protocol Status line to `ACTIVE — mechanics dry-run passed <date>`**

**Step 4: Commit**

```bash
git add docs/product/prds/0001-trial-protocol.md
git commit -m "product: trial protocol ACTIVE — every documented command executed once against the live tree, outputs verified (PRD-0001)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

**Definition of Done:**
- [ ] Every command in protocol §§3, 6 executed once with output matching the doc
- [ ] Status ACTIVE
- [ ] Committed

---

### Task 4: Wire-up — PRD pointer and tracker reconciliation

**Files:**
- Modify: `docs/product/prds/0001-measure-the-authoring-claim.md` (header block: add a
  `Protocol:` line pointing at `0001-trial-protocol.md`)
- Tracker: `hamlet-5fa1f7bfc0` — add a note that the protocol exists and is ACTIVE; refresh the
  stale description (it still reads N=5 / ≥4 of 5 / 2026-09-15 from before the owner amendment;
  the notes carry the corrected 15-pool / N=9 / ≥8 of 9 / 2026-10-06 state)

**Step 1: Add to PRD-0001's header block (after the `Corpus:` line):**

```markdown
Protocol: **`0001-trial-protocol.md`, ACTIVE <date>** — criterion 3's blind re-runs run against
this document and the corpus, nothing else.
```

**Step 2: Update tracker**

```bash
filigree update hamlet-5fa1f7bfc0 --description "<corrected text carrying 15-pool/N=9/8-of-9/2026-10-06>"
filigree note hamlet-5fa1f7bfc0 "Protocol written and ACTIVE at <sha> (docs/product/prds/0001-trial-protocol.md). Instrument criteria 1 (corpus) and protocol-existence both done; next: first trial — L is the highest-information draw (predicted INERT against hamlet-dc8f887cd5's zero-writer fields)."
```

(Check `filigree update --help` / `filigree note --help` for exact flag names before running;
fall back to the MCP tools if the CLI differs.)

**Step 3: Commit**

```bash
git add docs/product/prds/0001-measure-the-authoring-claim.md
git commit -m "product: PRD-0001 points at its ACTIVE protocol; tracker description reconciled to the amended N=9 shape (hamlet-5fa1f7bfc0)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

**Definition of Done:**
- [ ] PRD header names the protocol
- [ ] Tracker description no longer contradicts the amended PRD
- [ ] Committed

---

## Out of scope (explicitly)

- Running any trial (sequenced after the protocol exists; L first per current-state).
- A trial harness or any automation (PRD non-goal 5).
- Fixing anything a future trial finds (file-not-fix).
- `metrics.md` updates — those land at `/product-checkpoint`.
