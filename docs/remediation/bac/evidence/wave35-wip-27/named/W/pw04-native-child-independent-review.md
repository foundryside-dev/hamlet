# PW04 independent native flat replay and outer RNG source review

2026-11-14. Reviewer: independently assigned adversarial reviewer
`/root/pw04_native_children_astra`; did not author the implementation. Candidate
reported by root: R162 `6cac386ec762206cf88eb4ceee836a5ed7ba14fc`.
Disposition: **one P2 source defect in outer RNG input ownership/purity; no P1
identified and no additional concrete P2 identified in native flat replay.**
This is bounded component source review, not package closure or terminal evidence
qualification. Root reports 35 passed (flat9/RNG18/C8), with custody verification
pending at assignment; this reviewer did not execute or independently qualify them.

## Exact review inventory

Exactly five complete implementation/test bodies, 2,310 lines. No other source
or imported fixture body opened. No application import, runtime, test execution,
Git, branch/worktree, source copy/edit or delegation performed. AGENTS.md and
EVIDENCE-PROCESS.md were read. The only write is this review document.

| Path | Lines | SHA256 |
| --- | ---: | --- |
| src/townlet/training/replay_contract.py | 949 | de14dd2005934bee6f564f0aaca532bfefcd962d62a76a3a93efdb60274196c8 |
| src/townlet/training/replay_buffer.py | 860 | c1b41059d34c6712c0d19c4247a92cc4180d545fa33b622603fcb913a1ee34d2 |
| src/townlet/training/native_rng.py | 212 | ae3001eb8befdfa29e3e35812eea489e74437821d2f2396bac96f8057743805c |
| tests/test_townlet/regressions/bac/test_native_replay_data.py | 152 | 77748cfad75da2f6e2934c2cc162ea3df2ce9c4d429843afe6d968683747d53b |
| tests/test_townlet/regressions/bac/test_native_rng_state.py | 137 | 84dbe006bf370ce657db578dac58eebe561181dd6f99410029e384c41c473620 |

Supplier prose: pw04-native-replay-flat.md, pw04-native-rng.md,
pw04-native-pop-data-api.md, pw04-replay-native-api.md,
pw04-native-integration-assessment.md, pw04-restore-attempt-c-api.md.
Their historical proposals and line inventories are not substituted for the five
actual bodies above. Core/B/C/POP implementation claims below remain attributed
source facts, not additional independently opened source.

## P2: exact Tensor inputs can defeat owned RNG staging and pure validation

Location: `native_rng.py:29-39` and `:142-154`.

`_validate_state_tensor` accepts exact `torch.Tensor` objects but does not reject
instance attributes. It dynamically invokes `numel` and `is_contiguous`.
`_owned_payload` then dynamically invokes each incoming tensor's `clone` and
assumes its result is independent. Exact Tensor type does not exclude per-instance
method overrides. The inspected replay contract explicitly recognizes this same
fact in `_archive_clone_stable` and checks the instance dictionary before treating
the tensor as ordinary.

Concrete source-derived reproducer for the ownership branch (NOT executed here):
obtain a valid CPU RNG tensor `state = torch.get_rng_state().clone()`; assign
`state.clone = lambda: state`; put it in the otherwise exact valid payload. The
structural checks accept it, `_owned_payload` retains `state` itself, and detached
Generator.set_state accepts the valid bytes. `validate_payload` therefore returns
aliased bytes, and genuine `prepare` stores that same caller-owned tensor. A caller
can subsequently copy another valid RNG state's bytes into `state`, changing the
future restored stream after preflight; malformed bytes can instead defer refusal
to a setter after native world publication. Authentic POP/C authority does not
repair this data ownership failure.

The same missing closed-input check lets an instance `is_contiguous` override
perform a Torch draw and return True during the purportedly pure
`validate_native_rng_payload` call, outside domain admission. This is the same
root defect rather than a second counted finding. Exact key/scalar/container and
subclass refusal alone do not close it.

Narrow repair: reject nonordinary Tensor instance state before any overridable
instance call, or use source-controlled base operations with an equally explicit
closed-input contract throughout validation/cloning. Cover both CPU and each CUDA
state tensor. Add controls proving an exact Tensor with overridden clone cannot
alias validation/staging and an overridden metadata method cannot run in the pure
validator; preserve genuine ordinary owned-state success and unchanged ambient
bytes. Root must execute these controls on a new frozen candidate. No general
architecture change is required.

## Source disposition of the remaining child mechanics

