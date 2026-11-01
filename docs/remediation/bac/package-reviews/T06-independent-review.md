# Review provenance

Final bounded source/spec review; runtime qualification is supplied by the coordinator.

Original artifact: `T06-preservation-astra-review-r5.md`; SHA256 `242c9a3ccb556ecc63b8664e9fb6594c0ce05e5461605bd869f562bed1e9f465`. The original is retained unchanged. This portable rendering normalizes execution paths; it does not alter the review verdict or source binding. The final reviewed source hashes match sum tree `1a1ca88cab7cc5bfe97e0922534d23e733d17e2d`, identical to qualified source release `eb73173496a7955b30a6fea4b65ccae8cc615b87`. Earlier source identities and staged-candidate bindings in the body retain their original meaning.

# T06 preservation repair: independent R5 review

**Verdict: scoped static PASS.** The actual R5 implementation repairs the identified P2 constructor/pre-start preservation regression without permitting helper-only inputs through runtime admission. No unresolved P1/P2 or optional P3 finding is raised in this five-source lens. Runtime qualification remains root-owned and outstanding for this report; this is not a release or full-repository PASS.

## Exact reviewed candidate

Manifest `wave05/green-r5-candidate.json`; HEAD `23755537926c2808c8b312f4f5b52ad76ab594ab`; candidate tree `1a1ca88cab7cc5bfe97e0922534d23e733d17e2d`. Independently checked HEAD, five whole-source hashes/counts, empty unstaged diff and empty index-versus-candidate diff before and after review.

| Whole source | Lines | SHA256 |
|---|---:|---|
| src/townlet/demo/unified_server.py |616|626634171c744ecac9ac825f5db5727e3407031efd6c8fe0dcac5a1058e2a02c|
| src/townlet/config/resolved_launch.py |102|b55b4b816b02b167ee963a9a443045bff9b26d2ec5e3a0307026253767fe939d|
| src/townlet/universe/errors.py |97|af30223624658d5d9cad3f56232353433f72a340d1fdb4caec69b581f91c2a53|
| tests/test_townlet/regressions/bac/test_launch_transport.py |580|1bceb21245ebeff9ba6bc93d10603f669d964d2dbbfebdcfed56fbf8f3910d91|
| tests/test_townlet/unit/demo/test_unified_server_unit.py |122|0e4e90f087d69772ba25438871f4b4c19618a1076d73546246f6ae4a63eaaa28|

Total **five files / 1,517 lines**. Read the repair plan, original preservation review and manifest prose/data. Producer and public-loader contracts come from the root-supplied receipt/plan and previous source-verified preservation report; declarations, training DTO, CLI and Runner were not reopened in this lens. No imports, tests, runtime, probes, source/index edits, source copies or delegation.

## Actual behavior and adversarial assessment

Conventional selected training-path existence retains lazy constructor admission and initializes ordinary component handles and shutdown lock. Neither malformed standalone DTO content nor absent unrelated pack declarations is eagerly used to reject this historical constructor domain. Direct-level input normalizes to the root and refuses conflicting explicit selection with a located DECLARATION_SCOPE issue. Public arguments/order/defaults and immutable constructor total_episodes request semantics remain unchanged. Nonconventional input still calls the real resolver; the compatibility branch is not a new filename prerequisite for renamed or multidocument valid packs.

Unresolved helper state explicitly has `resolved_launch=None`, `training_config_origin=None` and its actual conventional path. No compiled/effective identity is fabricated. A helper first attempts full resolution; successful resolution installs the selected compiled level's training DTO and validated absolute path:positive-line origin. Installation obtains and validates both origin and DTO before assigning state. A later helper call returns its existing cache, consistent with the historical lazy/cached contract.

Fallback catches only CompilationError, inspects actual structured issues, requires a nonempty list, and accepts every issue only if code, exact required-family message and directory location match the supplied discovery contract. Pack locations must equal root:1; level locations must be direct children of root/levels at line1. The conventional selected path must still exist and equal the helper path. Plain-string errors have code=None in the verified errors API and cannot qualify. Mixed issue sets, generic missing messages, malformed paths and other codes cannot qualify. The level-location check deliberately admits other level directory names because missing families in other declared levels are legitimate full-discovery blockers; that is not permission to run the partial pack. This classifier is coupled to the supplied producer diagnostic ABI, with a conservative refusal on changes, not arbitrary formatted-text recovery.

The unchanged public standalone loader still validates the actual DTO after qualifying missing-only discovery. It neither substitutes default training fields nor converts an invalid DTO into success. Nonmissing duplicate/syntax/scope/sidecar diagnostics propagate intact. No broad exception catch conceals a failure. Retaining a cached helper DTO after files change is historical helper caching; it cannot become stale runtime admission because `start()` always calls `_admit_launch()` first.

Real `start()` resolves and installs complete selected configuration before checkpoint naming/mkdir, snapshot copying, file logging or thread creation. It does so even when a standalone or previously compiled helper DTO exists. The runtime path has no standalone fallback. A failed re-admission leaves previously obtained helper state available but starts no server resources; that state does not authorize start. A successful re-admission replaces the standalone DTO/origin with the compiled selection. Resolver-owned compilation/cache effects are not claimed absent; the ordering guarantee concerns server runtime resource side effects.

Snapshot, metadata naming, file logging and stop behavior remain available to the original pre-start helper domain; the three original unit tests remain byte-identical. No fixture conversion, assertion deletion or full-pack requirement was inserted into those tests.

## Regression quality and remaining execution

The original real CLI/Runner/Server transport matrix remains in the counted source. The CLI uses actual main/parser/server construction and a bounded start seam; it does not qualify real sockets or threaded training. The added twelve cases cover standalone pack/direct-level helpers and lazy DTO validation; explicit/auto checkpoint refusal after caching; duplicate, YAML syntax, scope and both recording-sidecar invalid placements; located direct-level conflict; and replacement of cached standalone state by full runtime admission. Negative inputs are first established as valid standalone/missing-only inputs, then corrupted, and compared with real resolver issue lists. Start-refusal tests assert missing resources and fail if resource helpers are entered. The successful admission test executes actual start until the first resource boundary and checks selected compiled object/origin installation before intentionally stopping execution.

Root reports R4 causal RED for all twelve new cases plus constructor errors in the three unchanged unit helpers. That is attributed historical root evidence, not this reviewer's execution. R5 new-case/unit GREEN, complete 53-case matrix, affected owner suites, guards and full repository qualification must be attached by root to the final candidate. Historical R3 41-case PASS and unchanged CLI/Runner hashes do not alone qualify changed R5 SERVER behavior.

## Required handoffs

T07 retains canonical standalone producer/public-loader discovery ownership; this compatibility adapter does not claim that broader implementation is complete. T32 retains actual live/evaluator content transport and readiness, beyond bounded start seams. T36 must serialize authored/effective identity and actual request provenance distinctly; `None` helper provenance must not be promoted to compiled identity, and a required constructor count is not evidence of a CLI flag. Existing T24/T25 native and T34 lifecycle/drain obligations remain open. No whole-BAC, end-to-end hosting/inference, learning or final closure claim follows.
