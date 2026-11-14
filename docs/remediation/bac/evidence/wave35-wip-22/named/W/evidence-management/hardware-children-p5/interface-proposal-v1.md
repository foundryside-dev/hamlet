# P5 strict child / fork / phase interface proposal v1

Status: exact historical consumer and supplied producer metadata reconciled; new
producer integration unresolved. Metadata proposal only; no new verifier/test
body authored or executed. Root owns interface adoption and later implementation.

Authorized body ledger: Q/verify_bac_replay_spawn_identity.py 752 lines,
SHA256 6006c7247d79a99226a74756a2266a2966fce800f9f84af802f2990db4606173;
Q/bac_hardware_protocol_v1.py 520 lines,
SHA256 adc8efeba368998e2e875a60c54ed3338a5ad2aa7daa710b7609e9ed2119de3c.
These two exact bodies were read, never imported/executed or edited. Remaining
allowance is the two named new Q bodies verify_bac_hardware_children_v1.py and
test_verify_bac_hardware_children_v1.py, combined <=3528 lines. Whole packet
<=4800/four bodies. No producer/testAPP/helper body was read. Metadata reports
are attributed facts, not independent inspection of their underlying producers.

## Exact established consumer inventory

The old verifier has exactly 28 jobs: two replay, sixteen core, ten flat/PER
producer. It admits no arbitrary case prefixes. Each fixed node uses one parent
controller, no xdist, and arguments -m pytest NODE --no-cov -p no:cacheprovider
-p no:benchmark -p bac_source_identity -q. Old runner digest is pinned to
180558c22da088a57326aa9251fbb64761e2788f18cb982532525b84b571f791. These bindings
are historical qualification schema, not the new P0/P3 launch contract.

Replay: replay-poison selects test_replay_rng_custody.py::
test_isolated_replay_poison_refuses_all_direct_samplers, worker replay_poison,
message `replay poison fail closed`. recurrent-replay-poison selects
test_recurrent_replay_rng_custody.py::
test_isolated_recurrent_scratch_work_cannot_heal_common_poison, worker
recurrent_replay_poison, message `recurrent replay scratch poison fail closed`.
Both files are under tests/test_townlet/regressions/bac/.

Core cases: bootstrap_failure, runtime_query_failure, local_completion_single,
local_completion_multiple_body, poison_unknown_ready, poison_ready_qualified,
poison_ready_healthy_only, operation_body_completion,
local_completion_duplicate_parent, inherited_pid, invocation_same_error,
invocation_child_failure, invocation_parent_failure, invocation_reported_failure,
invocation_phase_reference, invocation_phase_failure. Job is cuda-core- plus the
literal case with underscores replaced by hyphens; role cuda_core_CASE. Each
selects test_rng_cuda_admission.py::test_isolated_poison_protocol[CASE], except
inherited_pid selects test_isolated_inherited_pid_gate_refusal. Messages are
`cuda core CASE fail closed`, except `cuda core inherited pid gates fail closed`.
Six invocation cases each require a one-job spec. Current source-qualified B
core handoff preserves these roles and expands local fork actions as below.

Producer: flat/per crossed with local_single, local_distinct, local_same,
admitted_single, admitted_same. Job cuda-producer-poison-CASE; one-job spec;
node test_replay_cuda_producer.py::test_isolated_producer_poison[CASE]; role
cuda_producer_poison; message `cuda producer CASE poison quarantines under owner
custody`. Source owner identifies target _producer_poison_child(case, queue),
spawn Process name equal role. All 28 are CPU/CPU-standin contracts, never real
CUDA; logical [0,1] and [0,1,2] are exact finite stand-in protocol values.

## Exact inner schema and semantic retention

Controller exact fields: sha,candidate_tree,module,worker,torch,threads.
Replay child adds pid,ppid,manifest_sha256,debug,interop_threads,imports,
replay_imports. Core replaces replay_imports with cuda_core_imports and
cuda_core_test_sha256. Producer replaces replay_imports with producer_case,
cuda_producer_imports,cuda_producer_sha256. No optional superset acceptance.

