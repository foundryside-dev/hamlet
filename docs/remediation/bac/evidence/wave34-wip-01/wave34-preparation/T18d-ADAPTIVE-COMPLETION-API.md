# T18d adaptive completion — actual public facts and genuine fixture recipe

Readonly capsule for the active runtime test author. Exactly one new permitted implementation was read: `src/townlet/exploration/adaptive_intrinsic.py`,315 lines. All other facts below come from already-owned BANK/CP and `test_pw_scope_conversion.py`; no RP/EPS/HC/RND/ENV/runtime/new-runtime-test implementation was read. No runtime/import/compile/probe/test was executed. Only this ignored capsule was written. Recipe assertions below are required future executable evidence, not a claim that this worker has observed them run.

## Exact current adaptive rule

Public provider method: `update_on_episode_end(self, survival_time: float) -> None`. It first validates existing history, constructs prospective history by appending the supplied genuine survival and keeping the last `survival_window` entries, then decides annealing on that prospective history. It assigns prospective history and the resulting weight together. Invalid survival/history refuses before assignment.

- History must be an actual list of at most survival_window finite nonnegative numeric values; bool is forbidden. Values must also remain finite when represented as float32.
- **Minimum history is hardcoded ten survival records**, independently of configured window. Fewer than10 returns false. Setting survival_window below10 cannot accelerate annealing; it prevents the minimum from ever being retained.
- At length>=10, the estimator uses `torch.var(float32_history)` with the default sample-variance correction and `torch.mean(float32_history)`. Both must be finite.
- Annealing requires both **variance strictly less than variance_threshold** and **mean strictly greater than min_survival_for_annealing**. Equality at either threshold does not trigger.
- Derived target/minimum survival is `int(min_survival_fraction * max_episode_length)`, exact integer truncation. It is not the unrounded product or LaneOutcome.planned_horizon.
- If annealing triggers, new weight is `max(current_intrinsic_weight * decay_rate, min_intrinsic_weight)`. Otherwise weight remains unchanged. A weight already at the floor or decay_rate1 cannot show strict change despite a true decision.
- Config requires finite nonnegative scalar parameters, min_weight<=initial_weight, survival fraction and decay_rate within[0,1], positive exact integer max_episode_length/window. The method never invents histories to satisfy its minimum.

Public observation methods: `should_anneal(self) -> bool` applies that decision to current history; `get_intrinsic_weight(self) -> float` returns actual current weight; `checkpoint_state(self) -> dict` returns independently owned current native data. `anneal_weight(self) -> None` directly applies decay/floor but **must not be used to manufacture a passing completion test**: it bypasses the genuine once-owned episode path.

Relevant actual provider fields/current native keys: initial_intrinsic_weight, current_intrinsic_weight, min_intrinsic_weight, variance_threshold, min_survival_fraction, max_episode_length, min_survival_for_annealing, survival_window, decay_rate, survival_history; nested `rnd` live provider / `rnd_state` serialized native. Native schema is `adaptive-intrinsic-state-v2`; native validation requires exact current keys/config, consistent derived threshold, bounded current weight and valid actual history, then validates/loads real nested RND state. This is not permission to fabricate a native payload or mutate history/counters.

## Existing policy and Rig controls

Module imports: `tests.test_townlet.regressions.bac.test_pw_scope_conversion`. Reuse `compiled as compiled`, `policy`, `Rig`, `equal`, `live`, `on_backend`, `native_ledger`, `observe_training`, `set_gradients`, and `assert_baseline` by their public fixture names; do not copy their implementations.

`policy(compiled, family, scope, mode)` has no keyword overrides. Use family adaptive_rnd, scope shared/per_world, and service mode paced_fifo/occupancy_fifo. It genuinely authors:

| Authored fixture field | Value / effect |
| --- | --- |
| training.intrinsic.initial_weight |0.4|
| training.intrinsic.survival_window |10, sufficient for the hardcoded minimum|
| training.intrinsic.min_survival_fraction |0.01|
| training.training_loop.max_steps_per_episode |20, therefore derived minimum int(0.2)=0|
| training.intrinsic.annealing.min_weight |0.01, below0.4|
| training.intrinsic.annealing.threshold |100.0, strictly positive variance threshold|
| training.intrinsic.annealing.decay_rate |0.9, strictly less than1|
| replay batch / trainable pending capacity |2 /4|
| RND feature width / learning rate |4 /0.001|

Do not assign changed fields onto an already-created actual provider to bypass the policy/native-config identity. Existing fixture policy already supplies valid observable-anneal controls; no extra policy constructor/reconstruction is necessary. This worker did not read RP and does not invent additional RP override APIs.

