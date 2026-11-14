# P5 core/fork/phase supplier v1

Status: finite source facts and one proposed replacement protocol; not an adopted
schema or runtime qualification. C1 global APP freeze remains active. No APP or
testproducer edits, imports, tests, hardware, Git operations, branches, worktrees,
execution copies, installs or access changes occurred. Only this metadata capsule
is written. Production core, P3/P0 implementation, helpers and old verifier bodies
were not read. Supplied interfaces and production reviews are opaque attributed
metadata, not independently re-reviewed implementation.

## Exact read budget and sources

Both authorized bodies were measured and rehashed before their first body read:

| Path relative to repository | Lines | Bytes | SHA256 |
| --- | ---: | ---: | --- |
| tests/test_townlet/regressions/bac/test_rng_cuda_admission.py | 2883 | 134020 | b1f05946a4f2c0e145c44226323dc7b599f36a1364c854d26f090fa45b1a4409 |
| tests/test_townlet/regressions/bac/test_world_rng_bootstrap.py | 998 | 45937 | 452e427b945475e050b35273b6bb44effe3ade6ef96629c4382c2d68591ee727 |

Exactly two counted bodies, 3881/4200 lines. Relevant regions inspected include
core imports, 1363–1819, 1823–2360 and bootstrap 833–865. No other body expansion.
Read-only text/hash tools do not establish runtime outcomes.

Consumed metadata: E/hardware-children-p5/interface-proposal-v1.md SHA256
27312ae30234b9f27cbf9d04f6ada1bac720a5b312c5ac3c94e7fe64b79fc8bf;
interface-decision-and-owner-requests-v2.md
3cd9c4a5bc4ff3c37fbc0dcfe961e9f12d9cc757bbab414b30f2c3fff78c95c9;
E/hardware-identity-p3/context-contract-v3.md
1eb2d8b5e2e11621ce59aef78a7c982d2cafe4ab81117004897a6ed5a9447faf;
its v2 base context-contract-proposal-v2.md
0c640ebd57ffc2475e15dc1754837bdd88250d9576c4a171697f637ffd8a84c6.
P0 root-adoption-v2.json adopts interface-contract-v4.json, whose SHA256 is
0a0b4de21d8f9f168785f6b2483c7c1ad5e1ec79ec27fe56ec56838833b421b5.
P/T18e-R0-CUDA-PRODUCER-B-CORE-ACTUAL-REVIEW.md SHA256
46d1a5576db5cbc0de3111680a3d36eccf761b370e5257b95dc7a088d9860a3d
supplies attributed production guard ordering and local7 facts; its older test
hash is not substituted for the current measured test hash above. Older
CORE-CURRENT-API and CUDA-CORE-CONTRACT-DRAFT are historical contracts, not current
source attestations (the latter still describes an older empty manifest).

## Exact current case and process inventory

Every job below selects the path tests/test_townlet/regressions/bac/
test_rng_cuda_admission.py. The node is test_isolated_poison_protocol[CASE]
except inherited_pid, whose node is test_isolated_inherited_pid_gate_refusal.
The exact fixed job is cuda-core-CASE with underscores changed to hyphens;
these names are attributed P5 inventory, while cases/roles/targets are directly
confirmed in the test. There are fifteen parametrized cases and one inherited
case, not sixteen parametrized cases. No cold-import case is added to P5.
Preserve the supplied fixed-job selection with xdist_workers=0, one controller,
one declared outer spawn role and, only for inherited_pid, the guard role count3.
Six invocation cases each use a distinct one-job spec; the two phase subjects
add the separately declared pair wrapper, not another child role. New controller
argv explicitly uses `-p bac_hardware_identity_v1 --bac-identity-policy PATH
--bac-identity-policy-sha256 SHA` in place of old bac_source_identity activation;
root seals the complete actual interpreter/pytest argv and PYTHONPATH. Preserve
the exact node, --no-cov, -p no:cacheprovider, -p no:benchmark and -q inventory
unless root adopts a changed command contract. The child records its actual
interpreter argv rather than treating these pytest arguments as its own.

