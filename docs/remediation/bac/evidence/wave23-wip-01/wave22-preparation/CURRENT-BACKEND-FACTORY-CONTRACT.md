# Current backend factory contract

Implemented bounded PW03 factory producer handoff. Actual factory153 lines was read to verify this contract; other APIs are attributed to the root source-verified capsule and public RNG binding receipt. This is not bank/runtime integration, whole PW04 release or BAC acceptance.

## Actual public API

In townlet.exploration.provider_factory:

```python
def make_backend(
    policy: ResolvedExplorationPolicy,
    *, world_id: str | None, obs_dim: int, action_dim: int,
    device: torch.device | str, rng: WorldRNGState | None,
    descriptor: WorldCuriosityDescriptor | None,
) -> ExplorationStrategy: ...

def make_policy_selector(policy: ResolvedExplorationPolicy) -> EpsilonGreedyExploration: ...
```

All inputs are required. Both functions require an actual ResolvedExplorationPolicy and validate an owned reconstruction through its public to_dict/from_dict. The factory introduces no compatibility dispatch, seed/ID/geometry defaults, copied learning implementation or provider algorithm change.

make_backend first requires exact integer observation width: none allows0, Count/RND/adaptive/ICM require>0. Action dimension is always an exact positive integer. Device must resolve to CPU or CUDA; CUDA requires an explicit index. Private CPU ownership expects cuda_devices=(); private CUDA expects exactly (device.index,). Runtime owns CUDA initialization at quiescence; factory performs no explicit CUDA initialization. Existing device/provider operations retain their own failures.

Shared construction requires explicit world_id=None, rng=None, descriptor=None and policy service_clock_unit='vector_tick'. This remains a real positive construction path for all five families. Private construction requires actual descriptor and RNG types, exact nonempty declared world ID and policy clock 'world_eligible_admission', including none/count families without random network initialization.

Private preflight roundtrips descriptor through public from_dict(to_dict()). It reconstructs an expected descriptor with the validated policy, supplied descriptor's world_ids and training_seed, and actual obs_dim/action_dim; complete portable equality is required. It then invokes the actual caller candidate's required-argument validate_binding(descriptor=expected_descriptor, world_id=world_id, cuda_devices=expected_devices), before any selected provider constructor. No RNG snapshot/from_snapshot occurs inside this callback, no private RNG attribute is read, and no validation clone receives production draws.

Per RNG-BINDING-CURRENT-CONTRACT.md, validate_binding permits quiescence or this same owner's active custody, including OwnedWorldBackend.construct's model_init callback; active different owners refuse. It validates existing canonical descriptor identity (scope/provider kind/provider parameter hash/observation dimension/action dimension/seed policy/training seed), exact ID and device inventory plus descriptor/domain rules. Stable identity excludes spectator roster/order. Thus a caller descriptor with different spectators can bind the same exact owner ID if its stable identity matches; factory descriptor equality uses the caller's own roster. Diagnostic epsilon is not provider_parameter_hash. Binding is not arbitrary RNG continuation-component validation; public create/from_snapshot retain that responsibility. Errors propagate before provider allocation; the factory adds no exception recovery/fallback or general exception-normalization promise.

## Actual selected configuration

| Selected strategy | Real class and explicit configuration |
| --- | --- |
| none | EpsilonGreedyExploration with epsilon=policy.epsilon_start, epsilon_decay=policy.epsilon_decay, epsilon_min=policy.epsilon_end, via fresh make_policy_selector |
| count_based | CountExploration with validated policy, exact provider_parameters.quantization_width/max_entries and resolved device |
| rnd | RNDExploration with actual obs_dim, embed_dim=policy.rnd_feature_dim, learning_rate=policy.rnd_learning_rate, training_batch_size=policy.predictor_batch_size, all three epsilon values, device, same actual rng and policy clock |
| adaptive_rnd | AdaptiveIntrinsicExploration with the same RND geometry/LR/batch/epsilon/device/rng/clock mapping, plus explicit initial_intrinsic_weight, min_intrinsic_weight, variance_threshold, min_survival_fraction, max_episode_length, survival_window and decay_rate from policy |
| icm | ICMExploration with validated policy, actual obs_dim/action_dim, all seven exact provider_parameters (feature_dim, hidden_dim, learning_rate, inverse_weight, forward_weight, training_batch_size, max_pending_transitions), resolved device, same actual rng and policy clock |

