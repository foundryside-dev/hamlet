# P4/P5 finite owner contract v1

Status: concrete design for independent root review, not implementation or
adoption. This linked contract preserves the frozen supplier capsules and selects
one current transport. No runtime, imports, source edits, Git/index operations,
copies, branches, worktrees or hardware execution occurred. No implementation
body was read: the optional P4/P0 three-body allowance was not needed. All source
facts below are attributed to the exact capsules in the input inventory.

## Authority and current implementation

The adjacent `../evidence-management/hardware-verifier-p4/owner-contract-preparation/`
inventory pins the metadata consumed. P3 interface-v5 and its root adoption
supersede older capsule statements that P3 owner APIs remain proposals. P3 now
provides `current_process_context`, `prepare_owner_launch`, `record_process` and
`record_fork_process`, current raw-v2, exclusive claims, sampler and emission
records. This is bounded producer-transport adoption only. Source-qualified APP
instrumentation, inter-op=5 setup, P4/P5 acceptance and hardware remain absent.

Adopted P4 public API is `verify(spec_path: str, job_id: str, destination: str)
-> dict`. Its implemented fixed validator is `p4-common-v1`, internal
`common_validation`, accepting only process-custody/source-freeze/required-cases
with cpu/cpu-standin evidence. It has no P5 import or strict validator. Its
root-adopted source hash is
`e72330bcffc2942a2d908a22b5e3471e702d744f54282314c6bccc4afc2c9d81`;
this is metadata provenance, not a new live source inspection. Its old protocol
dependency was 520 lines; the current adopted P0 is 526 lines/hash
`e4f31eacb0e4499655a19ec91a4f5618a7b2ad3f4090e7ed068816b311e00860`.
The next freeze must pin current exact dependencies rather than reuse that old
dependency declaration.

P5 `validate_child_obligation(subject: dict) -> dict` is genuinely unimplemented.
There are no actual P5 implementation/receipt hashes to supply. Historical
`verify_bac_replay_spawn_identity.py` is not an implementation of this interface.
No adapter, old/new schema autodetection, inferred success or fake P2 validator
fills that gap. P2 Task 4 full-chain qualification stays blocked; independently
authorized P2 raw-v2 transport/backstop work need not wait for it.

## Fixed P5 integration and document closure

Select the proposed P5 pure-data interface exactly. Subject keys are
`schema,spec,job_id,obligation_id,documents`; schema is
`bac-hardware-strict-validation-subject-v1`. `spec` is an exact P0 reference;
IDs are exact P0 IDs. Each documents member has exactly `reference,content`,
with actual bytes content and a P0 `{path,bytes,sha256}` reference. Recompute
length/hash, reject duplicate paths even with identical bytes, conflicting refs,
duplicate JSON keys, nonfinite numbers and bool-as-int. Unknown keys refuse.

P4/standalone reader applies current P0 schema/live-reference checks first, then
passes the actual bytes. P5 parses the supplied spec, finds the exact job and
obligation and its exact contract/witness-schema/evidence records. No arbitrary
entrypoint, caller flag, status string or supplied callable is authoritative.
The only proposed literal dependency is
`verify_bac_hardware_children_v1.validate_child_obligation`. No dynamic import
by payload/path, filesystem I/O, subprocess, APP/Torch/CUDA/Git or receipt writes
occur inside it. Proposed inventory ID is `p5-strict-v1` with kinds exactly
strict-child-core, strict-child-producer, rng-custody, fork-three-trials,
phase-pair, evidence classes cpu/cpu-standin. Real-CUDA remains unsupported.

The caller constructs documents by a fixed schema-directed traversal from spec,
selected contract/schema and selected obligation-evidence records; phase-pair
also traverses its two explicit subjects. Parsed transport documents include the
selected result/completion/report/start/end/raw/source/launch/claim/sampler/
emission/delegation/grant/policy records needed for the selected checks. Source,
executable, log and other non-JSON file refs are opaque hash-checked leaves, never
guessed to be JSON. The closed finite reference positions are supplied by adopted
P0/P3 schemas and the strict schemas below; no general scan of arbitrary dict
values for path-shaped data. P5 must consume every supplied document exactly
within this traversal (shared references consumed once); reject unconsumed extras.
No source body needs to be present merely because a source reference occurs: its
live-byte authentication belongs to the P0 reader and source-grant custody. P5
still verifies the exact named refs/identity/correlation in parsed evidence.

