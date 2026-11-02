# T16 interface readiness — read-only, stationary

Prepared in the existing `/workspace/hamlet` on 2026-11-02. The T15 fullR2 source/runtime barrier remains active. This is the requested finite readiness receipt, not implementation clearance, a new plan, a new review round, RED/GREEN evidence or package qualification. Root remains the single integration owner.

## Actual source boundary

Exactly two complete implementation files were read, **3147 physical lines**. The third declared path is absent; no helper, config implementation, environment, sampler, network, conftest, existing test or sixth implementation was opened/imported/executed.

| Source | Actual lines | SHA256 | Existing projected ceiling |
|---|---:|---|---:|
| `src/townlet/demo/runner.py` (RR) |1001|`94842641bdce645fdd90d188d5bbdf6e09e7f4c071d15756202e173acd47c15d`|1500|
| `src/townlet/population/vectorized.py` (POP) |2146|`9569eab3d766ed5467ecf78736cd170c7aa0d0b77d90efe28239f3bab64ff12a`|3000|
| `tests/test_townlet/regressions/bac/test_runner_readiness.py` |absent|not created|350|

The declared complete projection is **3 files/4850 lines**, leaving150 below5000. Current two sources plus the complete350-line test reservation total3497, leaving1503 actual growth before5000. The minimal wiring appears confined to RR; POP already supplies the required seam and need not change merely because it is in the inventory. Recount before authoring and fresh review; preserve controls instead of silently exceeding the reservation.

Observed HEAD is `75bc8e438caaf4eadf8f4e0f6b522f84c680c1e7`; the T15 candidate has17 pre-existing staged paths. HEAD is not relabeled as the active candidate tree. Both source hashes match the current source-verified T15 independent review/runtime receipts. Root's brief attributes global fullR2 candidate `f71c52fad680a74da1b90cc7470455fc90f4fa3f`; its qualification result remains root-owned.

AGENTS.md and CLAUDE.md were read, with no nested guidance found on the declared paths. The explicit preservation/addition rulings, approved History A, strict per-world B plus the shared alternative, and root's read-only barrier override conflicting blanket deletion/general workflow prose. No tracker/index action follows from that older workflow guidance. Using-superpowers' dispatched-subagent stop applies; verification-before-completion was read for receipt custody. No test success is claimed.

## Concrete wiring choice

RR already stores the selected `effective_run` at115, the absolute training declaration path/line at116–120, and immutable launch overrides at121–124. Its executed episode limit uses that override or the effective declared limit at173–177. Nevertheless RR456–462 recomputes the effective brain through `apply_training_overrides`, then RR465–481 calls ordinary `VectorizedPopulation` without explicit replay options, warmup, owned sampler identity or a named horizon. It loads after construction at506 and performs genuine learning entry at616.

Use the already accepted public `VectorizedPopulation.for_training` (POP198–267), retaining every existing population argument and the real selected architecture/PER brain. Supply:

| Required qualified input | Exact runner supplier |
|---|---|
| `brain_config` | `self.effective_run.effective_brain`; retain base brain separately for authored-architecture metadata |
| `replay_options` | complete `self.effective_run.options.replay`, with an explicit non-None assertion; never authored partial options |
| `min_transitions` | `self.effective_run.training.replay_buffer.min_size` |
| `replay_rng` | separate `np.random.Generator(np.random.PCG64(self.effective_run.training.seed))`, per root's approved T15 policy |
| `replay_origin` | literal `authored`, denoting the selected explicit caller seed/configuration policy |
| `beta_vector_tick_horizon` | executed `self.max_episodes * effective_training.training_loop.max_steps_per_episode` |
| `beta_horizon_origin` | named upper-bound-vector-tick derivation containing both values and sources: `launch_overrides.max_episodes` when present, otherwise the effective training declaration/field; cap from that same absolute declaration/field |
| `current_vector_tick` | explicit fresh0 before the existing load path; never reapply0 or reconfigure after load |

