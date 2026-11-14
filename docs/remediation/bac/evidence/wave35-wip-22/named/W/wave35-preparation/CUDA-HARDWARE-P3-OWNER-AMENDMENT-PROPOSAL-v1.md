# P3 owner-process amendment proposal v1

Status: one metadata-only design for independent root review. No implementation,
imports, tests or source changes are authorized by this document. Existing P0/P2/
P3 adoption, C1 source freeze and historical bytes remain intact. This supersedes
the provisional owner transport suggestions in the bootstrap supplier capsule;
it is not an alternate accepted transport or compatibility adapter.

## Decision and scope

Implement one current owner-launch protocol in the existing P3 module, with a
prepared no-import execution path for actual fork guards. Keep P0 process/source/
job-evidence schemas and actual child source verification unchanged. Separate
Python assertions from Torch anomaly mode. Authorize the full inherited pytest
phase/worker environment through a causal parent launch, not an environment
whitelist, parent-generated child identity or rewritten job specification.

The selected fork path performs its OWN read-only Git HEAD/index checks, own
source/import hashes and own process/ancestry observations. Parent preparation
validates only immutable input declarations and preloads machinery. It never
supplies a substitute child's PID, start time, observed HEAD/tree or final witness.
No inherited-source exception is proposed. A child unable to make an observation
refuses; the corresponding mandatory owner obligation remains unqualified.

Counted inspection remains five bodies / 2,723 lines:
- historical bac_source_identity.py 60;
- adopted bac_hardware_protocol_v1.py 520;
- adopted bac_hardware_identity_v1.py 611;
- its test_bac_hardware_identity_v1.py 534;
- supplied test_world_rng_bootstrap.py 998.
Only the existing identity and test bodies are proposed for edits in this packet.
Projected ceilings are identity 1,100 + tests 1,200 + unchanged 1,578 = 3,878 lines,
within 5,000 and five files. Excluding the bootstrap supplier body, the original
four-body P3 packet remains at most 2,880/3,200. No extra helper/test/conftest body
or production/producer edit is included. P2/P4 consumer edits require their own
finite grants; source producer changes wait for C1 release and owner packets.

## Immutable baselines and supplier facts

- P0: adc8efeba368998e2e875a60c54ed3338a5ad2aa7daa710b7609e9ed2119de3c;
  interface-contract-v4 and schema-inventory-v2 remain the transport authority.
- P3 source: 938d44339e6c0fdc5b7763eb2b33031bf3794a66e97064cf3601e7b3dbf9b445;
  tests: 5cb82462041e95dec1bd617cc05b4dd76988400611ee0ae3297038d95e8c11c7;
  root-adoption-v1: d93c6db06f4411ff7d4eef909b1b440104f0c4f98187cdd3cf3c4b159decd7e8.
- P2 interface-contract-v2: 9c7b4e37f07014f99237b9f6ae5f70bc70fb79eb67639779c534af17a0aeb43e;
  root-adoption-v1: 6a2d6f1807a0557bca33ebd03f642e20804df381a2d7892a1872dbedc61b9b43.
  Its current accepted correspondence rejects arbitrary owner-child contexts;
  this design does not claim the adopted runner already implements this extension.
- P4 interface-contract-v1 requires actual P3 process/source identity correspondence,
  exact raw/context/env/role/report/lifecycle bindings and immutable receipts.
  Required P5/app/hardware dependencies remain unimplemented/unrun in that interface.
- Bootstrap supplier v1 identifies Python __debug__ as the existing strict debug
  witness; it is not torch.is_anomaly_enabled. Direct/recurrent/producer suppliers
  confirm spawn from the actual test call, no env rewrite, and intra-op=1/inter-op=5.
  None establishes where inter-op=5 is set. The recorder must not set it.
- Core supplier requires actual fork guards, no import/Torch/NumPy/Queue operations,
  no inherited-scope unwind, three exact trials/actions and original pipe/wait
  observations. P3's earlier synthetic fork test did not prove the no-import rule.

## Public operations and authority

Keep record_process(context,phase) for actual controller/worker/spawn/work roles.
Add these operations in the same P3 body (new APIs, not existing behavior):

