# Current owner reference fixture repair

Ready for root qualification. Stationary handoff; no runtime qualification claimed.

## Exact artifact

- Sole code file: `tests/test_townlet/regressions/bac/test_pw_rng_domains.py`.
- Before: 945 lines, SHA256 `e9119e4fd18d42157f7de0a83ccd0bf7eb649d65eca0ca33c722af6ee139d7d4`.
- After: 944 lines (ceiling 1100), SHA256 `55d82ac418642d936813d93dd89256c395fdfe9a6fce91ea32fe78327258462e`.
- Added `OrderedDict` import. `_equal` at line 29 retains exact type, Tensor dtype/shape/device/value, NumPy dtype/value, sequence type/length/value and scalar value checks; Mapping keys now compare in iteration order, with recursive values and optional OrderedDict `_metadata` presence/content comparison.
- `_learning_snapshot` at line 211 replaces the obsolete recursive Mapping-to-dict reconstruction with `copy.deepcopy(value)`. The reference now owns its native mapping kinds, entry order, recursive metadata, sequences and leaves. No actual owner result is normalized.
- No other implementation/test code changed. No production source was read or edited. No generated native payload, compatibility branch or assertion removal.

## Preserved identity inventory

All original decorators, parameter values, IDs and test bodies remain unchanged: 31 CPU identities plus one conditional CUDA identity, counted statically (no collection).

| Original function | Cases |
| --- | ---: |
| `test_private_rng_restores_global_streams` | 3 KINDS |
| `test_world1_rng_independent_of_world0_calls` | 3 KINDS |
| `test_native_global_rng_counterexample_and_private_continuation` | 1 |
| `test_constructor_compute_failure_restoration_and_quarantine` | 6: both after_update values × KINDS |
| `test_owned_snapshot_restore_aliases_and_late_load_failure` | 3 KINDS |
| `test_named_substream_recipe_and_activation_bound_python_facade` | 1 |
| `test_snapshot_callback_failure_restores_and_quarantines` | 1 |
| `test_invalid_rng_snapshot_is_pure_and_nested_components_resume` | 1 |
| `test_thread_ownership_serializes_and_releases_after_error` | 1 |
| `test_used_cuda_domain_restoration_when_hardware_available` | 1 conditional GPU |
| `test_restoration_failure_poisoning_isolated_from_pytest` | 1 |
| `test_object_array_result_does_not_alias_live_adaptive_history` | 2: plain/structured |
| `test_learned_adam_mapping_keys_and_values_are_owned` | 6: native/tuple × KINDS |
| `test_true_a_b_a_nested_activation_preserves_both_streams` | 1 |
| `test_stale_prepared_restore_refuses_after_real_owner_update` | 1 |

`KINDS` remains rnd/icm/adaptive_rnd. The poison-child source string is untouched (now lines 676–813); all exact source/hash/import/profile/index custody assertions and injected restoration/coordinator refusal assertions remain intact. Genuine learning/error, global RNG restoration, other-world independence, quarantined diagnostics/refusal, healthy restoration, optimizer/value ownership and continuation assertions remain intact.

## Access and verification inventory

- Authority read: `OWNER-REFERENCE-FIXTURE-BRIEF.md` in this folder.
- Whole implementation/test source read: owned test only, one of five permitted source slots, 945 original lines / 944 final lines, below the 4000-line named maximum. Targeted rereads were solely inside that same file.
- Public contract read: `../wave31-preparation/OWNED-NATIVE-METADATA-QUALIFIED-API.md`.
- No WS/RND/adaptive/ICM implementation reads; no other fixture/main/new test reads or introspection; no source/repository copies or subagents.
- Allowed scoped checks, with repository configuration: `.venv/bin/black --check tests/test_townlet/regressions/bac/test_pw_rng_domains.py` exited 0, one file unchanged; `.venv/bin/ruff check tests/test_townlet/regressions/bac/test_pw_rng_domains.py` exited 0, all checks passed.
- SHA256, line count and source identity/decorator text inventory only. No imports, compile, pytest, runtime probes, index operations, commit, push, branches, worktrees, installs or deletions performed.

