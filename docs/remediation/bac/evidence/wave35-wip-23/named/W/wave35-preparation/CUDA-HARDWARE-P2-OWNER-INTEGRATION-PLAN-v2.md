# P2 owner integration implementation plan v2

Linked correction to immutable v1 SHA256 `b87c79f807782985d0135e353b3ddf610a918c1b3f20114364570736fdaa7a97`: whole-call timing vectors belong to P4/P5; P2 implements no parallel timing validator. No other scope expansion.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans after root grants this bounded implementation. This document grants no execution or source mutation.

**Goal:** Update P2 transport validation for the adopted P3 owner producer and prove owned-group cleanup after actual abrupt guard death with live Git.

**Architecture:** Replace raw-v1 validation with raw-v2 and closed owner ancestry/claim/sampler/emission validation inside the existing runner. Preserve P0 transport and P2 actual launch/wait custody. P4 independently validates transport correspondence and timing; P5 authenticates source-owned call/return, payload, pipe/wait and strict actions.

**Tech Stack:** Python, closed JSON references, Linux process groups, existing P0 no-follow reference validation, existing inert pytest harness.

**Spec:** `CUDA-HARDWARE-P3-OWNER-AMENDMENT-PROPOSAL-v2.md`, `CUDA-HARDWARE-P3-OWNER-TIMING-AMENDMENT-v2.md`, adopted P3 `interface-contract-v5.json`, and `CUDA-HARDWARE-P2-P4-COMPLETION-CORRESPONDENCE-v1.md`. Exact references and authentication results are in `../evidence-management/hardware-runner-p2/owner-integration-plan/input-inventory-v2.json`.

## Global constraints

- Planning only; root reviews and grants implementation separately. No APP/Git/index/runtime/worktree/branch/copy operations in this planning pass.
- Root owns the sole candidate. Another APP writer remains active. Existing 14 registered/1 available worktree state is untouched and is not freshly remeasured here.
- Body budget: three charged whole files, 2,734 lines; ceiling five files/5,000 lines. Modify only `Q/run_bac_hardware_v1.py` and `Q/test_run_bac_hardware_v1.py`; read-only dependency `Q/bac_hardware_protocol_v1.py`. Q is `/workspace/bac-review-2026-11-01/qualification`. No P3/P4/P5/APP body expansion.
- Current P0 is the adopted 526-line module-alias amendment, not P2 freeze-v2's historical 520-line dependency. Historical freeze/reviews stay immutable; new freeze pins current exact dependencies.
- Replace obsolete raw-v1 fixtures/readers directly. No compatibility adapters, fallback paths, defaults, inferred authority or acceptance by exit zero alone.
- Keep 3 seconds each complete recorder call, 6 seconds cumulative complete calls, 8 seconds absolute returns, original 10 seconds acknowledgement/reap. Valid return at 7.9 seconds and acknowledgement at 8.1 seconds remains eligible.
- No Torch/CUDA/APP import in P2. Pure tooling results never discharge APP, CUDA, package, coverage, type, final CI or remote identity gates.

## Review focus

1. Resealed cross-case/nested-parent owner records must fail semantically, not only through stale hashes (Task 2).
2. Python assertions and Torch anomaly have independent meanings; false anomaly with true Python debug is valid (Task 1).
3. Process END plus sampler/emission does not prove an actual completed function return (Tasks 3–4).
4. Missing declaration cannot be repaired by later result/seal inventory membership (Task 3).
5. A killed guard cannot execute finally; a live Git descendant must be terminated by P2's existing owned-group backstop before leases release (Task 4).

## Baseline and finite boundary

P2 `Custody.process_context` currently accepts only raw-v1, requires delegated policy/runtime for every process, and explicitly refuses owner children. `evidence` separately checks own source witness and process pairing; `result` copies five validated completion arrays exactly. The test body is **test_run_bac_hardware_v1.py**, 959 lines, not test_bac_hardware_runner_v1.py. Existing generated `SUCCESS_CODE` is raw-v1 and must change with the reader.

