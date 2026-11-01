# T03 implementation receipt — effective run configuration and identity

Status: **SOURCE FROZEN; worker verification passed; fresh coordinator review/full gate pending.** No dependent release, commit, merge or publication is claimed.

## Candidate and bounded inventory

- `candidate_sha`: `049e305df42392373a52c9eb76552abbd74a5b2b` plus the four owned implementation/test changes below. This HEAD is the coordinator's documentation/JSON-only checkpoint; the implementation source base was `ac8f0f9c3c38cd77f533accc5c9259fe4abfc252`.
- Coordinator-selected source snapshot: tree `4175e78397be42fcdf0f126c5f5b85cd6ee1fe0d`, `/tmp/bac-verify-T03-4175e78397`. Worker executions imported `/workspace/hamlet/src/townlet/__init__.py`; their five source hashes exactly match that snapshot's published candidate JSON. The worker did not execute against the detached snapshot.
- Own extracted brief: `.superpowers/sdd/2026-11-01-bac-remediation-upgrades/tasks/task-T03.md`, current SHA256 `f0fef7540fec3a8e09ce2d7afd0b5091f124730fab10d7b2eef8af3e0c03f391`. The coordinator's routine EF400 recount changed budget/status metadata only; P1/RP/cache requirements stayed unchanged.
- Frozen P1 plan reference: SHA256 `2dde2d80d3d14c510878c26af1f99c42217be12d3cb3a554647bc68646feedc1`.
- `scope`: P1 effective configuration, selected-provider materialization, distinct identities, compiled persistence and explicit known-1.40 loader preservation. Historical checkpoint canonicalization/archive and provider/runtime factories remain later packages.

Exactly these five implementation/test files were inspected. Counts charge complete current files, including blanks/comments, rather than changed lines:

| Access | File | Actual lines | SHA256 |
| --- | --- | ---: | --- |
| create | `src/townlet/config/effective_run.py` | 332 | `30c888a79e739f45a6ea6333afc7d10498e212a3eeca628e89f218d1daa64af8` |
| modify | `src/townlet/universe/compiler.py` | 976 | `521a72dd6d0a155c89a216fa038828cc8054520714a58cc0e0420c2da9d09e92` |
| modify | `src/townlet/universe/compiled.py` | 1615 | `494f9676c236349f12c875c82dde821a85a3bf5077cae15654c78e8ac1630710` |
| read only | `src/townlet/config/exploration_policy.py` | 653 | `496b988555bc0f23f1a6e335386102acbc1450df1d064d87cfd616a0d953299a` |
| create test | `tests/test_townlet/regressions/bac/test_effective_run.py` | 330 | `4529f9074600233081014073a32aa737da10e31e5a148fe91745faf38595eda8` |

**Total: five files / 3906 lines**, below the amended projected 4600 and hard 5000 limits. No sixth project implementation/test/helper source was opened. No BC, OP, declarations, training DTO, network factory or owning-test implementation source was opened. Public DTO schema/signature introspection and runtime imports were used instead. The coordinator supplied the public NetworkFactory API and OP relational-check facts. AGENTS, own brief, T02/T18a receipts, B07/B08 reports, YAML and historical native data/manifests were reference material. Existing owner tests were executed without opening their source.

No unowned source, original fixture, whitelist, ratchet, root progress/ledger or approved-plan bytes were edited. No worker Git stage/commit/push, tracker claim or delegation occurred; the coordinator owns the staged candidate.

## Public API and ownership

`config/effective_run.py` supplies frozen `FieldRole(status, origin, reason)`, frozen `EffectiveRunConfig` and:

```python
resolve_effective_run(base, training, *, primary_level, origins, drive_intrinsic)
```

The result contains `base_brain`, `effective_brain`, original `training`, original partial `authored_options`, fully materialized `options`, immutable `exploration`, `primary_level`, immutable `field_roles`, `authored_brain_hash`, `authored_identity`, `execution_hash`, `training_hash`, `derivations` and `origins`. Public model access returns owned deep copies; mapping/role metadata is immutable. `to_dict()` exports fresh portable data. `from_dict()` independently resolves original authoring and validates the complete transported view. `validate_payload()` compares a canonical complete-tree digest after that resolution, including roles/provenance and every captured preset.

`CompiledUniverse` adds `effective_run`, `authored_brain_hash`, `authored_identity` and `execution_hash`. `brain` remains the selected **unoverridden** complete level brain, or inherited pack brain. The compiler records logical inherited/replacement/training/drive origins; clone and persistence retain those origins.

## Resolution and finite field roles

RP is called **first**, with original authored partial `BaCOptions`, or `BaCOptions()` when omitted. Materialized defaults are never fed back as authored RP overrides. After RP selects its final provider/batch/service context, EF consumes OP's empty-authoring versioned omission table, overlays original authored values, applies dependent ICM derivations and RP's selected provider/service values, then validates the resulting `BaCOptions` normally. There is no `model_construct`, swallowed validation error or validation bypass. RP owns selected batch/capacity checks; inactive typed provider presets remain retained even when their capacities would be unsuitable for an unselected provider.

