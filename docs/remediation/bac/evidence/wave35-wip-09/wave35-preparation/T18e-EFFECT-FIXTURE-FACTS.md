# T18e real effect/configuration fixture facts

READONLY extraction, 2026-11-10. This ignored capsule is the sole write. Metadata preceded implementation reads. Exactly five whole sources, 1705 lines <=5000; no sixth helper/test body, ENV/publisher/token body, import, runtime/probe/introspection, compilation/test, source copy, git/index operation, branch/worktree/checkout or subagent. Real YAML data and public capsules were read. No executable success or T18e completion is claimed.

| Whole source | Lines | SHA256 |
|---|---:|---|
|src/townlet/effects/manager.py|856|887ff837fdc7cbd5f7519a7a72456de6f288940819dc2159ccda6f59633fed07|
|src/townlet/effects/scheduler.py|103|adadc5718c9638cf33d87a5c5305b26cb42c7db1417a00debcf586679c71dd4b|
|src/townlet/effects/schema.py|113|eb8e14e5b5949a18b662517c427d51ad46c3d5557aa6f88e552bd0137c9fd97d|
|src/townlet/effects/context.py|363|17db0d89436d5959c0d3e13ea7e1e3d28f0ce51aef70feb872ceab94a26fd129|
|tests/test_townlet/integration/test_effects_smoke.py|270|f28190dadd6fdb83d6cf5d0176463000e65928222083e2d1543078aadd1a1d8c|

External API authorities: T18e-SUCCESSOR-EQUALITY-API, T18e-ITEM-REGISTRY-READ-PURITY, T18e-ENV-CANONICAL-REPORT, T18e-PARENT-FIXTURE-FACTS, and CURRENT-WORLD-CONSTRUCTOR-TRANSPORT/CURRENT-COMPILED-POLICY-UPDATED. No implementation behind those capsules was reopened. MAN/SCH/CTX below refer to the first, second and fourth counted sources.

## Actual packs and finite discriminating selection

Capacities below follow the public read-purity capsule's compiled formulas: item C=ground limit+inventory limit (one agent per world); effect budgets multiply their scope denominators; variable_element counts exposed elements, including one row per item owner slot. Obtain actual offsets/widths from selected.token_spec.compact_layout(), never hardcode total observation dimensions. These are source/data deductions, not compiled output receipts.

| Pack / primary level | Actual authored controls and expected positive token capacities |
|---|---|
|configs/reference/model_pack / L0_demo|Grid6x6, clamp/manhattan/diagonals; global vision (stratum supports both), temporal enabled and active, day_length24. Three meters energy/health/mood; three named affordances EAT/SLEEP/WORK at [2,2]/[1,1]/[3,3]. Apple/default_item, ground6+inventory2 => item8; reset appearance spawns two random apples. Agent ate_food observable, stack, duration10; max_active_effects agent1, other scopes0 => effect1. No exposed VFS variables => variable_element0. Actual training population8/seed42. This shipped reference YAML is the enabled-time cancellation candidate; current compilation remains unrun/unqualified here.|
|configs/test/items_smoke / L0_smoke|Grid5x5/clamp/manhattan/no diagonals, global vision, time disabled. Three meters energy/health/money; energy_station at [1,1]. Ground10+inventory3 => item13. Apple/food, medkit/medical, coin/currency; reset appearance three apples+one medkit. Four observable item effects; item budget4, other budgets0 => effect52. Medical durability scalar exposed to agent, normalized0..100/default100 => item variable_element13. No exposed ordinary variables. Population4/seed42.|
|configs/test/token_set_smoke / L0_test|Grid8x8/clamp/manhattan/no diagonals, global vision; stratum supports both and temporal enabled but level active_temporal false/day_length null. Item0/effect0. Ordinary exposed agent scalars deficit_energy and time_since_last_eat plus need_tokens tensor2d shape[4,3] => variable_element14. Eight declared meters and fourteen named affordances. Population8/seed42, as established by PARENT-FIXTURE-FACTS.|
|configs/test/bac_remediation/feedforward / L3_temporal_mechanics|Grid8x8/clamp/manhattan/diagonals, global vision (both supported), temporal enabled/active. Exposed global scalar day_phase, expression tick, initial0, cyclical_sin_cos period24; day_length {period_of: day_phase} => variable_element1 with two value lanes. Eight meters/fourteen named affordances. Items declaration ground1+inventory1 => capacity2 but no item types/reset-live-item witness; effects empty. Population8/seed42. EAT hours6..22, WORK9..17, DOCTOR8..18 are actual authored gates.|
|configs/test/action_space/aspatial / L0|Aspatial/global/time disabled; three meters energy/health/money, one Bed affordance with random deployment. Item declaration ground1+inventory1 => capacity2 but no item types; effects empty, variables declarations empty. Population1/seed42. This exercises rank0 geometry, not positive live items/effects.|
|configs/test/effects_smoke / L0_effects|Grid5x5/global/time disabled; energy/health meters, BED[2,2]/FOOD[3,3]. Agent observable energy_regen duration20/renew, poison20/merge, buff_replace15/replace, health_boost1/stack; agent budget4 => effect4. Ground1+inventory1 => item2 but no types; no exposed variables => variable_element0. Population1/seed42.|