1. current_process_context() -> {context,start} or None. None means no configured
   current qualification process, never acceptance. A recorded active context is
   returned only when its full actual PID/start/host/boot matches the caller.
   Maintain a per-process registry after successful start emission for pytest AND
   direct owner children, so a core spawn child can itself launch a fork guard.
   Inherited registry entries cannot impersonate the parent after fork.
2. prepare_owner_launch(parent_context,parent_start,owner_contract,case_id,
   child_role_id,instance_id,start_method) -> OwnerLaunch. This actual parent-only
   operation emits the immutable launch below and returns its reference plus an
   exact derived child context. For fork only it also returns an opaque in-memory
   ForkHandle. It validates the current process registry and all root/spec/contract/
   phase/source bindings, samples actual parent facts, and makes no RNG draws.
3. record_fork_process(handle,phase) -> P0 process reference. It accepts only a
   handle issued by this module in the actual live parent and inherited by fork;
   copied/unpickled/arbitrary handles refuse. It measures the caller itself.
   Ordinary record_process rejects fork-guard entry and directs source owners to
   this required prepared API; it never falls back to an import-capable path.

The configured P3 plugin and its existing sealed --bac-identity-policy/sha256
argv provide activation. No new environment marker or future context digest is
needed. Producer helpers may observe the already-loaded plugin's public current
context; absence is ordinary unqualified testing. Any attempted qualified emission
without active context refuses, and retired BAC_QUAL_* transport is not accepted.
No historical helper invocation, schema dispatcher or adapter remains in the
upgraded strict qualification path.

A direct owner launch is authorized only by an exact selected
spec.job.obligation.contract. Parse that P0 case-contract and require case_id,
role/config and obligation kind to match the job and actual launch. Source-owned
Process/fork observations remain additional P5 proof, not caller-supplied trust
booleans. Root's exact-spec authority and no-writer interval remain external.

## Exact owner-launch and child derivation

Every field is required; wrong exact types, unknown fields and duplicate IDs
refuse. All refs are normal P0 path/bytes/SHA references.

| Field | Exact type / binding |
|---|---|
| schema | literal bac-hardware-owner-launch-v1 |
| spec, command | parent context's exact P0 refs |
| owner_contract | selected job obligation's exact parsed P0 case-contract ref |
| parent_process | this actual parent's P3 start ref |
| source_witness | fresh actual source-witness from this same parent |
| parent_identity | P0 identity sampled now, equal parent_process.identity |
| parent_argv | actual /proc/self/cmdline text array |
| case_id | exact selected node ID, independently supplied by actual pytest request/owner case binding |
| pytest_phase | literal call for currently supplied launch sites |
| child_role_id | exact admitted role ID/config, never an inferred worker label |
| instance_id | unique P0 id in job output; no pre-guessed PID or random draw |
| start_method | spawn or fork, tied to actual source-owned Process/context or os.fork observation |
| environment | entire actual parent os.environ at the launch cut |
| python_assertions_enabled | actual __debug__ bool; strict qualification requires True |
| inherited_imports | unique actual loaded named-reference list; no forced child imports |
| module_names_sha256 | SHA256 of ASCII json.dumps(sorted(sys.modules), ensure_ascii=True, separators=(',',':')) |
| at, monotonic_ns | actual parent UTC and monotonic observations |

Write owner-launch-{instance_id}.json exclusively beneath the exact job.output.
The parent passes the produced child context as an explicit Process argument; a
fork branch retains the returned handle. The launch contains no future child or
end reference and therefore introduces no hash cycle.

Child context retains the current exact context field set. Copy schema, spec,
command, trusted_grant, job_id, required_imports, worker_roles, environment_delta
from the authenticated parent's raw context. Set role_id=launch.child_role_id,
parent_start=[launch.parent_process], lifecycle=[launch_ref], replacement_start=[],
worker_identity=None, policy=[], runtime=[]. P3/P2/P4 independently require this
exact derivation and owner contract. Follow parent links to the original delegated
job controller; empty policy/runtime alone never authorizes a direct context.

