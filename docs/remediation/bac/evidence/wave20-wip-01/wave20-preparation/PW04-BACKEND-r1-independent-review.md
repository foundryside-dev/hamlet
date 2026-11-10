# PW04 backend R1 independent actual-source review

Verdicts: specification FAIL; implementation quality FAIL pending the material defects below and fresh execution at the repaired hashes. This is an independent static source review, not a runtime result or PW04 release. The approved design is implemented substantially, including genuine learning and explicit required constructor inputs, but the current source does not yet provide the promised complete input/native refusal boundary.

## Frozen evidence and scope

Read the backend brief first; followed root's later actual-source review authorization. Accepted ABI proposal SHA256 44c00e460cc83940c3b1a5c8a746f48ae78014c8f1539a814ea45ff5521472bd and production report SHA256 b8cbcb93264337589f6d7c6531fc38485fcadd337e998c148d27c810dc1b46e9 independently matched disk. Read PW04-NO-DEFAULTS-RULING.md, actual PW04-BACKEND-r1-review-package.md, approved proposal and actual production report. Clock/RNG/context behavior is taken from published receipts and the test's actual API uses, not a fifth implementation source. Base/tree are attributed root custody: 64748bdf0b623c66bdc400238d4c17645bd6fba7 / 82b428748d2de3f46caca601893cb3308cdbb91a.

Measured before reading the exact four whole implementation/test files:

| File | Lines | SHA256 |
| --- | ---: | --- |
| src/townlet/exploration/rnd.py | 814 | a6d7f5c152f3f00d36f818f9309425ce39655c5098b74e151e1a43bfabe6f0a2 |
| src/townlet/exploration/icm.py | 468 | 55dec9e755f426c156e8cadadbfeb8d7f234d87a2866f597cdf3dd4ef1e44eed |
| src/townlet/exploration/adaptive_intrinsic.py | 315 | cb64d78d01c0bb8422dc664206e65588eba373a0a7ed8408634a7fa0a4b80df4 |
| tests/test_townlet/regressions/bac/test_pw_local_service.py | 1289 | 1242032018ff554700ad789c252f0717acfcefab690b4db089a9d02c6c84daa4 |

Actual 4/2886, within individual 1000/750/500/1500 and total3750 ceilings. No fifth implementation/helper/probe, imports, runtime, Git/index operations, source/test changes, branch/worktree/copy/deletion or subagents. This ignored review is the sole write. Independent execution remains pending root's explicit runtime-slot clearance. Attributed root R0 18 positive fixtures and 195FAIL/19PASS, R1 collection214/current fixtures18PASS and custody are retained as prior evidence; they are not this reviewer's execution.

## Material findings

### R1-S1 — P1: bounded RND admission can loop forever on its supported public shared buffer

Locations: rnd.py:327-331, 389-405, 435-462; adaptive delegates the same paths.

The call preflight validates every buffered row but never checks buffered occupancy against configured capacity. The loop handles only room==0, not room<0. Concrete case: explicit shared provider, B2/capacity4/paced cap1; externally append eight valid finite observation rows to public obs_buffer, then submit one valid row at a fresh vector tick. The first real update consumes two rows and reconciles admissions, leaving six buffered rows and exhausted ordinary pacing. room becomes -2. count=min(room, remaining) is -2, the input slice is empty, offset becomes -2 and admissions decrease. Each following iteration repeats without consuming, appending or dropping anything: the call does not terminate. The same issue is reachable after supported public update_predictor leaves an oversized tail, or through configured shared update delegation.

This violates full preflight before callbacks/mutation, bounded capacity and the explicitly adopted loop-progress/conservation requirements. It is not a late numerical/model failure and must not be parked as an optional extension. Before bounded admission, either refuse an over-capacity existing buffer unchanged or implement an explicitly reviewed finite treatment consistent with preserved direct-buffer semantics. Preserve legitimate public one-minibatch update_predictor behavior; do not solve this by removing substantive shared direct training.

Required regression within the counted test: RND and adaptive, all three overflow policies, valid over-capacity external buffer, both admit_and_service and configured update. Assert refusal before any forward/Adam callback, unchanged method-entry buffer/counters/clock/parameters/Adam/RMS and ambient RNG. Use a bounded isolated root-orchestrated timeout for the initial causal witness so the known hang cannot monopolize a runtime slot. No extra probe file.

