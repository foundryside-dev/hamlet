# PW04 RNG/NumPy source-verified document review

Disposition: the appended section `Native runner continuation at R174` (lines 251–259) is consistent with the five previously reviewed source bodies. No P1/P2 documentation correction is required within this section. This is a bounded document review, not terminal package qualification or independent runtime execution.

Reviewed postimage: `evidence-management/wip28-preparation/CURRENT-RNG-CUSTODY-CORE-CONTRACT-postimage-v1.md`, relative to `.superpowers/sdd/2026-11-01-bac-remediation-upgrades`.

Exact whole-document SHA-256: `416b35935c60d7be293eb4f0600293a2cfc0e12dd90e7e6ac89333570a956e6f`. Only the appended section identified above was substantively reviewed in this follow-up; the whole-document hash binds its containing artifact and does not extend review to the preexisting contract.

Reviewer: `/root/pw04_rng_numpy_astra_review`, independent of implementation and document production. The earlier source review `pw04-rng-numpy-independent-review.md` remains unchanged, SHA-256 `c489e726e8912dd673b0af02d397461959a6d299c9a4b207ab80196f69ee56b6`.

## Source identity and verification

Rehashed all five allowed source files. Their hashes match the original review exactly; no further source body was opened. The original charged source scope remains five bodies / 2,140 lines.

| Source | Lines | SHA-256 |
| --- | ---: | --- |
| src/townlet/training/native_rng.py | 244 | a17473a165b7022f554fca602a78762d54b4a98be52445a8a65160cf1802849d |
| src/townlet/config/world_roster.py | 329 | 0b219598f477a93c7faba4d7ab33144d26160fc1eb0cfbcca35a34ea20b54fcc |
| src/townlet/demo/runner.py | 1356 | 4f05e0eec706c4b64efc0b7adc3ebd7117446f0d17e419648a1ed812e1158018 |
| tests/test_townlet/regressions/bac/test_native_python_rng.py | 103 | aa2a53f25e35d3c5a22addc7fbc300454047f66538168ac543d5ee9704370651 |
| tests/test_townlet/regressions/bac/test_native_numpy_boundary.py | 108 | 1cb2bb4d392d27eef80fb697e1e467e50ea4c5ecf5a7c60e58cdb012dc67ca94 |

The strict v2 field inventory, exact inert Python state checks, detached validation and no-v1-fallback statements agree with native_rng.py. The phrase restoring state “last” correctly describes ordering after model/replay/curriculum/layout/persistent-state installation; population final bookkeeping still follows the RNG install. The source validates actual POP-plan/finalizer authority, consumes the prepared state, restores Python then Torch, and commits ambient custody only after setters succeed. Setter exceptions enter the poison path rather than rollback. This is source support for the stated fail-stop contract, not proof that a fault-injection test executed.

The ndarray description agrees with world_roster.py: exact plain ndarray; boolean/signed/unsigned integer/floating/complex dtype kinds; no object, structured, other nonnumeric or metadata-bearing dtype; copied storage at receipt ownership and public reads; exact dtype/shape and value comparison. Equality does not become bytewise comparison: signed zero is equal and NaNs are unequal, as already recorded in the source review. Exact-type checks reject subclass behavior before copying or NumPy equality.

No process-global NumPy state was added to the outer RNG payload. Private prioritized replay state and uniform recurrent replay's Python-random dependency remain parent-supplied source facts from the original diagnosis; those replay implementations were outside this review's source budget.

## Runtime provenance and remaining limits

Root reports R173 production runner continuation passed all four profiles, with 82 controls passed excluding two intentional NR2 RED controls, and exact custody. Root also reports R174's broader PW04/RND/native-owner selection passed 540 tests in 146.64 pytest seconds / 151.92 job seconds, with five-process custody passing. These are root-reported qualification facts; this reviewer did not execute tests or independently inspect their logs, candidate manifests, owner/Parameter-identity assertions or authoritative WIP28 packet. The appended paragraph appropriately routes that execution evidence to WIP28 rather than asserting that this source review independently establishes it. Counts are not added or treated as disjoint coverage.

The earlier P3 remains: the new Python regression file does not directly exercise authorized live installation and setter-failure quarantine, including a later Torch setter failure after Python has changed. Passing normal continuation does not itself close this fault-injection evidence gap. No new implementation defect is inferred from that gap.

CUDA remains unqualified by this review and by any CPU results described here. Final repository coverage, hardware, CI/remote identity and package closure remain separate obligations. This review authorizes no claim of global acceptance. No runtime, import, Git operation, source edit, source copy, branch or worktree was performed; only this new review record was written. Historical review/prose records remain unchanged.
