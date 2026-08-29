# PDR-0127 — The Lint gate was dark for 47 pushes under two "green" checkpoints: the gate is restored, and a green claim now requires reading every CI row at the tip

Date: 2026-08-29   Status: **accepted** (gate restoration and the checkpoint-protocol rule are
within the grant)
Author: Claude (standing product owner)
Related: `PDR-0102` (the same shape nine days earlier: seven reds, twice reported green),
`PDR-0010` / `PDR-0062` (Gates-green lessons), `PDR-0039` (gate 1 = CI green at the tip)
Evidence: `gh run list --branch project-recovery-2 --workflow Lint --limit 100` — last green
`0b659130` (2026-08-21), first red `7dc6f66c` (2026-08-22), 47 consecutive reds through
`8b733f3e`; fixes `237b0c38` (Black, 64 files) and `b915139e` (no-defaults, 18 hits); green
again at `b915139e` and `1065dbf0` (all three workflows `completed/success`); tracker comment
276 on `hamlet-fa6bb6da4a`

## Context

`/own-product` ORIENT on 2026-08-29 read the CI rows at the branch tip instead of trusting the
brief. `current-state.md` said *"everything pushed and green"*; the Lint workflow had been red on
**47 consecutive pushes**, spanning the 44th and 45th checkpoints, both of which recorded the
branch as green. Two walls were stacked: `black --check` (64 files) in front, and behind it
`scripts/no_defaults_lint.py` with 18 non-whitelisted hits — all in code landed 2026-08-22 → 26,
including unit 3's `token_spec.py`, `token_diagnostics.py` and `token_hashes.py`. The
`lint.yml` workflow runs `ruff` → Black → mypy → no-defaults and stops at the first failure, so
each red hid whatever was broken behind it; the local pre-push habit ran `ruff` only.

`PDR-0102` recorded the identical shape on 2026-08-20 (seven reds, twice reported green) and
closed it with protocol **B.7** — which governs trial commits, not checkpoints. The hole was one
layer up.

## Options

1. Whitelist all 18 hits and go green — fast, and exactly what the gate exists to refuse.
2. Classify each hit; fix the real defaults per `CLAUDE.md` ("make it required, set it
   explicitly"), whitelist the structural ones with the reason written down.
3. Option 2, plus a rule on the checkpoint itself.

## The call

**Option 3.** Three hits were real defaults and are now required: `TokenTypeSchema.slot_bindings`
(every construction site already passed it), `owner_capacity` on `describe_variable` /
`static_payload_signature` / `check_indistinguishability` (the compiler now states
`owner_capacity=None` at its two call sites instead of inheriting it — safe because
`describe_variable` raises rather than mis-describes when an owner slot lacks a capacity), and
`source_map` on `validate_v21_semantics`. Fifteen hits (eleven whitelist entries) were
structural — four declared "(computed)" fields on `transition_rules.yaml`'s DTOs, a container
idiom, five boolean/arithmetic expressions the AST rules misread, two diagnostic inputs — and
are whitelisted with their reasons in `.defaults-whitelist.txt`. 784 unit tests pass; CI green
at `b915139e`.

**The rule:** a checkpoint may not record `Gates green`, and a merge may not read gate 1 as met,
without reading **every** per-push workflow's conclusion at the tip SHA — `gh run list --branch
<b> --limit 6 --json headSha,name,conclusion` — and the local pre-push discipline is the CI set
(`ruff check .`, `black --check src tests`, `no_defaults_lint.py`), not a subset of it.

## Rationale

A gate that isn't read reads green. This project has now lost `Gates green` three ways — a
deselecting marker (`PDR-0059`), a probe-script `E501` (`PDR-0102`), and a formatter behind a
linter (here) — and each time the fix was to read the instrument rather than to infer it. The
no-defaults gate also earned its keep: the `owner_capacity` default *looked* like a silent
branch selection on the only production call path, and making it explicit turned a bug hunt
into a thirty-second review.

## Reversal trigger

If a future gate-2 sweep finds a Lint or Tests red streak of **more than three pushes** that a
checkpoint in that window recorded as green, this rule has failed as written and the checkpoint
protocol needs a mechanical step (a script that refuses to stamp), not a sentence.