Read the learner loop/frequency/batch/sequence/gradient inputs from the same effective training view. This consumes the selected complete policy, preserves exactly the five existing effective-brain overrides and adds no local warmup/options table. Do not substitute live-transition budget, population cardinality, retained count, episode index or optimizer count for the vector-tick horizon. Keep the recorded launch override and complete effective configuration for provenance.

Sampler origin and per-leaf origin remain distinct. Omitted replay leaves retain effective `bac-options-v1` derivations/roles; explicit leaves retain their authored roles. RR's canonical `effective_run.field_roles`, `derivations` and `origins` already carry that distinction. Do not replace them with the sampler's single origin or claim that the explicit factory currently populates POP's `replay_option_provenance` tuple: actual POP453 initializes that tuple to None, while only lazy compiled binding fills it at639–641. No second local provenance schema or new option-authoring field is needed for this wiring.

POP's factory validates/copies the six complete leaves/minimum/Generator/horizon/tick and selects the actual recurrent-PER backend eagerly. Existing ordinary construction remains the compiled learning adapter, including its separate inspection/serving/global-sampler roles. Its lazy binding/adoption and current captured restore must remain intact. RR must not reset or reseed loaded replay, discard archives/current qualified history, change brain to bypass recurrent PER, or manually attach a buffer as production proof. Native10/7 guarantees remain T24/T25.

## Missing observable contract versus already satisfied behavior

**The source-proven missing T16 contract is replay ownership; it supplies an intended causal RED, not an executed RED result.** POP508–537 deliberately sets `preserve_global=True` for ordinary nonrecurrent successive sampling. For flat PER that preserves the constructor's global NumPy sampler: POP503 configures an owned sampler only when preservation is false, and POP629 likewise avoids replacing that pristine legacy buffer. The approved explicit T16 caller policy instead requires its separate training-seeded PCG64 stream. The existing public flat serialization receipt gives a direct behavior-level observation:

`buffer.serialize()['sampling_rng']['ownership']` is currently `numpy_global_legacy`, with `sampling_origin='legacy-constructor'`, whereas the explicit authored runner route must publish `owned_numpy_generator`, engine `PCG64`, origin `authored`, and real owned state. Observe those public descriptors on a genuine RR-created population, then let its actual sample/update execute. Do not substitute the learner, inject replay or make a call-name spy the sole failure. A bounded global-NumPy perturbation around genuine sampling can additionally distinguish ownership if root's existing fixture supply supports an unambiguous paired witness; descriptor ownership plus actual use is already the concrete missing contract.

For recurrent PER, current ordinary construction starts with the two-argument sequential inspection buffer (POP400–404) and binds selected options/priority state only at actual learning entry. The explicit runner route must carry its genuine selected policy at construction, visible through public sequential serialization before the first step, and then roll out/learn. Construction-time selected state is a separate acceptance observation; current successful post-binding recurrent learning must not be falsely presented as a missing capability.

The following hypotheses are **refuted by actual T15 source and retained as regression controls**: ordinary RR learning ignores min_size; ordinary recurrent PER cannot learn; selected replay modes are ignored after binding; beta stops during warmup; LR/target clocks advance on skipped opportunities. `_compiled_replay_setup` reads real min_size/options/limits/seed; `_bind_training` activates before admission; `_replay_request` passes the minimum; `_learn` gates on backend readiness; total_steps/beta advance before scheduled learning at1333–1336; optimizer/scheduler/target updates occur only after successful optimization at763–768. The current direct gamma assignment at325 also preserves0. Recomputing the same five brain overrides does not itself prove a value-level defect; canonical forwarding is the accepted consistency contract, with gamma0 as a real behavior control.

## Exact fixture/API supply — reuse existing receipts

No imported helper implementation is needed in this three-file context. Use builtin pytest `tmp_path`/`monkeypatch`/`caplog` and a small in-file YAML-data recipe. The real `DemoRunner(config_dir, db_path, checkpoint_dir, max_episodes=..., level_name=..., max_environment_steps=...)` context manager is verified directly in RR; it resolves/compiles the actual pack itself. No fake compiled DTO, separate compiler wrapper or manually constructed environment is needed.

