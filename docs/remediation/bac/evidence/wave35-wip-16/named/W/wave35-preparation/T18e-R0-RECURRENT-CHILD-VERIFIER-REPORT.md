# Recurrent child verifier extension — frozen for independent review

Only the existing replay verifier and its synthetic test body changed. No recurrent application/test body was read, no application imported or run, and no actual child verification, Git/index operation, branch/worktree/checkout or delegation occurred. The producer protocol is the public T18e-R0-REPLAY-FIX-B-CHILD-API.md, SHA256 a5e327d4ca409f6c7c29e6ddf825f7201a053e3ed3b2c4d92cc95ba3c288c89e; its authored-source claims are not runtime evidence.

## Source budget and bytes

Retained five-body inventory before work: old publication verifier 102 + replay verifier 157 + synthetic tests 241 + old checkpoint selector 469 + old checkpoint tests 389 = 1,358 lines. Only the same two admitted bodies were reread/edited; final inventory is 102 + 230 + 382 + 469 + 389 = 1,572 lines, five bodies, below 5,000. No sixth body was read. Metadata-only hashes of the three unchanged bodies were measured.

| Body | Before SHA256 | After SHA256 | Final lines |
|---|---|---|---:|
| Q/verify_bac_replay_spawn_identity.py | aef826f304f66798c1845bdf1436b8fb27336708776a514f50d2f353942402a8 | 390c3a52837e88a716df15ff496967cb313f1fd63d892ca1eb0b4e48096e9146 | 230 |
| E/test_replay_spawn_verifier.py | bf2a20c8f2fa7120219717b62a8db4186e3914b66e78b0efe3955c2293658b4f | 40426b4c92459ba6861862568ccaabebc57ec23e9319ab47c87063e9b332ef71 | 382 |
| Q/verify_bac_publication_spawn_identity.py | 8fd7638fca79d2479286821f55573445f1acb4fc28a5efd801cec8a40cb53209 | unchanged | 102 |
| E/bac_checkpoint_delta.py | 33e992e31a2bfcdb0fa70fac315acc92ec3e961831b0d612c2ba8148c16ef8f8 | unchanged | 469 |
| E/test_checkpoint_delta.py | 8af61971bf01a7e2045d344fabad87905af4aaf0b5004418ecf98fa9e13941e2 | unchanged | 389 |

Q is /workspace/bac-review-2026-11-01/qualification; E is the existing work directory's evidence-management. Prior exact helper/test versions are retained in published WIP15 evidence. Scoped diff T18e-R0-RECURRENT-CHILD-VERIFIER-REVIEW.diff has SHA256 01bf31dabb3b9ef7dee4348a8533fc0821796ec3d708fd7a33fa9bc8fd7a5169; generated from retained pre-edit bytes, not Git. Black formatting contributes whitespace changes. Explicit subprocess check=False preserves the existing returncode refusal behavior while satisfying Ruff.

## Public interface and strict role selection

CLI remains python Q/verify_bac_replay_spawn_identity.py SPEC [JOB_INDEX]. Python entry remains verify(spec_path, job_index=0). Exactly two job names select finite configurations; no guessing, wildcard roles or arbitrary nodes:

- replay-poison retains role replay_poison, success message replay poison fail closed, its original exact pytest node/arguments and four fully qualified training imports.
- recurrent-replay-poison requires role recurrent_replay_poison, success message recurrent replay scratch poison fail closed, and exact node tests/test_townlet/regressions/bac/test_recurrent_replay_rng_custody.py::test_isolated_recurrent_scratch_work_cannot_heal_common_poison. Remaining args are exactly -m pytest NODE --no-cov -p no:cacheprovider -p no:benchmark -p bac_source_identity -q.

Recurrent replay_imports must equal the five actual absolute paths defined in the capsule: townlet.training.sequential_replay_buffer, townlet.training.replay_contract, townlet.exploration.rng_custody, test_recurrent_replay_rng_custody and test_replay_rng_custody. Both test module paths must belong to the current source inventory and their bytes are checked, alongside all source/config/artifact entries.

Both roles retain the original three bootstrap imports, exact controller/child/observation schemas, source tree/base and manifest binding, spec/result/locked-harness/command/log binding, positive finite duration, parent exit zero, positive exact-integer PID equality with parent-owned Process and queue PID, actual child PPID/parent PID pairing, qualified exact message, debug true, Torch identity, intraop1/interop5 and one-controller CPU profile. Existing repository metadata checks remain intact. The synthetic suite mocks subprocess Git calls and flock only; no real Git process is invoked.

Identity/observation filenames select the configured role; successful custody is exclusively written as replay-spawn-custody-ROLE.json in the selected job directory. Receipt case and expected_message are role-specific; remaining schema and limitations remain unchanged. This qualifies neither future broad jobs nor CUDA/restoration-failure/whole-package claims.

## Synthetic validation

The initial 30-test synthetic run against the unchanged verifier returned exit1: 29 passed and the valid recurrent positive/exclusive test raised ValueError: job schema/name mismatch at the existing guard. This is the intended missing-role RED, reported by unittest as one error. No application source or fixture was involved.

After implementation, 30 tests passed in 0.150s. Added reverse cross-role node/role and CPU-harness-profile refusal controls produced 36 passing tests in 0.131s. Initial targeted Ruff found the pre-existing implicit subprocess check argument; this was corrected without changing the guard's behavior.

Final exact-byte commands:

```text
/workspace/hamlet/.venv/bin/ruff check Q/verify_bac_replay_spawn_identity.py E/test_replay_spawn_verifier.py
/workspace/hamlet/.venv/bin/black --check --line-length 140 Q/verify_bac_replay_spawn_identity.py E/test_replay_spawn_verifier.py
PYTHONDONTWRITEBYTECODE=1 /workspace/hamlet/.venv/bin/python E/test_replay_spawn_verifier.py
```

Final results: Ruff PASS; Black PASS (both unchanged); 36 synthetic tests PASS in 0.129s. The original 13 tests remain, generalized over fixture role attributes; recurrent inherits their message/import/PID/source/profile/result/schema/exclusive-destination coverage and adds exact old-role substitutions, unauthorized job, old-node substitution and new-test-source tampering. Additional shared controls reject both cross-role directions and invalid harness workers. Synthetic source-path files contain inert data, never imported or executed. Tests exercise real verifier reads/hashes/refusals/exclusive writes while repository interactions are mocked.

Application/default suite and genuine recurrent child execution remain UNRUN by this actor under the explicit tooling-only boundary. Independent SOL review/rerun and root's fresh genuine source/spec/result/child evidence are required before actual use. Tooling writer relinquished at these hashes.
