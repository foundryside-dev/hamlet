# T08 implementation receipt

Status: **DONE** — scoped implementation, focused/static checks, and immutable selected-candidate owner verification pass. The earlier interrupted mutable owner run remains recorded as diagnostic-incomplete; fresh review and standing gates remain coordinator-owned. This receipt does not release a dependency or close D01/BAC.

- candidate_sha: base `7aa6a8cedfa95f88344a7deaa9c8f80994b0aeb0`, selected staged tree `00d385ce621b7818e5354b161c22082ba42f985f`, immutable snapshot `/tmp/bac-verify-T08-00d385ce62`. Every observed test-process HEAD was this base SHA; nothing was staged or committed by this worker. The coordinator created the selected snapshot.
- scope: P2 transport/validation and finite detached legal DQN/Double-DQN target primitives only. No storage/environment/population/learner wiring.
- review_record: pending coordinator-owned fresh other-model fixed-source review.
- full_suite_status: DEFERRED_BY_COORDINATOR until G1 or earlier impact trigger; NOT_RUN by worker.
- full_suite_reason: coordinator explicitly approved deferral for pure unused primitives: only three new modules/test with no existing runtime consumer/import/constructor/schema/config/identity changes. Producer/consumer integration and material findings trigger the full gate. Worker claims no repository-wide green.
- next_full_gate: G1, or earlier trigger selected by coordinator.
- unrun_checks: standing whole-tree Ruff/Black/mypy/no-default ratchet/compiler/doc guards, full pytest/coverage/slow/applicable-hardware checks, fresh review, commit. Scoped versions were run as listed below.

## Inventory and authority

Read/write source inventory is exactly three NEW files, absent before creation, **586 complete lines**:

| File | Lines | SHA256 |
|---|---:|---|
| `src/townlet/training/replay_contract.py` |222|`3eaa725bd6d592b7524dd249125877eb91a1f707d4dfd12fbfb59b5b6cc6356c`|
| `src/townlet/training/q_targets.py` |80|`39485fe2447dc4065bd7b806775c93c0e66b51827b088605fba98505b100491f`|
| `tests/test_townlet/regressions/bac/test_transition_contract.py` |284|`b079050f8d0e11f45a5ac247e66af3939d129abb1ccc22ed134a70f728cb7a9f`|

No additional implementation/test/helper/conftest file was opened or searched. Existing owner tests were executed uninspected. Reference material read: root `AGENTS.md`, exact extracted T08 brief, accepted design baseline C05/C06, frozen approved plan references, B04/B03 reports, Superpowers using/TDD/testing-reference/verification skills. Metadata outputs: this report and `/tmp/bac-T08-owner-mutable.log`; no hidden source/helper was created. No delegation, installation, network, index/commit/push, root plan/ledger/status, or unrelated source changes.

Authority: approved plan SHA256 `2dde2d80d3d14c510878c26af1f99c42217be12d3cb3a554647bc68646feedc1`, cadence SHA256 `2b73403fcd9d139e46009c2f49add6dbe6f99310ce37018ffcf839230845d370` / `BAC-CADENCE-A-2026-11-01`; T02 dependency facts supplied by coordinator. Historical Option A stays `BAC-HISTORY-A-2026-11-01`; no maskless optimizer exception or mask synthesis exists here.

## Interfaces for downstream packages

All dataclass fields are required constructor arguments, with optional reward components explicitly `Tensor | None`:

```text
ReplayRequest(batch_size:int, sequence_length:int, min_transitions:int,
              sampling_mode:str, sequence_mode:str, sequence_objective:str)
ReplayReadiness(ready:bool, retained_transitions:int, sampleable_units:int,
                reason:Literal['ready','warmup','batch_unavailable',
                               'window_unavailable','capacity_window_impossible'])
SamplingReceipt(indices:ndarray[int64,B], weights:ndarray[float64,B],
                population_size:int, conditional_draw_probabilities:ndarray[float64,B],
                mode:str, objective_unit:str, weight_rule:str)
ReplayBatch(legality_recorded:Tensor, observations:Tensor, actions:Tensor,
            rewards:Tensor, rewards_extrinsic:Tensor|None, rewards_intrinsic:Tensor|None,
            rewards_shaping:Tensor|None, next_observations:Tensor, dones:Tensor,
            next_action_masks:Tensor, loss_mask:Tensor, lengths:Tensor, unit_ids:Tensor,
            weights:Tensor, sampling:SamplingReceipt)
HistoricalLegalityUnavailable(ValueError)
validate_successor_masks(masks:Tensor, dones:Tensor, *, action_dim:int)->None
legal_bootstrap(q_online:Tensor|None, q_target:Tensor, legal:Tensor,
                bootstrap:Tensor, *, double_dqn:bool)->Tensor
legal_td_target(rewards:Tensor, dones:Tensor, q_online:Tensor|None,
                q_target:Tensor, legal:Tensor, *, gamma:float, double_dqn:bool)->Tensor
```

The validator is defined in RC and imported/reexported in QT. RC imports no later sampler implementation. Request strings remain the specified general P2 `str`; nonempty values are required and applicable downstream consumers MUST reject unsupported modes before sampling/mutation. Request sampling mode is the selected PER policy where applicable, while uniform consumers preserve their actual configured law. Receipt labels are nonempty provenance, not request-enum aliases; tests use `mode='uniform_without_replacement'`, `objective_unit='transition'`, `weight_rule='unit'`. Sampler-specific math/truthfulness remains T13/consumers' responsibility; conditional ordered-draw probabilities individually lie in `(0,1]`, without an erroneous sum-to-one constraint.

RC uses compact float32 observations and canonical float32 rewards/components; int64 actions/lengths/unit IDs; bool legality/dones/loss/masks; exact float64 learner weights matching the float64 receipt. Components stay independently optional and are never recomposed. Shapes are flat `[B,D]`/`[B]`/`[B,A]` or recurrent `[B,L,D]`/`[B,L]`/`[B,L,A]`, with `[B]` lengths/IDs/weights. Lengths define real prefixes; anchor-only loss masks do not erase real history. All real rows require recorded legality; live empty masks and real rows following a terminal refuse. Padding is transport, not experience. Receipt unit indices are nonnegative identifiers and need not be bounded by contiguous storage population slots.

Ownership: constructors detach/clone tensors; receipt arrays are copied/read-only; ReplayBatch also copies its nested receipt. Frozen fields prevent rebinding, not consumer tensor mutation. Producer mutation cannot rewrite the constructed transport; consumers must avoid mutation during learner use. Explicit unconstrained adapters must supply their declared all-legal invariant; no constructor invents one for constrained unknown history.

QT preserves arbitrary leading dimensions. It excludes non-bootstrap rows before any masked max/argmax, masks illegal choices, requires finite actually used legal selection/evaluation values, and returns detached results. Terminal poison never enters a `0 * -inf` path. Gamma is finite `[0,1]`, including zero; gamma zero does not read Q values for target arithmetic. Recurrent callers pass real rows defined by lengths, independently of loss selection. Full storage, historical archive dispatch, sampler estimators, sequence unrolling, and production optimizer integration remain later tasks.

## Red, API/fixture preflight, and green

Main-checkout test processes used `/workspace/hamlet/.venv/bin/python`, `CUDA_VISIBLE_DEVICES=`, `PYTHONPATH=/workspace/hamlet/src` (the final harness portability red/green used `/tmp/bac-T08-import-probe:/workspace/hamlet/src`), `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1`, and `torch.set_num_threads(1)`. The stdin runner imported public `townlet`, asserted `/workspace/hamlet/src/townlet/__init__.py`, printed observed HEAD and SHA256/absence for all three allowed files, then called pytest. Final focused/collection runners also asserted unchanged own file bytes afterward. The tests derive their checkout with `Path(__file__).resolve().parents[4]` and assert actual RC/QT module parents are that checkout's `src/townlet/training`, permitting immutable snapshot verification with multi-entry PYTHONPATH while catching accidental mutable-main imports.

