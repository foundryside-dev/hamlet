# Current P1 Consumer Repair Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans task-by-task after root grants implementation. No delegation, Git, branches, worktrees, source copies or runtime is authorized by this plan. Steps use checkboxes for subsequent execution.

**Goal:** Make P2 accept only the adopted native-Git P1 capture with complete source, terminal and namespace custody.

**Architecture:** Keep P0 and P1 wire formats unchanged. Add an explicit externally pinned root capture-custody input to P2, validate the current native command records and five source siblings, and use the same exact Git dependency for P2 source queries. P4 consumes the retained custody reference and sibling references after a coordinated runner freeze.

**Tech stack:** Existing Python runner, stdlib JSON/reference validation, existing pytest tooling tests.

**Spec:** `E/hardware-runner-p2/owner-integration/p1-native-git-consumer-gaps-v1.json` (dcc5441374e936c996b6859c099398d20f9277677f27acc868e5e7306f559804), adopted P1 root-v2 record (9b3489237f82591804daad0f3c305a01b705542013ca986e6721b69e9ad4f39f), output-interface-v2 (0554e5f0422ff7ce1488dae4c404a25fb8966def7ffd61cd57ac457da91dd3c0), producer custody capsule-v2 (b79532047f10410aeb7c5c2fe6a6f60ae473d84239d225cd59061e2561b94c96). E and Q retain their existing absolute locations. Every requirement in the gap capsule remains normative; the tasks below assign all five gaps.

## Global constraints

Current runner is 1603 lines, SHA 0d2a163305efb4683b8d90f42364d894a1af962129b9df15137ccd466374cc97. P4 is reviewing those bytes: no change until root releases the shared dependency. Current four bodies total4431 lines; per-scope limit remains five whole bodies/5000 lines, not selected excerpts. P0 remains read-only e4f31eacb0e4499655a19ec91a4f5618a7b2ad3f4090e7ed068816b311e00860. Current capture authority is d91d9a4eac393d1283de0fa2a894a6f7a837aa9e28aa854c4795462f5229a1bb,64451 bytes. No compatibility dispatch for obsolete Git records, default executable, fabricated measurement, dropped failure or relaxed ancestry gate.

Local real capture is blocked by namespace/full cgroup ancestry; neither this repair nor pure fixture success resolves it. Actual Task4 and P4/P5/APP/CUDA integration remain UNRUN until an adequate server and separately granted source/resource/input leases exist. The anticipated 16-worker CUDA server is not yet accessible. Preserve every existing freeze and failed/unrun attempt.

## Review focus

1. Self-authored custody files cannot authenticate themselves: root must supply the exact trusted reference independently (Task1).
2. bool/int/float coercion, duplicate JSON keys and nonfinite numbers must not evade closed joins (Tasks1–3).
3. Capture parent identity differs from discovery identity; timestamps describe observations, not whole-call return/ack/reap (Task2).
4. A changed executable or sibling after admission must refuse at the next boundary (Tasks2–3).
5. Optional NVIDIA topology failures retain the existing contract; mandatory Git cannot hide among driver rows (Task2).

## Required root authority: concrete proposed interface

Choose a root-sealed manifest, rather than letting P2's first read invent authenticity. This is the sole new authority input; approval of this design is required before implementation. Root creates it only after observing genuine P1 terminal publication in a previously unused, exclusively owned capture directory D, with no unrelated writers from directory creation through publication, sealing, consumer execution and final P4 recheck. P1 is the only authorized producer until it terminates; after terminal publication there are no producer writes. Root records producer identity, exit/wait evidence and the enforced namespace ownership mechanism. If this continuity is unavailable, refuse; a later hash snapshot cannot repair it.

Proposed closed metadata schema `bac-root-p1-capture-custody-v1`, fields exactly:
`schema, authority, capture_directory, candidate, request, tools, dependencies, git, spec, admission, terminal, siblings, capture_identity, publication, namespace, sealed_at`.
- `authority` exact string `root`; it is a label, not authentication. Root supplies the manifest's exact P0 `{path,sha256,bytes}` ref through the independently approved execution input/lease. P2 validates that ref before reading; P4 receives the same externally pinned ref. Root approval and custody are outside what JSON alone can prove.
- canonical absolute `capture_directory`; all ten existing capture filenames must be direct children, regular files with no symlink ancestors, and match the producer reference graph. `candidate,request,dependencies,spec,admission,terminal,git` are exact P0 refs; `tools` is the exact named-ref list. Capture tool must equal the adopted capture bytes above; manifest Git must equal the sole environment dependency named git.
- `siblings` exactly an ordered list of five P0 refs: start.json, source-before.json, source-after.json, source-before-git.json, source-after-git.json. No guessed/optional paths or extra entries.
- `capture_identity` uses the existing closed P0 process-identity shape and equals discovery-command.capture_identity. `publication` is an exact P0 ref to root's retained actual producer wait/terminal evidence; it must bind capture identity, terminal ref and observed successful exit. Do not invent a successful wait record when absent.
- `namespace` closed fields `start,end,mechanism,evidence`; UTC interval covers capture creation/publication/seal and the entire authorized consumer/P4 window; `mechanism` nonblank truthful string, `evidence` exact ref to root's existing namespace/source lease record. Root independently verifies actual protection and interval. Consumer requires its current time and all capture times inside the interval; expiry or missing authority refuses. Root releases/reuses namespace only after consumer/P4 completion and cleanup.
- `sealed_at` exact UTC after publication and sibling observations, within namespace interval. Root hashes all references while exclusive custody remains held. A root-authored fixture manifest in a pure test is explicitly synthetic, never actual authority.

