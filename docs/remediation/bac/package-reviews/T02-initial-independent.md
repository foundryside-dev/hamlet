# T02 fresh independent review

Verdict: **APPROVE the bounded T02 package, with one nonblocking P3 test gap.** No P1/P2 defect or unauthorized capability reduction established. This is not whole-BAC readiness or permission to skip the mandatory full suite.

## Fixed candidate and scope

- Base HEAD: `5c91dfb9d09b8ba2d422c6fef5c3e468eadfebaf`.
- Actual staged candidate tree: `25cdec4e82cfdeb64a715320313316c90e700747`.
- Reviewed/executed snapshot: `/tmp/bac-verify-T02-25cdec4e82`.
- Candidate manifest: `task-T02-candidate.json` in this directory. Verified its exact base/tree and all four whole-file SHA256 values before and after verification. Approved plan SHA256 `2dde2d80d3d14c510878c26af1f99c42217be12d3cb3a554647bc68646feedc1` and addendum SHA256 `2b73403fcd9d139e46009c2f49add6dbe6f99310ce37018ffcf839230845d370` also remain exact.
- Read only the four permitted candidate implementation/test files: `brain_config.py` 568, `training_v2_config.py` 443, `bac_options.py` 243, `test_options.py` 219: **1473 lines**. One own external probe, `/tmp/bac-t02-independent-probe.py`, adds 104 lines: **five source/test files / 1577 lines total**. No other implementation/test/helper source read, delegation, network, dependency install, or candidate/index/HEAD edit.
- References: extracted `tasks/task-T02.md`, corrected `tasks/task-T02-report.md`, `task-T02-review-package.md`, options documentation and YAML reference data. Did not open the whole approved plan. Reviewed both spec compliance and implementation quality from actual allowed source.

## Spec verdict

**Pass within T02's stated boundary.** The option literals match the extracted P1 contract. Nested option models inherit strict, frozen, finite, extra-forbidden validation; null remains an omission marker. Required old DTO fields and the previous brain/training paths are preserved. Encoder authoring uses the exact P4 portable `TokenEncoderOptions(mode, hidden_width)` interface, re-exported by brain configuration, independently of aggregation. Linear and explicit positive-width interaction MLP authoring both survive actual compiled brain transport.

The single versioned resolver fills every one of its 30 leaves, records a unique immutable provenance entry per leaf, derives dependent ICM widths/bounds, preserves explicit overrides, and refuses undersized predictor queues. Resolved receipt JSON round-trips. The four complete positive fixture packs and option examples remain accepted. Existing presets, zero-width flat policies, optimizer/loss/family choices, mean/attention, and the five override implementation remain present; existing owner tests confirm their relevant behavior.

`options.md` explains units, central resolution, active/inactive/unqualified roles, K02/K04 preservation, authored identity effects, and the absence of runtime qualification. T03/T18a/T17/T27 deferrals are explicit and consistent with the extracted task boundaries; T02 does not claim to implement those runtime consumers.

## Code-quality verdict

**Pass, with the P3 regression-test improvement below.** The implementation is small and additive. Validation and semantic resolution are separated, the derivation table is centralized, nested values/provenance contain no mutable dictionaries, and existing loader/override behavior is not refactored opportunistically. The recursive merge operates on validated option dumps and a fixed private table. No unnecessary aliases preserve the superseded unpublished encoder spelling.

### P3 — Assert encoder preservation at the actual compiled transport boundary

Location: `tests/test_townlet/regressions/bac/test_options.py:90` (the compiled round-trip assertions at lines 90–94).

Trigger/evidence: the family test checks `compiled.brain.architecture.type`, then checks only per-level training `bac_options` after `to_dict/from_dict` and msgpack. Its renamed-pack check likewise compares only the training receipt. The separate encoder test covers BrainConfig JSON, so a later compiler/cache change that drops `brain.architecture.{token_set,recurrent}.token_encoder` could pass these assertions while violating T02's promised actual transport contract.

