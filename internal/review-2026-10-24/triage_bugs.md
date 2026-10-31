=================== hamlet-0071c78ee9
ID:       hamlet-0071c78ee9
Title:    observable: true does not make a variable observable — it is the mark-and-sweep evaluation selector, and a mark naming no global-profile variable crashes the env at step 1
Status:   triage
Priority: P2
Type:     bug
Parent:   hamlet-15050f280a
Created:  2026-08-21T10:21:34.562453+00:00
Labels:   recovery:WS-4, vfs-gap-analysis
Ready:    YES (no blockers)

--- Description ---
VFS gap analysis G-13 (docs/product/assessments/vfs-gap-analysis-20260821.md). Analyst-attested with executed evidence.

On variables_reference.yaml, observable: true emits NO observation field for any scope (verified for global/agent/agent_private/pair/affordance; total_dims unchanged). Its only function: enter vfs_observation_marks, consumed as the mark-and-sweep evaluation set for the GLOBAL PROFILE — a different file's variables (see the G-2a ticket). The two roles collide: a mark naming no global-profile variable is KeyError 'VFS mark(s) not found in profile' at step 1. extract_observation_marks silently drops pair/group/affordance/zone/message marks. A key named 'observable' whose function is 'evaluate this, and crash if you cannot find it' — misnamed, cross-file, and load-bearing.
=================== hamlet-0268336cd1
ID:       hamlet-0268336cd1
Title:    env.reset() does not restore a global VFS variable's declared initial_value, and there is no declarative way to say 'episode-scoped global'
Status:   triage
Priority: P2
Type:     bug
Parent:   hamlet-15050f280a
Created:  2026-08-21T08:00:24.129720+00:00
Labels:   prd-0001-trial, recovery:WS-4
Ready:    YES (no blockers)

--- Description ---
Found by the Trial B tensorNd evidence audit (B-tensornd-audit-20260821.md, gap A-G7); independently reproduces the blind run's G-10.

Measured: grow the container to 243 occupied cells, call env.reset(), read back — still 243. lifetime: persistent is doing exactly what it says. The gap is that there is no declarative alternative: an author cannot say 'this global is episode-scoped and resets with the episode'.

RELATED, SAME FAMILY, DIFFERENT MECHANISM: hamlet-d76684f549 (effects survive env.reset() with elapsed_ticks continuing). That one is about spawned effects; this one is about global VFS variables. Together they are the 'what survives the episode boundary, and can an author declare it?' question that docs/product/current-state.md has carried as an open question across three reproductions.

Bears on facet B-F3 (rooted-at-a-declared-origin) and is FLAGGED, NOT SCORED — the audit's scope was B-F2 only. NOT FIXED — substrate freeze.
=================== hamlet-02bd5a3eaa
ID:       hamlet-02bd5a3eaa
Title:    zone scope is dead vocabulary: declared in VariableScope, no manager, no runtime consumer (Trial B by-catch)
Status:   triage
Priority: P2
Type:     bug
Parent:   hamlet-15050f280a
Created:  2026-08-18T15:25:37.125604+00:00
Labels:   prd-0001-trial, recovery:WS-4
Ready:    YES (no blockers)

--- Description ---
VariableScope.ZONE ('Per-zone state [num_zones, ...]', vfs/schema.py:40) is accepted in variable declarations but no ZoneManager or zone runtime exists anywhere in src/townlet/ — same dead-vocabulary shape as CapabilityConfig (hamlet-6b24c0bd83). Assessed by source read during Trial B surface scouting (not hit in-pack, so not counted as an encountered INERT surface). Idea K (world-acts-on-agent) pre-registers zone scope as a doubted surface — this issue is the evidence it will hit. Record: docs/product/trials/0001/B-20260819.md.
=================== hamlet-17a7f03bc9
ID:       hamlet-17a7f03bc9
Title:    A broken tool and an empty hand encode identically (0.0): the item-slot observation cannot distinguish 'no item' from 'item at zero' (Trial F evidence audit)
Status:   triage
Priority: P2
Type:     bug
Parent:   hamlet-15050f280a
Created:  2026-08-19T16:24:34.731578+00:00
Labels:   prd-0001-trial, recovery:WS-4
Ready:    YES (no blockers)

--- Description ---
Found by the Trial F EVIDENCE AUDIT (docs/product/trials/0001/F-evidence-audit-20260820.md), commissioned 2026-08-20 to test whether Trial F's PASS survived protocol amendment B.3. It does; this is by-catch, and it is the one place where the letter and the spirit of Trial F's facet 4 diverge.

THE SHAPE: the wear value occupies one observation slot. A tool worn to zero reads 0.0 at that offset. An agent holding NO tool also reads 0.0. The agent cannot tell 'my tool is broken' from 'I have no tool' -- two states that call for opposite actions (repair/replace vs acquire).

WHY IT IS FILED RATHER THAN LEFT: this is not a reward-hacking artefact of the kind CLAUDE.md protects as an interesting failure. It is an AUTHORING surface question -- an author who declares an item-scoped variable with a meaningful zero has no declarative way to say 'absent' distinctly from 'zero', and the substrate offers no presence bit alongside the value. That is a gap in the declarative grammar, not an emergent behaviour worth preserving.

RELATED: same observation-encoding family as hamlet-bf42ac60b5 (raw/unnormalized item-slot values). Consider triaging together.
=================== hamlet-1b9af9088c
ID:       hamlet-1b9af9088c
Title:    spawn_item is unreachable end-to-end from config: DTOs refuse coordinate positions, no runtime pipeline passes agent_positions (Trial B, BLOCKED)
Status:   triage
Priority: P1
Type:     bug
Parent:   hamlet-15050f280a
Created:  2026-08-18T15:25:14.235491+00:00
Labels:   prd-0001-trial, recovery:WS-4
Ready:    YES (no blockers)

--- Description ---
Trial B (docs/product/trials/0001/B-20260819.md) established that the entire spawn_item effects command — documented in effects.md as 'fully implemented and production-ready' — cannot execute from any declarative surface. (1) Parse: CommandConfig.position and the affordance DTO type position as str, so explicit coordinates ([x,y,...]) are refused at parse and the executor's explicit-coordinate branch (executor.py:276) is dead from YAML. (2) Runtime: the string strategies self/target/random all require context.agent_positions, and NO production pipeline supplies it — affordance_engine._execute_affordance_effects builds its context without positions, effects/manager.py _tick_effect drops the parameter tick() accepts, items/action_handlers.py omits it, and the one production call site vectorized_env.py:1036 calls effect_manager.tick() without agent_positions even though the whole subsystem threads the parameter ('NEW: for for_each spatial queries'). (3) The random strategy additionally hardcodes 2-D (dx,dy) in items/manager.py find_spawn_location. Tests pass only because they hand-construct CommandNode position lists and hand-supply agent_positions — supplying what the runtime never does. No shipped pack uses spawn_item. Verbatim refusals recorded in the Trial B record appendix. This BLOCKED the trial's facets 2 and 3 (durable creep-trail footprint).
=================== hamlet-266a0a41f0
ID:       hamlet-266a0a41f0
Title:    An agent cannot observe its own multi-tick interaction progress, and no config pack can declare it
Status:   triage
Priority: P2
Type:     bug
Parent:   hamlet-1ade187dcc
Created:  2026-08-15T21:28:42.945793+00:00
Ready:    YES (no blockers)

--- Description ---
FOUND 2026-08-16 while repairing hamlet-551be983a8.

## The shape

`env.interaction_progress` is a live engine tensor (`environment/vectorized_env.py:351`) that advances 1..duration-1 through a multi-tick interaction and resets to 0 on completion. It is **not observable**:

- the temporal observation block is exactly 4 features — `observation_encoder._build_temporal_observation` raises unless `dims == 4`, and fills sin / cos / day_progress / is_night
- `interaction_progress` has no VFS variable (`grep` in `src/townlet/vfs/` finds only the VTC program that ADVANCES it, never a declared variable)
- there is no observation mark for it in any pack

So an author cannot write config that lets an agent see how far through an interaction it is. The only way to get it is to edit Python — the shape `CLAUDE.md` calls a product defect rather than a shortcut.

## Why it is more than cosmetic

A multi-tick interaction the agent cannot observe is partially-observable *with respect to the agent's own action state*. An agent 3 ticks into a 5-tick SLEEP has no signal distinguishing that from tick 1; the completion bonus is therefore unlearnable except through recurrent memory. On the full-observability levels (L0/L0.5/L1, `SimpleQNetwork`, no LSTM) there is no memory at all, so it is strictly unlearnable there.

Note this is a *latent* gap in the shipped packs, because no shipped affordance is multi_tick. It bites the moment one is authored.

## Evidence

`tests/test_townlet/integration/test_temporal_mechanics.py::test_interaction_progress_is_tracked_but_not_observable` asserts BOTH halves: that progress advances as engine state, and that its value appears nowhere in the observation. That test was previously `test_interaction_progress_in_observations` and read `obs[0, -2]`, expecting `progress / 10.0` — an observation layout that no longer exists.

The test is written so it FAILS if progress becomes observable, which is the signal to close this issue.

## Direction (not a decision)

Either declare it as a VFS agent-scoped variable with an observation mark so a pack can opt in, or record deliberately that progress is hidden state and the recurrent path is the intended way to recover it. The first is the framework-shaped answer.
=================== hamlet-2aca57c0f0
ID:       hamlet-2aca57c0f0
Title:    Token indistinguishability refusal has no declared-parameter escape hatch: payload-identical entities cannot be distinguished by any authoring surface
Status:   triage
Priority: P1
Type:     bug
Created:  2026-08-26T05:17:18.890739+00:00
Ready:    YES (no blockers)

