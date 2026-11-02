# T16 tests-first authoring — execution pending, stationary

Authored only `tests/test_townlet/regressions/bac/test_runner_readiness.py` in the existing `/workspace/hamlet`, plus this requested ignored receipt. Entry/current HEAD is `f575ecefda7844fbd5b7b6138ad0c6bf7b1bafd8`. Root reports T15 source qualification at `ae0914afb3e7e1ca525e91acd49a07b3ae54c327`, tree `f71c52fa`, with6845PASS/16SKIP, six guards and six genuine clean native captures/independent postflight PASS; later documentation/evidence is committed/pushed at the current HEAD with exact remote verification. Those results and ongoing remote CI checks are root-attributed, not executed or independently requalified by this author.

Root explicitly cleared **tests-first authoring only**, after T15 qualification. No production edit, project import, runtime, pytest, collection, compiler or linter is cleared in this turn. Root must observe meaningful causal RED before production authoring. The test-driven-development skill and its writing-good-tests reference were read; its runtime steps remain pending under that explicit ownership boundary.

## Exact complete source context

Exactly five complete implementation/test files are charged, **4401 physical lines**. All four production hashes remain unchanged from readiness. No sixth implementation/helper/config/environment/sampler/network/conftest/existing test was opened. The existing source-verified serialization/API prose was reused without following its implementation links.

| Complete file | Actual lines | SHA256 | Effective projected ceiling/access |
|---|---:|---|---|
| RR `src/townlet/demo/runner.py` |1001|`94842641bdce645fdd90d188d5bbdf6e09e7f4c071d15756202e173acd47c15d`|1200 / no edit in this turn|
| POP `src/townlet/population/vectorized.py` |2146|`9569eab3d766ed5467ecf78736cd170c7aa0d0b77d90efe28239f3bab64ff12a`|2200 / no edit in this turn|
| BC `src/townlet/config/brain_config.py` |568|`6c041ed40de507dfed81dc4b3a58cbb728d446228f6fd831ee115348aa559079`|600 / read only|
| OF `src/townlet/agent/optimizer_factory.py` |162|`56af1a9c8edb70a25b43a6e10aa3080d9a7b8becff112924e21a9429d994717d`|200 / read only|
| Owned `tests/test_townlet/regressions/bac/test_runner_readiness.py` |524|`cca659ad5a85e6c13f3d0f7a07bc2fb64e5294bb09dea6c2b2e11d418677f90b`|700 / newly created|

Complete projection remains **5/4900**, leaving100 below5000; actual context4401 leaves599 actual physical lines. No reservation, task/lens/acceptance or frozen-plan change was made. No source-copy/new checkout/worktree/branch/deletion or subdelegation occurred; all14 existing checkouts are preserved. No index/commit/push/tracker operation occurred. Fresh tracked status shows only the new untracked owned test; `git diff --stat` reports no tracked edit. This destination matches `.git/info/exclude:7` `/.superpowers/`.

## Genuine runtime path and observers

Each future case runs the actual `DemoRunner.run()` context manager with a private authored pack, database and checkpoints. The in-file fixture copies **only `*.yaml` DATA** from the existing selected family into pytest tmp_path, then authors the verified flat brain and outer-training mapping before the real declaration resolver/compiler runs. Canonical packs stay unchanged. No fake universe/environment/network/replay/optimizer, manual buffer attachment, synthetic transition, mask replacement, loss replacement, forced action or warmup bypass exists in this test.

Pass-through observers call the original methods once, preserving their side effects:

- Actual runner checkpoint-load boundary (fresh fixture requires no checkpoint) captures the already-created public replay serialization, selected brain, initial weights/scheduler/LR and complete effective provenance. This exposes eager selected policy without testing a factory spelling.
- Actual population step and scheduled `_learn` capture real vector ticks, retained counts, actual request/readiness and successful-update counters. Retained warmup is independent of pending episode rows.
- Actual backend `sample_batch` records real receipt mode/weights/lengths/stable IDs/recorded bits and sampled objective rewards. It returns the original batch unchanged and remains observable when lazy binding replaces a pristine buffer with another instance of the same actual backend class.
- Actual Q optimizer, scheduler and target-load calls record their ticks; optimizer observations check actual parameter change plus finite model/optimizer state. Their original methods execute unchanged. The first actual Q update must see untouched initial online/target weights.
- Actual configured `_loss_values` records the already-calculated learner targets and returns the real configured loss. Gamma0 assertions compare those actual targets to the corresponding real sampled objective rewards, with exact zero tolerances.

No project import or runtime has been performed to prove these future fixture/observer paths yet. Unexpected API/setup/collection errors are prerequisite failures and cannot be called causal RED.

## Authored finite controls —12 expected parameterized cases