Use existing `run(spec_path: Path) -> int`, `Custody.process_context(self, job, record, role, envelope)`, `Custody.evidence(self, job)`, and `Custody.result(self, job, observation, attempt)` entry points. Add only private methods `Custody.owner_context(self, job, record, role, raw, envelope, ancestry) -> dict` and `Custody.owner_sampler(self, job, record, raw, launch, launch_ref, envelope) -> None`; ancestry is a set of visited exact process-start references represented by `(path, bytes, sha256)`. The former returns the validated launch; neither method accepts caller trust flags. All data are closed JSON dictionaries; invalid/missing facts raise ValueError through existing validation paths.

Producer/consumer division:

| Owner | Required deliverable |
|---|---|
| P3 adopted supplier | Current raw-v2, acyclic owner launch/claim, source witnesses, sampler commands and post-process emission; actual owner return is outside its observation boundary. |
| P2 this grant | Authenticate transport and finite owner ancestry, complete owner evidence inventory membership, source/phase/environment/resource bindings; preserve actual job launch/wait/result/seal and group cleanup. |
| P4 separate grant | Independently revalidate P2/P3 references, five-array completion/result equality, producer versus result/seal inventory scopes, and timing arithmetic with actual source-qualified owner rows and parent custody. |
| P5/APP separate grant | Actual Process/context/os.fork and PID/start identity; actual owner entry/return bracketing, strict payload and pipe acknowledgement/wait correlations; 4/7/5 trials/actions, RNG and source-owned inter-op=5 setup. `launch.start_method` alone proves none of these. |

P2's transport `successful` continues to mean the declared orchestration evidence passed; it does not assert P4/P5 satisfaction. P2 may not generate or infer missing owner returns, acknowledgement, reap, payload or validators.

## Prerequisites and exact supplier requests

Root must grant the two-file edit scope and freeze exact P3/P0 references from the inventory. Before actual source-dependent integration, supply a current single-candidate grant and read-only Git/source lease; the historical R129 P3 lease cannot authorize current APP bytes. The current APP writer must be quiescent for that interval. No new candidate or branch is created by this plan.

The P3 interface and proposal supply the closed owner/raw/sampler schemas and public APIs. P4 `validator-interface-proposal-v3.md` and P5 `interface-decision-and-owner-requests-v2.md` supply a proposed fixed pure-data `validate_child_obligation(subject: dict) -> dict`, with subject `{schema,spec,job_id,obligation_id,documents}` and referenced actual bytes; this is **not an implemented validator**. P4 emits the causal validation receipt and keeps its aggregate obligation gate incomplete when strict work is absent. Before Task 4 full-chain execution, P4/P5 must supply **metadata only** with: (a) adopted exact strict payload and parent-custody enclosing schema/field sets and fixed locator from obligation payload to both; (b) actual implementation/receipt hashes for that proposed interface; (c) owner-contract case/role/method mapping and source instrumentation qualification status. The timing amendment already fixes return/custody row shapes, but the enclosing payload locator and phase wrapper remain finite contract-design work; validator/APP implementations are separately absent. Root can have one supplier reviewer reconcile these facts; no repeated planning loop. Their absence blocks full-chain qualification, not raw-v2 tooling work or backstop tests. Authored inert fixtures must be labelled as such and cannot certify APP/HW.

For live inert P3→P2 tests root supplies explicit CPU/RAM/scratch bytes/inodes and input-byte reservations including runner/controller, owner, concurrent Git, output receipts and retained failed attempts. Use current `bac-hardware-cpu-bound-v1`, exact sampler-policy justification, grant.cpu_reservation_evidence membership, and pinned Git executable in environment.dependencies. Existing role/job/allocation/grant checks remain. Run one serial pytest controller with explicit inherited affinity and thread environment 1; no `-n auto`, no assumed 16 slots. The later server with 16 workers and CUDA has unknown access/allocation details and remains a separate hardware admission prerequisite.

## Task 1: Current raw-v2 and debug semantics

**Files:** Modify runner `Custody.process_context` (baseline line 1041 onward) and test `SUCCESS_CODE`/existing process tests. P0 stays read-only.

