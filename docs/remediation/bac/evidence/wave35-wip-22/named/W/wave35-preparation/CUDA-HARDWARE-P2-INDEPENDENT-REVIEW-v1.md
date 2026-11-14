# P2 independent frozen-source review v1

Disposition: **CHANGES REQUIRED**. Two finite implementation defects reproduced through `run(spec_path)` with inert subprocesses and synthetic source/capacity observations. No APP, Torch, CUDA, server, Git writes, branches, worktrees, installs, or execution copies. Reviewer did not edit implementation sources. P3 actual end-to-end integration and hardware qualification remain separately UNRUN.

Frozen runner SHA256 `c0ec80b6b632618e1c1b9cb373efcb61e3b3ccb9d3677be7a1129cf58ab60a5a`; author tests `398dee45706bd1e85b3b15d8908103f484ccaceb637bbe6c7508bd87ece6b397`; P0 `adc8efeba368998e2e875a60c54ed3338a5ad2aa7daa710b7609e9ed2119de3c`. Freeze SHA256 `480cf1de39248500a4be64b132f9f1076fcc205a58604bb86d4ed6219537348c`; P2 interface `35e0547eac55727dc9063023f8e987cf86451c55e7197d6d7f12b5e16ee56a2c`.

Evidence directory: `../evidence-management/hardware-runner-p2/independent-review/`. Exact inert source snapshots and before manifest precede all executions. `test_independent_p2.py.before-v1.txt` preserves the reviewer probe; `red-v2.json` records actual PID, argv, UTC start/end and exit1; `red-v2.log` contains both REDs. The initial `red-v1` attempt exited1 because default Python lacked pytest; it executed no tests and was retained. Existing installed repository Python was used subsequently, without installation.

## F1 — Full reservation charged again against remaining free capacity

`run_bac_hardware_v1.py:875-878`, called before each launch and again at final seal (`431`), compares current free RAM/scratch against the original entire admitted budget plus reserve/overhead. The budget was computed from the same initial free capacity. Legitimate consumption by this attempt therefore appears as an external capacity loss. In a headroom-limited admission, scratch directories alone can consume the required inode headroom before first launch. After a job retains scratch within its budget, the final witness can fail despite a successful job result, leaving the attempt unsealed. Concurrent launches likewise risk counting active job RAM twice.

The probe supplies initial capacity equal to the admitted reservation, then reduces final free scratch by one byte (within the job's two-byte scratch reservation). The real inert job completes with exit0 and valid synthetic transport, but final `source()` raises `current capacity below sealed reservation: scratch_bytes` instead of sealing. This is a deterministic accounting model probe, not an assertion of real filesystem byte measurements.

Required fix: distinguish remaining unconsumed reservations from usage already charged to this allocation/attempt, including retained scratch across jobs/attempts and active RAM. Retain fail-closed checks for genuinely unreserved external loss and CPU capacity reduction. Add boundary tests at admission-limited capacity, before launch directory consumption, concurrent active allocations, and final retained scratch. Do not merely disable live-capacity checks or add an arbitrary cushion.

## F2 — Raw initialized CUDA fact can become uninitialized success

`run_bac_hardware_v1.py:1019-1022` requires a boolean raw CUDA marker for loaded non-work observers but does not cross-bind its value to `cuda_observation`. The no-initialize check examines only the latter string. A raw record with `torch_loaded=true,cuda_marker=true` and process `torch_observation=loaded-without-calls,cuda_observation=uninitialized` is therefore accepted for a no-initialize role. The probe's public `run()` returns0 and writes `successful` despite this direct contradiction. All records are synthetic; no backend is loaded or called.

Required fix: reconcile raw CUDA marker, process observation, and exact role policy before success. Preserve truthful absent/uninitialized observations and avoid performing runtime backend calls in the runner. Add negative cases for initialized raw markers paired with uninitialized observations and any related forbidden policy combinations.

## Reviewed boundaries and remaining gates

Inspection covered runner control flow, exact admitted capture terminal gate, pool/allocation/device/domain/host leases, descriptor inheritance, owned-group termination, observed launch/wait identities, admission arithmetic, static/delegated identity context, environments, and evidence promotion. Public entry delegates root authority out of band; hashes are not treated as authorship. Source/body scope is four files including reviewer probe (runner1161, author tests880, P0 520, probe31; total2592 lines), within five-file/5000-line cap. Historical runner body was not opened.

Do not adopt this freeze on the basis of the existing suite. Fixed bytes must be frozen and reviewed against both defects; P3 real producer integration remains a separate prerequisite.

Independent existing-suite rerun: **66 passed in 10.11s**, actual exit0. Exact argv/PID/UTC/source-after hashes: `independent-review/baseline-v1.json`; log `baseline-v1.log`. Runner, author tests and protocol hashes matched frozen bytes after the run. These passes do not resolve the two independent REDs.
