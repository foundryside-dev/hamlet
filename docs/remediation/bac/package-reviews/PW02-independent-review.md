# Review provenance

Final bounded source/spec review; runtime qualification is supplied by the coordinator.

Original artifact: `PW02-astra-review-r5.md`; SHA256 `76abd742fc6ee7f50139b4d9a72e45fd7434915d575d2523f15fe53e267792a1`. The original is retained unchanged. This portable rendering normalizes execution paths; it does not alter the review verdict or source binding. The final reviewed source hashes match sum tree `1a1ca88cab7cc5bfe97e0922534d23e733d17e2d`, identical to qualified source release `eb73173496a7955b30a6fea4b65ccae8cc615b87`. Earlier source identities and staged-candidate bindings in the body retain their original meaning.

# PW02 adversarial source/spec reassessment R5

**Scoped static verdict: PASS — no remaining confirmed P1/P2 in the reviewed finite primitive.** The R3 mapping-key P2 is repaired without narrowing the callback contract. This verdict covers the complete inspected PW02 ownership/RNG/lifecycle implementation against its accepted capsule, not merely the changed expression. It is not repository qualification, CUDA qualification, native private-bank qualification, X02 closure or broad strict-B completion. Root must continue the complete BAC implementation and remaining gates.

## Candidate and complete source inventory

Existing workspace `/workspace/hamlet`; HEAD `23755537926c2808c8b312f4f5b52ad76ab594ab`; staged tree `1a1ca88cab7cc5bfe97e0922534d23e733d17e2d`; manifest `wave05/green-r5-candidate.json`. Exactly five complete source files / **2799 lines** are charged:

| File | Lines | SHA256 |
|---|---:|---|
| src/townlet/exploration/world_curiosity_state.py | 734 | 8b242ef58af2840c069db3d599606ba4760eea675e6be5bf00d8eb89c23b5b82 |
| src/townlet/exploration/rnd.py | 661 | 3a774dfb042cdbf20b66555c41f75c2d537b6ff49472395877dfcf5595e26e72 |
| src/townlet/exploration/icm.py | 380 | 8004aec68d19c962df0cf6785b00af32c8553a3746fee95be39009555f9d44b8 |
| src/townlet/exploration/adaptive_intrinsic.py | 226 | 80ecb26fb33626cc9efd271422c69cdae495412f5db94a505eb59628b58b6cd9 |
| tests/test_townlet/regressions/bac/test_pw_rng_domains.py | 798 | 5e671b5693eb3741424b1fadb098eca6ea3d5f51599dddc1513c1f2292847848 |

Both changed whole files were reread; the three unchanged provider files were previously read completely in this same review chat and their current hashes are identical. Their actual code remains part of this reassessment, including constructors, optimizer ownership, snapshots, loaders and adaptive history. No sixth source/helper/probe is read. Contract references remain the accepted PW02 interface capsule, PW02 task brief and per-world curiosity addendum. Root AGENTS.md was read previously; higher user preservation instructions control over conflicting blanket deletion guidance. Applicable verification evidence discipline remains in force, without overriding the explicit ban on reviewer runtime. No durable governance rule or user-only fallback is adopted; no failed rule is used as a grant or restriction.

No project import, runtime, test execution, source/index edit, branch/worktree/source copy, deletion, tracker write or delegation occurred. This ignored prose report is the only R5 write. No capability/default/shared alternative is removed or restricted by the verdict.

## Confirmed repair and meaningful regression

At `world_curiosity_state.py:248–249`, `_owned` now recursively owns **both** mapping keys and values. Native Adam Parameter keys pass through tensor detach/clone at 242–243; composite tuple keys recursively pass through 252–255. The original alias counterexample therefore no longer retains live parameter storage. This preserves general mapping results instead of imposing an unapproved numerical-only callback restriction.

The six cases at `test_pw_rng_domains.py:713–759` cover RND, ICM and adaptive RND × native/tuple keys. They construct two independent equal owners, execute an actual first optimizer update, and assert parameter/Adam-moment changes and counters before exercising the ownership edge. The callback exports native `optimizer.state` (725–728); the caller mutates an exported key and moment value outside the callback (744–748). It confirms that those exported values actually changed, the owner revision did not change, and the entire owned backend/RNG snapshot remains equal (749–752). It also requires detached key tensors, executes a genuine second update on both owners, compares draws/rewards/full learned state and final snapshots, and verifies global RNG restoration (753–759). The test does not merely mirror the clone implementation or hide damage by resetting the backend.

Root's counted pre-repair R4 log, `qualification/wave05-repair-red-r4/PW02-key-red.log`, shows all six cases failed on tensor state equality after the intended live parameter mutation: **6 failed, 26 deselected in 2.70s**. Root attributes intact source/HEAD/index guards to that run. This reviewer read the log tail and did not run the tests or read an additional probe.

## Whole primitive adversarial reassessment

**RNG identity and continuation.** WS:416–444 initializes separate named components with local generators, leaving unrelated globals untouched. CPU Torch primary seed and versioned Python/PCG64/legacy NumPy/CUDA suffix derivations remain distinct. WS:455–512 validates the required RNG envelope, descriptor identity, component/device inventory, declared seeds, canonical Torch/Python/legacy states and PCG64 ranges before creating live state. Descriptor identity excludes spectator order while exact world identity is retained. Snapshot copying remains recursive and does not borrow state arrays/tensors. I found no remaining reseed-to-initial-position path in ordinary restore.

