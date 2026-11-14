# Independent R144 narrow diagnostic repair review

2026-11-14. Reviewer `/root/bac_astra_env_c2_review`. **SPEC/QUALITY: approved for
the narrow accepted-cursor diagnostic repair**, on the exact source and executed
51-case evidence below. This closes the identified diagnostic-reentry defect,
not the remaining29 broader owner failures, restore integration, full C2 or BAC.
The separately rebound nine-case independent probe is awaiting root's R144 run
at this seal; historical R142 passes are not relabeled as R144 execution.

## Reviewed design, implementation and regression behavior

The approved composite C2 design explicitly permits diagnostic phase/cursor
reads under an explicit locked-external/private-internal policy. The original
implementation guarded `accepted_episode_seqs` externally but refused its
legitimate same-thread read from the already-guarded reset observer. That was a
real in-scope regression, as review-v2 recorded; it was not deferred hardening.

The actual final change adds ONLY `accepted_episode_seqs` beside `world_phase`
in the source-fixed held-active-call diagnostic exception. PID validation and
exact active Thread-object matching still occur first. The original guarded
method still owns domain admission and ENV's actual lock. The exception does
not create a reverse record, alter the claim validation slot or terminal denial,
bind an operation, admit a new retained scope, or bypass peer mutation/export
guards. Other threads continue into common admission before ENV exclusion.
An idle unbound retained scope still cannot call arbitrary guarded methods.

The ENV getter body remains unchanged: `MappingProxyType(dict(_world_cursors))`.
It returns a read-only owned copy, not live mutable storage or healthy authority.
During provisional reset that copy reports the last accepted cursors, while the
separate VFS projection already contains the pending reservation. The repair
does not publish that candidate early or change receipt/generation/revision
checks, reset RNG behavior, participation, original physical validation, callback
cleanup or completion authority. Fresh source inspection found no broader
mutation permission introduced by this exception.

Both new complete tests were independently read, in the context of the already
reviewed focused suite and full ENV/helper bodies:

- The genuine reset/evaluation observer reads old zero accepted cursors beside
  actual reservation-one VFS context, refuses attempted write to the returned
  mapping, and refuses VFS export plus affordance mutation. After acceptance,
  its retained diagnostic copy remains zero while a new copy reports one.
  Exact-reservation retries before and after a genuine A-only POP step preserve
  actual RNG bytes, identity/counts/tick and do not rerun reset evaluation.
- The external reader uses an actual second Thread and transparent admission
  observer. While ENV retention holds common admission, the peer reaches that
  admission but cannot enter or obtain cursor data; after release it succeeds.
  This distinguishes the narrow same-call exception from unlocked public reads.

## Exact source and actual evidence

R144 tree `ed561dc04fcffba4f6617f343862d54db6a8dad0`, base
`a42d61920ab302e16a4aab885fbbd44640e5d908`, manifest SHA256
`42fe2729f820795f4d5f94720e73c0feb20756ecb745ace2f6fb87711fe6cec8`.

| Body | Lines | SHA256 |
| --- | ---: | --- |
| src/townlet/environment/vectorized_env.py | 2949 | `aefccf149c20d9d1b7505539a7e261c7a0aa9ce9e40898a1fc18f5f3691c9b22` |
| src/townlet/environment/parent_custody.py | 252 | `bc83c8ce94da32cf9296692e167bbab42c52794cb2d3da91595d19b3cd176022` |
| tests/test_townlet/regressions/bac/test_environment_parent_custody.py | 840 | `372745a1c584d92ac0349479010f1d195a4fae9d89d4c2ba449a445297e6f68b` |
| independent test_env_c2_independent_v1.py, rebound only | 393 | `b0b5837ca9b4d4997fa3bca2730053a0e95f111fab41184f73aa4352ba2e2e0f` |

Final whole-body budget **4434/four**, unchanged source-read boundaries. No new
POP/core/runtime/BANK/fixture producer body was read; no APP edit/import/runtime
or Git action occurred here. The original VFS regression result is root-supplied
execution evidence; its body was not added to this review inventory.

Inspected the actual R143 failing log/result: two new cases give **1 FAIL / 1 PASS**.
The failing reset diagnostic reaches `_reverse_entry` and raises exact
`ValueError: ENV public methods cannot reenter active work`.
R143 result SHA256 `c7408b0cde3777b943a7331793cbef2d60565b6e7e8028c40a09312a96c49a71`,
log SHA256 `37e2602d04672deb513013276fab447dbc6cda23b65ec7f2ba7769edec26b92a`;
attempt path is `Q/wave35-r143-c2-diagnostic-runtime-attempt-1`.

Inspected R144 actual result/custody records at
`Q/wave35-r144-c2-diagnostic-runtime-attempt-1`: **51 PASS / 0 SKIP**, exit0,
23.08767318399623 seconds, 50 focused C2 cases plus the original VFS diagnostic
node. The actual command uses two xdist workers; custody reports three process
identities and source/index/import/thread/fixture custody PASS, 824 source guards,
573 config digests and 13 protected artifacts. Result SHA256
`4e3aac0000249d72e005578eb899a31d6d3c994b97d6f4b423b1ce01953575d6`, custody SHA256
`047c4b49c70420fae72da4f09f783c473dc890f17ad4e1a0323b4f979a9034b7`, log SHA256
`84772cfcb25c24e4268decbfd99202dabab1f326ca77cabf460031c6fb794878`.
Root also reports collection51/custody PASS; collection is not added as runtime
coverage. Here Q is `/workspace/bac-review-2026-11-01/qualification`.

## Scope still open

The previous four-suite result234 PASS/30 FAIL/4 SKIP stays historical. This
specific defect now has genuine red/green evidence; root retains **29 remaining
owner failures** requiring their source-backed dispositions. No full broad-suite
green result is implied. The separate R144 nine-case probe must retain its own
actual source/custody/fork witness and cannot borrow R142's process evidence.
Restore-correlation design review resumes only after its exact proposal exists.
Manual/no-decision driver, truthful inventory and completing-owner consumer,
constructor/cohort, full restore/runner/recurrent integration, CUDA hardware,
global typing/coverage/package and publication gates remain mandatory.
