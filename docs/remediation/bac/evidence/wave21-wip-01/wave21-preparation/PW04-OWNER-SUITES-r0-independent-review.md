# PW04 owner suites r0 independent static review

Review basis: frozen base `7e702ab885c2bc1bba37652273cfb89742624f08`, supplied candidate tree `04d822c62185771e689b38f5d84804ec0ef9b5a8`. Read the wave21 brief first, then the author report and supplied migration diff. Independently read all five complete current owned test files and the public CURRENT-BACKEND-LOCAL-SERVICE-CONTRACT.md. No sixth executable source, provider implementation, helper, POP, WS or core regression source was inspected. No pytest, collection, project imports, runtime, Git/index operations, branch/worktree, repository copy, deletion, source/test edits or subagents were used. This ignored review is the sole write.

Specification verdict: **PASS for the static five-test migration**, with actual execution and external integration qualification still REQUIRED OPEN.

Quality verdict: **PASS for the reviewed migration**, no blocking defect found. This is not a runtime PASS or integrated release approval.

## Seal and scope evidence

`sha256sum` independently matched the required author-report SHA256 `2fe344020e99a2af95d39fd8e1b7c88d922fd0f2f70e9ab1538d15dfb5ae3bc2` and all five file hashes reported by the author:

| Owned file | Lines/cap | SHA256 |
| --- | --- | --- |
| unit/exploration/test_rnd_stats_update_timing.py | 66/100 | 615787133f15e6553a337c30addd2e551222cbb41771d0de4f74c595ebfb13a1 |
| unit/exploration/test_rnd_normalization.py | 186/250 | 626299c949a45d567664b6142ec66d77dcfc4e35bd1d2938ba9f46dde5c1ea7e |
| unit/exploration/test_exploration_strategies.py | 1357/1500 | 81bfe2b9d22dbd03fd47822c1806db1b6f5a15b1e2da47e22725d4ee6c7a68a0 |
| regressions/bac/test_rnd_service.py | 634/800 | 920627d8ad09531838bfbe2b4ec8113cd40659249761fc1393f28928c4ec37d1 |
| regressions/bac/test_icm_provider.py | 352/550 | bf36d8c2d2f45c1d3484d61e223790c97990176309d985aa5474ab81d7793317 |

Paths are under tests/test_townlet. Independent `wc -l`: 2595 total, within 3200; every individual cap respected. Production byte identity and base/tree provenance are root-custody facts, not independently rechecked by opening production files or Git. The supplied diff contains only the five allowed test paths.

Static case inventory: 2 timing + 4 normalization + 62 strategies + 55 parameter-expanded RND service + 28 parameter-expanded ICM = 151. There are 101 test definitions. The diff preserves all parameter matrices and definitions except the two explicitly mapped RND renames. This is a static inventory, not a claim of fresh pytest collection. No skip, xfail, blanket deletion, signature fallback, swallowed failure, constructor default or invented private-owner fixture appears in the migration.

## Behavior and assertion review

All original shared constructor sites explicitly transport rng=None and service_clock_unit="vector_tick", including invalid minibatch and selected-policy negatives. ICM retains its positional selected policy before keywords. The two added adaptive constructors also explicitly select shared ownership. No fixture changes model initialization or draw order beyond these documented constructor inputs; preservation of provider allocation algorithms itself is established by the sealed public contract and prior source qualification, not re-proven here.

Timing and normalization assertions retain synchronous training RMS, stable evaluation RMS, reward magnitude/variance bounds, actual warmup training, normalization checkpoint equality and downstream single weighting with unchanged tolerances. Strategies retain epsilon actions/masks/decay, target freeze, trainable/different predictor initialization, rewards, learning, public direct buffer/minibatch/tail operations, adaptive survival/variance/window/weight behavior, delegation and current native roundtrips. Manual optimizer updates remain genuine Adam calls with positive configured learning rates.