Parent observation exact base: process_pid,queued_pid,exitcode,qualified,message,
manifest_sha256,parent_pid. Core adds queued_ppid; phase core additionally adds
invocation_phase_sha256. Producer adds case,queued_ppid,before,after,success.
Every PID is positive exact int; child.pid=Process.pid=queued_pid;
child.ppid=parent_pid != child.pid; queued_ppid matches where emitted. Child and
parent success exit are exact int0, qualification identity-True. Original three
bootstrap imports, finite role imports, actual imported file hashes and sealed
source inventory must agree. Controller/child Torch version agrees, intra1,
interop5, debug identity-True. New P3 must add actual start/host/boot/argv and
start/end lifecycle binding; the old fields cannot establish these themselves.

Producer preflight exact case,pid,ppid,qualified,before; before exact
 domain,devices,error_ids. Parent-before exact case,parent_pid,qualified,before.
After exact case,pid,ppid,qualified,phase,success,observations,failure. Accepted
phase complete/success True/failure null; preflight/fault remain failures.
Observation keys exactly healthy_controls,reached,started_work,syncs,peer_blocked,
worker_errors,peer_errors,completion_failed,outcome_errors,quarantine_before_unlock,
owner_quarantined,cpu_local_available,ambient_refused,domain_after.
Healthy/reached/peer/quarantine/CPU/refusal True; quarantine_before_unlock [True];
outcome_errors []; local syncs exact [0,1]; admitted trace starts0, members0/1;
nonempty all-True completion_failed and exactly one for admitted. Domain health
is [nonnegative exact int,nonnegative exact int,exact bool], healthy before,
poisoned after. No whole-domain-tuple equality across legitimate operations.

Errors exact type,message,id,children. Names ValueError/RuntimeError/OSError,
positive exact process-local id, leaves children[]. Distinct local output is
ExceptionGroup with B,C0,C1 in identity/order and new group id; same output is
B, single output C0. Preserve body/completion messages and actual started-work
phase. Peer is RuntimeError containing quarantined. No generic error matching.

Parent baseline exact domain,python,numpy,torch,cuda. Python/Torch are SHA256;
cuda null or ordered digest list. NumPy exact ["MT19937",digest,position 0..624,
flag exact int0/1,cached finite float]; do not coerce float/int/bool or reset cache.
Standalone parent-before equals observation.before; Python/NumPy/Torch/CUDA
before/after equal actual retained parent state. Core/replay actual parent RNG
assertions are source-owner obligations; the old verifier has NO serialized
baseline schema for them. A new generic baseline must not be invented here.

Fork requires exactly admission,local,invocation, each with child identity and
spawn-parent observation; all three distinct PIDs and no ancestor collision.
Identity exact schema,profile,role,trial,pid,ppid,inherited_domain_pid,qualified,
base_commit,candidate_tree,manifest_sha256,cuda_core_imports,module_origin,
source_sha256,os_threads,torch_profile,torch_profile_unavailable_reason,guard_results.
Observation exact schema,trial,role,parent_pid,fork_pid,waitpid_pid,wait_status,
exit_code,queued_pid,queued_ppid,identity_sha256,message,
parent_os_threads_before_fork,manifest_sha256. Schemas cuda-core-fork-guard-
identity-v1 and cuda-core-fork-guard-observation-v1; profile linux-fork-inherited-
guard-only-v1; role cuda_core_inherited_pid_guard; message `cuda core inherited
pid TRIAL fail closed`. Child PID equals fork/waitpid/queue; PPID=inherited domain
PID=observation parent/queue PPID=outer child PID. Normal raw Linux wait status0
and exit0 exact ints; identity byte digest, current manifest/source/imports exact.
OS task counts exact1 before fork and inside guard. Torch profile null and reason
exact `no Torch calls permitted in fork guard-only process`; module origin exact
inherited-loaded-module-objects. No Torch/NumPy/CUDA calls or RNG snapshots in
fork guard. Any added P3 observation must preserve this, not bootstrap a new role.

Admission actions resolve_cuda,enroll,report_failure,domain_admission. Local
resolve_cuda,complete,completion_failed,report_failure,domain_local_cuda_access,
domain_local_cuda_policy,domain_resolve_local_cuda_record. Invocation active_enter,
active_exit,active_completion_failed,completed_completion_failed,
domain_device_invocation. Every result exact lock_acquire_calls,
owner_lock_acquire_calls,cuda_touch_calls,body_calls,exception_class,diagnostic,
state_unchanged; counters exact int0, unchanged True, class builtins.RuntimeError,
diagnostic `RNG custody cannot be inherited by another process`. Zero counters
also depend on independent owner/source probe coverage; JSON does not prove it.

