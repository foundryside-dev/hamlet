# Task4 final-byte preparation packet

Status: tests and narrow wrapper support implemented; static AST parsing only. Collection, inert regressions, actual capture, actual P3/Git cases and independent runtime review are all UNRUN. Production runner and P0 bytes are unchanged. No actual source/index lease has been taken.

## Implemented scope and exact files

The existing test body now defines test_owner_actual_git_backstop with exactly controller-exit and job-timeout values. Without the root execution-lease file and its SHA256 the outer branch refuses. The nested real pytest controller enters only through its separately sealed driver-mode job environment and actual P3 plugin context; no _CALL injection, duplicate START or fake source/Git. The existing wrapper's four-CPU mode accepts only the two exact node arguments below, requires the root lease, assigns its exact CPU IDs, applies2GiB per-process AS limits, and puts runtime output outside the source checkout. Two/three-CPU modes retain4GiB limits.

The root lease supplies two per-case source-freeze references. Exact CPU-bound argv/environment/case inputs differ between cases, and P2 requires accepted bounds to equal the bounds used by a spec: each one-job spec therefore has its own two-bound source grant/freezing envelope while both remain under the same actual R144 no-writer barrier. No unused other-case bound is hidden in a grant.

Current unchanged runner: 0d2a163305efb4683b8d90f42364d894a1af962129b9df15137ccd466374cc97,1603lines. P0:e4f31eacb0e4499655a19ec91a4f5618a7b2ad3f4090e7ed068816b311e00860,526lines. Final test/wrapper hashes and inert snapshots are in task4-preparation-freeze-v1.json. Total four bodies4431lines; no extra implementation body opened. The tests record real group signals, leader wait, live-Git checks at lease close, supervisor reap and lease probes. Emergency cleanup is retained failure evidence and cannot make a run pass. No production cleanup correction has been made without actual RED.

## Fixed paths

R=/workspace/hamlet; Q=/workspace/bac-review-2026-11-01/qualification.
E=R/.superpowers/sdd/2026-11-01-bac-remediation-upgrades/evidence-management/hardware-runner-p2/owner-integration.
T=/workspace/bac-review-2026-11-01/task4-backstop-v1 (external data/output directory, not a repository, checkout or execution copy).

For each MODE in controller-exit,job-timeout use:

- T/inputs/MODE/identity-policy.json, sampler-policy.json, controller-bound.json, guard-bound.json, allocation.json, source-grant.json, source-freeze.json, candidate.json, request.json.
- T/inputs/MODE/ contracts and witness/validator references for process-custody, source-freeze, required-cases and fork-three-trials. They authorize a negative test workload; incomplete obligations must never be claimed satisfied.
- T/inputs/common/environment.json, tools.json, root-registry.txt and availability.json; actual dependency/source inventory references, not copied code.
- T/capture/MODE/{start,source-before,discovery-command,discovery,source-after,admission,spec,result}.json are actual P1 outputs. Destination must not already exist and must be outside R/output/scratch.
- T/output/task4-MODE-v1/backstop and T/scratch/task4-MODE-v1/backstop are job paths, initially absent. Their common roots are T/output and T/scratch. Request attempt_id is task4-MODE-v1 under current P0; do not use the older proposal's obsolete statement that request lacks attempt_id.
- Root supplies the one canonical host-wide lease_root; do not invent a private namespace to avoid contention.
- T/execution-lease.json is root-written only after both genuine admitted capture terminals and final pins exist. T/runs must exist; the wrapper exclusively creates T/runs/task4-actual01 and its fixtures/log/record files. E holds preparation metadata only.

## Inputs and measured P1 admission

Root supplied the R144 preparation baseline (refresh after WIP24/any later source or HEAD change before actual capture): tree ed561dc04fcffba4f6617f343862d54db6a8dad0, reported HEAD prefixa42d6192, source824/config573/artifacts13. Root supplies the full current HEAD and exact inventories from the actual existing checkout. No Git query occurred during this preparation. Registry text is actual git worktree list --porcelain stdout and availability derives from those exact paths/current existence; no new worktree/branch/checkout is created. Preserve the14 registered/1 available state.

