# B cold-import qualification — bounded proposal

2026-11-14. PROPOSAL ONLY. Implement and execute only after root publishes
WIP20 and grants the new bounded writer/runtime packet. Root owns source
integration, actual collection, command execution and evidence publication.
No application import, collection, test, child, lint, Git action, branch,
worktree, checkout, source execution copy, source edit or delegation occurred
while preparing this proposal. This named proposal is the only write.

## Read boundary, seals and reservation

Read AGENTS.md, the admitted source/test sections and prose supplier packets.
Only these two implementation/test bodies were admitted; no producer, helper,
other test or verifier body was read, including by diff/introspection/import.

| Body | Whole lines | SHA256 |
| --- | ---: | --- |
| `src/townlet/exploration/rng_custody.py` | 1195 | `6cb01ca77b58db5f4c4784dc36da566c06cf68c2a7c2ce227bb780549f3344f8` |
| `tests/test_townlet/regressions/bac/test_rng_cuda_admission.py` | 2360 | `6ec962f9c0b3d467375528b26de39bac154b46e4d5c6435ffcc289960f063085` |

Total3555/two, hard5000/five. Reserve <=650 added test lines, making
test<=3010 and total<=4205/two with unchanged core, leaving795 hard-limit
lines. Root accepted this prospective reslice FOR DESIGN ONLY; the later
implementation grant must replace the former test2500/combined3750 packet.
Headroom alone does not grant implementation or execution.
No new helper or other implementation body is proposed. No required existing
control may be dropped, moved, compressed or weakened to meet the reserve.
If actual clean implementation needs more, stop for a named reslice.

Consumed lifecycle requirement: producer B activation preparation SHA256
`a1c6b789046d60089fe4f852f7935ca6d8a48c8e808ab193ac062d315ca6f719`,
row `Resolver/import lifecycle`. Consumed private interface capsule SHA256
`851d113a120c5fcd40d7f11cb7731c9fb67e6c2d8c5b74dd2670c367a0e73ad3`.
Its formerly intended resolver/cache names agree with current admitted core.
Existing core test imports custody at module top level. Its ordinary spawn
target imports that test again; it cannot establish application coldness.
Existing exact18 warm resolver/cache and inherited-PID controls remain intact.
Root supplies existing89 core and67 activation controls; this worker ran none
and did not inspect the activation body or claim its collection.

## Mechanism and exact positive nodes

Add one ASCII, non-f-string, literal `_COLD_IMPORT_PROBE` in the existing
core test. It is authored probe code, never an application-source copy. It
imports no test module, bootstrap helper, pytest plugin or hidden fixture.
The parent uses `subprocess.Popen`, not a multiprocessing target importing
the warmed test. Use exactly this argv shape, all strings:

`[resolved_python, "-I", "-c", probe_literal, mode, entry, root, output, nonce]`.

`resolved_python` is the canonical current interpreter, not a PATH lookup.
`root` is the canonical current checkout; cwd is that root. Python `-I`
excludes ambient PYTHONPATH/current-directory injection. The probe explicitly
inserts exactly canonical `root/src` before its first application import.
That is the declared source path, not an implicit editable/install fallback.
There is no uv sync/install, copied source, sys.modules deletion, replacement
application module, reload or claim that clearing caches makes an import cold.

The three positive entries and roles are a closed table:

| Pytest suffix | entry | First selected application import | role |
| --- | --- | --- | --- |
| `test_fresh_process_canonical_import_order[core]` | `core` | `townlet.exploration.rng_custody` | `cuda_core_cold_import_core` |
| `test_fresh_process_canonical_import_order[flat]` | `flat` | `townlet.training.replay_buffer` | `cuda_core_cold_import_flat` |
| `test_fresh_process_canonical_import_order[per]` | `per` | `townlet.training.prioritized_replay_buffer` | `cuda_core_cold_import_per` |

