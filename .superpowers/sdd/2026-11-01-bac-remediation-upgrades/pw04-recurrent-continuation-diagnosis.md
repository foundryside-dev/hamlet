# PW04 recurrent-uniform continuation diagnosis

Read-only source diagnosis; no implementation change, runtime execution, imports, Git operation, branch, worktree, or source copy. Root owns execution and release. Inspected implementation budget: runner.py (1356), sequential_replay_buffer.py (2020), replay_contract.py (949), native_rng.py (219): four bodies, 4544 total lines. Inspection used selected ranges/searches; no additional implementation body was opened. Root AGENTS.md read; no nested src AGENTS.md found.

## Confirmed facts

- Recorded failure: `/workspace/bac-review-2026-11-01/qualification/wave35-r172-replay-green-attempt-1/runner-conversion/failure-controller-2ff669ee122ae4c3.json`, node `test_shared_runner_checkpoint_still_roundtrips[recurrent-uniform]`, candidate `72dd33a5abb56616986732b85f7678123b072ff3`. Exact tensor comparison fails within population network state: 137/544 elements differ, maximum absolute difference 0.0002708546817302704. Both population ledgers report completed batch episodes 3, eligible transitions 18, optimizer updates 6. This is learned-value divergence, not merely a counter mismatch.
- Production uniform `SequentialReplayBuffer.sample_batch` uses process-global Python `random`: `choices` plus `randint` for episode-length sampling (1481–1488), and `choice` for uniform windows (1492). Both adapter branches have the same omitted-state dependency.
- Current native payload schema permits exactly `schema`, `torch_cpu`, `torch_cuda` (native_rng.py:54). `capture` (136–146), detached ownership/validation (148–163), and final `install` (191–219) capture/restore only Torch streams. Python generator state is absent.
- Uniform sequential serialization (1775 onward) records replay rows, identities, options and archives but no sampler state. Only prioritized serialization appends `priority_state`; that state contains encoded private NumPy generator state (1681), validated/restored by the prioritized path. Prioritized sampling clones and commits that private generator (1510–1534).
- DemoRunner initializes with `seed_all(self.training_config.seed)` (201), captures native RNG under `native_boundary.rng_state` (484), prepares it before restoration (583), and installs it in the genuine component finalizer (605). Existing restoration location is correct for the RNG fields it actually carries. It cannot reinstall omitted Python state.
- Replay sample custody wraps sampling in its domain operation and owner mutation scope (replay_contract.py:725–732), but does not itself capture or restore Python sampler state. It is not a substitute for checkpoint data.

## Causal conclusion and remaining uncertainty

The native continuation contract omits an RNG stream actually consumed by recurrent-uniform learning. A receiving runner initializes a stream rather than resuming its checkpoint position, so its next uniform replay selections can differ despite exact replay row/model/optimizer restoration. Different selected sequences produce different gradients and explain the observed network and optimizer divergence. Parent-provided witness facts (recurrent PER and flat uniform pass the same actual-runner continuation scenario) support this diagnosis: recurrent PER has private persisted sampler state, whereas this uniform path uses Python ambient state.

The omitted stream is confirmed statically. Exact draw indices at the first divergent resumed update have not been observed by this agent; sole-cause/remediation sufficiency remains to be proven by root's genuine-runner rerun. Do not claim a passing repair from these static findings. Flat-uniform source and population source were deliberately not opened; their internal sampling mechanisms are not asserted here.

## Proposed minimal repair, pending root release

Extend NativeRNGState's current portable schema with an exact validated Python random state and install it through the existing genuine finalizer under the same admission, authority, revision, consumption and poison-on-setter-error protocol. This preserves the configured sampler algorithms and their distributions. Prefer a new exact schema version (for example native-rng-v2), replacing v1 rather than adding compatibility fallbacks, consistent with AGENTS.md.

Concrete requirements:

1. Capture `random.getstate()` at the same native boundary as Torch state.
2. Validate structure using exact inert built-in types before invoking any state-consuming API: current Python state version, complete MT integer vector including valid cursor, and valid optional Gaussian-cache value. Do not accept arbitrary sequences, callbacks, integer subclasses, or user-defined conversion behavior. Validate compatibility against a detached `random.Random` instance before any live publication; no temporary ambient set/rollback.
3. Own/store the validated immutable tuple state in prepared data. Schema validation and detached preparation must not advance or replace live RNG state.
4. Call `random.setstate` inside the existing install try/poison block with Torch setters; update ambient custody commitment only after all setters succeed. Preserve genuine POP-plan/C-finalizer requirements and last-install placement. A partial setter failure must retain existing fail-stop behavior, not roll back or continue.
5. Update exact-schema fixtures/callers affected by the deliberate schema change. Do not relax tensor equality, skip population fields, disable recurrent learning, replace the real runner/RNG with stubs, or move installation outside the genuine finalizer.

Do not expand the patch to process-global NumPy without evidence of a relevant consumer; private PER NumPy sampler already persists independently. Giving uniform replay a new private RNG is a larger alternative requiring factory/state changes and potentially changing sampling trajectories; it is unnecessary to repair this specific native checkpoint omission.

## Root validation required

- Rerun the unchanged actual-runner exact-continuation witness for recurrent uniform, recurrent PER, flat uniform, and flat PER after source release. Preserve the full checkpoint/population exact comparison and genuine owners.
- Native RNG regression: capture a genuine boundary after nonzero Python draws, then show authorized restore reproduces the next Python sequence exactly; test both uniform adapter routes where configured witnesses permit.
- Malformed Python-state payloads fail before live mutation; prepare/validation leave ambient Python state unchanged; prepared data ownership and unauthorized/stale/wrong-finalizer refusals remain intact.
- Retain setter-failure quarantine evidence and existing Torch CPU/CUDA coverage. No runtime evidence was generated by this agent.
