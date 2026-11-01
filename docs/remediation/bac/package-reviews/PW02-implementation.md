# PW02: Private RNG and backend ownership primitives

Source change `eb73173496a7955b30a6fea4b65ccae8cc615b87`; qualified common source release `eb73173496a7955b30a6fea4b65ccae8cc615b87`, tree `1a1ca88cab7cc5bfe97e0922534d23e733d17e2d`.

WorldRNGState and OwnedWorldBackend add owned component RNG streams, exact continuation, guarded nested activation, global cleanup, quarantine/poison custody and prepared replacement. Snapshots/results own object-bearing arrays and both mapping keys and values, including native Adam Parameter keys. Healthy checkpoint readback uses consistent mapping representation without weakening strict leaf comparisons. Real existing providers and shared alternatives/defaults are preserved.

## Verification

31 primitive cases passed, one CUDA-conditional case skipped; 138 provider/RNG consumers passed. Tests perform genuine optimizer updates, mutate exported native/tuple Adam keys and moments, check unchanged live state/RNG/revision, and execute exact continued updates.

The common four-worker repository gate passed **6213 tests, 16 skipped, 15 warnings** (1975.74s test time; 1982.01s wall). All six standing guards passed. Postflight verified 53 source hashes, three final Astra review hashes, five process identities, 573 config files, seven protected native/manifest artifacts and the unchanged 14-worktree registry. Only final source release `eb73173496a7955b30a6fea4b65ccae8cc615b87` has the exact tested sum tree; intermediate logical heads were not separately full-qualified.

Fresh Astra source/spec review found no unresolved P1/P2 within this bounded package. [The review](PW02-independent-review.md) and [wave05 evidence](../evidence/wave05-qualification.json) record exact source/evidence, causal failures, repairs and commands. The initial full attempt failed in qualification startup from concurrent Git index metadata writes; a bounded metadata lock and four-worker startup proof preceded the passing full replacement. Failed attempts remain retained.

## Required remaining work

PW04 real target/predictor construction hooks, complete backend semantic validators and local clocks; PW03 and later actual bank/runtime integration; T24/T25 native admission; X02 strict-B closure remain REQUIRED OPEN. A participating RNG lock does not exclude unrelated global users. No GPU or cross-device qualification is claimed.

This package release does not close whole-BAC acceptance. Final common-source design/implementation reviews, learning/E2E cohort, coverage, slow/applicable-hardware and exact-tip CI remain required. The source-verified receipt draft SHA256 is `b7493c4b2a253dfd3287b8e42c704e6567bcada2573dadc8a7ed251283a6f77b`; this final rendering adds the verified release result and portable references.
