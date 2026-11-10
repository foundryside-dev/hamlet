# T18e original real composer primitive — Stage0

Disposition: **READY** for explicit root Stage1 freeze release. Read-only preparation completed 2026-11-10 against root-supplied checkpoint 30a802a996fe8bf7cd63e53d211fa8b2cd028f77. No runtime/import/probe/compile/test, formatting/lint, tracked source/test write, git/index operation, branch/worktree/checkout/copy or subagent occurred. This ignored report is the sole write. No runtime success or RED is claimed.

## Fresh bounded source inventory

Metadata was measured before source inspection. Exactly two existing implementation sources entered this fresh context; the third slot is the prospective new test, not an opened helper.

| Source | Actual whole lines | Ceiling | SHA256 |
|---|---:|---:|---|
| src/townlet/vfs/vtc.py | 3508 | 3550 | a27e205ec3531292e56c5b743d5f70b5208a060282278b47a1dc6ee3f7470951 |
| src/townlet/environment/dac_engine.py | 956 | 1000 | c6ad4338f82aa2c905a32d66f666ef7725f02b8f1aef470d76a68e6185bb44e6 |
| tests/test_townlet/regressions/bac/test_intrinsic_scale_composer.py | not created | 350 | none |
| Total | 4464 | 4900 | exactly three reserved source slots |

Read owner AGENTS.md, the exact primitive brief, public composer readiness and real config/fixture API capsules, and the approved phase/clock reconciliation plus independent review. Reconciliation SHA256 matches 215d9486d073e6cdf116af957326ee9fd70f3e4b0b194a8c1b5bc20f253a6eac. No RWC/ENV/runtime/config/registry/test/helper implementation body or introspection was used. Configuration and registry construction below are capsule-attributed facts, not newly inspected fourth/fifth sources.

## Actual composer and faithful setup

Actual VTCRewardProgram.apply currently has no explicit scale, forwards raw unchanged to calculate_rewards through named keywords, expands reward_context separately, and checks every returned component tensor against dones.shape. Its four expected base component names remain compatible with two additional provenance tensors.

Actual DAC calculate_rewards currently accepts intrinsic_raw and **kwargs but no named scale. It clones raw, applies authored base, then the genuine compiled modifier product and existing done mask. It computes real extrinsic and shaping separately. Current intrinsic_raw diagnostic is raw*base before terminal masking; returned intrinsic_weights is modifier product including terminal rows. New scale must not reinterpret either. Real energy efficiency shaping is >= threshold and independent of scale. No primitive retirement term exists.

Use actual imports from townlet.config.drive_as_code: DriveAsCodeConfig, IntrinsicStrategyConfig, ModifierConfig, RangeConfig, ExtrinsicStrategyConfig, EfficiencyBonusConfig and CompositionConfig. Fresh configs author intrinsic strategy rnd/base .25/apply_modifiers double; energy range [0,1] multiplier2; constant_base_with_shaped_bonus/base_reward1 with empty bars/bonuses/modifiers; efficiency_bonus/weight .1/energy/threshold .7; normalize=False/clip=None/log flags True. Use capsule-specified real VariableRegistry(variables=[], num_agents=2, device=cpu, items_per_world=0, item_profiles=None, num_affordances=0), actual DACEngine with energy:0, and actual VTCRewardProgram(). No fake config/backend/registry, helper body, monkeypatched modifier, or provider stand-in is needed.

Use full [2] float32 raw/scale and [2,1] energy meters .8; long step counts, bool dones. Canonical live witness raw2/scale.5/base.25/modifier2 yields intrinsic.5, extrinsic1, shaping.1 and total1.6. Existing source would yield intrinsic1/total2.1 if scale were ignored. The required VTC keyword is currently rejected before this arithmetic, giving a causal initial interface RED rather than an executed numeric RED until production changes.

## Precise Stage1 regression plan (one new file <=350 lines)

Author a small local constructor helper inside the reserved test file using only the public constructors above. Fresh engine/config per case. The helper constructs genuine objects; it does not copy composition or bypass compiled terms. Use actual VTC.apply in arithmetic/provenance/ownership/gradient cases and direct actual DAC.calculate_rewards in contract validation cases.

