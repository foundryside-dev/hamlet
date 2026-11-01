# Review provenance

Historical finding/design review. The source identity in its body is historical; final repair and qualification are recorded in the implementation receipt.

Original artifact `T07-astra-review-r2.md`, SHA256 `1db9c66c4bcd5255f7b8d0553bb655d767c441f38d545d91cbd63b3a51989532`, retained unchanged. This portable rendering normalizes execution paths. Runtime results are coordinator-attributed unless the body explicitly records reviewer execution.

# T07 independent R2 actual-source/spec review

**Disposition: the sibling-scope and identifiable-family repairs are sound; one remaining P2 dependency-scope preservation defect is confirmed statically.** Do not declare T07 preservation complete. No reviewer runtime was executed. Root's 85-case R2 execution was active at dispatch; this report does not infer its outcome. No other confirmed P1/P2 or optional P3 is raised.

## Exact binding and scope

Candidate `c1707d1102887e596d588be2c6d98e61405b9f4f`, HEAD `44e9d494eb94da1450b3e7a1832acea23dbbdb8e`, manifest `wave06/green-r2-candidate.json` supplied by root. Read-only HEAD and index-versus-tree/unstaged comparisons succeeded. Exactly five whole sources / **1,419 lines**, hashes checked before and after:

| Source | Lines | SHA256 |
|---|---:|---|
| src/townlet/universe/declarations.py |791|59ce3cfab0f9b57f0875f3e965e3d956370cabde1cab3a9615e3408a45522709|
| src/townlet/config/resolved_launch.py |160|3feed2f886073d85fc8eeae29d14eba78a0766479b4a1479ae4bb2fd8a809dca|
| src/townlet/config/exploration.py |28|b5292e6d193ab224e76f727b63d9e078fdac0ca706ae0ee7f58e7f723302951d|
| src/townlet/config/curriculum.py |20|a65e3a3b4d02182f96e56d0ad3fd93c72b7e9921b64b5f9c272456250d620227|
| tests/test_townlet/regressions/bac/test_public_loaders.py |420|6cc4bec373c86f93064d36ad5bf0d65d8a5e13566f19907e644de22200bc2d88|

Accepted capsule/brief/consumer audit and earlier findings remain the normative preservation context. No sixth source, runtime/import, test execution, source/index change, write-tree, copy or delegation. R0 and family-note artifacts remain untouched.

## Corrected behavior reassessed

DS now takes an explicit family and scope. `_includes_section_path` excludes unselected level trees before parsing; `_includes_section_family` excludes identifiable nonrequested declarations before their semantic validation and sidecar normalization. LR first checks content-local scope, then selects a sole level or reports ambiguity; direct level selects its own scope. This repairs both previous counterexamples: sibling duplicate/syntax/sidecar corruption no longer blocks the selected target, and invalid identifiable training recording does not block curriculum. Requested training still validates its sidecars. The added controls establish valid target prerequisites, keep the same invalid whole pack rejected, and move corruption into the selected scope for negative controls across all three transports.

Selected-scope syntax and unclassifiable wrappers remain strict; full discover bypasses the section filters, retains required-family/scope enforcement and uses the same safe marked parsing/collision/sidecar machinery. Original public names, argument shape, exports, DTO types and required fields remain intact. Minimal sections do not compile a universe. The original regression's real compiled-product equality, literal shipped L3 day_phase24, relocated/multidocument marks, ambiguity, malformed clock and duplicated_numeric controls remain present. Clock lowering remains shared with full discovery; no adapter algorithm or hidden numeric default was introduced.

## Remaining P2: numeric direct curriculum depends on malformed ancestor YAML

Source: DS `_includes_section_path`, final `return self._section_family == "curriculum"`, combined with unconditional pack-root parsing in `_discover_documents`; LR invokes this inventory before inspecting selected curriculum.day_length.

Counterexample: create the counted valid numeric CURRICULUM at `pack/levels/A/curriculum.yaml`, with day_length24 and all original DTO fields. Verify the direct loader succeeds. Add `pack/broken.yml` containing `{invalid`. Calling `load_curriculum_config(pack/levels/A)` now includes that root file solely because family is curriculum, collects YAML_SYNTAX_ERROR and raises before returning A. The old direct loader read only A/curriculum.yaml. There is no period_of dependency in A and no recognized ambient clock in this witness. Malformed ancestor transport is outside the selected local document domain. Full discover should still reject this pack.

This is distinct from malformed YAML inside A: selected-scope parsing remains mandatory because the file might contain the requested declaration. It also does not justify treating a real period_of request as independent of pack variables, or removing the explicit duplicated_numeric clock rule. Merely changing the path filter to skip all pack-root files for numeric curricula would silently weaken that required rule and is not an acceptable repair.

## Finite dependency boundary and repair guidance

Use an explicit two-stage section dependency policy, within DS/LR and the counted regression:

1. Discover/validate the selected curriculum scope first, keeping selected transport, wrapper, duplicate and DTO validation strict. Its authored day_length determines whether external pack-clock content is required. Local pack-scope input remains selected scope; this finding does not authorize ignoring malformed root YAML for a root-local target.
2. An authored period_of mapping requires strict pack-variable dependency discovery and the existing exact reference/target/period validation. Unresolvable or malformed required dependency input must refuse with located diagnostics; do not retry a filename loader or return numeric defaults.
3. A direct-level numeric curriculum has no required external value lookup. Preserve the established clock-authority check by inspecting safe recognizable external variable declarations and retaining the shared duplicated_numeric refusal when a valid ambient clock is recognized. An unclassifiable malformed ancestor document alone must not be promoted into a new local loader prerequisite. Keep this narrow external-observation boundary distinct from strict selected parsing and strict required-reference discovery; do not catch arbitrary complete-discovery failures and reinterpret them as success.
4. Continue inspecting independent external transports after an irrelevant malformed one, so a valid recognized ambient clock in another file cannot disappear because of ordering. Likewise, if a valid clock document has already been safely recognized in a multidocument stream before a later malformed document, do not erase that positive clock evidence. Any explicitly recognized conflicting clock/variable authority still needs honest handling; do not blanket-ignore variable validation failures. Preserve safe transport containment and never follow an unsafe source to obtain optional evidence.

These are routine preservation choices, not a new feature mode or user scope waiver. The static witness establishes the narrow malformed-ancestor/no-reference conflict; it does not establish permission to ignore every malformed variable declaration or alter complete-pack semantics.

## Causal controls required before closure

- Direct numeric A succeeds before and after adding malformed nonselected root YAML, for conventional/renamed/multidocument target transports; returned original CurriculumConfig remains day_length24.
- Same malformed YAML inside selected A still refuses; strict full discover still refuses the malformed root pack.
- Replace numeric A with period_of while its required dependency is missing/malformed: refuse; valid authored day_phase reference lowers to24.
- Numeric A plus a valid recognizable ambient clock still reports CLOCK_REFERENCE/duplicated numeric authority, both without and with the unrelated malformed root file. Place malformed transport before and after the valid clock transport to prevent ordering-dependent bypass. Preserve valid-clock-before-malformed-document evidence when testing multidocument dependency transport.
- Retain all prior sibling/family isolation, original minimal/DTO/wrapper/selection/marks and shared full-discovery controls.

Root owns causal RED, implementation dispatch, GREEN and final common-candidate binding. The current 85 cases cannot prove this absent edge by passing. Whole-BAC/native checkpoint/lifecycle, downstream serving/provenance and final gates remain open; no release is authorized by this report.