All node prefixes are the current core regression filename plus `::`.
`mode` is exactly `qualify` for these roles. These are three actual exec
children, not three statements about a single warm child. In core mode,
assert both producer modules are absent immediately after core import, before
explicitly loading producers. In flat/per mode, select that producer first;
dependencies that it genuinely imports are part of its actual import graph.
Record actual initial entry and modules present at each checkpoint rather
than requiring an invented total dependency order.

## Assertions inside each positive child

1. Before Torch import, assert no key equal to `townlet` or starting
   `townlet.` exists in sys.modules. Record the exact empty list. Import real
   Torch, configure declared CPU threading, then assert the same empty list
   again. Reject any startup/site contamination; do not clean it up.
2. Install a NoCUDA object as `torch.cuda` before the selected application
   entry. Every attribute access increments a counter and raises a specific
   sentinel exception. Recheck application-module absence immediately before
   selected entry, after installing it; this is the boundary deliberately
   broken by the preloaded negative fixture. Retain it through constructors, failed
   lookups, genuine gates, completion, cleanup and final observations. Verify
   its identity is unchanged and counter remains zero. CPU Torch calls do
   not constitute GPU qualification.
3. During initial selected-entry/dependency imports, instrument calls to the
   source `_local_cuda_policy` and `_resolve_local_cuda_record`: any call is
   an immediate failure. A forwarding builtins import observer also rejects
   canonical producer imports requested by custody during this phase, using
   the actual caller globals name, fixed module names and fromlist. Record
   zero such calls. It must forward every allowed import to the real import
   function, never supply a fake class/module. Restore observers before real
   gate work. Core-first producer absence plus this observation and current
   fixed-import resolver source support deferred lookup. This is not a
   general Python import-hook purity theorem.
4. After selected import, get actual custody through normal import. Verify
   its resolved file is canonical root/src path and the sole domain PID is
   the actual child PID. Its policy cache is genuinely empty; do not replace
   it with an empty dictionary. Verify all18 exact exported contracts are
   distinct opaque source-issued identities and the complete immutable
   manifest is exactly those identities, with reviewed tags/routes/bits.
   Use a fixed literal expected18 table in the probe; do not generate the
   expected universe from the observed manifest. It matches the existing
   core exact18 oracle, including flat load_for_mode and no PER nineteenth.
5. Load both canonical producers normally and construct actual CPU flat/PER
   owners using supplier-confirmed constructor calls and their real existing
   registered participants. Do not synthesize fixture subclasses or replace
   the manifest. Assert exact type, strong owner retention and real domain
   member-to-owner binding. Constructors must leave the cache empty and
   CUDA untouched. Root supplies these source-qualified actual expressions:
   ReplayBuffer(4, torch.device("cpu")) and
   PrioritizedReplayBuffer(4, 1.0, 0.0, False, torch.device("cpu")). Each
   owner exposes rng_participant; owner._replay_lock is its actual lock and
   owner._owner_operation(mutation=False) its genuine private owner context.
   Cleanup is domain.unregister(participant=owner.rng_participant), then
   child exit; assume no dispose method. These are attributed supplier facts,
   not extra producer bodies read by this worker.
6. Install a forwarding resolver counter, saving the genuine bound resolver
   and delegating every call to it. Attempt both families' serialize contract
   before any success: temporarily remove only the real producer module's
   canonical class export from its actual __dict__, retain the actual class
   and owner strongly, then call real local_cuda_access with that owner's
   real participant. Expect actual ImportError; no gate body may execute.
   Cache stays genuinely empty, gates stay empty, CUDA counter stays zero,
   permission/health/currentness state stays unchanged. Restore the exact
   export in finally before any further work, also on failed assertions.
   Never alter sys.modules or insert a stand-in class. Removing an export
   tests failed canonical lookup; it is not described as a partial-import
   simulation. Both failures happen with a cold cache in a fresh process.
