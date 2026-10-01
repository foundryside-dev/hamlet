# Main consolidation README ground-truth review

Reviewed 2026-10-01 Australia/Canberra. The README at recovery head `ea9fc5fafe451cd59e7231ccef06d221e73ff99d` is identical to the inspected feature documentation head `2695962b`. Execution files (`src`, `configs`, `scripts`, `tests`, `pyproject.toml`, `uv.lock`, workflows) have no diff against qualified `b70fda104e5061ed2735e8b31b7f8f9caaf99f19`. No network or publication command was run, and no repository file was changed by this review.

Method: read PDR-0039 and PDR-0145; inventory branch/status/schema/platform/CI/compiler/policy claims; compare source, declarations, workflow files and retained exact-head execution receipts; test alternative interpretations before drafting. This is the ground-truth and draft-input stage, not the complete adversarial Gate 2 sign-off. The root will obtain an independent adversarial read of the replacement draft.

## Narrow corrections needed before the main merge

1. **README:8–9 — backend and immutability.** Replace “single frozen … executed GPU-natively” with a hash-carrying compiled artifact executed through a torch-tensor runtime. `CompiledUniverse` is a frozen dataclass with mutable nested contents; that is not deep artifact immutability. `DemoRunner` selects CUDA if available, otherwise CPU; current qualified evidence is CPU-only.
2. **README:27–47, 307–309 — main state and merge scope.** The fourth-merge account omits PDR-0146's fifth landing at `ea3648db`. Do not write the forthcoming local/GitHub consolidation as already landed. The initial read-only snapshot had local `main` at `04062872`; the root subsequently independently refreshed it to `origin/main` at `ea3648db`. This agent did not fetch or verify remote hosted status. Use a source-stamped candidate/landing record and the subsequent actual merge receipt, rather than a permanent “main trails the branch” or `origin/main` freshness instruction.
3. **README:56–74, 83–104, 461–553 — verification and CI stamp.** The claim that every current command/path/count was executed/read at `1eb347f7` is false after later Cut A/B/policy edits. Current source review is at `ea9fc5fa`; actual runtime/static gates are retained at `b70fda10`. Source proves workflow configuration only, not current hosted success. Keep old hosted readings explicitly historical or move them into linked PDR history. Consolidation hosted CI must remain pending until terminal success at its exact published head.
4. **README:54, 439 — divergence count.** Source register now has `DIV-001` through `DIV-015`, not twelve. Current matrix appends DIV-014 and DIV-015 to old hash bindings, with the six live input packs bound to DIV-015's complete byte inventory. Historical four-entry descriptions must be unmistakably historical.
5. **README:240–244, 603–609 — complete canonical variable contract.** Add required `readable_by`, `writable_by`, independent `exposed_to`, engine-read requirement, engine/empty writers, immutable initialization/reset, qualified item authority, known-write/compiler refusal and permission-bearing checkpoint identity. Deleted `vfs_profiles.yaml`, `variables_reference.yaml`, duplicate registry and old actor aliases have no live reader.
6. **README:570–580 — artifact version and integrity.** State compiled schema `1.29`, with exact-version load refusal and required policy/coherence checks. Distinguish it from `compiler.py`'s authored schema `1.0`, compiler version `0.1.0`, and checkpoint format `6`.
7. **README:642–646 — presentation compiler contradiction.** The claim that no compiler stage or hash sees `presentation.yaml` is false. `RawConfigsV21.from_declarations` validates the presentation family; `config_documents()` includes it in fingerprint/mtime. It does not enter world-semantic hashes or change execution. The earlier pack-layout paragraph already states the correct behavior.
8. **README:650–667 — delivered work.** Add accepted declaration-store Cut A, canonical variable Cut B and static epistemic access, linking their bounded acceptance receipts. Do not imply these finish BAC cognition, UX, convergence, Murk integration or broad privacy.
9. **README:762–793 — pack/program census.** Current transport-file census is 30 packs, 27 positive packs, 35 total levels and 32 positive levels (three named negative fixtures). Current `static_epistemic_access` has two ADVANCE action writes; “action_write empty in every pack” is false. Prefer discovery-driven claims over new brittle counts. Social-residue fleet emptiness remains a separate claim; do not infer it is now exercised because action writes are.
10. **README:744–777 — repaired cache failure.** Remove the current-tense rough-edge heading claiming successful compile can silently fail to cache; its own paragraph says fixed. Keep any historical account in a dated decision link. Do not confuse that repaired failure with the still-excluded initial-item-appearance cache gap.
11. **README:891–916 — document inventory.** PDRs now extend through 0153. The old thirteen-schema/banner census was stamped at `1eb347f7` and cannot describe rewritten declaration/variable docs today. Prefer links with source authority and archive status rather than a fresh unverified banner count.
12. **README:739–743 — frontend claim strength.** Package scripts and three test files exist, and no workflow installs Node. A new frontend build/browser run was not executed for this checkpoint; describe wiring and retain historical frontend execution as history, not fresh acceptance.

