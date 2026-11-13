# Recurrent child verifier: independent scoped review

2026-11-13. **SPEC: approved for the bounded recurrent role extension. QUALITY: approved at the exact source hashes below.** No material defect was found in the new role selection or the retained replay-poison guards. This review does not establish actual recurrent child execution or qualification.

## Scope and source identity

The producer was explicitly selected as `gpt-6-astra` medium; the root orchestrator explicitly selected this independent verifier as `gpt-6-sol` medium. Those are orchestration selections, not independently exposed runtime version identifiers. I reviewed the public `T18e-R0-REPLAY-FIX-B-CHILD-API.md` (SHA-256 `a5e327d4ca409f6c7c29e6ddf825f7201a053e3ed3b2c4d92cc95ba3c288c89e`), the author report (SHA-256 `384aa96310c7b9be7b323c590710b2b86258f939f06ecb422362f443a2ecd9f9`), and its scoped diff (SHA-256 `01bf31dabb3b9ef7dee4348a8533fc0821796ec3d708fd7a33fa9bc8fd7a5169`). `AGENTS.md` was read in the preceding bounded task. The only additional complete source bodies read in this review were the verifier and its synthetic tests; the previously retained checkpoint selector and tests were not rereviewed. No application or supplier body was read.

| Source | Lines | SHA-256 verified before and after test |
| --- | ---: | --- |
| `Q/verify_bac_replay_spawn_identity.py` | 230 | `390c3a52837e88a716df15ff496967cb313f1fd63d892ca1eb0b4e48096e9146` |
| `E/test_replay_spawn_verifier.py` | 382 | `40426b4c92459ba6861862568ccaabebc57ec23e9319ab47c87063e9b332ef71` |

Here `Q=/workspace/bac-review-2026-11-01/qualification`, `E=/workspace/hamlet/.superpowers/sdd/2026-11-01-bac-remediation-upgrades/evidence-management` and `P` is the adjacent `wave35-preparation` directory. The retained checkpoint source packet was 573 + 616 lines; these two new bodies add 612, making four bodies and 1,801 lines for this verifier's source boundary.

## Actual synthetic execution

In `E`, I executed `python -B -m unittest test_replay_spawn_verifier.py`. Exit code 0; output: `Ran 36 tests in 0.135s`, `OK`. The suite uses inert temporary source-path DATA and mocks subprocess Git calls and file locking. It exercises verifier reads, hash checks, refusals and exclusive synthetic custody output. No real Git command, application import, or child process ran in this review.

## Findings and disposition

`ROLE_CONFIGS` admits exactly `replay-poison` and `recurrent-replay-poison`. Each selects one fixed child role, success message, pytest node and exact argument vector, and fully qualified replay import map. The new recurrent tuple and five module paths match the public child API note; the existing replay-poison tuple and four training imports remain fixed. Cross-role role/message/import/node substitutions and an unknown job are refused in the synthetic tests. Both test module paths in the recurrent import map must occur in the manifest source inventory, whose listed bytes are rehashed.

The shared verifier still binds the selected spec and parent result to the manifest and exact command/log/harness; requires finite positive numeric parent elapsed time and exit zero; matches controller and child source identities, manifest hashes, Torch version, debug mode and intraop/interop profile; compares child PID with both Process and queue observations and child PPID with the observed parent PID; and checks the current repository identity/inventory before exclusive custody output. The synthetic controls cover wrong/boolean PIDs, wrong profile and manifest/source bytes, partial schemas, result drift and duplicate destination. The returned custody receipt records hashes of the exact spec, result, controller, child, observation and verifier bytes. No new weakness was identified in these inspected guards.

The verifier validates recorded evidence; the synthetic suite cannot establish that a genuine recurrent child emitted those records or that the public child's behavioral assertions passed. Root still owns fresh source/spec/result/manifest sealing and actual child execution, custody verification, substantive qualification and publication gates. No actual verifier invocation, application runtime/import, Git/index/remote write, branch/worktree/checkout/source execution copy, deletion or delegation occurred. The only persistent write here is this review. Application R81 remains frozen.