Parent identity is always the actual immediate launcher: worker if worker-launched,
core spawn child if it forks, controller only when it actually launches. The child
samples its own PID/PPID/start/host/boot/cwd/interpreter/argv/imports. A fork child
also matches actual inherited argv and module snapshot to its launch; a spawned
child records its different actual multiprocessing argv. P5 retains actual
Process.pid/queue/pipe/wait/start-method correlations. No guess normalizes these
into parent pytest argv.

## Full environment derivation, including nested launches

Base job.environment must not pre-authorize PYTEST_CURRENT_TEST or the three
PYTEST_XDIST_* instance keys. Existing common/worker framework additions retain
the adopted exact policy and actual-workerinput/lifecycle rules.

For a pytest parent, the launch environment must equal its authorized P3 start
map plus exactly PYTEST_CURRENT_TEST=case_id + ' (call)'. Independently bind case_id
to the selected owner contract and real request. For an already-running owner
child, its start environment already contains that phase key: require exact full
map equality and the same inherited case/phase; do not add, replace or infer a
new case. This permits core child -> fork guard without pretending it is pytest.

Child start and end environments must equal launch.environment exactly. Inherited
PYTEST_XDIST_WORKER, PYTEST_XDIST_WORKER_COUNT and PYTEST_XDIST_TESTRUNUID retain
parent values and are accepted only through the authenticated parent lineage;
they never change the child's own role to worker. No deletion, cleanup, projection,
base override, arbitrary key addition or independent child whitelist is allowed.

Root must explicitly seal observed startup values such as COLUMNS/LINES and
applicable locale/version when needed, removing duplicate policy additions.
Unexpected startup differences fail closed; no guessed compatibility allowances.
Current supplied sites are call-only; a future setup/teardown launch requires its
own source-backed protocol amendment, not a silent expansion of this enum.

## Python debug and Torch anomaly are different observations

Replace the current private raw schema with one current
bac-hardware-process-observation-v2; new current consumers reject raw v1.
Retain all existing raw fields, and require these additions:
- python_debug: actual bool __debug__;
- python_optimize: actual uint sys.flags.optimize;
- torch_anomaly: P0 observed(bool) shape (measured bool/empty reason, or unavailable
  null/exact no-call reason); never self-referential provenance;
- source_method: literal direct-git;
- recorder_mode: ordinary or fork-guard;
- module_names_before_sha256 and module_names_after_sha256: actual module-name
  snapshots using the launch's encoding rule. Equality is required for fork.

For qualification require python_debug=True and python_optimize=0. For nonfork
processes P0 process.debug is a measured Python-debug fact, compared to role.debug,
with provenance pointing to raw v2. This fact needs no Torch import/call even for
uninitialized roles. Current root role profiles/CPU bounds must declare the actual
Python value; old anomaly-based profile inputs are not rerun as current evidence.

For guard roles P0's existing invariant remains: intra_op/inter_op/debug are
unavailable with reasons. Raw v2 and the strict owner payload independently retain
actual Python debug/optimization values; there is no Torch debug getter.

Work roles with already-loaded Torch measure intra/inter-op through existing
getters and independently observe is_anomaly_enabled into raw.torch_anomaly.
False is valid and must not fail role.debug=True. Observer/uninitialized/guard
roles never call this getter; anomaly is unavailable with the exact reason.
Torch absence at work START remains truthful; work END still requires the
mandatory actual thread configuration. Preserve existing CUDA marker/no-init
rules and all no-RNG/no-setter constraints. Identity never sets either thread
count, anomaly mode or any RNG/device state.

## Prepared fork recorder: actual source, zero forbidden effects

First executable RED must run the currently frozen, preloaded recorder under the
strict traps and retain the exact failing operation; preloading is not assumed to
prove absence of imports. The implementation target is a deliberately narrow
prepared kernel, not a weaker observation schema.

Parent preparation performs full P0/spec/private JSON parsing and validation,
resolves immutable inputs, converts grant/freeze UTC bounds to numeric values,
and preloads exact file hashing, JSON primitive encoding, proc/clock and read-only
Git launch machinery. It validates source once itself, then releases its metadata
flock before forking. It builds a private immutable handle of those declarations
and root-bound references; no future child observations are stored in it.

