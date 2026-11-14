# P5 flat/PER producer supplier v1

Status: bounded source facts and one proposed replacement protocol, not adoption,
implementation, execution or qualification. C1 source remains frozen. No imports,
tests, hardware, production dependency reads, source edits, branches, worktrees,
copies or index operations occurred. Only this metadata file is written.

## Scope and byte identity

R=/workspace/hamlet. Exactly two counted bodies, 3556/3800 lines:

| Relative body | Lines | Bytes | SHA256 before = after |
| --- | ---: | ---: | --- |
| tests/test_townlet/regressions/bac/test_replay_cuda_producer.py | 2558 | 123958 | e629acf35a89bb5719945b4c8c9a5578de2dc1c69791038ba2072bb71dabe801 |
| tests/test_townlet/regressions/bac/test_world_rng_bootstrap.py | 998 | 45937 | 452e427b945475e050b35273b6bb44effe3ade6ef96629c4382c2d68591ee727 |

Both hashes were measured before and after source inspection in this turn.
Relevant producer regions: imports/fixtures 7–134, simulation 336–499 and complete
poison target/parent protocol 1115–1420; bootstrap qualification 833–865 and RNG
helpers 67–83. Metadata consumed: E/hardware-children-p5/interface-decision-and-
owner-requests-v2.md and interface-proposal-v1.md; P/CUDA-HARDWARE-P5-BOOTSTRAP-P3-
SUPPLIER-v1.md and CUDA-HARDWARE-P5-CORE-FORK-PHASE-SUPPLIER-v1.md. Their P0/P3
implementation and historical verifier claims are attributed, not newly inspected.

## Exact ten mappings and actual execution

Every node has prefix tests/test_townlet/regressions/bac/test_replay_cuda_producer.py::
and suffix test_isolated_producer_poison[CASE]. Every actual Process name/role is
cuda_producer_poison, target _producer_poison_child(case, queue), start method spawn.
The job vocabulary below comes from the P5 inventory; preserve literal underscores
in CASE. One case per one-job spec/output avoids the current fixed-name collisions.

| CASE | Job ID | Operation / error schedule |
| --- | --- | --- |
| flat_local_single | cuda-producer-poison-flat_local_single | serialize / completion0 |
| flat_local_distinct | cuda-producer-poison-flat_local_distinct | serialize / body, completion0, completion1 |
| flat_local_same | cuda-producer-poison-flat_local_same | serialize / same body and completion0 object |
| flat_admitted_single | cuda-producer-poison-flat_admitted_single | sample / completion0 |
| flat_admitted_same | cuda-producer-poison-flat_admitted_same | sample / same body and completion0 object |
| per_local_single | cuda-producer-poison-per_local_single | serialize / completion0 |
| per_local_distinct | cuda-producer-poison-per_local_distinct | serialize / body, completion0, completion1 |
| per_local_same | cuda-producer-poison-per_local_same | serialize / same body and completion0 object |
| per_admitted_single | cuda-producer-poison-per_admitted_single | sample / completion0 |
| per_admitted_same | cuda-producer-poison-per_admitted_same | sample / same body and completion0 object |

Exact success message: `cuda producer CASE poison quarantines under owner custody`.
Historical launch metadata has one controller/no xdist and -m pytest NODE --no-cov
-p no:cacheprovider -p no:benchmark -p bac_source_identity -q. The proposed current
argv replaces the obsolete plugin with separately adopted P3 activation and its
sealed policy path/hash; no exact new runtime argv is fabricated here. Record the
spawn child's actual /proc argv independently from pytest's parent argv.

Parent registers a baseline participant over all visible devices ONLY if CUDA is
already initialized, otherwise (). It creates spawn Queue/Process, captures RNG
inside domain.operation, checks healthy domain, writes parent-before, starts and
joins90s, requires dead/exit0, then queue.get(timeout5). Exact tuple comparison
binds message, Process.pid, actual parent PID and qualification bool. Finally it
terminates a still-live started process and joins5s, recaptures/asserts RNG under
the baseline operation, checks healthy domain, unregisters, writes observation,
then queue.close/join_thread and process.close. There is no explicit final
is_alive assertion after the emergency join; process.close on a live process
would raise. No successful terminal claim may survive cleanup failure. Current
observation precedes queue/process cleanup; success is set only after baseline
assertions and paired queue success, but is not itself a completed pytest report.