Return keys remain exactly `schema,obligation_id,verdict,reasons,cases,evidence,
payloads,producer_processes,related_attempts`, schema
`bac-hardware-strict-validation-result-v1`. The verdict is
satisfied/unsatisfied/unrun. Satisfied requires empty reasons and every required
strict check. Unsupported/not yet implemented required semantics return unrun;
well-formed retained failed/incomplete execution is unsatisfied; malformed,
contradictory or missing referenced bytes raise ValueError. Missing obligation
execution can be unrun, never satisfied. All lists derive from exact selected
evidence, not caller copies. This result alone conveys no common/hardware or
root-authority qualification.

## Exact payload locator and enclosing schemas

Use the existing P0 obligation-evidence `payload` reference; never infer a
neighbor path or discover a terminal file through globbing. Its spec/job/
attempt/obligation/kind/contract/validator/case/class/producer_process bindings
must match the selected sealed job. `producer_process` is the actual parent
START which emitted the terminal owner payload, not the child START.
Repeated references shared by different obligations are legal; duplicate evidence
within one obligation is not. Each obligation must cover its exact case set.

For core/replay/producer, this payload is the respective final parent object
described below. For fork-three-trials it is the SAME core final parent payload
for inherited_pid; no extra fork wrapper. For rng-custody choose by the exact
owner case table, never an arbitrary schema switch or inferred prefix. Phase-pair
uses only its explicit pair wrapper. Every schema identifier below is a literal,
not executable JSON Schema; witness-schema declarations pin the one-field schema
identifier as in the built-in common validator. The fixed P5 implementation owns
its complete recursive closed type checks.

| Payload schema | Exact keys / next references |
| --- | --- |
| bac-hardware-core-result-v1 | schema,spec,job_id,case,role,parent_start,owner_launch,process_pid,exitcode,acknowledgement,parent_rng_assertion,assertion_source |
| bac-hardware-replay-result-v1 | same exact keys as core-result-v1 |
| bac-hardware-producer-result-v1 | schema,spec,job_id,case,role,parent_start,owner_launch,parent_baseline,process_pid,exitcode,acknowledgement,before,after,assertion_source,parent_rng_assertion,cleanup |
| bac-hardware-core-phase-pair-v1 | schema,spec,job_id,obligation_id,subjects |

Core/replay acknowledgement exact keys:
`case,role,pid,ppid,message,result,process_start,process_end`.
Producer acknowledgement replaces `result` with `outcome`, retaining the other
seven keys. All are actual received queue objects. `process_pid` and exitcode
come from the real Process before close; successful exitcode is exact int0.
parent_start equals obligation producer_process and the launch's actual parent.
Emit final parent payload only after cleanup and final assertions complete.
Passing setup/call/teardown and parent END are joined later through completion;
no future report reference is embedded in an earlier payload.

Core child result exact keys remain
`schema,spec,job_id,case,role,owner_launch,process_start,python_assertions_enabled,
message,phase,forks,rng_assertion_scopes`, schema
`bac-hardware-core-child-result-v1`. Follow parent acknowledgement.result to it.
`forks` is empty except inherited_pid, where it is exactly three observation
refs in admission/local/invocation order. Phase/scopes/nested typed values are
exactly those in the pinned core supplier; no extra semantic observations are
invented. Replay child result, producer baseline/preflight/outcome, recursive
errors, parent RNG objects and cleanup fieldsets are the closed ones exhaustively
specified by their pinned source-owner capsules. Those fieldsets are selected
unchanged, not left to implementer inference. No bootstrap_poison cases are added
to the established 28-job P5 inventory merely because the shared helper supplier
describes them.

### Required linked correction for guard terminal timing

The old core proposal emits its guard result before P3 END. That cannot contain
the actual END return. Replace that proposal with the following v2 guard-only
schemas. Preserve the historical v1 bytes; new consumers accept only v2 at these
positions. No nonfork owner gains recorder_returns or this timing profile.

Guard terminal schema `bac-hardware-core-fork-result-v2`, exact keys:
`schema,spec,job_id,role,trial,owner_launch,process_start,inherited_parent_start,
inherited_domain_pid,python_assertions_enabled,module_origin,source_modules,
os_threads,torch_profile,torch_profile_unavailable_reason,guard_results,
recorder_returns`.

