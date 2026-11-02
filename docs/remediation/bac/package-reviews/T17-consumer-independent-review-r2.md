# T17 consumer R2 independent static review

2026-11-02 UTC. Fresh independent review in existing `/workspace/hamlet`, requested as Astra MEDIUM. Static-only authorization respected. No project imports, runtime, collection, pytest, compiler, lint, source/index mutation, branch/worktree operation, project-source copy/deletion, or delegation. Only this ignored report was written. All14 worktrees left untouched. Code-review verification guidance was consulted; implementation and runtime were outside this assignment.

## Verdict and severity-ranked dispositions

No new actionable source defect found in the bounded R2 observer repair. Static disposition: accept the causal observer correction. Runtime qualification remains open; this review cannot declare learning/memory GREEN.

1. **P2, addressed statically — constructor interception missed actual configured network construction.** The factory calls `RecurrentTokenQNetwork.from_resolved_encoder` (NF74–94). That method allocates via `cls.__new__` and calls `_initialize` (NET553–583), bypassing `__init__`. Both original consumer observers intercepted only `__init__`. R2 intercepts the common `_initialize`, calls the saved original exactly once first, then attaches the original hook to the initialized network's actual LSTM. The retained direct constructor also calls this common method (NET538–551). This fixes both gradient and rollout observation seams without redirecting construction or changing learned modules.
2. **P2, open evidence gap — actual R2 recurrent learning and rollout memory still require measurement.** Static placement proves that these construction paths reach registration, not that subsequent gradients are nonempty/positive or lane memory is correct. Root's R2 owned34+consumer4 run and six guards are separately scheduled/running according to the assignment; no result from them was consumed here. An independent four-node run proposed below is also pending separate root scheduling. Do not downgrade or remove any learning/memory assertion if a restored observer reveals a failure.
3. **Scope limitation, open — complete upstream runner/population ownership is not independently audited here.** DemoRunner, VectorizedPopulation, replay helpers, compiler, config resolver, and input assembler implementations are outside the three-source boundary. Their imported names are not implementation evidence. The factory-to-initializer path is established directly; the full configured runner-to-factory path and optimizer/network ownership must be corroborated by runtime. This is an explicit bounded-review limit, not a newly introduced regression.

The original actual R1 affected22-module result remains **2 FAIL / 407 PASS**, as supplied by root and the repair receipt. It is not relabeled all-green or erased by this source repair. The failure audit supplies the recorded empty-gradient failure; the repair receipt attributes the second rollout-observer failure to root. This review did not independently rerun or inspect those raw failure artifacts.

## Candidate binding and complete-source inventory

Manifest DATA: `.superpowers/sdd/2026-11-01-bac-remediation-upgrades/wave11/r2-candidate.json`.

- Base: `a0802a442bc7ea529de650b8705629923a0e6c72`.
- R2 candidate tree: `f0410f6b8185cf2c87f4f6d5ddbd0a730e886dc9`.
- R1 comparison tree: `5d4685b55ccd85879d0627bb55bbc20277c58af4`.

Whole-source reads were exactly these three files, **1056 lines** total:

| File | Lines | SHA256 |
| --- | ---: | --- |
| `src/townlet/agent/networks.py` | 655 | `24d4a8627255dab42b3b9b64995c62235f71f25ea04cdbaace6616f1b6e899ed` |
| `src/townlet/agent/network_factory.py` | 179 | `31b1340b6a125754ae15dbcc981223a4a6f4056ebf9db38ffbe63ba0ff9dd75c` |
| `tests/test_townlet/integration/test_recurrent_bptt_runtime.py` | 222 | `105656e944001f44213e8c721bc98d7c99e8d8512aa1172eeabc93ea0f3df0a7` |

Standard-library text/hash checks independently proved each working file equals its R2 Git tree blob and manifest SHA256. NET/NF equal their R1 blobs. `git diff --name-only R1 R2` names only the consumer test; thus production and main-five tree blobs did not change in this repair. No fourth imported/helper/probe source was opened. The audit, repair receipt, review-package diff, manifest, and AGENTS instructions were read as documentation/DATA.

Independent full-text verification read the same consumer test at R1 and proved that R2 equals exactly the four documented substitutions, each applied twice: saved method `__init__` to `_initialize`, local saved-original name, wrapper name, and monkeypatch target/name. All other text is identical. This is stronger than only counting assertions: all **23 original assertions**, their surrounding control flow, and all scenario configuration are preserved exactly. No AST execution, project import, or compilation was used.

