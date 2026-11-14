# B cold-import qualification — implementation contract v2

2026-11-14. PROPOSAL ONLY. Supersedes, preserves and links v1 SHA256
`e6538032760a26d82fde8f653f58f63b65ee386dac0c99fd06fdd6554c9fe819`.
Addresses all six items of Astra review SHA256
`326407a3ba8cc4f20384b8d87542fa53a62b3859bac2cac025fd75121bb95ced`.
Implementation starts only after plan PASS, WIP20 publication and root's writer
dispatch. This document grants no execution. No source/test/helper/tool edits,
application imports, collection, child execution, Git, branches, worktrees,
checkouts, execution copies or delegation occurred. This v2 is the only new write.

## Separate, root-approved packets

Preparation read reservation is exactly4307/three bodies:

| Body | Lines | SHA256 |
| --- | ---: | --- |
| `src/townlet/exploration/rng_custody.py` | 1195 | `6cb01ca77b58db5f4c4784dc36da566c06cf68c2a7c2ce227bb780549f3344f8` |
| `tests/test_townlet/regressions/bac/test_rng_cuda_admission.py` | 2360 | `6ec962f9c0b3d467375528b26de39bac154b46e4d5c6435ffcc289960f063085` |
| `Q/verify_bac_replay_spawn_identity.py` | 752 | `6006c7247d79a99226a74756a2266a2966fce800f9f84af802f2990db4606173` |

Q=`/workspace/bac-review-2026-11-01/qualification`. No other implementation
body was read. AGENTS.md and prose suppliers are not additional code bodies.

APP packet: unchanged core1195 plus existing core test growth<=650,
test<=3010, total<=4205/two,795 hard-limit lines remaining. No new helper;
one literal probe and five pytest nodes go in the existing test. Preserve all
existing89 controls/IDs, including warm exact18, active policy and fork guards.

TOOL packet: unchanged existing verifier752 plus new
`Q/verify_bac_cold_import_identity.py`<=1000,
`Q/bac_cold_worker_identity.py`<=250 and
`Q/test_verify_bac_cold_import_identity.py`<=800: total<=2802/four.
Root approved these projected separate packets for planning. Their implementers
must remeasure before reads/edits; do not combine APP growth with TOOL reads.
The existing spawn verifier is byte-for-byte unchanged, including ROLE_CONFIGS,
bootstrap imports and Torch interop=5 requirements. The new exec validator does
not call its spawn subject validator or relax any old branch. Exceeding either
packet requires an explicit finite reslice; do not compress/drop controls.

## Closed jobs, commands and destinations

T=`tests/test_townlet/regressions/bac/test_rng_cuda_admission.py`.
Every job has exactly one pytest node. Root harness command is exactly
`[root/.venv/bin/python, "-m", "pytest", T+"::"+node, "--no-cov", "-p",
"no:cacheprovider", "-p", "no:benchmark", "-p", "bac_source_identity",
"-p", "bac_cold_worker_identity", "-q", "-s"]`.
No xdist/workers or alternative flags; root harness concurrency is1. The parent
keeps its existing warm profile; the exec child has the distinct thread profile
below. The explicit -s makes the worker marker visible in the harness log;
the child itself still redirects both streams to its dedicated files. The five
closed rows, in qualification order, are:

| job / role | node | mode | entry |
| --- | --- | --- | --- |
| `cuda_core_cold_preflight_preloaded` | `test_cold_import_probe_faults[preloaded]` | `preflight_preloaded` | `core` |
| `cuda_core_cold_preflight_cuda_touch` | `test_cold_import_probe_faults[cuda_touch]` | `preflight_cuda_touch` | `core` |
| `cuda_core_cold_import_core` | `test_fresh_process_canonical_import_order[core]` | `qualify` | `core` |
| `cuda_core_cold_import_flat` | `test_fresh_process_canonical_import_order[flat]` | `qualify` | `flat` |
| `cuda_core_cold_import_per` | `test_fresh_process_canonical_import_order[per]` | `qualify` | `per` |

Application entries are fixed, respectively custody, replay_buffer and
prioritized_replay_buffer under their actual townlet packages. The role is
derived from this table, not a free argv value. Unknown role/mode/entry/node
combinations refuse. The harness's ordinary sealed spec/result/log remain the
root-run authority for exact command, candidate, manifest, tool and log bytes.