7. After restoring exports, use only the two genuine SERIALIZE_CUDA
   contracts, one per canonical family. Their FIRST successful lookup must
   occur through actual local_cuda_access,
   not a preceding private _local_cuda_policy call. Use the actual matching
   owner/participant. While the real domain gate is held, enter the real
   owner lock, then gate.complete(cuda_devices=()). Inspect live _Gate,
   exact cached descriptor/policy tuple, exact canonical owner/input class,
   route, rationale and independent healthy=True/post_poison=False bits.
   Require exact policy identity throughout completion and close. Each first
   success adds one cache entry, preserves prior entries' tuple identities,
   and calls the genuine resolver exactly once successfully.
8. Repeat both gates, again completing with an empty device tuple. Require
   the same cache tuple, same policy object and no extra resolver call.
   Two distinct policies survive, bound to their correct actual classes;
   the other16 contracts remain unresolved. This avoids repeating the
   already-required warm all18 canonical/input-policy control. Count two
   expected failed resolver attempts plus two successes, never
   treating failures as cache hits. Assertion observations use actual `is`
   relationships in-child; serialized ids are only that process's evidence.
9. Every completion finishes with completion_failed() is False while the
   gate is live. Closing gates leaves no active gates/operations; cleanup
   unregisters real participants using the supplier-confirmed lifecycle.
   Do not reset health, readiness, revision, membership generation or poison.
   Compare only state that pure resolution/empty completion must preserve;
   real constructor/registration/unregistration generation changes are
   recorded separately and must not be mistaken for resolver side effects.
   Retain baseline/final CPU RNG observations and exact health/readiness
   facts. Emit success only after all checks and cleanup pass.

The serialize contracts' exact canonical input type is type(None). The
existing warm all18 control retains its complete canonical input map. This
cold probe qualifies real canonical class/cache/gate binding; it executes no
replay leaf and does not replace the separate18-public-route producer ledger.

## Actual process, source and command provenance

Do not call existing child_identity/bootstrap in the probe: that would import
the warmed test/helper graph. Root's strict owner adds a distinct finite
profile `linux-exec-cold-import-v1`, not the existing spawn or inherited-fork
profile. Existing profiles and strict acceptance remain unchanged.

Before Torch, the parent supplies its reviewed CPU thread environment in a
child-only env: at minimum OMP_NUM_THREADS, MKL_NUM_THREADS,
OPENBLAS_NUM_THREADS, NUMEXPR_NUM_THREADS, VECLIB_MAXIMUM_THREADS and
BLIS_NUM_THREADS are all `1`. Probe explicitly sets Torch intra/inter-op
threads to1, observes actual getters, actual threading.enumerate main thread
and actual `/proc/self/task` count. Require one Python and one OS task at
the cold checkpoint and final checkpoint; do not substitute configured values
for actual observations. If the supported build cannot meet this profile,
preserve rejection and seek an explicitly reviewed concrete profile.

Child independently reads the canonical candidate manifest and verifies
base_commit/candidate_tree against the qualified environment, canonical root
and admitted source hashes. Record actual loaded Townlet module origins and
their source SHA256s, ensuring each lies under canonical root/src and matches
the sealed candidate inventory. No installed-origin fallback is accepted.
Include Torch/NumPy/Python actual versions/origins and interpreter identity.
The root manifest/source verifier owns the exact allowed dependency inventory;
this worker has not read those dependencies. Hashing provenance is not a
license to inspect extra source bodies during implementation review.

Derive actual argv from sys.orig_argv and cross-check `/proc/self/cmdline`;
hash the actual `-c` argument bytes as `script_sha256`, not a supplied digest
echo. Define `command_sha256` over UTF-8 JSON of the full argv with
ensure_ascii=True and separators=(",", ":"). Parent captures identical
launch argv/hash. Hash executable file, actual Python binary path, final test
bytes, manifest bytes and all recorded source files. Root verifier statically
extracts the one literal probe assignment from those sealed final test bytes
using AST, without executing/importing them, and hashes its evaluated string
bytes. It requires child actual-script hash == parent command script hash ==
that source-derived literal hash. Reject nonliteral/reassigned/dynamic probe
definitions and argv variants. This makes source the trust anchor rather than
allowing a child to proclaim a script hash or unfamiliar role.

