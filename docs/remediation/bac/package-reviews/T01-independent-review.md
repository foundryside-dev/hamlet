# T01 independent candidate review

Status: **APPROVED for T01 package**. Spec verdict: PASS. Code-quality verdict: PASS. No actionable P1/P2/P3 findings; no repair requested. This is not whole-BAC merge readiness.

## Identity and review boundary

Reviewed staged candidate tree `aa24cd3fbdd49a252c8437b18cc1c0ad2402b7a6` in `/tmp/bac-verify-T01-1139ddfa42`, based on HEAD `4aa5363b5de54d9a112977c32c2975f37627197f`. HEAD itself does not contain the candidate. Frozen plan SHA256 `2dde2d80d3d14c510878c26af1f99c42217be12d3cb3a554647bc68646feedc1` matched the snapshot plan bytes. Initial source hashes matched task-T01-candidate.json exactly.

Read scope: brain_config.py (565 lines), training_v2_config.py (440), test_numerics.py (255): 3 files / 1,260 lines. One independent scratch probe adds 48 lines, for 4 implementation/test/probe files / 1,308 lines. No additional implementation or test source was opened. Executed existing tests without reading their source. Read the brief, implementer report, review package, AGENTS.md, baseline C01/C02 and B01 report. Later baseline text appeared in a document excerpt but did not expand implementation inspection.

## Static findings and strengths

No actionable P1/P2/P3 finding identified in the inspected production change.

- `brain_config.py:32,74,102`: per-item bounds provide element-level locations and retain zero; no family vocabulary or finite preset is deleted.
- `brain_config.py:284`: selected SGD checks Nesterov after required fields are established. The equality-to-zero test is sufficient because the typed momentum already has a nonnegative finite bound. Inactive SGD settings do not select behavior or trigger this cross-field constraint.
- Both files set finite-only validation on each nested DTO, avoiding the mistake of applying it only to the parent model (whose configuration does not automatically govern nested model fields).
- `training_v2_config.py:95` aligns discount gamma with the existing brain interval, including both endpoints. Schedule gamma retains its distinct, unchanged decay-factor contract.
- The five-field override helper and content-hash algorithm are unchanged. The regression suite exercises base nonmutation, changed effective hash, complete level replacement, retained presets, actual factory selection and finite optimizer updates.
- The new tests use copied complete authored packs and canonical public APIs, verify snapshot import provenance, and contrast valid and invalid inputs. Zero-width checks assert observation independence, finite Q output and retained bias parameter counts for both flat families.

## Verification

Independent focused run: **104 passed, 2 warnings in 143.23s**, exit 0. Log: `/tmp/bac-T01-review-tests.log`. Executed from the snapshot with `/workspace/hamlet/.venv/bin/python -m pytest --no-cov -p no:cacheprovider`, targeting the new `test_numerics.py` plus the five named existing brain/loss/network/optimizer/training DTO suites. Environment: `PYTHONDONTWRITEBYTECODE=1`, `PYTHONPATH=/tmp/bac-verify-T01-1139ddfa42/src`, `OMP_NUM_THREADS=1`, `MKL_NUM_THREADS=1`, `CUDA_VISIBLE_DEVICES=`. Single pytest process, no xdist. The two warnings are expected PyTorch zero-element initialization notices, with finite output asserted.

Independent adversarial probe: `/tmp/bac-T01-review-probe.py`, output `/tmp/bac-T01-review-probe.log`, exit 0 using the same interpreter/environment after the tests completed. It asserts snapshot import provenance and sets torch threads to one. Results:

- **175 field-local finite-number refusals** across all 35 typed float/optional-float fields declared in the two inspected modules, testing numeric positive/negative infinity and NaN plus string `Infinity`/`NaN`. Missing unrelated fields cannot satisfy the probe: it requires the matching field location and `finite_number` error.
- Both gamma endpoints 0 and 1 accepted in both DTOs.
- **30 real feedforward factory + optimizer update controls**: all five activations, widths `[0]`, `[3,0]`, `[0,3]`, and layer norm on/off. Each yields finite observation-independent Q values and finite parameters after backward/update. Dueling zero-width behavior is separately covered by the executed full-pack regression.

Post-verification `git diff --cached --quiet aa24cd3fbdd49a252c8437b18cc1c0ad2402b7a6` exited 0. The three source byte hashes and frozen plan SHA256 still matched the manifest exactly. No candidate source or staged content changed during review.

## Explicit limits and declined judgments

This is T01 package approval only. Full repository gate and final integration-tree equality belong to root. No claim is made about full training convergence, rollout/learner parity, serving, checkpoint/resume, recurrent PER, replay readiness, scheduler clocks or other BAC tasks; their implementations are outside the permitted read boundary and this patch does not change them.

The broad C02 effective-view/provenance/preset-status design remains broader than T01. Preserving those surfaces here does not qualify their end-to-end implementation. The staged documentation/whole plan is identity-checked, not independently approved by this scoped code review.

`RecordingConfig.criteria` is `dict[str, Any]`, not a typed behavioral float surface; finite-only Pydantic configuration does not recursively constrain arbitrary Any payloads. T01 explicitly asks for typed behavioral floats, so no unsupported new restriction is requested there. Unvalidated `model_construct`, `model_copy(update=...)` or direct post-validation mutation are not authored parsing guarantees; the existing override helper takes validated DTOs. No new bypass was introduced.

Finite validation is not a guarantee that every arbitrarily large finite hyperparameter yields numerically stable float32 training. This review qualifies refusal of nonfinite authored values and the exercised finite controls, without inventing unapproved magnitude bounds or claiming global numerical stability.

The implementer's red/green development chronology was read as reported evidence, not independently reenacted. The independent current-candidate tests and probes below are the review's executable evidence. No costly full-suite run, install, network request, source edit, staging, commit or delegation was performed.