Flat stage authenticates the actual POP plan before device work and again inside
real prepare custody; it uses the existing complete validation/materialization
and archive merge. The issued native record has no currentness token. Registry
payload is private, handles refuse construction/reduction, the parent plan is a
weak reference, and PID/current Thread, receiving revision and capacity/device are
checked. No record-to-handle strong cycle is present. All staged payloads join the
admitted device inventory, including candidate fields and archive original_state.
Install independently reauthenticates POP and C before and inside genuine device
custody, consumes before publication, assigns storage/counters/archives to the
same owner, and advances revision. Publication exception quarantines replay;
actual completion failure also quarantines via `_device_operation`. Ordinary
PreparedReplay retains its current-token and receiver-revision validation; no
native fallback was added to ordinary install.

RNG validates exact inventory, owns ordinary input by cloning subject to the P2,
and uses detached CPU/declared CUDA generators for semantic compatibility under
real custody. Structural validation intentionally does not validate byte semantics.
Prepared records bind exact POP/plan, helper revision, PID/current Thread and
one-use status. Install rechecks actual POP/C at each cut, consumes under the real
install invocation, sets CPU then declared CUDA generators, marks ambient commit,
and poisons the real domain on setter/publication exception. It does not roll back.

Root supplied actual core facts: invocation completion calls `_complete`; completion
exceptions poison the domain; body/completion exceptions are retained; exit records
completion and raises. `_commit_ambient` marks revision without a draw. Core finish
synchronizes devices and updates metadata only, and C's suffix after the callback
has no RNG draw. Therefore no separate missing completion-poison defect is inferred
from the absence of a local outer RNG catch around context exit.

RNG records strongly retain parent and plan, but do not currently retain their weak
key. Root source-confirmed current POP plan records contain no child handles; no
present retention cycle is asserted. Future POP ownership of prepared RNG handles
must avoid forming plan -> handle -> registry value -> plan retention. Replay's
weak plan reference already avoids that direction.

## Remaining bounded evidence gaps

- Actual C finalizer success with nonempty flat replay, then exact resumed sample,
  action and real learner update; current tests exercise staging/refusal only.
- Genuine success/consumption and foreign/stale/PID/thread controls for RNG;
  flat tests cover foreign owner, revision and Thread but not every finalizer cut.
- Incoming tensor/archive ownership and retained staged device inventory through
  actual publication, plus receiver/participant identity and ordinary stale-token
  refusal after intervening BANK work.
- Actual setter, publication and device completion fault cuts proving domain poison,
  replay quarantine and parent terminal fencing without successful receipt/retry.
- Explicit supported CUDA inventory and actual hardware completion evidence. CPU
  controls do not qualify CUDA or an incomplete externally supplied device profile.
- Root's original fresh DemoRunner artifact/restore/next-learning acceptance and
  broader owner regressions remain owed; neither this review nor the reported 35
  component passes closes them.

These are existing obligations and unobserved cuts, not additional asserted source
bugs or a new test-count programme. Final independent acceptance must bind repaired
source hashes and actual execution custody; this R162 review remains historical.

## Independent fixed-source P2 follow-up

2026-11-14, requested through the RNG implementation owner on root's instruction.
Re-read the two existing complete RNG bodies only; cumulative inventory remains
five bodies, now 2,344 lines (native_rng219, native RNG tests164; other three as
above). Source SHA256 is
`cc0959e6deed8a5b57947ff456fcd838ee3762fc2a530c30dcf3cc197f073088`;
test SHA256 is
`feab54a5a88ccc68de4602179930c768bc1a6077b01573b9a24d71bdb79d231f`.
Both hashes were independently read from the working files. No application runtime,
tests, imports or source edits were performed by this reviewer.

**Fixed-source disposition: the reported P2 is addressed by the inspected change.**
The validator now rejects a nonempty exact Tensor instance dictionary through
`object.__getattribute__` before invoking any Tensor metadata method. Consequently
the original clone/contiguity overrides cannot execute or survive to the ownership
cut. Cloning and contiguity additionally use unbound Tensor operations. The common
validator applies the same rule to the CPU state and every declared CUDA state;
prepare continues to use this repaired owned-payload path. The four new test cases
exercise both instance overrides through both schema and owned validation and
assert ValueError, no callback calls and unchanged ambient bytes. These are
meaningful targeted controls; they do not constitute actual finalizer evidence.

The owner relays root-verified R163 four RED failures (DID NOT RAISE ValueError)
and custody PASS. Those execution observations are attributed to root; fixed-source
execution was still pending when this follow-up was written. The original R162
finding/history above is retained. No new concrete P1/P2 was identified in this
narrow repair review. All existing native success/continuation, failure-cut, CUDA
and package qualification gaps remain unchanged.
