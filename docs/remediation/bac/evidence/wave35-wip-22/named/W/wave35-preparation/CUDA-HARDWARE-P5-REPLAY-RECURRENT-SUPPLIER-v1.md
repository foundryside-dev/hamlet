# P5 direct / recurrent replay supplier v1

Status: bounded read-only source findings and one proposed replacement protocol;
not implemented, adopted or qualified. C1 APP freeze remains active. No producer
edits, imports, tests, execution, Git writes, branches, worktrees, copies or index
operations occurred. Only this metadata capsule was written. Production replay,
P0/P3/P4/P5 implementation and historical verifier bodies were not read.

## Measured source and metadata boundary

R=/workspace/hamlet. Paths below are under tests/test_townlet/regressions/bac/.
Exactly three counted bodies, 2794/3000 lines. Before and after were independently
hashed in this supplier turn; every hash is unchanged.

| Body | Lines | Bytes | SHA256 before = after |
| --- | ---: | ---: | --- |
| test_replay_rng_custody.py | 1156 | 50497 | e64eaa3fd18489ca40d6193800a012ad53d9bc0086911a645a4e12df5ded7d50 |
| test_recurrent_replay_rng_custody.py | 640 | 29103 | 1044513adaab42b3d6caef624cd4b3e6d70298ed3096f5dfe3dd4de0f32ad5b0 |
| test_world_rng_bootstrap.py | 998 | 45937 | 452e427b945475e050b35273b6bb44effe3ade6ef96629c4382c2d68591ee727 |

Consumed metadata, treated as attributed interfaces rather than implementation:
E/hardware-children-p5/interface-decision-and-owner-requests-v2.md SHA256
3cd9c4a5bc4ff3c37fbc0dcfe961e9f12d9cc757bbab414b30f2c3fff78c95c9;
interface-proposal-v1.md
27312ae30234b9f27cbf9d04f6ada1bac720a5b312c5ac3c94e7fe64b79fc8bf;
P/CUDA-HARDWARE-P5-BOOTSTRAP-P3-SUPPLIER-v1.md
658ddc71a74122ca85cc50c4420ac770b04f663ed60871d5fec2fee794af25e1;
P/CUDA-HARDWARE-P5-CORE-FORK-PHASE-SUPPLIER-v1.md
beb0bbc4db3aba91ffd54151da8f9f4542aaacbfee0ca345930666b1ce52ad29.
E and P are evidence-management and wave35-preparation under
.superpowers/sdd/2026-11-01-bac-remediation-upgrades. Repository AGENTS.md read.

## Exact current jobs, launches and records

| Fixed job (P5 inventory) | Node under the directory above | Actual target / Process name / message |
| --- | --- | --- |
| replay-poison | test_replay_rng_custody.py::test_isolated_replay_poison_refuses_all_direct_samplers | _replay_poison_child(queue) / replay_poison / replay poison fail closed |
| recurrent-replay-poison | test_recurrent_replay_rng_custody.py::test_isolated_recurrent_scratch_work_cannot_heal_common_poison | _scratch_poison_child(queue) / recurrent_replay_poison / recurrent replay scratch poison fail closed |

Both are CPU controls, not real-CUDA evidence. Each existing inventory job has
one controller, zero xdist workers, one spawn child and no fork descendants.
Historical argv, attributed to P5 inventory, is interpreter then
`-m pytest FULL_NODE --no-cov -p no:cacheprovider -p no:benchmark
-p bac_source_identity -q`. The two source bodies do not launch pytest or observe
their own argv. Replacement must seal the full actual interpreter argv with
`-p bac_hardware_identity_v1 --bac-identity-policy ABS_PATH
--bac-identity-policy-sha256 SHA` replacing old plugin activation; other node and
selection flags remain fixed unless root adopts a changed command contract.
The spawned interpreter's actual /proc argv is independently measured by P3;
it must not be copied from this parent pytest command.