**Nested activation and failure custody.** WS:532–589 retains one global RLock, a thread-local stack and cross-owner refusal before mutation. Same-component direct reentry shares active state; true A→B→A finds the suspended frame, saves B's current ambient state and restores the advanced A frame on B exit. The concrete regression is now at test:762–783 and compares both streams plus full snapshots. Python's facade (WS:372–387) uses the current global Python stream and refuses outside its frame. PCG64 stays an explicitly distinct stream. Cleanup catches BaseException, attempts each global restoration independently (349–369), quarantines failed capture, and poisons the coordinator if restoration fails. The process-isolated poison regression remains intact at test:598–685. Ordinary callback failure advances captured RNG and quarantines the backend; it does not claim rollback or silently repeat a completed optimizer step.

**Construction, backend ownership and readback.** WS:630–645 clones both input RNG continuation and the factory result, and runs construction in model_init. MappingProxy-bearing ICM policy reconstruction at 620–628 remains intact. Existing real constructors and shared draw order are unchanged (RND:166–175; ICM:86–93; adaptive:59–68). The object-bearing NumPy repair at WS:244–247 still deep-copies plain and structured object arrays; test:688–710 checks live adaptive history ownership. Canonical `_owned` readbacks before strict `_same` checks at 708, 712 and 715 still prevent healthy OrderedDict/plain-dict false rejection. Strict leaf type/dtype/device/shape equality is retained. Mapping-key recursion does not change the scalar string/integer keys used by these real provider checkpoints and RNG envelopes.

**Prepared restore and commit.** WS:681–718 keeps validated saved continuation RNG separate from disposable construction/load streams. Validation is a required pure provider contract, checked for changes to the candidate checkpoint and transported payload before load. The backend is loaded and read back off-side, then cloned before transfer. Destination token, revision, quiescence and single-use checks precede reference replacement at 720–734. Candidate construction/load failure cannot publish a partial replacement. Test:403–458 retains cross-destination/single-use checks, independent restores, alias mutation controls and late-load failure; test:786–798 rejects prepared state after a real intervening owner update. This wrapper is not a sandbox for malicious Python callbacks, and successful readback is not mistaken for complete provider semantic validation.

**Causal isolation evidence.** Tests:261–334 retain exact global state/cache restoration, real learning with incomplete tails, consumed-stream replay, same-WorldId independent instances, spectator/world0 perturbation, full backend/RNG comparisons and an unwrapped constructor counterexample. Failure tests:337–386 use genuine post-update changes and quarantine only the affected owner. The random-consuming wrapper is explicitly identified at 163–180; it does not misrepresent current deterministic service as native stochastic service. The thread test checks serialization and release, not exclusion of arbitrary nonparticipating shared-policy threads.

No new confirmed P1/P2 emerged from this reassessment. No optional P3 finding is asserted. Refuted hypotheses include retained mapping-key aliases (now cloned), shallow structured object arrays (dtype.hasobject deepcopy), healthy OrderedDict false rejection (canonicalized readback), A→B→A replaying stale A state (frame restoration), and restored continuation consuming constructor draws (separate saved/work RNG).

## Root runtime evidence and limitations

Root completed the full counted PW02 regression for R5: **32 collected, 31 passed, 1 CUDA-conditional skip in 22.72s; 31.54s wall time; exit 0**. Read-only evidence inspected:

- `qualification/wave05-green-r5-quick/PW02.log`
- `qualification/wave05-green-r5-quick/PW02-result.json`

The result JSON binds HEAD and staged tree to the candidate above, with manifest SHA256 `93e9f3536f3bb1f282a84c7f5f0913973915cc2b32f4843c09804e8b9eb8e8f3`. These are explicitly **root-executed** results, not independent reviewer execution. Root's overall quick/static postflight was still pending when supplied; no repository-wide green is inferred. The CUDA skip is not hardware qualification.

Required OPEN work is unchanged: PW04 native complete backend semantic validation (especially adaptive configuration/history), actual target/predictor constructor hooks and local eligible-admission clocks; PW03 actual factory/bank integration and subsequent bank/runtime ownership/routing/quiescence; T24/T25 native admission/loader qualification. Inactive-world routing, shared-Q/C09 controls, full simulator-state inventory, whole-bank atomic restore, shared/private conversion and old-artifact acceptance remain their mandatory later gates. X02 and broad strict B remain OPEN. Shared behavior/defaults and existing alternatives are preserved.

Finite evidence limitations remain explicit: current malformed-state tests emphasize envelope rejection more than every inner RNG canonicality branch; entry-install/private-capture failures and combined primary-plus-cleanup failures have less direct test coverage than healthy continuation and restoration poisoning. Static cleanup paths were reviewed; these are not asserted as reproduced defects or silently converted into global qualification.

## Final stationarity receipt

Before/after HEAD and staged tree equal the R5 manifest values above. All five source hashes match that manifest before and after. Index bytes remain SHA256 `48349cd6a726ae8ec6717f1b5952f34d6f63e82e050429d0e68098850c310706`. Unstaged tracked diff is empty; the same 13 staged paths remain unchanged. `git check-ignore` confirms this report is ignored. Inventory remains five complete sources / 2799 lines. This R5 report is complete and stationary.
