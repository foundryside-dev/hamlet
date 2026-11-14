# Independent P3 owner amendment design review v1

Verdict: CHANGES REQUESTED, limited to the three decisions below. The selected
single replacement protocol is otherwise suitable for bounded inert P3
implementation. This is a design review, not implementation or qualification.

Reviewed proposal SHA256:
16b5b16881c74276e30074976feae68124f4aacb7e525d12992d5a5cb21f0553.
Read AGENTS.md and actual current P0/P3/P3-test bodies (520+611+534=1665 lines,
three bodies). Verified their hashes respectively:
adc8efeba368998e2e875a60c54ed3338a5ad2aa7daa710b7609e9ed2119de3c;
938d44339e6c0fdc5b7763eb2b33031bf3794a66e97064cf3601e7b3dbf9b445;
5cb82462041e95dec1bd617cc05b4dd76988400611ee0ae3297038d95e8c11c7.
Consumed P0 interface v4, P2 interface v2, P4 interface v3 and owner supplier
capsules as metadata. No P2/P4 implementation, bootstrap or extra source body
was read. No imports, tests, Git command, branch/worktree/copy or source edit ran.
Only this review metadata was written.

## Required decisions before implementation

1. **Make actual call ownership independently observable.** The proposed API
   accepts case_id as caller data; the current P3 hooks retain configure, report
   and finish observations, but no active request/call association. Checking
   case membership plus PYTEST_CURRENT_TEST is not independent proof of the
   actual request. Add a process-identity-bound active call entry in the existing
   plugin body, populated from the actual pytest item at the call boundary and
   cleared on every exit. prepare_owner_launch must match that entry for pytest
   launchers. For a nested owner launcher require its authenticated start/launch
   case and phase, never a new environment-derived case. This needs no new
   schema field, environment marker, helper body or future report reference.
   A later actual call report still binds final acceptance. Retain a RED for a
   selected but wrong case with matching fabricated phase environment, and for
   a launch attempted outside the active call. The source-owned Process/start
   method correlation remains P5 evidence; the P3 API argument is not proof of
   the actual multiprocessing method.

2. **Fix preparation and launch-cut ordering explicitly.** Complete all imports,
   machinery preloading, immutable-plan parsing and parent source validation
   before sealing the fork launch's module snapshot. Release every recorder
   metadata/index lock and close its held descriptor before returning the handle
   and before actual fork. The final parent snapshot/launch emission must itself
   use already-prepared machinery; otherwise preparation after the snapshot can
   make a legitimate fork fail the mandated equality. Bind the in-memory handle
   to its issuing actual parent identity and launch reference; inherited parent
   registry state cannot count as the child's successful start. Start/end remain
   exclusive and actual-child-owned, and one launch must not qualify multiple
   distinct child identities. Full P2/P4/P5 inventory reconciliation must reject
   reuse even when separate children inherited the same handle. Retain a test
   for preparation-induced module growth and duplicate-child launch reuse.

3. **Specify bounded sampler custody under the owner's shorter deadline.** The
   core supplier gives its fork parent a 10-second pipe/wait deadline and bounded
   TERM/KILL of the guard PID. Saying Git remains in the P2-owned process group
   does not by itself bound a blocking flock, drain a full stderr pipe, reap an
   owned Git subprocess, or ensure Git exits when that guard is killed. Require
   nonblocking lock acquisition with a monotonic deadline, concurrent bounded
   stdout/stderr draining, and bounded actual Git wait/termination/reaping.
   Seal a sampler bound within the existing guard deadline with cleanup margin;
   account its process/CPU and output costs in the role bound before execution.
   No independent session/process group may escape P2 custody. P2 final group
   cleanup remains the backstop for abrupt guard death, and cannot be replaced
   by a fabricated child end. Test held lock, stalled/output-heavy Git and
   interrupted guard cases without application imports or Git writes. If the
   exact supplied runtime cannot meet the bound, retain failed/incomplete proof;
   do not relax the owner's deadline or substitute inherited source facts.