**Consumes:** Exact raw-v2 field set in P3 interface-v5. **Produces:** Current ordinary/controller/worker validation without old-schema acceptance.

- [ ] Add `test_raw_v2_closed_and_debug_semantics`, parametrized over old-v1, missing/extra fields, bool-as-optimize, wrong source_method, wrong recorder_mode, false Python debug, optimize>0, false anomaly with Python debug true, observer/absent-Torch unavailable anomaly and work END missing threads. RED must fail for the intended new behavior, with immutable exact source/log/result references.
- [ ] Replace `_closed` raw-v1 with raw-v2. Require actual Python bool true and exact uint optimize zero; `source_method=direct-git`; ordinary mode outside guard. For nonfork P0 debug is measured Python debug with raw provenance independently of Torch. Keep thread facts unavailable when unloaded/observer and measured for loaded work; compare measured role config. Validate anomaly observed-bool independently; no Torch getter/import by consumer. Keep CUDA marker/no-initialize binding.
- [ ] Update all old success fixtures to current raw-v2 explicitly; require `owner_claim=[]` and `sampler=[]` on controller/worker. Run targeted new test and existing P2 suite under the granted tooling execution wrapper; retain RED/GREEN and exact current source pins. A stale fixture rejection is not the new regression proof.

## Task 2: Owner ancestry and exclusive claim transport

**Files:** Runner `process_context`, new `owner_context`, `evidence`; existing test body.

**Consumes:** P3 owner-launch-v1, owner-claim-v1, current context; P0 case-contract/reference/process. **Produces:** Validated launch and exact owner context rooted in the actual P2-launched controller.

- [ ] Add `test_owner_context_chain`, parametrized over controller→spawn, worker→spawn, spawn→fork, foreign parent, wrong PPID/start/host/boot, parent cycle, wrong case/phase/contract/role/method, forged environment key, duplicate instance/claim identity, missing claim, crosswired claim, stale reference and resealed reference. RED includes actual public `run` rejection of a valid new owner fixture.
- [ ] Implement `owner_context` with closed launch/claim fields from interface-v5. Read every ref through P0 no-follow validation. Require fixed owner-launch/claim filenames and job-local refs, selected exact obligation/case-contract, admitted role config and case, call phase, unique instance, actual immediate parent START and source identity. Follow parent starts with cycle rejection to the validated controller/worker lineage, never treating empty policy/runtime as authority. Across start/end bind one claim/launch/identity, distinct actual process identity, parent PPID/start/host/boot and job launch/reap lifetime. Refuse duplicate claims assigned to distinct children.
- [ ] Derive child context exactly from authenticated parent: copied static fields; role=launch child role; parent_start singleton; lifecycle singleton launch; empty replacement/policy/runtime; worker_identity null. Controller/worker retains existing delegation/lifecycle checks. Pytest parent launch environment equals parent START map plus exact current case `(call)` key; nested owner uses its full existing map unchanged. Child START/END equal launch environment. Inherited worker keys do not make child a worker. Bind actual child argv/cwd/interpreter/imports; fork argv and module set equal launch, spawn argv remains actually observed.
- [ ] GREEN targeted matrix and existing suite; publish exact failure reasons/retained outputs. Do not claim actual start-method or pytest source custody from declarations; those are P5 acceptance facts.

## Task 3: Sampler/emission source and inventory correspondence

**Files:** Runner new `owner_sampler`, `evidence`; existing tests.

**Consumes:** Exact sampler observation/emission fields and command row from interface-v5 and timing-v2; owner policy from job.prerequisites. **Produces:** P2 transport proof for each guard START/END, never whole-call timing proof.

