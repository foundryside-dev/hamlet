# Evidence provenance

Original coordinator execution receipt SHA256 `c6aa573650fdcaa88fc99d6b4d2ac5a3254eb0a2f2a1e11d6187cc712d305ecb`; historical pre-fix identities remain historical. Fixed-source verification is recorded separately in the final implementation receipt.

# C01 — actual bounded authored reachability, root execution R1

2026-11-01. Root's completed runs establish new authored reachability of C01 under
the exact settings below: one real finite optimizer update, then a second ordinary
public learner sample failing at float32 priority normalization. Historical B04
was API-only evidence at that time; this result does not retrospectively promote
it. This receipt consolidates root logs/results as DATA and existing prose only.
The author ran no imports, runtime, tests or probes and read/edited no current
source/test implementation. PB/PS/HC production is changing under its separate
owner; no global stationary identity or current production success is asserted.

## Frozen execution identity and commands

R1 diagnostic candidate `2cfb5360ae46aa67fc2506743b469f257696c324`, base HEAD
`41edeb0858cba98a8dcb6ba2af36355457ef4e0a`, manifest
`wave07/red-r1-candidate.json` SHA256
`41aaa507885fa7839dfdb7f8e82d9045af2423a1266cedf223084efc4919dd55`.
The modest control ran at R0 candidate `0e446b995aa612a73438f610310139997cbe5680`,
same base, manifest SHA256
`3184f3c63b977221b8924b37f649ad3320bb79d52068eda10ac433ac4ca94244`.
Root reports the native witness/POP/OP/compact bytes unchanged across these runs.
These are historical execution bindings, not hashes of the changing workspace.

| Frozen source | Lines | SHA256 |
| --- | ---: | --- |
| src/townlet/population/vectorized.py | 1854 | 38d8c969a8acfc5f49a3c5c7e532f6f10b34844af12ca37e8696123511e47d3b |
| src/townlet/training/prioritized_replay_buffer.py | 783 | 47b0070b5e519c6703d87861da07d8971b6e466f2c3f04c7417fc58db3038c2f |
| src/townlet/config/bac_options.py | 294 | 10dc3ef7dc288d954147046c95bc8362df2162f3829986be26b2724e86dd4916 |
| tests/test_townlet/integration/test_compact_token_acceptance.py | 849 | 468b8b574044fd73b5ff1e3e153d3f326e2abbdb0a63d01a3f95e49a930c90b0 |
| tests/test_townlet/regressions/bac/test_per_native_learner.py | 270 | 6348f247dc9b5060a650f87fe8bee1d9c18ece46a868c40b6021f0360c19da16 |

Root issued these commands from `/workspace/hamlet`, each high case in its own
process. Identity-controller DATA records source module
`src/townlet/__init__.py`, matching base/candidate, torch
`2.11.0+cu130`, and one torch thread. Logs report Python 3.13.5/pytest 8.4.2.
The witness selects CPU; the torch build suffix does not establish GPU execution.

```bash
.venv/bin/python -m pytest tests/test_townlet/regressions/bac/test_per_native_learner.py -k modest -s -q --no-cov -p no:cacheprovider -p bac_source_identity
.venv/bin/python -m pytest 'tests/test_townlet/regressions/bac/test_per_native_learner.py::test_public_learner_two_finite_priority_updates[large-alpha0-control]' -s -q --maxfail=1 --no-cov -p no:cacheprovider -p bac_source_identity
.venv/bin/python -m pytest 'tests/test_townlet/regressions/bac/test_per_native_learner.py::test_public_learner_two_finite_priority_updates[large-alpha1-c01]' -s -q --maxfail=1 --no-cov -p no:cacheprovider -p bac_source_identity
```

## Admitted scope and actual observations

Real temporary authored `default_curriculum` YAML DATA, level
`L1_full_observability`, passed public DemoRunner/UniverseCompiler admission and
VectorizedHamletEnv.from_universe → build_curriculum → VectorizedPopulation
construction. Ordinary reset/step_population supplied real DAC rewards, replay,
network, optimizer and priority updates. No injected replay/priorities, replaced
producer, private counter/done/parameter assignment or unchecked DTO bypass was
used. The unchanged witness snapshots owned rows/parameters and checks actual
predecessor action legality, finite observations, real pre-update Q correspondence,
finite loss/parameters/Adam moments, parameter and forward changes, and real Adam
step counters. This receipt reads those executed assertions/results, not a rerun.

Admitted settings: feedforward [256,128], ReLU, dropout 0, layer_norm false; Adam
learning rate .0001, betas .9/.999, epsilon 1e-8, weight decay 0, constant schedule;
Huber delta .25; gamma 0 in brain AND training/effective override; Double DQN true;
target frequency 1000; two lanes; PER capacity/batch/min_size 2; frequency 1;
sequence length 1; beta 1, annealing false; clip norm 10; one episode with cap 20
ticks. Runtime exploration is the witness's ordinary EpsilonGreedy(.5,.99,.1),
temporary NumPy/torch seeds 731, authored training seed 42, static curriculum.
Drive uses constant_base_with_shaped_bonus with base 2e38, empty extrinsic bonuses
and modifiers, composition normalize false/clip null. Other drive components
remain ordinary. Controls change only base to 1 (alpha 1), or alpha to 0 (base
2e38). `training.bac_options` is null: no hidden sampling configuration was needed.

