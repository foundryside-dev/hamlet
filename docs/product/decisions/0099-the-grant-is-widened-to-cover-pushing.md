# PDR-0099 — The authority grant is widened to cover pushing `project-recovery*`, and the widening is read narrowly because the consent was indifferent

Date: 2026-08-20   Status: **accepted** (owner-approved in-session; this is a grant change and it carries owner sign-off)
Author: Claude (standing product owner)

Related: `PDR-0046` (push authority on this branch), `PDR-0093` (the stamp debt this discharges),
`PDR-0038` (the pattern: stamp corrected at an approved touch), `PDR-0039` (the merge gate that
is *not* touched by this)
Artifacts: `docs/product/vision.md` — authority grant + amendment log entry dated 2026-08-20

## Context

`/product-checkpoint` forbids pushing ("those are outward-facing and gate to the owner"), while
`PDR-0046` grants push on `project-recovery` freely and **every checkpoint in this product's
history has been pushed**. The contradiction surfaced as a flagged item at the thirty-fifth
checkpoint, was resolved ad hoc at this session's resume (the owner answered "push it now"), and
then recurred at the thirty-sixth checkpoint — where the agent pushed and declared the deviation.

Two recurrences in two sessions is a standing ambiguity, not an incident. The owner resolved it:

> *"you can extend the grant to include pushing, I don't actually have an opinion on this."*

## Options

1. Leave the grant alone and keep declaring the deviation each checkpoint.
2. Widen the grant narrowly — `project-recovery*` branches only, checkpoint commits included.
3. Widen the grant broadly — treat "pushing" as covering any push, including `main` and tags.

## Call

**Option 2.** The autonomous list gains *"commit AND PUSH `project-recovery*` branches — checkpoint
commits included"*, explicitly superseding `/product-checkpoint`'s blanket no-push rule **for this
product only**. Pushes to `main`, tags, and releases are **not** covered; the merge to `main`
remains the boundary and still gates on `PDR-0039`.

## Rationale

The deciding consideration is the *quality* of the consent, not its presence. The owner said they
have **no opinion**. That is genuine authorisation — it is their grant to widen, they were asked
directly, and they answered — but it is not a considered judgment about scope, so it cannot bear
weight it was never asked to bear. Reading "pushing" at its broadest would let an indifferent
sentence dissolve the one boundary this product's grant actually leans on: the public repo at
`github.com/foundryside-dev/hamlet` is **public**, so a push to `main` is a publication step, and
publication is on the escalation list by name.

So the widening is taken at its narrowest defensible reading: it removes a recurring false flag
without moving the boundary that matters. `project-recovery*` is a working branch on a pre-release
product with zero users; pushing it is a durability operation, not an outward-facing one, which is
exactly why `PDR-0046` already permitted it.

This is the **first scope change** to the grant since it was granted on 2026-08-11 — every prior
amendment-log entry was a factual correction. The log entry says so explicitly rather than letting
a scope change hide among stamp fixes.

**Consequence, taken at the same time:** this is an owner-approved `vision.md` touch, which is the
condition under which the stale `Last reviewed` stamp is corrected (`PDR-0038`, `PDR-0088`). The
stamp moves `2026-08-19` → `2026-08-20`, discharging the debt `PDR-0093` recorded and removing it
from the flagged list.

## Reversal trigger

This widening is wrong, and reopens, if any of these occur:

1. **A push carries something outward-facing that the branch scope hid** — for example a pushed
   branch that a CI workflow auto-publishes, or a branch protection change that makes
   `project-recovery*` feed `main` without a merge. The scope is defined by *what the branch does*,
   not by its name.
2. **The owner forms an opinion.** The consent was explicitly indifferent; an indifferent grant is
   the easiest kind to have drifted past. Re-offer this specific clause at the next grant
   re-confirmation rather than treating silence as continued assent.
3. **The distinction stops being real** — if `project-recovery*` ever becomes the default branch or
   the published one, this clause collapses into "push anything" and must be rewritten before the
   next push, not after.
