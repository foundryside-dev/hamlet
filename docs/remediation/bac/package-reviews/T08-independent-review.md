# T08 independent fixed-candidate review

Review status: **SCOPED PASS; coordinator release gates pending**. No demonstrated P1/P2 correctness or safety defect in the three-file candidate. Spec verdict: the P2 transport and finite historical legal-target primitive contracts pass the checks below; actual adapter law validation and production integration remain downstream responsibilities. Quality verdict: straightforward owned DTOs and correctly detached target arithmetic; no blocking finding. This is package technical review, not overall BAC/D01 readiness or repository-wide green.

## Immutable identity and bounded inspection

- Snapshot: `/tmp/bac-verify-T08-00d385ce62`.
- HEAD/base: `7aa6a8cedfa95f88344a7deaa9c8f80994b0aeb0`; staged candidate tree: `00d385ce621b7818e5354b161c22082ba42f985f`. HEAD alone does not contain the additions.
- Manifest: `task-T08-candidate.json`, SHA256 `b2bc3408df6c55abe8660379cd716cca67c78344a75c8099ab5aeb6d0cc9042e`.
- Independently verified all three file digests against that manifest before execution and again after focused/probe execution. Plan `2dde2d80d3d14c510878c26af1f99c42217be12d3cb3a554647bc68646feedc1` and cadence `2b73403fcd9d139e46009c2f49add6dbe6f99310ce37018ffcf839230845d370` bytes also verified by hashing, without opening the whole plan.
- Source inspection: `replay_contract.py`222 + `q_targets.py`80 + `test_transition_contract.py`284 + own `task-T08-review-probe.py`155 = **4 files / 741 lines**. No other implementation, helper, fixture or conftest source read. Additional references were task/review reports, extracted T08 brief and a targeted search of extracted T02 requirements. No candidate/index/HEAD edits, delegation, installation or network. The probe/report live only in the root ignored metadata directory.

## Independent execution evidence

All executions used `/workspace/hamlet/.venv/bin/python`, `PYTHONPATH=/tmp/bac-verify-T08-00d385ce62/src`, `CUDA_VISIBLE_DEVICES=`, `OMP_NUM_THREADS=1`, `MKL_NUM_THREADS=1`, `torch.set_num_threads(1)`, and snapshot working directory. API preflight inspected public signatures and asserted actual `townlet`, RC and QT module origins in the snapshot. No fixture data required mutation; owned probe arrays were copied into constructors before producer mutation.

Focused preflight/execution: `pytest.main(['--no-cov','-p','no:cacheprovider','tests/test_townlet/regressions/bac/test_transition_contract.py','-q'])`, first with `--collect-only`: **28 collected, then 28 passed in 0.07s**, exit0.

Independent probe command:

```bash
CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=/tmp/bac-verify-T08-00d385ce62/src /workspace/hamlet/.venv/bin/python /workspace/hamlet/.superpowers/sdd/2026-11-01-bac-remediation-upgrades/task-T08-review-probe.py
```

Probe result: **PASS**, exit0. Its independent NumPy action-enumeration oracle exercised30 combinations of scalar, batch1, batch7, rank2 and rank3 leading dimensions; standard/Double DQN; gamma0/.5/1. It poisoned terminal/illegal Q values with NaN/infinity and mixed finite values, and proved exact zero bootstrap/reward-only behavior and detached outputs. A separate Double witness selects online action1 and evaluates target4 even when the unused target action0 is NaN; vanilla correctly diagnoses that same legal NaN because vanilla must use it for ranking.

Actual loss/backprop tests confirm historical legal target3 instead of illegal51 for reward1/gamma.5/Q=[4,100]. Prediction10 has gradient+14 and takes a downward update; the explicit illegal51 counterfactual has the opposite direction. No successor gradient flows. This is execution evidence, not merely a shape assertion.

Mixed-length real recurrent windows length1/3/5 contain NaN padding, independently selected final-anchor loss rows, recorded real masks and a real terminal. Q is derived separately from each real-length group's captured successors; all computed targets match a separate formula. Mutating the producer observation/mask arrays after construction cannot change the sampled history. Unknown legality at a real non-anchor row, post-terminal real experience and padded loss selection all refuse. Components remain independently optional and canonical reward1 stays1 despite intrinsic component47. A receipt with conditional probabilities[.2,.8,1] is accepted without an erroneous sum1 condition; copied nested receipt indices remain unchanged when producer receipt storage is made writable and changed.

