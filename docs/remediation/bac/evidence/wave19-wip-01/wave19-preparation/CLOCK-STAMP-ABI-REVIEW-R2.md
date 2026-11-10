# CLOCK-STAMP ABI scoped technical rereview R2

Reviewed current proposal SHA256 5251388f5ad7c0328b6be4825be595e4b3f8fafd2271f1babd6618ded8bac0f0 and design fix receipt SHA256 2728018c9862fa5ce798ba062611522d98c1c82a0d978be302a13a5188ce8f41; both independently match root's frozen references. Compared the preserved proposal R1 with the current proposal using a prose-only diff. Review is limited to R1-1/R1-2 and changed content/import-cycle handoff.

## Findings

- **R1-1: ADDRESSED.** The declaration explicitly sets `__hash__ = None`, accompanying prose promises identity equality with hashing disabled, and the finite matrix requires `hash(stamp)` to raise TypeError. EventId/ServiceClock value equality/hash remain intact. No content-hash or bank-dedup surrogate was added.
- **R1-2: ADDRESSED.** The later-owner handoff now explicitly requires source epoch+1, cleared active last-event caches, episode-local eligible cursor and cumulative service origin0, preserved actual restored episode identity, and inherited learned/history counters labeled as template data rather than active dedup IDs. Ordinary reset retains cumulative service and resume retains cursors. Required explicit current-format conversion/evaluation operations and source artifacts remain preserved while implementation stays outside this bridge. The final exclusions paragraph now reinforces that distinction.
- **Import-cycle handoff: ADDRESSED.** The added paragraph records WS importing RP and requires future reciprocal stamp consumption to avoid module-initialization cycles while retaining runtime validation. Local runtime imports with TYPE_CHECKING are an example, not authority for a new source or an assertion of an existing defect. This remains the root-attributed future dependency constraint from R1, not a new source inspection.

## Verdicts

**Specification: APPROVED for the narrow public primitive design handoff at the exact proposal SHA above.** Both required amendments are present; no unresolved R1 specification finding remains.

**Quality: APPROVED for this scoped prose rereview.** The proposed hash ABI is internally consistent and the changed content introduces no observed new contradiction or scope weakening. The existing split between typed immutable data and future live bank cursor/phase/receipt authority remains intact. Shared cadence and genuine private learning obligations remain intact.

This approval allows root to proceed with its tests-first authorization sequence; it does not itself authorize source/test mutation or runtime. No implementation, test PASS, actual-source review, CUDA qualification, consumer integration, or final BAC acceptance is claimed. Subsequent frozen implementation still needs the required causal RED/GREEN, preservation gates and fresh review.

Only this ignored R2 report was written. No source/test read, project runtime/import, Git/index/branch/worktree operation, repository/source copy, deletion, extra helper or subagent occurred. No optional extension or additional design programme is requested.
