# Current state — Townlet · 2026-10-01

## Delivered and verified

Declaration-store **Cut A**, canonical-variable **Cut B** and **static epistemic access**
are accepted and consolidated on GitHub `main` at **`729779280820a31294013f9f7c839fbf23732ced`** (PR #42), as read at 08:17 UTC.
At that reading, local main matched publication, all 20 pre-consolidation local branch tips
were contained, and no additional committed branch work was found. Local main subsequently
advanced to documentation checkpoint **`792c6704`**; the repair branch is identified below.
[PDR-0154](decisions/0154-main-consolidation-and-product-checkpoint.md) records the pre-publication checkpoint;
[PDR-0155](decisions/0155-resume-reconciles-completed-main-publication.md) reconciles delivery at the 08:17 UTC resume.

| Package | Accepted contract | Qualification |
| --- | --- | --- |
| A | Content discovery, scoped declaration merge, collision/provenance diagnostics, single authored clock authority | [PDR-0149](decisions/0149-owner-extends-cut-a-acceptance-to-october-1-and-cut-a-is-accepted.md); exact implementation `75383d18` hosted gates accepted |
| B | Canonical variables, explicit lifetime/default/expression semantics, complete supported symbols and typed token scope | [PDR-0151](decisions/0151-cut-b-accepted-against-prd-0003.md); published implementation `22924d0a` hosted gates accepted |
| Static access | Required finite engine/agent read policies, engine/empty writers, independent exposure, checked ordinary/item access, immutable authority and policy-bearing cache/checkpoint identity | [PDR-0153](decisions/0153-static-epistemic-access-accepted-against-prd-0004.md); qualified execution `b70fda10` |

The static source passed **4,250 tests / 18 skips / 85% coverage**, all local lint/fleet gates,
31-case direct-parent comparison and ten frozen CPU cells. This is retained source qualification,
not a new full-suite run at the local merge. **201 postmerge checks passed** against
actual main-worktree imports. [Main integration receipt](evidence/main-consolidation/local-integration.json)
records identities, commands and preservation checks. Exact-head GitHub publication/checks are
verified separately in closed delivery issue **`hamlet-dd9a03f787`** and
[PR #42](https://github.com/foundryside-dev/hamlet/pull/42). Actual-main Lint, Config Validation
and Tests completed successfully; the retained hosted suite records **4,249 passed / 19 skips /
15 warnings**. [Publication reading](evidence/main-consolidation/hosted-publication.json)
records exact identities and run links. The resume reran no suite; a separate failed Dependabot
update is outside the delivery verdict. No release, tag or deployment is part of this task.

Three historical access defects are closed with bounded source/runtime evidence:
`hamlet-fc78bb49d3`, `hamlet-1a520475f4`, `hamlet-c78fbf32a3`. Owner/per-observer privacy
`hamlet-83a043a9b9` remains open. Unknown historical roles are refused, not implemented.

The owner's review of `72977928` exposed effect-admission refusal and canonical
variable-identity defects. Both reproduced. Local branch `fix/static-access-review`
now contains implementation **`7eb7ded3`** (following `c3faa4bf`): selected lifecycle writes authorize before
admission/reapplication, immediate nested denials restore runtime state, and structured
canonical identities retain distinct variables and origins. Deterministic lowest-free
item rows prevent rejected cascades from changing later allocation. **397 focused
item/effect checks and 988 compiler/oracle/access checks pass**; lint/type/no-defaults/fleet gates
pass. The final source's full suite passed **4,277 tests / 18 skips / 15 warnings /
85% coverage** in 989.23s, exit 0. `hamlet-f75ff623be`, `hamlet-bae419a592` and the
additional cascade defect `hamlet-940089c925` are closed against this local source. The repair is local;
published main's source and hosted qualification remain the historical readings above.
[PDR-0156](decisions/0156-static-access-review-refusal-and-identity-repairs.md) records
the repair scope, independent counterexamples and acceptance limits.
[Verification receipt](evidence/static-access-review/verification.md) banks the full
reading and skip disposition. No frozen trajectory or convergence campaign was rerun.

## Product judgment

The supported declaration → compiled state → checked runtime contract is stronger. The product
still has no freshly qualified multi-scenario compile → render → converge milestone. Static
policy tests do not establish trustworthy episode outcomes, full BAC cognition, browser behavior,
Murk integration, item ownership/locality, effect reset or portable model export.

Historical M4 remains four passing token architecture/aggregation cells at training `9d4e942f`,
one training seed and its fixed evaluation/budget protocol. It is not current-main multi-seed
convergence evidence. [Metrics](metrics.md) keeps those readings separate.

## Recovery exit and next step

Recovery remains open. **PDR-0058's register-growth trigger has fired:** A/B/static added
DIV-013/014/015 without terminalizing existing divergences. Reopen the oracle-retirement exit
framing for review; do not erase evidence, re-freeze the oracle or call registered differences
terminal because qualification passes. The existing exit is not met, and a main merge does not
meet it. [Checkpoint assessment](assessments/2026-10-01-main-product-checkpoint.md) records this
reading. No new exit definition or deadline is invented here.

The recommended next package is **truthful episode lanes**, starting from
`hamlet-d6fc84d147`: reproduce current main, then plan a bounded lifecycle/accounting contract
before another learning campaign. Proposed fixture: deaths at steps 2/5 give survival `[2,5]`,
seven live transitions, five vector ticks, one terminal/finalization each, and no post-death
replay/RND/annealing/bonus. Adjacent learner defects require reproduction before being treated
as confirmed scope. This recommendation is not authorization to implement it.

The initial resume reconciled publication. The subsequent owner review dispatched these
bounded contract repairs; no bet moved horizon and the standing authority grant remains
unchanged. Recovery is open. The repair/checkpoint branch is local only.

Next session: adjudicate the fired exit trigger, then source-reproduce and scope the episode-lane PRD. Keep effects reset and item fidelity as
separate packages unless the chosen scenario explicitly depends on them. The frozen oracle,
raw evidence and two unrelated dirty skill files remain preserved.