No new P0 record kind or P1 result field is introduced. Publication/namespace evidence remain root authority artifacts; before implementation root/P4 must freeze their actual existing record schemas and the exact selectors for identity, terminal, exit and interval, or approve a finite closed root schema. This is an authority decision, not a reason to iterate on native command parsing. P2 must never silently accept opaque evidence it claims to have semantically validated.

Public signature becomes `run(spec_path: Path, *, capture_custody_ref: dict) -> int`; `Custody(path, *, capture_custody_ref: dict)` likewise requires the explicit ref. CLI becomes exactly `runner SPEC CUSTODY_PATH CUSTODY_SHA256 CUSTODY_BYTES`, strict decimal byte count, no old one-argument fallback. Update every owned caller and hand P4 the exact signature metadata before source publication. Retain the manifest and all five siblings in the existing attempt seal inventory; `source()` rehashes them with existing terminal/spec/admission/discovery inputs. P4 revalidates the same graph, rather than trusting a receipt claim.

## Scope and body budget

Prefer a single source/test task scope only if a pre-edit whole-body projection proves total <=5000. Available growth569 lines is unlikely to cover this entire change rigorously; do not compress validation or omit adversarial tests to fit.

Recommended separately granted scopes, with no new production module or execution copy:
- **Test-only scope:** Q/test_run_bac_hardware_v1.py (current2202, target<=3100), read-only P0 (526) and existing run-inert-v1.py (100), total<=3726. Consume runner API/behavior through this sealed plan and an exact source-pin/interface capsule; do not open runner body in that scope. Author tests, freeze, then run only under granted pure resources; importing the actual runner in tests is not copying it. All existing callers receive required fixture custody input. Preserve actual Task4 lease gate and UNRUN status.
- **Source-only scope:** Q/run_bac_hardware_v1.py (current1603,target<=2300), read-only P0 (526), wrapper (100), total<=2926. Consume test case/fixture interfaces, RED logs and exact hashes as metadata without opening test body. No P1/P3/P4 body reads. Keep wrapper unchanged unless an independently justified invocation adjustment is required.
- If the current agent has already accumulated all four bodies, these are not permission to reset its count. Root must assign genuinely separate bounded review/author contexts or explicitly revise scope before body growth crosses5000. No delegation is authorized here. Cross-scope metadata defines test node IDs, fixture output/ref shape, signatures, exact source hashes and expected failures; never hand over source copies.

## Task1: Root input and terminal closed types (gaps4,5 and custody portion2)

**Files:** runner; tests in their respective scopes. **Interfaces:** required public signatures above; custody stores `capture_custody_ref`, `capture_sibling_refs`, selected `git_ref`. Existing P0 functions remain the only reference/identity authority.

- [ ] Author named fixture `current_p1_capture_bundle` returning spec path and exact synthetic custody ref, plus test `test_current_p1_terminal_and_root_custody` with missing/forged/crosswired/expired manifest, wrong capture adoption, refused/partial terminal, float/bool nested byte-count and changed terminal cases. Assert refusal before jobs/source execution; valid closed fixture reaches native-command validation.
- [ ] Retain test-only freeze and intended RED against unchanged0d2a runner; distinguish signature RED from direct terminal type RED so one cannot mask the other.
- [ ] Implement explicit required input, current capture authority, strict terminal nested P0 refs, admission/terminal equalities, canonical capture paths and retention. Exact Python primitive types: bool is not int, float is not int; strings/lists/dicts/null only where specified. Reject duplicate JSON object keys and NaN/Infinity for all newly validated capture JSON; do not use permissive reserialization as a substitute for shape/type validation.
- [ ] Run finite GREEN selection, retain logs and pin before/after; freeze source interface for Task2.

## Task2: Native discovery and source-sibling graph (gaps1,2)

**Interfaces:** add internal `Custody.capture_sources()` to validate the root-bound start/source/native sibling graph; native helper `_native_git_command(row, *, git_ref, argv, cwd, parent_identity, lower, upper)` validates one closed successful command and returns no acceptance receipt. Native input fields are exactly the adopted interface's13 keys; driver records retain their existing9-key format.

