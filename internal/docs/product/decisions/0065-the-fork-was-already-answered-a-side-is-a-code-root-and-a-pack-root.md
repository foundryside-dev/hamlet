# PDR-0065 — the harness fork was already answered by the register; the self-tests were the defect, and a side is (code root, pack root)

Date: 2026-08-16   Status: **accepted** (autonomous within the grant; the owner confirmed *"take it now
as repair"* at the 2026-08-16 `/own-product` resume, and approved the whole unit through to checkpoint)
Author: Claude (standing product owner)
Owner sign-off: given for the reframing (the resume offered the fork back to the owner with the
recommendation that it was repair, not specification; the owner took the recommendation).

Related: `PDR-0063` (superseded **in its framing** — its finding stands, its fork was narrower than
posed and its headline overstated the instrument's failure), `PDR-0062` (reversal trigger
**discharged** — `-m "not slow"` out in the same commit), `PDR-0052`/`PDR-0053` (the frozen inputs at
`49bdf28e`), `PDR-0037`/`PDR-0040` (the harness's verdict contract), `PDR-0059` (the gate hides
failures behind a marker), `PDR-0043` (a gate restored is not a gate verified)
Register: `DIV-004` (built, 2026-08-15)
Tracker: `hamlet-6f98e38a36` (closed), `hamlet-a0832f9004` (closed — its acceptance was this)
Evidence: `tests/test_townlet/unit/oracle/` + both self-tests **119 passed**; full default suite at the
fix commit `a725bf66` — **3193 passed, 16 skipped, 0 failed, nothing deselected** (889s), six gates green; harness matrix at the fix commit vs `oracle-2026-08-13`, CPU+CUDA, run `20260816-184228`: **16/16 `DIVERGED_AS_REGISTERED`** (10× DIV-004 hash-only, 6× DIV-003), exit 0 — same reading as `20260815-213851`, now taken through `main()`'s new plumbing

## Context

`PDR-0063` recorded, correctly, that `test_self_comparison_agrees` returns `HARNESS_ERROR` on
`environment.yaml` drift and that the hidden-failure count was 33, not 31. It then posed the fix as
a fork — *re-freeze the fixture, or register the divergence* — and declined to take it in passing:
*"it needs someone holding the oracle context."* Its headline was that the harness *"cannot
currently certify anything."*

At the 2026-08-16 resume, ORIENT read that context rather than inheriting the framing:

1. **The register had already answered the fork.** `DIV-004` — `built`, 2026-08-15 — says in so
   many words: *"the frozen fixtures under `oracle_fixtures/` stay at the old schema deliberately"*
   for the whole normalization programme, per `oracle_fixtures/README.md`'s own rule (*"if it is a
   schema change, leave the fixture at the old schema, set `pack_divergence` on the affected cells,
   and register the entry"*). The diff the harness reported — `range_type: normalized/unbounded` →
   `{kind: minmax, clip: false}` — is exactly DIV-004's surface. **"Register" was chosen the day
   before `PDR-0063` was written.**
2. **The matrix was certifying.** Run `20260815-213851`, taken at `2535a306` — *after* the last
   `environment.yaml` change — reports **16/16 `DIVERGED_AS_REGISTERED (DIV-004)`**: exactly the
   four declared hashes moved, every trace stream byte-identical. Every standing cell in
   `matrix.py` declares `pack_divergence="DIV-004"`. The instrument the strangler is measured with
   adjudicated the meter cut correctly.
3. **What was actually broken was two harness self-tests.** They build a bare `Cell` with no
   `pack_divergence`, so the frozen-input drift pre-check added at `49bdf28e` fires before either
   test reaches what its docstring says it exercises — that is why the second test got
   `HARNESS_ERROR` instead of `OLD_SIDE_ERROR`. And bypassing the gate would not have fixed the
   first: live `src` would then have parsed the frozen old-schema pack and crashed.

The root cause, stated once: **`run_side` already models a side as (code root, pack root), but
`run_cell` named the old side by its code root alone** and hardcoded its pack root to
`oracle_fixtures/`. `49bdf28e` parameterized half of what a side is. A self-comparison — same
`src` on both sides — has no oracle side and therefore no frozen inputs, and the API gave it no way
to say so.

## The call

1. **Reframe `PDR-0063`.** No oracle-specification decision was needed; the specification half was
   settled by `DIV-004`. The failing tests were a WS-7 harness/test defect inside the grant. The
   headline is corrected: the *matrix* certified; the *self-tests* were broken. `PDR-0063`'s
   reversal triggers are discharged (the issue closed at the first checkpoint after filing; no
   "harness green" was recorded in between).
2. **Fix at the source.** `run_cell(..., old_pack_root: Path)` becomes a **required** keyword;
   `pack_drift(old_pack_root, new_pack_root, logical_pack)` compares the two roots the sides
   actually read. A self-comparison passes the drift gate for the honest reason — identical
   inputs — not by bypass. `main()` passes `repo_root / ORACLE_PACK_ROOT` explicitly, with a comment
   saying the oracle side reads FROZEN inputs.
3. **Discharge `PDR-0062`'s trigger in the same commit.** `-m "not slow"` leaves `addopts`. With
   zero users the `slow` marker declaration is a declared-but-inert surface and is deleted — from
   `pyproject.toml` *and* from `tests/test_townlet/conftest.py`, which registered it a second time
   citing a `--runslow` option that exists nowhere. `full-tests.yml` runs bare `uv run pytest` and
   its step is renamed so it no longer describes a marker that does not exist. Both test READMEs'
   marker sentences are corrected; four "pyproject carries `-m 'not slow'`" comments in the repaired
   files are tense-fixed to *carried*.
4. **Close `hamlet-a0832f9004`** on the acceptance it was held open for: the default suite deselects
   nothing, and its title no longer describes any test.

## Rationale

**Why required, not defaulted.** A `None`-defaults-to-oracle would let the next self-test author omit
the argument and reproduce this defect exactly — the frozen root would again be the silent choice.
`run_side` already requires `pack_root`; `run_cell` now matches it. Twelve call sites naming the
root explicitly is the same fact spelled out, not a cost.

**Why not derive "self-comparison" from `old_src == new_src`.** The FIX-5 injection guard already
uses that predicate, which made it tempting. But two unit tests in `test_pack_freeze.py` pass
`old_src == new_src == tmp_path` as *filler* while asserting the old side resolves the FROZEN root;
deriving would silently invert what they pin. And an implicit rule — "equal code roots change how
inputs resolve" — is a hidden default in an API whose whole job is to be explicit about which side
read what.

**Why the matrix's certification stands.** DIV-004 is hash-only: a cell passes only when *exactly*
the enumerated hashes move and every stream is byte-identical. That is not a suppression of
behaviour; it is the strongest form of "the world did not change." The self-tests' failure said
nothing about it — they never reached the comparison.

**The method lesson, and it is this PDR's real content.** `PDR-0063` took the harness's own error
message — *"either re-freeze the fixture or register it"* — as the decision space, without reading
the register that had already made the decision. The message was accurate *for an oracle-vs-live
run*; the failing test was not an oracle-vs-live run. Reading an instrument's message as the set of
available choices is the same shape as reading "35 deselected" as *tests that are slow*: the number
was right, the reading of it was wrong. The correct move on an instrument's message is to ask what
situation the message was written for and whether this is that situation. Joins the family: a
recorded green is not a green (`PDR-0010`); a green tool is not evidence (`PDR-0033`); a red must
be distinguishable (`PDR-0037`); a correction is not self-verifying (`dcc5f803`); **an
instrument's fix message describes its author's scenario, not necessarily yours.**

**What this does not claim.** Exit condition 3 (*`Gates green` read on a suite that hides nothing*)
is met **on the branch**. `main` still carries all 33 behind the marker until the next merge, and
the nightly on `main` reported **31 failed** again this morning (run `31931718941`, 06:33Z) for
exactly that reason. Exit condition 2 (`AGREE` unreachable matrix-wide, `PDR-0056`) is untouched by
this — 16/16 `DIVERGED_AS_REGISTERED` is the *correct* reading while DIV-004 is open, and the
vocabulary is re-earned when DIV-004 closes, not here.

## Reversal triggers

- **If any production caller ever passes `old_pack_root=repo_root` for a real oracle run**, the
  freeze has been defeated to make a cell green. `main()` is the only production caller today and
  passes `ORACLE_PACK_ROOT`; `test_harness.py`'s `_fake_sides` pins that the old side resolves the
  frozen root. A second production caller must be reviewed against this PDR before it lands.
- **If the nightly `full-tests.yml` — now identical in command to `tests.yml` — is judged
  redundant**, that is a separate PDR: `PDR-0043` trigger 2 restored it deliberately, and its
  remaining distinction (nightly, against the default branch) is a real one on a quiet `main`. Not
  decided here.
- **If `pytest.mark.slow` reappears anywhere**, `PDR-0062`'s second trigger applies unchanged: the
  marker is gone from the project, and its return without a wall-clock measurement in the commit
  is the suppression coming back.
