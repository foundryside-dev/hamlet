# T18e successor equality: bounded source finding

Read-only source analysis, 2026-11-10, against coordinator-supplied frozen current `30a802a996fe8bf7cd63e53d211fa8b2cd028f77` (fullsuite30a802a9). Commit identity was not independently queried. This ignored report is the only write. No source/test/index/tracked-document changes, runtime/import/introspection/probes/compilation/tests, git operations, branches/worktrees/checkouts/source copies, or subagents. This is a source finding, not executable qualification or completion of T18e.

## Exact inventory

Line counts and SHA256 were obtained before implementation bodies. Exactly five whole implementation sources were read, 4737 <= 5000 lines. No sixth implementation/helper/encoder dependency body was read. Repository AGENTS.md and the permitted original task, ENV readiness report and BANK reward-phase report were documentary authorities; external facts below are attributed to those capsules.

| Source | Whole lines | SHA256 |
| --- | ---: | --- |
| src/townlet/environment/vectorized_env.py |2403|a7f998355bec48e3a12c5b8a57648797592bc16c84af0d3f099eb7799db9540b|
| src/townlet/environment/observation_encoder.py |253|a0d4aa8ec1230e19257d7fd8d74c016f6de74b41577e1081643031cc2c8f4144|
| src/townlet/environment/token_publishers.py |1122|dd449cd9bda7a1f2f20ae21df65b34a626d92027f0310c2bb1a63730f3b39c6d|
| src/townlet/effects/manager.py |856|887ff837fdc7cbd5f7519a7a72456de6f288940819dc2159ccda6f59633fed07|
| src/townlet/effects/scheduler.py |103|adadc5718c9638cf33d87a5c5305b26cb42c7db1417a00debcf586679c71dd4b|

Abbreviations: ENV, ENC, PUB, MAN, SCH respectively denote these files.

## API conclusion and status

**The proposed observation difference caused by retirement/dones, final hour, or cancellation of scheduled agent work is refuted by the inspected current observation graph.** These mutations do not change any shown observation input. In particular, scheduled-work cancellation is not cancellation of an active observable effect. No source counterexample to equality was found in this capsule. A second successor field, deferred reward composition or a new phase state machine is not justified by this hypothesis.

**Conditional source proof:** with the constructed encoder/publishers unchanged, no concurrent or callback mutation of simulator/registry/substrate/configuration, deterministic nonmutating external read helpers, and supported finite inputs on the same device, encoding at the existing RWC reward boundary and encoding at ENV1393 have equal values, shape, float32 dtype and device across every row. Reward and DAC callbacks must obey the supplied no-simulator-mutation requirement. The shown encoder/publishers themselves contain no RNG draw or simulator write. These conditions do not require disabling retirement, authored termination, effects, temporal mechanics, partial observability, any provider family or either curiosity scope.

**Unqualified:** the five files do not prove the bodies of external substrate/item/schema/registry read helpers pure, deterministic or free of RNG. Accordingly unconditional equality for arbitrary injected objects/subclasses/custom helpers is not certified. GPU execution/byte identity and integrated equality have not been tested. Conditional equality is sufficient to avoid designing a second successor now; discharge the named read-helper boundary and execute the finite equality gate before claiming universal integrated support.

## Dependency and interval proof

ENV564 builds the encoder once. ENV1074–1076 always calls `encode(num_agents, _build_token_publish_context())`. ENV584–603 supplies positions, `_velocity` (ENV1235–1239 returns it, or None aspatial), meters, cached affordance positions/deployment, vision, no agent slots, item slots and effect slots. No done, time_of_day, reward, component or intrinsic-weight input is supplied.

The supplied ENV report establishes that RWC encodes within its call at ENV1369; the RWC body is not reopened here. Between that encode and ENV1393, the visible ENV tail and the permitted no-mutation reward/composer requirement give:

| Operation | Observation consequence |
| --- | --- |
| Retirement bonus +1 to component extrinsic and total, ENV1370–1373 | Reward tensors only; no publisher reads them. |
| Inactive total/components/weights zeroing, ENV1374–1377 | No publisher reads these outputs; observation rows are not zeroed by done/activity. |
| OR newly_retired into dones, ENV1378 | No publisher reads dones. Authored terminal dones were already evaluated before reward. |
| Cancel pending agent work for newly_terminal, ENV1382–1385 | MAN549–553 calls scheduler.cancel only. SCH77–84 filters/replaces/deletes lists in pending; no commands, hooks, ticks, active-store removal or registry/meter/item write. |
| Set time_of_day from _clock_hour, ENV1391 | ENV704–706 derives a Python hour from global_tick/day_length. No observation publisher reads hour or opening-hour gates. |