At replay lines1057/1111 and recurrent549/597, the parent snapshots CPU ambient
RNG and actual PID, creates get_context("spawn").Queue/Process with args=(queue,),
sets started only after start succeeds, joins90, requires not-alive and exit0,
then reads queue.get(timeout=5). The child tuple is exactly
(message,actual PID,actual PPID,qualified). Parent checks exact message,
queued_pid==Process.pid, child_ppid==parent_pid and child_qualified is qualified.
The child calls bootstrap._child_identity BEFORE all owner semantic assertions.
If qualified it adds actual PPID and replay_imports to spawn-identity-ROLE.json.

The qualified parent exclusively writes spawn-observation-ROLE.json with exactly
process_pid,queued_pid,exitcode,qualified,message,manifest_sha256,parent_pid.
The checked queued PPID is NOT separately serialized in that observation. Its
emission precedes cleanup and final parent assertions. Finally both parents
terminate/join10 any alive started child, close/join the queue, close Process if
not survived, and reject a survivor; direct replay chains the active exception.
After finally they require unpoisoned parent domain and unchanged CPU ambient RNG.
Current child/parent JSON has no P0 refs, start/end pair or actual argv witness.
Normal child return plus actual parent exit0 is termination evidence; there is
no current child end record. No identity-only file proves semantic completion.

## Assertion retention, including what is not serialized

Direct child uses real flat, global-PER and direct recurrent owners, saves each
serialized state, additionally snapshots full flat/PER physical storage and
bookkeeping, and snapshots ambient RNG. Within one flat-participant prepare
lease it prepares all three retained states then publicly poisons the common
domain. Every direct sampler must raise RuntimeError matching
`Ambient RNG domain is poisoned after failed restoration`. It checks live rows,
complete transport and flat/PER physical state unchanged. For each owner it
requires prepare/load-prepared refusal and unchanged transport, then clears,
requires retained_transitions==0 and still-poisoned domain, and again requires
prepare/load-prepared/direct-draw refusal and unchanged cleared transport.
Final child ambient state must equal the initial snapshot before queue.put.
The physical comparator intentionally excludes authority revisions, which may
advance conservatively; do not add a false whole-domain/revision equality rule.

Recurrent child creates the priority owner with PCG64(911), successive sampling,
and takes one real batch before saving state and ambient RNG. It prepares under
the owner's lease and publicly poisons the domain. For priority-update and then
store-refresh it executes _observe_scratch, which calls the REAL sample_units
through a temporary observer: disposable rng is not persistent, beta==0.0,
batch_size==1, its copied bit-generator bytes advance, receipt.indices.shape is
(1,), and at least one observation exists. After MonkeyPatch restoration the
persistent generator is the identical object, its full state is unchanged, and
ambient state is unchanged. These observations remain assertions, not JSON.

_scratch_work requires the actual selected priority slot to change to7.0+1e-6,
other priority entries/IDs/windows/episodes unchanged and max_priority matching.
Store-refresh adds exactly3 transitions with preserved earlier episodes; appended
observations/rewards [21,22,23], successors [22,23,24], actions [0,1,0], dones
[False,False,True], all-True 3x2 masks and length3 legality, episode_id1,
transition_ids[3,4,5], length2 windows [[0,0,1],[0,1,2],[1,3,4],[1,4,5]], and
unit_ids[0,1,2,3]. Preserve these exact existing checks, not merely a success label.
After each work item, sample_batch, sample_sequences, prepare and load-prepared
all refuse poison while complete _live state remains unchanged. After clear,
num_transitions==0 and domain stays poisoned; sample_batch/prepare/load-prepared
refuse and preserve cleared state. Final ambient equality precedes queue.put.
The selected isolated test does NOT execute the separate five-family/two-mode
scratch matrix or its healthy next-selection comparison; do not claim that scope.