The first 16 fields preserve the core supplier's exact types/values. In particular
role=cuda_core_inherited_pid_guard; trial is admission/local/invocation;
inherited_parent_start is the actual outer spawn START; inherited_domain_pid is
its PID and actual guard PPID; Python assertions exact True; module_origin is
inherited-loaded-module-objects; source_modules has exactly
townlet.exploration.rng_custody and test_rng_cuda_admission refs; os_threads exact1;
torch_profile null; unavailable reason is exactly
`no Torch calls permitted in fork guard-only process`.
guard_results has exactly the respective 4/7/5 action keys, each with exactly
exception_class,diagnostic,lock_acquire_calls,owner_lock_acquire_calls,
cuda_touch_calls,body_calls,state_unchanged. Counts exact int0, unchanged True,
class builtins.RuntimeError and diagnostic exactly
`RNG custody cannot be inherited by another process`.

recorder_returns is exactly two objects, start then end, each exact
`phase,process,emission,entry_ns,return_ns`. References are the actual returned P0
process and the hashed fixed P3 emission filename for that actual identity/phase.
Times are nonnegative exact integers in nanoseconds, never booleans. No predicted
ref or P3 prefix clock substitutes for owner return. Both rows belong to the same
actual guard identity/launch/claim; first process equals process_start; second
equals the pipe acknowledgement.process_end.

Guard pipe acknowledgement keeps the exact keys
`trial,pid,ppid,result,process_start,process_end,message`. `result` is this terminal
v2 payload ref. Preserve source-owned message `cuda core inherited pid TRIAL fail
closed`, actual pipe bytes/read, <=4096-byte cap and actual _exit(0). Do not replace
the pipe with Queue or synthesize the received object from files.

Parent observation schema `bac-hardware-core-fork-observation-v2`, exact keys:
`schema,spec,job_id,trial,role,parent_start,owner_launch,fork_pid,waitpid_pid,
wait_status,exit_code,acknowledgement,parent_os_threads_before_fork,parent_custody`.
The first 13 fields preserve the source-owner v1 proposal. parent_custody exact
keys are `launch,child_identity,terminal_payload,acknowledgement_received_ns,
reaped_ns,wait_status`. launch equals owner_launch; child_identity equals both
P3 process identities; terminal_payload equals acknowledgement.result; wait_status
equals the parent's actual outer wait_status. Successful normal Linux raw status
and exit_code are exact int0. fork_pid=waitpid_pid=acknowledgement.pid=child PID;
acknowledgement.ppid=parent_start PID=child PPID. Parent has exactly one OS task
before this os.fork as already required by the source owner.

Thus the exact fork locator is:
`obligation-evidence.payload -> core-result.acknowledgement.result ->
core-child-result.forks[trial_index] -> fork-observation.parent_custody`
and `fork-observation.acknowledgement.result -> fork-result.recorder_returns`.
Cross-check parent_custody.terminal_payload against that exact same result ref.
The observation's parent_start is the outer spawn START, not the pytest parent;
the top-level core result links the pytest parent separately. No filename lookup
is used for this locator. Proposed existing fixed basenames remain
core-result-ROLE.json, core-child-ROLE.json, core-fork-result-TRIAL.json and
core-fork-observation-TRIAL.json under sealed job.output; filenames confer no
authority.

Actual owner order is: preload prepared primitives before fork; bracket START;
execute and check all strict actions; bracket END; hash both returned emission
refs; write terminal v2 guard payload; send actual pipe acknowledgement; _exit.
Take each return sample immediately after its P3 call, before owner emission.
Parent samples immediately after the actual full acknowledgement receipt and
after actual wait/reap, writes observation later. P3 END deliberately precedes
terminal payload write; the latter is covered by later actual pipe/wait and
source-qualified owner execution, not falsely labelled a P3 END observation.
Keep no-import/no-Torch/NumPy/RNG/Queue/no inherited unwind behavior throughout.

### Timing arithmetic and causal coverage

For each phase require entry <= sampler.start <= sampler.end <= emission_end <=
return. Complete call return-entry <=3,000,000,000; sum of both calls
<=6,000,000,000. Both entries and returns are inside launch.monotonic_ns through
launch.sampler_cutoff_ns (the existing absolute 8-second cutoff). END entry >=
START return and follows required strict actions in independently qualified
owner source. Do not use sampler cumulative_ns as complete-call time: it is
only the sum of source-sampling intervals. Emission excludes its own write.

