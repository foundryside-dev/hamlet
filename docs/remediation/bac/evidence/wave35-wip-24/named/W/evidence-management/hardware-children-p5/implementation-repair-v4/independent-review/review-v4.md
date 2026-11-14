# Independent P5 repair review v4

Disposition: **BOUNDED APPROVAL — exact P5 tooling freeze**. No remaining material
P1/P2 finding was identified within the authorized implementation/design review
and finite inert verification packet. All46 independent cases match their
expected outcomes. The complete279 authored synthetic tests independently pass.
This is not P4, APP, actual source-owner, full-chain or hardware qualification.

Reviewer `/root/bac_p5_independent_review` is separate from author
`/root/bac_astra_p4_p5_owner_contract`. The reviewer independently developed the
adversarial cases, retained the earlier failures and made no implementation
edits. V4 source changes were checked against the previously reviewed exact v3
source and the accepted design, then the actual v4 bytes were executed. Earlier
full-source reviews and their additive repair reviews remain linked evidence.

## Exact approved subject

- Author freeze-v4 SHA256:
  `380cd2a07937c610f70182fd5486af877f1797f868e73a2b448af1449696a4c2`.
- `Q/verify_bac_hardware_children_v1.py`,1518 lines,79319 bytes:
  `ecc7b3c32716adfb19bf8e115f835dffb12468549d877561079db57a8a37e83c`.
- `Q/test_verify_bac_hardware_children_v1.py`,1703 lines,72891 bytes:
  `fac752e3c7ca0b33f96c78a6eefe0bd39a0d4e378f6b456728a86b86e3affd4b`.
- Read-only `Q/bac_hardware_protocol_v1.py`,526 lines:
  `e4f31eacb0e4499655a19ec91a4f5618a7b2ad3f4090e7ed068816b311e00860`.
- Author HANDOFF.md SHA256:
  `2f82e690af12b0432a894dcadc7d64334727cf377c5d2f5a7a40dc1a300fb899`.

Q is `/workspace/bac-review-2026-11-01/qualification`. Approval applies only to
these exact bytes with the accepted owner contract SHA256
`960f6e1b1dec411007c9d33ab388ea9b99d560c0c701f008fe5fdf113645af97`,
root adoption SHA256
`1bfd632c5f890a0eee0748ccc75c72ea3c09c133e739527ca2e3117865deb50a`,
and approved explicit-selector/canonical-owner correction SHA256
`e685af9bf32907371aabc676fb7988a47633a906765e033bf36b37e7bf92d9bd`.
Any changed implementation, dependency or accepted contract requires appropriate
new review; a mutable pathname does not carry this approval forward.

## Repair verification and design assessment

The last two contract-bound gaps are repaired. An outer spawn's actual parent
must match the job's unique configured controller ID and kind; the existing
parent START/END binding carries that role through the lifetime. This rejects
coherent substitution of both parent records while preserving a legitimately
renamed controller ID. It does not force equality between distinct canonical,
selected strict, RNG or fork contract role subsets.

Passing call/teardown reports must occur no earlier than the selected child's
observed END and within the actual emitting parent lifetime. Both earlier pure
and standalone false acceptances now refuse; the standalone refusal publishes no
receipt. Setup before child execution remains valid. Exact microsecond equality
at the child-END lower bound passes, while one microsecond earlier refuses.
This is a necessary causal lower bound only. No sampler/process prefix is
equated to complete recorder return; fork returns and parent custody retain
their independent monotonic arithmetic and constraints.

All31 previously demonstrated false-acceptance mutations now refuse on the
current valid fixture graphs: phase substitutions, malformed private schemas,
source/import and role crosswires, process/claim/lock contradictions, guard
return/ack/reap after parent END, out-of-lifetime reports and the final coherent
controller/report attacks. Their original exact failed inputs, actual results,
source snapshots and reports remain retained in v1/v2/v3. No old result was
rewritten or promoted to execution of new bytes.