There are FIVE separate one-job root harness specs/runs, so root can validate
faults before launching positives without changing harness scheduling. Let O
be the common cold attempt output; each row's harness output is
R=`O/role/run`, and its job directory J=`R/role`. No two runs share result/log
destinations. Each J has exclusive files:
`cold-import-worker.json`, `cold-import-identity.json` (positive only),
`cold-import-fault-witness.json` (negative only), `cold-import-observation.json`,
`cold-import-stdout.log`, `cold-import-stderr.log`, and finally
`cold-import-custody.json`. A positive job cannot have a fault witness; a
negative cannot have a success identity. Exact `cold-import-*` file inventories
are checked; existing root-run collateral, including identity-controller.json,
remains governed by the unchanged harness inventory and supplies no PID inference.
duplicate role directories/files, unexpected identity files and overwrite refuse.
Failed attempts use separate exclusive attempt directories and retain every
partial file; they cannot gain the success filename or reuse an old receipt.

## Authoritative pytest-worker PID linkage

The old identity-controller has no PID. It is never used as a worker-PID
authority. The sealed stdlib-only worker plugin runs in pytest_sessionstart,
checks the exact one-node argv against the closed table, and exclusively emits
`J/cold-import-worker.json` from actual os.getpid/getppid, actual orig/proc argv,
actual `/proc/self/stat` start_ticks, actual cwd and interpreter. It prints exactly
`BAC_COLD_WORKER_SHA256=<hash-of-exact-worker-file-bytes>` to the job log.
Root harness result hashes that exact log and seals its exact command. Validator
requires exactly one matching marker, the exact plugin hash from the tool seal,
the correct spec/result/log references and command equality. Missing marker,
worker file, source seal or root-run linkage is rejection, not inference.
This source-issued worker record is the explicit authoritative PID record;
parent observations and child PPID must equal its PID and its start_ticks must
match the parent-observed worker process while child launch is live.

No harness rewrite or new server is needed. Qualified root runs expose Q using
their existing plugin search path and explicitly select this plugin. The child
uses -I, does not inherit that search path, and imports neither plugin nor test.
Ordinary unqualified pytest may run the same semantic probe against temporary
local context, without a root-run log/plugin seal; such files cannot pass this
validator and are never published as qualified custody. Missing qualified
linkage must never silently downgrade a run whose qualification env is active.

## Literal, argv, runtime and source seals

Require exactly one module-level simple assignment to `_COLD_IMPORT_PROBE`,
with one Name target and an ASCII ast.Constant string value. No annotated,
augmented, tuple, f-string, BinOp concatenation or later assignment/delete/
write target to that name anywhere in the test AST. Reject adjacent string
tokens too: tokenize the assignment RHS and require exactly one STRING token
besides whitespace/newline. The launch takes that exact variable value without
dedent, formatting, replacement, append or encoding round trip. Independent
source review verifies the Popen argument is that variable. Validator extracts
the literal with AST literal evaluation only, never imports/executes the test.

Actual child argv has exactly nine strings:
`[launch_python, "-I", "-c", probe, mode, entry, root, J, nonce]`.
launch_python is the sealed absolute virtualenv invocation path
`root/.venv/bin/python`, preserving its symlink spelling for venv discovery.
Do not resolve that symlink before launch. Separately record/hash actual binary
`/proc/self/exe` resolved path; compare it and sys.executable with sealed runtime
facts. This fixes v1's potentially incorrect resolved-interpreter launch.

Child records full sys.orig_argv and UTF-8-decoded `/proc/self/cmdline` argument
list (strip exactly its final empty terminator). Require equality of all nine
elements, with argv[0] the invocation path. Script hash is SHA256 of actual
argv[3].encode("utf-8"), matching extracted literal bytes. Command hash is
SHA256 of json.dumps(argv, ensure_ascii=True, separators=(",", ":")).encode
("utf-8"). Parent launch argv/hash and validator-derived argv/hash must agree.
Output is canonical J, exclusive and contained under the sealed attempt output;
nonce is exactly32 lowercase hexadecimal characters issued by the parent for
that job and bound across records. Extra flags/args, different nonce/output,
alternate interpreter/script/root or proc/orig mismatch all reject.