- [ ] Add `test_owner_sampler_transport`, with valid pair and individually missing/crosswired/extra/type-invalid launch, claim, sampler, raw, process, emission, source and command log/diagnostic refs; changed phase/source/identity/module hash; truncated/nonzero/unreaped-shaped command; source-stage cumulative mismatch; wrong policy/CPU bound/Git binary; source inventory omission. Reseal semantic mutations so digest errors cannot mask missing checks.
- [ ] Implement `owner_sampler`: fork only, singleton sampler and claim; fixed phase filenames, same launch/policy/identity/phase and exact emission sampler/raw/process refs. Empty sampler profile for spawn/ordinary. Validate exact positive policy numbers, role membership, root prerequisite and CPU-bound/grant correspondence. Require original 10/8/6/3 bounds and explicit reserves/output caps. Verify each command's exact pinned Git argv, PID, nonnegative chronological timestamps, zero exit, nontruncated bounded stdout/stderr, retained diagnostic equality and Git HEAD/tree correspondence to process source witness. Bind same host/boot clock domain, lock interval and sampler stage chronology; source-stage cumulative is the sum of completed sampling intervals only. Emission timestamp follows sampler/source/raw/process writes and module hashes agree. Neither sampler end nor emission timestamp is labelled return time.
- [ ] Enforce a **new explicit owner-local closure**, not a retroactive statement about old P2: each admitted owner START/END, raw, launch, claim, source witness, sampler, emission and command diagnostic/stdout/stderr ref must be exact members of completion.inventory. Each owner's source witness must also occur in completion.source_witnesses. Immutable external contracts/policy/grants/dependencies are independently hash-bound refs, not required inside job output or result.inventory. Reject duplicates/contradictory same-path refs. General nonowner transitive closure is outside this amendment.
- [ ] Add `test_owner_completion_result_correspondence`: validate unchanged exact JSON values/order of collected_ids, outcomes, process_records, obligation_records and source_witnesses in successful completion→result; prove omitted raw/owner closure cannot be repaired by its later result inventory. Result inventory remains a fresh sorted job-local snapshot excluding result; seal is later attempt-wide excluding itself. Do not require completion.inventory=result.inventory or a general external-ref subset relation. GREEN all transport and original suite cases.

## Task 4: Actual backstop and finite full-chain acceptance handoff

**Files:** Existing P2 test body only for actual backstop tests, unless a demonstrated defect requires a narrowly reviewed `_terminate`/`execute_jobs` repair. The P4/P5 whole-call timing matrix below is a supplier handoff, not P2 test/code scope. No supplier-body edits.

**Consumes:** Actual public P2 runner, adopted P3 API, root execution custody; P4/P5 metadata prerequisite for full-chain rows. **Produces:** independently reviewable live cleanup evidence and an explicit qualification matrix.

- [ ] Add `test_actual_guard_sigkill_live_git_backstop`. Under a real owned job process group, start the adopted P3 fork recorder with a deliberately stalled **actual Git executable**, e.g. a verified test-owned FIFO config input with explicitly sealed argv/environment and resource grant; no mock process or fabricated sampler PID. Establish Git PID/start/PGID and live stall from observed handshake/kernel facts, then SIGKILL the guard while Git is live. Retain actual guard wait, missing return/ack, partial sampler output and controller completion/failure facts. Bound the test externally; cleanup may target only that test-owned group. If the exact adopted Git invocation cannot induce this stall, request its supplier-approved inert stall recipe rather than substitute a fake executable silently.
- [ ] Exercise both controller exit and job timeout paths as two finite parameter cases. Assert P2 TERM/grace/KILL precedes leader reap and lease release, actual Git cannot remain running, owned controller/guard are reaped by their actual parents, and an available subreaper/reaper observes orphan Git terminal status where required. Record actual zombie/reap limitations honestly; disappearance checks alone are not invented parent wait. Assert no successful job/whole-chain receipt and preserve all partial files. Verify reacquisition only after cleanup, with no signal to a recycled PID or outside group. Existing P3 cleanup tests cannot substitute for this P2 test.
- [ ] Publish the following **P4/P5 supplier requirement**, UNRUN until their separately adopted validator API and implementation exist: `test_owner_timing_boundary_vectors` belongs in the P4/P5 supplier test scope, never in the P2 body. The supplier must exercise exact row order/start/end refs, missing/crosswired return/emission/payload/ack/reap; >3 per call; >6 sum; >8 return; >10 ack; >10 reap; bool/negative time; false claimed whole-call sampler timing. Accept inclusive 3/6/8/10 boundaries, valid7.9 return/8.1 ack, and actual reap-before-ack when both follow return and meet10. No clock subtraction across host/boot. P2 implements only Task 3 sampler-stage transport arithmetic and this task’s actual backstop tests; it must not add a fake parallel validator, owner whole-call timing test implementation, or new P4/P5 body. After supplier adoption, invoke only the adopted API in the separately granted full-chain integration handoff.
- [ ] Once suppliers/root provide the prerequisites, run one finite real P3→P2→P4→P5 E2E matrix below. Source-qualified owner instrumentation must make each timing row an observation, never a hand-authored success proof. If prerequisites remain absent, publish those rows UNRUN with reason, no implied completion. Root then commissions independent exact-freeze P2 review and decides bounded adoption separately from APP/hardware acceptance.

