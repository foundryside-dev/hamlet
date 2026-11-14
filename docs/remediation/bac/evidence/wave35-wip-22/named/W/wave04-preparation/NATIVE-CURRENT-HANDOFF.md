# Native current checkpoint handoff — T24/T25

Technical disposition: PASS for this finite interface clarification; native integration evidence remains BLOCKING for T24/T25 closure. This is neither runtime approval nor full BAC closure. Existing P2, approved historical Option A, T40, final independent reviews and all required gates remain binding. No new task or capability removal is authorized here.

## Evidence and responsibility

Reference evidence: `T10-fixed-independent-review-r2.md` and `T10-fixed-independent-runtime-r2.json` in this directory, reviewed as prose/data only. The independent reviewer reports 17 passing controls, ten diagnostic unexpected HC acceptances and one archive-placement observation on candidate `c82ca8362b9f2be98a60b722308951d7104392f8`.

HC access classification/owned preparation is not complete current checkpoint admission. Its `validate_legacy` callback does not certify current population, learned state or every replay tensor. Preparation accepted current replay with shortened observation/action columns, contradictory action width, invalid legality mode or unknown keys in both requested native modes; actual RB validation refused these cases atomically. No installed malformed learner state was demonstrated. Do not label those HC artifacts fully validated or close the downstream gap on classification success.

The same evidence found four historical rows preserved inside current replay but omitted from HC top-level accounting; mirroring the archives at the outer level yielded four. This is an open native transport/accounting obligation, not evidence of destruction and not optional cleanup.

T24/T25 own native producer/consumer integration and executable closure of the contracts below. Existing actual storage validators remain the authoritative validators for their formats. HC retains classification, archive validation and owned cloning; its output must be described as prepared/unadmitted until native validation and reconciliation succeed. These observations do not establish a need to retrofit HC into a universal current learned-state validator now. Native consumers must not bypass validation by treating its access policy as an admission receipt. A reusable HC reconciliation helper is permissible within existing ownership, but does not discharge native end-to-end tests.

## Current native admission and atomic installation

For supported native demo10/population7, both recorded_full_resume and inference admission must:

1. Classify the requested access and prepare owned input without installing live state.
2. Invoke the actual applicable current population, replay-kind and learned-state validators off-side; validate exact schemas, cross-field shapes/counts, dtypes, action vocabulary, legality declarations, reward/component metadata and compatible module/optimizer state. Validate the complete supported transport before reporting accepted native admission; inference must not accidentally attest malformed replay merely because it will not sample it.
3. Validate and reconcile archive transport as specified below before computing accepted access accounting.
4. Prepare the requested mode's complete installation off-side, including mode-specific clocks/RNG/resource handling. Only after all validation/preparation succeeds may live tensors, clocks, RNG or resources be installed. Preparation must not advance live RNG or mutate source aliases; dispose of temporary resources on failure.

A malformed rejection leaves the supplied payload and existing target state/resources unchanged. Test a populated target, not only a fresh target. Success installs owned state according to the requested mode; no alias to mutable caller payload survives. Never report successful full resume before the whole operation succeeds. Preserve existing inference isolation requirements and current full-resume continuation guarantees.

## Canonical historical archive registry

The native demo10/population7 producer emits an explicit outer `historical_archives` registry, including an empty registry when no history exists. It is the deterministic, domain-aware deduplicated union of all history owned by the native checkpoint, including archives nested in serialized buffers. Use existing validated archive records and their canonical state/domain identity, not raw pickle identity or a new invented provenance domain.

Validate each archive's schema, declared source-format domain and canonical state digest before deduplication. Equal identity requires identical archival content; contradictory records must be rejected, not resolved by choosing one. Preserve original rewards, priorities, episode boundaries, dtypes, query/export semantics and provenance. Equal-looking state from distinct legitimate source domains must not be conflated. Deterministic ordering must be defined by the implementation and verified by tests.

Every nested buffer archive, when present, must have an identical validated record in the outer registry. Missing outer transport, omitted nested members or contradictory content is a native admission error; no accepted full-resume result with misleading zero accounting. The outer registry may contain additional history that is not installed in the current active buffer, including history of another replay kind. Therefore enforce nested-subset consistency, not unconditional equality. Do not attach incompatible history to a different-kind active buffer merely to force equality; preserve it as native-owned history for query/export and subsequent saves.

Compute archived-row accounting once from the validated canonical outer registry, counting each archive identity once across duplicate references. Count archive records' validated row populations, not active replay readiness and not nested-plus-outer totals. Deduplication is by archive identity, not presumed overlap between distinct historical datasets. All native admission results and serialized summaries must agree with this accounting. A malformed or contradictory registry cannot be silently repaired into an apparently accepted checkpoint by the consumer.

These current-native rules preserve genuine old demo9/population6 Option A dispatch: validate/archive old history, preserve artifacts, restore permitted learned state/clocks and begin fresh qualified active replay. They do not add an outer-registry requirement to old wire formats. Preserve standalone current replay5 archive query/export and its honest standalone provenance; native wrapping must explicitly construct the canonical outer union rather than invent native provenance for those archives.

## Finite executable acceptance owed by T24/T25

- Current-native negative matrix in both requested modes: shorten observations/actions/rewards independently; mismatch declared sizes, action width, legality mode and component metadata; introduce unknown fields and malformed learned/population state. Actual native entry points must reject before installation, including cases HC alone currently classifies. Exercise applicable replay kinds through their actual validators.
- Archive negative matrix: missing outer registry, omitted nested member, altered outer state/digest/domain, and contradictory duplicates. Refuse honestly with no accepted accounting or installation. Valid duplicate references count once; distinct domains remain distinct. Extra valid outer-only history is preserved, not rejected or dropped.
- Atomicity/ownership: malformed loads against populated targets leave target tensors, optimizer state, clocks, RNG, pending/live resources and source payload unchanged; include late validation failure after earlier preparation. Mutating caller input after successful load cannot mutate installed state or archives, and mutating exported/query results cannot mutate retained history.
- Actual native save/load end-to-end: canonical empty; captured qualified replay without history; archived history plus fresh empty active replay; captured qualified replay plus history; and outer-only different-kind history. Verify full-resume replay/tail, learned state, clocks/RNG continuation, truthful archived counts, query/export and a second native save/load with no history loss or doublecount. Include valid inference admission/isolation controls.
- Regression controls: genuine old9/6 Option A remains archive-plus-fresh0 with preserved artifact/query/export behavior; standalone replay5 archive access remains supported. No old unmasked optimizer admission is introduced.

Record exact candidate/source identities, actual entry points, executable results and independent review evidence in the T24/T25 closure ledger. Until these pass, native validation/accounting handoffs remain explicit blocking dependencies. Classification-only demonstrations, storage-only tests and this prose review do not close them.

## Review limits

This reconciliation reads only the independent review report and result JSON; no additional implementation/helper/test source, runtime, import or probe was used. Technical review finds no material contract conflict in the finite handoff above. Existing user authority permits the additive strict current-native boundary; this text does not waive policy decisions or authorize a supported capability reduction.