`Rig(compiled, selected, ids=IDS, *, width=3, seed=701, membership=IDS)` uses genuine ENV, accepted tokens, owner issuers and BANK. `IDS=("A","B")`; ids/membership may be explicit coherent tuples. Width is synthetic curiosity geometry, seed is actual ENV/descriptor seed. `begin(batch)`, `step(tick, active=(True,True))` and `close()` are the existing genuine lifecycle methods. `step` returns actual `(context, stamp, reward, receipts)` after a real ENV step. `close` takes **no survival override**: for each actual BANK participant it constructs the typed outcome survival from `int(rig.env.step_counts[lane].item())`, final meters from real ENV, exact accepted batch/world/sequence and agent index. It freezes full canonical outcome payloads, prepares actual dispositions and ENV close, commits actual BANK completion and installs genuine next release. Planned_horizon20 does not override the actual survival used by adaptive.

Consequently one or a few real steps followed by **one** close do not anneal a fresh provider: shared sees at most one record per participating lane, private sees one per own participating episode. A strict test failure0.4<0.4 after that close is expected fixture insufficiency, not evidence that completion ownership is defective.

## Genuine strict-change recipe in both scopes

Use the same recipe for shared and private to avoid confusing shared multi-lane aggregation with private own history:

1. Construct selected adaptive policy and genuine Rig/runtime owner wiring using the existing fixture capsule. Keep A the sole participant with `active=(True,False)`. Start at genuine batch0 and advance actual batches; use monotonically increasing explicit vector ticks across episodes. Never assign history, current weight, ENV step counts or native counters.
2. Complete nine real episodes through actual begin -> real ENV step(s) -> settled reward/service -> genuine close. One real step per episode is sufficient **if the captured actual survival is positive**. Before each close, record actual A step_count; after close, compare actual native history exactly with those real recorded values. Assert the actual value is>0. If genuine ENV behavior fails that prerequisite, stop and fix actual survival participation rather than insert a synthetic survival.
3. At the ninth completed boundary, assert actual A/shared history length9 and current weight0.4. The private B provider must retain empty history/current0.4 as a nonparticipant; shared has one coupled history, not separate A/B histories.
4. Begin genuine episode10 (batch9), perform actual A-only step(s) and settle service. Record actual next survival from ENV. Compute the proposed ten-record evidence from the nine retained real survivals plus this value. Assert float32 sample variance<100 and float32 mean>0, and old weight above0.01. This establishes the exact causal trigger **before** asserting annealing. Repeated one-step survivals should give equal positive values, variance0; verify actual values instead of assuming a modelled history.
5. Capture actual native/learning witnesses, then invoke the runtime's actual owned completion route as it cooperates with genuine Rig/ENV close. After the first commit, require history exactly the ten genuine values and weight strictly below old0.4, numerically matching max(old_weight*0.9,0.01), ordinarily0.36. Do not weaken `<` to `<=`.
6. Exercise the unchanged owned completion retry using the exact genuine prepared completion handle/content/token, while the accepted close transaction is still authenticatable. Actual BANK `commit_completion(*, prepared)` is idempotent only for that exact committed handle. A scoped call wrapper can repeat the genuine completion invocation immediately before returning its receipt to ENV close; it must return the genuine receipt to the unchanged lifecycle. Capture and compare entire actual native history/weight after first versus repeated invocation, and require identical receipt identity where the runtime contract supplies it. Do not start a new episode or fabricate another handle to call that a retry. The existing Rig.close itself invokes completion only once; it does not by itself test repeated runtime ownership.
7. Prove actual learning continues afterward: use real next accepted episode and new reward/service, and verify actual predictor/Adam counters/parameters where applicable. Exact history update is append-and-truncate, not always a length increment: after length10 another genuine completion retains length10 but shifts the observed real survival sequence and decays once again when conditions hold.

The runtime author's completion signatures come from its accepted runtime design, not this capsule. Keep the existing actual BANK registered as ENV owner and route tested completion through runtime explicitly; merely completing raw Rig.bank does not prove runtime owns epsilon/completion cadence. The previous T18d-RUNTIME-FIXTURE-API.md describes retaining the actual BANK through the genuine issuer_factory callback without exposing a mutable child.

Shared alternative: both participating lanes add outcomes in actual accepted order to the coupled provider, so five genuine two-participant closes can accumulate ten records. The existing `trained_source(compiled,"adaptive_rnd",mode)` uses exactly five actual episodes with genuine steps/outcomes, yielding an evolved shared source. That helper is **shared only**. Five two-lane closes cannot stand in for ten completed own episodes on each private provider. The A-only ten-episode recipe makes the causal threshold identical in both scopes.

