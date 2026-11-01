# Review provenance

Historical finding/design review. The source identity in its body is historical; final repair and qualification are recorded in the implementation receipt.

Original artifact `T07-astra-review-r0.md`, SHA256 `28a823b2e9a280db56da5aee20715d995ca5303ed7ae2a2f8c407701e2f58d24`, retained unchanged. This portable rendering normalizes execution paths. Runtime results are coordinator-attributed unless the body explicitly records reviewer execution.

# T07 independent actual-source/spec review, pre-freeze r0

**Verdict: one confirmed static P2 preservation defect; repair and causal qualification required.** No P1 identified. This is a PRE-FREEZE scoped review, not common-candidate binding, runtime GREEN, release or final BAC closure. T12 has an authorized active writer; T07 production is intentionally unstaged relative to the test-only RED index. No whole-workspace freeze/index equality is asserted.

## Inventory and evidence

Read exactly five whole current source files, **1,269 lines**. Verified these hashes before and after review:

| Source | Lines | SHA256 |
|---|---:|---|
| src/townlet/universe/declarations.py |751|f34ac03d4084c2531643ca0837649d78d7a2dc67e3dcd05795423c3017d5510c|
| src/townlet/config/resolved_launch.py |155|8a704a5375c4dbcb9223c10d08a1fbae1041fdbb2627e866df4f2842ac6c06a1|
| src/townlet/config/exploration.py |28|b5292e6d193ab224e76f727b63d9e078fdac0ca706ae0ee7f58e7f723302951d|
| src/townlet/config/curriculum.py |20|a65e3a3b4d02182f96e56d0ad3fd93c72b7e9921b64b5f9c272456250d620227|
| tests/test_townlet/regressions/bac/test_public_loaders.py |315|f5987faba72c1f74da1086d42f99793cd1149f9505c44e01224bba2c2dfa2c47|

Consumed current T07 brief/activation notes, accepted launch-loader-interface-reconciliation capsule, task-T07 and the original sixteen-node consumer audit. Baseline standalone API facts are source-verified in those receipts; no sixth DTO/compiler/helper/owner-test definition was opened. Root reports RED36 intended failures/7 positive PASS, existing51 legacy owner PASS, collection170 PASS and69 source/input/index guards intact. Those are attributed prior root results, not this reviewer's execution or proof of current production GREEN. No imports/runtime/tests/probes/source/index edits, write-tree, copies, branching or delegation occurred. Only this report is written.

## P2: unrelated level diagnostics defeat local/direct target preservation

**Location:** `resolved_launch.py:66`, before target selection at68–84; `declarations.py:148–157` calls the unrestricted recursive inventory and raises all its issues before selection.

The accepted capsule states that old loaders read the requested section directly from the input directory, that a valid local target remains valid when unrelated level directories exist, and that direct-level selection chooses that local scope. The consumer audit explicitly distinguishes duplicate selected targets from unrelated levels. Current `discover_sections(root)` instead parses and validates every declaration in every level. `_consume`, `_normalize_training` and `_add` collect unrelated scope/sidecar/duplicate issues, then line157 raises them. The resolver never reaches its otherwise correct local-first selection logic.

Concrete static counterexample, requiring no compiler/DTO speculation:

1. Put the counted test's valid `TRAINING` document in `root/training.yaml` (epsilon_start0.8/end0.1/decay0.9).
2. Put a valid wrapped training document in `root/levels/other/training.yaml` and a second copy in `root/levels/other/duplicate.yml`.
3. Call `load_exploration_config(root)`.

The historical local loader reads only root/training.yaml and returns its valid ExplorationConfig. Current `_add` reports duplicate singleton training at scope `other`, `discover_sections` raises, and local selection is unreachable. There is no duplicate in the requested local scope. An equivalent direct-level counterexample has valid target A and duplicate training in sibling B; requesting A now fails because B is inventoried first. Invalid recording sidecars or malformed YAML in an unrelated sibling trigger the same coupling.

