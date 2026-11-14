# CUDA runner tooling upgrade implementation plan

> **For agentic workers:** On separately authorized implementation, use `superpowers:executing-plans` task by task under root integration ownership. This document authorizes no implementation, agent dispatch, branch, worktree, checkout, source execution copy, server action or spending.

**Goal:** Qualify separately named hardware-runner tools against the current BAC evidence contract, then use measured server resources for exact-source CPU and CUDA attempts.

**Architecture:** Keep historical tool bytes and attempts immutable. New versioned capture, runner, process witness and verifier tools share an explicit protocol; strict child, fork, RNG and phase obligations remain mandatory. Resource admission precedes collection and fixture controls; actual CUDA evidence is a separate gate from synthetic tooling validation.

**Tech stack:** Python, pytest/xdist, Linux process/cgroup/resource observations, Git source identities, PyTorch/CUDA; exact versions are admitted facts, not assumed here.

**Spec:** `CUDA-RUNNER-TOOLING-READINESS.md` and `../evidence-management/HARDWARE-RUNNER-HANDOFF-v1.md` are accepted baselines. This is an implementation plan, not a new review of their resolved findings. Repository `AGENTS.md` applies.

## Authority and boundaries

- Root owns integration, candidate sealing, execution selection and any later implementation authorization. Current CPU qualifications continue with unchanged tools.
- Inspection covered only the five bodies below: 968 lines total. No application bodies, other helper bodies or test bodies were read. No tests or source tools were executed.
- Sixteen advertised workers is neither sixteen GPUs nor an admitted concurrency. Access, GPU count/topology and usable quotas remain unknown.
- No legacy application compatibility, fallback schema, migration adapter or dual-version dispatcher. New tools reject unknown/old protocol versions. Historical tools remain evidence objects for their historical attempts; do not rerun old manifests against later source.
- Preserve current one-thread intra-op custody and role-specific inter-op/debug/fork constraints. No throughput change may relax RNG ownership, fresh-process boundaries, poison currentness or strict child evidence.
- Implement only after a fresh bounded packet inventory is authorized. Every packet below has at most five implementation/test files and 5,000 total inspected/projected lines; count dependency bodies too. Existing external helpers are opaque pinned interfaces until explicitly resliced. Exceeding a cap requires reslicing, never unbounded follow-up reading.

## Inspected baseline and concrete deltas

All paths in this table are under `/workspace/bac-review-2026-11-01/qualification` (Q).

| File | Lines | SHA-256 |
|---|---:|---|
| run_bac_packet_checks_locked.py | 20 | 180558c22da088a57326aa9251fbb64761e2788f18cb982532525b84b571f791 |
| capture_wave14_round.py | 103 | f4c8a6db1df092c6ef37a552d989f4107feef7f92e94578f5cb60f0d78868d02 |
| bac_source_identity.py | 60 | 0a376a6454e317104adc4bce2cdc0d268c216de8c67e91e60623e6df7d31719d |
| verify_bac_run.py | 33 | b00f16ec8666f475805399e80e7f4c2e335f8c6170c18cb705c22f8d6725c91d |
| verify_bac_replay_spawn_identity.py | 752 | 6006c7247d79a99226a74756a2266a2966fce800f9f84af802f2990db4606173 |

Capture stages source, hardcodes the old branch/path/T21 selection, checks precisely four cgroup CPUs and 16 GiB, and emits a fixed scratch path and unmeasured CUDA label. Its replacement consumes a root-sealed candidate and measures admission without staging. Runner unconditionally hides CUDA, overwrites output, conflates job capacity with a single workers field, and does not propagate job failures. Generic identity witnesses only pytest startup and generic verifier trusts log counts, does not pin argv/harness, and can accept skipped hardware cases.

The strict replay verifier already pins exact argv, runner digest and typed schemas; correlates Process/queue/child PID and PPID; checks exact imports, intra-op=1, inter-op=5 and debug=True; checks three fork guard trials with zero effects and no Torch calls; checks producer quarantine/error identity and unchanged parent RNG; and verifies separately qualified phase pairs. Its receipt creation is exclusive. Preserve these strengths. Its CUDA-named core/producer controls explicitly prove CPU stand-ins, not hardware. Its logical device lists [0,1] and [0,1,2] describe those protocols, not the future server topology. Do not loosen those lists or rename their evidence as GPU qualification.

## Review focus and owning checks

