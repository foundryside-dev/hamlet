# PDR-0001 — Bootstrap the product workspace from observed state, and record the authoring pivot

Date: 2026-08-11   Status: accepted   Author: Claude (standing product owner)   Owner sign-off: yes (grant + audience confirmed in-session)
Supersedes: —   Related: vision.md, roadmap.md (Now), metrics.md (north-star)

> **Naming collision, deliberate.** `docs/decisions/PDR-001..003` already exist and are
> *engineering* decision records (lint enforcement, no-defaults principle, Double DQN). This is a
> separate, independently-numbered **Product** Decision Record series living in
> `docs/product/decisions/`. The two series are not related and neither renumbers the other.

## Context

No product workspace existed. Nine months of commits (VFS, VTC, DAC, compiler, perf, security)
had accumulated against a strategy recorded nowhere durable, and the canonical narrative artefacts
had rotted: `docs/architecture/ROADMAP.md` is dated 2025-10-30 and says "Phase 3 Complete";
`README.md` and `CLAUDE.md` document config packs (`configs/L0_0_minimal` … `L3_temporal_mechanics`)
that **do not exist** on disk; `README.md` advertises 70% coverage against an audit that measured
19% and rated its own number unreliable. A stateless owner resuming cold would have inherited
nothing true. The workspace had to be constructed from evidence, not from a remembered history.

The same session surfaced something bigger than bookkeeping: asked who the product serves, the
owner reframed the product itself.

## Options considered

1. **Adopt the stated mission verbatim** ("trick students into learning graduate-level RL by
   making them think they're just playing The Sims") — pro: it is what `README.md`, `CLAUDE.md`,
   and `pyproject.toml` all say, so zero conflict with the repo. Con: the owner stated directly
   that this has evolved; seeding a superseded mission as authoritative would make every
   downstream bet answer the wrong question.
2. **Record the mission as ambiguous and defer** — pro: safe, no wrong commitment. Con: an
   unresolved vision is exactly the drift the workspace exists to prevent; every future session
   would re-litigate it.
3. **Record the pivot as stated, mark inferences explicitly** — pro: captures the owner's actual
   direction while keeping fabricated detail auditable and cheap to correct. Con: the repo now
   contradicts its own product workspace until the docs bet lands.

## The call

Option 3. The workspace records the product as **authoring-first**: *"the pivot in the vision is
from 'game as experience' to 'writing a game as experience'"* (owner, 2026-08-11). Purpose is a
**DRL substrate as code** enabling a **preset grammar of problems**, whose success condition is
that someone with a game-mechanic idea can build a DRL gym for it *trivially* — no Python. The
pedagogical Sims framing is demoted from mission to demonstrator use case. Audience is the sole
researcher/builder (primary) and other RL researchers / OSS users (secondary), with the *novice
author* named as the aspirational standard the substrate is judged against rather than a current
user. The three architectural pivots — UAC, BAC, one standard experimental compiler — are recorded
as the concrete arc of that vision, with honest shipped/partial/unbuilt status per pivot.

Every inferred claim is tagged `[assumption]` and every owner-stated claim `[stated]` in
`vision.md`, so the next session can tell evidence from guesswork.

The authority grant was proposed under the fixed taxonomy and **confirmed by the owner in-session**
(standard grant). It is authoritative, not draft.

The north-star was deliberately **not** set to test coverage, gate-greenness, or students taught.
Those measure output or origin-story, not the claim. It is set to **zero-Python authoring rate** —
the fraction of representative new mechanic ideas expressible as config with zero lines changed
under `src/townlet/` — because that is the only number that can falsify the central thesis. It is
seeded `UNMEASURED`; no bet may be accepted on north-star grounds until it is instrumented.

## Rationale

Option 3 beat the alternatives because the failure mode here is not "we picked the wrong bet" but
"we cannot tell what the bet was." The repo's own audit already demonstrates the cost: a public
README asserting a coverage number its architecture report contradicts, and a documented config
layout that no longer exists. Recording the owner's stated pivot immediately — while explicitly
marking what was inferred — converts a private direction into an inspectable one at the cost of a
temporary, *visible* contradiction with stale docs. That contradiction is not a side-effect to
regret; it is the Now bet's justification, and it is now measurable as a guardrail.

Setting an unmeasured north-star was chosen over setting a measurable-but-wrong one. A metric that
is honest and empty invites instrumentation; a metric that is convenient and green (coverage,
gates) invites the build trap — shipping architecture while the authoring claim stays untested.

## Reversal trigger

Reopen this PDR if **any** of the following:

- The owner confirms or corrects `vision.md` and any `[stated]` claim here is wrong — this PDR is
  superseded by a new one recording the correction, not edited.
- The **Zero-Python authoring rate** trial, once instrumented, shows fewer than half of the
  representative ideas are expressible in config alone. That falsifies "trivially" and forces a
  re-shape of the vision from *authoring is solved, surface it* to *authoring is not solved, build
  it*.
- The **Documentation truth** guardrail is still above zero confirmed false claims at the next two
  consecutive checkpoints — the Now bet is not converging and should be killed or re-scoped rather
  than continued.
- Any `[assumption]` tagged in `vision.md` is contradicted by the owner, most consequentially the
  demotion of the pedagogical mission to a use case.
