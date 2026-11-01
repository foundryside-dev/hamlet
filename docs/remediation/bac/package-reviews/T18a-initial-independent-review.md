# T18a independent spec and quality review

Verdict: **CHANGES REQUIRED — two P2 blockers.** The additions substantially implement the five-choice resolver, immutable policy/context/receipt interfaces, and provenance, but selected precedence is not consistently applied before capacity validation and portable reconstruction admits internally contradictory policies. Passing authored tests does not close these findings.

Reviewed immutable snapshot `/tmp/bac-verify-T18a-212b3d6d1a`; supplied base commit `050a1a70e979aa03724219b81e848093820f044f`; supplied staged tree `212b3d6d1aa71474c0bfadb3521bbbce3d3b7d5d`. This review identifies content by independently verified source hashes, not mutable checkout HEAD. The candidate patch's two complete added-file bodies exactly matched the snapshot; patch SHA256 `6b33bd4e8b28a95e1dd640bfdd3c65fbb88518179c690ce6a9982514cc77f1dc`. No git operations were performed.

## Blocking findings

### P2 — Validate capacity against the selected batch after provider precedence

Location: `src/townlet/config/exploration_policy.py:290` (early `resolve_bac_options` call), with selected resolution later at lines 390–504.

The first call resolves/validates options against training's batch before raw drive provider settings participate. With the actual canonical training DTO's batch=32, a valid `rnd` policy with `provider_parameter_source='drive'`, raw `rnd_config.predictor_batch_size=8`, and typed `rnd.max_pending_rows=8` raises `bac_options.rnd.max_pending_rows must accommodate training.replay_buffer.batch_size`. Its final selected batch would be 8, so its queue fits exactly. Independently, `icm_config.training_batch_size=8` plus typed `providers.icm.max_pending_transitions=8` raises `bac_options.providers.icm.max_pending_transitions must accommodate training_batch_size`, again because intermediate default 32 is checked before selected raw 8. Both are validated actual `IntrinsicStrategyConfig` and authored `BaCOptions` inputs, not model_construct bypasses.

This rejects valid explicit drive/typed combinations promised by P5a and makes training's overridden preset constrain the selected provider. Preserve typed > selected raw > derivation precedence and evaluate inter-field capacity constraints only after the relevant selected values are known. Keep the standalone options contract deliberately scoped; avoid weakening validation globally just to bypass this interaction. Add both exact-capacity cases, plus truly undersized selected-capacity negative controls.

### P2 — Validate provider schema, duplicate values, and activity independently of serialized roles

Location: `src/townlet/config/exploration_policy.py:126–145`, `:168–172`.

`from_dict` trusts serialized `field_roles` for scalar validation and accepts any provider-map subset. From a valid `rnd` policy with scalar `rnd_feature_dim=128`, changing only `provider_parameters.feature_dim` to 7 is accepted with both conflicting values intact. Replacing the entire provider map with `{}` is also accepted. Changing the scalar's transported role to `inactive_preset` permits `rnd_feature_dim=NaN` for the selected RND strategy. These were independently executed public `to_dict`/`from_dict` operations. Direct dataclass construction uses the same checks.

The portable policy is intended to be the single constructor/continuation contract. It must not admit incompatible architectures depending on whether a consumer reads the named scalar or provider map, missing required parameters, or nonfinite selected scalars disguised as presets. Validate the exact selected provider parameter schema and scalar/map/service consistency, and determine mandatory active fields from strategy/schema rather than trusting transported annotations. Reject contradictions with located diagnostics; preserve valid inactive authoring separately. Include direct-constructor and portable negative controls and unchanged round-trip controls for all five strategies.

## Independently executed evidence

Installed `/workspace/hamlet/.venv/bin/python`; working directory the fixed snapshot; `PYTHONPATH=/tmp/bac-verify-T18a-212b3d6d1a/src`, `CUDA_VISIBLE_DEVICES=`, `OMP_NUM_THREADS=1`, `MKL_NUM_THREADS=1`, and `torch.set_num_threads(1)`. Both test processes assert `townlet.__file__` resolves to the snapshot and assert all five SHA256 values before and after execution. Inline probes only: no sixth helper/probe source was created or read.