## Hook placement and ownership

NET585–632 completes `nn.Module` initialization, selected encoder construction, LSTM creation, and Q-head creation before each wrapper registers its hook. There is no subsequent initializer replacement of the observed LSTM on either directly visible construction path. Factory-selected encoder mode/width and all LSTM dimensions remain forwarded unchanged. Hooks neither construct throwaway networks nor replace parameters, perform backward, alter hidden state, append fabricated observations, or change return values. The gradient callback returns `list.append`'s `None`; the forward-pre-hook also returns `None`, preserving PyTorch observation-only hook semantics.

Each patch is test-local through pytest's monkeypatch fixture. It intercepts all recurrent instances constructed during that test, as the former constructor patch intended, rather than only a separately constructed probe. Each normal construction receives one registration; the shared-initializer path does not recursively call the patched method. The captured original is obtained before monkeypatching. The registration handles are not explicitly removed, but belong to test-created modules and capture only local observation lists; this behavior predates the repair and does not introduce a global class hook after monkeypatch teardown.

The broad observation lists do not carry network identity. In the gradient case this measures whichever initialized recurrent instances actually receive backward; in the memory case recording is further restricted to calls occurring within each real population step and shapes `[num_agents, 1, ...]`. Their intended online/rollout interpretation depends on the existing population execution path, which is out of the source budget. This is a preserved limitation, not evidence of false observations in R2; no speculative ownership defect is asserted. The sequence-graph test explicitly observes `self.q_network` and scopes/removes its forward hook in `finally`.

## Preserved real scenarios and invariants

`_make_pack` still authors the recurrent architecture into the curriculum copy: mean aggregation, embed32, hidden64, one LSTM layer, dropout0, Q-head64, population8, Double DQN, batch12/min16, 24 episodes, max40 steps, train frequency4. Gradient and memory cases retain horizon8; graph cases retain both horizons2 and8. No scenario reduction, skips, xfails, stand-in training, or fallback constructor was added.

`_run` still invokes the configured DemoRunner, wraps the actual initialized population optimizer's `step`, requires positive optimizer calls equal to the training counter, and compares real Q-network parameters before/after. The gradient case additionally requires recurrent type/flag, nonempty actual `weight_hh_l0` hook observations, and every recorded maximum absolute gradient strictly positive. General parameter movement has not replaced recurrent gradient evidence.

The graph cases preserve replay-request length equality, sampled bounds, actual full-length sampling, observation of the first real prefix by initial-hidden object identity, selected final loss mask, exactly one nonzero connected derivative, and finite derivative checks. The memory case preserves positive training progress, actual step-window observations, existence of mid-episode lanes, no exactly-zero hidden state for active lanes with positive counts, existence of completed lanes, and exact-zero hidden state for those completed lanes. These remain substantive configured-run requirements.

## Capability classification

This R1-to-R2 repair **restores test observation only**. It adds no runtime capability and changes no production construction, encoder selection, optimizer, backpropagation, sequence handling, or memory logic. The preexisting T17 explicit encoder construction route explains why the old observers became blind. Empty observations alone could not determine whether learning/memory was healthy; the corrected tests must now measure that behavior. A later passing R2 result would establish behavior under the retained scenarios, not demonstrate that R2 added a previously missing learning capability.

## Proposed later independent runtime: exactly four existing nodes

Only after root explicitly schedules this worker's runtime, run these existing nodes against the same bound candidate, preserving all fixtures/assertions:

1. `tests/test_townlet/integration/test_recurrent_bptt_runtime.py::test_recurrent_brain_yaml_trains_the_recurrent_weight_matrix`
2. `tests/test_townlet/integration/test_recurrent_bptt_runtime.py::test_training_keeps_the_configured_sequence_graph_connected[2]`
3. `tests/test_townlet/integration/test_recurrent_bptt_runtime.py::test_training_keeps_the_configured_sequence_graph_connected[8]`
4. `tests/test_townlet/integration/test_recurrent_bptt_runtime.py::test_training_does_not_clobber_mid_episode_rollout_memory`

These cover both repaired observation seams plus both unchanged full-horizon controls within the approved source inventory. Record actual command, candidate binding, exit status, counts, timing, and any failures. No additional helper/probe source or runtime was introduced in this static turn. Worker is stationary after this report.