1. Unlimited/nested cgroup limits or fractional CPU quota: measured effective capacity and explicit admission refusal when facts are insufficient (P1).
2. CUDA visibility remapping, MIG/shared physical devices and a CPU-only Torch build: no guessed physical identity or successful CUDA admission (P1/P2).
3. Worker replacement, PID reuse, absent child final witness and forbidden fork instrumentation: preserve process identity and fail closed without initializing Torch/CUDA in guard-only children (P3/P5).
4. Concurrent launch, termination mid-write and source changes restored before the final hash: no overwritten attempts or false immutable-source claim (P2/P3/P4).
5. Mocked CUDA, required tests skipped/xfail, duplicate collection IDs or swapped phase-pair artifacts: no hardware/contract acceptance from these records (P4/P5).

## New protocol interface decisions

These are proposed new interfaces, not claims about existing uninspected helpers. New files below are future Q-relative names. Use a single `bac-hardware-v1` family with closed versioned record schemas; immutable protocol metadata defines exact fields and allowed role inventory before implementation. The protocol module raises `ValueError` on unknown fields, wrong exact types (including bool-as-int), nonfinite measurements, unsafe paths, duplicate IDs or missing mandatory records.

- `bac_hardware_protocol_v1.py`: `validate_spec(spec: dict) -> None`, `validate_record(kind: str, value: dict) -> None`, `file_reference(path: Path) -> dict`. References contain resolved path, byte length and SHA-256. No application imports. All consumers pin its digest.
- `capture_bac_hardware_v1.py`: `capture(candidate: Path, admission_request: Path, destination: Path) -> dict`. Inputs include authorized root/interpreter/scratch, CPU versus CUDA profile, requested concurrency and resource budgets. Output binds candidate, protocol/tool/dependency inventory, measured admission and a normalized spec, exclusively created. It never stages or changes source/index.
- `run_bac_hardware_v1.py`: `run(spec_path: Path) -> int`. Commands are argument arrays with exact interpreter, cwd, selection, environment contract and seed policy. Exit zero requires all planned jobs completed successfully; failed/interrupted/refused attempts remain separately recorded.
- `bac_hardware_identity_v1.py`: `record_process(context: dict, phase: str) -> dict` plus pytest hooks. Phase is start/end; role comes from a sealed allowed inventory. Returned references bind actual process identity and observations, not parent-fabricated child facts.
- `verify_bac_hardware_v1.py`: `verify(spec_path: Path, job_id: str, destination: Path) -> dict`. No application imports. Recompute exact bindings and classify custody, test outcome and hardware obligation disposition independently. Receipt creation is exclusive.
- `verify_bac_hardware_children_v1.py`: `verify_children(spec_path: Path, job_id: str, destination: Path) -> dict`. Implements the explicitly resliced current child protocol plus new outer binding; never sends new-schema records through an old verifier or relaxes old exact-field checks.

Required spec fields cover schema, attempt ID, candidate reference, tool inventory, dependency/environment reference, admission reference, explicit profile, output/scratch roots, job concurrency, CPU budget, and jobs. Each job has unique ID, argv, cwd, environment/seed contract, required collected IDs, xdist count, process/child role inventory, CPU/RAM/scratch budget, device UUID allocation, serialization domains and prerequisite receipts. Candidate identity includes HEAD/tree plus exact source/tests/configs/scripts/ratchet/artifact inventory and actual authorized root/import roots. Preserve applicable registry/availability checks.

CPU profile intentionally hides CUDA in its job environment and records that policy. CUDA profile requires a nonempty admitted device mapping; do not clear inherited visibility blindly or expand an allocation beyond supplied authorization. Record requested and effective visibility, logical index → GPU UUID/MIG instance → physical parent mapping. Unsupported or unverifiable mappings refuse that profile rather than infer isolation. Hardware inventory probes run in a separate admitted discovery process so they cannot initialize CUDA in a case that must start uninitialized.

Resource admission records quota/period and cgroup ancestry, cpuset and process affinity, effective CPU capacity, host/limited RAM/current usage, scratch free space/inodes and resolved TMPDIR, CPU/NUMA and GPU/interconnect topology where observable, driver/runtime/Torch build and GPU UUID/model/VRAM, visible devices, competing workloads, timestamps and probe errors. `max`, absent cgroup controllers and unsupported probes are explicit values with provenance; required unavailable facts block admission. No fixed four-CPU/16-GiB threshold. Root supplies workload-specific resource minima; admission compares them against measurements with explicit reserve.

Schedule CPU reservations across concurrent controllers, xdist workers and simultaneous children, preserving one-thread baseline; xdist slots and outer job count are separate fields. CPU capacity is bounded by affinity/cpuset/quota, not marketing count. Take per-physical-device leases (including shared MIG parent when isolation requires it), RNG-domain leases and a timing-experiment lease. Multi-device leases are acquired in stable order. Timing cases default to an exclusive host interval unless their accepted contract proves measured co-running work harmless. Independent CPU jobs may use remaining admitted capacity while unrelated GPU work runs; GPU serialization does not become blanket CPU serialization.

