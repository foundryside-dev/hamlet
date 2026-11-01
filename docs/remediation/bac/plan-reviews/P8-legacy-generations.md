# T33 legacy generations proposal — independent technical review r1

Verdict: **PASS — design only; no implementation or release approval.**

Reviewed artifact: `LEGACY-GENERATIONS-PROPOSAL.md`.
SHA256 before review: `b28387782a8e3f9b09d5644fd59461fa9ca4f3389d64d44cd090a934260bb18c`.
SHA256 after review: `b28387782a8e3f9b09d5644fd59461fa9ca4f3389d64d44cd090a934260bb18c`.
No material design correction required. Review was prose/metadata only; no additional source inspection, runtime, imports, tests, delegation or repository/index mutation.

## Technical findings

- Baseline preservation is explicit: sequential same-episode legacy publication continues to replace the canonical filename and complete canonical SQL row, with unchanged relative locator and public constructor; file-only recording remains supported. Legacy queue.Full handling retains warning/drop or error/None behavior, with strict qualified/bound alternatives. The separate dropped-frame ledger prevents those preserved no-throw calls from being misrepresented as complete durable episodes. No removal/degradation waiver is hidden in this proposal.
- Immutable generation artifacts plus independently copied atomic canonical aliases preserve prior receipts while retaining the latest view. The stable legacy namespace, positive legacy generations, scoped generation0, fresh nonce, exact reserved-run check and by-index lookup avoid both repeat collisions and provenance invention. A changed alias cannot mutate a prior artifact through a hard link.
- Companion schema2 and the new reserved binding honestly distinguish new work from unqualified v1 evidence. Canonical metric schema/admission remain unchanged. Refusing occupied v1/unknown families without adoption, migration or deletion preserves evidence; no supported baseline recording companion is displaced.
- Required generation/legacy locator keywords, exact row readbacks, immutable history rows and owned DB context provide a concrete producer/consumer seam. The canonical-first order and explicit uncertain-result states correctly acknowledge that filesystem and two SQLite commits are not one atomic transaction. Failed publication retains the actual immutable orphan/row identity and prior receipts; it cannot become file-only success or a fabricated rollback.
- Output-root lock before the DB guard gives a consistent ordering across same-root legacy publishers, including file-only overlap. The proposal correctly limits per-DB latest semantics when another DB or file-only writer subsequently replaces the shared alias. Scoped publications retain no-overwrite protection without acquiring unrelated legacy identity.
- Finite acceptance covers repeat publication/reopen, bound and legacy capacity routes, durable queue accounting, file-only/scoped contrasts, earlier-success preservation, association/version refusal and real second-family commit failure. Later T34/T35/PW11/T39/F14 responsibilities are named and remain acceptance obligations rather than waived gaps.

## Implementation prerequisites already required by the proposal

These are evidence/dispatch conditions, not new design scope or an additional design review loop:

1. Select the exact supported host lock facility before implementation dispatch, as the decision boundary requires. Its process-coordination claim needs a real independent-process contention/release witness; same-process recorder instances alone do not qualify that claim. Keep the lock inode persistent and failures explicit. The finite competing-publisher/platform qualification case owns this evidence.
2. Apply file-only success requirements by route: legacy file-only requires immutable artifact plus canonical alias; scoped file-only has no legacy alias, as publication step3 expressly states. Neither route requires nonexistent SQL success, and indexed failure never downgrades to file-only.
3. Freeze actual whole-file counts and propagate the changed interface/floors before affected dispatches. The proposed main context is four files/2800 lines, or five/3150 with its bounded reviewer probe; the separate unit context is five/2287. These are projections, not proof of final sizes. Downstream five-file T34/F14 contexts must be recounted under the unchanged 5000-line hard limit; the explicit required propagation cannot be replaced with these initial figures.
4. Do not treat this design PASS as runtime evidence. Preserve existing raw-writer/diagnostic controls, strict family admission, old evidence files, exact-source independent review, standing/full gates and final common-SHA reviews. Returned tickets and incomplete provisional groups must all have the honest outcomes specified here.

No additional user decision is required for the selected additive preservation design. Actual implementation authorization remains coordinator-owned under the existing workflow.