The four required authored families are the existing T02 packs `configs/test/bac_remediation/{feedforward,dueling,token_set,recurrent}/`, each with `levels/L0_0_minimal` in the filename inventory. T02 task225 expressly owns those fixture families. Future test-local copies are authored YAML data only, not a project-source checkout/copy; none was created here. Keep canonical packs unchanged.

Existing source-verified prose already supplies:

- `T15-config-contracts.md`: effective deep-copy carrier, complete six-leaf omission table/roles, exact five override fields, seed/declared/launch horizon sources.
- `T15-interface-proposal-r1.md` and approved Astra r1: exact required factory keywords, separate PCG64(training.seed)/authored policy, named launch-adjusted upper-bound vector horizon and preservation/restore boundaries.
- `T15-constructor-fixture-suppliers.md` plus `T15-constructor-factory-bridge.md`: genuine compiled environment selected-training carrier and existing config/CPU fixtures if an already supplied public helper is reused. This author must not open their source.
- `T15-flat-contracts.md` and `T15-flat-serialization-api.md`: actual `serialize()` descriptor paths above, public readiness/sample APIs, stable IDs, actual beta formula, current owned sampler preservation; no nonexistent flat factory/state_dict.
- `T15-test-authoring.md`, schema authoring and actual independent r1/runtime r2: real selected-family/update controls, min_size independent of batch, actual retained/sampleable cardinality, pending collectors excluded, successful-update clocks and source-verified fixture handoff history.
- `T15-existing-integration-audit.md`: observers must watch actual `sample_batch`/functional learner losses, rather than legacy sample_sequences/loss_fn; recurrent collector commitment happens after the current learner opportunity and on flush.

Before tests-first authoring, root should relay the **existing source-verified authored DATA recipe**, not dispatch another implementation search: exact YAML wrapper/key shape for selected-level training edits, top-level/selected brain PER fields and a valid nontrivial scheduler block, plus confirmation of the chosen L0 minimal recipe's provider/curiosity scope and natural finite rollout behavior. Required edits are N1; min/batch/capacity; train_frequency; sequence_length; max_episodes/cap; gamma/target frequency; all six replay leaves; genuine prioritized=True with valid alpha/beta/annealing; and actual scheduler step/decay. Existing T15 test/fixture ownership receipts should be reused for this relay. No helper/config/environment/sampler source can be added to this author's inventory to answer it. These are finite fixture/API facts, **not an unresolved product capability or permission decision**.

Do not infer the runner's real provider or S1 guarantee from parsing an option. Actual RR still constructs AdaptiveIntrinsicExploration directly. Select the existing fixture/provider arrangement without claiming repaired provider selection/private runtime isolation; keep strict per-world B and shared alternative acceptance with their owners. Record actual curiosity scope/origin/world binding/local clock/guarantee and remaining limitations in the later receipt.

## Finite tests-first RED/GREEN selection, after explicit clearance

All future tests live in the reserved `test_runner_readiness.py` and run genuine `DemoRunner.run()` with its real compiled environment, networks, replay, optimizer and completion/flush. A wrapper may record/observe then call the original population step/sample/loss exactly once; it must not replace learning, forge masks/rewards or bypass readiness.

