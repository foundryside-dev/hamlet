# PW04 current runner acceptance migration

Fresh bounded test owner, reusing both existing tests and prior evidence. Root retains execution, source freezes and publication. No test or runtime execution, Git operation, branch/worktree/source copy, or delegation by this owner. Root released the R164 freeze and the approved two-test migration is now written and frozen for root verification.

## Inspected source inventory

| Body | Lines | SHA256 |
| --- | ---: | --- |
| `tests/test_townlet/regressions/bac/test_pw_local_service.py` | 1508 | `a7e5728891d41a3ebf96212799443bf63f657c6aa822a93815daee223072e1b9` |
| `tests/test_townlet/regressions/bac/test_rnd_service.py` | 647 | `6b506c49d32f5b8d0dd087cc65b17c93d49fe6b63d9030952adbbc386ad97bdf` |
| `src/townlet/exploration/scoped_curiosity.py` | 1569 | `fa3c5ce8f8e75bd242e7d2fec3d5264a75952e881a87ec21eba8c039f9219e7c` |

Three complete bodies, 3,724 lines. BANK was opened for its actual public checkpoint transport; RND, runtime, runner and child implementations have not been opened in this packet. Their relevant facts are explicitly supplied by root and existing source-owner capsules. Root owns ongoing implementation changes; recorded hashes are inspection identities, not final qualification.

## Existing acceptance and preserved assertions

`test_shared_runner_checkpoint_still_roundtrips` already runs production DemoRunner for three real learning episodes, reads written checkpoint2/checkpoint3 with digests, copies checkpoint2 plus the actual roster to a genuinely fresh receiver, resumes episode3 and compares full learner/curriculum/VFS state. Its current BANK path is correct. Add `native_boundary` to the existing complete-field comparison so actual ENV history and outer RNG are covered.

`test_native_runner_checkpoint_retains_tail_and_rejects_corruption` still uses obsolete `exploration_state.rnd_state` and direct `population.exploration.rnd` mutation plus INITIAL-only population wrappers on an already bound trained receiver. Those paths cannot qualify current native restoration: old wrapper refusal could mask the intended corruption. Root approved migration to genuine current runner artifacts/fresh receivers, preserving the actual contract.

The original shared sample remains 12 admitted /10 consumed /2 genuine Adam updates /2 pending rows at checkpoint2. Original NaN-tail and optimizer missing/empty/reset_steps/capturable corruptions remain. Add explicit deep clock position/unit refusal. Each negative writes a damaged real checkpoint2 artifact and its matching digest; a narrowly observational DemoRunner subclass captures actual fresh-bound state immediately before calling `super().load_checkpoint`, and compares it after the expected semantic ValueError. It inherits production construction and run, returns no fake success and injects no lifecycle authority. Invalid counters will not be invented merely to preserve the old sentinel: fresh receiver zero counters versus saved nonzero counters establish the replacement risk.

Positive controls retain exact checkpoint2 restoration and use checkpoint3 from uninterrupted real training as the next-learning oracle for a fresh receiver continuing from checkpoint2. No backend direct update or manual ENV session substitutes for native learning. Full current provider/optimizer/learner state comparison and demonstrable predictor/Q learning remain required.

## Source-qualified transport

BANK actual checkpoint export stores current shared provider native state at `runtime.checkpoint_state()['bank']['shared_backend']['native']`. The authored feedforward fixture drive selects `adaptive_rnd`, so its RND child is `['rnd_state']`. Root confirmed the current authored shared declaration requires `{'scope':'shared','seed_policy':'legacy_shared_v1'}`; despite the literal historical name, it is the required current shared algorithm, not a compatibility fallback. No guessed enum/alias or policy rename is introduced.

## Limits

No passing execution or PW04 closure is claimed. Real runner preconditions, strict format10/current VFS validation, native child publication, exact identity and eventual independent review/gates remain root-owned obligations. Refusal must occur at the intended semantic validation cut; an unrelated constructor, stale guard or schema prerequisite failure cannot count as corruption acceptance.

## Implemented candidate after R164 release

Both original node identities remain unchanged. The shared roundtrip adds `native_boundary` to its existing full comparison. The original native corruption test uses the exact production checkpoint2 bytes/digest/roster for both successful fresh receivers; negative cases alter a copy and publish the matching digest. The observation-only wrapper delegates actual load unchanged and requires complete fresh receiver state, actual binding identities, Q/target/optimizer Parameter identities, phase/release and ambient Torch/NumPy/Python RNG to remain equal on semantic refusal. It checks semantic error families so an unrelated outer/guard error cannot silently pass.

Original tail and four Adam corruption cases remain; two clock cases are additional. The fixture explicitly authors the current shared policy. Uninterrupted checkpoint3 is a real learning oracle; predictor parameters must change and actual Adam steps reach three, then full native and population continuation state must match. No direct provider update, successful mock, manual ENV session or fabricated lifecycle receipt is used.

Current pre-format inventory:

| Body | Lines | SHA256 |
| --- | ---: | --- |
| `tests/test_townlet/regressions/bac/test_pw_local_service.py` | 1509 | `239b7aa75fa6aeb1ce80ea19e344db366b979e2244f92e1a201b7ebe45460ff1` |
| `tests/test_townlet/regressions/bac/test_rnd_service.py` | 715 | `a1276f38a3c7f3e5c9623063f0b483aa880b73dc14a36b8e1c603c5f8cc56b5d` |
| `src/townlet/exploration/scoped_curiosity.py` | 1569 | `fa3c5ce8f8e75bd242e7d2fec3d5264a75952e881a87ec21eba8c039f9219e7c` |

Total 3793 lines / three bodies. Root may format and execute; this owner has performed no application import, test, formatter or Git operation.

Specific integration risk, not an executed finding: if malformed deep provider state is first discovered only inside C preparation, conservative uncertainty fencing could alter the fresh receiver before the original no-mutation assertion. The new negative witness must expose this; it must not be weakened to accept an unrelated guard or terminal mutation. Root source-qualified the observation cut and actual ENV binding getter.