RND service retains exact FIFO order, overflow alternatives, conservation, same-tick budget and newer-empty-tick service, model updates/frozen targets, RMS separation, storage ownership, manual optimizer offsets and complete continuation equality. Deep Adam damage tables, zero-loss step accounting, frozen primitive counters, no-work observation guards, queue/model/Adam identities and RNG invariance remain. The existing purity guard against townlet.exploration.rnd.deepcopy was preserved; its compatibility with actual source requires execution.

ICM retains its independent objective calculation, detached successor target, encoder-gradient comparison, action/successor novelty, active-on-entry admission, exact tail/order and next-update equality, service/overflow selection, real module-change matrix at positive LR, selected policy refusal, typed transitions, and malformed restore unchanged-state checks. Its deterministic parameter setup is unchanged and is not presented as private RNG proof.

## Native mutations and no-legacy reconciliation

RND service line147 now writes ordinary_updates_at_position=2 on a real current snapshot; this breaches the paced budget/total-update constraints rather than merely adding an obsolete unknown field. Lines225–229 now use ordinary_updates_at_position and service_position with the preserved coupled false count changes. Both names are current native keys. The latter payload intentionally has ordinary work despite zero total updates; its Adam step relation is also inconsistent, so a generic ValueError alone does not isolate which validation branch fired. This is a pre-existing coupled-mutation limitation, not an introduced loss of coverage or unknown-old-key-only refusal. No claim of branch-specific runtime validation is made.

The direct-minibatch test at line174 preserves real 7-row/one-minibatch work and tail progression, explicitly refuses diagnostic subsets through validate/prepare/load on both live and fresh destinations with full state equality, then imports a complete current snapshot and compares exact tail and full next-update state. Current schema/version/unit assertions make the intended positive explicit. Removed load_available_state acceptance is not emulated.

The manual-history test at line388 retains both historical_updates values 0 and 3, performs actual public manual Adam work, reconciles an incomplete two-row tail, refuses diagnostic import unchanged, and imports all current counters/clock/offset/tail/model/Adam coherently. It checks replacement of destination service count2 by source count0, offset0/3, exact state, and real next-step count historical_updates+1. The former unsupported hybrid of destination counters and imported foreign optimizer is correctly removed.

Strategies line829 replaces hand-built partial adaptive acceptance with a real source and matching receiver. A differently configured destination refuses complete current state with full unchanged-state comparisons; the matching receiver separately refuses the incomplete payload, then accepts complete native state, preserves all original scalar/history expectations and compares complete nested state after actual continuation. The adjacent roundtrip now selects matching initial/minimum weight, variance/window/decay and epsilon configuration. Missing optimizer/history negatives still remove those actual required keys and expect the current ValueError contract attributed in the author report to root's source receipt.

No historical artifact DATA/provenance mutation is present in the supplied five-path diff. Comments using “legacy” for still-current direct operations are not compatibility loaders.

## Required open evidence and limits

No independent runtime execution occurred in this review. Root's prior 262 owned + 262 independent R3 results qualify their own sealed source/test selection, not these 151 migrated fixtures. Fresh collection, covering/full151 execution and independent151 execution remain separately required. Any runtime failure must be traced causally, without relabeling it as an expected constructor TypeError or weakening the current assertions.

The actual DemoRunner/native integration test remains intact at RND service line269: actual run, artifact/digest, parent payload, saved12/consumed10/update2/tail2, changed Q/counters plus deep malformed provider atomic refusal, same-runner receiving restore and fresh-runner continuation. It is not replaced by provider-only evidence. Its actual ordinary runner, population/parent key handling, reset/factory callers and fixtures are outside this inspection and unqualified by this review. No exact external caller defect is newly asserted without its source or runtime stack.

Actual nine mypy errors, RR/LIVE caller transport, private factory and RNG ownership, bank/context/identity/completion custody, POP prepared transactional native restore, runner/native full proof, and coherent whole gates remain REQUIRED OPEN. Shared None input selection does not establish private ownership. This packet does not authorize integrated PW04/BAC release.