| Control | Finite required evidence |
|---|---|
| `test_real_runner_warmup1000` | N1, authored min1000, capacity>=1004, small independently declared batch, cap2 and enough declared episodes/actual transition budget for1004 rows. Observe after2 **retained** rows that optimizer_updates=0; pending rows do not count. Before warmup no optimizer/LR/target advancement. At the first scheduled sampleable opportunity after retained>=1000, exactly the first successful update occurs, with finite loss/state and actual network change. For flat successive PER also observe authored PCG64 ownership before and during the real sample; that is the intended prepatch RED. Do not assert exactly vector tick1000 for a recurrent commit-after-gate lifecycle. |
| `test_real_runner_recurrent_per` | Author the real recurrent prioritized brain and complete selected policy; inspect selected public serialized options/priority state before first step, then actual captured rollout/committed replay/sample/update. Cover both PER draw laws with actual receipt mode, finite weights/loss/optimizer state and real parameter change. No false non-PER brain/manual attachment. Preserve the same min1000/two-retained-row warmup assertion when this case shares the warmup parameterization, rather than replacing1000 with a smoke minimum. |
| Four-family cadence/gamma control | Real authored feedforward/dueling/token_set/recurrent; N1, min4 independent of B, cap2, train_frequency3, target interval2, nontrivial authored LR scheduler. Record successful updates only on eligible vector ticks (with controlled cap2, first eligible6; then9/12/15), target copies only on successful updates2/4, scheduler exactly once per success. Check explicit vector horizon from executed episode override versus declared limit, independent of max_environment_steps and N. Include authored gamma0 and compare actual learner targets against the corresponding sampled rewards to demonstrate myopic behavior, while keeping finite actual optimization. |
| Fixed-full no-window diagnostic | Recurrent cap1/L8/min1 with transition-tail retention; fixed_full reports `capacity_window_impossible`/truthful unavailable counts and zero updates without crashing. Observe the actual log at scheduled opportunities and no repeat for unchanged reason/counts. The additive adaptive-prefix/anchor configuration can sample a real length1 and perform a finite update. Do not fabricate an eight-row window or relax the fixed-full diagnostic. |

Parameterization/in-file observation helpers can share setup within350 lines; root retains discretion over the smallest exact combination preserving these controls. Collection/fixture/API failures are prerequisite failures, never causal RED. Current warmup/cadence/recurrent success may already be GREEN; record that honestly. Canonical forwarding/origin/horizon observations supplement the ownership RED but cannot be reduced to asserting the spelling of a factory call.

After root closes T15 and clears tests-first work, the finite focused selection is `tests/test_townlet/regressions/bac/test_runner_readiness.py` RED, then the same full owned file GREEN. Root's locked import/identity/fixture/TMPDIR/basetemp harness supplies the actual command and avoids a concurrent qualification/runtime. Affected owners are existing learner legality, population recurrent, training-loop/checkpoint, authored episode-lanes and lane-learning/bootstrap/BPTT selections from T15 receipts, narrowed causally by the actual RR-only or RR/POP patch. All six standing guards/fresh independent implementation review remain root-owned. The BAC cadence policy requires root to assess actual earlier-full triggers before deferring to G2; uncertainty means a full gate. Focused evidence is not repository GREEN.

## Custody and disposition

This ignored report is the only write. `.git/info/exclude:7` matches `/.superpowers/`. No source/test/tracked-doc/YAML/index/tracker edit, project import/runtime/pytest/collection/compiler/linter/probe, branch/worktree/project checkout/source copy/deletion, subdelegation, commit or push occurred. Existing14 checkouts are preserved. Prose searches that named an absent historical glob returned an ordinary missing-file diagnostic; no source/runtime was opened to compensate.

No real unresolved capability decision was found. The finite outstanding handoff is the existing authored fixture DATA/scheduler recipe above and root's actual T15 qualification/explicit authoring clearance. Remain stationary. No implementation starts from this receipt.

## Root-adopted bounded context extension — actual schema verified

Root subsequently adopted `T16-bounded-context-adjustment.json`, updated the task inventory and appended the effective boundary to `T16-task-brief.md`. This finite extension supersedes the earlier3-file/4850 projection and350-line test reservation above. It changes no frozen plan bytes, task/lens/acceptance scope or runtime clearance. The source barrier remains active; root reports fullR2 at72% without an error, which is progress rather than a PASS.

Both newly authorized sources were read **completely**, without following their imports. The current complete context is exactly **4 existing implementation files/3877 physical lines**, with the fifth future test absent:

| Complete source | Actual lines | Actual SHA256 | Effective projected ceiling/access |
|---|---:|---|---|
| RR `src/townlet/demo/runner.py` |1001|`94842641bdce645fdd90d188d5bbdf6e09e7f4c071d15756202e173acd47c15d`|1200 / modify only after clearance|
| POP `src/townlet/population/vectorized.py` |2146|`9569eab3d766ed5467ecf78736cd170c7aa0d0b77d90efe28239f3bab64ff12a`|2200 / modify only after clearance|
| BC `src/townlet/config/brain_config.py` |568|`6c041ed40de507dfed81dc4b3a58cbb728d446228f6fd831ee115348aa559079`|600 / read only|
| OF `src/townlet/agent/optimizer_factory.py` |162|`56af1a9c8edb70a25b43a6e10aa3080d9a7b8becff112924e21a9429d994717d`|200 / read only|
| Future `tests/test_townlet/regressions/bac/test_runner_readiness.py` |absent|not created|700 / create only after clearance|

