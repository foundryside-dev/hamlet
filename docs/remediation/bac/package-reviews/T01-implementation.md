# T01 — finite and constructible authored numerics

Status: **DONE** for the scoped implementation and focused verification. Root owns integration, the whole-repository gate, commit, and fresh independent other-model fixed-SHA review. Those gates remain required before overall acceptance; no full runner/training/convergence claim is made here.

## Source identity and ownership

Checkout: `/workspace/hamlet`, branch `project-recovery-bac-2026-11-01`; base HEAD observed before changes: `4aa5363b5de54d9a112977c32c2975f37627197f`.

Imported `townlet.__file__` was asserted under `/workspace/hamlet/src` both during API preflight and by the regression module fixture. All test commands used `/workspace/hamlet/.venv/bin/python`, `PYTHONPATH=/workspace/hamlet/src`, `OMP_NUM_THREADS=1`, `MKL_NUM_THREADS=1`, `CUDA_VISIBLE_DEVICES=`, one pytest process without xdist workers; the numerical module explicitly sets `torch.set_num_threads(1)`.

Exactly three implementation/test files were inspected/authored; final source-read inventory is **1,260 lines**, within the 1,750 projected-line budget:

| Owned file | Final lines | SHA256 bytes |
|---|---:|---|
| `src/townlet/config/brain_config.py` | 565 | `b99ae24a73371fe5466c29e9304f37c4622e474a9ca22ac8597d3a74b3af53be` |
| `src/townlet/config/training_v2_config.py` | 440 | `775c3fe6e025b378f6152aa16291d5c81fd6e31c2d7282426cb54dbca1bcc4e7` |
| NEW `tests/test_townlet/regressions/bac/test_numerics.py` | 255 | `7873e860354a5a52585c5b5e437fd6f4210a8dc1f25d0f8bc382c2fbb822f3b3` |

The tracked two-production-file `git diff -- ... | sha256sum` was initially the empty-diff hash `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`; final tracked production diff SHA256 is `1f09403fa9f07e45f39dc07d913352f4f6b1dffe0aec19254936263a4dbabc3b`. The new test is untracked and therefore independently identified above, not silently omitted from candidate identity.

Additional allowed inputs: task brief, repository `AGENTS.md`, baseline C01/C02, B01 report, authored default-curriculum YAML and runtime public signatures. No other implementation/test source was deliberately opened; no delegation, git mutation, dependency installation, parent-ledger edit, or production campaign occurred. Compiler error tracebacks were generated test evidence, not extra source inspection.

## Repair

- Each feedforward/dueling shared/dueling stream width now has an item-level `ge=0` bound. Zero remains admitted; a negative width receives a compiler diagnostic including its authored element index.
- DTO model configs in both owned configuration files now disallow nonfinite typed floating-point values (`allow_inf_nan=False`), including provided inactive/preset numeric values. Existing finite field ranges remain intact.
- Selected SGD with Nesterov requires positive momentum. Finite inactive SGD preset values do not select SGD or trigger its selected-only cross-field requirement.
- Required training gamma now admits `[0,1]`, matching brain gamma and preserving the zero-discount experiment.
- `apply_training_overrides`, complete level replacement, hashing implementation, family/optimizer vocabularies, preset acceptance and zero-width policy capability were preserved.

## Preflight and red evidence

Before tests, runtime public signatures were inspected without reading factory/compiler implementations. An initial assumption about a generic `NetworkFactory.build` produced `AttributeError`; corrected to the actual public `build_feedforward` / `build_dueling` methods before authoring/running tests. This was API preflight, not red evidence.

The original default-curriculum pack successfully compiled with `UniverseCompiler().compile(..., primary_level='L0_0_minimal', use_cache=False)`. Regression collection succeeded (38 initial cases; `/tmp/bac-T01-collect.log`). Module preflight copies the complete current authored pack, verifies raw brain plus wrapped training/sidecar shapes, compiles that copy, and loads its training DTO before behavioral cases run.

Red command (before any production change):

```bash
PYTHONPATH=/workspace/hamlet/src OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 CUDA_VISIBLE_DEVICES= .venv/bin/python -m pytest --no-cov -p no:cacheprovider tests/test_townlet/regressions/bac/test_numerics.py -q
```

First output: `/tmp/bac-T01-red.log`, **24 failed, 14 passed in 80.13s**. Six failures were an expectation error for already-rejected `-inf`/NaN cases: public compiler exception is `CompilationError`, not `ValueError`. The expectation was corrected before production edits; a complete-level-replacement positive control was also added.