Every process gets attempt/job/role, PID/PPID, process start identity (to disambiguate PID reuse), host/boot identity, interpreter/argv/cwd, actual imports and hashes, source witness, effective thread/debug/environment/device mapping, and start/end timestamps with monotonic elapsed time. Worker replacements are explicit new identities; a missing start/end or unadmitted replacement cannot be accepted. Distinguish observer/uninitialized and work-executing roles: do not force CUDA initialization or RNG draws just to produce identity. Guard-only fork roles retain their no-Torch constraint and inherited-module witness; missing facts get exact reasons, never fabricated observations.

An attempt directory is created atomically and exclusively; reject path escape/symlink substitution, existing destinations and duplicate names before launch. Write immutable start record, distinct per-process records, exact command/log/results and a final sealed reference inventory. Keep partial/terminated attempts without overwriting or fabricating finish times. Use unique scratch paths. A second verification writes a new receipt destination. Hash-only sealing detects changes, but does not prevent a privileged writer: record retention permissions and root's authorized no-writer source freeze honestly.

Root grants a source-freeze interval covering capture through final witnesses, including tracked/untracked executable inputs. Cooperating metadata users share the existing index lock; that lock alone is not source isolation. Pre/post source hashes plus process import witnesses detect observed drift but cannot prove a transient edit restored between samples. Require root's no-writer barrier; if it cannot be established, do not claim exact-source qualification. No checkout/worktree copy is a workaround authorized here.

## Finite implementation packets (future authorization required)

Each row is a complete bounded review packet, including tests and any historical body read. Limits are projected total lines, not additions. Protocol consumers may use its sealed interface metadata; reading its body adds a counted file and must stay within the cap. Packet tests must not import/execute an application or call real hardware during synthetic validation.

| Packet | Counted files | Maximum total lines | Independently reviewable deliverable |
|---|---|---:|---|
| P0 | new `bac_hardware_protocol_v1.py`, new `test_bac_hardware_protocol_v1.py` | 1,400 / 2 files | Closed schema and immutable reference rules |
| P1 | old `capture_wave14_round.py`, new `capture_bac_hardware_v1.py`, new `test_capture_bac_hardware_v1.py`, protocol module | 2,800 / 4 files | Measured read-only admission |
| P2 | old `run_bac_packet_checks_locked.py`, new `run_bac_hardware_v1.py`, new `test_run_bac_hardware_v1.py`, protocol module | 3,600 / 4 files | Exclusive attempts and bounded scheduling |
| P3 | old `bac_source_identity.py`, new `bac_hardware_identity_v1.py`, new `test_bac_hardware_identity_v1.py`, protocol module | 3,200 / 4 files | Actual per-process start/end custody |
| P4 | old `verify_bac_run.py`, new `verify_bac_hardware_v1.py`, new `test_verify_bac_hardware_v1.py`, protocol module | 3,800 / 4 files | Independent structured outcome verification |
| P5 | old `verify_bac_replay_spawn_identity.py`, new `verify_bac_hardware_children_v1.py`, new `test_verify_bac_hardware_children_v1.py`, protocol module | 4,800 / 4 files | Strict child/fork/phase/producer contracts under new binding |

For every packet perform this cycle, preserving evidence: write the named failing cases below; run only that packet's test file and retain failure showing the missing capability; implement the minimal interface; rerun the same file and retain success; root reviews exact bytes/diff and pins dependencies before the next consumer is integrated. Example command template after authorization: `<admitted-python> -m pytest <Q>/<packet-test-file> --no-cov -p no:cacheprovider -q`. Final commands must resolve placeholders and record actual argv. No tests have been run for this plan. Integration/commits remain root-owned, not automatic skill steps.

### P0 acceptance

- [ ] `test_closed_schema`: old/unknown schema, extra field, bool integer, NaN, duplicate job ID and path escape all refuse; complete correctly typed synthetic spec passes.
- [ ] `test_reference_tamper`: changed bytes, symlink escape, byte-length mismatch and missing pinned dependency refuse.
- [ ] Seal metadata defining every schema field, role and obligation; downstream tools consume the same version and exact hash.

### P1 acceptance