| CASE | Exact actual Process name / role |
| --- | --- |
| bootstrap_failure | cuda_core_bootstrap_failure |
| runtime_query_failure | cuda_core_runtime_query_failure |
| local_completion_single | cuda_core_local_completion_single |
| local_completion_multiple_body | cuda_core_local_completion_multiple_body |
| local_completion_duplicate_parent | cuda_core_local_completion_duplicate_parent |
| poison_unknown_ready | cuda_core_poison_unknown_ready |
| poison_ready_qualified | cuda_core_poison_ready_qualified |
| poison_ready_healthy_only | cuda_core_poison_ready_healthy_only |
| operation_body_completion | cuda_core_operation_body_completion |
| inherited_pid | cuda_core_inherited_pid |
| invocation_same_error | cuda_core_invocation_same_error |
| invocation_child_failure | cuda_core_invocation_child_failure |
| invocation_parent_failure | cuda_core_invocation_parent_failure |
| invocation_reported_failure | cuda_core_invocation_reported_failure |
| invocation_phase_reference | cuda_core_invocation_phase_reference |
| invocation_phase_failure | cuda_core_invocation_phase_failure |

Actual launch uses multiprocessing.get_context("spawn").Process, target
cuda_core_child(queue,case), or inherited_pid_child(queue,str(tmp_path)). Both
parent tests join for90 seconds, require not-alive and exit0, then queue.get with
timeout5; message/PID/PPID/qualification are checked against actual Process and
parent. Finally they terminate an outstanding child, join10, close/join the queue,
close Process, require healthy parent domain and unchanged ambient RNG.
Message is `cuda core CASE fail closed`, except inherited message
`cuda core inherited pid gates fail closed`. No current argv/env observation is
emitted by these functions. Spawn interpreter argv must not be copied from pytest.

## Current source/import, runtime and RNG evidence

Bootstrap qualification is all-or-none presence of BAC_QUAL_ROOT, BAC_QUAL_SHA,
BAC_QUAL_TREE, BAC_QUAL_MANIFEST, BAC_QUAL_OUTPUT. _child_identity calls the old
bac_source_identity.pytest_configure with synthetic workerinput containing only
workerid=role. It reads identity-ROLE.json, adds actual PID, manifest digest,
Python __debug__, Torch interop getter, and imported file origins for
townlet.exploration.world_curiosity_state, rng_custody and rnd; requires
__debug__ is True, Torch intra1/interop5; rewrites and renames spawn-identity.
Core child_identity adds actual PPID, import origins for
townlet.exploration.rng_custody and test_rng_cuda_admission, and test file SHA256.
These are old transport observations, not P0 candidate refs or P3 process starts.
The bootstrap debug field is Python assertions enabled, not Torch anomaly mode.
No core test occurrence of anomaly or __debug__ supplies a different meaning.

All parent ambient observations are actual in-memory assertions: Python
random.getstate(), NumPy get_state(), torch.get_rng_state().clone(); comparison
uses exact Python state, NumPy algorithm/array/tail and Torch tensor equality.
Neither core parent serializes these values nor hashes them. No CUDA RNG state
is captured. The inherited spawn child additionally snapshots before its trials,
asserts ambient unchanged after admission and local trials, after invocation and
again after unregister. Guard grandchildren take no RNG snapshots. Ordinary
poison children have no additional ambient-preservation assertion of their own.
Existing spawn-observation is emitted BEFORE the final parent cleanup/RNG checks;
its qualified flag alone cannot prove their completion. Retaining assertion-only
RNG proof therefore requires the exact source-qualified passing parent call and
teardown reports plus independently qualified assertion custody. Producer-family
serialized baselines cannot be imported as core proof.

The child protocol semantic assertions remain source-owned. Their current emitted
data is identity and success message, plus phase records and fork records below;
no existing JSON records all poison/error/lock assertions. Preserve all case
assertions under the exact source; do not relabel a new success boolean as an
independently observed error trace. Examples that must remain include original
error identity/order, unchanged revision/currency rules, poisoned refusal and
CPU-local nonhealing, owner quarantine before competitor access, exact invocation
own-completion outcomes, and the authentic parent completion suffix in duplicate
local error handling. More serialized error instrumentation would require a
separately specified source edit, not inferred existing fields.