Tool seal is a JSON object with exactly `schema, tools, runtime`:
schema=`bac-cold-import-tool-seal-v2`; tools is exactly the four TOOL filenames
mapped to FileRef below; runtime has exactly `launch_python, binary, binary_sha256,
python_version, torch_path, torch_version, numpy_path, numpy_version`.
Values are frozen before real runs, independent of child observations. Q tool
and external-runtime bytes are hash-verified references, not source copies.

Allowed Townlet origin inventory A is fixed BEFORE child execution from the
sealed candidate manifest's source_files: every regular .py path beginning
`src/townlet/`, mapped to its normal dotted module name (drop /__init__.py for
packages, otherwise drop .py). Reject duplicate derived names, path traversal,
symlink escape or hashes absent from that manifest. This finite mapping is
source-derived, never learned from the child. Each observed application module
must be in A, have exact canonical root-relative path/hash, and be under root/src.
Namespace/no-file modules refuse this profile. Every observed inventory is a
sorted unique list of those mapped names, not an open map accepting new names.

Checkpoint inventories are recorded before Torch, after Torch and immediately
before selected entry: all exactly[]. After selected entry, inventory must
contain actual townlet package, selected module and custody; core mode forbids
both producer modules then. After both explicit producer imports and at final
checkpoint, inventory must contain both producers/custody and match A origins.
Other members are permitted only from sealed A; exact child inventory is not
used to expand A. The exact reviewed probe contains only fixed application
import targets, preventing this source allowlist from becoming a caller registry.
All test/manifest/source/interpreter/tool/stdout/stderr hashes bind exact bytes.

## Cold observer and genuine controls

All provenance/setup imports before application entry are stdlib only, followed
by real Torch/NumPy. Check no townlet module before and after Torch. Configure
child-only OMP_NUM_THREADS, MKL_NUM_THREADS, OPENBLAS_NUM_THREADS,
NUMEXPR_NUM_THREADS, VECLIB_MAXIMUM_THREADS and BLIS_NUM_THREADS to string1
before Torch; call CPU torch.set_num_threads(1)/set_num_interop_threads(1).
Observe actual getters1/1, one MainThread and one `/proc/self/task` task both
after CPU setup and at final checkpoint. These are actual observations, never
configured-value substitutes. Unsupported actual profiles reject and remain
failed; they do not cause an inferred fallback profile.

Install NoCUDA as actual torch.cuda before any application import and retain it
through cleanup. Every attribute access counts then raises RuntimeError with
the fixed diagnostic `cold import CUDA sentinel touched`; positives require0
and exact sentinel identity throughout. Do not query GPU state for provenance.

Before FIRST selected import, install stdlib sys.setprofile callback, matching
canonical custody source filename plus exact code names `_local_cuda_policy`
and `_resolve_local_cuda_record`. It acquires no custody method/module object.
On a matching call, count then raise immediately. Also wrap builtins.__import__:
when actual caller globals __name__ is canonical custody, resolve name/level
with stdlib importlib.util.resolve_name using caller __package__, constructing
possible module targets from absolute base and fromlist. Reject before import
when base is either producer or base+fromlist member is either producer. This
handles absolute imports, relative imports and `from townlet.training import
replay_buffer` without warming custody. Invalid import metadata is passed to
the original importer for its real Python error; observer returns only genuine
original import results, never modules/classes. Install observers before any
selected import, save/restore prior hooks in finally, count zero eager calls
and zero custody-origin producer requests. Disable observers before genuine
gate resolution. This is a bounded observer backed by reviewed fixed-import
source, not a general Python import-purity theorem.

After selected import and observer removal, custody's sole domain PID must be
actual child PID and its actual cache must be empty. Do not reset it. Explicitly
assert actual manifest is MappingProxyType, has exactly the eighteen actual
opaque constants as its complete keyset, every constant has exact type
LocalCUDAContract, and every descriptor has exact immutable descriptor type,
reviewed tags/route/bits and source rationale. Record D below from these actual
objects against the independent fixed expected table. Then explicitly
import both real producers; construct actual CPU owners using root's supplied
facts: ReplayBuffer(4, torch.device("cpu")) and
PrioritizedReplayBuffer(4, 1.0, 0.0, False, torch.device("cpu")). Each has real
owner.rng_participant, owner._replay_lock and genuine
owner._owner_operation(mutation=False). Keep both strongly alive; validate
actual domain member owner identity and exact canonical owner class. Cache
must still be empty. These are attributed supplier facts; no producer body read.