Effective complete projection **5/4900**, leaving100 below5000. Actual existing sources plus the full700-line future test reservation total4577, leaving423 actual growth before5000; the projected existing-source ceilings reserve323 of that growth. POP has54 lines below its2200 ceiling, reinforcing the minimal RR-only wiring choice. No sixth implementation/helper/test/config/environment/sampler source was opened. Nested config/agent AGENTS/CLAUDE paths were checked and absent. HEAD and the original RR/POP hashes remain unchanged.

### Exact authored DATA and schema

Read only the four existing families' complete `brain.yaml`, `levels/L0_0_minimal/training.yaml` and `levels/L0_0_minimal/drive.yaml` as authored DATA. No canonical file was modified/copied. Root explicitly permits later test-local YAML DATA copies; that permission creates no source-copy/check-out authorization.

Brain documents are **flat mappings**, validated as `BrainConfig(**data)` by BC478–507; there is no outer `brain:` wrapper. Selected training documents contain sibling `run_metadata` and **`training`** keys. Therefore the future in-file fixture edits `training_doc['training']['population']['size']`, `['replay_buffer']`, `['q_learning']`, `['training_loop']` and `['bac_options']['replay']`. Drive documents have an outer `drive` mapping. Preserve the rest of each document, including accepted inactive architecture presets.

All four selected training declarations currently have seed42, N8, replay capacity100000/batch32/min1000, training gamma0.99/LR0.0001/target500/DoubleFalse, cap1000, episodes10000/frequency4/L8. Every brain has replay capacity100000/prioritizedFalse, Adam LR0.0001/beta1=0.9/beta2=0.999/eps1e-8/weight_decay0, smooth_l1, and an explicitly constant schedule. The brain's authored target1000/DoubleTrue differ from selected training target500/DoubleFalse; this supplies a genuine existing override control.

BC362–424 verifies the real prioritized schema. To author actual flat/recurrent PER, change the flat brain mapping's `replay` block to include **`prioritized: true`, `priority_alpha: 0.6`, `priority_beta: 0.4`, `priority_beta_annealing: true`**, retaining positive capacity. Alpha/beta accept0 through1; all three named PER fields are required when prioritizedTrue and forbidden when prioritizedFalse. These settings belong to brain replay, not selected training's replay_buffer. The canonical effective override changes capacity only and must retain prioritization/alpha/beta/annealing. No architecture-based recurrent-PER refusal exists in this inspected DTO; actual selected construction remains POP's factory proof.

Feedforward and token_set selected training explicitly author successive sampling, legacy recurrent uniform adapter, fixed_full/whole_episode/window_mean/max_abs. Dueling and recurrent explicitly author independent replacement, uniform-window adapter, adaptive_prefix/transition_tail/anchor_transition/mean_abs. Preserve the actual complete six leaves when exercising each family; test-local variations can cover the other PER law/diagnostic without replacing the architecture. The recurrent authored network is genuinely recurrent:16-dimensional token embedding, attention aggregator with2 heads, interaction_mlp encoder hidden32, LSTM hidden16/one layer/dropout0, Q-head16. Token_set uses16-dimensional tokens/mean/linear encoder/Q-head16; dueling uses shared16 and value/advantage8; feedforward uses256/128. Retain these real selected networks and accepted nonselected feedforward presets.

### Actual scheduler construction and finite clock oracle

The exact path is **`brain_doc['optimizer']['schedule']`**, not optimizer.scheduler or selected training.training_loop. BC189–222 validates schedule type `constant`, `step_decay`, `cosine` or `exponential`; optimizer.schedule itself is required atBC263. Step-decay requires positive step_size and gamma strictly between0 and1; cosine requires positive t_max and nonnegative eta_min; exponential requires gamma in(0,1). All four currently authored constant schedules return schedulerNone, so unchanged packs cannot by themselves prove LR scheduler advancement.