## Finite evidence schemas

All JSON objects reject extra/missing fields, duplicate keys, wrong primitive
types, bool-as-int and unknown enum values. Integer ids are positive and
compared only within their issuing process. Cross-process identity binds
PID/PPID/nonce and bytes, never assumes object-id equality.

Child filename: `cold-import-identity-{role}.json`, exclusive creation only.
Exact top-level keys:

`schema, profile, role, mode, entry, nonce, pid, ppid, parent_pid,
base_commit, candidate_tree, manifest_sha256, root, cwd, executable,
executable_sha256, python_version, argv, command_sha256, script_sha256,
test_path, test_sha256, source_modules, runtime, threads, cold, checks`.

`schema=cuda-core-cold-import-identity-v1`; profile and mode as above.
`source_modules` maps each strictly allowed actual module name to exactly
`path, sha256`; origins must match the final sealed candidate. `runtime`
has exactly `torch_version, torch_path, numpy_version, numpy_path`.
`threads` has exactly `environment, python_before, python_after, os_before,
os_after, torch_intraop, torch_interop`; environment is the exact root-admitted
finite variable map, thread snapshots contain actual name/ident/native_id.
`cold` has exactly `townlet_before_torch, townlet_after_torch,
townlet_before_selected, selected_entry,
producers_after_selected, eager_policy_calls, custody_producer_imports,
cache_before_owners, cache_after_owners`.
Empty lists/caches/call counts must be observed, not default-filled.

`checks` has exactly `missing_exports, gates, cache_size, cuda_calls,
cuda_sentinel_unchanged, domain_pid, health_before, health_after,
ready_before, ready_after, rng_unchanged, cleanup_complete`.
`missing_exports` is exactly two records in flat/per order, each with
`owner_kind, contract, exception_class, export_restored, cache_before,
cache_after, gate_body_calls, cuda_calls`; class is builtins.ImportError,
cache lists are empty and body/CUDA counts are0. `gates` is exactly four records,
flat/per serialize first pass then flat/per repeat pass, each with `pass, contract,
owner_kind, route, contract_id, descriptor_id, policy_id, cache_tuple_id,
owner_id, participant_id, canonical_owner_identity, canonical_input_identity,
descriptor_identity, cached_policy_identity, live_policy_identity,
completion_failed, resolver_calls_before, resolver_calls_after`.
All identity assertions are True, completion_failed False, cache_size2,
zero CUDA calls, successful cleanup and reviewed health/readiness/RNG values.
If additional observations become necessary, version this exact schema and
obtain owner review; do not accept a generic arbitrary `checks` dictionary.

Parent filename: `cold-import-observation-{role}.json`, exclusive creation.
Exact keys: `schema, profile, role, mode, entry, nonce, parent_pid, child_pid,
child_ppid, argv, command_sha256, script_sha256, manifest_sha256,
base_commit, candidate_tree, test_sha256, identity_sha256, stdout_sha256,
stderr_sha256, exitcode, timed_out, termination, reaped, elapsed_seconds`.
Schema is `cuda-core-cold-import-observation-v1`. Require actual Popen PID ==
child PID, PPID == actual pytest worker PID, positive elapsed within bound,
exitcode0, timed_out=False, termination=`none`, reaped=True. Identity hash
must be of exact child file bytes. Qualified parent worker PID/source/thread/
command/candidate custody remains rooted in the existing root-run receipt;
the new observation cross-binds that actual worker, not merely its shell PID.

Use exclusive attempt directories and nonce, direct stdout/stderr files,
start_new_session=True and a90-second deadline. On timeout terminate the
created group, wait<=5 seconds, kill that group if necessary, wait/reap<=5;
always close handles. Preserve partial identity, logs, exceptions, returncode,
timeout/escalation facts and failed attempt; never create a success record
after failed cleanup. Root may use bounded polling to maintain updates.