Exact focused invocation inside that runner:

```python
pytest.main(['--no-cov','-p','no:cacheprovider',
             'tests/test_townlet/regressions/bac/test_transition_contract.py','-q'])
```

- Before implementation: **20 collected,20 failed**, all intentional `AssertionError: T08 missing interface: replay_contract`; RC/QT absent. Fixture/import/collection succeeded; no unrelated syntax/fixture failure counted as red.
- Initial green:20passed.
- Additional causal red: scalar-Q diagnostic produced `IndexError`, shared nested receipt allowed producer mutation, and post-terminal real rows were accepted;23-case run showed3failures/20passes, then23passed after fixes.
- Dtype/receipt red from coordinator boundary facts:5new assertions failed/23passed; then28passed after float32 storage, float64 exact estimator-weight checks.
- Harness portability causal red: with multi-entry `PYTHONPATH=/tmp/bac-T08-import-probe:/workspace/hamlet/src`, selected Double-DQN test failed because the prior whole-PYTHONPATH path assertion treated the colon-separated string as one path (1failed/27deselected). Replaced expected checkout derivation with the test file location, removed unused os import, and ran all28 under the same multi-entry PYTHONPATH green. No broad mutable owner repeat.
- Final frozen-byte focused green: **28passed in0.11s**, exit0, same before/after HEAD and own hashes.

Hand-calculated controls cover legal target3 versus unmasked51 and gradient `[[14,0]]` for prediction10 (the illegal target would push10 upward); online-vs-target rankings distinguish Double target3 from vanilla6; detached successor Q gets no gradient. Terminal `-inf`/NaN/large values return exact bootstrap0/reward7 for both variants. Recurrent real vs skipped rows, gamma0 with poisoned Q, gamma-domain rejection, live empty masks, dtype/shape/value refusal, optional components/canonical reward independence, real non-anchor legality, real length1 transport, no post-terminal experience, clone isolation, and exact receipt dtypes/weights are exercised.

## Owner-suite commands and observed results

The same one-process identity runner used this exact pytest argument list, once with `--collect-only` added for preflight, then for execution:

```text
--no-cov -p no:cacheprovider
 tests/test_townlet/unit/training/test_replay_buffers.py
 tests/test_townlet/unit/training/test_prioritized_replay_buffer.py
 tests/test_townlet/unit/training/test_sequential_replay_buffer.py
 tests/test_townlet/unit/training/test_episode_accounting.py
 tests/test_townlet/unit/population
 tests/test_townlet/integration/test_authored_episode_lanes.py
 tests/test_townlet/integration/test_recurrent_bootstrap_runtime.py
 tests/test_townlet/integration/test_recurrent_bptt_runtime.py
 tests/test_townlet/regressions/test_episode_lane_population.py
 tests/test_townlet/regressions/test_episode_lane_learning.py -q
```

Preflight: **358tests collected**, exit0, unchanged own bytes. Mutable execution: observed four failures in `test_recurrent_bootstrap_runtime.py` and four in `test_recurrent_bptt_runtime.py`; preceding B04/population/authored suites showed passes and five skips. On coordinator instruction, stopped own process via SIGINT at96%, exit130. No completed owner pass count or exact failed node suffix/trace is claimed: pytest had deferred details until final summary and interrupt emitted no summary. The coordinator reported a parallel RND/population checkpoint-interface edit; this worker did not inspect those files or independently assign cause. Reconstructed progress/command receipt is `/tmp/bac-T08-owner-mutable.log` (explicitly not a complete raw stdout capture). No broad repeat against changing shared imports was made. The immutable selected-candidate run below supplies completed owner evidence.

## Completed immutable owner verification

Coordinator-selected snapshot `/tmp/bac-verify-T08-00d385ce62` contains base `7aa6a8cedfa95f88344a7deaa9c8f80994b0aeb0` plus only the three frozen owned files, staged tree `00d385ce621b7818e5354b161c22082ba42f985f`. The coordinator verified its RND/population files equal committed baseline, excluding the parallel work. Worker read only candidate metadata, not those implementations.