| Test | Actual contract and independent expectation |
|---|---|
| `test_real_runner_owned_sampling_identity`, both PER laws | A genuine feedforward-PER runner performs real finite sampled updates before checking construction-time public sampler identity: owned NumPy Generator/PCG64/authored, initial state exactly explicit PCG64(42), selected law in actual receipts, and genuine sampler state advancement. The omitted priority_reduction resolves to max_abs while authored omission/provenance remain intact. Actual vector pacing uses executed episode override×cap, independent of transition budget; named origin must retain launch episode source and the absolute training declaration origin/cap field. |
| `test_real_runner_warmup1000`, feedforward and recurrent PER | N1/min1000/B2/cap2 with1004 actual live transitions and enough declared/executed episodes. After exactly2 retained rows Q updates remain0. Every scheduled opportunity below retained1000 reports warmup with zero Q updates; first scheduled/sampleable opportunity after retained>=1000 advances exactly0→1 and changes real finite weights/state. Recurrent first update occurs after tick1000 because uncommitted current rows do not count. The separate replay beta vector clock advances through all1004 ticks. |
| `test_real_runner_recurrent_per`, both PER laws | Real authored recurrent/prioritized brain, adaptive-prefix L3/B3/min2/cap16 rolls out and learns. Actual samples have real lengths1–2 and selected-law receipts. Before rollout its public serialization must already be captured7 with all six resolved leaves, genuine selected priority state, authored PCG64 seed and horizon26/fresh tick0. Replacement can actually sample B3 from sampleable2; successive reports batch_unavailable at that support, then learns when eligible. |
| `test_real_runner_family_cadence_and_zero_gamma`, four authored families | Feedforward uniform, dueling PER, token_set PER and recurrent PER preserve their true selected architecture/policy. Independent min4, B1, frequency3 and target2 yield scheduled opportunities3/6/9/12/15 and successful Q updates6/9/12/15. Actual scheduler calls match successful ticks, actual target copies are(9,2)/(15,4), and StepLR LR values are literal0.001/0.0005/0.0005/0.00025. Canonical gamma0 yields actual sampled-reward targets, while effective LR0.001/cap32/target2 override the authored base values. |
| `test_real_runner_window_diagnostic`, fixed_full and adaptive_prefix | Recurrent PER cap1/L8/min1/transition_tail/anchor. Fixed_full keeps actual retained1/sampleable0, reports capacity_window_impossible once for unchanged counts, performs zero Q optimizer/scheduler/target/sample work, and preserves exact weights/scheduler/empty optimizer state. Adaptive-prefix uses actual length1 samples and real finite optimization. Both advance the independent beta clock through all8 vector ticks. |

The AST contains five test functions and99 assertions. Parameterized-case count12 is derived from the authored decorators, **not a collection result**. No assertion, law, family, declared1000 warmup or first-real-update requirement was lowered to obtain a pass. All four authored architecture families and both actual recurrent PER laws remain present. Existing configured scalar/gamma/clock behavior is intentionally observed as regression acceptance, rather than falsely claimed as a newly missing behavior.

## Intended narrow causal RED and honest existing behavior

The source-proven missing behavior is the explicit runner sampling identity/eager resolved policy. Current RR uses ordinary construction; ordinary successive flat PER intentionally retains the external global-NumPy owner, and current recurrent construction starts with unconfigured inspection transport until its first learning entry. Accordingly the intended narrow causal cases, after actual prerequisite/import/collection verification, are:

```text
tests/test_townlet/regressions/bac/test_runner_readiness.py::test_real_runner_owned_sampling_identity[successive_without_replacement]
tests/test_townlet/regressions/bac/test_runner_readiness.py::test_real_runner_recurrent_per[independent_with_replacement]
```

These are expected IDs for root to verify by actual collection. The first intended failure is public sampler ownership; the second is pre-rollout public captured7 selected policy. Both execute genuine sampled optimization before those assertions. Adding a factory call that fails to install/use the real selected owned policy cannot satisfy their actual replay/network/optimizer assertions. The origin/clock/provenance checks supplement those behavior observations and do not assert a method name or call count at a factory seam.

Warmup1000, after-binding recurrent PER, gamma0 and successful-update LR/target cadence are already implemented by the qualified T15 compiled adapter. Their expected prepatch PASS is an honest regression control, not RED evidence. Current factory/adapter source establishes that distinction; root still owns their actual execution. The first private ownership check can prevent later origin assertions from being reached, so root should report reached boundaries precisely instead of claiming every assertion was independently observed.

## Static verification, limits and next ownership

The only executed validation was standard-library AST parsing of this new test. It succeeds; a standard-library physical-line check found no line over140 characters. No project/module import, fixture execution, pytest/collection, compiler, linter, Black/Ruff, runtime guard or gate was run. Therefore there is **no observed RED/GREEN, fixture validity, formatter/linter or learning-PASS claim**. Production source remains untouched. Root must collect/verify source/import/fixture custody, run exact narrow causal RED, resolve only observed prerequisite faults, then decide authoring clearance; no production implementation follows automatically from this receipt.

The actual existing shared AdaptiveIntrinsic/RND construction and predictor service remain active. Q warmup checks count only real learner Q optimizer updates, not RND optimizer activity. Curiosity scope is the existing shared runner arrangement, origin its manual selected-training Adaptive construction, world binding one population module/N1 fixtures, guarantee limited to runner replay policy/readiness/clocks. No private curiosity/provider isolation or precedence repair is claimed. Local clocks remain retained eligible transitions for warmup, vector ticks for beta, successful Q updates for LR/target. Fixed-full limitations are diagnosed, while additive adaptive-prefix stays selectable. Historical Option A/current captured replay preservation and strict per-world B/shared alternative owners are unchanged.

Root owns the eventual actual patch's earlier-full-trigger assessment under BAC-CADENCE-A-2026-11-01, six guards, affected owner selection, fresh independent review, G2/full qualification and remote CI/publication. Focused tests cannot declare repository green. Full-suite status for this T16 test-only state is **NOT RUN**, next full gate G2 unless an actual earlier trigger/uncertainty requires full. Return stationary; no project/runtime/source action until root's next explicit clearance.