This is a capability restriction in the preserved standalone/direct-section domain, not a request to make an invalid complete pack runnable. Full `discover` must continue rejecting all such invalid pack content. Selected-scope duplicate/wrapper/sidecar/transport failures must also remain strict. The required correction is explicit scoped section inventory/selection with the needed authored clock dependencies, not catching arbitrary errors after whole-pack discovery, weakening full discovery, or retrying a conventional filename.

Bounded controls: add a valid root-local target with two duplicate declarations in an unrelated child, and a valid direct target with an invalid sibling; assert original target DTO success across conventional/renamed/multidocument target transport. Negative controls move the same duplicate or malformed sidecar into the selected scope and require its original located refusal. Retain a full-discover control proving the entire invalid pack still refuses. Existing `test_public_loaders_root_local_target_wins` uses only valid children, so does not detect this regression. Root should execute these only after synchronized authorization/freeze; no runtime witness was fabricated here.

## Refuted hypotheses and correct portions

- Full compilation is not forced on minimal inputs: `resolve_config_section` calls explicit section discovery, never UniverseCompiler.compile or resolve_launch. Minimal wrapped training with only exploration and numeric standalone curriculum need no complete pack/training DTO.
- Public DTOs, exports and loader arguments are retained. Exploration still constructs its original ExplorationConfig; curriculum restores the original outer wrapper for CurriculumConfig.model_validate. Missing/invalid required DTO fields do not acquire invented defaults.
- For an otherwise valid inventory, root-local selection wins; direct level uses its own scope; sole level is inferred and multiple levels without a local target refuse. No first-level or filename-existence heuristic is introduced. The P2 concerns validation occurring before that selection, not its basic ordering.
- Transport parsing and marks are shared, including lowercase YAML enumeration, hidden-path behavior, safe multidocument loader, duplicate keys/declarations, wrapper recognition, scope validation and sidecar conflict diagnostics. Origin remains absolute path:authored wrapper line, not a file path or runtime identity. This reuse is sound within the selected section's domain; it currently overreaches unrelated level scopes.
- Clock lowering is one shared algorithm: existing no-argument full-pack method delegates selected level names, retaining its original no-variables early return; public curriculum explicitly lowers its selected local/direct scope. With a period_of reference and no variables it now reports CLOCK_REFERENCE. Numeric curriculum without variables stays numeric. The code checks exact reference keys, global temporal ambient-tick cyclical target and scalar finite positive integral non-bool authored period; it refuses duplicate numeric authority when an ambient clock exists. Shipped L3 day_phase resolves to authored24 rather than a new default. Located reference/target diagnostics remain available.
- Full discovery remains separate: it does not enable `_section_inventory`, still rejects root training/curriculum and direct-level full discovery, and still calls `_require_families`. resolve_launch retains complete compilation and selection semantics. No confirmed weakening of full-pack admission found in this source inspection.
- The regression includes real full-compile before/after relocation equality, direct public L3 literal24, original DTO comparisons, selected wrapper errors, sidecars/duplicates/source marks and strict full-discovery controls. These are useful causal controls; they do not cover the unrelated-scope preservation counterexample.

## Limits and next binding

No optional P3 raised. Missing individual clock-negative permutations in the new file are not promoted to additional defects: source shares the existing authority checks and root owns execution of existing producer consumers. Original sixteen public-owner nodes should remain unchanged. No separate code-generation/provenance deep-immutability guarantee is inferred for ResolvedConfigSection's shallow mapping proxy.

Repair the scoped P2 within the same five-file owner, then verify frozen final hashes and common candidate, focused GREEN, unchanged public owners, shared producer consumers/guards and required full gate. This pre-freeze report cannot discharge those steps. T06 helper preservation and T32/T36 downstream hosting/provenance remain separate required obligations; no package/dependent or whole-BAC release is claimed.