--- Description ---
Surfaced by Task 10 (unit-3 cut). Spec §1's compile-time indistinguishability check refuses when two declarations share a static payload signature and coordinate space. Explicit exposure fired it on 8 shipped packs; the implementer deleted those duplicates ONLY after proving every one inert (referenced nowhere in any pack or in src/) — that is PDR-0066 dead-declaration cleanup, NOT reversal trigger 4. The open architectural gap: the next author's duplicates will NOT be inert, and there is currently no declared parameter that can distinguish two genuinely-different entities that happen to carry identical declared payloads. That is a hard authoring block with no config-level answer, which is the defect shape CLAUDE.md names as load-bearing. Needs a declared discriminator (an author-supplied identity/tag that participates in the payload signature) or an explicit, recorded decision that payload-identity IS entity-identity in this model. Decide before an author hits it.
=================== hamlet-2ca2cb373f
ID:       hamlet-2ca2cb373f
Title:    Engine/VTC writeback never validates against the declared schema: set_engine_value skips declaration shape/dtype checks and VTC write expressions anchor to phase-snapshot shapes
Status:   triage
Priority: P2
Type:     bug
Parent:   hamlet-15050f280a
Created:  2026-08-21T11:11:47.122901+00:00
Labels:   recovery:WS-4
Ready:    YES (no blockers)

--- Description ---
Files the general case behind hamlet-57a5126baa (now closed): the effects route commits through registry.set with full declared-schema validation, but the engine/VTC writeback route never consults the declaration at all. Recorded as the doc's own remaining-work item: docs/architecture/vfs.md §6.3 ("The unvalidated path is set_engine_value(), which the engine/VTC writeback uses") and §21.1 item 4.

THE CHAIN, verified at this tree:

1. VTC write expressions are validated only against the PHASE SNAPSHOT, never the declared schema. vtc.py:851 _coerce_expression_tensor checks value.shape against target.shape where target = phase_snapshot[write.variable_id] (vtc.py:485) — i.e. whatever storage currently holds — and COERCES dtype to the snapshot's dtype rather than validating it. Same pattern at the social-residue variant (vtc.py:1516).

2. The commit path skips declaration checks by design. registry.py:567 set_engine_value checks existence and engine write permission, validates shape ONLY for sparse pair variables, and coerces dtype via .to(dtype=expected_dtype). Both production call sites go through it: the evaluator writeback (vectorized_env.py:1084) and EVERY VTC phase commit (_commit_vtc_transition_state, vectorized_env.py:1207).

3. The carve-out that motivates the bypass is itself the drift vector. The docstring's stated reason: expressions on variables declared as global scalars can legitimately produce per-agent batches when they read batched bar state. So a variable declared scope: global, type: scalar can hold a (num_agents,) tensor at runtime — the declaration is not an invariant. Once storage has drifted, the phase-snapshot anchor in (1) validates FUTURE writes against the drifted shape, so the declared schema can never pull state back.

WHY IT MATTERS BEYOND TODAY: every future rule source that compiles into a VTC phase inherits this path. The declared schema is the authoring contract (No-Defaults Principle: the declaration is what the author reasoned about); a write surface that never checks it means a compiler bug or a bad write expression corrupts storage silently and the corruption becomes the new validation anchor.

SHAPE OF A FIX (not prescribed): either (a) make declared scope/shape win at writeback — resolve the batched-global carve-out the same way hamlet-cf16cdb6c4 resolved reads (declared scope wins; a batched result for a declared-global scalar is a compile error or an explicit reduction, not a silent storage widening), then set_engine_value can validate like registry.set; or (b) land declared-schema validation in the clamp_and_validate transition phase — the declared-but-empty phase tracked by hamlet-f46e2b381a, whose name promises exactly this "validate" half. Sequence with that ticket either way.

Related: hamlet-57a5126baa (effects route, closed — the contrast case), hamlet-cf16cdb6c4 (declared-scope-wins precedent), hamlet-f46e2b381a (clamp_and_validate phase).
=================== hamlet-2dde1015fe
ID:       hamlet-2dde1015fe
Title:    The dead-hash set is NINE, not four: five pack-level hashes are computed, serialized and compared by nobody
Status:   triage
Priority: P2
Type:     bug
Created:  2026-08-11T17:46:58.739357+00:00
Labels:   WS-1, inert-surface, provenance
Ready:    YES (no blockers)

--- Description ---
Found by task 4 recon (2026-08-12), out of that task's scope.

Task 4 (`04a59114`) closed the four PER-LEVEL content hashes — `curriculum_hash`, `bars_hash`, `affordances_hash`, `training_hash`. Recon found the same defect in five more, at PACK level:

  experiment_hash    compiler.py ~:200   computed, stored, serialized, round-tripped — never compared
  stratum_hash       compiler.py ~:201   "
  environment_hash   compiler.py ~:202   "
  actions_hash       compiler.py ~:203   "
  items_hash         compiler.py ~:204   " (nullable when the pack declares no items)

All five follow the identical shape the four just fixed: computed by `_compute_pydantic_hash`, carried on `CompiledUniverse`, written to the msgpack artifact, presence-required on load — and never compared against a checkpoint by anything.

**Consequence.** A change to `stratum.yaml` (the substrate — grid size, topology, boundary mode), `environment.yaml` (VFS variable declarations), or `actions.yaml` (the action vocabulary) does not reject a checkpoint on its own account. Some of these are caught indirectly: a grid change usually moves `observation_schema_hash`, and an action change usually moves `action_schema_hash`. But that is incidental coverage, not a guarantee, and `experiment_hash` has no proxy at all.

**Related, from the same recon:** `attach_universe_metadata` stamps SIX fields nothing compares, not four — `meter_count` and `observation_schema_hash` are stamped and never checked either. Worth folding into the same unit.

**Suggested shape** — identical to task 4, and cheap now that the pattern exists:
1. add the five to the top-level projection where they are missing;
2. stamp them in `attach_universe_metadata`;
3. hard-compare them in `assert_checkpoint_dimensions`, copying the `drive_hash` pattern (missing on either side RAISES — do NOT copy an `if x is not None` escape);
4. one pinning test per hash with the six-leg template from `tests/test_townlet/integration/test_content_hash_checkpoint_guard.py`.

Note `items_hash` is legitimately None for packs with no items, so it needs the nullable treatment rather than a hard raise — that is the one real design question in the set.

Sequence AFTER the oracle freeze unless WS-1 is still open, per PDR-0014's reversal trigger 2 (batch growth delaying the freeze). Related: `hamlet-ae6601e463` (task 4, the four), PDR-0008.

--- Fields ---
  severity: major
  component: checkpoint provenance hashing
  expected_behavior: All authoritative pack and schema hashes stamped into checkpoint metadata are compared fail-closed at load.
  actual_behavior: Five pack hashes plus meter_count and observation_schema_hash are produced and serialized but never compared.
=================== hamlet-310e336786
ID:       hamlet-310e336786
Title:    AdversarialCurriculum hardcodes the life-sim's bar vocabulary into the engine (game-engine residue)
Status:   triage
Priority: P2
Type:     bug
Parent:   hamlet-1ade187dcc
Created:  2026-08-12T15:54:28.836467+00:00
Labels:   authoring-surface, from-observation, package:townlet, recovery:WS-4
Ready:    YES (no blockers)

--- Description ---
Promoted before its 2026-08-25 expiry — this is the strangler's selection criterion made literal (PDR-0019: "strangle wherever the runtime still knows what the game is"), same defect class as the hardcoded torch.clamp(0,1) WS-1 fixed. Routed to WS-4 per PDR-0028's fence: authoring-surface-shaped, does not corrupt artifacts today.

Promoted observations:
- AdversarialCurriculum hardcodes the life-sim's bar vocabulary into the engine (game-engine residue)
  Detail: Five curriculum stages in src/townlet/curriculum/adversarial.py:31-59 hardcode active_meters=["energy", "hygiene", "satiation", "money", "mood", "social"] — the default_curriculum universe's bar names, baked into runtime logic rather than authored in a config pack. A universe that does not have these bars cannot use the adversarial curriculum at all.

Same defect CLASS as the hardcoded torch.clamp(meters, 0.0, 1.0) found in WS-1: the runtime asserting a fact about one particular universe. Owner's framing (2026-08-11): "the original 'game engine' needs to be strangled out by the engine engine" — VFS and the dynamic engine parts are the guiding star, not 'health = 0..100'.

Scope note: WS-4 (close the authoring surface), NOT WS-1. Filed so it is not lost; do not fold into the WS-1 batch.

Measured context: 95 hardcoded bar-name string references across src/townlet (energy 41, money 12, hygiene 10, health 9, satiation 9, mood 8, social 4, fitness 2). Most are docstrings/examples (vfs/registry.py, training/state.py); adversarial.py is the one confirmed to be live logic. A full logic-vs-docstring triage of the remainder has NOT been done.
  Location: `src/townlet/curriculum/adversarial.py:31`
  Observed while working on: hamlet-15050f280a
  Observation ID: hamlet-obs-334e99ffdb

--- Fields ---
  source_observation_ids: ['hamlet-obs-334e99ffdb']
  severity: major
  component: adversarial curriculum authoring
  expected_behavior: Curriculum stages derive their active variable vocabulary from authored configuration and work with arbitrary universes.
  actual_behavior: Five stages hardcode six life-simulation meter names, preventing other universes from using the curriculum.