### R1-S2 — P1: Adam loader coercion bypasses native dtype and finiteness validation

Locations: rnd.py:630, 659-691, 696-704; adaptive nested restore inherits this.

RND checks raw payload finiteness, then passes the payload to optimizer.load_state_dict at667. Adam casts moment tensors to destination parameter dtype. The promised moment dtype check occurs only afterward at688, and no post-cast finiteness validation runs. A warm payload with one exp_avg changed to a same-shape finite float64 tensor filled with1e300 passes raw finiteness, casts to float32 infinity, and then passes the shape/dtype check. The disposable optimizer.step probe only checks exceptions; it never checks the resulting moments/parameters. Adam can execute with inf/NaN without throwing, so that probe does not close this hole. Installing the returned candidate can put nonfinite Adam state into the live backend, and the next genuine optimizer update can poison parameters. A wrong-dtype moment with ordinary finite values is also silently normalized rather than refused; a tiny negative float64 second moment can round to negative zero before the nonnegative check.

Validate the raw serialized moment geometry/dtype/finiteness/nonnegativity before invoking any coercing loader. Retain complete parameter coverage/common step/group validation and the paired off-side optimizer. Optionally also verify the loaded candidate/probe finite state as defense against conversion effects; that does not replace raw validation. ICM already validates raw moments against actual prepared parameters before its loader.

Required regressions inside the counted test for warm RND and adaptive: float64/integer/bool exp_avg or exp_avg_sq; finite float64 exp_avg1e300; tiny negative float64 exp_avg_sq. Each validate_state, prepare_state and load_state must refuse unchanged, with ambient/input custody. Include a lawful float32 warm continuation positive control. These requests follow the accepted complete native dtype/nonnegative/finiteness contract, not a newly invented schema.

### R1-S3 — P2: RND optimizer state IDs accept bool/float aliases

Locations: rnd.py:660-667; compare ICM's explicit exact key-type check at335.

RND validates parameter IDs in param_groups as exact ints, but optimizer state mapping IDs only by set subset/equality. Python treats False as0, True as1 and integral floats as equal to the corresponding integer keys. Replacing a warm native state mapping key0 withFalse or0.0 therefore passes both membership/coverage checks and is mapped by Adam to the same live parameter. A malformed current native payload is accepted instead of refused, contrary to exact identity/type validation; snapshotting after restore normalizes it and loses supplied type information.

Require exact Python int keys in the raw optimizer state mapping before set comparisons/loading. Add RND/adaptive bool and float state-key refusal cases to validate/prepare/load in the counted test; retain an exact-int warm positive control. No compatibility normalization.

## Specification assessment of the remaining implementation

Source supports the required explicit rng/unit inputs without new defaults, read-only selected unit, actual target/predictor/model_init constructor contexts and adaptive delegation. The original RND model/loss/Adam update and ICM encoder/inverse/forward math remain substantive. Shared grouped pacing is separate from private consecutive per-admission events; private empty calls skip service entirely, while shared newer empty calls retain service capability. Clock position/type/unit/progression preflight is explicit; ICM retains lane order, active selection and context metadata matching in shared mode. Provider-specific overflow order remains visible, not replaced by a generic mock engine.

Native schemas are current-only with exact outer key sets; off-side candidate creation avoids random model reconstruction, retains optimizer/model parameter pairing, owns tails/history/RMS/tensors, and validates adaptive outer state before nested loading on an off-side object. Installation checks destination and consumption before one attribute-dictionary swap. These are good structural properties, but R1-S2/S3 prevent complete native-validation acceptance. R1-S1 prevents the full-buffer preflight and loop-progress acceptance.

The nine original defect controls remain in the actual test. The constructor fixture delta is explicit input transport, with no detected runtime signature fallback, swallowed errors, fake training engine or runner stub. Full learning traces inspect real forwards and real Adam pre-hooks. Private partition/idle tests, shared RND overflow and imported-tail ICM overflow are correctly distinguished; zero naturally reachable private RND overflow at B2/cap4/cap1 is not misreported as missing drop coverage.

## Quality assessment and required execution