This establishes selected drive batch8/capacity8 with original Q-training batch32, refuses selected8/capacity7, and preserves typed ICM batch4 precedence over raw8, selected raw feature7/derived hidden14, original authoring and nested unknown raw presets. RP role triples are copied structurally into EF's own immutable role type. Exact observation phases and observation/transition input kind survive persistence.

The execution projection is selected by finite executable cases; it is not a hash of the complete DTO:

| Surface | Role rule |
| --- | --- |
| Architecture | Selected family fields active; every other family block remains an inactive preset. Mean ignores retained attention head count. Selected omitted token encoder derives linear semantics; explicit equivalent linear authoring has the same execution projection. |
| Optimizer/schedule/loss | Selected optimizer parameters and selected schedule arguments active; other optimizer/schedule arguments inactive. Huber delta participates only for Huber. |
| Replay | Capacity is the training-derived effective override. PER parameters participate only with prioritized replay; recurrent option roles also respect recurrent/prioritized selection. |
| Five overrides | Base gamma, target interval, Double DQN, learning rate and capacity are inactive overridden authoring. Their effective values are separately derived from training and enter execution identity. |
| Training | Learner/population/seed/action/affordance/loop controls enter the selected projection; sequence length is inactive for nonrecurrent families. Static adversarial presets are inactive; adaptation rate participates with selected rate-limited adversarial difficulty. Version/run metadata/recording remain retained and explicitly unqualified in this view. |
| Options | Replay/curriculum selections use their relevant mode predicates. Serving/evaluation/checkpoint selections retain their resolved semantic identity. Provider/source/service selection and derivations come from RP rather than transported role claims. |
| Exploration | RP's strategy-defined active identity owns selection. None retains epsilon and excludes intrinsic presets. RND/adaptive/count/ICM use their selected schemas. Nonselected and unknown raw keys remain inactive, including nested lists/maps. |

The base is independently validated/copied before `apply_training_overrides`, preserving full level replacement and all five override values. Existing network families, zero widths, aggregators, sampling/service choices and public loaders are retained.

## Identity semantics

- `authored_brain_hash` hashes the complete normalized selected base through the existing `compute_brain_hash` API, including retained brain presets.
- `authored_identity` separately tags/hashes complete captured brain and RP-authored training/drive/options, including inactive and unqualified presets.
- `execution_hash` tags/hashes the finite selected field projection and RP's schema-owned policy identity. Active selected changes move it; inactive preset edits can preserve it and seeded selected-network weights.
- EF `training_hash` uses the existing current compiler `training.model_dump_json()` recipe. Source historical per-level `training_hash` is not rewritten when a current EF is reconstructed.
- Existing `brain_hash`, `pack_brain_hash` and `compute_brain_hash` meanings/code remain unchanged. Existing hashes still include their historical preset semantics and the five overrides.
- Existing metadata config/cache fingerprints remain source/transport/runtime freshness identities. A changed YAML preset can change that fingerprint and authored identity while preserving execution identity.

## Compiled cache policy

New schema **1.41** requires the old complete field set plus `effective_run`. Loading independently re-resolves authoring, checks RP numeric/schema/phase invariants, verifies every transported EF field/role/identity, and verifies the view against outer selected brain/training/drive. Missing views, changed execution hashes, role relabeling, changed phases/provider schemas and inconsistent outer authoring refuse without changing an existing object or original source artifact.

Exact known **1.40** has an explicit old-field-set dispatch. Its complete base/training/drive facts derive an honest **current** effective view with `capture_origin` saying it was derived from known schema1.40 and was not historically captured. Stored brain/pack/per-level source hashes stay unchanged. Subsequent serialization emits current1.41 with that derivation provenance. Unknown versions retain explicit refusal; there is no generic old-version fallback or fabricated historical capture claim.

Real protected uniform/per/sequence-trained manifest cache data (15 original msgpacks), plus the original pre-optimizer sequence cache, load successfully without byte changes. Original sequence L1 digest remains `5a654e72b714e771f7f9326b93647d71d804e48ff5fffd48d0f76d6d360c415a`.

An additional discovered edge was repaired causally: RP already accepts unknown inactive raw NaN presets, while ordinary Python dictionary equality rejects independently unpacked NaN objects. Canonical complete-tree comparison preserves those accepted presets through real msgpack/clone/dict roundtrips. It distinguishes numeric NaN from string `"NaN"` and null, keeps active epsilon NaN refusal, and leaves execution identity unchanged for the inactive edit. It does not activate unknown fields or weaken RP's active numeric validation.

## Red/green and final verification

All pytest runs used installed `.venv/bin/python`, CPU, `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 CUDA_VISIBLE_DEVICES= PYTHONPATH=/workspace/hamlet/src`, with no uv sync/build. Final execution identity records assert the local import and Torch thread count1.

