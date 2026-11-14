# Independent P5 implementation review v1

Disposition: **CHANGES REQUIRED**. The exact author freeze has three blocking
correctness gaps. Its 125 authored synthetic tests pass independently, but the
resealed independent probes reproduce false satisfaction. This review grants no
P4, APP, full-chain, hardware, source-assertion or external root authority.

Reviewer: `/root/bac_p5_independent_review`, separate from implementation author
`/root/bac_astra_p4_p5_owner_contract`. The parent supplied the author as Astra
medium; this reviewer independently read the allowed implementation and fixtures,
constructed the mutations below and observed their results. No implementation
source was edited by the reviewer.

Reviewed freeze: `freeze-v1.json`, SHA256
`ef7c4935eac1fa2cdc88a61b47a2361b995b16793bff6c34534ee055a6c0ea21`.
Source: `Q/verify_bac_hardware_children_v1.py`, 1256 lines, SHA256
`b1734829f8e57bf3d9538441ceca901e4eabd3703b243f564fb037e7c7f89843`.
Tests: 1354 lines, SHA256
`69fcbc92d1f8194c32260a53a92b1fccf1e8226b45a02aadd25372428ad492fd`.
P0: 526 lines, SHA256
`e4f31eacb0e4499655a19ec91a4f5618a7b2ad3f4090e7ed068816b311e00860`.
Here Q is `/workspace/bac-review-2026-11-01/qualification`.

The review applies the adopted owner contract SHA256
`960f6e1b1dec411007c9d33ab388ea9b99d560c0c701f008fe5fdf113645af97`,
root adoption SHA256
`1bfd632c5f890a0eee0748ccc75c72ea3c09c133e739527ca2e3117865deb50a`,
and approved interface correction SHA256
`e685af9bf32907371aabc676fb7988a47633a906765e033bf36b37e7bf92d9bd`.
The required explicit standalone obligation ID and distinct canonical/RNG/fork
contracts are accepted corrections, not findings.

## F1 — Bind phase labels to the actual recomputed subject

Priority: blocking. Source lines 951–976 compare the wrapper's `case` to the
expected label and recompute its named receipt, but never compare the selected
subject's actual case/job to that label. The shared comparison at 985–994 omits
completion state, so two independently identified reference jobs both containing
`completion_failed: null` satisfy a reference/failure pair.

Observed cases:

- `phase-two-reference-runs-no-failure-run`: both actual jobs are
  `cuda-core-invocation-phase-reference`, with distinct spec refs, attempt IDs
  `reference`/`failure`, and distinct output roots. Their complete child phase
  objects both contain null completion. The second wrapper still labels itself
  `invocation_phase_failure`. Result: **satisfied**.
- `phase-swapped-jobs-relabelled-wrapper`: reverse the two actual subjects,
  restore wrapper labels to reference/failure order and update related_attempts.
  Complete actual job identities/receipts remain internally consistent. Result:
  **satisfied**.

These probes retain all bytes, reseal hashes and retain recomputed receipt result
bindings; they do not rely on stale references. Repair must bind wrapper case to
the actual finite job/case and require null then exact True on the corresponding
recomputed phases. Preserve valid distinct attempts/output roots and sequential
numeric PID reuse. Add regressions for both substitutions, not only reversing
the wrapper array without relabelling it.

## F2 — Validate nested transport types and finite reference closure

Priority: blocking. `process` (around 371–407), `pair_process` (around 425–498)
and `timing` (around 817–850) check exact top-level keys for private transport
records but leave several nested values untyped or unchecked. Exact dictionary
keys alone do not implement the adopted recursive closed schema. Reader.get only
invokes P0 live validation for P0-schema records; private launch/raw/context/
sampler values retain these gaps in the standalone path.

Observed malformed cases all return **satisfied** after resealing:

- Launch command is boolean True; parent_argv and inherited_imports are objects;
  at and monotonic_ns are booleans; source_witness is the unrelated opaque ref.
- Raw worker_identity and observation_limit are arbitrary objects.
- Raw context trusted_grant and policy are booleans; required_imports is an
  arbitrary object.
- Sampler commands is `[true]`; lock_acquired_ns is boolean True.

The retained `standalone-malformed-launch-and-grant/receipt.json` is stronger than
a pure-path demonstration: real no-follow reads and current live P0 validation
still produce an exclusive **satisfied** receipt when launch.command=True and
child START raw.context.trusted_grant=True. All materialized files are inert
synthetic data/source-shaped bytes; none are imported as APP producers.

Repair requires a finite, complete recursive schema and schema-directed reference
position audit across every consumed private record, including launch, context,
raw, claim, sampler, emission and receipt. Validate opaque leaves as references;
follow required parsed references at the prescribed positions. Do not replace
this with arbitrary path-shaped scanning, dynamic dispatch, a relaxed schema, or
only a blacklist of these demonstrated values. Keep external root/source-grant
authority and P4 common qualification explicitly separate.

