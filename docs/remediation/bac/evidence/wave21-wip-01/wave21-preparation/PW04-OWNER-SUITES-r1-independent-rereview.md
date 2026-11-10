# PW04 owner suites R1 independent rereview

Basis: R0 tree `04d822c62185771e689b38f5d84804ec0ef9b5a8` to R1 tree `4c0cec9a4cd8893910a0abb64c396eb7011f5787`, base `7e702ab885c2bc1bba37652273cfb89742624f08`. This follows the complete five-file R0 review; read the appended author report and actual R1 greedy-fix review package, then inspected the actual changed constructor and unchanged action oracle. No sixth executable source or global fixture implementation was opened. Root's separate global basic_env identity-input repair and fresh Sol review are attributed prerequisites, not code reviewed here.

Specification verdict: **PASS for the owned fixture correction and selected150 component cases**. Quality verdict: **PASS for the owned correction**. The required actual runner/native integration remains **REQUIRED OPEN**; its previous real failure is not waived. Full151 suite PASS and integrated PW04/BAC release are not claimed.

## Source review and finding disposition

Independently verified author report SHA256 `ff478a3632b2f7fd1f4471f951f14a59b2401f5f2a039b5adc0b7d6f72077776` and strategies SHA256 `9dca12dcd0c58aef663b3287052fed40e3c233517e6010ad4513fe0cc7f43dc7`. The other four owned file hashes independently match R0 exactly. Strategies is1358 lines; five-file total2596, within the unchanged3200 total and every per-file ceiling.

The only owned delta is explicit `epsilon_min=0.0` beside `epsilon_start=0.0` in TestAdaptiveIntrinsicActionSelection.test_select_actions_delegates_to_rnd, lines709–716. It selects a valid zero exploration schedule, preserving the intended deterministic greedy positive and both original action assertions at lines740–741. No exception expectation, fallback, default, provider invariant, oracle or parameter matrix was weakened. R0 finding1 is closed by this source correction plus actual passing component execution.

R0 finding2's18 basic_env setup errors no longer occur in this independent component run: all18 cases now pass. Their separately owned helper repair was not inspected as a sixth source. R0 finding3 remains open: the unchanged actual DemoRunner/native test was deliberately excluded from this focused component run, not skipped/xfail-marked in source. No integration repair is inferred.

The R0 static preservation/no-legacy review remains applicable to the unchanged other four files and unchanged strategies bodies: explicit shared constructor inputs, real model/Adam/RMS/ICM gradient behavior, actual current native mutations, atomic unsupported-format refusal plus complete native positive continuation. No additional defect found in this narrow R1 review.

## Independent component execution and custody

Executed exactly the authorized locked runner command from /workspace/hamlet:

`TMPDIR=/workspace/bac-review-2026-11-01/qualification/scratch/tmp-wave08-r3 python /workspace/bac-review-2026-11-01/qualification/run_bac_packet_checks_locked.py /workspace/bac-review-2026-11-01/qualification/wave21-r1-independent-components-spec.json`

Then:

`python /workspace/bac-review-2026-11-01/qualification/verify_bac_run.py /workspace/bac-review-2026-11-01/qualification/wave21-r1-independent-components-spec.json`

Actual result: **150 passed, 1 deselected in48.18s**, no failures/errors, skipped0, xfailed0, xpassed0, warnings0. Locked runner and verifier both exit0; locked-runner wall time69.977210s. Runtime session13929 and verifier completed; no reviewer runtime session remains open.

The inspected spec contains exactly one deselection:

`tests/test_townlet/regressions/bac/test_rnd_service.py::test_native_runner_checkpoint_retains_tail_and_rejects_corruption`

The separate `wave21/r1-required-runner-open.json` explicitly records that case as REQUIRED OPEN and not optional/qualified, preserving its source unchanged. This is150 component evidence, not151 suite evidence; the next full qualification must include the actual runner after its causal prerequisites are fixed.

Verifier custody **PASS** for this named executable evidence:196 source guards,573 config digests,13 protected artifacts,1 process identity,14 worktree registry records/1 available worktree; source/index/import/threads/fixture custody PASS. Base/tree match the above R1 seal.

Log: `/workspace/bac-review-2026-11-01/qualification/wave21-r1-independent-components/independent-components.log`.

Log SHA256: `84d716496ee049c3f6f3915e7b8c889ec37d80422ee5090befe2ccb04ea1ff48`.

Manifest SHA256: `360779a793d93e63a97e664c62ea1879b20aa98e345566135356164152325eec`.

Harness SHA256: `180558c22da088a57326aa9251fbb64761e2788f18cb982532525b84b571f791`.

## Remaining required work

Actual ordinary runner world identity, bank/context/identity/completion custody, private factory/RNG ownership, RR/LIVE transport, POP/native parent transactional restore and real runner artifact/receiving/next-update proof remain required under their actual owners. The existing nine mypy errors and coherent whole gates remain OPEN pending their own evidence. Root's component/backend/guard results are separate selections and do not close these obligations. No source/test/index change, branch/worktree, repository copy, deletion or subagent was used in this rereview; this ignored report is its sole write.