Child calls identity first, checks case, constructs actual error objects and
writes preflight. The fault section runs inside MonkeyPatch/_cuda_simulation.
Worker Thread executes serialize/sample; competing Thread attempts actual clear.
Both are joined5s; both must be dead. Simulation and patches restore before the
finally-written spawn-after. Errors are recorded and re-raised; failed children
do not enqueue success. Successful child then queues message/PID/PPID/qualified.
No current child/parent P3 start/end exists; Queue success is not a termination
witness. No fork or guard path exists in this owner. No child OS-task-count1
precondition may be invented: Torch and the two deliberate threads can exist,
and Queue.put may start a feeder thread.

## Existing serialized facts and assertion preservation

The following are actual JSON fields, not proposed observations. _poison_json
uses exclusive `x`, sorted JSON, allow_nan=False, fixed STEM-cuda_producer_poison.json;
presence of BAC_QUAL_OUTPUT alone controls writing (qualification separately
requires the full bundle). Accepted source assertions remain mandatory even where
JSON is less detailed.

- Child identity extends the bootstrap identity with ppid, producer_case and
  cuda_producer_imports/cuda_producer_sha256 for exactly rng_custody,
  replay_contract, replay_buffer, prioritized_replay_buffer under their actual
  townlet module names, and test_replay_cuda_producer. Hashes read actual loaded
  module files. Bootstrap adds actual PID, manifest hash, Python __debug__, interop
  and actual imported world_curiosity_state/rng_custody/rnd paths. Old manifest,
  worker-label, sha/tree transport is obsolete, not an accepted inner schema.
- Preflight: exact case,pid,ppid,qualified,before; before has domain,devices,error_ids.
  devices is logical [0,1]; error_ids is [body-or-null, first, second-or-null].
- After: exact case,pid,ppid,qualified,phase,success,observations,failure. Phase starts
  preflight, becomes fault after healthy controls, then complete. success True and
  failure null require all child assertions; failures retain actual recursive
  error records and the observations available before failure.
- Full successful observations: healthy_controls,reached,started_work,syncs,
  peer_blocked,worker_errors,peer_errors,completion_failed,outcome_errors,
  quarantine_before_unlock,owner_quarantined,cpu_local_available,ambient_refused,
  domain_after. Healthy serialize checks actual observations equal _rows and
  authentic local arming/completion [0,1]; healthy sample checks shape(2,2) and
  syncs(0,1). These detailed value/arming checks are assertion-only; serialized
  healthy_controls=True is their checkpoint, not their independent proof.
- Fault must reach synchronization; peer attempts clear and remains blocked0.1s;
  release precedes joins; both threads dead, no outcome_errors; markers nonempty
  all exact True; quarantine_before_unlock exactly [True]. Local markers observe
  real gate.completion_failed; admitted markers observe the single actual issued
  invocation on its issuing worker. Exactly one worker error and one peer error;
  peer RuntimeError contains quarantined. Existing source checks invocation count1;
  strict accepted admitted completion_failed is [True].
- Error nodes have exact type,message,id,children recursively. IDs are positive
  process-local object IDs, not PID/source identity. Body is ValueError `CASE: body`;
  first RuntimeError `CASE: completion0` except same schedules alias the body;
  second OSError `CASE: completion1` only for local_distinct. Distinct output is
  the actual exception group with exactly body/first/second in that order and
  identity; other output is exactly first. Preserve new group identity distinct
  from its leaves. Singles have body/second null, same has body_id=first_id and
  second null. started_work True for body schedules (after a genuine selected
  tensor result shape(4,2) local or(2,2) admitted), False for single schedules.
- Local fault syncs exactly [0,1]. Admitted syncs nonempty, start0, members only0/1;
  do not invent a permanent cleanup suffix. Owner clear refuses quarantine before
  and after competitor release. Domain poisoned; separate CPU control clear/push
  succeeds with length4, its ambient sample refuses, domain remains poisoned.
  The length/value/actual rejection details are source assertions, not fully
  serialized traces. Domain status has two nonnegative
  exact ints and exact bool; before healthy, after poisoned, not equal tuples.
- Parent-before exact case,parent_pid,qualified,before. Parent observation exact
  case,process_pid,queued_pid,parent_pid,queued_ppid,exitcode,qualified,message,
  manifest_sha256,before,after,success. before must equal standalone parent-before.
  Child PID/PPID correlate actual Process/queue and parent; PID differs from parent.