## Collection, faulty-fixture preflight and acceptance

Preserve all89 existing core node IDs and all existing selection/profile
semantics. Three positive additions imply92 source-expected core nodes;
actual root collection and set comparison are mandatory before qualification.
Do not add collection-time application imports beyond the existing custody
import; the probe remains inert literal text until the test launches it.

Before accepting positive evidence, qualify the fixture itself. Propose two
additional finite nodes in the same bounded core test:
`test_cold_import_probe_faults[preloaded]` and
`test_cold_import_probe_faults[cuda_touch]`. The concrete proposed collection
is therefore94 expected core nodes (existing89 plus these five additions).
Root must collect that exact delta and run the two faulty-fixture nodes as
an explicit preflight selection before the three positive nodes. Re-running
them in the complete core selection does not create additional unique tests.
The same sealed literal supports only these two additional fixed modes:
`preflight_preloaded` imports real custody after sentinel setup but BEFORE
the cold boundary and must fail that boundary with the exact expected
AssertionError; `preflight_cuda_touch` attempts one CUDA attribute lookup and
must fail with the exact sentinel diagnostic. No clearing module state and
no successful identity is permitted. Their finite roles are
`cuda_core_cold_preflight_preloaded` and
`cuda_core_cold_preflight_cuda_touch`; they produce only negative observation
schema `cuda-core-cold-import-negative-v1`, never a positive child identity.
Require nonzero exit, actual child/PID/argv/source/script/log hashes, expected
diagnostic, bounded cleanup and absence of success files. Unrelated failures
do not qualify these controls. Preserve stderr traceback in full.
Exact negative-observation keys are `schema, profile, role, mode, entry,
nonce, parent_pid, child_pid, argv, command_sha256, script_sha256,
manifest_sha256, base_commit, candidate_tree, test_sha256, stdout_sha256,
stderr_sha256, exitcode, timed_out, termination, reaped, elapsed_seconds,
expected_exception_class, expected_diagnostic, matched, success_file_absent`.
Entry is core for both negative roles. Preloaded expects
builtins.AssertionError and diagnostic `cold import precondition violated`;
cuda_touch expects builtins.RuntimeError and diagnostic
`cold import CUDA sentinel touched`. Require matched=True,
success_file_absent=True, actual nonzero exit, no timeout and complete reaping.
The parent obtains diagnostic/class from the exact final traceback line,
checks its expected fixed value, and retains full stderr bytes for review.

Strict-owner preflight also mutates COPIES of a valid record pair to reject:
unknown role/profile/mode; wrong/missing entry; parent/child PID mismatch;
script/test/source/manifest/command hash mismatch; installed module origin;
nonempty pre-import module set; fake zero defaults/missing check; wrong
thread count; missing one of18 manifest contracts/four gates; failed cache identity;
cache entry after missing-export failure; nonzero CUDA touches; false cleanup;
timeout/nonzero exit; duplicate JSON keys; extra unknown fields. Original
attempt bytes are immutable. These are parser/provenance rejection controls,
not extra successful application executions or generic role acceptance.

Root runs reviewed fixture preflight before the affected canonical positives,
then reruns final-byte existing core89 and required activation/producer and
strict-profile selections. Report exact collected/selected/unexecuted IDs and
unique union counts; do not sum overlapping selections. Final independent
bounded review must reconcile all source/schema/probe/test hashes and actual
records. Failed and unexecuted attempts remain published with their scopes.

This proposal closes no qualification by itself. Cold CPU protocol evidence
does not establish producer leaf purity, post-poison permission, actual GPU
execution, mixed-device legality, parent outcome integration, B6/R0 or
whole-programme acceptance. WIP20 publication remains root's current task;
this preparation is not authority to delay it or begin this implementation.
