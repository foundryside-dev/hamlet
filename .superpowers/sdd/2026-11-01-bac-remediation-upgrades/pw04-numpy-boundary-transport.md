# PW04 native NumPy boundary transport

Scope: edit only src/townlet/config/world_roster.py and new tests/test_townlet/regressions/bac/test_native_numpy_boundary.py (maximum 250 lines). No runner or shared-service test changes. Root owns formatting, execution and independent review. Initial read-only diagnosis completed; root explicitly released these two files.

Initial source SHA-256:
- world_roster.py: 1c3f4ad0f29e663a3f7976b10593e08223bba2b46420b2d4472451a78c667f33
- runner.py: 4f05e0eec706c4b64efc0b7adc3ebd7117446f0d17e419648a1ed812e1158018
- test_pw_local_service.py: de6fae030c07cace4cdb17c6535ed09f775566811e4b400b4d5f246dafd00d66

Causal RED: qualification/wave35-r172-replay-green-attempt-1/runner-conversion/failure-controller-77c4361069931477.json identifies test_shared_runner_checkpoint_still_roundtrips[flat-per], failing first initial checkpoint through frozen_value -> owned_value with unsupported ndarray. The initially supplied c76314f405bc3a8e file instead describes the independent recurrent conversion lineage failure. Flat PER exports float32 priorities and int64 unit IDs; its existing producer contracts are retained.

Proposal: add NumPy import and exact plain ndarray support in owned_value, permitting boolean, signed/unsigned integer, floating and complex dtypes only. Reject object, structured, string/date dtypes, ndarray subclasses, and dtype metadata (which could retain mutable arbitrary objects). Copy via the ndarray implementation after validation. frozen_value and WorldRecord public reads already route through owned_value, providing input and output ownership. Add an early symmetric ndarray branch in same_value that checks exact types, accepted dtype kinds, no metadata, exact dtype and shape, and np.array_equal returning a Python bool. No coercion, subclass hooks, tolerance, pickle, deepcopy, fallback or producer changes. NaN equality remains false, consistent with torch.equal and existing scalar equality.

Tests: nested list/tuple/mapping ownership on input and repeated public payload/attribute reads; copied noncontiguous and scalar arrays; exact dtype/shape/content mismatches and non-array operands in both orders; rejection of object arrays, other unsupported dtypes, metadata and subclasses without calling custom hooks. Existing production flat-PER runner is the integration witness; root will execute it and controls.

No runtime/import/Git/new branches/worktrees/source copies performed by this worker.

Implementation delivered after root release: NumPy import plus owned_value and same_value branches only; frozen_value, WorldRecord, issuer/capability checks and producers unchanged. New regression file is 108 lines (30 parameterized cases across five tests). No tests or formatting executed by worker under root execution ownership.

Delivered SHA-256 (before root formatter):
- src/townlet/config/world_roster.py (329 lines): 0b219598f477a93c7faba4d7ab33144d26160fc1eb0cfbcca35a34ea20b54fcc
- tests/test_townlet/regressions/bac/test_native_numpy_boundary.py (108 lines): 1cb2bb4d392d27eef80fb697e1e467e50ea4c5ecf5a7c60e58cdb012dc67ca94

Qualification pending: root execution of new controls and actual four-profile DemoRunner roundtrip test, with independent review of exact accepted dtype domain and alias guarantees. No green/completion claim is made from static inspection.