Global_tick increment and registry engine tick publication already occur at ENV1339–1340; VFS expressions at1346; authored terminal conditions at1349; item aging/respawn at1359–1361. They are before both observations. There is no second tick publication, VFS evaluation, item tick, effect tick, action, position/velocity/meter/affordance write or schema/device switch in the interval. Exposed engine tick or temporal VFS expressions therefore do not create an intervening observation difference. A final action mask may change with dones/hour, but it is computed after ENV1393 and is a distinct returned info field, not a token input.

## Publisher audit

ENC36–116 constructs built-in publishers by positive compiled capacity, holding substrate, registry and compiled normalization/layout configuration as needed; it does not retain a live ENV reference in the encoder. ENC231–253 allocates fresh zero float32 [N,total_dims] storage on its configured device and dispatches publishers in compiled order. Thus the two outputs need not share identity/storage to be value equal. The encoder's docstring describing a single end-of-step point does not erase the supplied RWC encode call.

| Publisher | Runtime reads relevant to equality |
| --- | --- |
| Self, PUB417–449 | Position, velocity, substrate position dimension and normalize_positions; self presence remains1 including completed rows. |
| Meter, PUB452–525 | Meter context columns and compiled normalizer; no done/activity/hour input. |
| Affordance, PUB528–598 | Context positions/layout/deployment/vision and substrate normalization, egocentric_delta, visible. No opening-hour query. Aspatial branch uses ones visibility. |
| Agent, PUB601–654 | Context agent slots (ENV always None), substrate/context if supplied; no done/hour input. |
| Item, PUB657–715 | Context item slots, visibility, geometry and owner/carried data. No done/hour input. |
| Effect, PUB718–769 | Context effect slots only; active/presence, catalog index, remaining fraction, intensity and owner coordinates. No scheduler/pending read. |
| Registry variable_element, PUB772–927 | Live registry scope_arenas tensors, cached gather columns and normalizer. This is a live-registry read outside TokenPublishContext, but the interval contains no shown registry write. |
| Item variable_element, PUB940–1122 | Live registry item_vfs, item_vfs_index_to_profile and context item visibility/slots; no shown interval writer. |

PUB187–265 normalizes using cached tensors and deterministic arithmetic/finite checks; no RNG, registry or ENV call. Publisher writes target newly allocated rows/local payloads, not context tensors. Dynamic slot validation likewise allocates local occupancy and does not draw randomness. ENC and PUB expose no RNG consumption on their visible encode/publish paths.

ENV1078–1151 item assembly calls external `ItemManager.items_in_world(world)` and `holder_of(item)`, reads inventory slots, item fields and positions, and constructs new batch tensors. There is no shown item/inventory writer in the interval. Purity of those external calls is a remaining capsule boundary, not an assertion obtained from their names.

ENV1153–1227 assembles effects from ENV1229–1233 and MAN809–812 `effects_in_world`; MAN796–807 enumerates active lists, filtering by world without mutation. Effect durations/intensity/observable flags and store order are unchanged by terminal scheduled-work cancellation. It does not call MAN815 `cancel_effect`, which would run interrupt commands and remove an active effect. Observable agent/global/item/affordance instances therefore retain identical slots/presence/values. Even a pending command holding an effect reference is merely removed from pending; cancellation does not execute or mutate that reference.

## Corrections to the preceding public reports

The ENV report's statement that effect-slot visibility *can be affected by intervening cancellation* is not supported for this call path: only future pending work is cancelled. Its explicit nonproof of equality was reasonable before this capsule, but that suggested witness is now refuted.

The BANK report's statement that encodings *may differ even without retirement because time changes* is not a demonstrated current token-observation fact. Current publishers do not consume time_of_day; exposed registry tick/expressions advance before both encodings. Its conditional statement that unequal successors cannot share one current context remains valid, as does BANK's reward/service content equality contract. Its proposed required reward_successor and acceptance requirement to force unequal early/final encodings should not be adopted on the now-refuted causes. Do not reject a correct real equality test because both encodings are equal.

