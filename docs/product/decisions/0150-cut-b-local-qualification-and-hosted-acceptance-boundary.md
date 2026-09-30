# PDR-0150 — Cut B local qualification and hosted acceptance boundary

Date: 2026-10-01 Australia/Canberra
Status: **locally qualified; integration and hosted acceptance pending**
Author: Codex
Owner instruction: “excellent work, please plan and execute B”
Related: PRD-0003, PDR-0147, PDR-0149, `hamlet-89cae04b5e`, `hamlet-33e520cebd`, `hamlet-61e3de957f`

## Decision

Record Cut B against its own contract without weakening PRD-0003's evidence gates.
The implemented canonical variable model, shared symbol roster and typed token scope are
source-reviewed. Their final CPU qualification checkpoint is
`baced7dba659ab2024a3f164f18c450695000362`. Core authoring semantics landed at
`8060ef19b820ddada047570825865b69e6b38b3b`; isolated scope evidence is at `8a234b61`.

This is not a full product acceptance decision. The complete local suite passed: 4,055 tests,
18 skips, 84% coverage, exit 0. Ruff, Black, mypy, unchanged no-defaults whitelist and compiler
CLI fleet passed. Local integration verification follows this checkpoint. Feature publication
and exact-tip hosted checks remain pending.
Automatic approval review rejected private-source publication without explicit authorization
for GitHub. That external action will not be retried until the owner authorizes it.
No calendar deadline is added or silently extended for B.

## Evidence and consequence

Read all eight criterion findings, commands, artifacts, reviews, custody and exclusions in the
[qualification evidence](../evidence/declaration-cut-b/acceptance.md).
The required-variable catalog replaces the old authoring routes; schema **1.28** refuses old
artifacts. No compatibility readers, type aliases, fallback defaults or migration paths remain.
Internal compiler-owned profile execution products are not alternative authoring routes.

Direct-parent qualification: 31 cases / 884 readings, 212 exactly attributed identity movements,
no unexplained or stale attribution, byte-exact ten CPU trajectory sets and eleven reset censuses.
Frozen matrix: ten registered CPU cells, ten explicit CUDA skips, exit 0; verified old oracle and
fixtures unchanged. DIFF output identity is not confused with a learned-world change.

Close implementation and the specific omitted-symbol defect only after required local gates,
committed evidence and local integration are established. Keep acceptance task
`hamlet-61e3de957f` open until the exact pushed implementation's hosted checks are terminal-success
and a final accepting decision records that evidence. Cut A's hosted results do not qualify B.
A B draft PR must stack on Cut A's feature branch (#40) to expose the B-only change; local merge
remains `project-recovery-4`. No main merge, deployment, CUDA, browser, convergence, Murk or full
cognitive-domain acceptance follows from this decision.
