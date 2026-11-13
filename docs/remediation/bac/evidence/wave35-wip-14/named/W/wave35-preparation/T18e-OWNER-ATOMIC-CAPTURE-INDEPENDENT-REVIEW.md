# Independent atomic owner capture SPEC and QUALITY review

2026-11-13. Independent bounded review and execution of R67, candidate tree
`04af55dcf99559c949b16af6fa92effd30b54f6f`. SPEC: **PASS**.
QUALITY: **PASS**. Independent frozen full16 execution passed; exact evidence is
appended below. No blocking findings. Root confirms aggregate custody verification;
publication remains root-owned and no BANK/programme acceptance is implied.

Read AGENTS.md, the atomic-capture brief/report, producer supplier facts, the
atomic-capture appendix and the supplied production diff. Exactly four whole
application/test source bodies were admitted; no additional source/helper body,
source copy, source edit, Git/index/branch/worktree operation, import, compiler,
pytest or other application execution was performed in this initial review.
The only authored file is this review. Root retains publication ownership.

## Independently observed source seals

| Body | Lines | SHA256 |
| --- | ---: | --- |
| `src/townlet/exploration/world_curiosity_state.py` | 1361 | `433b3563457fbf68d26d47d73dc375c1382e0cc77d0987a4c9d4f62f3cdfcce3` |
| `src/townlet/exploration/rng_custody.py` | 371 | `9d6cd6fcfe62d8e53bda1e6ce7b34a89454ccc88373b5ec4cd072fe004ad66fb` |
| `tests/test_townlet/regressions/bac/test_world_rng_bootstrap.py` | 998 | `452e427b945475e050b35273b6bb44effe3ade6ef96629c4382c2d68591ee727` |
| `tests/test_townlet/regressions/bac/test_world_rng_capture.py` | 598 | `ad6f50b0991efc30eb0e960dc5f5c78560ed849e4046240f029139e716fcc180` |

Total3328. `sha256sum` and `wc -l` directly observed these bytes. Independently
hashed `.superpowers/sdd/2026-11-01-bac-remediation-upgrades/wave35/r67-candidate.json`
at SHA256 `f256db6b0a8759ef5a15501fe1a637f4f8d62c09dc224e999ec47eb4aa29f102` after
root clarified its absolute location.

## Contract and implementation

The production diff is one additive28-line method at world-state1032. Its single
`_scope("snapshot", lineage)` reuses domain-before-owner admission, exact active
lineage authentication, frame quiescence and same-owner exclusion. Explicit
parent lineage cannot make nested lifecycle admissible inside the active private
frame. Another thread waits at the actual process RLock. These guards remain
held through native serialization, auxiliary capture, both ownership traversals,
activation restoration/completion, RNG snapshot and result construction.

One `checkpoint_state()` invocation and one `capture(self._backend)` invocation
execute in the same service activation against the same retained backend. There
is no reconstructed provider or second serializer. Native and auxiliary `_owned`
copies occur inside activation; tensors are detached/cloned, including Parameters
returned through supported value containers. Private `_snapshot()` occurs after
activation exits, including its nested domain completion. The outer scope still
performs its existing completion before the caller actually receives a result.

The existing envelope schema/healthy/backend/rng fields and old snapshot method
are unchanged. The auxiliary value is separate. Native/callback/copy/activation
failure sets `_failed`, rethrows and advances owner revision once; uncertain
restoration or completion propagates existing common-domain poison. Outer-scope
completion failures are caught by `_scope` and quarantine the owner. Malformed
noncallables reject before activation/native work and do not quarantine a healthy
owner. They still undergo actual admission, with its existing domain currency
semantics. The new capture invalidates previous prepared destination state.

As with existing snapshot, a previously quarantined owner can yield diagnostic
data with `healthy=False`; this does not clear quarantine or enable `call`.
The read-only callback/value-data requirement is a cooperative contract, not a
sandbox for arbitrary callback code or arbitrary custom deepcopy hooks. Retaining
raw live aliases through side effects remains prohibited caller behavior. This
does not weaken the approved producer contract.

## Test quality assessment

The causal RND test uses the actual compiled-provider supplier and real Torch
Parameters. It checks identical backend/Parameter identities, optimizer pairing,
mixed gradients and detached returned Parameters/borrowed gradients. A serializer
counter and deliberate second-call gradient mutation make a two-serialization
implementation observable even if its native bytes remain equal. Mutating both
returned native and auxiliary data is checked against the live provider.

The RNG ordering test consumes Python, NumPy legacy and Torch draws in native
serialization, native-copy traversal, capture and auxiliary-copy traversal. Local
independent generators predict saved continuation and next managed draws. It
also requires actual activation completion before the quiescent RNG snapshot and
checks other components and ambient continuation. This is substantive ordering
and continuation evidence rather than count-only coverage.

The reentry test probes owner and peer lifecycle both with absent and authentic
lineage, plus public private-RNG snapshot, during native and gradient phases.
The coordinated thread witness delegates to the original actual RLock and checks
nonblocking acquisition at native, gradient and restoration cuts; blocked
callbacks then run after custody release. Timeouts bound hangs, while actual
lock acquisition results supply the exclusion assertion.

