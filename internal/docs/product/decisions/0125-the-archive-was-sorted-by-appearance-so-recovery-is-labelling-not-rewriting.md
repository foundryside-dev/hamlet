# PDR-0125 — The archive was sorted by appearance, not by value: recovery is labelling, and the rewrite is gated

Date: 2026-08-26   Status: **accepted** (owner-authorised in-session: *"yes please unarchive
it, I didn't have a strong methodology, just 'what looks old'"*, then *"you're authorised to
recover anything that has ongoing value"*)
Author: Claude (standing product owner)
Related: `PDR-0118` (the six-doc HLD set), `PDR-0066` (a declaration reaching nothing),
`hamlet-ad2773718a` (WS-5, the gate this ran into), `PDR-0121` (which satisfied that gate's
first prerequisite)
Evidence: `scratchpad/docs-recovery.md`; 12 docs-only commits; tickets `hamlet-8f2e13c5a9`
(P1) plus four filed and three commented

## Context

On 2026-08-24 the owner bulk-archived most of `docs/` into `docs/zzz. archive/`. He later
stated the method plainly: *"just 'what looks old'"*. A dead-path sweep had already found the
live HLD set citing `docs/config-schemas/` 39 times — UAC.md alone fourteen — while
explicitly delegating schema detail there. The reference tier the current documentation was
written to point at was sitting in the archive.

Verification before restoring changed the picture: of the 13 `config-schemas` files, **only
2 are clean**. `affordances.md` documents an entire `capabilities:` schema wired to nothing;
not one YAML snippet in `items.md` parses; `effects.md` never mentions a field required
whenever effects are declared; `expressions.md` is stale in the *inverted* direction —
disclaiming as "planned" nine functions that ship, documenting 4 of 49 registered functions,
and stating that type checking is deferred when the registry-backed checker exists.

## Options

1. Leave archived — the live docs keep pointing at nothing.
2. Recover and rewrite — restore, then fix the content.
3. Recover and **label** — restore with dated banners naming the verified defects, and file
   the corrections as work.

## The call

Option 3, plus a scope boundary. **53 files recovered, 413 left as history, ~92 citations
repointed, 51 dated banners, dead live references 134 → 87.** Each stale document carries the
specific wrong claims *and the correct values where known* (`name` not `id`, `t_max` plus a
required `eta_min`, `interactions:` not `effect_pipeline:`, bare `tick` not `temporal.*`).

**The rewrite is BLOCKED and that gate is respected.** `hamlet-ad2773718a` requires schema
docs be generated from **consuming code paths, not Pydantic models** — *"otherwise the
rewrite re-certifies the ~40 inert fields."* That reasoning is sound and load-bearing: this
project's signature defect is the declaration that parses and does nothing, and generating
from DTOs would stamp every one of them as real. Its first prerequisite (coherent compiler
stage numbering) is now **satisfied** by `PDR-0121`; the second needs WS-4.

## Rationale

An undocumented live surface is worse than a documented-and-flagged one, and deleting would
strand 39 citations a second time. Labelling is safe under the gate; rewriting is not. The
durable fix is neither: `tests/…/test_vfs_doc_social_residue_examples.py` already compiles a
doc's fenced examples as a test — which is why *that* doc's examples were caught when a
rename moved the file. Extending that pattern, and generating the 49-function reference from
`FUNCTION_SPECS`, converts documentation truth from a periodic audit into a gate that cannot
silently rot. Two documents were audited twice with materially different results and both
first passes were wrong; more human passes is not the answer.

## Reversal trigger

If WS-4 lands and schema docs still cannot be generated from consuming code paths, the
generate-from-source premise in `hamlet-ad2773718a` is falsified and the doc strategy is
reopened — hand-maintained references would then need a different anti-rot mechanism, not a
delayed rewrite.