Quality FAIL is driven by the concrete hang and validation-after-coercion mistakes, not style. No separate P3 defect is asserted. The214-case suite is useful but currently omits over-capacity valid public buffers and raw Adam moment dtype/state-ID cases, which explains why these source defects may survive its current matrix. Additional root-owned existing-suite coverage should exercise occupancy service and non-unit budgets at the same source hashes; the new test fixture uses paced_fifo/cap1 throughout. This is a coverage request, not a claim of an additional implementation defect.

Do not count a future214PASS as closing R1-S1/S2/S3 without the new adversarial witnesses. Preserve every original214 case/assertion and all nine original causal defects; additions remain within the counted1500-line test ceiling or require root reslice before growth. Independent runtime will be performed only after root clears the process slot. CUDA behavior remains unqualified by CPU-only evidence.

Actual POP/native dispatch/current strict schemas, enclosing atomic preparation/commit, required-constructor external callers and actual ordinary runner/native save/load/tail/Adam/LR/clock/next-update/deep-refusal qualification remain REQUIRED OPEN. test_shared_runner_checkpoint_still_roundtrips belongs to that actual integration owner and must not be stubbed or substituted. This producer review neither waives those obligations nor changes the original66packets/28releases.

## Root R1 execution and gate receipt, appended after static review

The following facts are attributed to root's fresh wave20/r1-postflight.json receipt, not independent execution by this reviewer. Root reports the nine original causal controls PASS in6.1148s; full R1 is21FAIL/193PASS in16.2809s. Nineteen failures arise from ICM prepare_state's deepcopy(self) encountering a MappingProxyType in the actual resolved policy. Two RND/adaptive Owned fixtures call snapshot after prepare, which correctly stales the prepared ownership token under the actual public protocol. Root reports all193source/573configs/13artifacts/3process custody PASS and all runtime CLOSED. CLI128.9665s PASS; scoped Ruff/Black expression checks PASS. No old214 rerun is independently performed before prerequisite repairs.

ICM copy prerequisite is a material P1 implementation defect: icm.py:453 unconditionally deep-copies the entire backend after state preparation, including the actual immutable resolved policy. The resulting TypeError prevents valid native preparation, validation and load, and blocks the promised native continuation. Fix off-side candidate ownership using the actual public policy.to_dict/from_dict API and a correctly scoped deepcopy memo or equivalent policy-aware copy; maintain independent mutable state and model/optimizer pairing. No WS/RP fifth-source read is needed. A valid warmed ICM snapshot must validate, prepare/install and continue learning; malformed-native refusal must then reach its intended semantic boundary instead of receiving unrelated copy-prerequisite credit. Adaptive/RND direct native controls remain separate evidence.

Owned fixture protocol is a P2 test defect, not a production WS defect: the tests at the owned restore/continuation boundaries take an intervening destination snapshot after preparation. That snapshot legitimately invalidates the prepared token. Preserve and explicitly assert the stale-token refusal after an intervening snapshot, then perform a fresh prepare followed by install without another token-invalidating operation. Do not weaken production WS ownership/epoch guards or add compatibility inference to pass the fixture.

Root also reports the defaults gate605>601, with new RND84/228/736 and ICM121 structural ternaries counted as defaults. This is a required producer gate defect, not permission to raise the baseline or create a waiver. Root reports mypy10errors/3files: owned RND line183 reuses an int-inferred local for float-valued constructor validation, plus seven prior external caller errors and two POP missing-required-new-argument errors. Repair the owned RND typing defect; migrate actual external constructor callers under their bounded owners. Untyped RR/live caller paths also remain required external migrations rather than assumed compatibility. These root gate results do not change the requirement that both new constructor inputs have no defaults.

Root authorized the same original Astra author for TESTS ONLY: add causal witnesses for R1-S1/S2/S3 and repair the Owned fixture protocol. New counted test ceiling1800 and exact four-file total4050 replace the prior1500/3750 test/total ceilings; individual provider ceilings remain unchanged. No extra helper/probe/source is authorized. All three independent static findings remain OPEN pending causal execution, repaired frozen source, same Sol re-review and independent actual execution. ICM copy, Owned protocol, defaults/typing gates and actual POP/runner/native/external-caller obligations are additionally required closures; none are optional extensions.