Planned test identities and controls:

- test_real_vtc_dac_composes_independent_factors: parametrized base .25/.5, scales 0/.5/1, authored modifier1/2, and raw1/2 with independently enumerated expected totals/intrinsics. Include the exact 1.6 witness, zero-scale total1.1, and independently changed base/scale/modifier controls. Verify actual extrinsic/shaping, legacy diagnostic raw*base and modifier-only weights rather than computing only a replacement total.
- test_full_population_scale_and_terminal_diagnostics: heterogeneous scale [.5,0] on live rows proves rowwise application; a separate [False,True] done case proves terminal total/extrinsic/intrinsic/shaping zero while provider raw, runtime scale, legacy raw*base and modifier product retain original terminal diagnostics.
- test_scale_is_required_at_both_composer_entries: direct real VTC and DAC calls omitting scale must raise TypeError; no default or compatibility path.
- test_dac_rejects_malformed_runtime_scale: parametrize Python scalar/list/non-tensor; scalar, short, long and [2,1] tensor shapes; float64/int64/bool; NaN/+Inf/-Inf/negative; CPU-engine versus meta tensor device mismatch (no GPU assumption). Expect scale-named TypeError/ValueError/RuntimeError as applicable. Direct named input avoids hiding missing validation behind the VTC wrapper.
- test_inputs_and_provenance_components_have_owned_storage: snapshot all inputs, verify computation leaves them unchanged, mutate returned provider/raw-scale diagnostics and verify no changes to source inputs, legacy raw diagnostic, effective intrinsic or total; independently mutate caller raw/scale after composition and verify captured provenance and reward tensors stay unchanged. No detach in the production implementation is permitted.
- test_runtime_scaling_preserves_autograd_and_terminal_mask: leaf raw/scale require gradients, live plus terminal rows; total.sum().backward verifies live raw derivative scale*base*modifier and live scale derivative raw*base*modifier, terminal derivatives zero. Input values remain unchanged.

Keep all regression source <=350 whole lines, including helpers and imports. Parametrization should keep the actual implementation comfortably below this ceiling. Exact authored identities/hash/line count will be appended after authorized Stage1. Root will own collection and actual intended RED; Stage2 remains forbidden until root supplies actual causal RED under exact source/process identity.

## Finite Stage2 direction and remaining obligations

After explicit Stage2 authorization, add required keyword-only runtime_intrinsic_scale to DAC and required explicit keyword input to VTC with named forwarding. Validate tensor type, exact [num_agents] shape, float32 dtype, selected device via existing device semantics, finite/nonnegative values before scale use. Clone scale for owned provenance and preserve autograd. Apply runtime scale exactly once on the genuine DAC intrinsic path. Add provider_intrinsic_raw from owned cloned original raw and runtime_intrinsic_scale from owned cloned scale, retain intrinsic_raw raw*base and modifier-only weights, and retain done masks. No config field, alias, default, adapter, unrelated validation or capability reduction.

Original all-provider/both-scope runtime scale0, ENV/RWC real transition delivery, normalization/admission once, successor equality and ICM/predecessor identity, parent clock/custody/service and current native resume, retirement/inactive masking and actual canonical replay remain separate mandatory integration work. Primitive success does not release current consumers or establish repository green, T18e completion, or global BAC gates. Root owns integration/index/runtime/review/publication. No new missing API fact blocks this finite primitive; full integration facts remain outside this source envelope.

# Stage1 — regression authored, awaiting root causal RED

Root explicitly released only the new regression source after fullgate/custody completion, retaining production VTC/DAC freeze. Applied test-driven-development and its writing-good-tests reference. Only new regression source and this ignored report were written. No runtime/import/probe/compile/test execution, git/index operation, source copy, branch/worktree or subagent occurred. Black/Ruff were permitted scoped to the new test; no production edit occurred.

Exact whole-source inventory after Stage1:

| Source | Actual | Ceiling | SHA256 |
|---|---:|---:|---|
| src/townlet/vfs/vtc.py | 3508 | 3550 | a27e205ec3531292e56c5b743d5f70b5208a060282278b47a1dc6ee3f7470951 |
| src/townlet/environment/dac_engine.py | 956 | 1000 | c6ad4338f82aa2c905a32d66f666ef7725f02b8f1aef470d76a68e6185bb44e6 |
| tests/test_townlet/regressions/bac/test_intrinsic_scale_composer.py | 195 | 350 | 0ad34fdfb781a5679762a2eacfa4ff2d86a026967e5039fe514e81a2fce0e745 |
| Total | 4659 | 4900 | three sources |

Seven authored test functions, statically enumerating 29 parametrized cases (collection not run here):

- test_real_vtc_dac_composes_independent_factors: six independent literal arithmetic controls, including required total1.6 and zero scale total1.1; real modifier, legacy and separate provenance assertions.
- test_full_population_scale_and_terminal_diagnostics: two live/terminal variants with heterogeneous scale [.5,0].
- test_done_masks_nonzero_intrinsic_without_erasing_diagnostics: additional terminal nonzero-scale control so scale0 cannot hide missing done masking.
- test_scale_is_required_at_both_composer_entries: two real entrypoint omission cases.
- test_dac_rejects_malformed_runtime_scale: fifteen scalar/list/None, rank/length, dtype, nonfinite/negative and meta-device mismatch controls, requiring scale-attributed exception types.
- test_inputs_and_provenance_components_have_owned_storage: two separately mutated provenance diagnostics; input immutability and caller mutation after composition, plus observer mutation independence of all other outputs.
- test_runtime_scaling_preserves_autograd_and_terminal_mask: live and terminal raw/scale gradients plus original inputs and gradient-carrying provenance.

Genuine constructors are used directly inside the reserved test. No mocks, fallback, helper implementation imports, copied composer or optional scale path. Static mental mutation check covers ignored/doubled scale, scalar scale reduction, base/modifier conflation, extrinsic/shaping contamination, lost masks/provenance, invalid scale acceptance, borrowed storage and detach/in-place autograd regressions.

Static commands from /workspace/hamlet:

```
.venv/bin/black --check tests/test_townlet/regressions/bac/test_intrinsic_scale_composer.py
exit 0: All done! 1 file would be left unchanged.
.venv/bin/ruff check tests/test_townlet/regressions/bac/test_intrinsic_scale_composer.py
exit 0: All checks passed!
```

Status: **READY FOR ROOT COLLECTION/CAUSAL RED**. No runtime/collection/pass/fail claim is made. Stage2 production changes remain blocked on explicit root-attributed actual RED and Stage2 authorization. Original runtime/ENV/phase/service/clock/native/replay and global obligations listed above remain mandatory; no capability reduction or acceptance substitution occurred.

# Stage2 — finite production primitive authored

Root explicitly authorized Stage2 after actual root R11 RED and independent Astra authored-regression/spec approval (zero material gaps). Root-attributed RED receipt: 29 collected, 29 FAILED, no errors/skips/warnings, 9.9647 wall seconds; 12 VTC unexpected-scale-keyword failures and 17 direct DAC required/invalid-scale DID NOT RAISE failures. Root reports custody PASS for 798 sources, 573 configs, 13 artifacts, three process/index identities and 14 registry MAIN1 identities. Real config/registry/compiled terms instantiated, with no prerequisite-fixture failure. Root retains the exact actual command/output and negative-custody record; this author did not execute runtime.

Only production VTC/DAC were edited, and the test remained byte-for-byte frozen. VTC now requires explicit runtime_intrinsic_scale and forwards it by named keyword. DAC requires keyword-only runtime_intrinsic_scale and validates Tensor type, exact [num_agents] shape, float32 dtype, existing selected-device semantics, finite and nonnegative values before composition. Scale type/dtype failures are TypeError, shape/value failures ValueError, and device mismatch RuntimeError, all naming the scale.