- Initial exact focused command, before implementation: **9 intended missing-`effective_run` failures**, with one initially vacuous historical loop subsequently corrected. Its initial audit captured the before state only; no separate post-run identity file exists for that first exploratory run. This limitation is not relabeled as a complete before/after audit.
- Corrected original historical native cache control then independently ran **red**, failing specifically at the missing effective view after real digest/schema/load prerequisites. `/tmp/bac-T03/red-historical-identity.json` records actual before/after identity.
- First implementation run caught an incorrect DriveAsCode wrapper access; it was repaired within the owned compiled file. It is not counted as causal red evidence.
- Exact standalone focused command then passed **10/10 in 102.90s**, including genuine historical cache controls (`green-r2.log`). The later expanded pre-NaN snapshots passed 168 and 169 combined tests; these are earlier revisions, not final-source qualification.
- Additional permanent NaN control ran **red** at real msgpack deserialization, then **green** after canonical comparison (`nan-red.log`, `nan-green.log` and their actual before/after identity JSONs).
- **Final source: 170 passed in 228.81s**, comprising all **17** owned regressions and **153** B07/B08 owner controls. Collection independently found170. `/tmp/bac-T03/green-owner-r5.log` and `green-owner-r5-identity.json` are authoritative final worker evidence.
- Final scoped Ruff/Black/mypy and whole defaults guard all exited0. Defaults remain **614 whitelisted / ceiling614**; initial new defaults were repaired with explicit branches, without suppression or whitelist/ratchet changes. Evidence: `/tmp/bac-T03/static-r5.log`, `static-r5-identity.json`.
- Final static and test before/after snapshots are all identical: HEAD049e, local import, Torch1 and all five hashes in the inventory table. They exactly match coordinator candidate tree4175e78397's source manifest. Final `git diff --check HEAD -- <four owned paths>` also exited0.
- Preflight verified three canonical artifact digests and all114 manifest config-file digests. Manifest SHA256: `d1582c8a3b84eff4dca06c7fdf17e12c7b1adfcbf65f8c7b1c1979f1f87bbfe1`. Existing fixture bytes were never edited.

`focused_commands`:

```text
.venv/bin/python -m pytest --no-cov -p no:cacheprovider tests/test_townlet/regressions/bac/test_effective_run.py -q
.venv/bin/python -m pytest --no-cov -p no:cacheprovider tests/test_townlet/regressions/bac/test_effective_run.py::test_inactive_raw_nan_presets_survive_real_msgpack -q
```

Final `owner_suite_commands` ran the focused file plus these existing files in one invocation, with the same pytest flags and `-q` (the exact argv is in `green-owner-r5-identity.json`):

```text
tests/test_townlet/unit/universe/test_brain_level_override.py
tests/test_townlet/unit/universe/test_compiler_declaration_origins.py
tests/test_townlet/unit/universe/test_declaration_input_shapes.py
tests/test_townlet/unit/universe/test_declaration_store.py
tests/test_townlet/unit/training/test_token_checkpoint_gates.py
tests/test_townlet/unit/training/test_brain_lineage_legibility.py
tests/test_townlet/unit/universe/test_compiled_universe_serialization.py
tests/test_townlet/unit/universe/test_compiled_token_coherence.py
tests/test_townlet/integration/test_token_transfer_contract.py
```

`static_commands`: `.venv/bin/ruff check` and `.venv/bin/black --check` on the four owned source/test paths; `.venv/bin/mypy` on the three owned production modules; `.venv/bin/python scripts/no_defaults_lint.py src/townlet/ --whitelist .defaults-whitelist.txt --ratchet .defaults-ratchet` on the complete production tree.

## Remaining coordinator gates and limits

- `review_record`: pending fresh other-model Astra HIGH review of the fixed five-file snapshot. Worker verification is not independent approval.
- `full_suite_status`: **not run by this worker; mandatory before dependent release**.
- `full_suite_reason`: existing compiled/cache schema and effective identity/precedence contracts changed; this triggers the early full gate.
- `unrun_checks`: coordinator's whole-repository Ruff, Black, mypy, compiler CLI and generated-expression-doc guards; detached-snapshot collection/import/fixture checks; mandatory full four-worker pytest; independent review. The complete-tree defaults guard was run here but coordinator still owns its standing-guard qualification.
- `next_full_gate`: coordinator's current fixed-candidate early full gate before T03-dependent consumers/T03a release; final G1–G7, coverage, slow/hardware and remote-CI requirements remain unchanged.
- Runtime consumers have not been switched to EF here; provider construction, historical identity canonicalization/archive and later consumer learning/serving/continuation qualification remain explicitly owed to their own tasks. No convergence, full resume, coverage percentage or repository-wide green claim is made.

Suggested coordinator commit subject after required review/gates: `feat(config): expose effective run identity and provenance`.