## Actual three fork trials, no-Torch boundary

inherited_pid_child preloads module objects, prepares the source fixture and real
locks, substitutes forwarding LockProbe wrappers, and installs ForbiddenCUDA.
run_fork_trial creates torch.device("cuda") and all action closures BEFORE fork.
It requires exactly one /proc/self/task entry before each os.fork. Each child
executes fork_guard_grandchild using inherited loaded module objects; no import,
Torch/NumPy call, queue call or inherited context unwind occurs in that function.
Its actual os task count must be1, PID differs from domain._pid, PPID equals it.

| Trial | Exact action set |
| --- | --- |
| admission (4) | resolve_cuda, enroll, report_failure, domain_admission |
| local (7) | resolve_cuda, complete, completion_failed, report_failure, domain_local_cuda_access, domain_local_cuda_policy, domain_resolve_local_cuda_record |
| invocation (5) | active_enter, active_exit, active_completion_failed, completed_completion_failed, domain_device_invocation |

Each action requires exact RuntimeError text `RNG custody cannot be inherited by
another process`, class builtins.RuntimeError, unchanged guard_state and exact
integer zero lock_acquire_calls,owner_lock_acquire_calls,cuda_touch_calls,body_calls.
guard_state includes domain/member/operation/token/gate/invocation/cache/manifest
identity and scalar state. These counters do not by themselves prove every read
preceded the PID check; that remains independently reviewed source evidence.

Child writes exclusive fork identity, computes its byte SHA256, writes a closed
pipe acknowledgement {trial,pid,ppid,identity_sha256,message} <=4096 bytes, closes
the pipe and os._exit(0). On error it writes bounded diagnostic and os._exit(1).
Parent uses select, nonblocking read, owned waitpid with10-second deadline and
bounded TERM/KILL cleanup; requires normal wait, exit0, exact acknowledgement,
PID/PPID/identity digest and writes exclusive fork observation. No multiprocessing
Queue is used inside guard. All three fork PIDs must be distinct from one another,
the spawning child and its ancestors under strict validation; numerical reuse
across independent phase jobs is not prohibited.

Current fork identity additionally emits actual inherited module paths and hashes
for precisely the two core/test names, module_origin inherited-loaded-module-objects,
os_threads1, torch_profile null, and reason `no Torch calls permitted in fork
guard-only process`. Current metadata uses old manifest/base/tree transport.
Current observation has parent/fork/waitpid/queued PID/PPID, raw wait_status,
exit_code, identity hash, message, parent_os_threads_before_fork and manifest hash.
Those semantic observations all survive replacement below.

## One replacement closed protocol proposed for owner adoption

All records below are NEW required instrumentation; none is claimed present.
One protocol only: old identity/manifest fields are replaced, never accepted as an
alternate schema. `ref` always means exact P0 {path,bytes,sha256}, validated against
actual bytes. `start/end` mean actual P3 records, not labels or copied parent
identities. Exact JSON keys below reject extras/missing fields, duplicate keys,
nonfinite numbers and bool-as-int. Only listed finite cases/trials are legal.
Source observations and references remain subordinate to root no-writer custody.

Use the P3 supplier's owner-launch contract and direct context from
CUDA-HARDWARE-P5-BOOTSTRAP-P3-SUPPLIER-v1.md. Its P3 amendment must be adopted before
this protocol can run. In particular child worker_identity remains null; actual
launching parent start is linked even if that parent is a pytest worker. Actual
PYTEST_CURRENT_TEST and inherited xdist environment must be carried by owner
launch phase transport, not deleted, generalized, or fabricated as workerinput.
No accepted current P3 API is falsely claimed to handle these additions today.