Forward-count the saved genuine bound resolver without replacing manifest,
cache or returned policies. Before ANY success, attempt flat and PER serialize:
temporarily delete only actual producer.__dict__[canonical_class_name], retain
class/owner strongly, enter real domain.local_cuda_access using real participant,
and require ImportError before body/gate creation. Cache remains empty; pure
domain state is unchanged and CUDA untouched. Restore exact export in finally
even if assertion fails. No sys.modules deletion/replacement or class stand-in.
This is missing-export recovery, not a simulated partially initializing module.

Then first successful real local gates, flat serialize then PER serialize,
must cause exactly one genuine successful resolution each. No private policy
lookup precedes them. Under the authentic domain gate, take the actual owner
context, enter gate.complete(cuda_devices=()), and verify completion False while
live. Repeat flat then PER with exact cache tuple/policy identity and no resolver
call. Four gates total, two failed resolutions plus two successful resolutions,
two cache hits, two retained policies and exactly16 unresolved contracts.
Inspect actual descriptor/policy/gate/participant/owner `is` relations in-child;
cross-process serialized ids are supporting local observations only. Unregister
real participants in finally, no dispose assumption, no health/domain resets.

## Typed JSON grammar and complete observations

Every object below has EXACTLY its listed keys. Use duplicate-rejecting
object_pairs_hook recursively and parse_constant rejection for NaN/Infinity;
then recursively reject nonfinite floats. No parser default values. Integers
are exact int, never bool. I is nonnegative int; P is positive int; B is exact
bool; H is64 lowercase hex; S is str; Ref=`{path:S, bytes:I, sha256:H}` with
absolute canonical path, actual byte length/hash. Duration is finite exact
float>0 and <=100; nonce is32 lowercase hex. Generic maps occur only where
explicitly source-derived A or fixed field enumerations authorize their keys.

ThreadSnapshot=`{python:[{name:"MainThread", ident:P, native_id:P}], os:I,
torch_intraop:1, torch_interop:1}`; list length1, os1, observed native_id equals
actual sole `/proc/self/task` entry. Worker thread snapshots instead record
actual sorted lists/counts without claiming the child's single-task profile.
State=`{generation:I, revision:I, currency:I, ambient_revision:I, poisoned:false,
ready:false, gates:I, operations:I, members:I}` read directly from actual domain
fields under its actual lock, without status() draining retirement callbacks.
Checkpoints outside gates require gates=operations=0. After constructors members2;
after explicit unregister members0. Compare State BEFORE and AFTER each failed
lookup, first gate and repeat gate for exact equality (cache recorded separately).
Do not compare generation across actual registration/unregistration.
RNG=`{python:H, numpy:H, torch:H}` hashes pickle protocol5 of actual Python and
NumPy CPU states, and contiguous CPU Torch RNG bytes. Compare after-constructors
baseline to after-gates before cleanup; no constructor RNG-invariance claim.

Fixed descriptor inventory D has exactly18 ordered records. A record is
`{name:S, contract_id:P, descriptor_id:P, owner_kind:S, route:S, input_kind:S,
rationale:S, healthy:true, post_poison:false}`. Names and triples are this table;
ids distinct in their respective sets, rationale nonempty and exact source
descriptor value. Source AST/supplier review binds rationale semantics; parser
nonemptiness does not prove purity.