For RND/adaptive, factory builds RNDOptions with all four resolved policy fields: service_mode, max_updates_per_tick, max_pending_rows, overflow_policy. It calls configure_service before return; adaptive delegates to its actual nested RND. ICM receives its selected policy and complete constructor configuration. Factory does not admit rows, invoke service, change completion/epsilon cadence or retain a new RNG owner.

Private owner construction must pass the callback argument itself:

```python
OwnedWorldBackend.construct(
    rng=world_rng,
    factory=lambda candidate_rng: make_backend(
        policy, world_id=world_id, obs_dim=obs_dim, action_dim=action_dim,
        device=device, rng=candidate_rng, descriptor=descriptor,
    ),
)
```

Each factory call returns a fresh selected real instance. make_policy_selector independently returns a fresh existing EpsilonGreedyExploration using the selected epsilon schedule. The global action selector is a separate mutable object from none backend/private diagnostic epsilon; factory does not synchronize their decay or own when decay occurs.

Count-zero operational support was an explicitly refuted hypothesis from the initial incomplete constructor capsule: unchanged actual Count.compute_intrinsic_rewards requires D>0 (root source verification count_based.py103). Factory now refuses Count-zero before allocation/draw. None-zero remains positive. No Count algorithm or supported positive-width capability was removed.

## Qualified inventory and evidence

Final R3 tested candidate tree:32108b7f6a869c02e0547e6297315cc2aaabfcba. Exact whole-file context:

| File | Lines | SHA256 |
| --- | ---: | --- |
| src/townlet/config/exploration_policy.py |768|af8843ec1a270cfa49ec44b7ac5615d33db0d4d16b2d169d161bb4a1cd402c8c|
| src/townlet/exploration/rnd.py |834|0848cfe8f08635fac6843d90bdf38ca7c08f92ef8220d7859e2ce65dae4ecf0d|
| src/townlet/exploration/adaptive_intrinsic.py |315|cb64d78d01c0bb8422dc664206e65588eba373a0a7ed8408634a7fa0a4b80df4|
| src/townlet/exploration/provider_factory.py |153|7ca30733720017eea4a8063be0261dfd365c9547f501649bd71d937eecd5efb0|
| tests/test_townlet/regressions/bac/test_pw_backend_factory.py |530|565c9279a86d3da3d1998762289c0a20f3b3823c5ccfd0f4770d32a708092061|

Actual5/2600; respective caps1100/1000/500/400/1500 total4500, hard5000. No sixth implementation/helper/test source was read by this implementer. Public source-verified bridge receipt identifies WS871 SHA256a639d6f927492cf0334a49f330f514b6472be75f624f24a2f1b5e8381af93b2c; it is not an additional source inspection in this factory inventory.

Root reports genuine initial RED:142 collected, valid fixture control1PASS, then141 expected missing-factory call-phase FAIL/1PASS, no import errors/skips. R1 root140PASS/2FAIL and independent Astra140PASS/2FAIL isolated the two Count-zero hypotheses. Revised shared/private preallocation refusal regressions then produced two genuine constructor-called RED failures before the narrow factory guard fix. At final R3, root142PASS14.9746s and independent Astra142PASS, both with custody PASS; Astra SPEC/QUALITY APPROVED and findings ADDR. These are separately attributed overlapping selections, not summed evidence.

Qualified factory cases cover real five-family construction in both scopes, selected configuration/service/native state and geometry, CPU private ambient restoration, same-ID construction independent of ambient draws/row/spectator order, actual candidate RNG handoff, wrong binding refusal, independent instances/model storage/optimizers/containers, independent global epsilon, Count-zero preallocation refusal and none-zero positives. Construction and state identity evidence does not establish optimizer learning/isolation under real updates.

Root also reports four global guards PASS (including Black41.0356s/defaults601). Global mypy retains9 old-caller errors: global mypy is not PASS. Prior covering R1 execution, with the same backend/WS bytes, reported378PASS/2conditional CUDA skips34.975s; it was not rerun against the new factory guard and is not presented as final R3 covering execution. No runtime was executed while writing this handoff contract.

## Required open integration and qualification

Actual bank ownership/routing/service/completion and genuine optimizer learning with strict cross-world isolation under updates remain required PW05 and later work. Factory class/config/ownership proofs do not close those gates. Actual native/parent checkpoint coherence and ordinary runner save/load/next-real-update tests remain required. CPU evidence does not establish CUDA or cross-device bitwise behavior; conditional CUDA hardware qualification remains open. Current global old-caller mypy failures, required CLI/full/static/owner-consumer/hardware/remote gates and independent full qualification remain owed where not separately satisfied. No integrated release, package-count increment or X02/BAC closure follows from this bounded producer handoff.