Both parent endpoints >= BOTH returns and <= original owner_deadline_ns with
the source's min(existing 10-second limit, launch deadline). No ack/reap ordering
is required: actual reap-before-ack is legal. Ack at8.1 after actual return7.9
remains eligible; do not enforce ack<=8 or infer return<=8 from ack. Host/boot
and actual immediate ancestry must establish one monotonic clock domain.
Missing call/row/emission/terminal/ack/reap or killed guard cannot qualify.
P4 independently checks correspondence and arithmetic; P5 checks them again with
strict source-qualified Process/os.fork/pipe/wait/action semantics. P2 owns only
its transport/source-stage arithmetic and outer group cleanup, never a parallel
whole-call validator.

P4 must independently implement current P3 raw-v2, launch/claim ancestry,
phase/environment/source/import/module-name/policy/resource/emission checks and
the P2 completion correspondence contract. Owner start/end/raw/launch/claim/
source/sampler/emission/command diagnostics/logs are explicit completion.inventory
members; owner source witnesses also occur in completion.source_witnesses.
All strict result/observation/custody/payload refs are explicit completion
members too. External immutable contracts/grants/policy/dependencies do not become
job outputs. Preserve exact five copied arrays completion->result; result and
seal inventories remain independent later snapshots, never equal to completion.
P5 checks exact selected strict graph membership; P4 checks transport closure.

## Phase pair and receipts

Select the core supplier pair wrapper exactly. subjects has two exact objects
`case,spec,attempt_id,job_id,strict_receipt`, in reference then failure order.
Cases invocation_phase_reference and invocation_phase_failure; distinct spec
refs and attempt IDs, one matching phase job each, separate outputs.
P0 related_attempts equals these two spec refs in order. Each subject is validated
without a phase-pair obligation of its own; reject nested pair recursion. Compare
shared source root/input/module refs, devices [0,1,2], exception labels
[body,synchronization] and actual observed nonempty event vector, with completion
null then exact True. Do not prescribe a tail or forbid numeric PID reuse between
independent subjects. Each subject still needs its own actual complete identity.

Select standalone receipt schema `bac-hardware-strict-child-receipt-v1` with exact
keys `schema,spec,job_id,obligation_id,validator,validator_dependencies,contract,
witness_schema,documents,result,validation_identity,validated_at` as proposed by
the core supplier. documents is the exact consumed reference list, result the
closed strict result above, identity actual observed P0 identity, UTC actual.
`verify_children(spec_path: Path, job_id: str, destination: Path) -> dict` reads
and validates live P0 transport and writes exclusively; it never reports P4/common
or hardware satisfaction. Pair validation recomputes each subject with the SAME
fixed pure function and compares result recursively with exact types. Prior
validator identity/time are authenticated recorded observations, not recomputed
equal to a new PID/time. A prior receipt hash or supplied satisfied string alone
does not establish assertion/source authority.

P4 retains its adopted case-validator receipt fields, selects validator_id
p5-strict-v1 and pins exact P5 source/dependencies, own actual validation identity
and start/end UTC, contract/schema/spec/job/obligation and recomputed lists.
No new receipt authority is invented. Root's external inventory is created only
after exact validator freeze, with literal common/P5 IDs and finite kinds; its
validators entry fields remain id,kinds,validator,dependencies,contracts,
witness_schemas,evidence_classes. It is pinned once in authorized prerequisites.
Common dependency list remains P0; P5 list is exact current P0 (and any actual
fixed source dependency explicitly included in the later freeze, never dynamic).
P4's own freeze additionally pins its literal P5 dependency. Unknown IDs refuse.
Strict/common components remain independently labelled; P0 aggregate custody
stays unsatisfied while any required strict/APP/hardware obligation is incomplete.

## Source-owner case/role/method map

These are attributed static source observations from supplier capsules, not
executions or independent body inspection in this pass. Fixed 28 CPU/control jobs
have zero xdist workers, one actual controller and one spawn child; inherited_pid
adds exactly three fork guards of role cuda_core_inherited_pid_guard. Actual
child argv must be observed, never copied from pytest argv.