- Focused command via `pytest.main(['--no-cov', '-p', 'no:cacheprovider', 'tests/test_townlet/regressions/bac/test_exploration_policy.py', '-q'])`: **32 passed in 9.61s**, with before/after import and five-hash assertions passing.
- Owner command via the same harness: `pytest.main(['--no-cov', '-p', 'no:cacheprovider', 'tests/test_townlet/unit/config/test_drive_as_code_dto.py', 'tests/test_townlet/unit/config/test_training_v2_config_dto.py', 'tests/test_townlet/regressions/bac/test_options.py', '-q'])`: **62 passed in 69.13s**, with before/after import and five-hash assertions passing. Owner test sources were not opened.
- Independent negative probes produced the two valid-input capacity rejections and the three invalid-transport acceptances above.
- Independent nested unknown raw-key contrast preserved execution identity while changing authored identity; valid portable round-trip retained the entire tree.
- Independent mutation probes for all four context tensor inputs and all four returned accessors confirmed snapshot ownership. Original predecessor/successor/actions/eligibility tensors and accessor clones could be mutated without changing the context.
- The focused suite executes the real compiler/CompiledUniverse transport contrast using a temporary copy of the canonical YAML pack. No compiler/helper source was opened. Its passing result is bounded compatibility evidence, not proof of every historically accepted pack.

## Spec coverage and handoff

The source implements all five provider parameter sets now, training-owned epsilon/initial scale, drive selector/base weight/modifiers, typed count/ICM overrides, opt-in raw RND/adaptive ownership, equal-rank located conflicts, recursive immutable storage, inactive unknown-key retention and separate authored/execution identities. Active finite numeric checks and located raw conflicts are exercised, subject to the reconstruction finding above. The exact `predictor_observation_phase='eligible_predecessor'` literal remains; additive `predictor_input_kind='transition'` for ICM preserves complete-transition admission semantics. Context snapshots carry complete predecessor/action/successor/eligibility/tick data. Actual provider construction, reward invocation, service, continuation and strict per-world behavior remain later deliveries; this review does not claim them implemented or approve dropping any choice.

**T03 mandatory handoff:** pass authored partial `BaCOptions` (or `BaCOptions()` for omission), never materialized `resolve_bac_options(...).options`, to `resolve_exploration_policy`. The materialized type cannot distinguish derived provider values from explicit typed overrides, and using it silently changes the raw-drive precedence. This requirement is already explicit in the implementation receipt and must appear in the consumer receipt/integration tests.

The newer user preservation rule supersedes root AGENTS.md's older blanket break/delete guidance. No capability removal, provider degradation, or consolidation is approved. The two findings require repair and fresh review before dependent release. A later joint-wave refresh must reverify the unchanged owned bytes against its complete candidate; these old hashes do not approve changed source.

## Actual source inventory

Exactly five implementation/test sources, 2187 whole lines, including new test. No sixth implementation/test/helper/conftest/compiler source was opened. Task brief was read first; AGENTS.md, implementation receipt, candidate metadata, review package and candidate patch are reference material.

| Source | Lines | SHA256 |
|---|---:|---|
| src/townlet/config/exploration_policy.py | 567 | 0bd35dd1c6a669b3904c1d39358e28855cb74bd91a183c4e71d98b01a9d3090e |
| tests/test_townlet/regressions/bac/test_exploration_policy.py | 329 | 39d93ae67f982b491b61306edd49ab233b946b06b2039dd3d082106dbf52c29d |
| src/townlet/config/drive_as_code.py | 605 | 870e44fbc55f4bc7a221e7272cebea893ff95bfe37f23c6e4e01c4e80595150c |
| src/townlet/config/training_v2_config.py | 443 | d103aafbfe4e7fd4e957b71fd0651c6b6d8bebb98de4581d9d53e2356907ca68 |
| src/townlet/config/bac_options.py | 243 | 1de08a7cc36c49772254d8b9dc2d8adf3cac76533eecba5c36568745bc48c8f1 |

## Limits and release status

Scope: bounded independent spec and code-quality review of unused additive T18a module. No source edits, staging/commits, subagents, runtime wiring, repository-wide static guards/full pytest/coverage/slow/hardware/remote CI, or root release gates performed. Worker static/94-test evidence is attributed to its receipt; this reviewer reports independently run evidence above. Next mandatory full gate remains coordinator-owned G1 or an earlier applicable trigger. Full-suite status: unrun by reviewer by explicit scope. No repository-green or release approval.
