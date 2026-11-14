# P3 delegated identity interface v3 — root approved semantics

This replaces only v2 authority/transport and dynamic lifecycle linkage; all other
v2 observations/environment restrictions remain required. v2 is read with these
explicit superseding definitions, not implemented as an alternate schema.

Static policy exact keys (JSON):
{schema:bac-hardware-identity-policy-v1, spec_path:P0 path, command_path:P0 path,
runtime_path:P0 path, job_id:P0 id, role_id:P0 id,
required_imports:[v2 phase-specific import], worker_roles:[P0 id],
environment_delta:{common:P0 env,worker:P0 env}}.
Policy contains no spec/command/grant/runtime digest references. command_path and
runtime_path must equal job.output/command.json and job.output/runtime-context.json.
CLI options are --bac-identity-policy PATH --bac-identity-policy-sha256 SHA; exactly
one occurrence each in job.argv, unambiguous separate argv elements. P2 hashes and
validates policy against spec/job before launch. The policy is outside candidate
inputs (otherwise grant→inputs→policy could cause indirect future-ref cycles).

P2 exclusively writes job.output/runtime-context.json BEFORE spawning job, exact:
{schema:bac-hardware-identity-runtime-v1, spec:P0 ref, command:P0 ref,
trusted_grant:P0 ref, policy:P0 ref, runner_identity:P0 identity,
runner_source_start:P0 ref}.
runner_source_start is P2's actual prelaunch attempt-level source-witness (not an
attempt-start wrapper); its process_identity must equal runner_identity. Policy
known paths/spec job/command/grant/source-witness bindings all match exactly.
P3 validates live actual PPID identity equals runner_identity before controller
start and end, including start token/host/boot. Runner death/reparenting refuses
final witness. Descriptor/spec/command/policy references are rechecked every phase.
Root has explicitly delegated exact-spec authority to P2 run(spec_path) and its
exclusive descriptor under root no-writer custody. This is process/file custody,
not proof of authorship from text/hashes. Unknown adjacent files are never anchors.

Acyclic construction order:
1. finalized tool bytes + inert/actual candidate input bytes + known output paths;
2. static policy (only prior refs: required import files); then final argv pins policy;
3. CPU bounds pin argv/env/source; source grant pins bounds/allocation/input refs;
4. source-freeze/candidate/environment/admission/spec bind grant and final argv;
5. P2 writes command + prelaunch source witness; then runtime descriptor;
6. actual process start/source/raw/lifecycle/end/completion records.
No object points back to a later object's digest. A static policy in candidate
inventory is forbidden here; future inputs/grant/argv digests in policy reject.

Runtime record_process context exact v2 keys plus policy:[P0 ref] and runtime:[P0 ref],
both length0 or both length1. CLI-derived context uses each length1, validates
context static fields equal policy, exact runtime refs, and root grant binding.
Direct owner API contexts use both empty and explicit trusted_grant authority;
only separately accepted owner integration may supply these. Direct invocation
is not a generic route for P2 completion acceptance; P2/P4 require policy/runtime
provenance for job controller and workers.

Initial CLI controller context derives spec,command,trusted_grant from descriptor;
static context fields from policy; parent_start/replacement_start/lifecycle empty;
worker_identity null. Controller creates actual start before configuring workers.

Lifecycle exact schema is v2 shape plus prior_lifecycle:[P0 ref] length0/1.
Initial configure has prior_lifecycle=[],predecessor_start=[],process_start=[].
Down has prior_lifecycle=[configure ref], process_start=[actual worker start],
predecessor_start equal configure predecessor; error is actual down error text
(empty on normal down). Replacement configure has prior_lifecycle=[failed down],
predecessor_start=[failed down.process_start[0]], process_start=[] and retains role.
Controller queues failed-down records, chooses oldest queue item deterministically;
actual gateway identity plus unique start full identity remove label ambiguity.
Worker derived context replaces ONLY role_id,parent_start=[controller start],
replacement_start=configure.predecessor_start,lifecycle=[configure ref],
worker_identity=actual workerinput's four base fields. Other base fields are exact.
Worker verifies configure controller/source/role/identity and predecessor chain.
P4 verifies cardinalities/limits and missing end; P3 never fabricates end on crash.

Full worker env key spellings:
PYTEST_XDIST_WORKER=workerid; PYTEST_XDIST_WORKER_COUNT=str(workercount);
PYTEST_XDIST_TESTRUNUID=testrunuid. Other accepted additions only explicit policy
common {PYTEST_VERSION,LC_CTYPE} and worker {COLUMNS,LINES}, measured in v2/v3
probe artifacts. Entire actual map must equal base+accepted additions, with no
base overrides. Raw observation exact v2 fields and fact-provenance linkage retained.
P2 validates CLI policy/runtime/raw identity/environment correspondence before
orchestration success; P4 owns full semantic lifecycle/strict child qualification.