| Family | Exact cases / role / actual target and method |
| --- | --- |
| Direct replay | replay_poison / replay_poison / _replay_poison_child(queue), spawn; job replay-poison; node test_replay_rng_custody.py::test_isolated_replay_poison_refuses_all_direct_samplers |
| Recurrent replay | recurrent_replay_poison / recurrent_replay_poison / _scratch_poison_child(queue), spawn; job recurrent-replay-poison; node test_recurrent_replay_rng_custody.py::test_isolated_recurrent_scratch_work_cannot_heal_common_poison |
| Core (16) | bootstrap_failure, runtime_query_failure, local_completion_single, local_completion_multiple_body, local_completion_duplicate_parent, poison_unknown_ready, poison_ready_qualified, poison_ready_healthy_only, operation_body_completion, inherited_pid, invocation_same_error, invocation_child_failure, invocation_parent_failure, invocation_reported_failure, invocation_phase_reference, invocation_phase_failure. Role cuda_core_CASE. Target cuda_core_child(queue,case), except inherited_pid_child(queue,str(tmp_path)); spawn. |
| Flat/PER (10) | flat_local_single, flat_local_distinct, flat_local_same, flat_admitted_single, flat_admitted_same, per_local_single, per_local_distinct, per_local_same, per_admitted_single, per_admitted_same. Role cuda_producer_poison, target _producer_poison_child(case,queue), spawn. |

All nodes are under tests/test_townlet/regressions/bac/. Core node is
test_rng_cuda_admission.py::test_isolated_poison_protocol[CASE], except inherited
test_isolated_inherited_pid_gate_refusal. Core job cuda-core-CASE replaces case
underscores with hyphens. Producer node is
test_replay_cuda_producer.py::test_isolated_producer_poison[CASE]; job
cuda-producer-poison-CASE retains underscores. Single phase/producer subjects have
one-job specs as supplied. Core/replay success messages, producer error schedules,
baseline/error/refusal/quarantine/currentness predicates and exact imports remain
the pinned capsule contracts. No contract is discharged by a new boolean alone.

Admission actions: resolve_cuda,enroll,report_failure,domain_admission.
Local actions: resolve_cuda,complete,completion_failed,report_failure,
domain_local_cuda_access,domain_local_cuda_policy,domain_resolve_local_cuda_record.
Invocation: active_enter,active_exit,active_completion_failed,
completed_completion_failed,domain_device_invocation. Counts remain 4/7/5.

Core and both replay parents have assertion-only Python/NumPy/Torch CPU RNG
checks; no serialized baseline or CUDA/draw-vector proof may be invented.
Core function assert_ambient_unchanged; replay _assert_same_transport (recurrent
alias _same). Their final source assertion checkpoint is after_child_cleanup.
Producer retains actual serialized domain/python/numpy/torch/cuda before/after,
typed equality and _assert_tree_equal checkpoint after_child_join_before_unregister;
domain may legitimately differ but must remain healthy. It does not acquire the
bootstrap helper's next-draw test. Strict acceptance needs independently qualified
exact assertion source and passing call/teardown, not merely checkpoint strings.

Finite remaining source-owner questions, to be answered in owner implementation
capsules rather than guessed here:

1. What exact source-owned startup sets inter-op=5 before child work, and which
   actual source/argv/import record qualifies it? Existing capsules explicitly
   find only getters, not the setter. P3 never sets it.
2. What actual loaded test-module aliases and complete startup environment are
   observed for the sealed owner jobs? Seal exact values; P3's adopted finite
   owner-launch derivation is available, not an arbitrary extra-key whitelist.
3. Can the actual canonical guard reference paths plus acknowledgement stay
   <=4096 bytes with this v2 terminal link? Preserve the cap; do not truncate or
   silently widen. Any necessary finite cap amendment requires concrete bytes.
4. Do prepared primitive clock/hash/encoder/writer cuts preserve zero imports,
   forbidden runtime calls, no unwind and nonperturbation in the actual source
   owner? P3 inert transport qualification cannot answer this for APP code.

These are evidence/implementation gaps, not unresolved enclosing fieldsets or a
request for another speculative planning round. All source assertions/actual
observations must be obtained from separately scoped owners.

## Finite work packages and acceptance matrix