- [ ] `test_admission_limits`: finite/fractional/unlimited/nested quotas, affinity restriction, memory `max`, missing controller, insufficient memory/scratch and unknown required fact yield explicit expected admission/refusal.
- [ ] `test_profile_mapping`: CPU profile differs from CUDA; nonempty remapped visibility is preserved within allocation; CPU-only Torch, duplicate/unknown GPU UUID and unsupported MIG mapping reject CUDA.
- [ ] `test_read_only_capture`: subprocess spy forbids git add/checkout and source writes; occupied destination refuses; measured TMPDIR differs from old constant; discovery probe is separate from future case processes.

### P2 acceptance

- [ ] `test_nested_budget`: synthetic 16 outer ×16 workers cannot enter a 16-slot admission; controllers/children and thread reservation are accounted for; independent CPU jobs advance when unrelated GPU lease is held.
- [ ] `test_serial_domains`: same device/RNG domain never overlaps; different admitted devices can; multi-device allocation has no reversed-order deadlock; timing-exclusive case excludes competing work.
- [ ] `test_exclusive_attempt_race`: two launches on one attempt admit exactly one; occupied log/result/scratch destinations never overwrite.
- [ ] `test_failure_and_interrupt`: nonzero child exit makes runner nonzero; signal/timeout preserves start/log/partial records with interrupted disposition; no invented final witness; exact argv/env/cwd/seed and hashes survive.

### P3 acceptance

- [ ] `test_process_custody`: controller, worker and spawned child emit actual distinct PID/PPID/start identities and imports; wrong interpreter/import root, missing child/end, unadmitted replacement and reused PID with wrong start identity reject.
- [ ] `test_nonperturbing_observer`: discovery/identity cannot call CUDA or change RNG in fresh-uninitialized cases; fork guard observer cannot call Torch; role-specific inter-op=5/debug=True stays required where currently prescribed.
- [ ] `test_source_freeze_witness`: source/index/import mutation is refused; absent no-writer barrier is unqualified even when start/end hashes match. Source change tests use inert synthetic fixtures, not another application checkout.

### P4 acceptance

- [ ] `test_exact_bindings`: altered argv, tool/spec/candidate/dependency/log hash, seed, device assignment or exit code cannot pass; unsafe result paths reject.
- [ ] `test_required_case_outcomes`: expected collection set equals observed set, with no duplicates; required skipped/xfail/missing/collection-only cases remain unsatisfied even if pytest exits zero; structured setup/call/teardown failures are retained.
- [ ] `test_evidence_class`: CPU seam, mock CUDA and metadata-only device presence never satisfy real-CUDA obligation. Real-work evidence requires accepted case-specific producer/consumer observations, not an `is_available` flag.
- [ ] `test_immutable_receipt`: repeated destination refuses; successful, failed, interrupted, refused and UNRUN classifications stay distinct; missing absolute times are stated unavailable.

### P5 acceptance

- [ ] `test_strict_child_mutations`: independently mutate each existing PID/PPID/queue/Process correlation, import/source digest, typed field, thread/debug value, parent RNG digest, error identity/order, quarantine-before-unlock and case inventory; each rejects.
- [ ] `test_fork_protocol`: all three existing trials, exact actions/counters, OS single-thread profile, no-Torch reason and parent wait/queue/hash ancestry are mandatory; no-zero-effect or missing trial rejects.
- [ ] `test_phase_pair`: swapped/duplicate specs, wrong existing custody, typed bool/int difference, changed shared source/events or missing reference refuses; valid two-attempt CPU pair remains explicitly CPU evidence.
- [ ] `test_hardware_roles_separate`: new real-device cases use explicitly supplied protocol inventory. CPU stand-in logical device values cannot silently become hardware obligations. Complete synthetic records prove verifier behavior only.

## Additional interface packets required; not read or authorized here

The five inspected bodies cannot establish child instrumentation or real-work evidence end to end. These are explicit prerequisites, not permission for another read campaign:

1. **Child producer interface slice:** root supplies the exact current producer/consumer helper paths for `test_replay_rng_custody.py`, `test_recurrent_replay_rng_custody.py`, `test_rng_cuda_admission.py` and `test_replay_cuda_producer.py`, already named by the strict verifier. Split by protocol family, with at most one producer/test body, its actual helper if needed, new witness interface and focused test per packet, ≤5 files/5,000 lines. Establish record emission inside the actual child, parent observation hooks, output path routing, end witness and no-Torch fork exception. These files have not been inspected; their line budgets must be supplied before a body read. If a body alone exceeds the cap, request an explicit reslice.
2. **Real CUDA evidence interface slice:** existing owner supplies executable exact IDs and witness schema for each of the six accepted hardware groups. Pin source/storage/output/device/event observations, actual async work completion, before/after RNG custody and injected-versus-native failure labels. Do not invent test IDs or production APIs. Missing executable controls stay UNRUN with their existing owner. Split each group into separately bounded producer/helper/test packets, never include application bodies implicitly.
3. **Current B/parent/recurrent protocol slice:** root supplies current canonical route/ten child inventory, final-source disposition and accepted parent/currentness receipts. Generic process identity does not replace route-specific leaf, B6, outer completion or owner-lock evidence. Inspect only a newly authorized bounded helper packet if metadata cannot settle the interface.
4. **Failed/interrupted evidence interface:** derive explicit new failed/interrupted schema in P0/P4; if reuse of another historical verifier is proposed, request a separate bounded packet for that verifier and tests. The failed verifier mentioned by readiness was not read here. No silent schema rewrite or generic-success receipt for a failed run.

These are finite interface requests. They do not reopen accepted application designs, expand this read scope, or authorize implementation. Resolve them using existing sealed metadata where possible; otherwise root explicitly assigns the minimal reslice.

## Final tool qualification and actual-server checks owed

- [ ] Root seals new tool bytes and dependency closure after P0–P5 pass synthetic tests, then runs adversarial complete synthetic attempts through runner → identities → both independent verifiers. Verifier tests must not depend solely on runner-produced expected fixtures. Preserve negative evidence and exact qualification command/result/tool hashes.
- [ ] Independent review verifies no accepted child/RNG/fork/phase obligation was dropped, and every historical tool hash above is unchanged. Qualification applies only to pinned new bytes; any later edit requires affected checks again.
- [ ] On supplied authorized server, record access/location and measured resource admission. No remote creation, installation, quota increase or spend is implied. Confirm dependencies/driver/device mapping in a separate probe and root's source-freeze interval.
- [ ] On exact final B candidate, collect exact owned selections and establish causal fixture/import positive controls before costly runs. Missing/stale consumers return to owner; do not repeatedly execute a known broken suite or replace required suites with focused subsets.
- [ ] Execute a bounded CPU smoke attempt and one real CUDA operation/observation attempt under the qualified new tools. Verify identities, topology mapping, source pre/post witnesses, exclusive attempt retention, exit handling and actual device work independently. This qualifies transport/tooling, not all BAC hardware behavior.
- [ ] Exercise actual server scheduling: two independent CPU jobs within measured capacity, contending same-device jobs serialized, per-device independence only where available, and timing-exclusive interval with observed contention. Do not launch sixteen workers unless admission supports the full nested resource budget.
- [ ] Execute all six accepted real CUDA groups from the handoff, with exact supplied cases: fresh initialization/CPU no-init, nondefault-device and ambient RNG preservation, unindexed switching, cross-device prepared material/parent currentness, async completion with competing owner, and injected failures after delegated real work. At least two visible GPUs are needed for two-device cases; one GPU leaves those UNRUN. CPU mock device lists do not imply three real GPUs are required for unrelated cases.
- [ ] Root proceeds with the handoff's remaining ordinary runner/joint learning, restart/transfer/serving/output, repository/coverage and finite learning obligations only under their existing prerequisites. This tooling plan changes no cohort, acceptance threshold or global gate.
- [ ] Publish a new exact-source receipt with immutable references and predecessor linkage through the existing BAC evidence process. Keep hardware, component, package and tool qualification separate; preserve all failed/interrupted/skipped/UNRUN attempts and deduplicate overlapping selections by exact candidate.

## Blocking facts and risks

Implementation is not authorized by this report. Root must allocate the finite new-tool packets and resolve the child/real-CUDA interface slices. Current B qualifications must finish or release their freeze before integration changes. Server access, authorized execution path, CPU quota/affinity, GPU count/topology/MIG arrangement, visibility, Torch/driver compatibility, RAM/scratch/retention, competing workloads and permissible resource allocation are still missing.

A single GPU cannot discharge two-device obligations. Hardware inventory cannot prove actual CUDA execution. Startup/post-run hashes alone cannot prove no transient source mutation. Generic pytest hooks cannot attest arbitrary children or native device events. Stronger instrumentation can itself perturb lazy CUDA, RNG or timing unless role-aware. Filesystem permissions and hashes provide evidence retention under the authorized writer model, not protection from a privileged host administrator. Each limit is handled by the specific checks above or an explicit unqualified disposition, never scope reduction.

**Plan status:** Static plan only. No implementation, runtime validation, server access or BAC qualification result is claimed. Self-review maps all requested capabilities to P0–P5, interface prerequisites or the actual-server checklist; unresolved facts remain explicit.