For **high alpha 1**, tick 1 has actions [4,11], dones [false,false], each actual
extrinsic/total/pre-optimizer absolute TD/serialized priority
`1.9999999360571385e38`. Intrinsic components are [0,0], intrinsic weights [1,1],
and shaping [0.0036754447501152754,0.005527863744646311]. Thus observed totals, rather
than an assumed composition, establish the large finite input. Independent
float64 priority sum is `3.999999872114277e38`, above float32 maximum; normalized
oracle probabilities are [.5,.5]. Actual Huber loss is `4.999999840142846e37`.
Six parameter tensors change, Adam step is 1, all checked parameters/moments remain
finite, initial Q absolute maximum is `0.13513588905334473`, and parameter absolute
maxima move from `0.09205705672502518` to `0.0921388790011406`. The witness bounds
finite Q/parameter maxima by 1e6, TD/total by [1.9e38,2.1e38], and other components
by 1e6; actual values satisfy those prerequisites. Tick 1 reports no warning.

Tick 2 reports `overflow encountered in reduce` and raises
`ValueError: probabilities do not sum to 1` with completed learner updates = 1.
The original traceback is ordinary `step_population` at POP:984 → `sample` at
PB:352 → `_draw` at PB:345 → `numpy.random.choice(..., replace=False)`.
Original PB's float32 score-sum normalization is the established failing boundary;
compiler admission, liveness and the first genuine optimizer update preceded it.
The process exits 1 (`1 failed`), as expected for this causal old-source RED.

Both matched controls complete **two actual updates** and exit 0. Modest alpha 1
has finite losses `0.2005024403333664` and `0.19476845860481262`, finite priorities,
six changed tensors per update, Adam steps 1/2 and no warnings. High alpha 0 has
the same large finite TDs/priorities and loss as above on both updates, six changed
tensors per update, finite parameters/moments, Adam steps 1/2, no warnings and
float64 [.5,.5]. Its second pre-Q maximum is `0.12537488341331482`, and parameter
maximum reaches `0.0922064557671547`; both lanes remain live. This distinguishes
the alpha-1 normalization failure from rejecting large rewards or failing the
optimizer/loss prerequisites.

Temporary YAML digests: modest alpha1
`b6620640a5b39a7ee557964438038a6034d23855b199e03743c4186f74f15779`;
high alpha0 `74db412ad0146ce6b668af479b8f438a4efcb4de30ca75e779afc6cc9679a3f3`;
high alpha1 `76858043731c761c05ebd708e33b10b0020e0bda4409dd2ff22460764fd0b965`.

## Required independent telemetry follow-up and limits

Both high-alpha0 updates and the high-alpha1 first update separately publish
`mean_td_logging: "inf"` for a finite true unweighted mean
`1.9999999360571385e38`. This is the independently triaged existing **P1 X04**, OPEN
and required: T15 owns the truthful producer repair before T15 release/G2, and T35
consumes its verified receipt at the sink. It is not optional, closed, caused by
the sampler, or evidence of optimizer divergence. The finite actual optimizer
evidence above remains intact. MEAN-TD-TRIAGE.md and X04-acceptance-overlay.json
record the separate contract/acceptance. Recurrent same-expression risk was
identified statically; no recurrent authored incident was independently executed.

This new evidence is bounded to the ordinary legacy global-NumPy/physical-index
route and these admitted settings. Its bootstrap remains unmasked; gamma 0
isolates this witness without qualifying that behavior. No replacement-mode,
captured-mask learner, native C07, strict recurrent/world isolation, GPU,
long-run learning quality, native checkpoint continuation or whole-BAC claim
follows. No repaired-source GREEN is asserted. Root retains integration/runtime
ownership; all standing implementation, review and release requirements remain.

## Hashed root evidence

Paths below are relative to `qualification/`.
Hashes were checked against the actual DATA files during this consolidation.

| Evidence | SHA256 |
| --- | --- |
| wave07-red-r0/native-modest-prerequisite.log | da5bd787780e335153e8542bc09b169608234f61beea504b068421d130c29d1d |
| wave07-red-r0/native-modest-prerequisite-result.json | f8990791b78606adcf1e94734cb84d14f6c33fb472c21b73f53edec3e9389da5 |
| wave07-red-r1-narrow/native-alpha0-control.log | ed145846f07341d21d07e78b57babecf172e9acaf63b4e23674d213d95593558 |
| wave07-red-r1-narrow/native-alpha0-control-result.json | acd4354c0628a77dc483bfe34482f205340c418637df5cd8f900f9a91f36a0ec |
| wave07-red-r1-narrow/native-alpha1-causal.log | 0a16aa91fbf9c855ddc3133451209fc7e61a4860cbd27cdde49f63c71b70650a |
| wave07-red-r1-narrow/native-alpha1-causal-result.json | 833c6fea377590092e5009355c9daf8a8aad808df43d73fa6979784f765bf41a |

Under `.superpowers/sdd/2026-11-01-bac-remediation-upgrades/`:
`wave07/causal-red-clearance.json` SHA256
`a9734a2574f732bd2bc4cfc43175a0390890b1115e616fcbe8f884bc97d0b508`;
`wave07-preparation/MEAN-TD-TRIAGE.md` SHA256
`d4562d2cb241dff87e921e0a0c9540cb54832785a6dbf36c6ef8f1ee8fae8b76`;
`wave07/X04-acceptance-overlay.json` SHA256
`bd1e028dd6df9ed2bbaad38cb93a9aa0adeffd28ba227e8441110c2d27b68d8c`.

Only this ignored prose receipt was written. No source, test, index, branch,
worktree, source copy, deletion or subdelegation action occurred. STATIONARY.
