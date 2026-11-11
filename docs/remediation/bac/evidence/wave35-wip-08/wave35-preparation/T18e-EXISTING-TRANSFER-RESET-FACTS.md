# Existing POP transfer/reset facts for the native owner

READONLY prose extraction from the already-owned sealed POP source only. No source/test/runtime/import/probe/compile/git/index action or additional implementation body was used. This ignored file is the only write. Source is src/townlet/population/vectorized.py,2596 lines,SHA25690f937a11064c157baad8226f243e8e15a0064543b977fc7aed38d54745a3d0a. The complete parent context remains POP2596/RP1299/clock48/state263/test578=4784/4921; no sixth body. Source line references below are the sealed current file. No execution or native constructor behavior beyond the call site is claimed.

## Actual transfer entry and mutation order

`load_token_network_cross_universe(source_q_network_state: dict[str,torch.Tensor]) -> TokenRosterReport` at2524 is the existing public transfer seam. Its explicit runtime argument is a mapping of source Q-network tensors. It does not receive a source exploration/native checkpoint, parent boundary preparation, accepted token, source runtime, RNG owner, queue disposition, reset receipt or epoch. It is not called inside step_population in this source. This POP body does not establish the phase of external callers, paused/active serving quiescence, or a current source-native provenance relation; serving facts must come from that separately owned source.

The retained transfer sequence after initial architecture guard is:

1. `load_token_network_state_by_type(self.q_network, source_q_network_state)` applies imported token/type intersection transfer. Its implementation is not opened here. This POP docstring states intersecting per-type encoders/aggregator transfer, with payload-schema mismatch refusal and both-direction reporting; no new proof of that external helper is claimed.
2. Copy the resulting online state_dict into target_network and call target_network.eval(). This resets target values to the transferred online values; it does not construct a new target object.
3. Set training_step_counter=0.
4. Call OptimizerFactory.build(config=self.brain_config.optimizer, parameters=self.q_network.parameters()) and replace POP optimizer/scheduler. This passes the actual online network parameters to the factory. POP does not supply old optimizer/scheduler state for continuation.
5. Call `_reset_rnd_state()` and return the transfer report.

No explicit total_steps reset, replay clear, clock-ledger replacement, current observation reset, accepted cursor change, episode completion, provider admission/service or epsilon-decay call appears in this sequence. In the old direct path, resetting training_step_counter without a corresponding ledger reset is now incompatible with newly current ledger.optimizer_updates equality; the native/transfer owner must explicitly reconcile this established transfer operation and full current ledger rather than infer a whole-clock rewind. This report does not authorize silently resetting total_steps or lifetime predictor counters.

**Current sealed safety state:** at2548 the new `isinstance(self.exploration, ExplorationRuntime)` guard raises `RuntimeError('Cross-universe transfer requires the current same-BANK novelty-reset owner protocol')` *before* step1. Current POP initialization requires actual ExplorationRuntime, so the retained old direct helper is not a current fallback route. This deliberate explicit technical dependency is not final transfer capability closure. Root has separately assigned its preservation producer. Existing old helper remains available as source evidence of intent while that work is pending.

## Exact retained RND reconstruction arguments

`_reset_rnd_state` at2566 defines a local `_fresh(rnd)` which calls a new `RNDExploration(...)` with exactly:

| New constructor keyword | Value taken from actual old RND |
|---|---|
| obs_dim | rnd.obs_dim |
| embed_dim | rnd.embed_dim |
| learning_rate | float(rnd.optimizer.param_groups[0]['lr']) |
| training_batch_size | rnd.training_batch_size |
| epsilon_start | **rnd.epsilon, the current diagnostic epsilon** |
| epsilon_min | rnd.epsilon_min |
| epsilon_decay | rnd.epsilon_decay |
| device | rnd.device |

The retained helper does not pass old fixed_network/predictor_network weights, optimizer moments/gradients, reward RMS state, obs_buffer/pending rows, native service counters/position/budget, RNG state, service options, service_clock_unit, origin or descriptor. It performs no serialization, selective dictionary transplant or queue replay. It does not call admit_and_service or update_predictor.