From the snapshot, the SAME358 owner selection above was executed first with `--collect-only`, then without it. Both commands added `-p bac_source_identity --maxfail=1 --tb=short` and used the exact environment:

```bash
CUDA_VISIBLE_DEVICES=
PYTHONPATH=/tmp/bac-verify-T08-00d385ce62/src:/workspace/bac-review-2026-11-01/qualification
OMP_NUM_THREADS=1
MKL_NUM_THREADS=1
BAC_QUAL_ROOT=/tmp/bac-verify-T08-00d385ce62
BAC_QUAL_SHA=7aa6a8cedfa95f88344a7deaa9c8f80994b0aeb0
BAC_QUAL_TREE=00d385ce621b7818e5354b161c22082ba42f985f
BAC_QUAL_MANIFEST=/workspace/hamlet/.superpowers/sdd/2026-11-01-bac-remediation-upgrades/task-T08-candidate.json
BAC_QUAL_OUTPUT=/workspace/bac-review-2026-11-01/qualification/T08-owner
```

Interpreter `/workspace/hamlet/.venv/bin/python`; one process, no xdist, `torch.set_num_threads(1)`. The qualification plugin was executed uninspected. The runner asserted `townlet.__file__` resolves into the snapshot, recorded base HEAD, selected tree, and all three hashes, and checked `git diff --cached --quiet 00d385ce621b7818e5354b161c22082ba42f985f --` before and after. Own file hashes and selected staged index were unchanged after both processes. No index/source edit was performed.

- Collection/import preflight: **358tests collected in0.77s**, exit0.
- Complete owner run: **353passed,5skipped in269.16s**, exit0. All recurrent bootstrap/BPTT and episode-lane learning cases passed in this coherent snapshot.
- Permanent complete logs: `/workspace/bac-review-2026-11-01/qualification/T08-owner-collect.log` (SHA256 `b57726afb8f107b36098e9c0ec58fd59a0cb6bf5023c408a4406c7f90a21828d`) and `/workspace/bac-review-2026-11-01/qualification/T08-owner-tests.log` (SHA256 `a95399153a57327cfcfb63ff425569565c20ef4b0d7c6d4b5b01ec5a6e7c235a`). Both were captured with `set -o pipefail` and `tee`, so pytest exit status and causal diagnostics survive.

The earlier mutable run's eight failure node suffixes/traces remain unavailable and are not invented or retrospectively attributed. No additional source file, test, helper, fixture, or plugin was inspected; the original586line/threefile source inventory is unchanged.

## Static commands

Final exact scoped commands all exited0:

```bash
.venv/bin/ruff check src/townlet/training/replay_contract.py src/townlet/training/q_targets.py tests/test_townlet/regressions/bac/test_transition_contract.py
.venv/bin/black --check src/townlet/training/replay_contract.py src/townlet/training/q_targets.py tests/test_townlet/regressions/bac/test_transition_contract.py
.venv/bin/mypy src/townlet/training/replay_contract.py src/townlet/training/q_targets.py
.venv/bin/python scripts/no_defaults_lint.py src/townlet/training/replay_contract.py src/townlet/training/q_targets.py --whitelist .defaults-whitelist.txt
```

Ruff:all checks passed; Black:3files unchanged; mypy:2source files clean; no-default:zero defaults. Initial lint/format/no-default findings were repaired within owned files. An initial scoped no-default command with global `--ratchet .defaults-ratchet` detected zero defaults but exited1 because scoped0 is below the whole-repository ceiling614 and requested lowering that global ceiling. The global ratchet was not edited or bypassed; scoped scan was rerun without inappropriate whole-tree ratchet, and the standing whole-tree ratchet remains coordinator-owned.

The three source files are frozen at the hashes above. No production D01 repair, full-suite success, review approval, commit, or overall BAC closure is asserted.
