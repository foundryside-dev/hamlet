# PDR-0072 — Gate 2 is executed for the second merge (`905acd96`, stamped at `54132aaf`); twenty-one claims stale in 27 commits; and a claim about `main` must be written to survive becoming `main`'s README

Date: 2026-08-17   Status: **accepted** (an ACCEPT against `PDR-0039`'s stated criteria, squarely
within the grant; the merge itself is the owner's, `PDR-0046`)
Author: Claude (standing product owner)
Related: `PDR-0039` (the two gates and the method — sweep, fix not re-describe, adversarial pass),
`PDR-0048` (gate 2 at the first sweep, ten claims in one day), `PDR-0058` (gate 2 re-fires at
every merge; five claims in four commits at the first merge), `PDR-0065` (the reading note: a
claim about `main` written from the branch's vantage), `PDR-0068`/`PDR-0071` (why now),
`PDR-0056` (the second divergence shape the README had not learned), `PDR-0070` (the frontend
gate the README said could not exist)
Tracker: `hamlet-0d750af814` and `hamlet-df91baa2bb` (filed by this sweep),
`hamlet-f9090ec3e8` (the flake class the README now describes correctly)

## Context

`PDR-0039` binds every merge to a README re-verification *by the same method that produced it* —
ground-truth sweep, fix rather than re-describe, adversarial pass — and forbids a re-read.
`PDR-0058` made the re-fire unconditional at every merge. Between the first merge (`33bfff51`,
2026-08-15) and this resume, 27 commits landed on `project-recovery-2` and the README was not
touched.

## What was executed

Four ground-truth verifiers, one per section, executed every claim against the tree at
`54132aaf` and the GitHub API the same day (not read: compiled all five levels and compared
hashes, byte-diffed the two quoted YAML files, ran every CLI command in the file, ran the harness
cell, re-ran the model_pack cache failure, ran a two-episode training run to the *"Training loop
completed normally"* line, ran `npm test` and `npm run build`, listed 60 CI runs and 91 nightly
runs). Then one adversarial reviewer over the revised draft.

**Twenty-one claims stale or misleading in 27 commits** — itemised: (1) the first merge was a
168-commit PR merge, not a 167-commit fast-forward; (2) *"main is now current"* while 27 behind
and red; (3) *"CI green — every run passed, six pushes"* — 19 pushes, 59 of 60, one red at
`bf0f2fe4`; (4) *"three of four run and pass"*; (5) *"six pushes"*; (6) *"every run since has
passed"*; (7) the nightly's *"15-run failure streak"* — 64, and the workflow has never passed in
91 scheduled runs; (8) *"may still need `gh workflow enable`"* — `active`, fired twice; (9) *"the
full matrix has not yet completed a run against the merged tree"* — twice, 31 failures each;
(10) the flaky test is a class of two, not one member; (11) *"the README still on `main` badges
a test count"* — `main`'s README **is** this file since the merge; (12) `docs/architecture` /
`config-schemas` *"not reconciled"* — partly; (13) the `environment.yaml` gloss omitted that meter
observation types now live there; (14) L0_0's `training.yaml` delta was understated (six
hyperparameters, not two categories); (15) the harness *"runs the same pack"* — each side is a
(code root, pack root) pair, the oracle side reading `oracle_fixtures/`; (16) `DIVERGED_AS_REGISTERED`
described with **one** shape when the harness has adjudicated two since `PDR-0056`; (17) *"both
checkpoint-boundary entries"* as if the register held two — it holds five; (18) the five
pack-level hashes *"read by nobody"* — the harness diffs them; (19) **the frontend "cannot be
built as shipped"** — `package.json` since `a5cca764`, builds, vitest gate; (20) 23 packs carry an
`experiment.yaml` — 25; (21) the two quoted-file and Trial-001 caveats were fine, but the pack
layout omitted `presentation.yaml`, `range_type`, `semantic_type`, `interaction_type` — declared
surfaces the file did not know existed. All fixed in place, none re-described.

**The adversarial pass then found ten more in the revised draft**, and the two that matter most
are a new class:

- One outright FALSE: a *"167 commits went unchecked"* holdover now contradicting the corrected
  168 three paragraphs above — the exact shape `PDR-0058` recorded (a number fixed in one place
  and left in another).
- **Two sentences that were true on the branch at the moment of writing and would read as false
  the instant the file became `main`'s README** — *"the tests … which `main` still deselects …
  They go green when this branch merges"* and *"at this stamp it trails by 27 commits —
  including the deletion of the `slow` marker its nightly is still red behind"*. On `main`,
  after the merge, the marker is gone and the reader is standing on the tree the sentence says
  is missing.
- A literal test count (*"37-test vitest suite"*) that broke the file's own no-literals rule —
  written by the same hand that had just re-read the rule.
- *"the recovery's own changes had broken"* the 31 — partly pre-existing at `f0a9ae8a` (the
  temporal file asserted `Bed`/`Job` against a pack that already named `SLEEP`/`WORK`).
- *"one line of one file"* (comment lines also differ); *"the 31 are repaired"* (29 repaired, 2
  deleted); the stamp sentence's *"the commit that goes to `main` next"* (the checkpoint commit
  follows it).