A valid finite test-local schedule is `{type: step_decay, step_size: 2, gamma: 0.5}`. OF24–111 builds the actual optimizer from declared Adam fields and then calls `_build_scheduler(config.schedule, optimizer)`. OF114–162 dispatches constant→None, step_decay→actual Torch StepLR, cosine→CosineAnnealingLR(T_max=t_max,eta_min=eta_min), exponential→ExponentialLR(gamma=gamma). No separate sampler/helper/provider API is needed for this schedule. BC534–568 independently verifies exactly the five copied effective overrides and direct gamma assignment, including gamma0; optimizer's schedule/Adam fields and replay's PER fields survive those overrides.

For the future genuine runner cadence witness, capture the scheduler/optimizer baseline after construction, then count successful **Q-optimizer** updates. Actual POP763–768 orders optimizer.step, successful-update-counter increment, scheduler.step, then target copy on counter modulo target interval. With authored frequency3/min4/cap2 and sufficient retained/sampleable support, successful ticks6/9/12/15 correspond to updates1/2/3/4. The intended executable oracle for step_size2/gamma0.5 is LR factors1,0.5,0.5,0.25 at those successes, target copies only at successes2/4, and no LR/scheduler/target progress on skipped ticks. Record actual baseline-relative scheduler counters and LR values; this source inspection does not assert that PyTorch/runtime has executed or that a test passed.

Q warmup is distinct from curiosity training. Actual RR constructs its real AdaptiveIntrinsicExploration with the selected training intrinsic/RND fields, and POP admits/services existing RND predictor work during Q replay warmup. `optimizer_updates == 0` must mean the learner's `training_step_counter`/real Q optimizer steps; do not accidentally demand zero RND predictor updates or suppress them to simplify the witness. The current real shared Adaptive/RND arrangement remains unchanged.

### Runtime guarantee boundary and remaining supplies

All four authored drives select `drive.intrinsic.strategy: adaptive_rnd` with base_weight0.1 and identical modifiers/rewards; their complete drive DATA share hash `1dfaca1e050a33fc1776b065481ce77f77789ea9b450a35ee3cf86171bb048e8`. RR still directly constructs one shared AdaptiveIntrinsicExploration/RND object from training fields and attaches it through POP. Dueling/recurrent options specify provider_parameter_source=drive while feedforward/token_set specify training; parsing those alternatives does not establish that this manual runner construction honors provider precedence. T16 preserves the real shared object arrangement and records that limitation; no selector/preference repair, private bank, private predictor RNG or provider isolation guarantee is introduced here.

Later receipt fields must distinguish actual runtime curiosity_scope=`shared` (the existing RR arrangement), origin=`existing RR AdaptiveIntrinsicExploration construction from selected training`, and world_binding=`single population exploration module; N1 finite fixtures`, from any declared/effective per_world policy. Guarantee is limited to actual runner resolved replay/warmup/sampling/horizon propagation and observed learner clocks. Local units are retained eligible transitions for warmup, vector ticks for PER beta, and successful Q-optimizer updates for LR/target cadence. N1 tests make no multiworld differential or strict per-world curiosity qualification claim; strict B/shared alternatives remain preserved with their actual owners.

The previous request for external PER/scheduler/wrapper DATA supply is **closed by these complete authorized source/DATA reads**. No new supplier/search/review loop is needed. Natural finite rollout and the intended assertions still require root-owned actual tests after clearance; the cap/budget/episode counts do not substitute for observed retained rows or sampleability. Root's actual T15 qualification and explicit tests-first authorization remain the sole next clearance dependency.

Only this ignored report was appended. No source/test/tracked-doc/DATA/index edit, project import/runtime/pytest/collection/compiler/linter/probe, branch/worktree/check-out/project-source-copy/deletion, subdelegation, commit or push occurred. Existing14 checkouts remain preserved. Return stationary under the active source/runtime barrier.
