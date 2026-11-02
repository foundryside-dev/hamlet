# T17 direct-consumer failure audit — static, no repair

2026-11-02 UTC. Root remains the sole integration/index owner. This audit ran only static reads, file inventory/hash checks, and the ignored-document write. Runtime sessions remained root-owned; no project imports, pytest/collection, compiler, runtime probes, formatter/linter, source edits, index writes, branch/worktree operations, project copies/deletions, or delegation occurred. All existing worktrees were left untouched. Systematic-debugging guidance was consulted; its runtime reproduction and implementation stages were deliberately outside root's current authorization.

## Evidence boundary

The whole-source inventory is exactly three files, matching `T17-consumer-source-baseline.json`:

| Source | Lines | SHA256 |
| --- | ---: | --- |
| `src/townlet/agent/networks.py` | 655 | `24d4a8627255dab42b3b9b64995c62235f71f25ea04cdbaace6616f1b6e899ed` |
| `src/townlet/agent/network_factory.py` | 179 | `31b1340b6a125754ae15dbcc981223a4a6f4056ebf9db38ffbe63ba0ff9dd75c` |
| `tests/test_townlet/integration/test_recurrent_bptt_runtime.py` | 222 | `2701678bcb442360eb2a860ea4e74bc7d5b8d4b9b2f639b78c21cd7db9f2494a` |
| Total | **1056** | No fourth implementation/helper source read |

Failure DATA read: `/workspace/bac-review-2026-11-01/qualification/wave11-r1-affected/affected/failure-gw0-567287f6c9070f7a.json` and its `failure-controller-567287f6c9070f7a.json` duplicate. Both identify the same node, call-phase failure at test line103, empty `gradients`, and candidate tree `5d4685b55ccd85879d0627bb55bbc20277c58af4`; they are two reports of one failure, not two independent reproductions.

`T17-implementation.md` was read as supplier prose. Its claims about unchanged prior forward/state/RNG behavior, versioned omission policy in OP, earlier runtime results and the wider implementation inventory are attributed to that supplier, not independently established by reading other source here. The current three-file hashes and actual construction/forward code below were independently checked. DemoRunner, VectorizedPopulation, compiler, config resolver and input assembler implementations were not opened. Accordingly the complete runner-to-factory upstream call chain is not independently audited; the factory-to-network route is established directly, and the failing configured scenario is evidenced by the supplied failure record and test.

## Exact causal diagnosis

1. The test captures `RecurrentTokenQNetwork.__init__`, patches that method, calls the original, then registers a real autograd hook on `self.lstm.weight_hh_l0` (test92–98). Appending to `gradients` happens only in that registered hook. No hook installation happens outside this wrapper.
2. `NetworkFactory.build_recurrent` now resolves the token encoder and returns `RecurrentTokenQNetwork.from_resolved_encoder(...)` (NF74–94), forwarding all configured LSTM dimensions and the explicit selected encoder pair.
3. That classmethod allocates with `cls.__new__(cls)`, invokes `network._initialize(...)`, and returns the network (NET553–583). This explicit allocation/setup path never calls the patched Python `__init__`. Both the retained direct constructor and additive classmethod share `_initialize`, but only the direct constructor passes through the instrumented method.
4. `_initialize` calls `nn.Module` setup, constructs the selected token encoder, then the real `nn.LSTM` and Q head (NET585–632). Forward still computes encoder → LSTM → Q head (NET639–655). Bypassing the test's `__init__` patch therefore bypasses hook registration; it does not bypass LSTM construction or forward computation.
5. The recorded test reaches line103 after `_run` returns and the recurrent flag/type checks pass. `_run` itself requires positive actual optimizer-step calls, equality with the population training counter, and at least one changed actual Q-network parameter (test81–85). Those earlier assertions did not fail in this recorded execution. They establish actual updates and some parameter movement, not specifically movement or nonzero gradients in `weight_hh_l0`.

The empty list is causally explained by a missed observation seam after the additive construction route changed. In this route the hook is never attached, so the same empty list would result whether the recurrent gradients were healthy, zero, or absent. The recorded assertion does **not** diagnose a learning regression; it also does **not** prove recurrent learning is healthy. Nonzero recurrent gradients must still be measured after restoring the observer on the actual network. A generally changed parameter is insufficient to substitute for that measurement.

## Bounded proposed correction, awaiting separate root clearance

Change only the existing consumer test file. In its two network-construction observers, wrap the common `RecurrentTokenQNetwork._initialize` instead of `__init__`: save the original initializer, call it once with the existing `self, *args, **kwargs`, and attach the existing hook immediately afterward. Rename local wrapper variables to reflect initialization if desired. No production change is needed for this diagnosed observation failure. Do not make the factory call the retained linear-only constructor, construct throwaway linear modules, replace learned modules, or remove the explicit interaction selection to satisfy the observer.

The same file's rollout-memory test (test184–196) uses the identical `__init__` interception pattern to attach an LSTM forward-pre-hook. It has the same statically established blind spot under resolved construction. Move that observer to the same common initializer in the same bounded correction; no claim is made here about a second runtime failure, since this audit read only the requested failure pair. The sequence-graph test already observes the live population network during `_recurrent_predictions`; its construction seam does not need changing.

Common-initializer interception preserves coverage of both retained direct construction and the additive factory construction. Calling the saved original exactly once before registration preserves module construction, parameter identity/order, and the real LSTM object being observed. Do not manufacture gradients, append observation sentinels, simulate a backward pass, substitute standalone training, or weaken empty/nonzero assertions. Existing hook bodies continue measuring actual configured-run autograd and actual LSTM inputs.

## Preserved capability and required subsequent evidence

- Keep the authored recurrent YAML scenario, mean aggregator, embed32/hidden64, one LSTM layer/dropout0, population8, Double DQN, batch12/min16, 24 episodes, 40 steps, train frequency4, and sequence length8 for the recurrent-weight and rollout-memory tests. Keep both sequence-graph cases, lengths2 and8. No fixture or scenario reduction.
- Retain all `_run` real optimizer-count/counter/changed-parameter assertions and recurrent flag/type checks. Retain `assert gradients` and **every** recorded recurrent gradient being strictly positive. Merely observing any updated parameter cannot replace these.
- Retain the real first-prefix-to-final selected-Q derivative test, full-length sampling, correct replay request, exact selected loss-mask check, exactly one connected nonzero derivative and finite derivative checks across both horizons.
- Retain real rollout-step observation, positive training progress, mid-episode evidence/nonzero live-lane memory, completed-lane evidence and exact-zero completed-lane hidden state assertions. The common initializer only restores the original forward-pre-hook placement on actual LSTMs.
- Retain `from_resolved_encoder`, required explicit encoder options, legacy direct constructor signatures/linear meaning, and interaction-MLP capability. This proposal changes observation only.

After root closes active runtime sessions and separately clears source repair, implement the bounded test-seam correction, then rerun the affected real recurrent integration cases and root-required qualification gates. The gradient case must now produce real nonempty strictly-positive `weight_hh_l0` observations while all existing training assertions pass; both horizon cases and rollout/completed-lane assertions must also pass. If restored observation instead reveals absent/zero recurrent gradients or broken memory, treat that as new runtime evidence and investigate it rather than masking it. This audit neither ran those gates nor declares a fix/pass/full qualification.

Only this ignored audit was written. Worker returns stationary; no source repair or runtime command is authorized by this document.