- [ ] Author `test_current_p1_native_discovery` and `test_current_p1_source_siblings` parameter matrices: validCPU/CUDA; missing/duplicate/unknown/native-as-driver rows; wrong executable_after/version/argv/env/cwd/PID/PPID/host/boot/time; bool exit/truncation-like extras; partial/errors; nested parsed-stdout/raw coercions; crosswired/reordered/missing/mutated siblings; wrong registry/inventory/availability; clock rollback. Include valid optional NVIDIA topology failure according to existing driver contract.
- [ ] Retain direct native-record and source-sibling RED, independently of Task1 authority failure.
- [ ] Implement exactly one nativeGit version row on CPU and CUDA; CPU otherwise retains empty devices/noTorch/noNVIDIA. CUDA separates driver records without converting schemas. Require successful native int0/errors[], before/after exact executable refs, full stdout version with only one terminal LF removed; no strip/split. Preserve permitted stderr. Parsed discovery stdout and raw dependency inventories must compare recursively exact types.
- [ ] Validate version child PPID against raw discovery PID; source children against wrapper.capture_identity.pid. Same host/boot and nonempty birth tokens; child cannot equal its still-live parent. Do not prohibit sequential PID reuse or demand post-reap /proc availability. Identity authority is actual P1 observations protected by root custody, not reconstruction from candidate paths. Keep existing discovery wrapper process, argv/env, leaseFD and provenance checks.
- [ ] Validate start exact `{at,candidate,request,tools,dependencies}`. Source exact `{at,head,tree,inventory,registry,availability}`. Ordered inventory flattens source/tests/configs/scripts/ratchet/artifacts; registry is literal porcelain string; availability ordered exact `{path,directory_exists}` with bool. Never reinterpret these values as refs. Each source list has exactly3 ordered commands with adopted prefix/env: HEAD; staged diff-index against candidate.tree; worktree porcelain. Join HEAD output, staged exit0, registry stdout/candidate bytes and availability observations. Source tree is not inferred from HEAD tree.
- [ ] Enforce nonregressing UTC chain: start <= ordered before commands <= before.at <= wrapper.start <= raw.at <= discovery native command intervals <= wrapper.end <= ordered after commands <= after.at <= admission.at. Producer source.at is post-query observation; no invented source identity/start/end or return timestamp. Reject rollback, don't rewrite it. Run finite GREEN matrix and freeze.

## Task3: Same Git source authority and integrated freeze (gap3 plus all joins)

**Interface:** `_git(root, args, *, git_ref)` requires the selected exact P0 executable ref; caller supplies query tail. Pre/post rehash executable around each query. Full argv prefix: `[git.path,'--no-optional-locks','-c','core.fsmonitor=false','-c','core.pager=cat','-C',authorized_root]`; cwd authorized_root; exact env PATH=/usr/bin:/bin, LC_ALL=C, GIT_CONFIG_NOSYSTEM=1, GIT_CONFIG_GLOBAL=/dev/null.

- [ ] Author `test_current_p1_source_git_binding` asserting exact argv/env/ref and pre/post mutation refusal with inert subprocess instrumentation; no real Git. Preserve HEAD, staged diff, additional unstaged diff and registry guards. Add `test_current_p1_custody_retained` asserting final inventory and boundary rehash closure.
- [ ] Retain RED before replacing hardcoded executable/call sites. Implement required signature throughout owned source with no fallback. Require the same Git ref in root manifest, environment, P1 version/source records and existing P3 sampler binding. Preserve P3's independently adopted argv/env and two-query wire; never rewrite it to P1's profile.
- [ ] Run GREEN plus all original safe pure P2 tests on final bytes under approved wrapper/unique attempts. Bulk2CPU/4GiB; exact known public admission cases needing3CPU separately scheduled, never capacity bypass. Record actual argv/PID/UTC/affinity/threads/RLIMIT, source hashes, raw outcomes and per-test requirements. Retain failures; no overlapping counts added as unique tests.
- [ ] Independently review admission, source joins, namespace authentication boundary, retained graph and all Task3 owner transport invariants. Root then freezes final runner/test/API refs and grants P4 pin/caller update; P4 requalification uses those exact bytes. No concurrent mutation during P4 verification.

## Completion and decision

Routine implementation choices: helper placement, parameterization and reuse of existing typed validators within these fixed contracts. No user clarification is needed for them.

Root decisions before implementation: accept the explicit root-manifest authority/API above and provide the concrete namespace/publication evidence schemas; allocate separate body-bounded contexts if projection exceeds5000; release the shared runner only after current P4 verification. These decisions do not authorize runtime by themselves. Local pure testing then needs its own scheduled resources. Actual server capture/backstop/full-chain/CUDA requires authentic access, supported ancestry, real measured admission and exclusive source leases later.

Coverage check: all five sourcefacts gaps map to Tasks1–3; strict primitives, sameGit authority, terminal gate, five siblings, root custody, source identity and retained P4 graph are explicit. Historical Task4 preparation and actual UNRUN remain intact. This document records design only; no test collection or execution is claimed.
