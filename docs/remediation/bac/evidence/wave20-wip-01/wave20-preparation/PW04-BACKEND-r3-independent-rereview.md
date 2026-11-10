# PW04 backend R3 independent source rereview

Specification: PASS for the bounded producer repair, subject to pending independent fixed-source execution. Implementation quality: PASS for the reviewed repair; no new material source defect identified in this R1-to-R3 delta. Neither verdict is integrated PW04 release, a runtime result or a waiver of external obligations.

## Frozen inputs and scope

Retained original backend brief, approved ABI44c00e460cc83940c3b1a5c8a746f48ae78014c8f1539a814ea45ff5521472bd and no-defaults ruling from the earlier actual-source review. Read actual appended production report and separate PW04-R1-PRODUCTION-FIX-RECEIPT.md; their disk hashes independently match f56b235e799d2f7fb46ddf829401a76a6660574a19824a3fe53018c7d8198129 and a31ba312ccede2d72829d4297b81170e04342c476cdce121a24d85bef57d485e. Read PW04-BACKEND-r3-fix-review-package.md and inspected corresponding actual source changes plus the actual new counted tests. Previous reviewed tree82b428748d2de3f46caca601893cb3308cdbb91a to attributed fixed treeee8d22825ab3b28fd72d9e00fc7a869bbb8d4ba6.

Measured whole files before the rereview:

| File | Lines | SHA256 |
| --- | ---: | --- |
| src/townlet/exploration/rnd.py | 834 | 0848cfe8f08635fac6843d90bdf38ca7c08f92ef8220d7859e2ce65dae4ecf0d |
| src/townlet/exploration/icm.py | 481 | eb7003c15404fea5e3ce8d5779f88235b96b622b853a1c11731a300d3059c90f |
| src/townlet/exploration/adaptive_intrinsic.py | 315 | cb64d78d01c0bb8422dc664206e65588eba373a0a7ed8408634a7fa0a4b80df4 |
| tests/test_townlet/regressions/bac/test_pw_local_service.py | 1412 | 3dcc780c36c15b553272246ac605f9ca6a89cbd732f0142552fd1ee0df4f9dc7 |

Four files3042 lines, within1000/750/500/1800 individual ceilings and4050 total. Adaptive source is byte-identical to R1. No fifth implementation/helper/probe, source/test edits, runtime/imports, Git/index, branch/worktree, repository copies/deletion or subagents. This ignored review is the only write. Runtime remains closed to this reviewer until root explicitly clears its slot.

## Dispositions

| Item | Static disposition | Evidence and limits |
| --- | --- | --- |
| R1-S1 P1 bounded shared-buffer hang | Fixed in source | RND validates existing occupancy against the checked configured capacity before clock progression, counter changes or service callbacks. Both shared admission and configured update reach that check; adaptive delegates. The public direct one-minibatch update_predictor path remains available and does not inherit this bounded-admission limit. Existing overflow/FIFO algorithms are unchanged. Twelve actual counted cases cover both providers, both shared entrypoints and all three overflow policies. Callback sentinels stop causal RED before the old unbounded loop without replacing learning. |
| R1-S2 P1 Adam coercion bypass | Fixed in source | Original serialized moment fields, concrete layout/device, shape, dtype, finiteness, scalar integral nonnegative step and nonnegative variance are checked against paired off-side parameters before optimizer.load_state_dict. Complete dense coverage and common-step checks remain. Loaded state and disposable optimizer/probe parameters receive additional finiteness checks. This closes the float64/int/bool moment conversion, finite-to-infinite overflow and negative-underflow witnesses. New counted tests first establish pristine warm native validation, then exercise all three public native methods with input/live/ambient custody. |
| R1-S3 P2 optimizer ID aliases | Fixed in source | Raw state mapping keys require exact Python ints before set comparisons/loading; existing group ID validation remains. Explicit false/true and integral-float aliases are covered, including retained input key types. |
| ICM MappingProxy copy prerequisite P1 | Fixed in source | Provider __deepcopy__ uses the documented public policy to_dict/from_dict transaction, memoizes the policy and off-side backend, and deepcopies the complete attribute graph with one memo. Native prepare seeds that memo with its already validated policy. The constructor is not invoked, so this does not consume model RNG or rebuild random weights. One graph copy preserves optimizer-to-model parameter pairing; native prepare then installs its separately paired prepared models/optimizer on the off-side candidate. This hook also supports the actual OwnedWorldBackend's ordinary deepcopy use. Runtime pristine native/owned continuation is still decisive. |
| Owned fixture protocol P2 | Fixed in test | The original purity/state/RNG assertions are retained. The test explicitly asserts the old token refuses after a destination snapshot, checks state/ambient equality, then prepares a fresh token and installs without intervening owner observation. Production WS guards are unchanged. |
| Owned RND typing | Fixed in source | Constructor scalar-validation loop uses distinct scalar_name/scalar_value rather than reusing the int-inferred first-loop local. No suppression or runtime type weakening. |
| Four new structural defaults | Fixed in source | RMS array count uses int(x.size); service origins use explicit validated-unit branches; native options require a configured destination before model_dump. Both new constructor arguments remain required, with no whitelist, ratchet increase or compatibility adapter. |