Use enabled-time model_pack for real pending cancellation; items_smoke for actual live item/profile exposure; token_set_smoke for ordinary exposure; feedforward L3 for real clock expression/rollover; aspatial L0 for rank0; effects_smoke for the directly established agent-duration/token behavior when time is disabled. This finite set does not require a Cartesian matrix or pretend that an empty declaration yields a live item. Do not schedule in effects_smoke/items_smoke/aspatial: SCH44-45 rejects time_enabled=False. Positive capacity must be asserted on the actual selected compiled layout before execution.

## Public genuine construction, without old-world compatibility

From PARENT-FIXTURE-FACTS, the actual compiler is:

```python
from pathlib import Path
from townlet.universe.compiler import UniverseCompiler
compiled = UniverseCompiler().compile(
    Path(pack), primary_level=level, use_cache=False,
)
selected = compiled.get_level(compiled.metadata.primary_level)
env = compiled.create_environment(
    num_agents=N, level_name=compiled.metadata.primary_level, device=device,
    world_roster=roster, training_seed=seed, lane_world_ids=ids,
)
```

Here pack/level/N/seed are one actual row above, ids and roster are the actual identity owner's declared matching membership. Use the existing current real bootstrap/accepted episode/activation/parent PreparedVectorStep/runtime binding supplied externally. Construction does not itself reset or activate. Old smoke tests omit mandatory world arguments, use obsolete reset/step calls and sometimes change N independently of training; those call sites are not a current lifecycle recipe. Their staleness does not invalidate the YAML/catalog/manager facts. No adapter, guessed constructor field or fabricated accepted owner is proposed.

## Actual active effect plus genuinely pending agent work

For enabled-time model_pack/L0_demo, after actual activation/reset, before the first genuine step, the source-backed setup statements are:

```python
manager = env.effect_manager
bars = {name: env.meters[:, col] for name, col in env.meter_name_to_index.items()}
active = manager.spawn_effect(
    effect_id="ate_food", target_entity_id=0, world=0,
    intensity=1.0, current_step=manager.current_step,
    bars=bars, vfs_registry=env.vfs_registry, item_manager=env.item_manager,
)
assert active is not None and active.observable
assert active.duration_remaining == 10 and active.elapsed_ticks == 0
assert active.world == 0 and active.target_entity_id == 0
assert manager.command_executor is not None
assert manager.scheduler.time_enabled
commands = manager.catalog.effects["ate_food"].on_tick
assert commands
manager.scheduler.schedule(
    commands=commands, delay_ticks=10, base_tick=manager.current_step,
    scope="agent", entity_id=0,
    context_overrides={"effect": active}, effect_instance=active.instance_id,
)
due = manager.current_step + 10
pending = tuple(manager.scheduler.pending[due])
assert any(item.scope == "agent" and item.entity_id == 0 for item in pending)
```

