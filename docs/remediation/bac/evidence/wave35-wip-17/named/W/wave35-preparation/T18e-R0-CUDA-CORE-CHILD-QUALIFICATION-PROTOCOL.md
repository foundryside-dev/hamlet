# CUDA core child qualification — nine finite roles, guard-only fork profile

2026-11-13. PROPOSED public protocol, not implementation or execution approval. Read only public tests report P/T18e-R0-CUDA-CORE-TESTS-REPORT.md, its embedded CHILD-API, accepted gate/design prose and supplier facts. No additional implementation body, source/tool edit, application/helper runtime, Git/index action, source copy or delegation. Retained five-helper source budget is unchanged. Test source835/b0f9e15457fa0a0f8e2b9cf0da63bd03b97ea96a11694d9bc74267c49fd75e60 and unchanged core371/9d6cd6fcfe62d8e53bda1e6ce7b34a89454ccc88373b5ec4cd072fe004ad66fb are report facts, not new body inspection.

## Exact finite outer admission map

Root uses one named job per node, one controller, no xdist. Command arguments are exactly -m pytest NODE --no-cov -p no:cacheprovider -p no:benchmark -p bac_source_identity -q. Node prefix is tests/test_townlet/regressions/bac/test_rng_cuda_admission.py. No alternate selectors or arbitrary suffix expansion.

| Job | Role / Process.name | Node suffix | Exact success message |
|---|---|---|---|
| cuda-core-bootstrap-failure | cuda_core_bootstrap_failure | ::test_isolated_poison_protocol[bootstrap_failure] | cuda core bootstrap_failure fail closed |
| cuda-core-runtime-query-failure | cuda_core_runtime_query_failure | ::test_isolated_poison_protocol[runtime_query_failure] | cuda core runtime_query_failure fail closed |
| cuda-core-local-completion-single | cuda_core_local_completion_single | ::test_isolated_poison_protocol[local_completion_single] | cuda core local_completion_single fail closed |
| cuda-core-local-completion-multiple-body | cuda_core_local_completion_multiple_body | ::test_isolated_poison_protocol[local_completion_multiple_body] | cuda core local_completion_multiple_body fail closed |
| cuda-core-poison-unknown-ready | cuda_core_poison_unknown_ready | ::test_isolated_poison_protocol[poison_unknown_ready] | cuda core poison_unknown_ready fail closed |
| cuda-core-poison-ready-qualified | cuda_core_poison_ready_qualified | ::test_isolated_poison_protocol[poison_ready_qualified] | cuda core poison_ready_qualified fail closed |
| cuda-core-poison-ready-healthy-only | cuda_core_poison_ready_healthy_only | ::test_isolated_poison_protocol[poison_ready_healthy_only] | cuda core poison_ready_healthy_only fail closed |
| cuda-core-operation-body-completion | cuda_core_operation_body_completion | ::test_isolated_poison_protocol[operation_body_completion] | cuda core operation_body_completion fail closed |
| cuda-core-inherited-pid | cuda_core_inherited_pid | ::test_isolated_inherited_pid_gate_refusal | cuda core inherited pid gates fail closed |

The first eight nodes/roles/messages are authored report facts; their job names above and the ninth node/role are proposed. Root and source author must adopt these exact names in the next capsule before helper implementation. Existing replay-poison and recurrent-replay-poison maps stay unchanged.

All nine outer children use actual multiprocessing spawn. Their full bootstrap identity remains unchanged, enriched with actual ppid, exact cuda_core_imports of townlet.exploration.rng_custody and test_rng_cuda_admission, and cuda_core_test_sha256 of actual test bytes. Expected source paths are R/src/townlet/exploration/rng_custody.py and R/tests/test_townlet/regressions/bac/test_rng_cuda_admission.py. Outer identity keeps the original three supplier imports, debugtrue, actual Torch version, intraop1/interop5 and current manifest/base/tree.

Exact parent observation fields remain the authored CUDA protocol: process_pid, queued_pid, parent_pid, queued_ppid, exitcode, qualified, message, manifest_sha256. Queued success tuple is (message, child os.getpid(), child os.getppid(), qualified). Match actual Process.pid, parent os.getpid(), child-owned pid/ppid and every actual manifest hash; require parent result exit0 and child exit0. Exclusive role-specific files are spawn-identity-ROLE.json and spawn-observation-ROLE.json. No parent-generated child identity.

## Ninth control: real inherited domain and live gates

Use one qualified spawn child to isolate two sequential fork trials, admission then local. The main pytest process never forks or acquires the tested inherited gate. The spawn child first completes the normal bootstrap identity and saves its own domain-health/ambient-state baseline. It constructs the real CPU-empty participant and finite source-owned local-contract fixture already accepted for this packet. Do not manufacture domain, participant, gate, PID or issuer authority.