## Strengths and limits

- RC owns exactly the required DTO fields and has no dependency on later sampler code. Dtypes and per-unit estimator weights are checked, with exact learner/receipt weight agreement. Validation occurs before any input mutation, and tensors detach/clone after validation.
- Real prefixes come from lengths, not loss masks. Every real row requires legality provenance, including non-anchor rows. No masks are inferred for constrained history. Post-terminal rows cannot be disguised as real sequence experience.
- QT selects/evaluates historical legal actions with separate online ranking for Double, excludes non-bootstrap rows before reduction, and rejects nonfinite actually used values or overflowing final targets. Gamma0 avoids Q arithmetic while retaining shape/type/mask checks.
- Request mode fields intentionally remain `str` and currently accept unknown nonempty strings (`ReplayRequest(1,8,0,'typo','typo','typo')`). This primitive has no sampler or mutation path, so the probe does not demonstrate a silently wrong sampler. Prescribed P1 values must be supplied and applicable consumers must reject unsupported modes before mutation, as the implementation receipt states; later adapter tests must verify that contract. A receipt label alone is not proof of an actual proposal law. The coordinator explicitly confirmed this boundary ruling during review: P2 remains string-typed; T02 authoring enums remain strict; nonprioritized adapters preserve the configured uniform law and treat selected PER mode as inactive/preset. Unknown strings do not authorize fallback.
- Diagnostics identify the field/invariant but generally do not include offending row coordinates. The coordinator confirmed field/invariant identification is the applicable located-diagnostic requirement at this DTO boundary, which has no authored source locations. Row coordinates could improve usability but their absence does not establish a defect here; no P3 finding is raised.
- Tensor transports are owned copies, not immutable tensors. Frozen dataclasses forbid rebinding; deliberate consumer tensor mutation remains possible and documented. NumPy receipt arrays are read-only copies; callers can deliberately re-enable writing on their own arrays, but nested transport does not alias them.
- No actual buffers, samplers, recurrent hidden-state unroll implementation, public loaders, archive restoration, population optimizer integration, full production D01 fix, GPU path, full-suite coverage or stochastic proposal estimator correctness was reviewed. Existing implementation source beyond the bounded inventory was not opened. No generic PER sample-max rule or zero-times-terminal multiplication rule was substituted for the BAC contracts.

## Remaining release evidence

The implementer's mutable broad run had eight observed recurrent failures and no final diagnostics; this review does not assign them to T08. The separately assigned coherent immutable owner run is now PASS: 358 collected, 353 passed and 5 skipped in 269.16s; see the verified evidence below. It was not duplicated by this reviewer. Coordinator whole-tree static guards remain required before package release. Full pytest is deferred only under the coordinator's manifest impact ruling to G1 or an earlier trigger; this review does not independently waive that gate. Red evidence is attributed to the implementer's receipt; the reviewer independently executed fixed-candidate green/probes, not the original red baseline.


## Immutable owner result appended after completion

The coordinator supplied the completed owner run for the same snapshot/base/staged tree: **358 collected; 353 passed, 5 skipped in 269.16s**, one CPU/no xdist, torch threads1. The owner runner asserted snapshot import origin, base, staged tree and three source digests before/after. The reviewer independently hashed both logs and inspected their result/identity summaries:

- `/workspace/bac-review-2026-11-01/qualification/T08-owner-tests.log`: SHA256 `a95399153a57327cfcfb63ff425569565c20ef4b0d7c6d4b5b01ec5a6e7c235a`.
- `/workspace/bac-review-2026-11-01/qualification/T08-owner-collect.log`: SHA256 `b57726afb8f107b36098e9c0ec58fd59a0cb6bf5023c408a4406c7f90a21828d`.

After reading that evidence, the reviewer again verified the unchanged manifest SHA256, HEAD/base, staged tree and all three candidate source hashes. No further source was read or probe added: the inventory remains4files741lines. The in-progress main-checkout RND/POP changes were excluded from this snapshot. Earlier mutable-run failures remain diagnostic-incomplete and are neither attributed to QT nor treated as passing evidence.

Final scoped spec/quality verdict remains **PASS, no actionable P1/P2/P3 findings**. Independent focused/probe and exact-candidate owner evidence pass. Root standing non-test guards are still running; the coordinator owns their completion and package release. Production integration and overall BAC readiness remain outside this primitive approval.
