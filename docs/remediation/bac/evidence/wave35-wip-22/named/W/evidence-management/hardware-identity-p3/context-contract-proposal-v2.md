# P3 closed actual-process context v2

Supersedes v1 proposal; no P0 changes. No hardware/APP qualification claimed.
The root-authored CLI context is pinned by --bac-identity-context PATH and
--bac-identity-context-sha256 SHA already sealed in job argv; direct child callers
receive the same authority through their accepted owner contract.

Context exact keys:
- schema: bac-hardware-identity-context-v1
- spec, command, trusted_grant: P0 references
- job_id, role_id: P0 IDs
- required_imports: unique [{name:P0 id,reference:P0 reference,phases:nonempty
  unique subset of [start,end]}]; origins must belong to candidate inputs or
  environment dependencies. No APP/Torch imports by recorder. Modules not yet
  loaded may be absent only before their sealed required phase.
- worker_roles: list of role IDs, length xdist_workers, initial slot order;
  repeated IDs allowed only within role.count. Limits from sealed P0 roles.
- environment_delta: {common:P0 env,worker:P0 env}; exact values explicitly sealed
  by root based on pinned installed framework/interpreter. No launch-controlled
  key can be overridden; additions only. Observed initial permitted names:
  common subset {PYTEST_VERSION,LC_CTYPE}; worker exactly {COLUMNS,LINES} when
  absent from launch. For this observed installation PYTEST_VERSION=8.4.2,
  LC_CTYPE=C.UTF-8 (only observed locale coercion), COLUMNS=80, LINES=24.
- parent_start, replacement_start, lifecycle: lists of P0 references, length0/1.
- worker_identity: null or exact {workerid:P0 id,workercount:positive-int,
  testrunuid:32 lowercase hex,mainargv:[text]}. Actual workerinput fields, not
  environment guesses. Runtime worker context is derived by controller only.

Actual process.environment is entire os.environ. Validate equality to exact
job.environment plus sealed common additions; workers additionally receive sealed
worker additions plus PYTEST_XDIST_WORKER/WORKER_COUNT/TESTRUNUID derived from
actual workerinput, cross-bound to lifecycle and controller. All unexpected
keys/deletions/overrides refuse. Children started during tests require their owner
to explicitly supply separate phase transport; arbitrary PYTEST_CURRENT_TEST is
not silently permitted. No dynamic seed/thread/device/import/tool overrides.
Root may explicitly seal COLUMNS/LINES/PYTEST_VERSION/LC_CTYPE in launch; in that
case no duplicate addition is permitted and actual value must remain exact.

Controller pytest_configure_node records exclusive closed lifecycle JSON:
{schema:bac-hardware-worker-lifecycle-v1,phase:configure|down,controller_start:ref,
worker_identity:exact worker_identity above,role_id:id,predecessor_start:[ref],
process_start:[ref],error:string,at:UTC}.
Configure uses no process_start (worker has not executed); derives initial role
by worker count/slot. On node down, controller requires unique actual start file
whose environment workerid, parent identity and role match lifecycle; retains
that ref and observed error. If crashed worker has no start, replacement remains
unqualified and controller refuses ambiguous predecessor rather than fabricates.
A replacement consumes exactly one failed-down lifecycle queue item, retains its
role, links predecessor_start to the unique prior actual start, and links lifecycle
to prior down record. Root policy preauthorizes role/count/replacement_limit; no
future file ref must exist in initial sealed context. Exceeding limit refuses.
Worker compares actual workerinput to controller derived context/lifecycle.
Worker process ID hashes actual PID/start/host/boot, never gateway label alone.
P4 checks whole-job counts, lifecycle ordering/replacements and missing end.

record_process(context,phase) -> immutable P0 process ref. Samples own actual
PID/PPID/Linux stat field22 decimal start/host/boot, /proc/self/cmdline argv,
resolved interpreter reference, cwd, environment, monotonic/UTC, imported module
origins/hashes. parent_start must equal observed live parent full identity;
replacement_start is same-role distinct prior identity plus failed lifecycle.
End requires existing same-identity start and preserves absent ends on crash.
P2 owns runner start/end/exit/log. Job controller is actual launched pytest process.

No loaded Torch gives unavailable thread/debug reasons, not-loaded/uninitialized.
Uninitialized loaded Torch observes module dictionaries only (no getattr hooks,
Torch calls/imports); cuda._initialized must be exact bool. This witnesses Torch's
loaded marker only, never every native context. Fork guard observes inherited
module origins only, no Torch calls and unavailable thread/debug reasons. Work
roles observe already-loaded getters get_num_threads/get_num_interop_threads/
is_anomaly_enabled/cuda.is_initialized and exact role config; no initialization,
RNG draws or setter calls. Raw observations bind limitation/provenance. P0 devices
are admitted mapping references only; they never certify actual device work.

Root exact trusted_grant supplied out of band; candidate/spec cannot authenticate
itself. Validate active grant and source-freeze intervals, no-writer/untracked,
exact root/head/tree/import/input inventory, current hashes plus HEAD/read-only
cached diff-index under existing no-follow index lock, at each start/end. Check
all actual imports under source root or pinned declared dependency origins.
No write-tree/staging/source writes and no claimed prevention of transient edits.

Exclusive process/source/raw files under job.output retain partial writes/failures.
Private pytest report exact keys schema=bac-hardware-pytest-report-v1, process:ref,
case_id:text, phase:setup|call|teardown, outcome:passed|failed|skipped|xfailed|xpassed,
longrepr:string, at:UTC. Every phase report persists causally; controller aggregates
actual reports/process/source refs into exclusive P0 completion.json job-evidence.
No terminal/log fields; no fabricated obligation records or P4 acceptance claim.
Exact collection list comes from actual collection; differing worker collections,
duplicate report phase, ambiguous process identities refuse envelope assembly.

Discovery: xdist-discovery-v2 observed controller/worker configure + finish env;
v3 observed Python locale addition and real gw0 crash→gw1 replacement with count1
and same testrunuid. v3 deliberately failed 1/passed1, preserved as discovery
negative evidence; no implementation existed. All source snapshots/argv/PID/UTC/
exit are retained. Counted bodies remain historical60 + P0 520 + two new P3 files.

Exact full dynamic env names: PYTEST_XDIST_WORKER, PYTEST_XDIST_WORKER_COUNT,
PYTEST_XDIST_TESTRUNUID. Their values are workerid,str(workercount),testrunuid.
Raw filename is process-{process_id}-observation-{phase}.json, included in
completion.inventory and referenced by process intra_op/inter_op/debug.provenance.
Exact raw keys: schema=bac-hardware-process-observation-v1, context:context-object,
identity:P0 identity, phase:start|end, environment:P0 env, worker_identity:null|object,
torch_loaded:bool,cuda_marker:bool|null,observation_limit:text,at:UTC.
This is observation provenance, not independent authority. P2/P4 locate by facts
provenance (all three equal), hash-check raw and require matching identity/phase/
environment plus context spec/command/job. Root base context exact bytes are
bound by the two CLI options in sealed job.argv. Derived worker context differs
only role_id,parent_start,replacement_start,lifecycle,worker_identity; all other
fields equal sealed base. Lifecycle ancestry leads to actual controller start and
root-sealed policy, with actual down→configure predecessor chain. No adjacent
unbound file authenticates environment exceptions. Child derivation outside pytest
requires separately accepted owner contract; no generic child authority assumed.