Freeze the actual tool/interpreter/Git and test sources. The environment's Git dependency must refer to the actual executable, not pretend it is a Python distribution. Current read-only discovery resolved Git /usr/local/bin/git, SHA9dae295c1a4ffae4ee772e6205fcf22b26e1bfeeb5ee98f278b5139bda7ca22f; root rehashes before sealing. Tools use the six current P0 names protocol,capture,runner,identity,verifier,children-verifier. Root must pin the newly repaired/adopted P1 before invocation; P4/P5 references do not imply they validate this intentionally incomplete attempt.

The in-checkout .venv interpreter symlink resolves to /usr/bin/python3.13. Pytest is under R/.venv/lib/python3.13/site-packages. P3 authenticates every loaded source-root module, so root must retain a genuinely observed pytest/tool import closure and authorize its exact files/import roots as a runtime-input supplement to the unchanged R144 APP bytes, or supply an already-existing appropriate external environment. Do not copy an environment or fabricate module observations. A nested non-isolated job may declare PYTHONPATH=Q:R/.venv/lib/python3.13/site-packages, but isolated P1 discovery ignores PYTHONPATH; declared discovery dependencies must match its actual environment. No unobserved venv package origin/version can be substituted.

Build acyclic metadata in order: actual fixed input/dependency/executable refs and allocation authority; sampler policy; identity policy with future spec/command/runtime path strings; exact job argv/env/case/resource configuration; controller/guard CPU bounds with actual ordered input refs and justification; source grant with exactly those bounds; source-freeze; candidate; case contracts/jobs; admission request. Candidate has no request/spec back-reference. Identity policy must not be added to candidate inputs (cycle); CPU bounds can pin test/recipe refs in justification. Keep grant.inputs and bound.inputs identically ordered. Both source-freezes share root's maintained no-writer/index barrier but bind their own exact job authority.

Use actual P1 capture, never sealed_fixture/stub_source or fabricated discovery JSON. Supplier confirms its supported API is capture(candidate:Path,admission_request:Path,destination:Path)->dict; no top-level capture CLI exists. The exact argv bootstrap is:

```python
[
  '/usr/bin/python3.13', '-I', '-B', '-c',
  'import json,sys; from pathlib import Path; sys.path.insert(0,"/workspace/bac-review-2026-11-01/qualification"); from capture_bac_hardware_v1 import capture; print(json.dumps(capture(Path(sys.argv[1]),Path(sys.argv[2]),Path(sys.argv[3])),sort_keys=True))',
  '/workspace/bac-review-2026-11-01/task4-backstop-v1/inputs/MODE/candidate.json',
  '/workspace/bac-review-2026-11-01/task4-backstop-v1/inputs/MODE/request.json',
  '/workspace/bac-review-2026-11-01/task4-backstop-v1/capture/MODE'
]
```

MODE is substituted once per serial case. The interpreter ref and source pin must match this real interpreter. Set actual root-approved4CPU affinity, thread variables1, empty CUDA_VISIBLE_DEVICES, PYTHONDONTWRITEBYTECODE=1 and an explicit external TMPDIR; record actual argv/PID/UTC/affinity/limits and complete logs. Isolated bootstrap imports the existing pinned Q module; it does not create an execution copy. Retain capture exceptions/refusals. A zero bootstrap exit is not admission: require closed terminal result.json disposition admitted, empty reasons and exact spec/admission refs. The capture itself produces and retains actual raw discovery/process/source observations.

Current P1 blockers found by its supplier are the historical P0 hard pin adc8 versus currente4f31 and treating git as a Python distribution. Root is arranging bounded supplier repair/adoption. Do not run the above with stale P1, hand-edit measured outputs, disable its checks, or claim capture complete. The exact P1 supplier capsule is still pending at this checkpoint; its direct API/blocker confirmation and historical adopted interface are recorded in the preparation freeze. Do not infer an executable repaired P1 from this packet.

For each request: profile cpu, requested_job_concurrency1, authorized_devices[], requested_visibility empty, devices[], xdist_workers0. Exact job CPU3 comprises controller peak1 plus guard peak2 (guard and actual Git). Proposed allocation capacityCPU4/RAM8GiB/scratch192MiB/inodes5120; overheadCPU1/RAM2GiB/scratch64MiB/inodes1024; minimum/jobCPU3/RAM6GiB/scratch128MiB/inodes4096; reserve allzero only if root explicitly accepts it. Genuine P1 available capacity may refuse these values and must be retained as refusal. Policy CPU2 and scratch/input caps are explicit root-accepted bounds, never derived merely from inter_op. Guard inter_op5 remains a declared role configuration, not an observed Torch work fact. Original10/8/6/3 sampler policy stays fixed.