All ten fixed. Fifth consecutive rewrite in which the adversarial pass earned its cost.

**The same rule applied to in-code text the sweep named**, because a docstring that describes
one shape misleads the next verifier exactly as the README would: `harness.py`'s module
docstring (*"currently one shape"* → two, plus per-side pack roots), the `full-tests.yml` comment
(*"15-run"* → the actual history), and `ORACLE.md`'s table row (*"next, reshapes WS-3"* → built,
`PDR-0032`; does not subsume WS-3, `PDR-0034`).

## The call

**Gate 2 is executed and satisfied at `905acd96`, stamped against the tree at `54132aaf`.** The
sweep found what `PDR-0039` predicted it would — the recovery fixed the things described — and the
merge is ready for the owner. Gate 1 (CI) is read on the push: Lint and Config Validation green
at `905acd96`; the Tests job's reading is stated in `metrics.md` and `current-state.md` as it
stood at checkpoint, not banked ahead of the run.

## The durable rule this adds (extends `PDR-0065`'s reading note)

`PDR-0065` recorded that a claim about `main` written from the branch's vantage goes false when
`main` moves. This sweep found the mirror image: **a claim in a file that will *become* `main`'s
README must be written to be true after the merge, not only before it.** The test is mechanical:
for every sentence naming `main`, ask *"a reader on `main` after this lands — is this still true
for them?"* If not, pin it to the stamp (*"at this stamp `main` still sat at `07b26ed5`…"*) or
state the transition (*"the merge that carries this file removes both the marker and the
failures; the first nightly after it is the reading to check"*). The adversarial reviewer's
brief now carries this question explicitly.

## Consequences

1. Both gates stand for the second merge; both are commit-scoped. `PDR-0039`'s rule is
   unchanged: if further *code* commits land before the owner merges, the sweep is owed again.
   The commit after `905acd96` is this checkpoint (`docs/product/` only) and touches nothing the
   README describes.
2. The merge checklist inherits nothing new: the nightly is `active` (verified this sweep, so
   `PDR-0043` trigger 2 stays discharged); the workflow file and the per-push Tests job are the
   same invocation, so the first post-merge nightly is the reading that closes the `main`-is-red
   thread.
3. Two defects filed by the sweep, neither folded into anything: `hamlet-0d750af814` (the run
   directory branches on the literal path segment `runs` — a name-branch, `PDR-0045`'s shape on
   a path) and `hamlet-df91baa2bb` (a stray, unread `drive_as_code.yaml` fixture whose only
   effect is to make a `multiplicative` grep lie, plus the legacy loader that would read it).

## Reversal trigger

- **Fire gate 2 again at the merge** if any commit touching `src/`, `configs/`, `frontend/`,
  `.github/`, `scripts/` or `tests/` lands on the branch after `905acd96` and before the owner
  merges. Citing this PDR as the satisfied gate for such a commit is the trigger.
- **Reverse the "fixed, not re-described" reading** if the first post-merge nightly on `main` is
  still red on the three named files — that would mean the README's account of the 31 is wrong
  and the branch did not carry what it claims.
- **Reopen the tense rule** if the next sweep finds a sentence pinned to a stamp that has itself
  become misleading (a stamp-pinned claim about `main` that a `main` reader takes as present
  tense): the rule is meant to remove one class of decay, not add another.
