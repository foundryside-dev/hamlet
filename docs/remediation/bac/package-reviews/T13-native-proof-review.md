# Review provenance

Final scoped source/spec review at tested tree `f88f7cb3e3d0203ab199a2d898e3b0f8370d7e48`, identical to qualified source `495360d68c167b741d8ed5016c0921f995aac1f4`. Coordinator runtime is attributed; this artifact does not assert independent runtime unless its body does.

Original `T13-native-proof-independent-review-r4.md`, SHA256 `749603652a6dbaa2963936711c783c453c08212347f5334e7173b85444f10763`, retained unchanged; portable rendering normalizes execution paths.

# T13 native proof — fresh independent static review R4

Scoped verdict: APPROVE the bounded C01 authored-reachability witness and its current fixed-source integration. No new P1/P2 defect or material evidentiary gap found against that bounded claim. This is static review plus independent reading of root-executed historical logs, not reviewer execution or fresh R4 runtime qualification. X04 remains a required OPEN P1 owned by T15. Root retains core, owner, runtime, full-gate and whole-BAC final qualification.

## Identity and complete scope

HEAD independently read: `41edeb0858cba98a8dcb6ba2af36355457ef4e0a`. Candidate manifest: `.superpowers/sdd/2026-11-01-bac-remediation-upgrades/wave07/green-r4-candidate.json`; tree `f88f7cb3e3d0203ab199a2d898e3b0f8370d7e48`. Read exactly these five WHOLE implementation/test files, 4364 lines total; no sixth helper, runner, compiler, environment, sampler or test source was opened. Working bytes match these hashes and the supplied manifest; read-only cached diff against the candidate tree is empty. Index SHA256 at review/postflight: `bb01f53d99128a2bbde6854b45280e1461f87e123b1c78457f3d9c6443f5afc3`.

| File | Lines | SHA256 |
|---|---:|---|
| src/townlet/population/vectorized.py | 1854 | 38d8c969a8acfc5f49a3c5c7e532f6f10b34844af12ca37e8696123511e47d3b |
| src/townlet/training/prioritized_replay_buffer.py | 1092 | 290eadca0305658abdd4aec361a9b167ac63d7a887438b602c19c2eaf9020de9 |
| src/townlet/config/bac_options.py | 294 | 10dc3ef7dc288d954147046c95bc8362df2162f3829986be26b2724e86dd4916 |
| tests/test_townlet/integration/test_compact_token_acceptance.py | 854 | 5c2369f2303b417b1b6021e13444db93f2c47827b074c57f6ccbc68f376adb23 |
| tests/test_townlet/regressions/bac/test_per_native_learner.py | 270 | 6348f247dc9b5060a650f87fe8bee1d9c18ece46a868c40b6021f0360c19da16 |

Read repository guidance, STATUS severity bar, effective T13 brief and accepted P3 prose, C01-authored-reachability-r1.md and MEAN-TD-TRIAGE.md. Using-superpowers expressly exempts dispatched subagents; verification-before-completion was consulted and applied by limiting claims to verified static/hash observations and attributed execution. Specific stationary read-only dispatch governs over generic worktree/runtime workflow; preservation/approved History A governs over blanket deletion guidance. No durable user-only fallback was saved/adopted; failed rule grants/restricts nothing. No worktree/branch/project copy, deletion, source/test mutation, import, pytest/runtime, staging, commit, write-tree or subdelegation occurred. Only this ignored prose report was written.

## Why the witness establishes the bounded claim

Native test lines35–73 copy YAML DATA, edit authored brain/training/drive declarations, hash the pack, and let the public DemoRunner constructor admit it. Lines216–268 consume runner.compiled through VectorizedHamletEnv.from_universe, real build_curriculum/initialize_population, ordinary EpsilonGreedy and VectorizedPopulation, then reset and call step_population exactly twice. This is public component assembly after DemoRunner admission, not DemoRunner.run or CLI end-to-end execution. The explicit EpsilonGreedy(.5,.99,.1) is a real supported exploration object but differs from the training YAML's epsilon values; the receipt correctly identifies this harness setting. Assignment of the runtime objects onto runner is attachment, not TD/priority/counter/network injection. Compiler/environment internals are outside the five-file scope; executed admission and the public call sites substantiate their use.

Population construction builds the real networks, target copy, optimizer/loss and ordinary PER (vectorized.py:206–289). step_population computes real Q/action masks, curriculum decisions and env.step; stores eligible real rewards and transitions; calls PER.sample at984, computes TD/loss at992–1024, performs backward/clipping/optimizer.step at1035–1038, and updates priorities at1045–1047. The witness never calls a private sampling/TD/priority setter. Its exception handler annotates and rethrows; no xfail, skip or swallowed fallback turns the causal crash into success.

The admitted setting is feedforward256/128 ReLU/dropout0, Adam lr.0001/betas.9,.999/eps1e-8/weight-decay0, Huber delta.25, gamma0 in both declarations and effective brain, Double DQN, target interval1000, two CPU lanes, replay capacity=batch=min_size2, train frequency1, sequence1, beta1 without annealing, gradient clip10, cap20, static curriculum. Seed731 is set temporarily for NumPy/torch; the training declaration seed42 is reported separately. Drive base2e38, no bonuses/modifiers, no normalization/clipping produces the tested finite reward. Modest base1/alpha1 and high base2e38/alpha0 are matched controls. bac_options is null, so this qualifies the existing global-NumPy physical-slot adapter, not configured owned-generator sampling.

