# P5 bootstrap / P3 linkage supplier v1

Status: read-only source-factual capsule plus an explicit new API proposal.
Nothing here is implemented or adopted as a replacement protocol. C1 application
source freeze remains active. No source import, test, application/Torch/CUDA/server
execution, Git write, branch, worktree, execution copy or source edit occurred.
Only the newly granted bootstrap body was read; no dependency body was added.

## Scope and unchanged byte identities

R=/workspace/hamlet; Q=/workspace/bac-review-2026-11-01/qualification.
The four earlier P3 bodies total 1,725 lines. This grant adds exactly
R/tests/test_townlet/regressions/bac/test_world_rng_bootstrap.py (998 lines), giving
five counted files / 2,723 lines, below the root's 5,000-line bound.

The following before/after hashes are identical; both observations were made in
this supplier turn. Source bodies were never written.

| Body | Lines | SHA-256 before = after |
|---|---:|---|
| R/tests/test_townlet/regressions/bac/test_world_rng_bootstrap.py | 998 | 452e427b945475e050b35273b6bb44effe3ade6ef96629c4382c2d68591ee727 |
| Q/bac_source_identity.py | 60 | 0a376a6454e317104adc4bce2cdc0d268c216de8c67e91e60623e6df7d31719d |
| Q/bac_hardware_protocol_v1.py | 520 | adc8efeba368998e2e875a60c54ed3338a5ad2aa7daa710b7609e9ed2119de3c |
| Q/bac_hardware_identity_v1.py | 611 | 938d44339e6c0fdc5b7763eb2b33031bf3794a66e97064cf3601e7b3dbf9b445 |
| Q/test_bac_hardware_identity_v1.py | 534 | 5cb82462041e95dec1bd617cc05b4dd76988400611ee0ae3297038d95e8c11c7 |

Inputs: P5 interface-decision-and-owner-requests-v2.md; adopted P3
interface-contract-v2.json, context-contract-v3.md and observation-matrix-v1.md;
P3 root-adoption-v1.json remains intact. This capsule does not expand its bounded
synthetic-tool adoption into source-qualified strict owner integration.

## Facts from the bootstrap body

- Line 49 defines exactly BAC_QUAL_ROOT, BAC_QUAL_SHA, BAC_QUAL_TREE,
  BAC_QUAL_MANIFEST, BAC_QUAL_OUTPUT. _qualification_active (833) tests key
  presence, not nonempty values. No keys means False; all five means True; a
  partial bundle asserts. There is no hardware-v1 activation in this body.
- _child_identity (840) returns False without writing when inactive. When active
  it imports the historical bac_source_identity and invokes its pytest_configure
  with a fabricated pytest workerinput label equal to the supplied role. That
  call is historical transport; it is not an actual xdist-worker identity.
- It reads identity-{role}.json, adds actual os.getpid(), manifest byte hash,
  Python __debug__, torch.get_num_interop_threads(), and resolved import paths
  obtained by actual importlib imports of townlet.exploration.world_curiosity_state,
  rng_custody and rnd. It requires Python debug True, intra-op 1 and inter-op 5,
  rewrites the identity file, then renames it to spawn-identity-{role}.json. The
  helper itself does not set inter-op to 5. The current bootstrap has no source
  that establishes the origin of that setting; do not infer a dependency body.
- The historical helper (previously inspected in the P3 packet) invokes Torch,
  forces intra-op 1, imports application code and calls git write-tree. It must
  not be reused for hardware-v1 or a no-Torch/no-import fork guard. This capsule
  does not execute it. Its old bytes remain a historical evidence object.
- _poison_child (874) selects bootstrap_poison_{setter|cleanup|completion}, calls
  _child_identity before compiling the real selected provider and exercising the
  bootstrap. It installs actual failure injections and undoes them in finally.
  It requires the common RNG domain poisoned, original offside checkpoint bytes
  unchanged, and participating operations to refuse poison. Only then it queues
  ("bootstrap poison {kind} fail closed", actual PID, qualified bool).
- test_fresh_child_bootstrap_poison_fails_common_domain_closed (958) uses
  multiprocessing.get_context("spawn"), Queue, and Process(target=_poison_child,
  args=(queue,kind), name=role). The parent snapshots _ambient before start, joins
  for 90 seconds, demands exit 0, gets the queue tuple with 5-second timeout and
  checks exact message, queued PID == Process.pid and qualified identity.