## Genuine model/tail/gradient evidence

No manual history/counter mutation or fake native state is needed. A-only service with batch2 performs real updates across episodes while retaining an odd pending tail across completion. Use `native_ledger(live(actual_bank,"A")["native"],"adaptive_rnd")` to inspect actual nested counters/tail; it unwraps rnd_state. Check admitted=consumed+dropped+pending and actual optimizer updates, and compare actual learned predictor tensors/Adam moment state from owned witnesses. `observe_training(actual_bank,"adaptive_rnd","A")` installs hooks on the actual owned predictor and records genuine grad-enabled inputs; remove its returned hook before final state comparison. `live` computes actual live IDs/storage/gradients in the owner callback and returns owned witness data, rather than exporting a copied provider.

With ten real single-A admissions and no overflow, expected actual batch2 service evidence is five optimizer updates and empty active tail. Then an actual eleventh admission yields a genuine one-row pending tail. Confirm actual receipts/counters and hook inputs instead of inserting those values. `set_gradients(actual_bank)` is the existing explicit None/zero/nonzero **actual parameter-gradient** fixture control for transport tests, not an adaptive/history/weight/counter control. Genuine service must establish real backward/Adam/model change first; do not claim this helper alone proves learning. Completion must preserve actual predictor/fixed-network/optimizer/gradient/tail state while changing only adaptive history/weight and BANK dispositions.

Private witnesses must run via `live`/`on_backend`; do not call shared-only backend helper for private or inspect a backend copied out of an owned callback. A pure witness is an actual observation with owner revision effects; take baselines at the appropriate boundary and do not export/snapshot after prepare before install. Private B should remain unchanged in native/RNG/gradient/storage witnesses while only A participates. CPU synthetic geometry evidence remains a component result, not full runner or exact simulator continuation qualification.

## Exact assert_baseline argument correction

Existing signature: `assert_baseline(bank, source, choice, world, local_admitted, local_updates)`. **source is a captured shared BANK checkpoint mapping**, not a Rig and not the containing runtime envelope. For trainable families the helper immediately indexes `source["shared_backend"]["native"]` and derives source counters independently. Passing the Rig causes TypeError rather than an acceptance failure.

When the runtime's genuine captured envelope has the accepted `bank` member, retain `source_bank_state = source_runtime_state["bank"]` directly. This references the actual captured current BANK data; it is not an implementation/source copy or fabricated native format. Proper call example: `assert_baseline(actual_target_bank, source_runtime_state["bank"], choice, "A", 2, 1)` after two genuine target A admissions and one real batch2 update. For zero future work use local values0,0. Use the actual requested choice and actual measured local work; do not hardcode2,1 when another sequence ran. The same captured bank mapping must be the genuine source used for initialization/archive comparison. If a test already retained that mapping under another variable, pass it directly rather than the Rig or entire runtime envelope.

The helper's nontrainable branch only checks inherited_baseline None; that does not make a Rig a valid source argument for trainable calls. Source/shared_backend and target/private owner are intentionally different structures. Keep actual source state unchanged and compare the runtime archive against the real captured bank mapping; no fabricated parser, fallback or normalization.

## Inventory and readiness

Already-owned unchanged sources: CP1138 SHA4de4c481eca21fb3d7fa9aea8804c2b2875c63df6077046e7e286470b6faeb5a; BANK1284 SHA294ef0f8d9f11e74869567e21f2ca44b623fe1cd54ca5c3eb59819c80681a05f; existing fixture1456 SHA672a1441520b69cfda5045220a29d2abf891afa7fbad8d461c5e22c91adab893; none test233 SHA646797d6f256c6396f57b0203413614bb0c4b7b2786b764ed62c425b45e53a13. Newly permitted adaptive315 SHAcb64d78d01c0bb8422dc664206e65588eba373a0a7ed8408634a7fa0a4b80df4 is the sole fifth source. Actual total4426, named ceilings CP1200+BANK1300+fixture1456+none700+adaptive315=4971<=5000.

No sixth source, RP/runtime source, import/introspection, runtime/compile/probe, test/source/index/git mutation, copied implementation or subagent. This capsule explains the observed fixture insufficiency and exact argument contract; it supplies no worker-run model PASS or repaired-test result. Root must obtain actual model/history/strict-weight-change/retry/healthy-continuation evidence after the active test author corrects its genuine fixture.