## Verified stable content that can stay

- `townlet` distribution/source identity, version 0.1.0, alpha classifier and Python requirement `>=3.13` (`.python-version` 3.13), from pyproject/source; 16 immediate source packages remain.
- Both full README YAML examples parse identically to current `stratum.yaml` and L1 `drive.yaml`.
- Five default levels still share meters/affordances/reward declarations; partial vision and temporal runtime settings distinguish their execution. No new default multi-seed learning result is implied.
- Content-based nested declaration discovery, pack/level scope, complete level brain replacement, five scalar training overrides, canonical extents and linked clock authority are real source paths.
- Supported four BAC architecture selectors, token ABI and shared checkpoint identity/format 6 remain real; layer 1/3 and general policy export remain intended.
- Compile/validate/inspect and training/serving command forms remain wired. No new training/server/browser campaign was executed by this audit.
- Four workflow files configure Python 3.13/all-extras; three push/PR jobs target main and project-recovery*, and the full workflow configures dispatch/nightly. No Node/frontend, oracle, unified demo or convergence workflow is present. Bare pytest no longer deselects `slow`.
- Local tag inventory contains two oracle tags. This does not establish current remote release inventory.

## Evidence and checks used

- Read PDR-0039, PDR-0145/0146 and PDR-0153; current README; pyproject, four workflows, package scripts; compiler discovery/hash/load, registry policy, checkpoint gate, runner device path and pack-smoke sources.
- `git diff --name-only b70fda10 HEAD -- src configs scripts tests pyproject.toml uv.lock .github` and same comparison from `ea9fc5fa`: empty.
- `git diff --name-only ea9fc5fa HEAD -- README.md`: empty.
- Read retained static-access `local-gates.json`: all local gates/full suite/parent/frozen terminal zero at exact b70fda10; `local-integration.json` records recovery merge and preserved execution source.
- Parsed YAML fence blocks against their actual config files; equality true for both.
- Read-only filesystem census and source register/package/class inspection produced the current counts above; no fresh compiler/cache/browser/CUDA/training run was invented.

Draft scope: remove or clearly segregate stale hosted/history claims, keep supported quick-start and authoring intent, summarize accepted bounded contracts and honest operational gaps, and point to exact qualification receipts. The final hosted-main CI/merge result must be recorded by the root after it actually completes.

## Replacement draft

Prepared `/tmp/hamlet-main-checkpoint-README.md` from the verified sources above. It preserves the actual YAML examples, supported quick-start commands, architecture and oracle contracts, historical M4 witness and concrete remaining work. It removes brittle fresh-looking historical CI/run/census claims, names source review at ea9fc5fa separately from qualification at b70fda10, and leaves consolidation hosted acceptance pending. This agent performed the source sweep and drafting; independent adversarial review remains a separate required step, not implied by this report.