Native lines93–177 check live finite predecessor observations, nontrivial bounded pre-Q, actual selected-action legality, exact pre-Q correspondence with returned producer Q, finite loss and parameters, parameter change, nonempty finite Adam state with actual step1/2, changed forward values, and exact replay observation/action/reward/done/component alignment. Gamma0 permits the independent float64 pre-update TD oracle without trusting bootstrap correctness. Priorities must match TD+epsilon within tolerance and exceed the float32-sum boundary in aggregate. These checks defeat an implementation that merely increments training counters or logs fabricated successful loss.

A useful causal detail: capacity2 is completely overwritten by the next two real transitions before the second sample. Their insertion priority is inherited from the actual first-update max_priority. Thus tick2 proves large learner-produced priority propagation into the next ordinary sample; it does not prove replaying the original tick1 rows. This is sufficient for the reported normalization defect and does not rely on private injection.

Current PB.sample converts live priorities to float64 and calls the supplied shared sampler contract, returns float32 weights and writable int64 physical indices, and preserves the existing learner call path. Its small-buffer guard only restores the original diagnostic; it cannot bypass the full-size native sample. Atomic priority conversion retains the finite large values. Given the explicitly supplied PS contract, no local fallback/skip or clamp explains GREEN. PS mathematics/internal proof remains the separate core review's responsibility. OP's default successive law agrees with P3, but this witness does not test option-resolution wiring.

## Attributed execution and numeric receipts

Independently read the complete raw logs below, plus the R2 result JSON. Root executed these; this reviewer ran no tests.

| Evidence under qualification | SHA256 | Observed result |
|---|---|---|
| wave07-red-r1-narrow/native-alpha0-control.log | ed145846f07341d21d07e78b57babecf172e9acaf63b4e23674d213d95593558 | 1 passed, two updates |
| wave07-red-r1-narrow/native-alpha1-causal.log | 0a16aa91fbf9c855ddc3133451209fc7e61a4860cbd27cdde49f63c71b70650a | 1 failed, tick2 probability-normalization crash |
| wave07-green-r2/native-green.log | b55277ded982906d76682e0d1909032e7227b1a490c4cd0b3f5ba4efb4051d3d | 3 passed, two updates each |

R1 causal binding is `2cfb5360ae46aa67fc2506743b469f257696c324` per the reachability receipt. R2 GREEN result explicitly binds tree `e29a9cba67f98960efd29013a284d86997ef2ab5`, manifest SHA256 `5921b10fd6c89d40edbadb189cc99eb43f47f7d73241b14436e515f084b76e90`, common HEAD above. Its command is `.venv/bin/python -m pytest tests/test_townlet/regressions/bac/test_per_native_learner.py -s -q --no-cov -p no:cacheprovider -p bac_source_identity`, exit0. This historical R2 execution is not relabeled as R4 execution.

R1 alpha1 first update has finite per-row reward/TD/priority `1.9999999360571385e38`, sum `3.999999872114277e38`, Huber loss `4.999999840142846e37`, six changed parameter tensors, Adam step1, initial Q maximum `.13513588905334473`, parameter maxima `.09205705672502518`→`.0921388790011406`. Tick2 emits overflow encountered in reduce and raises probabilities-do-not-sum-to1 from ordinary POP984→old PB352/345→NumPy choice, with exactly one completed update. Alpha0 reaches step2 with finite moments/parameters and max `.0922064557671547`; no warning. R2 high alpha1 reaches that same second finite update, with no warnings. R2 modest losses are `.2005024403333664` and `.19476845860481262`; both steps change six tensors and Adam counters advance1/2. All three authored YAML digests match those recorded in C01-authored-reachability-r1.md.

The printed float64 probabilities are an independent oracle over serialized post-update priorities, not a captured sampler receipt and not the second conditional probability of a without-replacement tuple. The label is truthful in that limited sense. This witness therefore cannot replace core ordered-law/estimator tests. In particular B=N=2 gives all-one full-population weights and cannot discriminate all unequal-priority estimator failures. It can and does discriminate the observed numerical normalization crash.

## Defects, limits and optional observations

**Existing required P1 X04 remains OPEN:** vectorized.py:1029 computes the float32 mean before .item(), yielding infinity for these two finite residuals whose true mean is `1.9999999360571385e38`; get_training_metrics publishes it at1137. The native test records it as a string at180 without asserting finite correctness. Both high controls and GREEN expose it. Finite optimizer evidence refutes conflating this telemetry overflow with optimizer divergence. T15 owns producer repair and required finite-mean acceptance; T35 consumes its verified result. This approval does not pass, waive or close that requirement.

No new P1/P2 found in the bounded witness. Historical API-only B04/C01 classification remains an accurate historical assessment; this new authored evidence promotes current reachability only. The compact acceptance source has independent current6 roundtrip, mixed-tag5/4 refusal with input/live purity, genuine old4 archive preservation, and original Buffer size refusal checks. Those synthetic transport checks do not establish native C07 or native resume.

Optional P3: a future receipt could call the logged probability field explicitly first-draw/post-update oracle probability to reduce possible misreading. Current source/receipt context is sufficient; this is nonblocking and no scope expansion is requested. Warnings are recorded rather than asserted empty; the reviewed logs are actually empty on GREEN, so this does not weaken the present bounded claim.

Proof limits: no DemoRunner.run/CLI orchestration claim; no gamma>0 legal-target qualification (bootstrap remains unmasked), recurrent or recurrent-PER witness, replacement-mode/owned-RNG wiring, exact stochastic continuation, long-run learning quality, world-isolation, GPU, native checkpoint continuation, full native C07, or whole-BAC completion. Core mathematics and fresh exact R4 execution/gates remain root-owned. STATIONARY after source/index postflight.