These are finite refinements of the proposed APIs/kernel/tests, not an additional
planning phase or permission to read/edit other source bodies.

## Accepted design decisions and limits

- **P0 fit:** the actual P0 permits a measured nonfork process.debug Python fact
  and requires fork intra_op/inter_op/debug unavailable. Raw v2 can retain actual
  __debug__/optimization and separately typed anomaly observations without P0
  mutation. All nonfork profiles must use their actual Python value, including
  uninitialized controllers whose old synthetic profile used debug=False.
  Anomaly=False is valid with Python debug=True. No setter is authorized.
- **Authority and acyclicity:** the selected obligation's parsed case-contract,
  exact parent raw context, fresh parent witness and actual live ancestry form
  the right authority chain. Empty policy/runtime never grants standalone
  authority in the replacement strict path. Launch then child then terminal
  payload then actual reports avoids a future-reference cycle. Root's exact
  invocation and no-writer interval remain external authority.
- **Environment:** full parent-start map plus the exact call key for pytest,
  followed by exact full-map inheritance for nested owners, preserves worker
  provenance without relabeling children as workers. Reject base phase/xdist
  keys and arbitrary additions. Startup COLUMNS/LINES/locale/version must be
  observed and sealed once, not silently normalized.
- **Fork observation:** retaining own read-only HEAD/index commands, own
  PID/PPID/start/host/boot, actual source/import hashes and actual intervals is
  the correct choice. Parent preparation is a validated immutable declaration
  cache, never a replacement child source witness. Rehash every reference used
  by that cache and reject namespace changes. A fresh regular no-follow lock
  descriptor avoids the inherited open-description lock trap. Primitive-only
  emission and import traps must cover both start and end; module-name equality
  alone cannot prove no imports. The before/after name hashes must bracket the
  whole recorder operation, including final file/reference work.
- **Source owner semantics:** retain the three 4/7/5-action guard trials, exact
  error/counter assertions, pipe/wait correlation and os._exit/no-unwind path.
  Parent launch preparation belongs inside the source's existing RNG capture
  interval. Successful parent terminal emission follows all actual cleanup,
  RNG/currentness assertions; later passing setup/call/teardown reports remain
  required. Identity success is never owner success.
- **Runtime blocker classification:** the supplied inter-op=5 origin is missing.
  It blocks source-owner qualification until source-owned prework setup and
  actual per-child measurements are established. It does not block independent
  inert P3 RED/GREEN development with explicit synthetic runtime sentinels. The
  recorder cannot establish the profile by setting threads. Work END still
  requires measured mandatory thread values; guards never query them.
- **Consumer separation:** P2 adopted v2 and P4 repaired v3 do not implement this
  amendment. Their separately bounded amendments must independently parse raw
  v2/owner launches, rederive full context/environment, reconcile cardinality,
  times, source/process identity and terminal inventory. P3-only closed
  completion tests are synthetic integration tests, not complete P2/P4/P5 or
  source/hardware qualification. Update the proposal's P4 baseline reference
  from v1 to current repaired v3 metadata; do not claim v3 is already adopted.
- **Budget and execution inputs:** retain the proposed ceiling
  1100+1200+1578=3878 lines across five bodies, with edits only to identity/tests.
  No extra helper, compatibility adapter or source producer edit is needed.
  Root-supplied existing read-only Git identity and pinned interpreter/environment
  must precede the actual direct-Git probe; no git-init or source copy is allowed.
  Preserve exact-source RED, focused GREEN and bounded whole-suite evidence.
  A budget overrun is a concrete reslice request, not license to weaken a gate.

After the three refinements are incorporated, proceed with the bounded synthetic
implementation. Actual owner integration, P2/P4 amendments and hardware execution
remain distinct required gates; this review waives none of them.