P3 supplier's exact proposed launch keys are schema,spec,command,owner_contract,
parent_process,source_witness,parent_identity,case_id,pytest_phase,child_role_id,
instance_id,start_method,environment,python_assertions_enabled,inherited_imports,
at,monotonic_ns. Schema bac-hardware-owner-launch-v1; pytest_phase call; actual
start_method spawn for the16 outer children and fork for each guard. Parent
process is its actual P3 start ref, source_witness its fresh source observation,
parent_identity its actual full identity, environment its entire observed map.
launch.python_assertions_enabled must be identity-True, independently checked by
P5, so parent assertion-only proof cannot be accepted with Python optimization.
This flag is not P3's Torch anomaly/debug runtime fact.
owner_contract must equal the selected obligation contract. case_id is the full
fixed pytest node above, instance_id an explicitly allocated unique role instance,
inherited_imports actual named file refs, UTC/monotonic sampled by the emitter.
The exact launching parent emits this record immediately before Process.start or
os.fork, after all pre-fork Torch preparation and identity dependencies are loaded.

Direct child context exact keys remain schema,spec,command,trusted_grant,job_id,
role_id,required_imports,worker_roles,environment_delta,parent_start,
replacement_start,lifecycle,worker_identity,policy,runtime. Copy spec/command/
trusted_grant/job_id/required_imports/worker_roles/environment_delta from the
actual parent's referenced raw context; set role_id to the exact child role,
parent_start=[launch.parent_process], replacement_start=[], lifecycle=[launch],
worker_identity=null, policy=[], runtime=[]. These changes are permitted only by
the separately adopted owner integration, not current generic worker derivation.
Launch environment is authorized parent start environment plus exactly observed
PYTEST_CURRENT_TEST=`FULL_NODE (call)`; nested fork inherits its spawn parent's
same call-phase map through the explicitly recognized launch chain. Other dynamic
xdist keys, if present, stay actual inherited values. Child P3 compares its full
map to launch.environment and observes its own /proc/self/cmdline independently.
Parent/child argv need not match. Spawn runtime getters occur before CUDASeam
patching and after restoration; no getter may run while ForbiddenCUDA is installed
in the fork guard. All guard runtime facts use the no-Torch unavailable branch.

Proposed sealed required imports are the names
townlet.exploration.world_curiosity_state, townlet.exploration.rng_custody,
townlet.exploration.rnd, test_world_rng_bootstrap and test_rng_cuda_admission.
Because the shared required_imports is copied from a pytest controller context,
test modules cannot be required at controller start before collection. Seal these
requirements at end; strict core additionally requires the actual child/fork
start and end imports to contain those already-loaded origins, as observed by P3.
This strengthens child correlation without inventing a different copied context.
Each named ref comes from the sealed actual candidate inventory, never a guessed
SHA. The guard's semantic source_modules remains exactly its existing two
core/test objects while P3 independently validates the larger inherited source
inventory. Source/file hashes for current production modules are deliberately not
invented here; root's accepted source inventory supplies them.

P3 supplier explicitly reports that present record_process also reaches read-only
Git subprocess/source validation and datetime/P0 machinery. Preloading the module
alone does NOT qualify the guard's no-import boundary, and its prior synthetic
fork test imports inside the target. A bounded P3 guard recorder amendment and
independent no-import/no-Torch probe are required. This proposal selects no
source-freeze exemption: actual child source observations remain mandatory; it
does not silently replace them with a copied parent HEAD/tree assertion. If P3
cannot supply the full recorder within this boundary, guard transport remains
UNRUN pending an explicit root contract decision, not a synthetic workaround.

1. **Child semantic result** exact keys:
   {schema,spec,job_id,case,role,owner_launch,process_start,python_assertions_enabled,
   message,phase,forks,rng_assertion_scopes}.
   schema=`bac-hardware-core-child-result-v1`; spec/owner_launch/process_start refs;
   case/role/message fixed by table; Python flag actually sampled __debug__ True.
   phase=[] except exactly one {devices,synchronize_events,exception_labels,
   completion_failed} for a phase case. Those values come directly from
   invocation_case's existing returned phase dict; devices exact ints[0,1,2],
   events nonempty exact int0/1/2 vector, labels exactly [body,synchronization],
   outcome null for reference and identity-True for failure. forks=[] except
   inherited case exactly three fork-observation refs in admission/local/invocation
   order. rng_assertion_scopes=[] except inherited exactly
   [after_admission,after_local,after_invocation,after_unregister], emitted only
   after the existing assertions complete. These are source assertion checkpoints,
   not serialized states or stand-alone proof. This child result follows the
   restored MonkeyPatch context and all existing child assertions, before P3 end.

