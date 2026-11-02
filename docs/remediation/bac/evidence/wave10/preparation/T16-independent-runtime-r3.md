# T16 independent runtime r3

**PASS: three selected cases, 32.19 seconds pytest time; 36.62794756889343 seconds harness wall time, exit0.** This is an independently executed focused runtime following root's explicit R3 clearance. It is not all12 owned cases, an affected-owner gate or full-suite qualification.

Candidate tree `0bdd6133f2224b25bce5668e15021fa1353accba`; base `f575ecefda7844fbd5b7b6138ad0c6bf7b1bafd8`. Manifest SHA256 `83c9b20654d85f90f732d9f5e4a7de2aed8bd25fec48f8cc141d03b0b292c5c8`; harness SHA256 reported `180558c22da088a57326aa9251fbb64761e2788f18cb982532525b84b571f791`.

Exact authorized launch from `/workspace/hamlet`:

```sh
env TMPDIR=/workspace/bac-review-2026-11-01/qualification/scratch/tmp-wave08-r3 python /workspace/bac-review-2026-11-01/qualification/run_bac_packet_checks_locked.py /workspace/bac-review-2026-11-01/qualification/wave10-r3-independent-spec.json
```

The supplied spec executes `/workspace/hamlet/.venv/bin/python -m pytest` with these exact nodes:

- `tests/test_townlet/regressions/bac/test_runner_readiness.py::test_real_runner_owned_sampling_identity[successive_without_replacement]`
- `tests/test_townlet/regressions/bac/test_runner_readiness.py::test_real_runner_recurrent_per[independent_with_replacement]`
- `tests/test_townlet/regressions/bac/test_runner_readiness.py::test_real_runner_window_diagnostic[fixed_full]`

Flags: `-q --no-cov -p no:cacheprovider -p bac_source_identity -n 2 --dist worksteal --basetemp=/workspace/bac-review-2026-11-01/qualification/scratch/wave10-r3-independent`. The harness launches one job with two pytest workers. No additional runtime selection or helper was introduced.

Actual log: `/workspace/bac-review-2026-11-01/qualification/wave10-r3-independent/independent.log`, independently computed SHA256 `2d5f3a18369c65a0912ea639cf627090ff8ae737232abe7a42b4ff4bbcd35ee0`. Native result: sibling `independent-result.json`. The log ends `3 passed in 32.19s`.

## Process and source custody

I read all three emitted identity receipts: `independent/identity-controller.json`, `identity-gw0.json`, `identity-gw1.json`. Each records the exact base and candidate above, module `/workspace/hamlet/src/townlet/__init__.py`, Torch `2.11.0+cu130`, threads1, and its distinct controller/gw0/gw1 identity. Reading these receipts does not entail opening the module's implementation.

Independent SHA256 before and after runtime matched each other and the R3 manifest:

| Complete source | Lines | SHA256 |
|---|---:|---|
| `src/townlet/demo/runner.py` |1017|`e1c4b6c00923416f6fdf9e70976ea57a4a706e38a2ea228b4b10273906d6aacf`|
| `src/townlet/population/vectorized.py` |2146|`9569eab3d766ed5467ecf78736cd170c7aa0d0b77d90efe28239f3bab64ff12a`|
| `src/townlet/config/brain_config.py` |568|`6c041ed40de507dfed81dc4b3a58cbb728d446228f6fd831ee115348aa559079`|
| `src/townlet/agent/optimizer_factory.py` |162|`56af1a9c8edb70a25b43a6e10aa3080d9a7b8becff112924e21a9429d994717d`|
| `tests/test_townlet/regressions/bac/test_runner_readiness.py` |529|`2352066710ef7d97de02efb498021f26f7ffc50e2ce2afe96ea6ba4bbee04ce4`|

Scope remains exactly5 complete sources/4422 physical lines. All production bytes match R2. The narrow static R3 disposition is appended to the preserved `T16-independent-review-r2.md`: the corrected fixed-full assertion expects one message per actual retained0/retained1 signature and retains duplicate rejection. The earlier static review missed the original overstrict one-message assertion; R2's actual11PASS/1FAIL remains preserved rather than relabeled.

## What this execution proves

Both genuine causal controls now pass after actual sampling, finite Q optimization and changed weights: flat successive PER owns its authored PCG64 stream, and selected recurrent replacement PER is configured as captured7 before rollout and really learns. The fixed-full control now passes with retained1/sampleable0, zero Q sampling/optimization/scheduler/target progress, unchanged state and exactly the two truthful nonrepeated diagnostic signatures. All three traverse normal runner checkpoint publication with the class-level scheduler observer.

This selection does not execute warmup1000, the other PER-law combinations, the four-family cadence/gamma0 matrix or adaptive-prefix diagnostic counterpart. Root owns common-source all12/affected-owner/G2 evidence. It does not establish current native resume/atomicity, complete PER mathematics, private-world curiosity isolation or provider precedence. Those limits and owners in the static review remain unchanged.

Curiosity scope remains existing shared AdaptiveIntrinsic/RND construction from selected training, one population module and N1 fixtures. Warmup uses retained eligible transitions; beta uses vector ticks; LR/target use successful Q updates. RND service remains independent of Q warmup. History A, strict per-world B and shared alternative are preserved without a new qualification claim.

Full suite: **NOT RUN by this reviewer**. Next mandatory full gate G2; root retains earlier-full-trigger assessment, six guards, affected-owner selection, final all54 requirements/22 lenses and publication/CI custody. Reported25/66 qualified status is not advanced by this receipt alone.

Only the cleared harness runtime and static reads/hash checks were performed. Human-authored writes are the authorized static addendum and this ignored receipt; the harness owns its native output/scratch files. No source/test/tracked-doc/index edit, sixth implementation/helper read, new probe, branch/worktree/checkout/source-copy/deletion, subdelegation, commit or push occurred. Existing14 checkouts were not mutated. All selected runtime processes have completed; return stationary.