=================== hamlet-3381043d2e
ID:       hamlet-3381043d2e
Title:    Action writes are unreachable from config: ActionsCompiler hardcodes writes=() and no WriteSpec is ever constructed from any YAML surface (Trial O blind re-run)
Status:   triage
Priority: P2
Type:     bug
Parent:   hamlet-15050f280a
Created:  2026-08-19T15:20:41.291327+00:00
Labels:   prd-0001-trial, recovery:WS-4
Ready:    YES (no blockers)

--- Description ---
Found by the Trial O blind re-run (gap G-1) and INDEPENDENTLY VERIFIED at HEAD before filing.

MEASURED:
- 'WriteSpec(' appears exactly 3 times under src/townlet/, ALL in src/townlet/vfs/schema.py (the class definition at :220 and two docstring examples at :231/:243). No production code path constructs one.
- src/townlet/universe/compilers/actions.py:205 hardcodes 'writes=()' when building the runtime action space.
- ActionConfig (src/townlet/environment/action_config.py:84) DOES declare 'writes: list[WriteSpec]' with a description ('Variables this action writes with expressions'), so the field exists on the model and is never populated from a pack.

Classification ABSENT: the declared capability exists in the schema and is reachable from no config file.

CORRECTION TO THE SOURCE REPORT: the blind record attributes the refusal to a class named 'CustomActionConfig' forbidding a writes key. There is no CustomActionConfig in action_config.py (the classes are ActionConfig and ActionSpaceConfig) and the writes field is present rather than forbidden. The substantive finding -- hardcoded writes=() plus zero WriteSpec construction -- holds and is what is filed here.

RELATED: this is the same shape as hamlet-1b9af9088c (spawn_item) and hamlet-a737e444c0 (effects blind to position/time) -- the grammar declares a capability the execution path never threads data for. Candidate for triage as ONE unit rather than three tickets.
=================== hamlet-4597fd5d04
ID:       hamlet-4597fd5d04
Title:    environment.yaml variables are hardcoded lifetime: tick — no accumulator, counter, or cooldown can survive a step on this surface, and no key changes it
Status:   triage
Priority: P2
Type:     bug
Parent:   hamlet-15050f280a
Created:  2026-08-21T10:21:03.775916+00:00
Labels:   recovery:WS-4, vfs-gap-analysis
Ready:    YES (no blockers)

--- Description ---
VFS gap analysis G-7 (docs/product/assessments/vfs-gap-analysis-20260821.md). Analyst-attested with executed evidence (four consecutive interactions: env-var stays 5.0 while the agent-profile control accumulates 5/10/15/20).

compilers/observation.py:866 hardcodes lifetime='tick' for every environment.yaml variable; reset_tick_scoped() runs at the top of every step(). The write lands and IS observed within the same tick, so the surface is not useless — but every cross-tick accumulator silently resets. configs/simple names its env vars time_since_last_sleep / time_since_last_doctor / time_since_last_cook — exactly the shape that cannot work here. Same family as hamlet-0268336cd1 (lifetime hardcoded 'persistent' on vfs_profiles.yaml) — the two surfaces hardcode OPPOSITE lifetimes and neither is declarable; the shared fix is one declarable lifetime key.
=================== hamlet-45f501e15b
ID:       hamlet-45f501e15b
Title:    max_items_per_agent: 0 silently nullifies the entire items catalog at load (Trial B, INERT surface)
Status:   triage
Priority: P2
Type:     bug
Parent:   hamlet-15050f280a
Created:  2026-08-18T15:25:36.780267+00:00
Labels:   prd-0001-trial, recovery:WS-4
Ready:    YES (no blockers)

