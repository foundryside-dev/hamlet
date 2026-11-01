# Review provenance

Historical finding/review; see the final implementation receipt for repair and qualification.

Original artifact: `T06-independent-review-r0.md`; SHA256 `60dfa3a7eb9c52aa4596cdf011b360ae6b85ad26cb9f6bdfd5ed03b1b0cae3db`. The original is retained unchanged. This portable rendering normalizes execution paths; it does not alter the review verdict or source binding. This artifact describes its recorded earlier source. The repaired implementation and final review are linked from the package receipt; final qualified release `eb73173496a7955b30a6fea4b65ccae8cc615b87` has sum tree `1a1ca88cab7cc5bfe97e0922534d23e733d17e2d`. Historical findings below are not current unresolved findings.

# T06 independent source/spec review r0

Verdict: **PASS for bounded static T06 design/implementation review**. No concrete unresolved P1/P2 or in-scope blocking gap found. Runtime/owner/full qualification remains root-owned and unclaimed here. This is not whole-BAC/final approval.

Exact HEAD verified `23755537926c2808c8b312f4f5b52ad76ab594ab`; index equals frozen candidate tree `1ecb3cea003062964605a2dde6854c41cad34ab8` (`git diff --cached <tree> --name-only` empty); no unstaged tracked drift (`git diff --name-only` empty). Manifest is wave05/green-r0-candidate.json. All14 existing worktrees were listed and preserved. Source hashes matched manifest before verdict.

| Whole scoped source | Lines | SHA256 |
| --- | ---: | --- |
| scripts/run_demo.py | 215 | 0029a2d758ed45907be30c6e8a21003798ddaef99dad392acc2c8a0ce3abd43a |
| src/townlet/demo/runner.py | 1001 | 94842641bdce645fdd90d188d5bbdf6e09e7f4c071d15756202e173acd47c15d |
| src/townlet/demo/unified_server.py | 542 | 7789de97326fadd9f828df5c41f6c5641ceda709e7b44f57235e4485c381f1ad |
| src/townlet/config/resolved_launch.py | 102 | b55b4b816b02b167ee963a9a443045bff9b26d2ec5e3a0307026253767fe939d |
| tests/test_townlet/regressions/bac/test_launch_transport.py | 325 | 97bd7d30839b72edbb40fc25cd612bce75407ca9db588f17aa55600e9ac6f82f |

Exactly five whole source files/2185 lines. No sixth unit/server/live/DTO/helper source, imports, runtime/test/probe, source/index change, staging/commit, branch/worktree/source copy or delegation. Only this ignored report was written. Read T06 brief/preparation/phase2 authorization, real-server capsule, launch-loader interface capsule and P1/D20/B12/T32/T36 prose contracts. At review time no T06 phase2 work report was discoverable under the supplied preparation directory; root was notified. Its absence is an evidence-document limit, not a source defect or presumed runtime PASS.

## Actual candidate reassessment

CLI now calls actual resolve_launch before dispatch, retaining argparse flags/requiredness and explicit max-episode transport. Omitted episodes reads effective.training.training_loop.max_episodes; explicit value is retained without mutation of authored DTOs. Its log distinguishes authored count, explicit --episodes and omission. No experiment.yaml/training.yaml presence gate or conventional training reread remains in this consumer.

Actual UnifiedServer construction also resolves root/selected level, preventing the previous independent renamed-training gate from surviving a superficial CLI repair. It stores selected compiled.get_level(level).training and `_load_training_config` returns that original DTO. `_determine_run_directory` therefore consumes actual discovered run_metadata, including multidocument declarations, with existing sanitization/missing metadata behavior. Constructor argument names/order/defaults are preserved. Required total_episodes is recorded in MappingProxyType launch_request expressly as a constructor request; code does not claim it proves a CLI flag.

Actual DemoRunner similarly resolves/compiles before checkpoint directory, database or TensorBoard allocation, then uses the selected DTOs and compiled/effective object. It does not compile a second time inside the constructor or reopen training YAML. max_episodes explicit/omitted behavior remains3/authored100000 for the fixture; launch_overrides is an immutable mapping of the actual explicit argument only. This is appropriately distinct from server request provenance. Constructor signature remains compatible, with added unambiguous/direct-level inference through its existing optional level argument. force_new_vfs and max_environment_steps paths remain present; explicit step-budget validation precedes resource allocation.

Both runner/server retain full training_config_origin and derive training_config_path by rpartition of the final colon, requiring an absolute path and positive numeric line. Thus filenames containing earlier colons and genuine multidocument line locators are handled without treating the complete locator as a filename. These fields are diagnostic provenance; they no longer drive a fixed-file parser.

Root/direct-level/conflicting/unknown/ambiguous selection is delegated to unchanged LR. A direct levels/<name> path selects that name and normalizes root; conflicting explicit selection refuses rather than silently switching. Pack explicit selection and singleton inference are deterministic. CLI --level stays required and server's existing default level remains the same. Complete authored pack validation remains strict. No standalone section-only public loader is inadvertently routed through full compilation by this T06 change; that separate T07 contract is untouched.

## Adversarial hypotheses and evidence limits