Phase artifact exact schema,role,case,pid,ppid,base_commit,candidate_tree,
manifest_sha256,source_sha256,devices,synchronize_events,exception_labels,
completion_failed; schema cuda-core-invocation-phase-v1. Actual source map exact
two core/test keys, devices exact ints[0,1,2], nonempty observed integer0/1/2 vector,
labels [body,synchronization]; completion null for reference and True for failure.
Parent pins actual phase byte hash. Exact phase-file inventory, including zero
phase artifacts for nonphase roles. Pair requires two distinct one-job specs and
job directories in reference/failure order; separately qualified existing strict
receipts recomputed and compared recursively with exact types. Shared source/root,
manifest,devices,labels and observed event vector equal; independent sequential
subjects may reuse numeric PIDs. Missing/swapped/duplicate/tampered/coherently
rehash-mutated records refuse. Pair does not invent a fixed event tail.

## Concrete new interface proposal, requiring root decision

Planned public standalone entrypoint remains
verify_children(spec_path: Path, job_id: str, destination: Path) -> dict.
Proposed fixed internal integration export is
validate_child_obligation(subject: dict) -> dict. It performs pure data validation:
no APP, Torch, CUDA, old verifier, Git, dynamic module import, subprocess, output
write or caller-selected callback. Only literal supported P5 kinds dispatch to
reviewed functions. P4 remains receipt writer with actual validation PID/UTC;
P5 standalone records its own actual validation identity/time and exclusive
receipt. Return is a strict-component verdict, never a hardware/common-P4 PASS.

The exact subject dictionary and return keys must be finalized jointly after the
owner payload decision below. Required subject material is pinned P0 spec/job/
obligation/contract/schema/evidence plus parsed reference-bound payload/process/
source records, and exact two phase subjects when applicable. No unchecked
`checked=True`, status-string or arbitrary mapping constitutes authority. P4
recomputes all common bindings and P5 recomputes strict correlations. Root's
adopted finite inventory must pin P5 source/dependency/contract/schema/evidence
class and independently reviewed entrypoint before P4 can invoke it. Existing P4
four-body slice currently imports no P5; root must explicitly reslice integration.

Do not reuse old verify/_validated_subject: old spec is root/manifest/output/
workers/jobs(name,args), old result/controller schemas differ, its repository
check invokes write-tree, and exact argv pins the old plugin. P0 candidate
reference is not an old manifest digest. P3 raw context and start/end are actual
new observations, not fields that can be synthesized from old receipts. No
compatibility fallback, old/new autodetection or dual acceptance is proposed.

## Finite owner-interface questions before implementation

1. Supply/adopt one exact new producer transport contract for these finite roles:
   either retain the above closed inner semantic records with an explicitly
   reviewed new P0 binding, or replace their schemas directly in the owning
   slices. Who emits each record, how source identity maps without fake old
   manifests, exact filenames/output paths and allowed inventory must be explicit.
2. Supply exact direct-owner P3 contexts and actual parent-start linkage for
   spawn and all three forks; their start/end placement, imported-source phases,
   no-Torch fork path and inherited argv. P3 v3 allows empty policy/runtime only
   for separately accepted direct-owner integration. Exact child environment
   phase transport including PYTEST_CURRENT_TEST remains unprovided. Controller
   policy/runtime binding is mandatory, with newly sealed argv; no old argv waiver.
3. Supply current source-qualified parent RNG observation contract for core and
   both replay families, or explicitly identify retained actual source assertions
   plus their independently qualified custody as the intended proof. Producer's
   existing serialized baseline alone must not qualify unrelated families.
4. Define phase-pair related_attempts exactly (two spec refs in fixed reference/
   failure order is proposed), subject job/receipt discovery without adjacency
   guessing, and new independently recomputable strict receipt shape. Each
   subject must be already individually strict-qualified with no recursive pair
   requirement; no circular common/P5 receipt authority.
5. Root authorizes exact current source/case inventories and finite P4 integration
   reslice after P5 freeze. Existing core metadata confirms local7/admission4/
   invocation5 actions and preserved16 roles; it does not attest current P3
   instrumentation. No new B routes/ten-child acceptance follows automatically.

Six real-CUDA owner schemas/executable controls remain pending separately. They
are not P5 CPU roles; missing controls stay UNRUN. No server/GPU/application or
whole-program qualification is claimed by synthetic fixture success.
