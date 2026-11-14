# Independent P5 repair review v2

Disposition: **CHANGES REQUIRED**. All twenty original false-acceptance
mutations now refuse on the corrected current fixture graphs, and the five
original positive controls remain satisfied. Eight additional resealed probes
expose remaining causal, role and source-origin joins. The complete authored
suite independently reports **267 passed**, separately from the probes.

Reviewer `/root/bac_p5_independent_review` is separate from author
`/root/bac_astra_p4_p5_owner_contract`. The reviewer made no implementation edits.
This is an additive exact-freeze review; v1 evidence and failures remain intact.
No P4, APP, hardware, full-chain or external source authority is acquired.

## Exact subject and accepted repairs

Author freeze-v2 SHA256:
`ff756a6e2f351312ecb6efb0b866fb616ac06c82fe46cfcb075d8f610b745ecb`.
HANDOFF.md SHA256:
`ac3241b2032de3654293f84fe9fb2101c6d5727a0cca9f033b86dcc9117dc04a`.
Source `Q/verify_bac_hardware_children_v1.py`: 1475 lines, SHA256
`84c92b654be50f1224190045882519496fdf57d842d43a62c5e21b6ba615e28d`.
Tests: 1610 lines, SHA256
`0ed6091b6b774f5fd907542438b02c9ffb7ab7a1be8d21b466621f4b48723ae9`.
Read-only current P0: 526 lines, SHA256
`e4f31eacb0e4499655a19ec91a4f5618a7b2ad3f4090e7ed068816b311e00860`.
Q is `/workspace/bac-review-2026-11-01/qualification`.

The same adopted design SHA256
`960f6e1b1dec411007c9d33ab388ea9b99d560c0c701f008fe5fdf113645af97`
and approved explicit-obligation/canonical-contract correction apply. The full
repaired implementation was reread, including fixed dispatch, strict guard
actions/trials, source/report joins, recursive transport schemas, timing,
producer RNG/error predicates, phase recomputation, result distinctions and
standalone publication. The test changes were checked against previously read
unchanged test bodies; no other implementation body was read.

F1's actual phase case/job binding and null/True complement are now explicit.
Both former phase substitutions reject with `phase wrapper actual case mismatch`.
F2's demonstrated malformed nested types reject, including through standalone.
F3's previously demonstrated process/claim/lock contradictions reject. The source
also adds complete recursive private descriptors and live opaque-reference hash
checks. These are substantive repairs, but they do not close all required joins.

The independent probe reconstructs the original twenty mutations using current
valid fixtures. In particular, inherited controls now contain two typed sampler
commands and consistent process/lock/command/emission clocks. Thus the repairs
are not credited merely because old malformed baseline fixtures now fail.
The immutable old exact subjects remain in the v1 review; they were not rewritten
or represented as current valid subjects.

## R1 — Parent lifetime still does not enclose guard return/acknowledgement/reap

Priority: blocking; remaining F3 scope. At source 609–614, parent END encloses
the guard START/END process timestamps. At 989–1005, recorder returns and parent
ack/reap endpoints are checked against launch deadlines and each other, without
being bounded by the actual observing parent's END.

From a valid inherited_pid bundle, change only outer child END monotonic_ns and
its matching elapsed_ns, then reseal:

- `parent-end-before-guard-return`: END=10,000,000,000; elapsed=8,000,000,000.
  The nested guard's process END at9.1s remains inside that lifetime, but its
  actual recorder return at10.9s, acknowledgement at11.1s and reap at11.2s occur
  after the observing parent has ended. Result: **satisfied**.
- `parent-end-before-guard-ack-reap`: END=11,000,000,000;
  elapsed=9,000,000,000. Actual return10.9s now fits, but parent receipt11.1s and
  reap11.2s still follow its END. Result: **satisfied**.

Require every strict owner endpoint to fit the actual process lifetime implied
by the final cleanup/source assertions. Preserve the approved 3/6/8/10 limits,
inclusive boundaries, 7.9-return/8.1-ack and either post-return ack/reap order.
Do not impose ack-before-reap or equate a process prefix timestamp to full return.

## R2 — Report and parent END observations can be assigned to the wrong lifetime/role

Priority: blocking; remaining F3/process correspondence scope. Report ordering
at750 is internal to the three reports, and the join at797 checks only their
process reference. Their UTC times are never bounded by that controller's START
and END. Parent END selection at609 matches identity/phase but fails to bind its
role to the START role; process() at495 only verifies that its new role separately
exists somewhere in the job.

Observed resealed cases:

- `reports-after-parent-end`: setup/call/teardown at
  `2026-11-15T00:00:00.000000Z`, controller START/END both recorded on November14.
  Result: **satisfied**.