No fabricated commands/config/backend: `commands` is the real compiled ate_food on_tick pipeline (`bar.energy + (0.05 * intensity)`), and spawn executes the actual on_spawn `is_digesting=true` through the real executor/registry. Public scheduling is an explicit test setup operation; this is not an assertion that shipped YAML authors a delay block. No executor/compiler body was inspected to qualify a separate DSL-delay construction route. The active object's effect reference supplies intensity and world in future work; agent scope/entity supplies self/target row0 (MAN689-693). No spatial reads/spawns occur in this pipeline, so extra geometry arguments are unnecessary. World0 is agent row0 in current independent single-agent worlds, regardless of its external world ID spelling; no agent-position write is needed. Other worlds remain companions.

For authored terminal setup, the candidate real meter control is `env.meters[0, env.meter_name_to_index["health"]] = 0.001` before a WAIT step. Actual model_pack health depletion .005 and natural recovery .001, lethal_min true, energy and mood initially1: a normal complete tick should terminate row0 without ate_food changing health. Confirm the real terminal result; this is a data/source expectation, not an executed death receipt. Retirement/coincidence use the current ENV owner's already-qualified real retirement controls, not a new effect lifecycle mechanism. Keep the pending due tick strictly after this terminal tick. Resolve WAIT by the actual action-space name, make a full-N long tensor, and submit through the actual prepared parent step contract.

Observe scheduled state at the actual unchanged RWC reward boundary and again after actual ENV return. Require the retained pending item object in scheduler.pending before terminal tail cancellation and absent afterward; filter by scope='agent', entity_id=0, effect_instance=active.instance_id. Require actual newly_terminal/done evidence independently. Confirm a nonterminal companion can retain separately scheduled agent1 work if needed. Do not call cancel/advance/drain/reset from the observer. Tuple/list snapshots alone retain ActiveEffect aliases, so copy scalar lifecycle fields and clone tensor evidence when retaining comparisons.

Require active in manager.effects_in_world(0) at both observation boundaries, observable true, remaining9/elapsed1 after exactly one manager tick, with actual effect token presence1 and nonzero remaining_fraction. Compare the entire actual reward-boundary and returned observations, including terminal row0; also compare the effect block. These two encodings occur after the SAME effect tick, so remaining fraction is unchanged between them, although it decreased from setup. The pending list changes, the active effect survives. Health_boost duration1 cannot serve this control: it expires in the first tick. Do not claim scheduler cancellation removes the active effect or call cancel_effect to manufacture such removal.

## Supported API semantics and observation coordinates

MAN107-148 constructs EffectManager(catalog,device='cpu',command_executor=None,scheduler=None,time_enabled=True); genuine ENV must supply its actual compiled catalog/executor, accessed above through env.effect_manager, not a guessed CompiledUniverse catalog attribute. MAN150-264 spawn_effect has no duration override; duration/observable/reapply/scope come from catalog.effects[id], stable index from catalog.get_effect_index(id). RENEW resets remaining to catalog duration with no hook; merge accumulates intensity without resetting duration. Budget refusal returns None/telemetry. Agent world must equal target row; item effects use the registry item_world(arena_row); global/affordance require explicit world. MAN538-553 exposes schedule_key and cancel_scheduled_for_entity; the latter only invokes scheduler.cancel.

SCH34-67 schedule accepts commands, delay_ticks, scope/entity_id, context_overrides, base_tick and effect_instance. Delay0..1000, total10000 cap. Omitted base_tick anchors scheduler.current_tick; explicit base above removes ambiguity. advance requires a nondecreasing tick and drains only the exact due tick, not all skipped ticks (SCH69-75). Actual contiguous ENV ticks are required. MAN588-656 tick first advances/executes due work, then ticks active effects, then repeatedly drains zero-delay work. MAN730-766 decrements remaining and increments elapsed once per tick; MAN652-655 despawns at <=0. These counters decrement even for a masked dead world; the live mask gates writes, not lifecycle counters. Do not infer frozen duration from the tick docstring's dead-write language.

