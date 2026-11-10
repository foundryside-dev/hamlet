# T18e current canonical reward-flow API

Source-verified public consumer capsule, 2026-11-10. Prose only; no source/test/index/runtime/import/probe/compile/git/branch/worktree/copy/subagent actions. Exactly the existing five whole sources,4828 lines; no sixth implementation opened. This records current declarations and qualification limits, not copied implementation or whole-programme acceptance.

| Source | Whole lines | SHA256 |
|---|---:|---|
|src/townlet/environment/vectorized_env.py|2452|3b65e6f143edf1a1a363b6b537376f2e8f3f5dc1f7ce6f6feb8ba9c06bca5256|
|src/townlet/environment/reward_calculator.py|68|72368cb6f10eb96ad4f772fbcf46b4229c809091ff6b5414764382141ae0b45c|
|src/townlet/config/exploration_policy.py|1299|fbda6a2178e794747ef1e9b7771d450463051aeba53a598dd40fc334c2754e67|
|tests/test_townlet/regressions/bac/test_parent_intrinsic_handoff.py|668|a794a5a9beb5639b132c6f01f042026d436da8d7c994df2b1f2e93d930156c51|
|tests/test_townlet/regressions/bac/test_intrinsic_composition.py|341|9d4c9812af426a6611e4169a4b33b2d52f4762ba4157ffc1278e3891ae2d54c8|

## Required binding and accepted step

Public ENV declaration: `set_exploration_runtime(*, exploration: ExplorationRuntime, claim_vector_step: Callable[..., int]) -> None` (ENV612). It now requires fresh-unbound world phase and an unbound constructor flag before checking actual ExplorationRuntime instance/callback callability and retaining both references. Successful binding marks the flag; **every later setter call, including the exact same pair, refuses before reference replacement**. First binding after world authority registration likewise refuses. Invalid arguments before successful binding leave the opportunity unconsumed. This is the small once-only pre-custody contract; it adds no callback-owner introspection or mutable BANK accessor. Registered world roles remain separately bound by bind_boundary_authority; the setter does not rebind them. Initial trusted constructor callback capability remains parent-owned. Final owning SPEC/QUALITY and API/README guard clauses are approved; current bounded runtime qualification is recorded below. None strategy is an actual selected runtime, not None or an old provider path. Obsolete set_exploration_module is removed.

Public ENV step declaration: `step(actions: torch.Tensor, depletion_multiplier: float=1.0, *, vector_step: PreparedVectorStep) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, dict]`. PreparedVectorStep is the qualified opaque public `townlet.training.clock_ledger.PreparedVectorStep` declaration (TYPE_CHECKING import; clock body not read). Consumers must obtain it from the actual parent, not construct/copy/serialize authority.

ENV first requires active world phase and non-None exact-current accepted token. It captures detached owned actual encoded predecessor, action tensor and entry activity `~dones`, then calls the bound claim with **exact kwargs** `prepared, accepted, world_ids, predecessor, actions, active_on_entry`. Claim executes before world revision increment, tick-scoped reset and physical writes. Its returned int supplies authoritative parent vector_tick. Actual owned actions drive physics. ENV has no additional lifetime vector clock; global_tick remains resetting episode physics time. Authentication/identity/single-use/nonreentry of the handle is parent-owned under its separately qualified prepare/claim contract. The ENV callable type check alone does not prove a bound callback belongs to that parent.

## One context, stamp, reward and handoff

At unchanged postphysics reward boundary, ENV constructs actual `townlet.config.exploration_policy.IntrinsicTransitionContext(*, predecessor, actions, successor, active_on_entry, vector_tick)`; successor is actual current encode there. This frozen context owns detached tensor clones and returns independent tensor clones from public predecessor/actions/successor/active_on_entry accessors. It has one successor, not a second reward/final successor field.

Actual bound runtime calls are `prepare_step_stamp(*, accepted, world_ids, active_on_entry, vector_tick)` once, then `reward(*, context, stamp, accepted, update_stats=True)` once through RWC. Actual stamp/token identity remains intact. All five families and both scopes use this route, including selected none and all-inactive contexts; BANK remains responsible for actual eligibility/zero-event semantics. No observation-only fallback or second diagnostic reward exists.

RWC declaration is `_calculate_shaped_rewards(*, active_on_entry: Tensor, intrinsic_context: IntrinsicTransitionContext, intrinsic_stamp: CuriosityStepStamp, accepted: WorldAcceptedEpisode) -> Tensor`. Every input is required. ENV's existing private reward wrapper forwards this same complete contract. RWC sends actual reward.raw and reward.scales independently as `intrinsic_raw` and required `runtime_intrinsic_scale` to actual `VTCRewardProgram.apply`, preserving actual reward_context/action-hour kwargs. Composer implementation facts are attributed to T18e-COMPOSER-SCALE-API, not additional source reads: full float32[N] scales multiply once in DAC as raw*scale*drive_base*real_modifier. No RWC preweighting/normalization/mean/scatter/recomposition.