The fork child does NOT call generic recursive validators/date parsers or decode
untrusted JSON. It rehashes EVERY metadata/tool/dependency/source reference that
was parsed into its plan through the adopted no-follow reference algorithm and
compares exact bytes; changed authority/namespace/input files refuse. No prior
validation is trusted after a reference mismatch. Later P2/P4 still perform full
P0 and private-schema validation on the emitted bytes.

The child then independently:
1. samples actual process/parent identity, interpreter/cwd/argv, full env, clock,
   Python flags, inherited module origins and OS task count;
2. checks actual live parent identity, launch/module/role bindings, single-task
   guard requirement and active numeric root/freeze intervals;
3. obtains the existing cooperative index lock via a fresh no-follow regular-file
   descriptor (never an inherited held lock);
4. runs actual `git rev-parse HEAD` and
   `git diff-index --cached --quiet <candidate.tree> --` in authorized_root, with
   actual exit/output observations. The chosen kernel uses prebound POSIX spawn,
   pipe/poll/read/wait primitives and already-loaded encoding/hash routines; no
   Python import or shell. The Git subprocess stays in the owned job process group
   and existing timeout/termination custody; it does not become a role substitute;
5. hashes actual source files in fixed P1 category order and actual inherited
   imports, rechecks namespace/reference identity and freeze interval, then emits
   its OWN P0 source-witness with its OWN process_identity and actual queried
   head/tree correspondence. No parent logical source value is relabeled as an
   observation by the child;
6. writes exclusive source/raw/process records using a prebound primitive-only
   JSON encoder and no-follow output descriptors, samples module-name map again,
   and refuses any import-map change. No generic __str__/default serializer hook.

Start is emitted before strict actions. End follows actual guard observations and
checks, with actual elapsed monotonic time; end's timestamp follows its final
source sample. Owner pipe output references actual child records and preserves
all 4/7/5-action trial/error counters. The owner branch terminates with its existing
os._exit discipline, never unwinding an inherited owner context. No Queue,
Torch/NumPy API, RNG getter/draw/setter, thread setter or device query is called.
Native read-only Git subprocesses are explicitly part of actual source sampling;
this is not an inherited-source exemption or a new application worker.

Strict no-import qualification traps EVERY builtins.__import__ call, including
already-loaded modules, and importlib entrypoints; verifies the module map and
all Torch/NumPy/Queue effect sentinels; and checks the complete start + end path.
Hashes alone are not offered as proof that a transient import did not happen.
The trap results plus pinned implementation/interpreter/dependencies establish
that property for the exact qualified path. Missing/end-failed evidence stays
incomplete. Any unavoidable forbidden operation is a concrete failed gate for
root, never a reason to silently inherit source facts or weaken the constraint.

## Consumer changes and acyclic construction

P0: no source/schema mutation. process.debug's semantic definition is corrected
in consumer metadata; guard unavailable constraints and all source invariants stay.

P2 (separate bounded amendment): recognize raw v2, independently bind Python/anomaly
facts, and accept direct child contexts only through the new closed owner-launch
lineage. Preserve exact source/process identity, refs/times, actual full env,
runner terminal/log ownership, resource accounting, inherited leases and final
inventory. Do not invoke P3 as an acceptance oracle or fabricate missing records.

P4 (separate bounded amendment): independently parse owner-launch/raw v2, rederive
env/contexts, validate parent ancestry/source and report/case chronology, and
reconcile guard Python flags with unavailable P0 runtime slots. P5 independently
checks strict semantic/Process/queue/pipe/wait/phase receipts. Unknown owner or
old raw schemas refuse; missing strict proofs remain unsatisfied/unrun.

Construction order remains acyclic: frozen code/input/witness-schema/validator
bytes -> static policy -> exact argv/env/role CPU bounds -> source grant/freeze/
candidate/admission/spec -> runner command/runtime -> actual parent process/raw/
source -> owner launch -> actual child start/source/raw/end -> owner terminal
payload and actual pytest reports -> obligation envelope/strict receipts. No
owner launch or current child context digest is placed into earlier argv/env.
Parent strict terminal payload is written after final RNG/currentness assertions;
its later report binding occurs only after that real phase report exists.