MAN796-812 get_all_active_effects/effects_in_world enumerate/filter stores without mutation. MAN815-856 cancel_effect separately runs interrupt/removes active; terminal pending cancellation does not call it. SCH77-84 cancellation filters only matching scope/entity and deletes empty pending buckets, without executing commands or mutating retained effect references.

CTX37-68 declares actual ExecutionContext fields, notably bars/vfs_registry/self_index/target_index/effect/self_is_item/target_is_item/effect_manager/item_manager/current_tick/scheduler/write_mask and spatial fields. MAN454-500 builds hook contexts itself; no need to instantiate or write private lifecycle fields. CTX76-132 resolves agent row and world from entity/effect. Public get_path/set_path resolve bar.energy, bare VFS variables, and item.condition with real authorization/liveness. This capsule uses the manager-generated contexts, not a manually simulated tick.

The smoke test240-270 supplies the exact public compact access pattern: layout=env.token_spec.compact_layout().get_type('effect'); slice observation row `[layout.start:layout.start + layout.capacity * layout.compact_row_width]`, reshape(capacity,compact_row_width), dynamic_features.index('remaining_fraction'); presence is column0. Require actual layout capacity and remaining lane; do not invent a fixed offset or include static metadata in the dynamic slice. Full shape/dtype/device and torch.equal assertions remain the external successor contract. Ownership/catalog index/intensity fields come from actual layout dynamic_features and public equality capsule, not guessed numeric columns.

## Companion controls and precise proof limits

Items_smoke already supplies live medkit/medical durability exposure without authoring new schemas. Select the actual registered medkit from real items_in_world(world) and its actual arena row using the already-qualified item owner API; never assume reset RNG puts it at row0 or [0,0]. For an item-effect companion call spawn_effect('wear_and_tear',target_entity_id=actual_row,world=actual_world,intensity=1.0,current_step=manager.current_step,bars=bars,vfs_registry=env.vfs_registry,item_manager=env.item_manager). Duration10 gives remaining9 after a tick; it changes common item.condition, while exposed medkit durability remains the real profile value. This capsule does not inspect or invent item pickup/spawn/move signatures; carried/hidden companions use the named existing item-owner capsule APIs and require actual ownership/visibility evidence. Do not silently treat global-only items_smoke as a partial-vision witness.

For real rollover, compile feedforward with primary L3_temporal_mechanics (not its L0 projection), advance 24 real prepared WAIT steps from tick0 with safe actual meter state, and retain ticks23/24 plus actual clock hour and exposed day_phase token. No direct global_tick/time_of_day write is required. The default bars remain above lethal minima over24 WAIT ticks from initial1; assert continued participation. The day_phase expression is evaluated before both encodings under the external equality contract. Periodic normalization can make values at0 and24 equal, so record tick23 versus24 and the actual registry expression value as well. A changing action-hour mask is a separate output, not observation inequality. This case has no live effect/pending-work witness and does not pretend otherwise.

All recipes are unrun. In particular, presence of shipped model_pack YAML is not a fresh current compiler-success receipt; if it refuses, obtain the exact compiler/config owner correction before claiming this candidate executable, without legacy fallback, synthetic catalog, or bypassing scheduling-disabled checks. No missing constructor body is essential to the established manager/scheduler setup; actual configuration acceptance is the remaining narrow runtime qualification. No claim is made of a single shipped pack containing all positive branches, a hidden/carried-item API not supplied here, callback purity, actual integrated equality, GPU/byte identity, real runtime/provider/replay acceptance, or release closure. Original T18e and all five-family/both-scope obligations remain intact.