All original214 cases remain alongside48 additions; no detected assertion weakening, swallowed copy prerequisite, old-signature fallback, fake optimizer or runner stub. ICM comparison cases establish a valid warm preparation outside expected-refusal assertions, so unrelated deepcopy failure cannot receive malformed-native refusal credit. The prior R1 finding severity/history remains preserved in the separate R1 review rather than rewritten as an optional concern.

## New-fix breakage assessment

The occupancy guard applies only to bounded admission and refuses from the method-entry baseline after earlier caller buffer edits. It does not silently discard queued rows or change service opportunities. Raw moment validation preserves lawful current float32 Adam moments, exact service-step/offset accounting, transported supported RND optimizer settings and off-side model/optimizer pairing. The finite disposable probe does not replace the candidate optimizer or consume its next step. Native options rejection changes no accepted unconfigured current payload, since a configured-options payload already disagreed with an unconfigured destination. ICM copying reconstructs policy through public schema rather than depending on private MappingProxy internals. No change to learning math, constructor component domains, selected unit immutability, private partition/FIFO/empty-call semantics, native schema/key sets or prepared installation was found.

No additional P1/P2/P3 source defect is asserted in the scoped repair. CPU suite coverage still does not qualify CUDA, and existing occupancy/non-unit-budget owner coverage remains useful at coherent fixed hashes without inventing extra scope.

## Attributed root evidence and pending independent execution

Root reports R3 collection262PASS; four ICM prerequisites PASS4.8203s, specifically lawful warm native, malformed moment, ID alias and owned real resume. Root reports57 covering cases PASS10.641s, comprising original nine controls plus48 material/comparison cases, with193source/573config/13artifact/1process custody PASS. Defaults nowPASS at601 with unchanged baseline/no whitelist. Owned RND mypy error is closed; nine external oracle/POP errors remain required OPEN, and untyped RR/live constructor callers remain external obligations. These are attributed results, not independent execution here.

Root's full262 run and remaining Black/CLI processes are active at this review stage. Independent full262 will run only after explicit root slot clearance, at these stationary hashes; no old R1 broad rerun is requested. Source dispositions above must be supplemented with that fresh result before independent runtime qualification is claimed.

Actual POP/current-native consumer dispatch and strict schema migration, whole-parent preparation/commit, required constructor callers, ordinary runner.run plus real save artifact/digest/load/tail/Adam/LR/clock/next-update/deep-refusal qualification remain REQUIRED OPEN. test_shared_runner_checkpoint_still_roundtrips belongs to its actual owner and cannot be replaced with producer fixtures. This is a bounded producer rereview, not PW04/BAC release; original66packets/28releases remain unchanged.

## Independent fixed-source execution and closure

After root explicitly cleared a1CPU independent slot, executed exactly the authorized orchestration command:

`TMPDIR=/workspace/bac-review-2026-11-01/qualification/scratch/tmp-wave08-r3 python /workspace/bac-review-2026-11-01/qualification/run_bac_packet_checks_locked.py /workspace/bac-review-2026-11-01/qualification/wave20-r3-independent-spec.json`

The execution session23463 closed with exit0; independent wall20.913580179214478s. Then executed the exact verifier:

`python /workspace/bac-review-2026-11-01/qualification/verify_bac_run.py /workspace/bac-review-2026-11-01/qualification/wave20-r3-independent-spec.json`

Verifier exit0:262PASS,0skipped,0xfailed,0xpassed,0warnings. Candidate treeee8d22825ab3b28fd72d9e00fc7a869bbb8d4ba6, base64748bdf0b623c66bdc400238d4c17645bd6fba7. Custody PASS:193source guards,573config digests,13protected artifacts,1process identity,14worktree registry records/1available; source/index/import/thread/fixture custody PASS. The independent orchestration session and verifier are both closed; this reviewer leaves no running runtime session. No helper implementation was read as a fifth source.

Independent log: /workspace/bac-review-2026-11-01/qualification/wave20-r3-independent/independent.log SHA25670f1bb33b78cb7b7870d4cefe450869123490563b08b7285f8dedab284ba7c26. Manifest SHA256fa81768e9a5dde360b1c39e77cd9f3da572a0630666d50b74e304fd988e1d30e; harness SHA256180558c22da088a57326aa9251fbb64761e2788f18cb982532525b84b571f791.

The bounded producer source specification/quality PASS now has independent full262 CPU runtime evidence. R1-S1/S2/S3, ICM copy prerequisite and Owned fixture protocol are closed for this repaired candidate under the tested contracts. Root separately reports its full262PASS/0warnings28.4517s and covering/prerequisite results; those remain attributed corroboration. External nine mypy errors, untyped RR/live required constructor callers, current POP/native strict schema/dispatch and whole-parent prepared commit, actual ordinary runner/native artifact/load/next-real-update/deep-refusal and remaining coherent gates stay REQUIRED OPEN. This execution is neither integrated PW04 release nor whole-BAC completion, and does not qualify CUDA.