- Qualified parent emission is exclusive spawn-observation-{role}.json with
  exactly process_pid, queued_pid, exitcode, qualified, message, manifest_sha256.
  It occurs BEFORE final parent domain-currentness/_assert_ambient assertions.
  A future terminal success payload must follow those assertions and bind the
  actual pytest call outcome, not treat this earlier JSON as terminal success.
- Finally, an alive child is terminated and joined, liveness is rejected, queue
  is closed/joined and Process is closed. Parent common-domain poison remains
  False and _assert_ambient(before) is required. Current emission has no end
  witness, host/boot/start token, PPID, actual argv, or P0 process/source references.
- _ambient (67) deep-copies Python and NumPy state and clones Torch CPU RNG state.
  _assert_ambient (80) checks typed equality AND equal next Python/NumPy/Torch CPU
  outputs from independent stateful generators. These are actual assertions,
  not a serialized before/after RNG payload in this body. Do not invent a prior
  source-owned RNG digest schema. _no_rng_or_native_effects (95) wraps the named
  RNG/native constructors and checks an empty observed effect list in its thread.
- This bootstrap file contains no fork target and no os.fork call. Its helper
  cannot establish the separate core owner's three-fork-trial semantics. Its
  CPU-empty-inventory test (807) forbids CUDA queries including is_initialized;
  an identity recorder must not run work getters inside that guarded interval.

## Current P3 facts and mandatory integration gaps

The adopted public API is record_process(context,phase), with phases start/end.
The exact current context fields are schema, spec, command, trusted_grant,
job_id, role_id, required_imports, worker_roles, environment_delta, parent_start,
replacement_start, lifecycle, worker_identity, policy, runtime. Direct owner calls
use empty policy/runtime and explicit trusted_grant; they are not automatically
accepted P2 job evidence. The owner integration contract is still owed.

Current pytest activation is explicit -p bac_hardware_identity_v1 with
--bac-identity-policy ABS_PATH --bac-identity-policy-sha256 SHA, already sealed in
job.argv. Policy precedes final argv/CPU bounds/source grant/spec; P2 writes the
known-path runtime descriptor afterwards. No child context may be hash-pinned
inside the earlier argv: that would recreate the rejected reference cycle.

P3 samples own actual /proc PID/PPID/start token/argv, host/boot, interpreter/cwd,
imports and source files. parent_start must identify the actual live PPID with
matching full identity. A child launched by gwN must therefore name gwN's actual
P3 start, not the job controller's start. Parent records never substitute for
child-produced records. Reparenting prevents a valid end witness.

Two concrete mandatory amendments were identified; adopted P3 bytes are unchanged:

1. The bootstrap's debug witness is Python __debug__, whereas adopted P3's work
   getter maps role.debug to torch.is_anomaly_enabled(). These are not equivalent.
   Preserve Python assertions-enabled True and do not force anomaly detection True.
   Proposed bounded P3 correction: measured work process.debug uses actual
   __debug__; any separately needed Torch anomaly fact must be a separately owned
   field, never the replacement for Python debug. Keep P0 fork debug unavailable
   as its guard schema requires, while the strict owner payload independently
   records actual python_assertions_enabled=__debug__ without a Torch call.
   P3/P4 observation metadata and focused tests require linked requalification.
2. A real pytest child inherits phase and possibly xdist environment. Current P3
   with worker_identity=None expects only job.environment plus declared common
   additions, so PYTEST_CURRENT_TEST and worker dynamic keys refuse. Pretending a
   spawn/fork child is a worker also refuses and would be false role attribution.
   A finite owner-launch derivation is required; no environment clearing,
   projection, arbitrary whitelist, or fabricated child job/environment is valid.

## Proposed single current owner transport — not existing APIs

After root approval and C1 freeze release, replace the obsolete strict producer
identity transport in its owners. Do not add an old/new adapter or run new payloads
through the historical verifier. Ordinary nonqualification tests remain ordinary;
they cannot provide accepted hardware-v1 evidence.

Proposed activation: root seals BAC_HARDWARE_QUALIFICATION=bac-hardware-v1 in the
actual launch environment before CPU bounds/grant/spec, along with the existing
P3 plugin argv. Absent marker means ordinary unqualified tests; a present wrong
value, missing active P3 parent context, or any retired BAC_QUAL_* bundle refuses
qualification. This is a new explicit mode boundary, not compatibility with the
retired transport. No dynamically created context digest is placed in launch env.