Three live failure stages check error propagation, owner quarantine, healthy peer
operation and ambient preservation. Four malformed values check rejection before
native/RNG work. Old transport equivalence, genuine/expired/fabricated lineage
and prepared-handle invalidation cover the additive API boundaries. Three fresh
spawned child cases inject failures after real setters or completion, retain a
distinct callback failure during cleanup, and check actual enrolled entrypoints
fail closed. Child qualification/PID receipts use the admitted existing supplier.

Coverage is intentionally CPU (empty CUDA inventory); injected completion is a
real completion seam with a post-operation exception, not physical GPU evidence.
No claim is made about GPU execution, every curiosity family, BANK adoption,
paused CP changes, full-parent restoration or exact simulator continuation.

## Independent execution selection and pending evidence

Select exactly the complete frozen
`tests/test_townlet/regressions/bac/test_world_rng_capture.py` module (16 cases).
This finite selection covers every new atomic producer obligation above,
including the three isolated poison children. Root has been asked to allocate
the frozen independent harness before this reviewer executes it. No extra test
source or helper will be introduced, and no runtime has yet been run here.

The R66 causal missing-method RED and R67 causal GREEN1 are root-supplied results;
the root also reports full new16 and existing56 controls underway. These are
not substituted for independent other-model fixed-source execution. Final
execution disposition requires exact command, immutable attempt artifacts,
candidate/source/process custody verification, result and preserved failures.

## Independent fixed-source execution result

After the source review, root explicitly authorized this finite invocation once:

```text
cd /workspace/hamlet
python /workspace/bac-review-2026-11-01/qualification/run_bac_packet_checks_locked.py /workspace/bac-review-2026-11-01/qualification/wave35-r67-independent-atomic-spec.json
```

The locked harness performed its authorized internal index identity reads; this
reviewer performed no direct Git/index mutation. One job/one pytest process ran
the selected module with three isolated poison children. Actual command:

```text
/workspace/hamlet/.venv/bin/python -m pytest tests/test_townlet/regressions/bac/test_world_rng_capture.py --no-cov -p no:cacheprovider -p no:benchmark -p bac_source_identity -q
```

Result **16 PASS**, exit0, no skips/warnings reported, pytest23.37s and harness
27.910327196121216s. No retry or failed independent attempt occurred. Artifacts
are under `/workspace/bac-review-2026-11-01/qualification/wave35-r67-independent-atomic/`:
`independent-atomic-result.json`, `independent-atomic.log` and the
`independent-atomic/` identity/observation directory. Directly read the exact log
and result. Independently hashed log SHA256
`1afd2d0cc9addca7f2b01381b10aa3ab3228e3c15dd9013a0d013f8527219155`, matching result.
Result records the exact candidate/manifest above and harness SHA256
`180558c22da088a57326aa9251fbb64761e2788f18cb982532525b84b571f791`.

Read controller identity and all three child identity/observation pairs. Setter
PID18872, cleanup18898 and completion18924 each match identity/process/queued
PID, exit0, qualified=true, exact manifest, expected fail-closed message, exact
candidate/base and `/workspace/hamlet/src/townlet/` import paths. Child debug=true,
threads1 and interop_threads5. Controller records the exact candidate/base,
workspace module and threads1. These direct artifact observations do not replace
root's separately owned complete source/config/artifact/index/registry verifier.

Root reports its separate new16 PASS32.315819s and existing56 PASS45.185444s,
with814-source custody and all six actual spawn identities verified. Those
root-supplied controls are not counted as this reviewer's execution. The finite
independent result now satisfies the requested other-model fixed-source run;
root was notified to complete final custody verification and publication.

Root subsequently confirms independent16 PASS27.910327s with verified
814-source/573-config/13-artifact/controller/import/index/14-MAIN1 custody and
all three actual spawned children. The unchanged strong child verifier plus
explicit role whitelist has version SHA256
`dd9101db18203a0399587a0b3ccabfac8f26672d5a7bb58426d85acb45196ee0`.
This verification is attributed to root; the execution and artifact inspection
above were performed by this independent reviewer. Final bounded SPEC and
QUALITY verdicts are PASS. Additional existing owner/binding/domain controls
remain root-owned and are not inferred passed from collection or startup.

## Draft source-truth paragraph and public capsule

For root's later documentation publication, without editing frozen tracked docs:

`OwnedWorldBackend.snapshot_with_capture(capture, *, lineage)` returns
`(snapshot_envelope, owned_auxiliary_value)`. The read-only callback receives the
same actual backend whose native `checkpoint_state()` is invoked exactly once;
it may capture gradients from that backend's real Parameters. One managed owner
scope and private service activation cover serialization, capture and ownership
copies. Activation restoration and completion precede the internal quiescent RNG
snapshot. The unchanged envelope contains `schema="owned-world-backend-v1"`,
`healthy`, `backend` and `rng`; auxiliary data remains separate. Returned supported
value data is detached and owned. Forward the exact current authenticated parent
lineage; retain BANK's outer process-domain operation and lock. The callback must
not invoke lifecycle work, load/configure native state, snapshot private RNG or
retain live aliases. Failure preserves established quarantine/common-domain
poison behavior; there is no weaker retry/fallback capture path. Existing `call`
and `snapshot` remain available with their existing semantics. This additive
producer seam is qualified on CPU by independent16 and root controls; GPU
execution, BANK consumption/integration, full-parent restoration and deferred
exact simulator continuation are not established by this packet.
