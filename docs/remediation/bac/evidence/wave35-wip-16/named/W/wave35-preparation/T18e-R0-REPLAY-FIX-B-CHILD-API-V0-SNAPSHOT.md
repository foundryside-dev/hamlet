# Recurrent replay B child protocol — source-qualified tests-only handoff

2026-11-13. New source `tests/test_townlet/regressions/bac/test_recurrent_replay_rng_custody.py`,577 lines, SHA256 `be1d4a56c30c4aa6bd797904a8d8f6ca7502059dcda992d3132fc06d2e2abadb`. This is an authored-source protocol capsule for the separately bounded verifier actor, not a runtime receipt. No bootstrap or verifier implementation body was read. Existing helper behavior is attributed to `T18e-R0-QUALIFIED-CHILD-CUSTODY-API.md`; the child's additional protocol below is directly defined in the new admitted test source.

| Field | Exact value |
| --- | --- |
| pytest node | `tests/test_townlet/regressions/bac/test_recurrent_replay_rng_custody.py::test_isolated_recurrent_scratch_work_cannot_heal_common_poison` |
| child role / multiprocessing Process.name | `recurrent_replay_poison` |
| child target | `test_recurrent_replay_rng_custody._scratch_poison_child(queue)` |
| exact queued success message | `recurrent replay scratch poison fail closed` |
| proposed root harness jobname | `recurrent-replay-poison` (not allocated/executed by author; root owns its final capture binding) |
| bootstrap call | `bootstrap._child_identity("recurrent_replay_poison")` |
| child identity artifact | `BAC_QUAL_OUTPUT/spawn-identity-recurrent_replay_poison.json` |
| parent observation artifact | `BAC_QUAL_OUTPUT/spawn-observation-recurrent_replay_poison.json` |

Child starts with the supplied genuine bootstrap identity call before constructing the tested replay. In qualified mode it reads that actual emitted child identity, adds `ppid = os.getppid()` and `replay_imports` with actual `importlib.import_module(name).__file__` paths resolved via Path.resolve(), then writes back that child-owned identity. These five exact keys and expected source locations must be verified under the root's real source checkout:

- `townlet.training.sequential_replay_buffer` -> `R/src/townlet/training/sequential_replay_buffer.py`
- `townlet.training.replay_contract` -> `R/src/townlet/training/replay_contract.py`
- `townlet.exploration.rng_custody` -> `R/src/townlet/exploration/rng_custody.py`
- `test_recurrent_replay_rng_custody` -> `R/tests/test_townlet/regressions/bac/test_recurrent_replay_rng_custody.py`
- `test_replay_rng_custody` -> `R/tests/test_townlet/regressions/bac/test_replay_rng_custody.py`

Here R is `/workspace/hamlet`; placeholder R is capsule notation only, never emitted as an observed path. Existing bootstrap imports/PID/debug/thread/manifest identity fields remain intact. The child does not fabricate their values or implement a replacement source verifier. Qualification environment is the existing all-or-none BAC_QUAL_ROOT/SHA/TREE/MANIFEST/OUTPUT protocol and must be supplied fresh by root, with bootstrap's required interop/intraop prerequisites. Bootstrap's historical supplier capsule is not evidence that current source matches any earlier manifest.

The child constructs a real prioritized recurrent owner, creates a real support domain by sampling, captures its serialized state and ambient state, issues a real prepared handle inside authentic `prepare` lineage, then publicly poisons that child domain. Both owner-local priority update and store-refresh execute genuine disposable-generator draws under transparent observation and preserve persistent/global streams. Each is followed by real sample/direct-sample/new-prepare/preissued-install refusal with full live preservation. Clear is permitted only as healthy-owner local work; domain remains poisoned and sample/prepare/install continue refusing. Complete ambient state remains unchanged after the poison experiment. Only after these assertions does child queue exactly `(message, os.getpid(), os.getppid(), qualified)`.

Parent uses multiprocessing spawn, actual context Queue/Process, name=role, and the stated target. After bounded join90 it asserts stopped/exitcode0 and receives the tuple with timeout5. It checks exact message, queued PID equals actual Process.pid, child-reported PPID equals actual parent os.getpid(), and child qualification equals the parent's genuine predicate. In qualified mode parent exclusively creates the observation JSON with `process_pid`, `queued_pid`, `exitcode`, `qualified`, `message`, `manifest_sha256` of actual manifest bytes and `parent_pid`. The external verifier must pair it to the actual child-owned identity and exact source/capture inventory. The parent neither supplies a fabricated child PID/PPID nor rewrites its identity.

Finally parent terminates only its still-running owned child if needed, joins10, closes/joins queue, closes stopped Process and refuses a surviving child; parent domain must remain healthy and its ambient state equal entry. This cleanup is the test's existing process-resource protocol, not author-run process work. Author has not executed this node. Root must admit this new distinct role/message/node/module map to the verifier before qualified execution; existing replay_poison receipts or capture roles cannot qualify it. No CUDA/hardware, restoration-failure witness, broader process ancestry or package acceptance is inferred.