2. **Guard semantic result** exact keys:
   {schema,spec,job_id,role,trial,owner_launch,process_start,inherited_parent_start,
   inherited_domain_pid,python_assertions_enabled,module_origin,source_modules,
   os_threads,torch_profile,torch_profile_unavailable_reason,guard_results}.
   schema=`bac-hardware-core-fork-result-v1`; role cuda_core_inherited_pid_guard;
   source_modules exactly {townlet.exploration.rng_custody:ref,
   test_rng_cuda_admission:ref}, actual inherited module file refs, cross-checked
   against P3 imports and candidate input inventory at both start/end.
   inherited_parent_start is the actual enclosing spawn start, never its parent.
   inherited_domain_pid equals that start PID and actual guard PPID; module_origin,
   os_threads, Torch-null/reason and exact guard_results retain values above.
   Each guard result exact keys are exception_class,diagnostic,lock_acquire_calls,
   owner_lock_acquire_calls,cuda_touch_calls,body_calls,state_unchanged.
   Python flag samples builtin __debug__, not Torch. P3 guard recording uses only
   its accepted no-Torch branch with identity/protocol preloaded BEFORE fork;
   inability to maintain the no-import/no-Torch path leaves this role UNRUN.

3. **Guard acknowledgement and parent observation.** The pipe acknowledgement
   becomes exact {trial,pid,ppid,result,process_start,process_end,message}, refs
   replacing the old identity digest. Parent observes/waits and writes exact
   {schema,spec,job_id,trial,role,parent_start,owner_launch,fork_pid,waitpid_pid,
   wait_status,exit_code,acknowledgement,parent_os_threads_before_fork} with schema
   `bac-hardware-core-fork-observation-v1`; acknowledgement is the exact decoded
   object received, not reconstructed from files. Existing normal Linux status0,
   exit0, task-count1 and PID/PPID ancestry checks persist. P3 end is recorded only
   after guard assertions/result emission and before pipe write/_exit. A successful
   parent wait is mandatory after that end. P3 end alone is not termination proof.
   Exact <=4096 pipe cap must be verified after adopting canonical output paths;
   if references exceed it, implementation needs an explicit finite cap decision,
   never truncation or changed meaning. Existing owned cleanup remains mandatory.

4. **Spawn queue acknowledgement** becomes exact
   {case,role,pid,ppid,message,result,process_start,process_end}; result is the
   child-result ref. It is emitted after child semantic result and actual P3 end.
   The parent checks the actual queue object, Process.pid, PPID, exact source and
   start/end identity; it never backfills a missing start/end on crash.

5. **Final parent payload**, the sole core obligation payload, exact keys:
   {schema,spec,job_id,case,role,parent_start,owner_launch,process_pid,exitcode,
   acknowledgement,parent_rng_assertion,assertion_source}.
   schema=`bac-hardware-core-result-v1`; parent_rng_assertion exactly
   {kind:source-assertion-only,checkpoint:after_child_cleanup,
   function:assert_ambient_unchanged,channels:[python,numpy,torch_cpu]}.
   assertion_source is the actual current core test ref. This payload is emitted
   exclusively AFTER existing parent cleanup, healthy-domain and RNG assertions.
   PID/exitcode are retained from actual Process BEFORE process.close; retaining
   them is new plumbing, not an invented runtime observation. acknowledgement is
   the actual queue object. Parent start links to the real process running this
   test. P3 completion later lists this payload, real parent end and actual pytest
   setup/call/teardown reports; P4 requires all pass and no skip/xfail. P5 may only
   accept assertion-only RNG/poison proof once the exact source/checkpoint custody
   has independent qualification, never from the checkpoint string alone.