## F3 — Correlate process/claim clocks with the owner observations

Priority: blocking. `pair_process` checks child START<=END and clock-domain
identity, while `timing` validates sampler/emission/return inequalities. It does
not relate the actual process timestamps to their respective recorder call
brackets. Parent END is merely located and parsed around lines 701–709. Claim
monotonic_ns is checked only as a nonnegative integer around lines 450–452.

Observed contradictory cases all return **satisfied** after resealing:

- `guard-process-time-after-return`: admission END process monotonic_ns becomes
  999,000,000,000 while that END call has already returned at 10,900,000,000.
- `parent-end-before-child-start`: controller END monotonic_ns becomes 1, before
  its own START at 1,000,000,000 and before child START at 2,000,000,000.
- `claim-time-before-launch`: child claim monotonic_ns becomes 0, before its
  owner launch at 1,500,000,000.
- `sampler-lock-reversed`: lock_released_ns becomes 1, before its acquisition at
  3,000,000,000 and outside the sampler interval.

Repair the actual causal correspondences against the approved producer ordering,
including typed clock fields and nested sampler lock/command chronology. Do not
invent a new ack/reap ordering or shorten the allowed ack deadline: 7.9-second
return with 8.1-second acknowledgement, reap-before-ack and inclusive 3/6/8/10
limits remain required positive cases. Source execution authority remains a
separate owner-instrumentation prerequisite.

## Verification and accounting

`attempt-01` executes the single independent 208-line probe, SHA256
`4a28229c955395c697aacbe28fda4d2af918625c1a0118b714da193f16276195`.
It has 26 cases: five valid controls satisfied; one negative exit-bool control
refused; twenty adversarial cases unexpectedly satisfied. Exit 1 is the retained
expected review failure status, not a harness crash. stderr is empty.

`attempt-02` runs the author's complete suite with plugin autoload disabled,
`--noconftest`, `-c /dev/null`, an exclusive retained basetemp and no cacheprovider:
**125 passed in 1.87s**, exit 0. These are separate overlapping selections;
there is no combined unique-test count or broader coverage claim.

Both executions use the existing `/workspace/hamlet/.venv/bin/python`, affinity
[0] and a 4GiB address-space cap. Each retains actual argv, PID, PPID, start token,
host, boot ID, UTC interval, duration, stdout, stderr, before/after exact inert
source snapshots, probe hash and a retained file inventory. All three source
hashes remained unchanged throughout each execution. The 1CPU runtime slot was
released after attempt-02. No further runtime is needed for these v1 findings.

Only the allowed P5 source/tests and P0 bodies were read (3136 lines). Historical
752-line verifier body was not needed or read. Including the 208-line probe gives
3344 lines actually read/authored; even charging the unused historical allowance
gives 4096 lines, within the granted five-body/5000-line bound. No APP, Torch,
Git, network, producer child, branch, worktree, checkout, source-execution copy,
index or new spending operation occurred.

The author fixture helpers were reused to construct complete synthetic graphs;
independent mutations and expected refusals were authored here. Phase probes test
the pure interface and do not claim live P0/source-root qualification of the
synthetic phase fixtures. The standalone malformed-field probe additionally
demonstrates the public live-reader boundary. Existing author-test success and
these controls do not establish actual strict owner behavior or hardware.

A later read-only metadata inspection initially selected the one-field witness
schema instead of the phase wrapper and raised `KeyError: subjects`; this was
not a verifier/test attempt. A corrected inspection required the subjects key
and confirmed both retained counterexample contents. It changed no artifact or
finding. The two runtime attempts above are complete, unhidden and immutable.

## Scope assessment and next action

Static inspection found fixed dispatch, no dynamic import or filesystem operation
in the pure validator, explicit selected obligations, typed guard 4/7/5 action
predicates, three trials, whole-call 3/6/8/10 arithmetic, typed producer RNG/error
checks, source/import/report joins and exclusive standalone writes. These useful
checks do not cure F1–F3. Unsupported, failed and unrun authored tests remain
separately classified; no acceptance is inferred from a supplied success string.

Repair under root-authorized source ownership, add finite regressions and retain
a new exact freeze. Independently rerun these exact semantic counterexamples on
that new freeze, plus the complete bounded suite. Retain v1 and its failures.
P4 wiring, source-owned startup/inter-op=5 and assertion custody, actual complete
P3→P2→P4→P5 behavior, abrupt guard death/live-Git backstop, APP/package checks and
all six real-CUDA groups remain outstanding regardless of these tooling results.