Impact: a regression-detection gap, **not a demonstrated current transport defect**. My independent public-boundary probe compiled copied token-set and recurrent packs and verified exact explicit encoder values after dict and msgpack restoration; both currently pass.

Suggested fix: in the existing family round-trip test, compare the selected brain encoder declaration (or complete brain DTO) before/after each actual compiled dict/cache round-trip and declaration rename. No extra production source or runtime wiring is needed. Nonblocking for this candidate because independent current-boundary proof passes.

## Independent execution

All Python execution used `/workspace/hamlet/.venv/bin/python`, snapshot cwd, `PYTHONPATH=/tmp/bac-verify-T02-25cdec4e82/src`, `CUDA_VISIBLE_DEVICES=`, `OMP_NUM_THREADS=1`, `MKL_NUM_THREADS=1`; torch threads were set to one by the focused session fixture and own probe. One test/probe process at a time; no xdist workers. Snapshot import identity asserted.

Preflight: all 134 new YAML files loaded as mappings; focused collection succeeded with **35 cases**.

Executed combined command:

```text
python -m pytest --no-cov -p no:cacheprovider tests/test_townlet/regressions/bac/test_options.py tests/test_townlet/regressions/bac/test_numerics.py tests/test_townlet/unit/agent/test_brain_config.py tests/test_townlet/unit/agent/test_loss_factory.py tests/test_townlet/unit/agent/test_network_factory.py tests/test_townlet/unit/agent/test_optimizer_factory.py tests/test_townlet/unit/config/test_training_v2_config_dto.py -q
```

Result: **139 passed in 262.40s**, comprising 35 focused T02 and 104 owner/T01 cases. Two expected PyTorch zero-element warnings from preserved feedforward/dueling constant-policy witnesses. Extra owner tests were executed without opening their source.

Own adversarial probe: `python /tmp/bac-t02-independent-probe.py` under the same environment. **All checks passed**:

- Every resolved leaf has exactly one provenance entry; no resolved leaf remains null.
- Explicit null at every leaf produces exactly the omission receipt.
- Explicit values at every leaf preserve values and mark exactly that leaf authored.
- Unknown sibling fields reject; all numeric leaves reject boolean/string coercion and NaN/positive or negative infinity.
- Training DTO JSON retains every individual option declaration; resolved receipts JSON round-trip.
- Resolved envelope, provenance entries and nested options reject ordinary mutation.
- Interaction encoder width rejects bool/string/float/nonpositive/nonfinite inputs.
- Actual compile/dict/msgpack brain encoder preservation passes for `{mode: linear}` and `{mode: interaction_mlp, hidden_width: 32}`. Both fixture packs were copied before compiler execution.

## Declined judgments and limits

- Did not classify runtime options being unwired as a T02 defect: source/doc expressly declare schema/transport only, with named later consumer tasks. Likewise, final field-role identities and raw-drive precedence belong to T03/T18a; retaining authored options and provenance is the appropriate current boundary.
- Did not infer old-cache refusal from new nullable serialized fields. Existing hash APIs are unchanged, identity adaptation is explicitly T03a, and the coordinator independently established old native cache loading. T02 still triggers the full-suite requirement because current DTO identity inputs change.
- Did not call accepted null width for linear an unauthorized relaxation: the stated authoring convention treats null as omission. Positive interaction width remains mandatory.
- Did not invent upper bounds for positive integer options or enforce a nonzero sum of ICM loss weights: the approved interface specifies positivity/nonnegativity and no such additional operational constraint. Extreme allocation or downstream numeric behavior is not runtime-qualified here.
- Static guards/full suite/coverage/GPU/learning behavior were not independently rerun by this reviewer. Root owns mandatory full-suite and standing-guard release evidence for this exact candidate. No overall BAC completion claim follows from package approval.

No blocking plan issue discovered in the extracted T02 interfaces. The explicit future-boundary qualifications and mandatory full gate remain necessary.