Explicit proposed paths are fixed by the adopted owner_contract referenced in
owner launch, not discovered by directory adjacency. Proposed basename vocabulary is
core-child-ROLE.json, core-result-ROLE.json, core-fork-result-TRIAL.json and
core-fork-observation-TRIAL.json under the exact sealed job.output. P3 generated
start/end/raw/source paths are returned actual refs; parent may not guess their
process IDs. Every referenced result, launch, process/raw/source and pytest report
must enter P0 completion inventory; absence, unconsumed extra strict records,
unexpected phase records and undeclared children refuse. No runtime output may be
added to candidate inputs to create a self-authentication cycle.

## Phase pair: explicit subjects, no receipt/path inference

New wrapper exact keys {schema,spec,job_id,obligation_id,subjects}, schema
`bac-hardware-core-phase-pair-v1`. subjects is exactly two objects in order:
{case:invocation_phase_reference,spec:ref,attempt_id:id,job_id:id,strict_receipt:ref}
and {case:invocation_phase_failure,spec:ref,attempt_id:id,job_id:id,strict_receipt:ref}.
P0 related_attempts equals these two spec refs in this order. Subject specs and
attempt IDs are distinct; each has exactly one corresponding phase job, separate
job.output, and explicit strict_receipt. No adjacent receipt search, supplied
generic status, or old verifier spec translation is accepted. Wrapper's own
spec/job/obligation bind the separately declared pair obligation, not a fabricated
third execution of either test.

Proposed standalone strict receipt, pending joint P5/P4 adoption, exact keys:
{schema,spec,job_id,obligation_id,validator,validator_dependencies,contract,
witness_schema,documents,result,validation_identity,validated_at} with schema
`bac-hardware-strict-child-receipt-v1`. validator/contract/witness_schema are pinned
refs; validator_dependencies exact finite refs; documents exact consumed ref set;
result the P5 v2 proposed strict-validation-result object; validation_identity is
actual validation process identity, validated_at actual UTC. These provenance
fields are verified as observations; semantics must be recomputed from referenced
bytes using the accepted fixed pure P5 function, then recursively compared with
exact types to result. Re-execution cannot recreate the prior validator PID/time;
it checks their recorded authority/custody separately, never fabricates equality.
This is strict-component proof, not a P4/common/hardware PASS receipt.

Each phase subject is individually recomputed/strict-qualified without a phase-pair
obligation among its own prerequisites. The pair then checks equality of actual
source root/input inventory/module refs, devices, exception labels and observed
synchronize_events; complementary completion null/True, exact case binding and
separate current start/end/source chain remain mandatory. Events are observed
vectors, not a prescribed invented tail. Duplicate/swapped subjects, identical
attempts, changed roots/source/events, missing/extra phase payloads, tampered
receipts, coherent rehash mutations and bool/int substitutions refuse. Numeric
PIDs may repeat in independent sequential subjects but complete P3 identities and
ancestor linkage must remain actual. The pair wrapper names receipt refs without
claiming authority from their names or digests.

## Owner boundaries and finite later edit proposal

Core owner owns the two exact core test parent/child targets, guard pipe/lifecycle,
assertion retention and new semantic records. Bootstrap/P3 owner owns replacing
old synthetic-worker identity bootstrap, the owner-launch/context/environment
contract, actual P3 emission and no-Torch preload feasibility. P5 owns strict
schemas, parser/correlations, individual receipts and phase comparison; P4 owns
common custody/report/end validation and case-validator receipt publication. P2
owns actual job argv/env launch and terminal waits, not inner child assertions.
Root owns source freeze/grants, accepted contracts, role counts, CPU bounds and
exact import/input inventory. No owner may infer another's authority from JSON.

Proposed AFTER C1 freeze release only: core edit packet one existing body
test_rng_cuda_admission.py, current2883, maximum3200 lines, plus one new inert
protocol test body at root-chosen explicit path maximum650; total3850, two edited
bodies. The shared bootstrap helper changes belong to its separately allocated
owner, not this packet; P3/P0/verifier/production bodies remain opaque dependencies.
If actual integration cannot fit these caps or requires another helper body, stop
for root reslice. Proposed verification is finite inert protocol mutants plus
later separately admitted exact16 core child jobs/three guard trials/two phase
subjects under root custody and independent qualification; no execution is granted
by this document. Real CUDA six-group controls remain separately required/UNRUN.
