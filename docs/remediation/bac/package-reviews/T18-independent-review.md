# T18 wave02 identity refresh — scoped GREEN

T18-R1 and T18-R2 remain addressed. No new scoped finding. The specification/code-quality assessment and 117-test evidence are recorded in [the r1 review](task-T18-r1-review.md); all four T18 source hashes are byte-identical to that reviewed repair. This refresh additionally exercises the actual native runner against the new joint dependency candidate.

Exact candidate: `/tmp/bac-verify-wave02-3d1d21cff5`, base HEAD `050a1a70e979aa03724219b81e848093820f044f`, selected tree `3d1d21cff5abdf60b630f97da0cdb09bf8ccd036`. The probe asserts the actual `townlet.__file__` inside that snapshot and compares **all** index-entry metadata with that exact tree using read-only `ls-files --stage` / `ls-tree -r`. HEAD alone is the base. Complete tree/import/four-source identity checks passed before and after execution.

| Scoped source | SHA256 verified before/after |
|---|---|
| `src/townlet/exploration/rnd.py` | `3a774dfb042cdbf20b66555c41f75c2d537b6ff49472395877dfcf5595e26e72` |
| `src/townlet/population/vectorized.py` | `38d8c969a8acfc5f49a3c5c7e532f6f10b34844af12ca37e8696123511e47d3b` |
| `src/townlet/config/bac_options.py` | `1de08a7cc36c49772254d8b9dc2d8adf3cac76533eecba5c36568745bc48c8f1` |
| `tests/test_townlet/regressions/bac/test_rnd_service.py` | `ecd2db6e72de5fba9453a6fff217d68113f6ff138c3c7a6cc9b5548e9e340c74` |

The existing 265-line independent probe was updated only to select the new snapshot/tree; its fixed-refusal assertions and positive controls are unchanged. Executed command, exit 0:

```bash
PYTHONPATH=/tmp/bac-verify-wave02-3d1d21cff5/src CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /workspace/hamlet/.venv/bin/python -u /workspace/hamlet/.superpowers/sdd/2026-11-01-bac-remediation-upgrades/task-T18-review-probe.py
```

Actual output: `/tmp/bac-t18-wave02-review-probe.log`. Native evidence on this exact joint candidate:

- Full authored pack runs through the real runner and saves a checkpoint with admitted=12, consumed=10, two optimizer updates, saved optimizer offset=0, and two pending rows.
- Ordinary runner checkpoint load restores the exact saved RND state; the same next three nonconstant observations yield an identical complete RND checkpoint.
- Missing/empty/reset/unequal Adam history retains the captured service metadata and also changes candidate Q tensors/counters. Public population validate and load refuse every variant before installation; the complete live population checkpoint stays unchanged. CPU capturable corruption also refuses.
- Standalone refusal, manual 1/5-step clocks, signed historical-import offsets, supported optimizer flags/tensor learning rate, no validation/load RNG draws, and 144 FIFO mode/policy calls all pass again.

Scope remains four project files/3180 charged lines plus the same 265-line probe, five sources/3445 lines. No AE/AS/ENV/RP or sixth implementation/helper/test source was inspected; changed dependencies were executed only through existing APIs. No source/index mutation, delegation or broad pytest rerun. The unchanged 117-case r1 run was not repeated for this identity refresh. Coordinator-owned full-wave integration/static/full gates remain required before release. This is not strict per-world ownership, production bounded-service wiring, G03/G04, whole-BAC or repository-green acceptance.