For each trial, the spawn child enters a genuine live scope on its sole actual domain: domain.admission(lineage=None), then separately domain.local_cuda_access(participant=actual_participant, contract=actual_fixture_contract). Keep the real gate open and the actual domain lock held in the forking main thread until the grandchild is reaped. Do not fork an expired gate or obtain a fresh grandchild domain. The inherited references, original domain process identity, participant and open gate are the objects under test. No _pid patch, fake token, forged lineage or replacement-domain factory is allowed.

One fork per scope is deliberate: it proves both new gate families without relying on an unspecified nested admission/local composition. This remains one ninth pytest node/outer role with exactly two fixed grandchild trials, not unbounded roles.

Before each fork, measure actual Linux OS task count with /proc/self/task and require exactly1. threading.active_count alone is insufficient. Ensure no Queue.put has started a feeder thread in the spawn child before forking. Any non-single-thread observation is a prerequisite refusal, not a guard failure or skip-to-PASS. Existing outer bootstrap Torch thread configuration remains truthfully recorded even if no pool workers have started; it does not substitute for this OS observation. Root owns actual applicability evidence.

Pre-create an OS pipe, the input torch.device object, exception sentinel, plain counter containers, expected source paths and fixed method/action descriptors before fork. Use os.fork and its actual returned grandchild PID. The grandchild never calls bootstrap, process_rng_domain(), imports modules, starts a thread, invokes Torch/NumPy/CUDA, captures RNG state or flushes Python logging/pytest/queue machinery.

Inside the grandchild invoke only inherited guard entrypoints:

- admission trial: inherited gate.resolve_cuda(device=precreated_cuda_device), gate.enroll(participant=actual_participant, cuda_devices=()), gate.report_failure(error=precreated_error); fresh entry on the inherited domain.admission(lineage=None) must also refuse before lock acquisition.
- local trial: inherited gate.resolve_cuda(device=precreated_cuda_device), entering gate.complete(cuda_devices=()) with a counter-only body, gate.completion_failed(), gate.report_failure(error=precreated_error); fresh inherited-domain local_cuda_access entry must refuse before lock acquisition.

Each must raise the source-owner-specified inherited-process refusal, before any domain/owner acquisition, CUDA query/init/completion, completion/body callback or mutation. A generic RuntimeError, missing symbol, invalid fixture, unknown contract, scope/thread mismatch or timeout is not sufficient. Parent-created open gates establish the intended precondition; the PID mismatch is real os.getpid versus inherited issuing process. The grandchild does not unwind the inherited parent gate on exit.

Observe lock attempts through a transparent finite test-only forwarding probe around the actual sole RLock, installed before genuine gate entry. It must delegate all parent behavior and preserve access to the same actual lock, never supply fake ownership or bypass locking. Reset child-local counters after fork, before actions. Instrument the owner's actual lock similarly if reachable, and the already accepted finite CUDA seam with forbidden-touch counters; never report zero merely because no instrumentation exists. The implementation owner must confirm all lock entry/acquire routes are observed within its admitted core body. If a gate caches a raw lock bypassing the probe, fix the observation design before claiming pre-lock rejection. Guards are not mocked. Compare plain pre-fork domain state/first-cause values in the grandchild without calling domain APIs; a failed inherited report_failure must not mutate them.

No CUDA accessor should execute in the grandchild, including an identity probe. The device object is precreated, and forbidden CUDA seams do not run actual Torch code. Successful guard refusal yields all acquisition/CUDA/body counters zero and unchanged child-local domain state. The live spawn parent, after reaping and normal scope exit, verifies its genuine domain remains healthy and its ambient state equals entry; pytest parent separately preserves its existing healthy/ambient invariant. Fork memory separation alone is not a parent-health assertion.

## Guard-only grandchild evidence, distinct from spawn profile

Grandchild role is fixed cuda_core_inherited_pid_guard; trial is exactly admission or local. This is a separately named nested guard-only profile, not a tenth accepted top-level job. It never reuses the outer spawn identity schema or fabricates inherited Torch thread values.

Each grandchild exclusively creates fork-identity-cuda_core_inherited_pid-TRIAL.json using standard-library OS/file operations. Exact fields:

- schema = cuda-core-fork-guard-identity-v1; profile = linux-fork-inherited-guard-only-v1; role = cuda_core_inherited_pid_guard; trial.
- pid and ppid from grandchild os.getpid/os.getppid; inherited_domain_pid copied from the real inherited domain's issuing-process field, unchanged by the fixture.
- base_commit, candidate_tree and manifest_sha256 from the actual opened manifest bytes, matching the sealed outer identity; qualified is the actual complete-environment predicate, never a success default.
- cuda_core_imports: exactly the two inherited loaded module objects' actual resolved __file__ paths; module_origin = inherited-loaded-module-objects. Hash those actual files into source_sha256 keyed by the same two module names. No importlib/Torch probing.
- os_threads = actual /proc/self/task count (must1); torch_profile = null; torch_profile_unavailable_reason = no Torch calls permitted in fork guard-only process.
- guard_results: exact fixed action keys for its trial, each containing observed exception class/diagnostic, lock_acquire_calls0, owner_lock_acquire_calls0, cuda_touch_calls0, body_calls0 and state_unchanged true. These are measured outcomes, not prefilled success records.