## Root-owned next steps

Run the two genuine `[True-rnd]` / `[True-adaptive_rnd]` failure controls first, then the complete current owner suite and coherent main/covering qualification gates. Obtain independent Astra-medium review. All runtime outcomes, custody refresh, index/integration and publication remain root-owned; this report makes no unrun PASS claim.

## Fixround1: restrict order checking to OrderedDict

The initial artifact above is superseded by this bounded correction. Read the original brief/report and updated independent review SHA256 `9d67423cb9caa14406b192b4df89901a1b38a84aea30ee6d5b7abdbee9789f8f` before editing. Root explicitly supplied the sole-write baton after all runtime sessions closed; candidate `dd09287c79bef1444b34575e511d3d71460b41a4` / base `a7c4cd0b` identifies the failed frozen artifact, not the corrected candidate awaiting root capture.

Causal RED evidence, reported by root and the independent reviewer rather than rerun by this author:

- Root complete old-owner suite: 3 failed, 28 passed, 1 conditional CUDA skip; 12.9714 seconds wall. Root's exact invocation/spec spelling was not supplied to this author.
- Independent review records `run_bac_packet_checks_locked.py` with `wave32-r0-independent-spec.json`, followed by `verify_bac_run.py` with the same spec. Pytest exit 1: 3 failed, 28 passed, 1 skipped, 32 collected; 17.252760887145996 seconds wall (17.2528 rounded). Verifier exit 1 at the result exit-code assertion. Run-log SHA256 `a0b68391abc1d01658d38bcc3683e305f4e496275ee3affc3b3bac0c9893d364`; manifest SHA256 `6d8733d3011e279a439af5f94f857537782c58fc7342fe0695ba56f37717aa37`. These are recorded command identities, not an invented full shell invocation.
- All three `test_private_rng_restores_global_streams` KINDS failed at former line 314 / comparator line 37: equal plain-dict RNG records use different insertion order (`seed` first versus `torch_cpu` first). My universal Mapping order requirement exceeded the public contract, which preserves OrderedDict order and leaves generic Mapping handling unchanged.

Exact fixround1 code delta from SHA256 `55d82ac418642d936813d93dd89256c395fdfe9a6fce91ea32fe78327258462e`: line 37 restores `assert left.keys() == right.keys()` for generic Mapping; line 41 adds `assert list(left) == list(right)` inside the existing `isinstance(left, OrderedDict)` block. Exact type/value/recursive metadata checks and `_learning_snapshot` deepcopy remain intact. No production or test body/decorator/parameter/poison-child changes.

Final owned test: 945 lines (ceiling 1100), SHA256 `7bc3f942badf058967fa1f96bd981b48c38c59c3a28f73e299af81a2bf2c1990`. `_equal` remains line 29; `_learning_snapshot` is line 212; the unchanged poison-child string is now lines 677–814. All 31 CPU plus one conditional GPU identities in the original inventory above remain unchanged, including both original after-update failure controls and all three RNG provider variants.

Scoped `.venv/bin/black --check tests/test_townlet/regressions/bac/test_pw_rng_domains.py` exited 0 (one file unchanged); scoped `.venv/bin/ruff check tests/test_townlet/regressions/bac/test_pw_rng_domains.py` exited 0 (all checks passed). Source access remains the single owned-source slot, with targeted comparator and text-inventory rereads only; no additional implementation source read. No runtime, pytest, imports, compile, probes, index operations, commit, push, branch, worktree, copies, subagents or external messages performed in fixround1.

Ready for stationary root handoff. Runtime remains explicitly deferred until root captures a coherent manifest. Required root coverage: complete original 32-case owner suite, focused former two after-update controls, and focused three RNG variants, followed by root-owned coherent covering gates and independent review. No corrected-runtime PASS claim is made here.