| name (prefix RB=`REPLAY_BUFFER_`, PB=`PRIORITIZED_REPLAY_BUFFER_`) | owner | route | input |
| --- | --- | --- | --- |
| RB+PUSH_CUDA | flat | push | tensor |
| RB+PUSH_RECORDED_CUDA | flat | push_recorded | tensor |
| RB+READINESS_CUDA | flat | readiness | request |
| RB+SERIALIZE_CUDA | flat | serialize | none |
| RB+VALIDATE_SERIALIZED_CUDA | flat | validate_serialized | mapping |
| RB+LOAD_FOR_MODE_VALIDATION_CUDA | flat | load_for_mode | mapping |
| RB+HISTORICAL_ARCHIVES_CUDA | flat | historical_archives | none |
| RB+INSTALL_HISTORICAL_ARCHIVE_CUDA | flat | install_historical_archive | archive |
| PB+PUSH_CUDA | per | push | tensor |
| PB+PUSH_RECORDED_CUDA | per | push_recorded | tensor |
| PB+DECLARE_UNCONSTRAINED_ACTION_DIM_CUDA | per | declare_unconstrained_action_dim | integer |
| PB+READINESS_CUDA | per | readiness | request |
| PB+SERIALIZE_CUDA | per | serialize | none |
| PB+VALIDATE_SERIALIZED_CUDA | per | validate_serialized | mapping |
| PB+HISTORICAL_ARCHIVES_CUDA | per | historical_archives | none |
| PB+INSTALL_HISTORICAL_ARCHIVE_CUDA | per | install_historical_archive | archive |
| PB+UPDATE_PRIORITIES_CUDA | per | update_priorities | indices |
| PB+UPDATE_UNIT_PRIORITIES_CUDA | per | update_unit_priorities | indices |

Cache lists are ordered lists of D names, never ids or implicit count only.
Before owners/after owners/after each failed lookup they are[]. First flat cache
is[RB+SERIALIZE_CUDA], first PER/repeats are[RB+SERIALIZE_CUDA,PB+SERIALIZE_CUDA].
Unresolved is exactly D minus those two, in D order. Do not sort D by dynamic id.

Common C fields, expanded into each child object: `schema:S, profile:S, role:S,
mode:S, entry:S, nonce:S, pid:P, ppid:P, worker_ref:Ref, root:S, cwd:S,
launch_python:S, binary:S, binary_sha256:H, python_version:S, orig_argv:[S],
proc_argv:[S], command_sha256:H, script_sha256:H, manifest_ref:Ref, test_ref:Ref,
base_commit:S, candidate_tree:S`. Root/cwd equal sealed root; ppid equals actual
worker_ref.pid; manifest/test paths and bytes match final source/candidate.
Profile is exactly `linux-exec-cold-import-v2` for all five rows. Version/paths
match tool-seal runtime. All argv lists have the exact nine elements above.

Positive identity schema=`cuda-core-cold-import-identity-v2`, fields C plus:
`runtime, checkpoints, source_modules, threads_before, threads_after,
environment, eager_policy_calls, custody_producer_imports, manifest_contracts,
missing_exports, gates, unresolved, rng_before, rng_after, cleanup`.
runtime exactly `{torch_version:S, torch_path:S, numpy_version:S, numpy_path:S}`.
checkpoints exactly `{before_torch:[S], after_torch:[S], before_selected:[S],
after_selected:[S], after_producers:[S], final:[S]}` as constrained above.
source_modules is exactly the union of checkpoint application names mapped to
`{path:S, sha256:H}`, each matching A. environment has exactly the six thread
variables above, all string1; threads_before/after are ThreadSnapshot.
eager_policy_calls and custody_producer_imports both exactly[].
manifest_contracts is exactly D. rng_before/after are identical RNG objects.

missing_exports has exactly two records, flat then PER:
`{contract:S, exception_class:"ImportError", export_restored:true,
body_calls:0, cuda_calls:0, cache_before:[], cache_after:[], state_before:State,
state_after:State}`. Each State pair is identical with members2.
gates has exactly four records, first flat/PER then repeat flat/PER:
`{pass:S, contract:S, owner_id:P, participant_id:P, descriptor_id:P, policy_id:P,
cache_tuple_id:P, owner_class:S, input_class:"builtins.NoneType", route:"serialize",
rationale:S, healthy:true, post_poison:false, exact_binding:true,
completion_failed:false, cache_before:[S], cache_after:[S], resolver_before:I,
resolver_after:I, state_before:State, state_after:State}`.
pass is first/repeat in that order; class strings are exact canonical dotted
classes, plus actual in-child `is` assertions source-bound by exact_binding.
Resolver counts are2->3,3->4,4->4,4->4. Each State pair identical members2.
Repeat ids, rationale/bits and all prior cache tuples equal first observations.
cleanup=`{unregistered:["flat","per"], state:State, cache:[S], unresolved:[S],
cuda_calls:0, sentinel_identity:true}`; members0, cache two, unresolved16.