- Removing only CLI checks while real SERVER still rejects renamed/multidocument training: refuted directly by constructor/cache source and independent real-server regression cases.
- Using ResolvedExplorationPolicy or an invented compiled top-level training field as the original DTO: refuted; actual consumers call get_level(selected).training.
- max_episodes override silently changing authored/effective hashes: refuted by assignment paths; only runtime count/receipt changes. Full immutable provenance publication is later T36 work, not claimed here.
- Origin locator accidentally opened as a file: refuted by source; split is validated and selected DTO is reused.
- Invalid discovery causing new DB/logger leaks: resolver and origin validation now precede runtime-resource allocation in RR; SERVER constructor has no started threads/resources. Later constructor I/O failures and runtime shutdown/recorder cleanup are preexisting lifecycle owner concerns, not established fixed by this transport patch.
- All valid transport forms being constrained to the four test names: refuted structurally; no whitelist of test transports exists. LR owns enumeration/scoping and ordinary constructor behavior is preserved. Static review cannot prove every compiler transport on every runtime profile.

The counted regression executes a real CLI subprocess/main/parser and real UnifiedServer constructor, patching only start with a bounded seam that calls actual training loader and run-directory derivation then stop. It does not replace the compiler/resolver/whole server. The same file separately constructs real RR with context-managed DB/logger cleanup and restores process signal handlers in finally. Native YAML copies are DATA. Compiler-valid fixture transformations are checked against conventional execution identity before consumer assertions. Tests cover conventional/renamed-training/renamed-experiment/multidocument, explicit3/omitted100000, direct-level including renamed experiment, required parser arguments, missing-training/conflicting-level located diagnostics and runner override mapping mutation refusal. The tests are causal for the requested seam; actual server sockets/background threads, a training run, GPU and learning quality are intentionally not their claim. I did not execute these tests or substitute historical results for current results.

## Required downstream handoffs, not closure

**T32:** current evaluator must consume LR/EV and qualified inference, preserve all declared-family calling/reset/state behavior and retained historical FF instrument scope. SERVER source forwards normalized root/selected level/total count to LiveInferenceServer, but that uninspected implementation and actual server/evaluator readiness are not qualified by the bounded start seam. Carry content transport to the actual later consumer; do not label this T06 result an end-to-end hosting/inference PASS.

**T36:** consume actual authored/effective configuration plus explicit RR launch_overrides and SERVER constructor request, preserving the distinction from CLI-origin logging. Do not infer “CLI override supplied” from every non-None server total. Persist/report runtime requests separately from authored/execution hashes and include real units/roles/intervention effects. Existing runner hardcoded telemetry/intervention behavior is not repaired or requalified here. Do not let an immutable mapping be mistaken for an already serialized run provenance record.

Existing T24/T25 native admission and T34 drain/cleanup/status obligations remain required; this patch's early validation order and successful test resource scopes do not close them. Existing ownership and actual tool approvals continue to govern, with no failed-rule authority or user-only fallback inferred.

No optional P3 is raised. Scoped static PASS is ready to combine with root's exact-source collection/focused/owner/static/full evidence; no release or final closure follows from this report alone.

## Phase-two receipt reconciliation addendum

Read `T06-phase2-work.md` after root supplied the previously unavailable producer receipt. Its five line counts and SHA256 values exactly match this review's inspected 2,185-line source set. Its implementation account agrees with the actual source reviewed: CLI selection/default episode cap and request logging; early Runner resolution, selected DTO/origin preservation and immutable explicit overrides; actual Server constructor resolution, cached selected training/run metadata and constructor-request provenance; preserved signatures; required T32/T36 handoffs. No substantive discrepancy or additional P1/P2 finding arises. This resolves the earlier documentation-availability limitation only.

The receipt explicitly claims no runtime PASS. Producer Black/Ruff results are attributed producer evidence, not independently rerun in this addendum. No extra source, imports, runtime, tests, index or production edits were used. Root reports the same five source hashes and R2 quick static guards PASS; final R3 manifest binding and the 41 runtime cases remain outstanding and are not inferred from that report. The scoped static PASS and its downstream limitations remain unchanged.

## Frozen R3 binding

Bound the existing scoped T06 static PASS to `wave05/green-r3-candidate.json`, candidate tree `f372de50f0efce29229855eb9fe4b6d09bff5d53`, over HEAD `23755537926c2808c8b312f4f5b52ad76ab594ab`. Read the manifest and independently confirmed HEAD, empty unstaged diff and empty index-versus-candidate-tree diff. The five T06 source SHA256 values were rechecked and remain identical to the original reviewed inventory (2,185 lines); no additional source was inspected. Changes elsewhere in R3 are outside this T06 review and receive no inferred approval.

This is a static source-identity binding only. Root-owned actual T06 41-case GREEN execution remains pending; no runtime was run by this reviewer. T32 and T36 handoffs above remain required, and actual end-to-end hosting/inference, provenance publication, lifecycle/native obligations and whole-BAC/final closure remain open. No source or index changes were made.

## Preservation finding supersedes release readiness

Subsequent bounded actual-owner review found a P2 regression in training-only UnifiedServer construction/pre-start helpers. See `T06-preservation-interface-review.md` for five-source baseline/current evidence and additive repair. Earlier static PASS and R3 binding do not discharge this newly established preservation requirement; T06 release remains blocked until repaired and verified. No runnable partial-pack support is asserted or required.