## Executable adversarial acceptance within the two P3 files

Every new behavior requires a retained exact-source RED before mutation, then
focused GREEN and the bounded whole P3 suite. No new helper body, source checkout,
Git init/write, application import or real Torch/CUDA operation is permitted.

| Proposed test | Observable gate |
|---|---|
| test_python_debug_is_not_torch_anomaly | Python debug True + anomaly False records both truthfully; no anomaly setter |
| test_optimized_python_cannot_qualify | actual pinned interpreter -O subprocess refuses, even with mocked anomaly True |
| test_owner_launch_from_actual_worker | real inert pytest/xdist parent launches real spawn child; immediate parent identity and all worker/phase env keys preserved |
| test_nested_owner_fork_parent_identity | actual spawn child launches actual fork guard; parent_start names the spawn child, not pytest |
| test_owner_environment_mutations | case/phase mismatch, extra/deleted/changed key, wrong worker UID/count, role spoof and stale launch all refuse |
| test_owner_contract_and_reference_mutations | wrong contract/spec/grant/parent/start token/instance and changed raw/source/namespace refs refuse |
| test_preloaded_fork_recorder_zero_imports | import/Torch/NumPy/Queue traps remain zero over actual start/end, single task, actual child Git/source queries and exclusive records |
| test_fork_source_is_not_parent_replay | mutate inert source/metadata after preparation; change actual read-only Git outcome; child refuses despite valid earlier parent witness |
| test_fork_reparent_and_missing_end | actual reparenting refuses end; killed/interrupted child retains start only; no parent-authored completion |
| test_fork_no_rng_and_no_unwind | parent before/after RNG state unchanged with inert sentinels; pipe result and os._exit path preserve inherited scopes |
| test_new_raw_schema_exactness | old/extra/missing fields and cross-wired anomaly/debug/source provenance reject in updated consumers |
| test_owner_completion_integration | real inert controller/worker/spawn/fork records plus report/launch refs reach closed completion; P2 actual wait and P4/P5 remain independently required |

The source sampler test uses inert candidate files and read-only commands against
an explicitly root-supplied existing Git identity; root supplies current HEAD/tree
metadata if needed. No test repository is initialized and no executable source is
copied. A subprocess double alone cannot satisfy the final zero-import/direct-Git
acceptance; actual local subprocess execution under the traps is mandatory.
Actual producer/application and hardware suites are separate later gates.

## Finite external fields still required before implementation/integration

These are concrete owner inputs, not permission for further body reads:
1. Root/owners must supply source-owned prework thread setup for exact role
   profiles: where intra-op=1/inter-op=5 is established BEFORE the qualification
   cut, measured in each actual child, with failure behavior. Existing suppliers
   establish assertions but not inter-op setup. A future 16-worker host default
   cannot be assumed. Recorder setters or weaker assertions are forbidden.
2. Owners/P5 finalize exact case-role/start-method and loaded-module alias/ref
   inventories, safe pre/post-patch emission cuts, and unchanged strict payload/
   RNG/phase semantics. Replay/recurrent and flat/PER observed aliases are supplier
   facts; no test module name is guessed by P3. Guard trial IDs/actions stay owned.
3. P2/P4 confirm their finite corresponding schema/environment/debug changes and
   source lifetime checks; their adopted current code stays frozen until separately
   authorized. P2 supplied its exact source correspondence above; P4/P5 requests
   are outstanding where not already specified by their interface metadata.
4. Root supplies the immutable executable/interpreter/environment and read-only Git
   identity used for inert fork qualification, plus any exact existing resource
   bound updates needed for this sampler. No new server/access/install is implied.

Root can review this single design now. These fields must be pinned before the
relevant execution/owner integration, but they do not require speculative variants
or expansion of this proposal. No current gate is waived, and no source/hardware
qualification is claimed by the design document.