## Independent151 execution addendum — supersedes static-only verdict

Root subsequently opened the independent runtime slot and authorized these exact orchestration commands, with all five files and source/index still frozen:

`TMPDIR=/workspace/bac-review-2026-11-01/qualification/scratch/tmp-wave08-r3 python /workspace/bac-review-2026-11-01/qualification/run_bac_packet_checks_locked.py /workspace/bac-review-2026-11-01/qualification/wave21-r0-independent-spec.json`

`python /workspace/bac-review-2026-11-01/qualification/verify_bac_run.py /workspace/bac-review-2026-11-01/qualification/wave21-r0-independent-spec.json`

Actual collection151; **131 passed, 2 failed, 18 errors in32.14s**. Locked runner measured35.887303s, reports child exit1 (wrapper itself exit0). Log: `/workspace/bac-review-2026-11-01/qualification/wave21-r0-independent/independent.log`, SHA256 `093c3d6677b43d3dcd370c2e5f1033c71ce30444e0b1d42e0f67da7655183715`. Manifest SHA256 `d45ac35155ea8ac76d7236adcad4bd1f6a1ca772601d4818f11452240cb69508`; harness SHA256 `180558c22da088a57326aa9251fbb64761e2788f18cb982532525b84b571f791`.

The verifier exits1 immediately at the assertion requiring result.exit_code==0. Therefore it supplies **no completed custody PASS** for this run. The emitted identity-controller.json records the expected base/tree, module `/workspace/hamlet/src/townlet/__init__.py`, Torch2.11.0+cu130, controller worker, threads1. That identity receipt is narrower than full custody verification. Execution session61113 completed; the verifier completed; no reviewer runtime session remains open. Root owns any further failed-run custody verification.

### Actionable findings

1. **Owned current-positive fixture configuration defect (blocking full151).** `test_exploration_strategies.py:709`, TestAdaptiveIntrinsicActionSelection.test_select_actions_delegates_to_rnd, selects epsilon_start=0.0 for the existing deterministic greedy positive but leaves epsilon_min at0.01. The actual stack reaches adaptive_intrinsic.py:87 then RND constructor rnd.py:192, which rejects epsilon_min > epsilon_start. All explicit rng/unit inputs are present, so this is a separate current configuration mismatch. Set epsilon_min=0.0 explicitly in this owned constructor to preserve the original greedy action assertions. Do not turn it into an expected refusal, relax constructor validation or change the action oracle. No fix was made while frozen.

2. **External basic_env caller prerequisite (18 setup errors).** The actual stack identifies tests/test_townlet/_fixtures/environment.py:44 calling VectorizedHamletEnv.from_universe without required keyword-only world_roster, training_seed and lane_world_ids. Eighteen checkpoint/strict-validation cases error before their owned assertions. These tests remain required; their fixture needs separately owned explicit input transport. No sixth helper source was opened; attribution is solely from the execution traceback.

3. **Actual runner prerequisite (blocking runner/native proof).** The real native integration test reaches runner.run at owned test_rnd_service.py:293, then src/townlet/demo/runner.py:410 fails at VectorizedHamletEnv.from_universe with the same three missing required inputs. The test therefore does not reach its artifact, parent atomicity or receiving continuation assertions. Repair the real caller under its separate ownership; do not replace the test with provider-only continuation or expected TypeError. Attribution comes from the runtime traceback, not a new source inspection.

Updated specification verdict: **CHANGES REQUIRED** for the owned greedy fixture configuration; full151 qualification **NOT PASS**, with18 external fixture errors and1 actual runner failure also open.

Updated quality verdict: **CHANGES REQUIRED** until that owned positive is made reachable and requalified. The rest of the static preservation/no-legacy assessment stands; no additional assertion weakening or migration defect was observed. Independent successful execution establishes131 current cases only, not151. All nine mypy errors, RR/LIVE/private-factory/bank/POP/ordinary-runner/native and coherent final gates remain REQUIRED OPEN. No integrated release is approved.
