# Independent P5 repair review v3

Disposition: **CHANGES REQUIRED**, limited to the two material joins below.
All28 previously demonstrated false-acceptance mutations now refuse. Ten valid
controls satisfy, including the new boundary/import/UTC controls. Three new
coherently resealed cases falsely satisfy. The separate complete authored suite
reports **275 passed**. No further exploratory expansion or runtime follows this
finite42-case packet.

Reviewer `/root/bac_p5_independent_review` is separate from author
`/root/bac_astra_p4_p5_owner_contract` and made no implementation edits. V3 changes
were reviewed against the previously fully reviewed v2 source and unchanged
accepted design, then exercised on actual frozen v3 bytes. The new cases and
expected results were independently authored. V1/v2 evidence remains immutable.

## Exact reviewed subject

- Freeze-v3 SHA256:
  `5e67213a22a93da7652c1cbe4ce8d61b1f9583f8161e23442c73a64ee511e858`.
- Source1511 lines:
  `34df34f0d5a1b80a90d8d553b96f3a7fa9c3a9258c1601742110df39568bd81c`.
- Tests1651 lines:
  `89a44f3d7c8fd77bd9975a7192b46522cd2a6683ec85df9d3804e3e4294317f4`.
- Read-only P0526 lines:
  `e4f31eacb0e4499655a19ec91a4f5618a7b2ad3f4090e7ed068816b311e00860`.
- HANDOFF.md:
  `f846fdd0a8b2aa06f23f6d9234bc3c02610b6c50de106a8adf04d15863eb0cbb`.

Source/tests/P0 are the named Q files, where Q is
`/workspace/bac-review-2026-11-01/qualification`. The accepted owner contract is
`CUDA-HARDWARE-P4-P5-OWNER-CONTRACT-v1.md`, SHA256
`960f6e1b1dec411007c9d33ab388ea9b99d560c0c701f008fe5fdf113645af97`.
The previously approved explicit obligation selector and distinct canonical/
RNG/fork contract-role subsets remain valid; no proposed finding changes them.

## V3-R1 — Coherent parent role substitution removes the actual controller

Priority: blocking. Accepted source-owner-map requirement:

> Fixed 28 CPU/control jobs have zero xdist workers, one actual controller and
> one spawn child; inherited_pid adds exactly three fork guards.

The contract also identifies obligation-evidence.producer_process as the actual
parent START emitting the terminal payload. The actual strict owner graph must
therefore include the controller parent and the configured spawned owner, not
merely declare those roles in a sealed job.

`both-parent-phases-substitute-child-role` starts from the valid replay bundle.
For both parent and parent-end, it sets role_id to the configured replay child
role and role to `spawn-child`; it changes the matching raw.context.role_id too.
Both parent identities, the actual child identity, reports, payloads, references,
job definitions and canonical contract stay internally consistent and are
resealed. Result: **satisfied**, despite two observed spawn-child identities and
no observed controller identity.

The v3 check that parent START and END have the same role fixes the previous
one-sided substitution but cannot reject this coherent pair. `process()` checks
that each role belongs to the job; `pair_process()` does not require the outer
actual parent to be the controller. Planned role counts in `run()` do not count
the actual observed identities by role.

Bind the actual parent/controller and spawned owner roles in the fixed case's
process graph. This is an observed-role/cardinality requirement. It does **not**
require equality between canonical, selected strict, RNG or fork contracts:
their distinct approved role subsets and exact job definitions remain intact.

## V3-R2 — Passing call/teardown can predate the child's observed execution

Priority: blocking. Accepted payload/source-owner requirements:

> Emit final parent payload only after cleanup and final assertions complete.
> Passing setup/call/teardown and parent END are joined later through completion.

The same contract specifies core/replay final RNG assertion checkpoint
`after_child_cleanup`, and the source-owner map requires actual Process/queue
semantics. Its spawn acceptance matrix requires refusal of an early payload,
cleanup failure or teardown failure. A passing pytest call report is emitted
after that source-owned call completes; teardown follows it. The child's START
and END observations occur inside the child execution that the parent waits for
and cleans up within that call.

The new positive `control-separated-utc-timeline` establishes coherent distinct
UTC observations, all on2026-11-14 with exact microseconds:

- Controller START00s and END20s; child START02s and END15s; raw.at matches.
- Launch01.5s; claim02s; reports setup01s, call16s, teardown17s.
- Result END20s and elapsed20 seconds. This control is **satisfied**.

Two independently resealed mutations preserve that controller lifetime:

- `passing-call-before-child-start` moves call to01.75s and teardown to01.8s,
  before the child's observed START02s. Result: **satisfied**.
- `passing-call-before-child-end-standalone` moves call to14s and teardown to
 14.5s, before the child's observed END15s. Current live P0/no-follow validation
  still writes an exclusive **satisfied** strict receipt. The exact receipt and
  materialized inert graph are retained in that case directory.

V3 constrains reports to the controller's overall lifetime and keeps their
internal setup/call/teardown order, but does not join call completion to the
child work belonging to the selected case. Merely being inside the parent's
lifetime does not establish after-child-cleanup source-assertion custody.

The required refusal is a **necessary causal lower bound**, not an assertion
that a process timestamp proves full recorder return. The child END observation
is an earlier point inside child execution; its recorder return and eventual
Process termination/parent join occur later. A report preceding even that earlier
point is contradictory. Do not equate sampler timestamps, process END prefixes
or emission timestamps with complete function returns, and do not invent missing
spawn return observations. Preserve separately recorded fork return/ack/reap
semantics and all existing3/6/8/10 bounds. Setup may validly precede child work.

## What v3 successfully repairs

The previous two guard-lifetime negatives now reject because acknowledgement/
reap must precede the observing parent's END; their after-return ordering also
encloses returns transitively. Previous early/late controller-lifetime reports,
one-sided parent END role substitution, and required/inherited alias crosswires
all refuse. The original twenty v1 mutations still refuse on current valid
fixtures, including both phase substitutions and malformed standalone transport.

Fresh valid controls satisfy for: observer END exactly equal to reap; both
endpoints exactly on the10-second deadline; actual reap-before-ack; correct
explicit required/inherited mappings; and the separated UTC timeline above.
Existing authored tests preserve inclusive3/6/8/10 and7.9-return/8.1-ack cases.
No valid boundary failure was observed in this packet.

## Evidence and accounting

`probe-v3.py` is the single active287-line independent probe revision, SHA256
`411391537cb9cbd462676801fe05f2e8a7cd4e8cf396ded09e53dce81fcb6bb2`.
Its previous revisions remain retained as historical artifacts.

- `attempt-01`:42 cases;10 valid controls satisfy,28 prior adversarial cases
  refuse, one original negative control refuses, three fresh cases falsely
  satisfy. Exit1 is the recorded review failure result; stderr is empty. The
  former late-controller-report standalone case refuses without a receipt;
  the fresh before-child-END standalone case publishes one.
- `attempt-02`: complete275 authored synthetic tests pass, exit0, pytest4.54s.
  Plugin autoload disabled, no conftest/cacheprovider, `/dev/null` config and
  exclusive retained basetemp.

Selections overlap and are not summed. Each execution retains actual argv,
interpreter/cwd, PID/PPID/start token, host/boot, UTC interval/duration, stdout,
stderr, exact source before/after snapshots and fixture inventories. Source,
tests and P0 hashes remained unchanged throughout both executions. Both used
existing .venv Python, affinity[0] and4GiB address-space cap. Runtime slot released.

Conservative body budget:1511+1651+526+752 unused historical allowance+287 probe
=4727 lines across at most five logical bodies, below5000. Historical/P3/P4/APP
bodies were not read. No APP/Torch import, actual producer child, Git command,
CUDA, network, new environment, branch/worktree/checkout, source edit, index
operation or spending occurred. Source-shaped fixtures and described commands
are inert. No source-qualified assertion or external root authority is acquired.

## Disposition and remaining gates

Root should review these two exact contract-bound findings before authorizing
the next finite repair. Preserve every existing freeze, failed probe and suite
result. Further repair needs a new exact freeze and bounded independent review.

P4 dispatch/current-owner transport, actual source-owned startup/inter-op5,
assertion custody, actual P3→P2→P4→P5 integration, abrupt guard death/live-Git
backstop, mandatory APP/package checks and six real-CUDA groups remain required.
The user expects a16-worker CUDA server this evening; no access, allocation or
hardware execution was observed here. Actual CUDA remains UNRUN.