1. **P5 pure semantics and standalone transport.** New
   Q/verify_bac_hardware_children_v1.py and
   Q/test_verify_bac_hardware_children_v1.py; retain historical bodies immutable.
   Implement exact tables/closed schemas/locator above, strict subject/result,
   source-checkpoint correlations, 4/7/5, timing, error/baseline and phase receipt
   recomputation. Proposed source cap1500/test cap2000. With existing historical
   verifier752 + current P0526, four-body total4778 <=4800. No other body/import
   expansion. This replaces the older 3528 new-line allowance with3500 to account
   for current P0. Inert fixtures are labelled synthetic, never APP/HW proof.
2. **P4 current-owner transport and fixed P5 dispatch.** Existing verifier/tests,
   P0 read-only and the frozen P5 source as literal dependency. Proposed four-body
   caps1350+1550+526+1500=4926 <=5000, remeasure before granting. Add independent
   raw-v2/ancestry/emission/source/inventory checks, arithmetic and receipt wiring;
   preserve common/replacement/report semantics. If implementation cannot fit,
   report the concrete cap issue before widening, not silently add helpers.
3. **Owner instrumentation in separately supplied finite slices.** Core inserts
   actual two call brackets and v2 terminal/custody ordering in existing guard;
   replay/producer/bootstrap replace old transport and preserve assertions and
   cleanup. Core supplier cap3200+650=3850; producer2900+650=3550;
   replay two existing bodies<=2000 plus inert tests<=500. Shared bootstrap helper
   has its own owner grant; no P4/P5 grant edits it. Reuse adopted P3 APIs, not old
   fabricated worker identities. Current root APP writer/source freeze governs
   when edits/execution occur; this document does not create another candidate.
4. **Bounded full-chain handoff.** After exact P4/P5 freeze/review and qualified
   owner instrumentation, give P2 Task4 exact implementation/receipt hashes,
   fieldsets/locator and source mapping/status. Execute actual P3->P2->P4->P5 only
   under root source/resource custody. P2 live-Git abrupt-death backstop remains
   separately required. Publish retained attempts and exact dependencies; no
   overlap-summed test counts or inferred package/hardware qualification.

| Required finite test group | Expected result |
| --- | --- |
| Exact closed schemas and locator | Valid synthetic closure passes semantics; missing/extra/duplicate keys, wrong schema, malformed refs, bool times/status, nonfinite/negative values, duplicate/unconsumed docs refuse. |
| Crosswired causal evidence | Reseal wrong case/trial/role/method/parent/full identity/source/launch/claim/raw/emission/return/payload/pipe/ack/reap refs and reject semantically, not just stale digest. |
| Completion boundaries | Missing END, emission, either return row, terminal payload, actual received ack or reap cannot satisfy; END alone and internal prefix labelled complete cannot satisfy. |
| Timing limits | Reject >3 each, >6 sum, >8 return, >10 ack and >10 reap; accept inclusive3/6/8/10, actual7.9 return/8.1 ack, reap-before-ack with both after return; reject cross-host/boot subtraction. |
| Source-owner strict behavior | Exact4/7/5; action omission/extra/error/counter/state mutations reject; original no-import/no-Torch/NumPy/Queue/no-unwind and actual pipe/wait/Process method tested by owner, not launch label. |
| Spawn/parent semantics | Preserve90s joins and empty sampler profile; wrong queue PID/PPID/Process exit, early payload, cleanup or teardown failure, Python -O refuse; anomaly false with Python assertions true remains eligible. |
| RNG and producer | Reject foreign borrowed baseline, changed typed/digest/cache/CUDA state, wrong error identity/order/quarantine/poison/completion markers; source assertion-only families require exact qualified source/report custody. |
| Phase pair | Missing/swapped/duplicate/same-attempt/foreign job or output, changed source/input/event vector, bad null/True type, tampered receipt, recursive pair and extra phase payload refuse; sequential numeric PID reuse is allowed. |
| P4 regression/inventory | Existing common/replacement tests stay valid with current P0; five-array change and owner closure omission reject even if final result/seal later includes bytes; unknown validator ID and forged root inventory refuse. |
| Actual integration | Instrumented positive chain plus late/missing/crosswired rows and abrupt guard death with live Git; inert vector success alone does not qualify this group. |

No tests ran in this planning pass. Actual CUDA is UNRUN; server/16-worker access,
allocation and hardware admission are unknown. All six real-CUDA groups and
other mandatory APP obligations remain required and unsatisfied/unrun. The finite
next step is independent review of these exact bytes, then implementation within
root's existing scoped authority; no additional approval mechanism is proposed.
