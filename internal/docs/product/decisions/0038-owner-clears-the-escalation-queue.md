# PDR-0038 — The owner clears the escalation queue: URL corrected, tag pushed, wardline instruction deleted, README rewritten

Date: 2026-08-14   Status: **accepted** (all four items **owner-decided this session**; three
of them sat outside the grant and could not have been actioned otherwise)
Author: Claude (standing product owner)
Related: `PDR-0012` / `PDR-0013` (no tech debt until 1.0 — the rule the wardline deletion
serves), `PDR-0007` (an option not yet enabled ≠ debt — the rule that preserves the wardline
*intent*), `PDR-0010` (the Gates-green lesson this closes a repeat of), `PDR-0030` (the oracle
tag now pushed)
Tracker: `hamlet-f894ade20a` (wardline), `hamlet-6730ba7915` (README)

## Context

Four items had accumulated on the blocked-on-owner list, three of them across multiple
checkpoints. All four are outward-facing or vision-touching and therefore sat outside the
authority grant. The owner cleared all four in one turn at the tenth checkpoint.

Recording them together, in one PDR, because they were decided together and because three of
the four are *authorizations* rather than product calls — a PDR each would inflate the log
without adding provenance. The one genuine product decision among them (wardline) gets the
full treatment below.

## The calls

**1. `vision.md`'s public-repo URL — CORRECTED.** From `github.com/tachyon-beep/hamlet` to
`github.com/foundryside-dev/hamlet`. Measured before and after: the old path redirects to the
new one and **both report `PUBLIC`**, so the grant's blast radius never differed. Amendment-log
entry added per `vision.md`'s own convention. No other section touched; the grant is unchanged.

**2. The oracle tag — PUSHED.** `git push origin oracle-2026-08-13`, executed and verified on
the remote (`refs/tags/oracle-2026-08-13^{}` → `0e875d7a`). Outward-facing, so it needed the
owner; near-zero blast radius, since the commit was already public as an ancestor of the pushed
branch. What it actually repairs: `ORACLE.md`'s own documented consult command
(`git worktree add --detach <dir> oracle-2026-08-13`) now works in a fresh clone, where before
the freeze was reachable only by SHA and only if you had read `ORACLE.md`.

**3. The wardline instruction — DELETED, and the intent kept.** Owner: *"delete the
instructions, we'll adopt wardline as a hygiene activity later on."*

This is the substantive one. `CLAUDE.md` and `AGENTS.md` each carried a machine-managed block
instructing **every agent** to run `wardline scan . --fail-on ERROR` as a gate before returning
code that touches external input. Measured 2026-08-13: it passes, and `--fail-on-inert` fails —
*"taint gate INERT: 0 trust boundaries recognized across 1555 analyzed functions."* Zero
boundary decorators anywhere in `src/townlet/`, no `trust_packs` in `weft.toml`, and wardline
is not a project dependency. **No code change could make that command fail.** A third falsehood
sat in the same three lines: the block cites `docs/agents.md`, which does not exist.

That is `PDR-0010`'s Gates-green failure in a fresh instance — a gate recorded as protecting
something while checking nothing — caught this time at one day old instead of three months.
Under `PDR-0012` an instructed-but-inert gate is debt by definition, and the triage rule
(`PDR-0005`: *wire, not delete*) yields to the owner's explicit call. **Deleting an
unfalsifiable instruction is strictly better than keeping it**: the instruction's only current
effect is to spend agent time producing a green that means nothing, and to teach that a green
gate is evidence when this one cannot be.

**The capability is deferred, not rejected** — `PDR-0007`'s reading, and the same treatment
episode recording got before its deletion (`hamlet-16ae192d42`). The `wardline-gate` skill and
the `weft.toml` / `loomweave.yaml` references are **left in place**: they are what adoption
will need, and deleting them would destroy the thing the owner said they want later. Roadmap
carries it under Later as intent.

**4. The README — REWRITE AUTHORIZED.** `hamlet-6730ba7915`. Outward-facing: it is the public
face of a public repo. Carried out this session against verified source facts with an
adversarial false-claim hunt, because the defect being corrected *is* false claims — the
`Documentation truth` guardrail attributes several of its confirmed-false entries to this one
file, including a coverage badge that is wrong on a public repo.

## Consequences

- The blocked-on-owner list is **empty for the first time since the workspace was bootstrapped**
  (`PDR-0001`, 2026-08-11).
- **Watch for re-infection:** the wardline block is machine-managed
  (`<!-- wardline:last-writer:wardline install -->`). Running `wardline install` in this repo
  will put it back. If that happens, it is not a regression to re-litigate — it is the tool
  doing its job, and the block should be removed again until adoption is real.
- `Documentation truth` moves in the right direction for the first time by more than one
  correction at once: the `vision.md` URL, the wardline block's three false claims, and the
  README's set.

## Reversal trigger

- **Re-instate a wardline gate** when boundaries are actually declared — i.e. when
  `wardline scan . --fail-on-inert` can pass. Re-adding the instruction before that recreates
  exactly the unfalsifiable gate deleted here, and the next reader will have no record of why
  it went. This PDR is that record.
- **Revisit the deletion** if a trust-boundary defect reaches the tree that a wired wardline
  would have caught. That would show the capability was load-bearing sooner than "later," and
  adoption moves from Later to Now on evidence rather than on principle.
- **Re-open the README** the moment its `Documentation truth` count is non-zero again. A public
  README is the one document where a false claim costs credibility with people who have no
  other information about the project.