- Parent baselines really serialize exact domain,python,numpy,torch,cuda. Python
  digest hashes repr(getstate()). NumPy is [algorithm,digest of state-array bytes,
  position,has_gauss,cached_gaussian]; Torch CPU hashes state.numpy().tobytes().
  CUDA null means not initialized at snapshot, otherwise ordered per-device state
  hashes after CPU transfer. Full in-memory tuple equality also executes through
  _assert_tree_equal, including CUDA tensors, dtype/device and exact RNG values.
  It is not merely digest equality. Strict baseline schema retains MT19937,
  position0..624, exact int flag0/1, finite float cache, SHA256 strings and null-or-
  ordered CUDA hash list. All RNG fields before/after equal; domain status need not
  equal across legitimate operations, but both are healthy. No RNG draw-vector
  comparison occurs in this producer path. Bootstrap's _assert_ambient is unused.
- Autouse preserve_cpu_rng captures/restores Python/NumPy/Torch CPU in fixture
  teardown; that restoration is not the parent unchanged assertion and cannot
  replace it. Fixture does not capture CUDA. Passing teardown remains required.

## Actual launch/import/thread requirements and hardware boundary

All five BAC_QUAL_ROOT/SHA/TREE/MANIFEST/OUTPUT keys present activate historical
qualification; none gives unqualified tests; partial bundle asserts. Empty values
are not rejected by activation itself. Bootstrap calls old bac_source_identity
with fabricated workerinput role, requires assertions-enabled True, intra1/inter5.
Neither inspected body sets those thread counts. The old helper's setting/import/
Git behavior is attributed to the P3 capsule, never authorized for reuse here.
Module-level imports already load Torch, NumPy and listed replay dependencies;
the target explicitly imports test_world_rng_bootstrap even when unqualified.
Its helper imports the three exploration modules only when qualified. Exact origin
hashes must come from the actual accepted inventory, not guessed files or aliases.

Neither body overrides spawn environment nor reads/clears PYTEST_CURRENT_TEST.
The target inherits actual call-phase environment and any parent worker keys;
P3 owner-launch phase derivation is required. Preserve complete actual env and
nonworker child identity; do not erase keys or fabricate xdist workerinput.
P3 supplier amendments for Python debug versus anomaly and authenticated launch
env are pending. No proposed current_process_context/prepare_owner_launch API is
claimed implemented. Fork/no-import amendment remains separately pending but is
not a new requirement to run this spawn-only owner.

The poison cases use _SimCUDA (initialized True, logical device_count5) and
_CUDAData CPU storage. torch.cuda, transfers, six allocators and gate observation
are patched; real producer algorithms are exercised, real GPU completion is not.
No actual CUDA availability/version/device prerequisite is established for these
ten synthetic cases. A parent already initialized on CUDA additionally snapshots
real CUDA RNG; that alone does not qualify child GPU behavior. All six real-CUDA
owner groups in root's required inventory remain UNRUN. Their accepted hardware
host/runtime/device contract, real tensor/control/synchronization runs, actual
source/process records and independent qualification must be supplied separately;
logical [0,1], fixture device_count5, or successful synthetic poison is no substitute.

## Single new closed protocol proposed for adoption

Use the exact owner-launch/context proposal in the bootstrap/P3 capsule: actual
parent start, fresh parent source witness, admitted case/role/instance, spawn,
complete authenticated call env and actual __debug__ True; child derives context
with parent_start=[actual launcher start], lifecycle=[launch], worker_identity=null.
Activation is the proposed sealed BAC_HARDWARE_QUALIFICATION=bac-hardware-v1,
with retired BAC_QUAL_* rejected for qualification. This is one replacement;
no old/new fallback, retained identity inner object or adapter to old verifier.

Every ref below is exact P0 {path,bytes,sha256}; actual bytes, uniqueness, source,
process/raw/start/end/import and contract links are rechecked by P0/P3/P4/P5.
Closed JSON rejects missing/extra/duplicate keys, nonfinite values and bool-as-int.
The exact expected source imports are the three bootstrap exploration modules,
four producer production modules listed above (rng_custody overlaps), and actual
test_replay_cuda_producer/test_world_rng_bootstrap loaded modules. Declare test
imports end-only for controller collection; strict child start/end require their
already-loaded actual refs. Do not force imports inside patched observation cuts.
P3 start occurs after required modules are loaded and before simulation patching;
end occurs after all child assertions and patch restoration, before queue emission.
Recorders must not perturb parent RNG; baseline source assertions remain in force.