Proposed new P3 public APIs (names and behavior need adoption/implementation):
- current_process_context() -> exact {context,start}, returning this actual
  process's configured context and immutable P3 start reference. It must check
  current PID/start against the referenced emitter; inherited state after fork
  cannot impersonate the parent.
- prepare_owner_launch(parent_context, parent_start, owner_contract, case_id,
  child_role_id, instance_id, start_method) -> owner-launch reference. Called by
  the actual launching parent inside the active test call immediately before
  Process.start or os.fork; it validates actual parent/full env/source authority
  and exclusively writes the object below. It performs no work/RNG draw.
- Existing record_process gains an explicitly reviewed owner-launch interpretation
  of lifecycle for admitted spawn-child/work-child/fork-guard roles. Context
  field set and P0 process shape need not change. This interpretation is NOT
  present in adopted P3 today. Its raw/context/parent checks must be updated
  together with P2/P4/P5; adjacent JSON is not an authority source.

Proposed exact owner-launch object, rejecting unknown fields/types:

| Field | Type / meaning |
|---|---|
| schema | literal bac-hardware-owner-launch-v1 |
| spec, command | exact P0 refs from actual parent context |
| owner_contract | exact selected spec.job.obligation.contract ref; parsed contract binds case/role/kind |
| parent_process | actual launching parent's P3 start ref |
| source_witness | fresh read-only source-witness from that same actual parent |
| parent_identity | actual sampled P0 identity, equals parent_process.identity |
| case_id | exact sealed required node ID, independently provided by actual pytest request |
| pytest_phase | literal call for the inspected test-body launch sites |
| child_role_id | exact admitted role ID, matching owner contract; not gateway label |
| instance_id | unique root-policy-compatible P0 id for this launch; not PID guessed before spawn |
| start_method | literal spawn or fork; bootstrap actual current method is spawn |
| environment | complete actual os.environ at parent launch, not a projection |
| python_assertions_enabled | exact actual bool __debug__, required True for strict cases |
| inherited_imports | unique P0 named-reference list from already-loaded modules; no forced child imports |
| at, monotonic_ns | actual parent UTC and monotonic sample |

The immutable destination is owner-launch-{instance_id}.json under job.output;
instance collision refuses. The reference is passed as an explicit Process target
argument, or retained in the pre-fork parent's local state for the fork branch.
No parent can pre-create the child's identity or its end reference.

Exact proposed child-context derivation from the authenticated parent raw context:
copy schema, spec, command, trusted_grant, job_id, required_imports, worker_roles
and environment_delta; set role_id=launch.child_role_id,
parent_start=[launch.parent_process], replacement_start=[], lifecycle=[launch_ref],
worker_identity=None, policy=[], runtime=[]. The caller's trusted_grant is the
same root-authorized exact ref from the parent chain. A child owner contract must
be explicitly accepted; empty policy/runtime never makes an arbitrary caller's
JSON authoritative. No child worker replacement is inferred from this transport.

At start/end the child itself validates the closed launch ref, exact contract,
root/source bindings, actual live parent full identity, admitted role, and actual
complete environment. It emits its own P0 identity/source/raw records. Its actual
/proc argv is recorded independently: multiprocessing spawn/execnet argv is not
copied from pytest job.argv. Work children observe thread settings at permitted
cuts; guard children take the separate no-Torch path. End is emitted only after
owner cleanup/actual assertions at an allowed observation cut; crashes leave
missing end. Queue tuples and parent Process/exit observations must bind the
actual child start/end refs, actual queued PID and instance_id; P5 owns their
strict payload fields and correlations. A later final binding joins the actual
pytest report ref after the phase has completed; it must avoid a future-ref cycle.

## Exact phase environment rule

The inspected bootstrap never reads, assigns or removes PYTEST_CURRENT_TEST.
Its spawn call supplies no environment override. This is static launch evidence,
not a runtime observation of bootstrap in this supplier turn. Earlier inert P3
xdist-discovery-v1 metadata actually observed
`test_bac_hardware_identity_v1.py::test_xdist_environment_probe (call)` in that key;
v2/v3 observed it absent from configure/sessionfinish records. Those observations
establish the framework phase distinction, not actual bootstrap execution.