- `reports-before-parent-start`: all reports at November13 instead. Result:
  **satisfied**.
- `standalone-reports-after-parent-end`: the late-report mutation survives live
  P0/no-follow checks and writes an exclusive **satisfied** strict receipt. It is
  even dated after actual validation on November14. The retained receipt is at
  `attempt-01/standalone-reports-after-parent-end/receipt.json`.
- `parent-end-substitutes-child-role`: change parent-end.role_id to the actual
  replay child role, parent-end.role to `spawn-child`, and its raw context role_id
  accordingly. Preserve the controller identity and all other graph bindings.
  Result: **satisfied**, although there is no controller-role END.

Bind each actual START/END pair's full invariant role/process properties, then
require report times to fall within their actual emitting parent lifetime and
source-owned ordering. Apply the same checks in the standalone path; relying on
future P4 validation leaves an incorrect strict-component receipt today.

## R3 — Named required/inherited module declarations can contradict actual origins

Priority: blocking; remaining F2 source/process correspondence scope. At536–539
and601–602, declared required/inherited import refs need only belong to the
candidate input set. The named alias is not joined to the actual process import
mapping. Candidate membership alone permits a different approved file to be
borrowed as the origin of a named loaded module.

Observed resealed cases:

- `inherited-module-alias-crosswired`: set admission-launch.inherited_imports to
  one member named `townlet.exploration.rng_custody` whose reference is the
  inherited test's assertion source file. The actual parent/guard process
  imports still record rng_custody.py. Result: **satisfied**.
- `required-import-alias-crosswired`: set every replay raw context's
  required_imports to that same module name with the replay test source ref and
  phases `[start,end]`. Parent and child contexts agree with each other, but
  disagree with their actual observed imports. Result: **satisfied**.

Join every declared name/ref/phase to the corresponding actual recorded import
origin under the approved source-owner contract. Preserve legitimate role subsets
and explicitly required aliases; do not infer aliases or permit a borrowed file
merely because it is another member of the candidate inventory. Add coherently
resealed cross-record negatives, not only wrong-type mutations.

## Retained execution evidence and accounting

The one active independent probe revision has238 lines, SHA256
`411eaf8d077f43f866f305cda99c8a45b1651ff514a01aadc65421f569352214`.
It preserves the original26 semantic cases and adds eight targeted cases.

- `attempt-01`: 34 probe cases. Five valid controls satisfy, all twenty original
  false-acceptance mutations and the original negative control refuse, eight
  new adversarial cases falsely satisfy. Exit1 reflects the retained review
  failures; stderr is empty. The refused standalone malformed case publishes
  no receipt, while the late-report standalone case publishes one.
- `attempt-02`: complete exact267 authored tests pass, exit0, pytest4.72s.
  Plugin autoload is disabled; `--noconftest`, `-c /dev/null`, no cacheprovider
  and an exclusive retained basetemp are used.

These selections overlap; no combined unique count or coverage claim is made.
Both actual launches retain UTC, duration, argv, interpreter, cwd, PID/PPID,
process start token, host/boot, stdout/stderr, exact source before/after text
snapshots and fixture inventories. Both used existing .venv Python, affinity[0]
and4GiB address-space cap. All three source hashes stayed unchanged throughout
each run. The runtime slot was released after attempt-02.

Budget: source1475 + tests1610 + P0526 + unused historical allowance752 +
probe238 =4601 lines across at most five logical bodies, below5000. The
historical verifier was not read. The old probe revision remains retained as
historical evidence; only the new revision executed. No APP/P3/P4/Git bodies,
APP/Torch imports, actual producer children, network, new environments,
branches/worktrees/checkouts, Git/index operation or spending occurred.

Synthetic fixture source-shaped files and command descriptions are inert; no
described Git or child command executes. Pure phase fixtures do not acquire live
P0/source-root qualification. The late-report standalone case additionally proves
its public live-reader acceptance. These are bounded tooling findings, not
evidence that actual APP or hardware behavior has executed.

## Next action

Repair the remaining complete joins under root-authorized source ownership,
retain v1/v2 failures and produce a new exact freeze. Independently verify the
specific repaired cases together with current valid controls and the bounded
suite. Original typed parsing and phase fixes must remain intact.

Root adoption, P4 literal wiring/current-owner transport, source-owned
startup/inter-op5 and assertion custody, actual P3→P2→P4→P5 integration, abrupt
guard death/live-Git backstop, APP/package checks and six real-CUDA groups remain
outstanding. Actual CUDA is UNRUN; server16 access/allocation remains unknown.