## Exact nested controller argv

For MODE and the source-hashed identity policy, seal this argv (actual interpreter path remains /usr/bin/python3.13):

```text
/usr/bin/python3.13 -B -m pytest -q -p no:cacheprovider -p bac_hardware_identity_v1 --rootdir=/workspace/bac-review-2026-11-01/qualification --confcutdir=/workspace/bac-review-2026-11-01/qualification /workspace/bac-review-2026-11-01/qualification/test_run_bac_hardware_v1.py::test_owner_actual_git_backstop[MODE] --bac-identity-policy /workspace/bac-review-2026-11-01/task4-backstop-v1/inputs/MODE/identity-policy.json --bac-identity-policy-sha256 POLICY_SHA256
```

PYTEST_DISABLE_PLUGIN_AUTOLOAD=1, thread env1, empty CUDA visibility, explicit PYTHONPATH/TMPDIR and BAC_P2_TASK4_DRIVER=MODE must be sealed. No root execution-lease digest is put into that job environment: it would create a spec-to-lease reference cycle. Actual P3 root context and job authority gate this branch. Identity-policy spec_path points at T/capture/MODE/spec.json; command_path/runtime_path point at the exact job output. Actual P3 plugin emits parent START and establishes the actual test-call binding. Required collection/case ID is test_run_bac_hardware_v1.py::test_owner_actual_git_backstop[MODE]. Confirm it with the retained collection command before sealing.

## Root execution-lease shape

The closed JSON has exactly schema,authority,start,end,recipe,source_freezes,pins,cpu_ids,ram_limit_bytes,execution_root,cases. schema is bac-p2-task4-execution-lease-v1; authority root. UTC start/end are explicit offset timestamps; each case requires at least35s remaining. recipe is the exact already accepted c8fd6245...999d reference. source_freezes is the two per-case P0 references. pins contains current runner,test,P0,P3,wrapper,interpreter,Git plus any required input pins; actual P3 must remain adopted dee985...b07. cpu_ids is four actual allowed integers; ram_limit_bytes2147483648; execution_root is T. cases maps each MODE to exactly {spec: genuine_P1_spec_reference}. Missing/changed refs refuse.

The genuine captures have120s discovery/5s cleanup bounds each; two30s case watchdogs also apply. If capture and tests share one uninterrupted source barrier, reserve up to six minutes and release immediately when finished or refused. The earlier recipe's approximately two minutes was an estimate, not authority to overrun a lease. This does not extend any guard deadline. No APP/P5 runtime or source/index writer may overlap the four-CPU actual window.

## Commands prepared but UNRUN

Collection (two-CPU resource grant required; executes tooling imports only, no actual test body):

```text
BAC_P2_TEST_CPU_SLOTS=2 BAC_P2_TEST_RAM_BYTES=4294967296 /workspace/hamlet/.venv/bin/python -B E/run-inert-v1.py task4-collection01 --collect-only
```

Pure regression selection:

```text
BAC_P2_TEST_CPU_SLOTS=2 BAC_P2_TEST_RAM_BYTES=4294967296 /workspace/hamlet/.venv/bin/python -B E/run-inert-v1.py task4-inert01 -k 'not owner_public_run_observes and not owner_actual_git_backstop'
```

Actual two-case run, only after genuine capture, exact-byte review and explicit root source/resource lease:

```text
BAC_P2_TEST_CPU_SLOTS=4 BAC_P2_TEST_RAM_BYTES=2147483648 BAC_P2_TASK4_LEASE=T/execution-lease.json BAC_P2_TASK4_LEASE_SHA256=ROOT_SEALED_SHA /workspace/hamlet/.venv/bin/python -B E/run-inert-v1.py task4-actual01 /workspace/bac-review-2026-11-01/qualification/test_run_bac_hardware_v1.py::test_owner_actual_git_backstop[controller-exit] /workspace/bac-review-2026-11-01/qualification/test_run_bac_hardware_v1.py::test_owner_actual_git_backstop[job-timeout]
```

E and T above are explicit path abbreviations defined at the top, not shell variables supplied by the test. Preserve actual argv expansion in the execution record. The separately reserved nine three-CPU ordinary admission/spawn regressions remain a later distinct selection. No hardware/server claim is made; the expected16-worker CUDA server is not available here.