Both families use replay._ambient_cpu_state: actual random.getstate(),
np.random.get_state(), torch.get_rng_state().clone(). _assert_same_transport
requires exact Python types and recursively compares mappings/sequences,
torch.equal tensors and np.array_equal arrays. There are no serialized RNG
states/digests, CUDA RNG samples or next-draw comparisons in these selected jobs.
Bootstrap._assert_ambient's separate next-draw check is not called here. Both
parent modules have autouse fixtures restoring Python/NumPy/Torch CPU state on
teardown; the final test-body equality occurs before restoration, so a teardown
reset cannot substitute for that assertion. Child/parent poison, data-preservation
and scratch predicates are source assertions, not independently serialized trace
facts. Acceptance must depend on exact independently qualified assertion source,
Python assertions enabled and actual passing setup/call/teardown, never a supplied
boolean or new invented baseline borrowed from the flat/PER producer family.

## Actual environment, imports and thread preconditions

Bootstrap833-865 supplies all-or-none PRESENCE of BAC_QUAL_ROOT,SHA,TREE,MANIFEST,
OUTPUT (each with BAC_QUAL_ prefix). Missing all means unqualified; partial asserts.
Its old helper fabricates workerinput.workerid=role for bac_source_identity,
records Python __debug__, requires True, Torch intra1/interop5 and actual imported
world_curiosity_state/rng_custody/rnd paths. Neither replay/recurrent/bootstrap
body sets interop5; its origin remains an external launch/setup obligation.
The P3 capsule attributes intra1 forcing and git write-tree to the old helper;
that dependency body was not read here and must not be reused for current transport.

Direct replay_imports is exactly townlet.training.replay_buffer,
prioritized_replay_buffer,sequential_replay_buffer,replay_contract (all full
townlet.training names). Recurrent is exactly townlet.training.sequential_replay_buffer,
townlet.training.replay_contract,townlet.exploration.rng_custody,
test_recurrent_replay_rng_custody,test_replay_rng_custody. These paths come from
actual importlib module imports. Source imports also explicitly load
test_world_rng_bootstrap; recurrent imports replay as retained and aliases its
_assert_same_transport/_ambient_cpu_state, using its episode/options helpers.
P3 must pin the actual loaded test aliases and actual file refs; no guessed
module aliases/hashes or forced imports merely to manufacture evidence.

There is no PYTEST_CURRENT_TEST/environment rewrite at either spawn launch.
Static inheritance requires the P3 capsule's exact call-phase owner-launch
derivation, including any authentic parent xdist keys, although fixed jobs have
zero workers. Do not remove dynamic keys or pretend the child is an xdist worker.
Python __debug__ is not Torch anomaly mode. The pending P3 debug/owner-launch
amendment and separately pinned complete environment must precede integration.
No fork/no-import recorder is used by these two jobs; the core/P3 fork amendment
remains an independent required gap, not an exception granted by this supplier.

## One proposed closed current payload

This is NEW instrumentation, not an existing API. Adopt the bootstrap/P3 capsule's
single activation, prepare_owner_launch/current_process_context proposal and exact
launch/context derivation before implementation. No legacy adapter/fallback or
historical verifier acceptance. Required source inventory contains all existing
bootstrap and respective replay module refs above plus actual test/bootstrap
module refs. Controller requirements may be end-only before collection; P5
additionally requires actual already-loaded child start/end imports. Source refs
come from root inventory. Root no-writer authority remains external to records.

`ref` means exact P0 {path,bytes,sha256}. All new objects reject missing/unknown
keys, duplicate JSON keys, nonfinite numbers and bool-as-int. Finite case values
are replay_poison and recurrent_replay_poison with exact table mapping. No other
child kind/phase/fork list is admitted for these jobs.

1. Child result exact keys: {schema,spec,job_id,case,role,owner_launch,
   process_start,python_assertions_enabled,message,assertion_source,
   rng_assertion_scopes}. Schema bac-hardware-replay-child-result-v1; case=role;
   spec/launch/start/source are actual refs. Python flag is actual __debug__ True.
   Source is the respective owner test ref. rng_assertion_scopes is exactly
   [after_all_poison_operations] for direct, or
   [after_priority_update,after_store_refresh,after_all_poison_operations] for
   recurrent, each naming the actual existing assertions above. These checkpoints
   are assertion-only, not serialized RNG state or stand-alone proof. Emit only
   after all existing child assertions and restored observation patches, then
   actual P3 end. P3 itself must be independently qualified as nonperturbing at
   those cuts; no runtime getter belongs inside the scratch observer.