Corrected red, same command: `/tmp/bac-T01-red-corrected.log`, exit 1, **18 failed, 21 passed in 98.69s**. Intended failures were:

- Four negative-width full-pack compiles: `DID NOT RAISE CompilationError`.
- Selected zero-momentum Nesterov full-pack compile: did not refuse.
- Positive infinity in overriding training LR, base brain LR and inactive schedule `eta_min`: did not refuse.
- Positive infinity in Adam epsilon, inactive RMSprop epsilon, weight decay, Huber delta, RND LR, intrinsic annealing threshold, intrinsic initial weight and training-loop gradient norm: DTO/load did not refuse.
- Both gamma-zero constant-policy controls: compiler rejected authored `q_learning.gamma` with `Input should be greater than 0`.

Positive SGD contrasts, four selected optimizer finite updates, finite inactive presets, already-invalid negative-infinity/NaN cases, and complete level replacement were passing controls. The extra inactive negative-width control was added as supplementary coverage after this red and does not have an independent red-run claim.

## Green and integration controls

First green output `/tmp/bac-T01-green.log`: **4 failed, 36 passed, 2 warnings in 55.52s**. All four failures were an over-specific test locator spelling: the canonical compiler renders `hidden_layers[1]`, not `hidden_layers.1`. Corrected assertions to the actual exact bracket index (also tightened inactive-width regex); no production edits were needed for those failures.

Final combined command:

```bash
PYTHONPATH=/workspace/hamlet/src OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 CUDA_VISIBLE_DEVICES= .venv/bin/python -m pytest --no-cov -p no:cacheprovider tests/test_townlet/regressions/bac/test_numerics.py tests/test_townlet/unit/agent/test_brain_config.py tests/test_townlet/unit/agent/test_loss_factory.py tests/test_townlet/unit/agent/test_network_factory.py tests/test_townlet/unit/agent/test_optimizer_factory.py tests/test_townlet/unit/config/test_training_v2_config_dto.py -q
```

Observed exit 0, **104 passed, 2 warnings in 67.16s**; `/tmp/bac-T01-green-focused.log`. This is 40 new numerical cases plus the 64 named B01 baseline cases, not a whole-repository result.

Actual demonstrated contracts:

- Full copied authored packs refuse each negative flat/dueling width before allocation, with the exact invalid element index; inactive dueling negative width is also validated while feedforward remains selected.
- Selected invalid Nesterov refuses during compile; positive-momentum Nesterov and plain zero-momentum SGD compile, build and update finite parameters.
- Full compile rejects `.inf`, `-.inf` and `.nan` in selected base/overriding LR and inactive schedule eta-min. Additional unbounded behavioral floats reject infinity/NaN via authored DTO/load paths.
- Both feedforward and dueling zero-width brains compile with training gamma exactly zero, build actual networks, emit finite observation-independent Q values and retain their existing nonempty bias parameters (2 and 3 scalar parameters respectively).
- The real optimizer factory performs one finite scalar-gradient update for Adam, AdamW, SGD and RMSprop; parameter value changes and remains finite.
- Finite inactive architecture/optimizer/schedule presets survive compilation; the selected optimizer is the actual factory product, including selected Adam-family execution with inactive zero-momentum Nesterov settings retained.
- All five overrides apply with asserted values (gamma, target interval, Double DQN, LR, replay capacity), base brain remains unchanged, and brain hashing still reflects the changed configuration.
- A complete authored level-brain replacement selects dueling and does not inherit the base feedforward block.
- Named existing DTO/loss/network/optimizer factory suites remain green.

Additional final checks:

```bash
.venv/bin/ruff check src/townlet/config/brain_config.py src/townlet/config/training_v2_config.py tests/test_townlet/regressions/bac/test_numerics.py
.venv/bin/black --check src/townlet/config/brain_config.py src/townlet/config/training_v2_config.py tests/test_townlet/regressions/bac/test_numerics.py
git diff --check -- src/townlet/config/brain_config.py src/townlet/config/training_v2_config.py
```

All passed. Early formatting checks found a long annotated line and test-import ordering; these were fixed before the final checks/test run.

## Remaining boundaries

No known T01 implementation concern remains from focused verification. The two warnings are PyTorch's existing `Initializing zero-element tensors is a no-op` notices in the preserved zero-width controls; Q values and updates are asserted finite. No warning suppression was added.

Root must still run the full candidate gate and fresh independent review against the integrated immutable candidate. This report does not qualify full runner, rollout/learning parity, serving, checkpoint, resume, recurrent replay or broader remediation behavior. Root alone stages/commits; proposed commit subject remains `fix(config): validate constructible finite brain parameters`.