Proposed parent launch validation reconstructs the parent's already-authorized
full P3 environment (job base + pinned common additions + actual worker additions)
and adds exactly PYTEST_CURRENT_TEST = case_id + " (call)" for these call sites.
The provided case_id must belong to the selected owner contract/required selection
and actual pytest request; it is not authorized merely by parsing an env string.
The actual full parent map must equal that reconstruction. The child's full map
must equal the stored parent launch map; P3 recognizes inherited xdist keys through
this authenticated launch lineage while keeping the child's own nonworker role.
No other added/deleted/overridden key passes.

Known dynamic worker names are PYTEST_XDIST_WORKER, PYTEST_XDIST_WORKER_COUNT and
PYTEST_XDIST_TESTRUNUID; values come from the parent's actual workerinput/lifecycle,
not new child values. PID/PPID identity still comes from the child itself.

For deterministic spawn setup root should explicitly seal observed startup values
(COLUMNS, LINES, applicable locale and actual pytest version) in base environment
where needed and omit duplicate addition entries. Earlier inert P3 spawned-child
negative evidence recorded COLUMNS/LINES additions, so plain inheritance must be
verified, not assumed. Any new startup difference requires a separate exact
observed/pinned contract amendment; this capsule authorizes no generic extras.
Seed/thread/device/import/tool keys retain exact values. Future setup/teardown or
nested-child launch sites require their own explicit phase/case provenance; no
inference from the present call-only schema is authorized.

Parent policy may mark test-module imports end-only because pytest controller
start precedes test collection. A child copies those phases, but P3 still records
already-loaded declared modules at start. P5 can require the owner-supplied exact
module refs in actual child start/end records; absent required observations refuse
strict acceptance. Do not invent pytest module aliases or force imports solely to
produce a witness. Existing bootstrap's three townlet module names are source facts;
actual test module aliases/loaded timing remain owner collection/setup evidence.

## Fork feasibility: no existing complete qualification claim

Adopted P3's guard branch makes no Torch calls and leaves runtime facts unavailable;
its own PID/start/host/boot/argv and inherited module dictionaries can be observed
without substituting a parent's identity. Load identity/protocol and required
stdlib machinery before entering a fork-sensitive scope, not in the grandchild.

Preloading alone does NOT establish the core owner's stronger no-import boundary.
The current recorder calls read-only Git via subprocess and uses recursive P0
validation/datetime parsing; this supplier has not qualified their complete lazy
import behavior under an import trap. The prior P3 synthetic fork target itself
performed an import and therefore cannot prove the strict owner's no-import test.
The core supplier also requires no Torch/NumPy/queue operations and no inherited
scope unwind; preserve its existing os._exit structure and pipe observations.

A finite P3 guard-specific amendment and inert tests must prove zero child imports
and forbidden runtime calls at the exact owner cut. If the root elects to avoid
child Git/subprocess work, it must explicitly approve a typed provenance rule:
parent HEAD/tree are inherited parent observations, while child PID/PPID/start/
imports/file hashes are actual child observations. Never label inherited HEAD/tree
as a fresh child Git query or silently reinterpret P0 source-witness semantics.
Whether to qualify the preloaded existing query path or approve that constrained
inherited-source exception is a root/P0/P3/P4/P5 decision still open. This capsule
supplies neither a waiver nor a fabricated guard source witness.

## Finite follow-up boundaries

1. Root adopts/revises the owner-launch and activation proposal before producer
   edits, and decides the strict fork source/no-import path. P5 should keep it
   unqualified until those interfaces are exact and implemented.
2. A separately bounded P3/P2/P4 amendment must fix Python-debug semantics and
   implement owner launch/current-context/phase environment verification, retaining
   all immutable P3 evidence and updating metadata. No P0 change is presumed.
3. After C1 freeze release, owners replace old identity/observation transport while
   preserving all existing queue/Process/error/poison/RNG/currentness assertions.
   The bootstrap slice does not authorize reads or edits of other owner bodies.
4. Inert RED/GREEN + independent review must cover real actual child/parent IDs,
   phase env including xdist inheritance, wrong parent/contract/role/extra key,
   missing end, Python -O refusal, anomaly=False with Python debug=True, and the
   exact no-import/no-Torch fork boundary. No such new tests ran in this turn.
5. Actual source-qualified owner execution, complete P2→P3→P4→P5 integration and
   real CUDA evidence remain UNRUN; keep every required obligation visible.