Worker object schema=`cuda-core-cold-worker-v2` with EXACT keys
`schema, role, node, pid, ppid, start_ticks, root, cwd, launch_python, binary,
binary_sha256, orig_argv, proc_argv, command_sha256, manifest_ref, test_ref,
plugin_ref, base_commit, candidate_tree, python_threads, os_threads`.
PID/start_ticks positive exact ints, source/path/hash/command constraints above;
python_threads is sorted exact observed `{name:S, ident:P, native_id:P}` list,
os_threads positive int equal actual observed count. Parent plugin does not
claim child Torch profile or import Torch/custody to produce this record.

Parent observation schema=`cuda-core-cold-import-observation-v2` has EXACT keys
`schema, role, mode, entry, nonce, parent_pid, child_pid, worker_start_ticks,
worker_ref, launch_argv, command_sha256, script_sha256, subject_ref,
stdout_ref, stderr_ref, exitcode, timed_out, termination, reaped, seconds`.
PIDs positive; worker_start_ticks matches worker record and live proc read;
launch_argv equals expected9 and child actual argv. subject_ref references
identity or fault witness according to closed role. stdout/stderr Ref paths are
exact J filenames. Positives require exitcode exact int0, no timeout,
termination="none", reaped=true. Negatives require exact int1 and same cleanup.
No field is called child-origin merely because the parent launched that argv.

## Negative causality and non-success witness

Probe has exactly one `_cold_boundary` function containing the fixed diagnostic
assertion `cold import precondition violated`, and exactly one sentinel raise
site with `cold import CUDA sentinel touched`. Validator extracts inner probe
AST, derives their function/line locations, and source review confirms the
designated fault callsites. Probe compile line numbering starts at1 as actual
-c source; no prepended wrapper. Normal traceback class spelling is
AssertionError/RuntimeError, not builtins-prefixed spelling.

Preloaded mode: first prove before/post-Torch emptiness and install sentinel;
deliberately import real custody, emit the non-success witness immediately
before `_cold_boundary`, then fail its pre-entry emptiness assertion. Witness
phase=`before_preentry_assert`, modules contain actual custody/origins, CUDA0.
The final traceback frame must be the designated assertion site, with its
designated caller frame after the real preload; final line must be exactly
`AssertionError: cold import precondition violated`.

CUDA-touch mode: prove all three cold checkpoints empty, install sentinel, and
deliberately evaluate torch.cuda.is_initialized attribute without calling it.
Sentinel increments once, emits witness immediately before raising at its
designated source site, then raises. Witness phase=`before_sentinel_raise`,
modules[], CUDA1. Traceback must contain the designated access callsite and
terminate at sentinel raise; final line exactly
`RuntimeError: cold import CUDA sentinel touched`.

Witness schema=`cuda-core-cold-import-fault-witness-v2`, fields C plus exactly
`phase, modules, source_modules, cuda_calls, site_function, site_line,
caller_function, caller_line, threads, environment`. Modules sorted per A,
source_modules exact origins/hashes; thread/env profile as positive. Site and
caller names/positive line ints equal extracted exact probe AST sites, not
arbitrary source labels. Role determines phase/modules/count/exception.
Child itself writes actual PID/PPID/orig/proc argv/script/source and witness
phase before expected failure. An unrelated earlier failure emits no matching
witness and cannot qualify. Parent retains full stderr bytes; validator parses
the full traceback's final chain, checks exact site/function/line sequence
against that witness and extracted source, and refuses appended/multiple
terminal exception chains or an unrelated terminal error. No success identity,
timeout, import error, wrong thread/source profile or failed reaping qualifies.

## Validator API, synthetic tests and root sequence

New validator CLI is exactly
`Q/verify_bac_cold_import_identity.py COLD_SPEC ROLE` using root's Python.
API `verify(spec_path, role)` writes only exclusive J/cold-import-custody.json
after every check succeeds; no application imports. COLD_SPEC exact keys:
`schema, root_run_specs, manifest_ref, tool_seal_ref, root, output, jobs`.
schema=`bac-cold-import-spec-v2`; root_run_specs is exactly the five role names
mapped to Ref objects for their separate existing-format one-job harness specs;
jobs is the exact five ordered `{role:S, node:S, mode:S, entry:S}` table above.
Each referenced harness spec must have exactly one job, with the exact command
above, workers1, matching canonical root/manifest and its role's exact R output.
For the selected role require its successful result/log and worker marker;
validate source hashes of the other four specs without requiring their runtime
results before they execute. This enables strict preflight-first sequencing.
Spec/manifest/tool bytes freeze before real tests; validator cannot invent
missing worker linkage or infer a manifest from results. It verifies current
candidate/source/config/artifact hash inventory using the root's established
repository guard protocol without widening that protocol's acceptance.