2. Queue acknowledgement replaces the old tuple with exact
   {case,role,pid,ppid,message,result,process_start,process_end}. PID/PPID are
   observed by child; result and starts/ends are actual emitted refs, never
   pre-created by parent. Queue only after child result and end. It is transport,
   not terminal parent success. Missing end/crashed child remains failure.
3. Sole terminal owner payload exact keys: {schema,spec,job_id,case,role,
   parent_start,owner_launch,process_pid,exitcode,acknowledgement,
   parent_rng_assertion,assertion_source}. Schema bac-hardware-replay-result-v1.
   parent_rng_assertion is exactly {kind:source-assertion-only,
   checkpoint:after_child_cleanup,function:_assert_same_transport,
   channels:[python,numpy,torch_cpu]}; recurrent's _same is the exact alias of
   that same function. acknowledgement is the actual received object. Retain
   actual Process.pid/exitcode before Process.close; emit payload exclusively
   AFTER cleanup, final healthy-parent-domain and RNG assertions. No new bool
   claims qualification. Source assertion custody and all actual report phases
   must be independently qualified before strict acceptance.

P5 cross-checks exact job/case/role/message, launch contract/node/method=spawn,
actual parent P3 start, child start/end same full identity and live PPID chain,
queued PID=Process.pid=child PID, queued PPID=actual parent PID distinct from
child, exit exact int0, source/input/import refs, same observed Torch version,
intra1/interop5 and actual Python assertions True. P3 start/end provide host/boot/
start-token/argv/source authority unavailable from the old identity file.
Absent/conflicting/malformed refs refuse; no parent substitutes a child's record.
Preserve the complete owner assertions above rather than making P5 fabricate
data/exception traces that are not serialized.

Parent payload is final for test-body assertions; acceptance is deferred until
P0 completion inventory binds actual parent end and actual passing pytest
setup/call/teardown (no skip/xfail). No future-report ref is embedded in an earlier
record and no circular hash is created. P4 supplies common validation/report
custody; P5 checks the strict source checkpoints and correlations. Proposed
exclusive output basenames replay-child-ROLE.json and replay-result-ROLE.json
under sealed job.output are fixed in owner_contract; returned P3 refs are never
guessed from names. Every consumed launch/result/process/raw/source/report enters
the declared inventory, with missing/extra strict records rejected. Neither job
has a phase pair or related-attempts requirement of its own.

## Owner decisions and finite later edit boundary

Root must adopt the closed schema and independently qualified assertion-only
RNG/data proof approach; currently there is no source-owned serialized baseline.
P3 owns debug correction, actual context/launch API, environment and thread/source
observation qualification; bootstrap owner owns replacing the old helper. P2 owns
sealed argv/environment and outer process waits. P4 owns common/report custody;
P5 owns exact schema/correlation/receipt qualification. No proposed API here is
claimed implemented. Unknown interop5 setup and actual module/startup environment
remain explicit owner evidence gaps, not guessed facts.

After C1 freeze release only, proposed replay-owner edit packet: exactly the two
existing replay bodies, present1796 lines, maximum2000 combined; one new inert
protocol test at a root-named path maximum500, total2500 lines/3 edited bodies.
Bootstrap remains a separately owned dependency with its own edit cap. Source
read ceiling stays the present three named bodies/3000; adding any implementation
helper or exceeding caps needs root reslice. Suggested finite verification covers
wrong role/node/parent/env/PID/PPID, missing end, pre-assertion payload, failed
teardown, Python -O, anomaly False with assertions True, extra/malformed refs and
unchanged source-qualified semantics. No test execution is authorized here.
Both current owner integrations and all six missing real-CUDA groups remain
UNRUN/unqualified; these CPU controls cannot satisfy hardware obligations.