The cumulative actual-source/design review covers fixed job/case dispatch,
closed type-sensitive parsing, finite document consumption, canonical owner and
selected-obligation evidence bindings, source/process/report/clock correspondence,
three guard trials and4/7/5 action sets, complete3/6/8/10 timing bounds, typed
producer RNG/error predicates, phase recomputation, unsupported/failed/unrun
distinctions, pure-function isolation and exclusive no-follow standalone writes.
The direct required obligation_id API and role-subset corrections are preserved.
No dynamic payload-driven imports, APP execution or filesystem operations were
identified in the pure validation path. Standalone receipts retain their strict
component scope and observed validation identity; they acquire no root/no-writer
or common/hardware authority.

## Finite independent packet

The active `probe-v4.py` is301 lines, SHA256
`f576e68cff5fcf310c38382fe58b6ef9a35229c92ce1515875f9102819045403`.
It retains the previous42 semantic cases and adds only four bounded checks:
exact child-END/report equality, one-microsecond-early refusal, a valid separated
UTC standalone receipt, and a correctly configured non-hardcoded controller ID.

`attempt-01`:46 cases, exit0, empty stderr;13 valid controls satisfied and33
expected refusals observed. The refusals comprise all31 earlier false accepts,
the original exit-bool negative control and the new microsecond boundary case.
There are zero expectation mismatches.

Positive controls include the distinct phase pair, typed producer data, inherited
strict owner, actual observer END equal to reap, both endpoints exactly on their
10-second deadline, reap-before-ack, explicit correct required/inherited import
joins, separated UTC reports, and successful exclusive standalone publication.
The authored suite additionally retains inclusive3/6/8/10 and valid7.9-return/
8.1-ack cases, document/schema adversaries and receipt exclusivity/no-follow tests.

`attempt-02`: the complete279 authored tests pass, exit0, pytest4.83s, empty
stderr. Plugin autoload is disabled; no conftest/cacheprovider, `/dev/null` config
and an exclusive retained basetemp are used. These tests overlap the independent
packet and previous runs; no combined unique-test count or coverage is claimed.

Each launch retains actual OS argv, interpreter/cwd, PID/PPID/start token,
host/boot, UTC interval, measured duration, stdout/stderr, probe hash, exact source
before/after snapshots and all generated fixture evidence. Source/tests/P0 were
unchanged throughout both runs. Both used the existing .venv Python, affinity[0]
and4GiB address-space cap. The runtime slot was released after attempt-02.

All regular files are hash-inventoried and reverified; pytest symlinks are
separately recorded as symlinks. Historical review artifacts and author failed
attempts remain linked through immutable freezes. The author candidly records
its earlier fixture mistakes; this approval relies on the final frozen source
and the actual independent runs, not those earlier invalid fixtures.

## Boundaries and next handoff

The conservative body budget is1518+1703+526+752 unused historical allowance+
301 active probe=4800 lines across at most five logical bodies. The historical
verifier was not read. No APP/P3/P4 implementation body, APP/Torch import, actual
producer child, Git command, CUDA, network, new environment, branch/worktree/
checkout, source/index edit or spending operation occurred. Described commands
and source-shaped fixtures remain inert; historical snapshots are text evidence.

This bounded approval supports root's exact tooling adoption decision and a
separate, explicitly scoped P4 integration handoff. It does not prove actual
source assertions, controller/child execution, immutable root authority or real
hardware facts. P4 current-owner transport/literal dispatch, actual source-owned
startup/inter-op5 and assertion custody, actual P3→P2→P4→P5 integration, abrupt
guard-death/live-Git backstop, mandatory APP/package checks and six real-CUDA
groups remain outstanding.

The user expects a16-worker CUDA server this evening. No access, allocation or
hardware runtime was observed in this review; actual CUDA remains UNRUN. The
finite review is complete, with no further optional expansion or repeated
runtime required for this unchanged tooling freeze.