Receipt exact keys: `schema, status, role, mode, entry, spec_ref, root_run_spec_ref,
root_run_result_ref, root_run_log_ref, tool_seal_ref, worker_ref, subject_ref,
observation_ref, stdout_ref, stderr_ref, base_commit, candidate_tree,
manifest_ref, parent_pid, child_pid, script_sha256, command_sha256, scope`.
schema=`cuda-core-cold-import-custody-v2`; status is exactly
`COLD IMPORT POSITIVE VERIFIED` or `COLD IMPORT EXPECTED REJECTION VERIFIED`
as role requires. Scope is fixed CPU import/canonical-gate protocol only; no
hardware, producer leaf, post-poison, B6/R0 or whole-programme qualification.
The exact scope string is `CPU cold-import/canonical-gate protocol only; no
GPU hardware, producer leaf, post-poison, B6/R0 or whole-programme qualification.`
Join that displayed line break as one ASCII space in the literal receipt.

Tool tests use authored synthetic records only, with no Townlet imports or
actual probe execution. Matrix covers every nested schema/type/value and named
mutation: unknown role/mode/profile/node, PID/start_ticks/worker marker linkage,
all source/tool/interpreter/script/manifest/log hashes, argv flags/element count/
nonce/root/output, proc/orig mismatch, preimport contamination, missing D row,
wrong cache/policy identity or unresolved16, wrong resolver count/state/RNG,
nonzero CUDA, wrong threads, wrong fault site/exception/count/phase/witness,
positive file in negative job, duplicate JSON keys/files/roles, extra keys,
NaN/Infinity, bool duration/PID, timeout/nonzero positive exit and failed cleanup.
Parser tests prove wrong/missing-value rejection. Observed-zero assurance comes
from reviewed probe bytes plus execution custody, not a parser's ability to
detect fabricated numeric zero. Pin unchanged old verifier hash and run its
existing strict-profile regression checks; no generic role fallback added.

Finite sequencing:

1. After WIP20 and v2 PASS, root dispatches separate APP and TOOL packets with
   this exact schema/role/source contract. APP author may write tests but cannot
   execute application/fixture before TOOL qualification.
2. TOOL owner implements/reviews synthetic tests, runs them and required existing
   strict-profile regressions, freezes tool/plugin/test bytes and tool seal,
   obtains independent tooling review. No real child run during this step.
3. APP owner freezes probe/test bytes and final source review; root seals updated
   candidate manifest, runtime/tool references, exact spec and actual collection
   delta existing89 plus5=94. Do not change scripts/schema after sealing.
4. Root executes two fault jobs and strict validator first. Both must yield
   expected-rejection receipts. Only then execute/validate the three positives.
5. Root reruns existing89 and required activation/producer/strict-profile selections
   on those final bytes. The five cold jobs already cover their five unique nodes;
   preserve actual collection/selection/unexecuted IDs and union accounting.
6. Independent bounded final review checks exact linked seals/artifacts. Preserve
   every failed/partial/unexecuted attempt; schema/source changes require new
   linked attempts/seals, never edits to historical evidence.

Parent starts only its new child session, redirects logs to exclusive files,
and enforces90-second child deadline. Timeout: terminate that process group,
wait<=5, kill if needed, wait/reap<=5, always close handles. Preserve failures
in separate `cold-import-failure.json` with exact keys `schema, role, phase,
error_type, error_message, elapsed_seconds, timeout, termination, returncode,
reaped, files`; schema=`cuda-core-cold-import-failure-v2`, files a sorted list
of actual Ref objects, returncode int or null if unreaped, finite nonnegative
elapsed, explicit phase string from setup/import/lookup/gate/cleanup/validate.
These failure records cannot satisfy successful schemas. Root owns bounded
polling/progress, publication and retention. This remains finite cold CPU proof,
not a new producer/hardware/tooling programme or permission to delay WIP20.