No global source-inventory or Torch profile certification is claimed by this narrow record. The outside verifier independently checks the entire candidate inventory, exact two file hashes and outer source custody. Actual inherited Python module identity plus the archived source bytes establishes the named source binding; no fresh-import claim.

After successful assertions/write, grandchild sends a bounded UTF-8 JSON acknowledgement through the OS pipe with exactly trial, pid, ppid, identity_sha256, message. Message is cuda core inherited pid TRIAL fail closed. Cap payload at4096 bytes, handle complete writes/reads, then os._exit(0). On any exception, no success acknowledgement; optionally write a bounded failure diagnostic and os._exit(1). Never ordinary return through inherited context managers, atexit or multiprocessing cleanup.

Spawn parent exclusively creates fork-observation-cuda_core_inherited_pid-TRIAL.json only after actual waitpid confirmation. Exact fields: schema=cuda-core-fork-guard-observation-v1, trial, role=cuda_core_inherited_pid_guard, parent_pid, fork_pid, waitpid_pid, wait_status, exit_code, queued_pid, queued_ppid, identity_sha256, message, parent_os_threads_before_fork, manifest_sha256. Parent pairs fork return PID = waitpid returned PID = pipe PID = child identity PID; pipe/identity PPID = actual spawn parent PID; inherited_domain_pid = same parent PID != grandchild PID. Require WIFEXITED and exit0; don't treat signal termination as exit0.

Only after both exact trial records and genuine parent invariants pass does the spawn child queue its ninth-role success to the original pytest parent. Thus the parent job, qualified spawn and two guard grandchildren form one explicit evidence chain.

## Owned timeout and cleanup

Use monotonic total deadline (10seconds per grandchild), nonblocking waitpid(WNOHANG) plus bounded pipe readiness/read. No blocking read before the wait deadline is established; EOF without a complete valid acknowledgement fails. Spawn parent closes its pipe write end immediately; grandchild closes read end. In finally, terminate only its unreaped fork child, reap it with bounded escalation, close descriptors; never signal a reaped/reused PID. A timed-out guard is failure, not successful wrong-PID rejection. Outer existing90second spawn join/owned terminate/queue cleanup remains.

Require actual Linux/POSIX os.fork, waitpid and /proc support and observed single-thread precondition. Other platforms are explicitly NOT APPLICABLE/UNRUN, never substitute spawn as inheritance evidence. Real CUDA initialization/use in either forking process is forbidden for this CPU guard control. Actual one-/two-GPU qualification remains separate.

## Proposed verifier extension boundary

Use explicit finite per-job configurations for the nine outer mappings above, with CUDA outer identity/observation schemas separate from the two existing replay schemas. Retain all existing replay invariants and exact nodes unchanged. CUDA observations add queued_ppid; CUDA identities add the two core imports and actual test hash. No optional broad acceptance of unknown fields or arbitrary role prefixes.

The ninth config additionally requires exactly the two named fork identity/observation pairs, exact trial/action sets and guard-only schema/profile. Check all source hashes against candidate inventory; exact ancestry/manifest/role/message pairing; parent single-thread observation and grandchild actual single-thread count; no Torch numerical fields in guard records; no unknown trial, missing record, extra success, PID reuse/equality, signalled child or mixed-role replacement. Root captures actual effective CPU environment externally; verifier does not invent it from null fields.

Synthetic tooling controls must reject wrong nodes/jobs/messages, altered source/import/hash, wrong outer/inner PID/PPID or waitpid, wrong trial/action sets, missing guard records, fake Torch profile, non-single-thread profile, nonzero effect counters, incorrect refusal diagnostics and mismatched manifest/result. Valid nine-role fixtures must pass while both replay roles keep passing. Tooling grant/review and actual root source-bound execution are separate future steps.

## One specific unresolved prerequisite

The source owner must publish the exact inherited-PID exception class and stable diagnostic predicate from its admitted core body, and confirm which plain issuing-PID/state slots and transparent lock probe cover the actual paths. Existing public prose does not supply that diagnostic. Do not weaken the assertion to any exception, or fabricate a new production error implementation in tests. This is a small supplier fact within the owner's existing two-body budget, not a sixth-body request or acceptance waiver.

Until that capsule and the added ninth test are frozen/reviewed, this protocol is a concrete proposal and genuine inherited-PID evidence remains UNRUN. The child tests may grow within the author ceiling1200 lines/two-body2400; if the finite instrumentation cannot fit, surface exact budget pressure rather than remove guards. No hardware or B6 acceptance follows.
