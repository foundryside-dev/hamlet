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