ENV creates actual frozen `IntrinsicStepHandoff(context,stamp,accepted)` and returns this **same object provenance** as `info['intrinsic_transition']`; context/stamp/token are the exact objects used for RWC reward. Handoff's actual class validation requires genuine context/stamp/token types; it does not itself issue/validate their owner authority. RP supplies the current facade methods and typed DTO; BANK/parent own stronger authentication.

## Phase, canonical output and sole service owner

Reward boundary remains after real action/depletion/effects/VTC transition writes, physics tick publication, expression evaluation, authored terminal conditions, eligible step counts and item aging/respawn. It precedes retirement done installation, terminal delayed-work cancellation and final action-hour switch. Authored-terminal active rows still cause eligible provider events, then existing DAC done masking applies. Retiring rows compose live, then ENV adds separate+1 to extrinsic and total; authored termination wins lifespan coincidence. Existing inactive-entry final masking zeros total, every component and modifier weight. Final hour/observation/legal successor masks remain committed before return; live empty-action rows refuse.

Canonical result is final returned rewards and info.reward_components after those ENV adjustments, with info.intrinsic_weight modifier-only. Existing intrinsic_raw means raw*drive_base; provider_intrinsic_raw means unweighted actual provider raw; runtime_intrinsic_scale means actual independent runtime factor; intrinsic is effective scaled contribution. Final inactive masking applies to all component diagnostics. RWC preserves backend objects before ENV's explicit adjustments. Return tensors/dict remain ordinary mutable tensors; sinks must own captured data for later retention.

Actual parent is the sole `admit_and_service(*,context,stamp,accepted)` caller after real ENV return and canonical replay admission. It consumes the same handoff; ENV adds no service. No POP diagnostic reward may recompose canonical total, repeat stats or admit a second time. Count/none do not acquire predictor work merely from using the common facade. Sampled replay uses actual UniformReplayBatch.rewards total and rewards_extrinsic/rewards_intrinsic/rewards_shaping with matching presence flags, per separate REPLAY-BATCH-API; no replay source was opened here.

Failures after claim/physics/provider/replay/service may have real effects. No ENV rollback, fake physics retry or successful-return-only clock guarantee is added. Parent progress/clock advancement remains separately owned. Input refusal before claim effects does not authorize reconstructing a token/handle. Supported recovery requires actual owning healthy boundary restore; component retry caching does not make repeated ENV physics safe. Authentic pre-first-step mixed participation retirement remains absent from current ENV public lifecycle and separately open.

## Actual proof scope and pending qualification

Final current fixed candidate `b2d57f456a68501fa203602b36e6c60a8f0295f7` was qualified in R10 by root and independent Astra:

| Executor | ENV current31 | Parent current44 |
|---|---|---|
|Root|31PASS,27.05925s|44PASS,25.62365s|
|Independent Astra|31PASS,24.37632s|44PASS,20.50740s|

These are the **same75 overlapping cases independently verified**, not150 unique cases. Each execution reports zero errors/skips/warnings and full custody PASS for800 sources,573 configs,13 artifacts,controller/index/import/threads and14registry MAIN1 identities. This capsule author performed no runtime. Earlier R6 partial19 and R7 rich3/originalparent41 involved distinct candidate versions; they are historical staged evidence, superseded for this bounded current75 qualification by R10. Owning ENV source SPEC/QUALITY and API/README guard clauses are approved. Original single-batch A/B3 cases passed in R8 and are included in current parent44; they are not still-pending original defects.

Root reports global Ruff/Black/NoDefaults600/Expr PASS. Global mypy retains6 failures in the existing oracle caller. Compiler CLI34packs/35processes passed in152.12084s with each source/import/thread/config/artifact identity checked. These checks do not qualify stale oracle/current caller migration, full repository tests or complete T18e acceptance.

Parent review remains **CHANGES REQUIRED** for new A2 identical multi-batch retry and D2 install/bind race, with C authentic mixed lifecycle, fullD restored role/native custody, E transfer and F native history/clock correlations still open. Ordinary runner/current caller migration, additional original finite stats/admission/queue/zero-scale/rollover/item/aspatial/coincidence witnesses, actual HC/T26/all-child publication/recovery and all final global gates remain owed. The initial callback remains trusted actual constructor capability; no callback-owner introspection or generic authority framework is claimed.

The last authoritative full-suite baseline is still failed30a:1010failed/7285passed/21skipped/231errors; no broad repeat through known prerequisites is represented as a new full result. CUDA is unavailable and unqualified. No full-repository GREEN, whole-parent approval, whole-T18e closure or release/accounting change follows; original28qualified/38remaining66 remains unchanged. Source/guard hashes above are unchanged; this prose now freezes for root checkpoint/publication custody.