Per the supplied BANK capsule, current IntrinsicTransitionContext owns one predecessor/actions/successor/entry-mask/tick and BANK enforces reward/service equality in both scopes. Under the equality conditions above, capture the reward-phase successor once into that owned context, use it for the existing reward call and the same-context service, and verify it equals the actual returned observation. That gives ICM the true (s,a,s') while preserving observation-family reward phase. Capture predecessor and action before physics; do not substitute diagnostic novelty or repeat provider queries. Retain original authored-terminal masking, live retirement composition, +1 extrinsic/total afterward, inactive zeroing, action-hour shaping/modifiers, all five families, both scopes and final replay values. Equality does not resolve the independently reported lifetime service-clock or production parent/replay ownership gates.

## Exact remaining read-helper capsule

No sixth body is authorized here. To turn the conditional proof into a closed source proof, request a bounded owner report, with exact files/hashes and positive-capacity/configuration mapping, covering:

1. `townlet.substrate.base.SpatialSubstrate` (imported from src/townlet/substrate/base.py), actual factory-selected implementations of `position_dim`, `normalize_positions`, `egocentric_delta`, `visible`: deterministic reads, no hidden clock/done/ENV/RNG/state mutation. Source paths for selected concrete implementations must be supplied by that owner, not guessed here.
2. `townlet.items.ItemManager.items_in_world` and `holder_of`, and the used item/inventory field accessors: repeatable read-only traversal with stable order and no RNG/state mutation. The imported package does not establish their defining source filename; owner must name it.
3. `townlet.universe.dto.token_spec.TokenSpec.compact_layout`/`get_type` (src/townlet/universe/dto/token_spec.py), and `townlet.vfs.registry.VariableRegistry` live arena/item/profile accessors (src/townlet/vfs/registry.py): stable layout/storage reads, no lazily recomputed hour/done dependency or mutation on publish access. Ordinary immutable schema/storage semantics are the explicit condition, not independently verified bodies.
4. Existing RWC/DAC/provider owners: confirm the permitted public no-simulator-mutation callback contract covers the complete interval after the first encode; identify any actual registry, meter, item, substrate or schema write/alias. This request is documentary, not permission to open RWC/DAC/provider bodies here.

No actual violating helper/callback was found; these are precise proof boundaries, not claims of bugs.

## Finite future acceptance and genuine adverse controls

Execute only after freeze release in an authorized implementation/test envelope. None executed here.

1. Genuine ENV steps capture the existing RWC encode and actual ENV-returned encode without replacing either encoder or composer. Assert full-batch shape/dtype/device plus torch.equal, including eligible terminal/retirement rows and already inactive rows. Cover retirement alone, authored termination, coincidence (authored wins bonus), and next inactive step. Assert reward components/+1/inactive behavior independently. Observations of inactive worlds need not be all zero.
2. Include an observable active effect still alive after tick AND pending agent work that terminal cancellation actually removes. Compare active effect tokens unchanged while pending work disappears; cover authored terminal and retirement. An empty effect manager or no matching pending work cannot discriminate the cancellation claim. The control must show pending mutation without inventing active-effect removal.
3. Cover spatial and aspatial, temporal enabled/disabled, a real hour rollover and an exposed tick/temporal expression, configured meters/affordances/items/effects/variable_element capacities, partial/full vision and carried/hidden item companions where available. Compare actual token tensors; changing action masks is not evidence of observation inequality.
4. Repeated encoding at fixed state must have equal output and unchanged simulator/registry/item/effect/scheduler/RNG state, with independently allocated output storage. Input/returned-observation mutation must not alter the owned context. Same-device value equality with shape/dtype/device checks matches BANK's documented equality; byte identity (including signed zero), cross-device equality and hardware determinism are separate assertions, not inferred from torch.equal.
5. Genuine ICM reward and queued service transitions must use captured pre-action observation/action and a successor equal to final ENV return; RND/adaptive service remains predecessor admission. Observation-family rewards remain at the original reward boundary, stats/scale/admission once, same context for reward/service/retry. Check none/count/rnd/adaptive_rnd/icm in shared and private paths. Final replay retains actual returned successor/dones/canonical rewards/components.
6. A genuine unequal-observation witness would need an actual intervening writer to an encoded dependency, a stateful/RNG-consuming external read, or configured publisher/helper that consumes the changed done/hour/pending state. It must identify source and nonzero changed token lane, under admissible real configuration, rather than fabricate unequal successors or monkeypatch a stateful publisher. Callback simulator mutation violates the stated contract and should be diagnosed as that violation. If such a supported witness is later proven, preserve both semantic phases with the smallest explicit seam and review it across BANK/composer/parent owners; never move the existing reward phase silently or drop ICM/retirement/shaping to manufacture equality.

Disposition: interval-based difference hypothesis REFUTED; conditional current-input equality CONFIRMED by source; external-helper purity and integrated executable equality UNQUALIFIED pending the named finite evidence. T18e/release gates remain open.