This is an instruction to construct a fresh RND object, not an exact proof from POP of what every current RND constructor field initializes to. The native producer must inspect/qualify the actual current constructor to establish exact model/optimizer/gradient/RMS/tail/clock/RNG defaults and its required arguments. Root already reports known direct RND constructor required rng/service_clock_unit caller diagnostics; this retained call does not supply them. Therefore do not describe its current execution as successfully clearing or preserving a native tail. If that constructor refuses, the historical transfer ordering would already have changed Q/target/optimizer/counter before helper failure; the new current-runtime preflight guard avoids that partial mutation while the new protocol is absent.

## RND versus adaptive wrapper behavior actually visible in POP

| State/control | Direct RND branch | Adaptive branch |
|---|---|---|
| Outer exploration object | Replace self.exploration with `_fresh(old_rnd)` | Retain existing adaptive wrapper object |
| RND inner object | New object | Replace exploration.rnd with `_fresh(old_inner_rnd)` |
| RND fixed/predictor models | No old weights transported to new constructor | No old inner weights transported to new constructor |
| RND optimizer/gradients | New constructor receives LR only, no old state/gradients | Same inner reconstruction |
| Tail/pending rows and service accounting | No old tail/counters/options/RNG transported | Same; no wrapper-side tail preservation |
| RMS | No old mean/variance/count transported | Same inner reconstruction |
| Diagnostic epsilon | New constructor's epsilon_start is old current rnd.epsilon; min/decay retained explicitly | Same old inner current epsilon/min/decay passed |
| Adaptive survival_history | Not applicable | Explicit `survival_history.clear()` |
| Adaptive current_intrinsic_weight | Not applicable | Explicit assignment to wrapper's existing `initial_intrinsic_weight` |
| Adaptive initial weight/configuration | Not applicable | Wrapper remains; no assignment changes initial_intrinsic_weight, min weight, threshold, horizon, decay or other configuration |
| ENV binding | Calls old env.set_exploration_module(fresh) with new direct RND | No setter call; existing wrapper remains attached and its inner reference changes |
| Current runtime global EPS/cadence | This old path has no ExplorationRuntime/global cadence object | This old path has no ExplorationRuntime/global cadence object |

The fresh-object intent is supported directly by the call and replacement, while exact native constructor initialization is outside POP evidence. There is no evidence here that old pending work was deliberately archived, drained, retained or given a lossless disposition. Absence of transport is not permission to discard it in the newly current native contract. The separate reset contract must preserve admitted obligations/accounting under its explicitly qualified semantics and surface any actual geometry conflict.

The old comment saying 'epsilon schedule carries over' concretely means current inner RND diagnostic epsilon is passed as epsilon_start, and epsilon_min/epsilon_decay are copied. It does **not** mean reset to the original authored epsilon_start. The adaptive wrapper's current weight/history are deliberately restarted, not preserved as learned state. Do not treat a fresh whole adaptive wrapper as equivalent without checking all retained wrapper configuration and identity relationships.

Current runtime global selector EPS and parent cadence are separate authorities from native diagnostic epsilon. A same-BANK runtime reset must preserve global current EPS/schedule/cadence exactly under the new contract and explicitly reconcile native diagnostic epsilon from producer facts. POP's retained helper cannot prove that new behavior because it never operated on the current facade/BANK. Likewise, new private learning epochs, lifetime service offsets, cache disposition and queue conservation are required current ownership design, not pre-existing APIs evidenced by this helper.

## Consequence for the bounded native owner

Preserve the actual transfer option and its online/target/optimizer behavior, direct current diagnostic epsilon carry-forward, adaptive initial-weight/history restart and all retained authored parameters. Qualify exact native models/RMS/optimizer/gradients through the actual producer. Do not silently replace actual BANK/issuer, reset accepted cursors/vector clock/global EPS/cadence, fabricate epoch/history/receipts, drop pending work or call a hidden service. The new boundary preparation must move all expected refusal ahead of any online/target/optimizer/native mutation, including source transfer-schema validation, and must settle genuine parent/native clock origin/accounting before publication. This prose supplies facts, not an executable reset producer or a capability reduction.