Actual DAC clones raw and runtime scale without detaching, then applies runtime scale once in raw * runtime_scale * authored_base before the unchanged real compiled modifier product and terminal mask. components['provider_intrinsic_raw'] owns the raw clone; components['runtime_intrinsic_scale'] owns the scale clone. Existing components['intrinsic_raw'] remains raw*authored_base without runtime scale or terminal masking; intrinsic_weights remains only the authored modifier product. Extrinsic and shaping paths, done masks, total summation, and VTC base-component checks are unchanged. Public API docstrings/example now describe the required argument and diagnostic meanings. No config, modifier alias, default, compatibility path, helper or unrelated validation was added.

Exact post-Stage2 whole-source inventory:

| Source | Actual | Ceiling | SHA256 |
|---|---:|---:|---|
| src/townlet/vfs/vtc.py | 3510 | 3550 | a2d14e8bf9d7363e36f5778182395a4e5110052ca5591efacb1c98d63dad4390 |
| src/townlet/environment/dac_engine.py | 977 | 1000 | b129d7ac5cdbf7e6ed27dd6cd5f9529dc9e7d2e0154b43a4db028d7aef78e317 |
| tests/test_townlet/regressions/bac/test_intrinsic_scale_composer.py | 195 | 350 | 0ad34fdfb781a5679762a2eacfa4ff2d86a026967e5039fe514e81a2fce0e745 |
| Total | 4682 | 4900 | three sources; frozen regression unchanged |

Permitted static commands from /workspace/hamlet:

```
.venv/bin/black --check src/townlet/vfs/vtc.py src/townlet/environment/dac_engine.py tests/test_townlet/regressions/bac/test_intrinsic_scale_composer.py
exit 0: All done! 3 files would be left unchanged.
.venv/bin/ruff check src/townlet/vfs/vtc.py src/townlet/environment/dac_engine.py tests/test_townlet/regressions/bac/test_intrinsic_scale_composer.py
exit 0: All checks passed!
```

Status: **READY FOR ROOT SOURCE CAPTURE/GREEN AND SAME INDEPENDENT REVIEW**. No author runtime/import/probe/compile/test/git/index/branch/worktree/checkout/copy/subagent occurred. No green, completion, repository release or integration claim is made. Existing direct callers now owe explicit scale migration in the unreleased coherent integration; no fallback preserves omitted scale. Genuine runtime/provider/all-family/both-scope, ENV phase/equality/retirement/inactive masking, stats/admission once, parent service/clock/native and canonical replay obligations remain mandatory and open as previously recorded. No capability reduction occurred.

# Root and independent actual GREEN receipt; frozen public capsule

Root reports actual same frozen regression GREEN29 PASS in 8.12831354 wall seconds; independent Astra reports actual GREEN29 PASS in 7.56000137 wall seconds. Both verifiers report custody PASS for 798 sources, 573 configs, 13 artifacts, three pytest processes, 14 registry MAIN1 identities and source/index/import/thread checks. Same 29 cases are overlapping, not 58 distinct cases. Independent actual fixed three-source/spec/quality review is APPROVED with zero owning material findings. This is attributed evidence supplied by root, not author-executed runtime.

Exact root-provided artifacts (result files contain actual commands/log hashes):

- /workspace/bac-review-2026-11-01/qualification/wave34-r12-owned/owned-custody.json
- /workspace/bac-review-2026-11-01/qualification/wave34-r12-owned/owned-result.json
- /workspace/bac-review-2026-11-01/qualification/wave34-r12-independent/independent-custody.json
- /workspace/bac-review-2026-11-01/qualification/wave34-r12-independent/independent-result.json

Wrote only ignored T18e-COMPOSER-SCALE-API.md alongside this ignored report. Capsule records exact public signatures, required float32 full-vector scale geometry, actual validation order/device comparator, once-only raw/scale/base/modifier composition, legacy and added diagnostics, owned mutable tensor/autograd behavior, terminal meanings, unchanged source identities and remaining direct current-consumer gap. No source/test/API probing or new source context; no runtime/import/compile/test/git/index operation. All three source files remain frozen at Stage2 identities above. Root trusted static guards run separately against this frozen candidate.

Finite primitive qualification does not establish current ENV/providers/all-family/both-scope runtime, stats/admission once, phase/equality, parent clock/service/native, retirement/inactive masking, canonical replay or fullgate closure. Those original requirements remain mandatory. No reduction, compatibility mechanism or global closure is claimed.