| E2E row | Expected outcome and owner |
|---|---|
| Actual controller/worker→spawn→fork current producer | P2 transport passes; P4/P5 pass only with actual source-qualified payload/custody and strict trial/action proof. |
| Actual ordinary work anomaly false / Python debug true | Transport accepts; thread/config and work-END checks remain mandatory. |
| Missing/resealed crosswired owner claim/raw/source/emission | P2 rejects; P4 independently rejects if given the malformed retained bundle. |
| P0 END written then receipt/return absent or guard killed | P2 closure incomplete or whole-chain P4/P5 rejects; no fabricated return/ack. |
| Actual abrupt guard death with live Git | P2 backstop kills owned remaining Git, observes truthful cleanup and refuses qualification. |
| Valid source-owned return7.9, ack8.1, reap≤10 | P4/P5 eligible; never incorrectly enforce ack≤8. Synthetic vectors alone do not qualify this actual row. |
| Actual return late, ack late, reap late, wrong payload/pipe/PID | P4/P5 reject with actual observed facts retained, even with a successful P0 process END. |
| Five copied arrays omitted/reordered/replaced or inventory gap | P4 rejects transport mismatch; P2 rejects missing mandatory owner closure at production time. |

Complete-call acceptance uses exactly two strict child payload rows `{phase, process, emission, entry_ns, return_ns}` in START/END order. Parent extension is `{launch, child_identity, terminal_payload, acknowledgement_received_ns, reaped_ns, wait_status}`. Require owner.entry≤sampler.start≤sampler.end≤emission_end≤owner.return; both parent endpoints≥return and≤original deadline without inventing ack/reap order. Return-entry≤3s each, sum≤6s, starts/returns within launch..cutoff8; END entry follows START return and required strict actions. P4 validates arithmetic and correspondence, P5 validates source-owned observations and actual Process/pipe/wait/action semantics. This paragraph is their required acceptance contract, UNRUN until the adopted implementation exists; P2 does not implement these whole-call checks. Spawn retains90s join and empty sampler profile.

## Evidence, verification and stop condition

For each authorized RED/GREEN/adversarial attempt, record exact command, interpreter/dependencies, candidate/head/tree, input hashes, source lease, actual controller/import/thread/affinity/CPU/RAM custody, UTC/elapsed/exit, logs and complete output inventory. Freeze current test/runner bytes before review. Preserve every failed/unrun attempt and historical P2/P3 result; do not sum overlapping reruns. No package or CUDA pass is inferred.

Planned core command after grant, under root's execution wrapper and frozen thread/affinity/resource envelope: `python -B -m pytest -q /workspace/bac-review-2026-11-01/qualification/test_run_bac_hardware_v1.py` with explicitly selected new test nodes for RED and targeted GREEN. Use a unique external basetemp/output for each attempt, no source-cache writes, no Git mutation. P3-dependent runs additionally require the exact source lease; no execution occurred in this plan.

Stop after four tasks, one frozen handoff and one independent bounded review. Repair concrete findings only; no speculative design loop or wider body reads. Root adoption may state bounded tooling completion while enumerating unrun full-chain/hardware rows; it must not call the full owner chain qualified until all required actual rows pass. Evidence publication/index changes remain root-owned after selection, not part of this planning artifact.