--- Description ---
raw_configs_v21.py:152: if max_items_per_agent == 0 or max_items_in_world == 0, the loaded items catalog is silently replaced with None — no error, no warning. The declared item types, interactions and profiles all validate and then simply do not exist; the first symptom is a misleading UAC-RES-ITEM 'unknown item_type' from the level appearance file two stages later. A pack author declaring carry-nothing worlds (items as pure world state, exactly Trial B's creep) gets the whole items system turned off. Violates the fail-loud principle; INERT-class silent surface (counts toward the published INERT surface tally, A.7). Record: docs/product/trials/0001/B-20260819.md authoring log step 4.
=================== hamlet-4b931faaf4
ID:       hamlet-4b931faaf4
Title:    Held/exclusive items are invisible to the entire item token type: lift_item removes the row, so a carried item's presence, coordinates and item-arena state never reach the observation
Status:   triage
Priority: P1
Type:     bug
Parent:   hamlet-15050f280a
Created:  2026-09-02T01:20:18.344597+00:00
Labels:   package:townlet, recovery:WS-4
Ready:    YES (no blockers)

--- Description ---
Measured during token unit 5 (hamlet-55b2826a02), while wiring the item-arena
`variable_element` publisher (ItemArenaVariableElementPublisher, unit-3 Task 8) for the
first time via compile emission.

CODE PATH: `VectorizedHamletEnv._item_slot_batch()` builds the ItemSlotBatch every publish
tick from `ItemManager.get_all_items()`, which returns only `self.active_items.values()`
(world-resident items). `ItemManager.lift_item()` — called for every EXCLUSIVE item on
pickup (`exclusive: bool = True` is the default on ItemInstance/item type config, so this
is the common case, e.g. items_smoke's medkit) — pops the item out of `active_items` into
`held_items` entirely. `held_items` has no reader anywhere in the observation path. The
SAME ItemSlotBatch feeds both the plain `item` token type (ItemTokenPublisher) and the
item-arena half of `variable_element` (ItemArenaVariableElementPublisher), so this is not
scoped to item-profile state: a carried exclusive item's position, egocentric delta,
carried flag, owner-slot coordinate, AND any exposed item-profile variable (e.g.
`medical.durability`) all vanish from the observation the instant GET-style pickup lifts
it out of the world, even though the item instance and its VFS state still exist
(`item.vfs_index` is preserved, `ItemManager.despawn_item` is what finally unregisters it).

DEMONSTRATED (not merely asserted) at
tests/test_townlet/integration/test_item_vfs_observations.py::test_exposed_item_variable_publishes_through_the_item_arena
— the test spawns a second medkit directly into the world (proving presence/value/
normalization on the item-arena scope's own terms), then calls
`env.item_manager.lift_item(spawned.instance_id)` on that same instance and asserts the
durability row goes back to absent (`present_count(after_lift) == baseline`), with an
in-code comment naming this as a pre-existing, out-of-scope gap.

CONTEXT (why this task didn't fix it): the brief's own literal test used the existing
`spawn_and_pickup_item` helper, which performs a full GET-style pickup (add to inventory +
lift_item for exclusive items). Running it against the real items_smoke pack showed the
newly-picked-up medkit's durability row never appears at all -- not merely "already
counted", but structurally absent -- because ItemSlotBatch has no held-item source. The
harness's `items_smoke:L0_smoke` run this task landed shows the shape of what CAN move
today: obs shape [4, 61] -> [4, 474] (39 dims added = 13 item-token-capacity slots x
(presence + value_0 + value_1), all from WORLD-resident durability rows) -- none of that
growth, and none of the existing `item` token rows, will ever reflect a held exclusive
item.

FIX SHAPE (not designed here, scoping only): ItemSlotBatch (token_publishers.py) is
world-shared, `[K]`, with `carried: [N, K] bool` as its only per-world axis -- it has no
per-agent-inventory-slot axis at all. Representing held items requires either (a) folding
`ItemManager.held_items` into the same batch with a coordinate that survives per-agent
inventory-slot identity (the existing but currently-dead `+ max_items_per_agent x
agents_per_world` headroom in the compiled `item` token capacity formula --
token_spec.py's `item_capacity()` -- looks like it was sized for exactly this), or (b) a
second, inventory-scoped ItemSlotBatch and either a third publisher or an extended
ItemTokenPublisher. Either shape moves `layout_hash` on every items-catalog pack, not just
items_smoke -- not a minimal fix, hence filed as its own issue rather than folded into
hamlet-55b2826a02.
=================== hamlet-4cd664a955
ID:       hamlet-4cd664a955
Title:    An effect's declared scope is ignored at spawn: every spawn path hardcodes agent scope, so 'scope: global' validates, compiles, and silently attaches per-agent — EffectManager.global_effects is reachable from no YAML
Status:   triage
Priority: P2
Type:     bug
Parent:   hamlet-15050f280a
Created:  2026-08-18T12:36:13.482697+00:00
Labels:   prd-0001-trial
Ready:    YES (no blockers)

--- Description ---
Found by Trial O (adversarial bidding, PRD-0001). EffectDefinitionConfig accepts scope: global|agent|item|affordance and the compiler validates it, but _execute_spawn_effect (src/townlet/effects/executor.py:228-231) passes scope=EffectScope.AGENT unconditionally — the comment says 'scope hardcoded to AGENT for now (can extend later)'. The manager's global_effects list, its tick loop (manager.py:375-379) and GLOBAL despawn handling all exist and work, but no YAML can reach them: a 'scope: global' effect definition is INERT in its scope declaration — it spawns agent-scoped with agent-death despawn semantics instead of world-lifetime semantics. Trial O worked around it by declaring the auction-house clearing effect agent-scoped and pinning it to slot 0 via target: "0" from the spawning affordance. INERT classification per PDR-0079: the surface exists, validates, and its declared meaning has no observable effect.
=================== hamlet-53bce4af41
ID:       hamlet-53bce4af41
Title:    inspect --format json cannot report observation fields or offsets: an author cannot ask the compiled artifact where a declared variable landed without writing Python (Trial O blind re-run)
Status:   triage
Priority: P2
Type:     bug
Parent:   hamlet-15050f280a
Created:  2026-08-19T15:20:40.923975+00:00
Labels:   prd-0001-trial, recovery:WS-4
Ready:    YES (no blockers)

--- Description ---
Found by the Trial O blind re-run and INDEPENDENTLY VERIFIED at HEAD before filing.

MEASURED (configs/default_curriculum, L1_full_observability):
  inspect --format json top-level keys: ['action_schema_hash','artifact','metadata','observation_schema_hash','transition_graph_hash','variable_schema_hash','vfs_hash']
  metadata keys: action_count, affordance_count, affordance_id_to_index, affordance_ids, compiled_at, compiler_git_sha, compiler_version, config_hash, config_mtime, config_version, economic_balance, grid_cells, grid_size, max_sustainable_income, meter_count, meter_name_to_index, meter_names, observation_dim, position_dim, primary_level, provenance_id, pydantic_version, python_version, schema_version, substrate_type, ticks_per_day, torch_version, total_affordance_costs, universe_name
  observation-related keys: ['observation_dim'] = 124  (a SCALAR)

There is no field list, no field names, no per-field offsets, no activity mask. meter_name_to_index exists for meters; nothing equivalent exists for VFS/profile variables or item slots.

WHY IT MATTERS FOR THE PRODUCT: 'I declared a variable -- where does it appear in the observation?' is a first-order authoring question. The documented inspection surface cannot answer it. Every trial to date has answered it by importing UniverseCompiler in a hand-written probe, i.e. by writing Python -- the exact thing the product exists to remove.

COLLATERAL: the PRD-0001 trial protocol's own section 4 worked example ('inspect --format json shows an observation field for the wear variable') is NOT EXECUTABLE as written. Both Trial O executors pre-committed that command and both silently substituted the in-process CompiledUniverse object. Routed to the owner as a protocol-amendment question in docs/product/trials/0001/O-comparison-20260820.md (AM-3); this ticket is the PRODUCT half only.
=================== hamlet-559cc74246
ID:       hamlet-559cc74246
Title:    Item tokens carry no declared identity: three distinct item types in a shipped pack emit byte-identical tokens apart from position
Status:   triage
Priority: P1
Type:     bug
Created:  2026-08-26T05:49:45.929375+00:00
Ready:    YES (no blockers)

--- Description ---
Found by the Task-10 capability review. Pre-cut, ItemVFSVariableConfig.default_metadata injected exposed_to=['agent'] when absent (4a313b28:config/vfs_profiles_config.py:319-327). The cut deleted that fail-open, so EVERY item-profile variable in the fleet that relied on it lost exposure SILENTLY — unlike trial_f_durability, whose exposure was explicit and therefore produced a visible refusal. LIVE IN A SHIPPED PACK: configs/test/items_smoke declares apple/medkit/coin across three profiles with food.freshness and medical.durability exposed only by that default; all three item types now emit byte-identical tokens apart from position. 'item' is the only live token type with no static identity block, so nothing else distinguishes them. NB the Task-10 report's 'Exposure removed — 1 pack' line names only trial_f_durability and therefore undercounts this class. Decide: an identity block in the item payload (declared type/tag participating in the payload signature), or explicit re-exposure in every affected pack. Relates to hamlet-2aca57c0f0 (the same missing-discriminator theme on the affordance/variable_element side).
=================== hamlet-5f99e89865
ID:       hamlet-5f99e89865
Title:    environment.yaml variables hardcode lifetime=tick — declared counters/accumulators silently reset every step
Status:   triage
Priority: P2
Type:     bug
Created:  2026-08-22T12:33:55.938870+00:00
Ready:    YES (no blockers)

--- Description ---
Round-2 VFS review (systems S8). environment.yaml variables are hardcoded lifetime='tick'; configs/simple/environment.yaml declares time_since_last_sleep / time_since_last_doctor — exactly the accumulator shape that silently resets each step. Global-profile variables are hardcoded 'persistent' (episode-scoped globals undeclarable — related hamlet-0268336cd1). The one surface that CAN declare lifetime (variables_reference.yaml) is isolated from affordances/effects/drive references (symbol-table exclusion). Silent wrong-behavior, not a crash.
=================== hamlet-628e202bf7
ID:       hamlet-628e202bf7
Title:    Item on_drop is INERT: parsed, compiled and dispatchable, but no call site ever invokes it (Trial K, INERT surface)
Status:   triage
Priority: P2
Type:     bug
Parent:   hamlet-15050f280a
Created:  2026-08-19T08:12:54.174400+00:00
Labels:   prd-0001-trial
Ready:    YES (no blockers)

--- Description ---
Trial K declared an `on_drop` hook on the coat to return the incoming cold to its unmitigated magnitude when the garment is removed (countersigner boundary case 10, unequip residual).

It validates, compiles, and does nothing.

    after GET : insulation_worn=0.0000
    after USE : insulation_worn=0.6000   <- on_use FIRED, so the hook path works
    after DROP: insulation_worn=0.6000   <- on_drop did not fire

items.yaml declared:
    on_drop:
      - modify: target.bar.insulation_worn
        value: "0.0"

WIRING. `items/manager.py:103` builds on_drop_configs, `:51` stores compiled_on_drop, and `items/action_handlers.py:65` types the interaction Literal as on_pickup|on_use|on_drop with a dispatch branch at :93 returning compiled_on_drop. But the only call sites are:
    action_handlers.py:184  interaction="on_pickup"
    action_handlers.py:227  interaction="on_use"
`grep -rn 'interaction="on_' src/townlet/` returns exactly those two. `handle_drop_slot_action` (:346) never invokes the hook it compiles.

This is the INERT signature exactly: a surface that exists, validates, compiles, and produces no observable effect — the worst kind of debt for a declarative product. The author gets no error; the mechanic silently does not happen.

Counts as INERT SURFACE by-catch #4 for the corpus (after recovery.natural hamlet-d45331a367, effect scope: global hamlet-4cd664a955, max_items_per_agent: 0 hamlet-45f501e15b).

Evidence: docs/product/trials/0001/K-20260819.md; probe configs/trial_k_cold/probe_trial_k.py.
Route: WS-4. File-never-fix held.
=================== hamlet-6b24c0bd83
ID:       hamlet-6b24c0bd83
Title:    The capability vocabulary (cooldown, meter_gated, prerequisite, probabilistic, skill_scaling) is dead code: no YAML surface reaches CapabilityConfig
Status:   triage
Priority: P2
Type:     bug
Parent:   hamlet-15050f280a
Created:  2026-08-18T06:40:34.228662+00:00
Labels:   prd-0001-trial
Ready:    YES (no blockers)

--- Description ---
Found by Trial L (PRD-0001, record docs/product/trials/0001/L-20260818.md, pin fb8c6148). config/capability_config.py declares six capability DTOs including CooldownCapability (type: cooldown, cooldown_ticks, scope agent|global) — a purpose-built surface for exactly the mechanic Trial L measured. MEASURED: grep finds zero imports of CapabilityConfig/CooldownCapability anywhere in src/townlet outside the module itself; AffordanceConfig (affordances_v2_config.py) has no capabilities field, and extra=forbid means a pack declaring one is refused at parse. So the vocabulary is unreachable from any pack — dead declared surface, not INERT (it cannot even validate). Trial L built cooldowns from depletion.passive: -1.0 + if-gated interactions instead, which works. WS-4/PDR-0005 call: wire capabilities onto the affordance schema, or delete the module (zero-backcompat). Note docs/config-schemas/effects.md Example 8 documents an affordance-scope on_cooldown pattern that also has no runtime gate consulting it (AffordanceEngine gates only on can_afford/opening hours).
=================== hamlet-6c49488b22
ID:       hamlet-6c49488b22
Title:    Item appearance fixed placement is typed 2-D only: N-D packs cannot statically place items (Trial B, ABSENT)
Status:   triage
Priority: P2
Type:     bug
Parent:   hamlet-15050f280a
Created:  2026-08-18T15:25:36.439336+00:00
Labels:   prd-0001-trial, recovery:WS-4
Ready:    YES (no blockers)

--- Description ---
SpawnPlacementConfig.fixed_positions is list[tuple[int, int]] (items_config.py:323) — a 5-tuple is refused at parse ('Tuple should have at most 2 items'). DeploymentConfig.positions for AFFORDANCES is list[list[int]] and accepts N-D fine (Trial B used 5-D fixed affordances successfully) — the two placement surfaces disagree about dimensionality for no declared reason. On any gridnd pack, items can only spawn_position: random. Record: docs/product/trials/0001/B-20260819.md.
=================== hamlet-787aaa29f1
ID:       hamlet-787aaa29f1
Title:    Item variable of a list type crashes at spawn_item, not compile — and item observation width (2-3 dims) permanently disagrees with storage width (1 column)
Status:   triage
Priority: P2
Type:     bug
Parent:   hamlet-15050f280a
Created:  2026-08-21T10:21:03.425931+00:00
Labels:   recovery:WS-4, vfs-gap-analysis
Ready:    YES (no blockers)

--- Description ---
VFS gap analysis G-6 (docs/product/assessments/vfs-gap-analysis-20260821.md). Analyst-attested with executed evidence.

ItemVFSVariableConfig admits vec2i/vec3i; VFSObservationSpec sizes them at 2/3 observation dims; item_vfs storage gives every variable exactly ONE f32 column; ItemManager.spawn_item (items/manager.py:358) does float(compiled_var.initial_value) -> TypeError: float() argument must be a string or a real number, not 'list'. Compiles, constructs, survives reset(), dies at first spawn of that item type. Even absent the crash, the width disagreement is permanent: the extra observation columns can never be anything but zero. Adjacent to hamlet-bf42ac60b5 / hamlet-17a7f03bc9 but a distinct defect.
=================== hamlet-7eadeb214c
ID:       hamlet-7eadeb214c
Title:    effects.md omits the entire for_each collection vocabulary that makes engine-ticked effects authorable, and calls it 'future' while it ships
Status:   triage
Priority: P2
Type:     bug
Parent:   hamlet-7a52a63e0b
Created:  2026-08-19T15:20:41.653320+00:00
Labels:   prd-0001-trial, recovery:WS-4
Ready:    YES (no blockers)

--- Description ---
Found by the Trial O blind re-run (gap G-8, doc-truth half) and INDEPENDENTLY VERIFIED at HEAD before filing.

MEASURED occurrence counts in docs/config-schemas/effects.md:
  all_agents  0
  switch      0
  delay       0
  sample      0
  reduce      4
  parallel    1

'for_each: all_agents' is the LOAD-BEARING surface both Trial O executors independently converged on -- it is how a declarative clearing step over simultaneous agent submissions is expressed at all -- and the schema doc for effects does not mention it once. The doc additionally describes for_each collections as a future capability while they ship and work.

CONSEQUENCE, stated in the trial terms: a docs-only author cannot author idea O. Both executors reached the winning surface only by reading src/townlet/effects/collections.py. This is the strongest single piece of evidence to date for the gap between the north-star's expert-ceiling construct and the novice-authorability claim it is an upper bound on (PDR-0086).

NOT FILED, could not confirm: the source report also claims effects.md teaches 'global.vfs.*' which raises 'Invalid path'. src/townlet/world/expression/context.py:65-68 DOES resolve a 'global' root and dispatches to _resolve_vfs_chain(scope='global'), so the claim is not reproduced as stated and is deliberately excluded from this ticket.
=================== hamlet-83a043a9b9
ID:       hamlet-83a043a9b9
Title:    agent_private is INERT as a privacy declaration: the variable lands fully observable in every agent's observation row
Status:   triage
Priority: P1
Type:     bug
Parent:   hamlet-15050f280a
Created:  2026-08-21T10:19:51.609579+00:00
Labels:   recovery:WS-4, vfs-gap-analysis
Ready:    YES (no blockers)

--- Description ---
VFS gap analysis G-1 (docs/product/assessments/vfs-gap-analysis-20260821.md), INDEPENDENTLY VERIFIED by the standing agent (grep + encoder read).

VariableScope.AGENT_PRIVATE is documented as hidden-from-observations / observable-only-by-owner. Neither enforcement point is on the observation path: (1) registry.get(reader='agent') refuses correctly — but nothing in the runtime ever passes reader='agent'; the only occurrences are three docstring examples (registry.py:94/500/504), every real site passes 'engine'. (2) The observation encoder branches scope in ('agent', 'agent_private') — identical treatment — and reads through registry.get_agent(), which has NO access control (registry.py:774).

Measured: an agent_private variable written to 99.0 appears at its observation columns in EVERY agent's row, value tracking under negative control (60->0.6, 20->0.2). The declaration is a no-op on a surface an author reads as a guarantee: every information-asymmetry mechanic (private goal, hidden inventory, secret state) is unimplementable and APPEARS implemented. Textbook INERT — the debt class.
=================== hamlet-88578e629e
ID:       hamlet-88578e629e
Title:    Effects DTOs are the only config DTOs without extra=forbid, and carry behavioral defaults (observable=True)
Status:   triage
Priority: P2
Type:     bug
Created:  2026-08-22T12:34:34.050291+00:00
Ready:    YES (no blockers)

--- Description ---
Round-2 VFS review (SA H6/S5). EffectsConfig and EffectDefinitionConfig have no model_config (effects_config.py:214-267) unlike every neighbouring DTO — a typo'd field is silently ignored, defeating the No-Defaults enforcement mechanism. Behavioral defaults: observable: bool = True (:231), version default, effect_definitions default=[]. Also default=[] mutable-literal idiom vs default_factory used elsewhere in the same file. Prerequisite for the token design's max_active_effects field being enforceable at all.
=================== hamlet-8b5af63108
ID:       hamlet-8b5af63108
Title:    tensorNd is entirely undocumented: the container type that carries Trial B — and genuinely works — cannot be discovered from the docs
Status:   triage
Priority: P2
Type:     bug
Parent:   hamlet-15050f280a
Created:  2026-08-21T08:00:24.467080+00:00
Labels:   docs, prd-0001-trial
Ready:    YES (no blockers)

--- Description ---
Found by the Trial B tensorNd evidence audit (B-tensornd-audit-20260821.md, gap A-G8); confirms the blind run's G-1.

config/vfs_profiles_config.py:39-52 accepts tensor1d / tensor2d / tensor3d / tensorNd. docs/config-schemas/vfs-profiles.md documents a SMALLER vocabulary and does not mention tensorNd at all.

WHY THIS IS FILED AT MORE THAN DOC-ROT PRIORITY: the audit's finding is that the capability is REAL — a global-profile tensorNd genuinely expresses one entity's state as a set of occupied cells, observation-encoded faithfully, and it is what made the blind run's B-F2 PASS sound. An undiscoverable working capability is the worst case for a product whose north-star is authorability: it costs the author the whole feature AND makes the substrate look less capable than it is. Note the blind run reached it only by source-reading (its own discovery-path annotation records 'source-reading-required').

Bears on the PDR-0086 discovery-path metric row.
=================== hamlet-8c354c90bb
ID:       hamlet-8c354c90bb
Title:    initial_value_mode (all five members) is unreachable from vfs_profiles.yaml: compile_variable falls through to parser.parse(None) — the working registry implementation has no door from the profile surface
Status:   triage
Priority: P2
Type:     bug
Parent:   hamlet-15050f280a
Created:  2026-08-21T08:00:23.787499+00:00
Labels:   prd-0001-trial, recovery:WS-4
Ready:    YES (no blockers)

--- Description ---
Found by the Trial B tensorNd evidence audit (B-tensornd-audit-20260821.md, gap A-G3).

registry.py:653-654 INTENDS to raise "initial_value_mode 'eye' requires square 2D shape" — which is correct and is a good loud refusal. What the author actually sees is:

  AttributeError: 'NoneType' object has no attribute 'expandtabs'

The compiler's error formatter fails on the raised error before the real message reaches the author. The refusal is right; the diagnostic is unusable.

This is a FAILURE LOUDNESS defect (see metrics.md input metric 'Failure loudness' — an authoring mistake should produce a clear compile-time error). A correct refusal rendered unreadable is only marginally better than a silent no-op, because the author cannot act on it. NOT FIXED — substrate freeze.
=================== hamlet-8f2e13c5a9
ID:       hamlet-8f2e13c5a9
Title:    docs/config-schemas/expressions.md understates the engine: 9 shipped functions labelled 'planned', 19 more entirely undocumented, of 49 in FUNCTION_SPECS
Status:   triage
Priority: P1
Type:     bug
Parent:   hamlet-7a52a63e0b
Created:  2026-08-26T05:13:17.002888+00:00
Labels:   docs, docs-drift
Ready:    YES (no blockers)

--- Description ---
Found during the 2026-08-26 documentation recovery sweep and VERIFIED FIRST-HAND at HEAD before filing.

WHY P1 RATHER THAN DOC-ROT PRIORITY: the other stale schema docs cost a reader a failed parse and a trip to source. This one costs the product its central claim. A designer who reads 'planned but not yet implemented' against the spatial and statistical functions concludes the declarative surface cannot express their idea and reaches for Python. CLAUDE.md names that exact outcome as the load-bearing defect the project exists to prevent: 'When something can only be expressed by editing Python, that is a product defect.' The document makes the framework look materially less capable than it is. Same failure class as hamlet-8b5af63108 (tensorNd undocumented) and hamlet-7eadeb214c (effects.md omits for_each), and it bears on the PDR-0086 discovery-path metric row.

MEASURED: src/townlet/world/expression/functions.py registers 49 FunctionSpec entries in FUNCTION_SPECS.

(1) NINE SHIPPED FUNCTIONS ARE LABELLED 'planned but not yet implemented'.
expressions.md:229-239 ('Phase 2 Roadmap (Deferred Operators)') and :327-334 ('Domain-specific functions (Phase 2 - planned)') and :872-880 ('Future Extensions') disclaim: distance, within_radius, mean, sum, min, max, distance_to_affordance, manhattan_distance, perlin_noise. All nine are present and working in FUNCTION_SPECS.

(2) 'Type checking: Function signature validation is deferred to Phase 2 (requires function registry)' (expressions.md:336) IS FALSE. The registry exists and type checking is wired: world/expression/type_checker.py:358-366, visit_function_call imports FUNCTION_SPECS, raises TypeCheckError("Unknown function '<name>'") when absent, then calls spec.validate_args(arg_types).

(3) TWO ENTIRE CAPABILITY FAMILIES ARE INVISIBLE - 19 functions with zero mentions in the doc.
Temporal (11): lag, delta, ema, moving_average, rate_of_change, rising_edge, falling_edge, elapsed_ticks, time_in_window, phase_sin, phase_cos.
Tensor (8 absent + 2 incidental): gather, scatter, one_hot, masked_add, masked_set, argmin, argmax, count_where all absent; 'where' appears twice incidentally and 'normalize' appears ONLY in the 'Phase 3 - Vector Types (planned)' list while it ships.

(4) THE 'planned' LABEL IS CORRECT for these - genuinely absent from the registry, and they fail at TYPE-CHECK time, not parse: sin, cos, tan, asin, acos, atan, sqrt, count, random, bernoulli, normal, has_item. Note normal_dist and uniform DO ship; the absent spellings are 'normal' and 'random'.

TWO CORRECTIONS TO EARLIER FINDINGS so the fix pass does not chase ghosts:
- sqrt/sin/cos fail at TYPE-CHECK, not at parse (amends the effects.md finding). The parser accepts any identifier as a call; type_checker.py:363-365 is what rejects it.
- The ternary form 'if C then A else B' is CORRECT as documented. The Python conditional form failing is not a defect.

FIX MUST INCLUDE a complete function reference covering all 49 FUNCTION_SPECS entries, not just a correction of the wrong labels.

STRONG RECOMMENDATION - GENERATE THE REFERENCE, DO NOT HAND-WRITE IT. Signatures and arity already live in the registry, so a generated table cannot drift; hand-writing 49 entries would rot within a month, which is how this defect arose. The repo already has the durable anti-rot mechanism: tests/test_townlet/unit/config/test_vfs_doc_social_residue_examples.py compiles a doc's fenced YAML examples as a test, which is why the VFS doc's examples were caught when a rename moved the file. Extend that pattern: generate the function table from FUNCTION_SPECS and add a test that regenerates and diffs it, so drift fails loudly.

ACCEPTANCE: the doc's examples must parse and type-check after the fix, every FUNCTION_SPECS entry appears in the reference, and no shipped function is labelled planned. A regeneration test guards it.
=================== hamlet-a737e444c0
ID:       hamlet-a737e444c0
Title:    Effects cannot read position or time: the effects expression context threads neither agent_positions nor temporal, so spatial operators and temporal.* are unreachable from any effect (Trial K)
Status:   triage
Priority: P1
Type:     bug
Parent:   hamlet-15050f280a
Created:  2026-08-19T08:12:53.825652+00:00
Labels:   prd-0001-trial
Ready:    YES (no blockers)

--- Description ---
Trial K (PRD-0001) needed a world-driven effect to land differently depending on WHERE the agent is (mitigation B) and to be driven by a world clock (F1). Both are expressible in the expression grammar and unreachable from an effect.

THE GRAMMAR HAS BOTH. `world/expression/context.py` resolves a `temporal.*` namespace (_read_temporal, line 233) and `world/expression/functions.py` ships spatial operators guarded by _require_positions (line 206) plus _affordance_position (212) and _distance (1032).

THE EFFECTS EXECUTOR SUPPLIES NEITHER. `effects/executor.py:_make_eval_context` (642-726) builds the expression context two ways and neither passes agent_positions, affordance_positions, or temporal:
  - line 712 _TargetAwareExecutionContext(bars, vfs, target_bars, target_vfs, self_bars, self_vfs, vfs_registry, self_index, self_is_item, device)
  - line 726 ExprExecutionContext(bars=..., vfs=..., affordances={}, temporal={}, device=...)

Probed with a context shaped exactly as the executor builds it:
    RuntimeError: Spatial operators require agent_positions on the execution context
    KeyError: "Path 'temporal.tick' not found in execution context"
    agent_positions is None; temporal is {}

CONSEQUENCE FOR AUTHORING. An effect is the only engine-ticked surface a pack can declare (Trial O). Because that surface is blind to position and time, no declarative world process can vary by location or follow a clock. 'It is colder outside than inside' and 'it gets cold at night' both have no route.

SAME ROOT-CAUSE FAMILY as hamlet-1b9af9088c (spawn_item unreachable end-to-end because no production pipeline passes agent_positions). This is the second confirmed instance of the pattern: the expression/command grammar declares a capability that the execution path never threads the data for. Also note `for_each: nearby_agents` with `radius` (effects/schema.py:77-82) depends on the same missing positions.

Classification: ABSENT for the capability (no declarative surface reaches it); the refusal itself is loud.
Evidence: docs/product/trials/0001/K-20260819.md, probe configs/trial_k_cold/probe_trial_k.py F7 section.
Route: WS-4. File-never-fix held.
=================== hamlet-b3a30b82ef
ID:       hamlet-b3a30b82ef
Title:    self. and target. mean OPPOSITE entities in effects vs affordances, and no working route exists from an effect to a single agent's VFS variable
Status:   triage
Priority: P1
Type:     bug
Parent:   hamlet-15050f280a
Created:  2026-08-21T10:21:04.869147+00:00
Labels:   recovery:WS-4, vfs-gap-analysis
Ready:    YES (no blockers)

--- Description ---
VFS gap analysis G-10 (docs/product/assessments/vfs-gap-analysis-20260821.md). Analyst-attested with executed evidence, all three consequences L2-verified.

Affordance interactions set self_index=None / target_index=<interacting agent> (affordance_engine.py:512-513); effect lifecycles set self_index=<target entity> / target_index=None (effects/manager.py:225-226). Consequences: effect + target.vfs.X compiles clean then KeyError at runtime; effect + self.vfs.X on a non-item variable is a COMPILE error (the schema builder emits only vfs.X and target.vfs.X); affordance + spawn_effect target 'self' raises ValueError self_index not set.

NET: there is NO working route from an effect to one agent's VFS variable — the only reachable spelling is the bare vfs.X whole-batch write (see the G-9 ticket). Same context-threading root as hamlet-a737e444c0 (effects blind to position/time); candidate to triage as one unit.
=================== hamlet-b5cd718368
ID:       hamlet-b5cd718368
Title:    vec2i/vec3i/vecNi/vecNf accepted by the profile DTOs and rejected by the compiler: two type vocabularies disagree by four members
Status:   triage
Priority: P2
Type:     bug
Parent:   hamlet-15050f280a
Created:  2026-08-21T10:19:53.341065+00:00
Labels:   recovery:WS-4, vfs-gap-analysis
Ready:    YES (no blockers)

--- Description ---
VFS gap analysis G-4 (docs/product/assessments/vfs-gap-analysis-20260821.md) — the analysis found this recorded as an in-tree comment (trial_b_blind_organism/vfs_profiles.yaml, blind run gap G-5) but NEVER FILED; filing now closes the untracked confirm.

The profile DTO Literal accepts vec2i/vec3i/vecNi/vecNf — the DTO validator even enforces dims for vecNi/vecNf, a validation rule for types that can never compile — while the compiler runtime type set rejects all four. Verbatim refusals for both profiles and all four types in assessment §3.2. Declared-then-refused (BLOCKED, loud) — but the DTO half is a false promise the author pays for late.
=================== hamlet-b9a3bcbde2
ID:       hamlet-b9a3bcbde2
Title:    A bare vfs.X write to an agent-scoped variable writes the WHOLE agent batch, once per interacting actor — the shortest spelling is the wrong one
Status:   triage
Priority: P2
Type:     bug
Parent:   hamlet-15050f280a
Created:  2026-08-21T10:21:04.512606+00:00
Labels:   recovery:WS-4, vfs-gap-analysis
Ready:    YES (no blockers)

--- Description ---
VFS gap analysis G-9 (docs/product/assessments/vfs-gap-analysis-20260821.md). Analyst-attested with executed evidence.

effects/context.py set_path for vfs.* calls registry.set with the whole tensor; the affordance engine runs the command list once per interacting agent, the effect manager once per active effect instance. Measured: modify vfs.avar value 'vfs.avar + 5.0', 2 agents both interacting -> [10.0, 10.0] (not [5.0, 5.0]); effect route +10/tick with 2 instances -> [20,20]->[40,40]->[60,60]; a global gets the same doubling. The correct per-agent form (target.vfs.X) exists on the affordance route and gives [5.0,5.0] — but nothing warns, and vfs.X is the shorter, more obvious spelling.

Counterpart of hamlet-57a5126baa (the indexed route's bypass): together they are the whole write-addressing question. Related: the fix for hamlet-cf16cdb6c4 made vfs.X scope-aware for READS; write fan-out semantics are this ticket.
=================== hamlet-bf42ac60b5
ID:       hamlet-bf42ac60b5
Title:    Item-slot observation emits raw variable values into a normalized observation vector: Trial F's durability reads 3.0 at offset 58 while every other component is [0,1]
Status:   triage
Priority: P2
Type:     bug
Parent:   hamlet-15050f280a
Created:  2026-08-18T13:10:35.307442+00:00
Labels:   prd-0001-trial
Ready:    YES (no blockers)

--- Description ---
Found by the 2026-08-18 PRD-0001 methodology review (RL lens). The obs_item_slots compiler feature emits item-scoped variable values UN-normalized: configs/trial_f_durability's wear state observes as 3.0 (its raw value) at its compiled offset, in an observation vector whose other components are minmax-normalized to [0,1]. An unbounded, out-of-scale feature at network input silently degrades training. Related: hamlet-1ad6383186 (item-observation layout question) — this is a concrete defect that layout decision should subsume. Companion authoring-surface improvement, same review: a compile-time conditioning lint (warn when a feature's active dynamic range is a small fraction of its declared normalization range — Trial L's cooldown gate boundary is a 0.002 difference at network input under minmax [0,1000]) would serve the novice author at compile time rather than at training time.
=================== hamlet-c6c6c241c5
ID:       hamlet-c6c6c241c5
Title:    A variable declared with expression: cannot reference VFS state — the field is accepted by the DTO and refused at compile Stage 6
Status:   triage
Priority: P2
Type:     bug
Parent:   hamlet-15050f280a
Created:  2026-08-21T08:00:23.454144+00:00
Labels:   prd-0001-trial, recovery:WS-4
Ready:    YES (no blockers)

--- Description ---
Found by the Trial B tensorNd evidence audit (B-tensornd-audit-20260821.md, gap A-G6).

vfs_profiles_config.py:57 accepts 'expression:' as one of three mutually-exclusive init sources, so it reads to an author as an available passive-dynamics surface. Declaring organism_cells with expression: "max(vfs.organism_cells, 1.0)" is refused at Stage 6:

  Reference traversal requires schema entry for 'vfs.organism_cells'

So the surface is declarable and not usable for this scope — the declared-but-inert shape, in its BLOCKED variant (it fails loudly rather than silently). Likely the same root cause as hamlet-cf16cdb6c4 (A-G1): the schema has no entry for the global path. Re-test after A-G1. NOT FIXED — substrate freeze.
=================== hamlet-cb0ccdaa98
ID:       hamlet-cb0ccdaa98
Title:    Cascades cannot target VFS variables: CascadeConfig source/target are typed as meter names, so there is no declarative per-tick passive dynamic over a tensor container
Status:   triage
Priority: P2
Type:     bug
Parent:   hamlet-15050f280a
Created:  2026-08-21T08:00:23.119535+00:00
Labels:   prd-0001-trial, recovery:WS-4
Ready:    YES (no blockers)

--- Description ---
Found by the Trial B tensorNd evidence audit (B-tensornd-audit-20260821.md, gap A-G5).

config/environment_config.py:161-168 types CascadeConfig.source and .target as meter names, and validation refuses anything else with [CASCADE_INVALID_METER]. Cascades are the declarative per-tick passive-dynamics surface, so a tensor container has NO passive dynamic available to it.

variables_reference.yaml does not fill the hole either: it is documented as static-only (no expressions, no item-scoped variables), per CLAUDE.md's VFS section.

Bears on the same class as hamlet-cf16cdb6c4 (A-G1) and hamlet-a737e444c0: the ways a declared world-state container can be made to CHANGE on its own are all closed. NOT FIXED — substrate freeze.
=================== hamlet-cebe51077a
ID:       hamlet-cebe51077a
Title:    Transition phase names are a closed canonical set at compile — designer-named phases refuse, and VFS.md's own design examples (action_costs, passive_depletion, threshold_cascades, emergency_relocation) are unauthorable as written
Status:   triage
Priority: P1
Type:     bug
Created:  2026-08-24T17:44:58.799430+00:00
Ready:    YES (no blockers)

--- Description ---
Surfaced 2026-08-25 by the VFS documentation-truth loop (pass 3, docs/architecture/VFS.md §11.4). sort_key in vfs/transition_graph.py / transition_schedule.py refuses any phase name outside DEFAULT_TRANSITION_PHASES at compile, so the phase names used throughout the doc's §10.2/§12.3/§13.3/§14.3 examples cannot be declared by a pack. Additionally, action writes scheduled after apply_completion_bonuses raise at the first env.step (transition_schedule.py:123-127) — a compile-green/runtime-crash seam. Per CLAUDE.md this is the load-bearing defect shape: a designer cannot express phase structure in config without editing Python. Coverage at HEAD: 11 of 18 canonical phases have compiler-emitted rules, 7 are engine-imperative. Decide: (a) open the phase vocabulary to declared names with declared ordering (declarative surface), or (b) keep the closed set and rewrite the doc examples to canonical names + make the post-completion-bonus write refusal a compile error. Either way the runtime raise must move to compile time.
=================== hamlet-d45331a367
ID:       hamlet-d45331a367
Title:    bars.yaml `recovery.natural` is INERT: required in every pack by no-defaults, consumed by zero runtime sites
Status:   triage
Priority: P2
Type:     bug
Parent:   hamlet-15050f280a
Created:  2026-08-18T06:40:12.883357+00:00
Labels:   prd-0001-trial
Ready:    YES (no blockers)

--- Description ---
Found by Trial L (PRD-0001, record docs/product/trials/0001/L-20260818.md, pin fb8c6148). MEASURED: a meter declaring recovery natural: 1.0 moved 0.0 over 9 idle ticks; grep shows the only non-test mentions of 'natural' are the DTO field itself (config/bars_v2_config.py:49) and a comment. The no-defaults principle forces every pack to write this field, and nothing reads it — the exact INERT class (declared, validates, does nothing). Trial L's timers advance via depletion.passive: -1.0 instead, which DOES execute. Fix direction is a WS-4/PDR-0005 call: wire it (natural recovery per tick) or delete the field from the DTO and every pack (zero-backcompat).
=================== hamlet-d76684f549
ID:       hamlet-d76684f549
Title:    Effects survive env.reset(): a spawned effect keeps ticking across the episode boundary with elapsed_ticks continuing
Status:   triage
Priority: P1
Type:     bug
Created:  2026-08-15T04:58:08.978322+00:00
Ready:    YES (no blockers)

--- Description ---
MEASURED incidentally while verifying Trial 002 (PDR-0051) — the PDR-0049 pattern, second
occurrence: found by verifying, not by the work. Independent of anything money-specific.

## Symptom

`env.reset()` correctly restores bars to their declared `initial`, but a previously spawned
effect is NOT cleared. Its `on_tick` pipeline continues to run in the new episode, and
`elapsed_ticks` keeps counting from the old episode.

## Reproduction (configs/trial002_money_log_gdp, effect `business_cycle`)

    env.reset()
    env.positions[0] = <WORK tile>
    env.step(INTERACT)            # spawns business_cycle; money -> 2000.0
    env.reset()
    #   money == 1000.0           (correct: bars.yaml initial)
    env.step(WAIT)
    #   money == 2258.8           <-- tick 1 of the PREVIOUS episode's cycle

Expected after a reset: 2000.0 only if the effect were legitimately re-spawned, and 1000.0
otherwise. 2258.8 is only reachable if the effect instance and its elapsed_ticks survived.

Independently corroborated: sweeping actions 0..9 with an `env.reset()` before each shows money
moving on actions 8 and 9 but NOT when action 9 is run alone from a fresh env — the effect was
spawned during an earlier iteration and outlived every reset in between. That order-dependence is
the same bug seen from the other side.

## Why it matters

Episode state leaking forward corrupts training: episode N+1 begins mid-process with a
carried-over phase, so returns are not comparable across episodes and the leak is invisible in
bar values (which DO reset correctly). It also makes any effects-based test order-dependent,
which is how this was found.

## Where to look

`effects/manager.py` (EffectManager instance storage) and the reset path in
`environment/vectorized_env.py` — bars are re-initialised there; effect instances appear not to
be. Note `EffectManager.spawn_effect` has exactly one production caller
(`effects/executor.py:228`), so the spawn side is narrow and the fix should be too.

## Acceptance

A test that spawns an effect, calls `reset()`, steps once, and asserts the bar equals its
declared `initial` — plus an assertion that no effect instance survives the reset. Put it in the
golden-tick / phase-ordering set (hamlet-c8c316ba03) so ordering leaks are caught structurally.
=================== hamlet-de52c40c03
ID:       hamlet-de52c40c03
Title:    Item-profile VFS expressions never evaluate, and the item expression schema uses bare bar names instead of the bar. namespace
Status:   triage
Priority: P2
Type:     bug
Parent:   hamlet-15050f280a
Created:  2026-08-21T10:19:52.649784+00:00
Labels:   recovery:WS-4, vfs-gap-analysis
Ready:    YES (no blockers)

--- Description ---
VFS gap analysis G-2(c) (docs/product/assessments/vfs-gap-analysis-20260821.md). Analyst-attested with executed evidence.

Nothing in the runtime evaluates CompiledItemProfile.variables[].ast — measured: item expression (energy*100) holds 0.0 across steps under eager. Additionally the item schema namespace differs from global/agent: 'bar.energy' is refused at Stage 6 with available paths ['energy', 'health', ...] — bare names. So the same expression text is valid in one profile and a compile error in another. Adjacent to hamlet-f2a37a8c8a (item accessor gap) but a distinct mechanism.
=================== hamlet-df2b972c49
ID:       hamlet-df2b972c49
Title:    Two checkpoint stamp/compare paths that neither task 4 nor task 5 covers
Status:   triage
Priority: P1
Type:     bug
Created:  2026-08-11T17:47:15.397352+00:00
Labels:   WS-1, provenance
Ready:    YES (no blockers)

--- Description ---
Found by task 4 recon (2026-08-12). The WS-1 plan treats the checkpoint boundary as two sites — `attach_universe_metadata` (task 4) and the serving path (task 5). Recon found two more, both real:

**1. `VectorizedPopulation.get_checkpoint_state` / `load_checkpoint_state`.** An independent stamp/compare path for population state. Whatever identity guarantees tasks 4 and 5 establish on the DemoRunner path do not apply here.

**2. `DemoRunner._validate_checkpoint_compatibility`.** Unpickles a checkpoint **before any universe exists**, behind a broad `except`. So the earliest thing that touches a checkpoint is the thing least able to reject it, and its failures are swallowed. A broad `except` on the validation path is the "silent fallback" antipattern CLAUDE.md names explicitly.

**Why this matters beyond the two sites.** The Provenance-integrity guardrail's target is *"no silent acceptance"*. Enumerating stamp/compare paths by grepping for `attach_universe_metadata` finds the call shape, not the set of places a checkpoint is read — the recurring lesson recorded four times in `docs/product/current-state.md`. Closing tasks 4 and 5 and declaring the breach closed would repeat it.

**First unit should be enumeration, not repair:** find every site that writes or reads a checkpoint dict, list them, and only then decide which need the guard. Suggested starting point: search for `torch.save`, `torch.load`, and every consumer of the checkpoint mapping — not just callers of the two known helpers.

Priority 1 because it bears directly on whether PDR-0008's breach can be called closed after task 5, which gates the oracle freeze (PDR-0006 precondition 2: freezing a bug makes it a requirement).

Related: `hamlet-ae6601e463` (task 4, done, `04a59114`), `hamlet-1029f99f4b` (task 5, the serving path), `hamlet-c8c316ba03` (hash-boundary tests unwritten), PDR-0008.

--- Fields ---
  severity: major
  component: checkpoint provenance and compatibility
  expected_behavior: Every checkpoint writer and reader stamps or verifies the same universe identity contract before accepting data.
  actual_behavior: Population checkpoint state and early DemoRunner compatibility paths bypass or swallow parts of the identity guard.
=================== hamlet-f278b8691f
ID:       hamlet-f278b8691f
Title:    SetEncoderConfig.token_field_name resolves only at network-build time, not compile time
Status:   triage
Priority: P2
Type:     bug
Created:  2026-08-22T07:14:16.426198+00:00
Labels:   authoring-surface, vfs
Ready:    YES (no blockers)

--- Description ---
Found while executing the Phase A pivot plan (PDR-0109). NetworkFactory.build_set_encoder (agent/network_factory.py:196) is the first place a bad token_field_name fails — at runtime network construction, not at UAC compile. The compiler already holds both the brain config and the observation spec, so cross-validating the field name, and dims == max_tokens*token_dim, belongs in stage 4 cross-validation. PDR-0052 shape: underspecification is a compile error.
=================== hamlet-f2a37a8c8a
ID:       hamlet-f2a37a8c8a
Title:    Item-scoped variables are unreachable through registry.get(): the accessor the VFS docs name as THE read path raises KeyError (Trial F evidence audit)
Status:   triage
Priority: P2
Type:     bug
Parent:   hamlet-15050f280a
Created:  2026-08-19T16:24:35.077079+00:00
Labels:   prd-0001-trial, recovery:WS-4
Ready:    YES (no blockers)

--- Description ---
Found by the Trial F evidence audit (docs/product/trials/0001/F-evidence-audit-20260820.md), reported there with a reproduction. NOT independently re-verified by the standing agent at filing time -- stated so the next reader does not assume it was.

CLAIM: item-scoped variables cannot be read through registry.get(), which docs/architecture/vfs-current-implementation.md and docs/config-schemas/variables.md name as the read path with access control enforced at registry.get()/set(). The audit reports KeyError. The values ARE reachable -- the audit read the durability value four independent ways, including at its compiled observation offset -- so this is an accessor gap, not missing state.

WHY IT MATTERS: 'read the variable I declared' is a first-order authoring operation, and the documented accessor is the one that does not work for one of the nine declared scopes. Same family as the item-observation questions in hamlet-1ad6383186.

VERIFY FIRST: reproduce the KeyError and establish whether it covers all item-scoped variables or only those declared through item_profiles, before treating the docs or the accessor as the defect.
=================== hamlet-f54b887148
ID:       hamlet-f54b887148
Title:    A global tensor whose leading dim equals num_agents hard-fails at the first step — live on configs/trial_b_blind_organism at num_agents=3
Status:   triage
Priority: P1
Type:     bug
Parent:   hamlet-15050f280a
Created:  2026-08-21T10:19:52.996124+00:00
Labels:   recovery:WS-4, vfs-gap-analysis
Ready:    YES (no blockers)

--- Description ---
VFS gap analysis G-3 (docs/product/assessments/vfs-gap-analysis-20260821.md), INDEPENDENTLY REPRODUCED by the standing agent at HEAD on the UNMODIFIED landed pack: ValueError: global_active_mask length 243 does not match global_vfs_dim 81 — configs/trial_b_blind_organism, first env.step(), num_agents=3.

RULE (measured, assessment §4 G-3): a global tensor variable fails exactly when its leading dimension equals num_agents. Probe pack with global tensor2d shape [2,2]: OK at num_agents=1/3/4, crashes at num_agents=2. Trial pack with tensorNd shape [3,3,3,3,3]: OK at num_agents=1 (the ONLY agent count its trial evidence was gathered at), crashes at num_agents=3.

MECHANISM: observation_builder.py _flatten_to_batch decides already-batched-vs-broadcast from value.shape[0] == batch_size ALONE. For a global variable that equality is a coincidence, not a fact: the container is treated as per-agent and contributes shape[0]-fold fewer columns than the spec computed, tripping the active-mask check at observation_builder.py:329.

WORST-SHAPED FAILURE AVAILABLE: compiles clean, artifact valid, and whether it RUNS depends on a training hyperparameter the author may change for unrelated reasons. Any global tensor with a small leading dim (3, 4, 8 — the shapes authors actually write) sits one num_agents edit from a crash.

NOTE: the tensorNd evidence audit (B-tensornd-audit-20260821.md §9) named exactly this case as its untested information gap and flagged it as the obvious follow-up. It predicted the case 'could silently appear to work'; measured reality is a loud crash — better than silent, but the audit's boundary was real.
=================== hamlet-f9090ec3e8
ID:       hamlet-f9090ec3e8
Title:    Wall-clock ratio assertions inside the CI gate: two tests assert timing ratios under always-on --cov, and both have reddened at random
Status:   triage
Priority: P2
Type:     bug
Created:  2026-08-15T01:31:55.370601+00:00
Labels:   guardrail-tests, package:townlet
Ready:    YES (no blockers)

--- Description ---
OBSERVED 2026-08-15 during the hamlet-60dd3c4b53 deletion verification. Two consecutive full-suite runs on the same tree, same machine, minutes apart:

    run 1: 1 failed, 3123 passed, 16 skipped, 35 deselected  (1088s)  <- test_vfs_overhead_under_limit FAILED
    run 2:    3124 passed, 16 skipped, 35 deselected          (1005s)  <- same test PASSED

Run alone it passes in 5.58s. Nothing about the tree changed between the runs.

## Why it is flaky by construction

`tests/test_townlet/performance/test_performance_threshold.py:36-56`:

- It times `env.step()` for two different packs by wall clock (`time.perf_counter`) and asserts the RATIO `(vfs_time - baseline_time) / baseline_time <= 0.05`.
- `pyproject.toml` `addopts` always enables `--cov=townlet --cov-branch`. **Every timing sample is taken under coverage instrumentation**, whose per-line overhead is large and varies with which code paths each env exercises. The measurement is dominated by instrumentation, not by VFS.
- A 5% threshold on a ratio of two noisy wall-clock means, on a shared machine, with a `jitter` allowance of `1e-4` that is four orders of magnitude smaller than the noise it is meant to absorb.

The test is not measuring what it claims. It is measuring "did these two envs get comparable CPU during this run".

## Why it matters more than one flaky test

CI runs bare `uv run pytest` (`.github/workflows/tests.yml:37`), so this test is in the CI gate. CI on this branch went green for the first time in its history on 2026-08-15 (hamlet-2100105c9a), and PDR-0043's rule was that a gate restored is not a gate verified. **A gate that reddens at random is how a verified gate becomes a waved-through gate** — the PDR-0010 failure mode, arriving by a new route. One unexplained red teaches the next reader to re-run rather than investigate.

Note it did NOT redden CI in the runs on record (569a7738 and 1b25c99d both green), so this is pre-emptive, not a live outage.

## Fix options

1. **Mark it `slow` or `gpu`-style and deselect it from the default run**, keeping it as an on-demand measurement. Cheapest; the suite stops asserting something it cannot measure.
2. **Measure without coverage** — run performance assertions in a separate pytest invocation with `--no-cov`, so the numbers mean something.
3. **Assert on a robust statistic with a real tolerance** — best-of-N rather than a single mean, and a threshold derived from observed variance rather than a round 5%.
4. **Delete it.** `Runtime throughput` in `docs/product/metrics.md` already records that there is no recorded baseline artifact and that benchmarks must be re-run to be cited. A threshold test that cannot measure its threshold is not protecting the guardrail the metrics row describes.

Option 1 or 2 preserves intent; 4 is defensible under the zero-tech-debt rule if nobody will fix the measurement.

RELATED: PDR-0010 (a recorded green is not a green), PDR-0043 (a gate restored is not a gate verified), PDR-0033 (ask what a green tool cannot see), `docs/product/metrics.md` → `Runtime throughput` and `Gates green`.

--- Fields ---
  severity: minor
  component: performance threshold test suite
  expected_behavior: A test in the default CI gate either measures its stated quantity reliably or is excluded from the gate.
  actual_behavior: A 5% wall-clock ratio assertion taken under always-on coverage instrumentation passes or fails nondeterministically across identical runs.
=================== hamlet-fba3d5aa3c
ID:       hamlet-fba3d5aa3c
Title:    A pack with zero affordances validates and compiles, then crashes at the first observation (obs_affordance_at_position shape mismatch)
Status:   triage
Priority: P2
Type:     bug
Parent:   hamlet-15050f280a
Created:  2026-08-18T11:09:40.558720+00:00
Labels:   prd-0001-trial
Ready:    YES (no blockers)

--- Description ---
Found by PRD-0001 Trial F (by-catch, filed not fixed). Repro: any pack whose environment.yaml declares affordances: [] — it passes 'python -m townlet.universe validate' and compiles, then env.reset() raises ValueError: Value for 'obs_affordance_at_position' has shape (1, 1), expected (1,). Cause: ObservationEncoder._build_affordance_encoding emits (num_agents, num_types+1); with num_affordance_types == 0 the compiled registry slot for the field is scalar-shaped per agent, so the publish at observation_encoder.py:315 fails. Declared-and-crashing class: the declared surface (a world with no affordances — items-only worlds are a legitimate authoring shape) lies at env.reset(). Trial F worked around it with one inert BENCH affordance.