Proposed exact records (only the last is the obligation payload):

1. Parent baseline record keys {schema,spec,job_id,case,role,parent_start,owner_launch,
   before}; schema bac-hardware-producer-parent-baseline-v1. before retains the
   exact existing baseline schema. Emit after healthy baseline assertion and before
   Process.start. Launch preparation precedes this record; both are inside the
   captured parent RNG interval so perturbation cannot be hidden.
2. Child preflight keys {schema,spec,job_id,case,role,owner_launch,process_start,
   python_assertions_enabled,before}; schema bac-hardware-producer-preflight-v1.
   before is the existing domain/devices/error_ids shape; debug sampled __debug__.
3. Child outcome keys {schema,spec,job_id,case,role,owner_launch,process_start,
   python_assertions_enabled,preflight,phase,success,observations,failure}; schema
   bac-hardware-producer-outcome-v1. Retain every above observation/error schema and
   constraint. Full observations always has the exact14 listed keys: on failure
   only unobserved fields are null (new instrumentation, not historical fields),
   failure is the actual error tree; successful record has phase complete, success
   True, failure null and every established successful value. Emit after context
   restoration/all child assertions. A failed outcome is diagnostic, never success.
4. Queue acknowledgement exact {case,role,pid,ppid,message,outcome,process_start,
   process_end}, emitted only after successful outcome and actual P3 end. Parent
   validates actual received object, child start/end identity and Process PID/exit;
   it never reconstructs a missing acknowledgement from files. P3 end alone is
   not proof of process exit; successful join/exit0 remains mandatory.
5. Sole terminal payload keys {schema,spec,job_id,case,role,parent_start,owner_launch,
   parent_baseline,process_pid,exitcode,acknowledgement,before,after,assertion_source,
   parent_rng_assertion,cleanup}; schema bac-hardware-producer-result-v1.
   before/after retain exact baseline objects; before equals referenced baseline.
   assertion_source is actual producer test ref. parent_rng_assertion exact
   {kind:source-assertion-and-serialized-digests,checkpoint:after_child_join_before_unregister,
   function:_assert_tree_equal,channels:[python,numpy,torch_cpu,cuda_if_initialized]}.
   cleanup exact {participant_unregistered,queue_closed,queue_thread_joined,
   process_closed}, all actual completed True checkpoints. Save actual Process PID/
   exitcode before close. Emit exclusively only after baseline comparison/healthy
   assertion, unregister and queue/process cleanup return successfully; add explicit
   no-live-child assertion after emergency cleanup. No terminal payload on failure.

Proposed fixed basenames under exact job.output: producer-parent-baseline.json,
producer-preflight.json, producer-outcome.json, producer-result.json, sealed in
owner_contract, not found by adjacency. P3 refs are returned actual refs. Outcome
is emitted before end, acknowledgement binds both, terminal binds acknowledgement,
avoiding future-reference cycles. Later P0 completion inventories all referenced
bytes, real parent end and actual pytest setup/call/teardown reports; P4 requires
all pass/no skip/no xfail. Early failure diagnostics remain preserved and refuse
satisfaction. No generic success/debug/checkpoint boolean independently proves
assertion execution: exact source-qualified reports and independent assertion
custody are mandatory. P5 independently checks every retained typed correlation.

## Owner decisions and finite later edit packet

Root/P3 must first adopt exact activation, owner-launch/env derivation, Python
debug correction, imported-origin requirements, record names and P3 runtime cuts.
P5 owns adoption of the closed nested schemas and error/baseline comparisons;
P4 owns report/source/process/end custody, P2 actual outer launch/wait. Child
error IDs stay process-local and must never be compared across jobs. Root must
retain ten independent job/output instances and all six real-CUDA obligations.

Proposed AFTER C1 freeze release only: edit existing test_replay_cuda_producer.py
current2558/max2900 lines, plus one root-named new inert protocol test body max650;
two edited bodies/max3550. Bootstrap/helper changes belong to separately bounded
P3 owner packet; no production/P0/P3/verifier body enters this edit grant. This
supplier read cap grants no edits or tests. Any extra helper/body or cap increase
requires explicit root reslice. Later finite tests should reject each error-order/
identity, poisoned-domain, admitted-sync, baseline type/cache/CUDA, wrong actual
parent/role/source/env, missing end/queue, cleanup failure and -O mutation, followed
by separately authorized exact ten jobs and independent qualification. Hardware
execution is a separate required packet. None ran here.
