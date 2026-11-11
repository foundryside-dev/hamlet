# Initial participation: mask and observation owner facts

Read-only source capsule, 2026-11-11, following root's durable WIP4 d4426803 and bounded task. No source/test/runtime/import/probe/compile/lint/git/index/branch/worktree/checkout/source-copy/extra-agent action. Only this ignored prose was written in this followup. AGENTS.md direct-current/no-BC rules apply. Read approved design T18e-PRE-STEP-RETIREMENT-DESIGN-ASTRA.md, verified SHA256901342a6b27ae5bacdff535c337352061fa6c55b7e1d31373be40bbcdad47234. Proposed APIs below remain proposed; this is not implementation authority or acceptance closure.

## Exact source custody

ENV's actual import/constructor/get_action_masks identified action_mask_builder.py. Its metadata206 lines was checked BEFORE opening, within the available1322-line addition. Exactly one additional complete body was read; no dependency implementation was expanded.

| Complete body | Lines | SHA256 |
|---|---:|---|
|src/townlet/environment/vectorized_env.py|2452|3b65e6f143edf1a1a363b6b537376f2e8f3f5dc1f7ce6f6feb8ba9c06bca5256|
|tests/test_townlet/regressions/bac/test_exploration_factory.py|1226|151742778748b41ef40af13df0b5fbd5ce87d825ef3e3d2a4365c2f2822f314f|
|src/townlet/environment/action_mask_builder.py|206|5d02f08f94c68bbd63b4491a5ed00a432a3fbadbec6b9a02572d544bfbcb7174|
|Total|3884|exactly three bodies, <=5/5000; metadata repeated unchanged|

Shared FX1456 remains unopened. No fourth body, subset/excerpt charging, reflection or source copy. Historical builtin observation-read purity reports/receipt were consulted as attributed prose. Their named observation geometry/item-registry duties do NOT automatically certify action-mask dependencies discussed below.

## Actual mask owner and dependencies

ENV constructor creates ActionMaskBuilder once with actual action_space, device, substrate, _movement_deltas, action_ids and enable_temporal_mechanics. Builder stores these references in ordinary attributes; no immutable wrapper or copied ownership is enforced there. It does not cache a per-tick mask or mutate its own fields in build. Actual signature:

`build(*, num_agents, positions, dones, item_inventory, item_manager, item_handler, affordances, affordance_open) -> torch.Tensor`.

ENV.get_action_masks forwards its current num_agents/positions/dones (or None if absent), item_inventory/item_manager/item_handler/affordances and bound _affordance_open_mask. It calls build every time, has no phase/participation-operation guard and retains no last-action-mask cache. Actual output contract is full bool[N,A] on builder device, A from actual action_space. No explicit result shape/dtype/device validation is present in ENV.get_action_masks itself.

Source execution order and mutable/read dependencies:

1. action_space.get_base_action_mask(num_agents=N,device=device) supplies the working tensor. Builder mutates this tensor in place; **fresh/nonaliased base ownership is an external action_space contract, not established by this body**.
2. With inventory: get_action_by_name('GET') and each USE_SLOT_i/DROP_SLOT_i, slots/max_items_per_agent reads; slot/fullness masks modify only working mask locally. For eligible GET rows, item_manager.world_of_agent(i) and items_at(world,positions[i]) determine availability. Their implementations are unopened.
3. With item_handler: compute_custom_action_masks(action_space,action_masks,positions) is called, passing actual live positions and mutable working mask. The builder does not constrain additional callback writes/RNG or isolate positions.
4. Rectangular boundary masking reads substrate.width/height/position_dim and optional depth plus movement_deltas. It derives axis-boundary rows and movement IDs with tensor operations, writing working mask only. It does not call movement execution or position initialization. Width/height/depth are actual selected substrate state, not a scalar grid_size assumption.
5. Affordance masking reads action_ids['INTERACT'], iterates affordances and calls substrate.is_on_position(positions,affordance_pos). If temporal mechanics enabled, it also invokes supplied affordance_open(name). INTERACT retains its base mask AND actual on/open availability.
6. **Last, if dones is not None, action_masks[dones]=False.** Existing builder already suppresses every action for every done row, after custom/item/boundary/affordance work. An extra global terminal-masking fix is unnecessary for this producer. Done rows do not skip earlier read/callback work; clearing last is output semantics, not proof callbacks were skipped.

ENV._affordance_open_mask returns full bool[N] from _is_affordance_open. Non-temporal returns True directly. Temporal reads actual current time_of_day unless explicit hour, then vtc_affordance_gate_program.is_affordance_open(name,time_of_day,device), converting missing gate KeyError to ValueError. No VFS evaluator or random call appears in these ENV wrappers; gate implementation is unopened. Despite mask-builder doc wording, this wrapper does not itself query per-world overrides.

## Candidate staging: feasible versus proved pure

**Feasible with current signature:** under the new operation guard, own candidate_dones as a detached clone of the pristine live false dones, mark exactly the selected retired-ID rows true in that candidate, and pass candidate_dones to the actual builder while forwarding unchanged actual positions/items/affordances/open callback. No temporary write to ENV.dones is needed. Own/validate the returned candidate mask as dense bool[N,A] at actual device; ensure retired rows false and every remaining live row has a legal action before any publication. Population stages its live-row selector view from that full mask. Do not select actions to compute this candidate.

An alternative is to capture one genuine full all-active legal mask at the fixed reset state, own it, and derive candidate_mask as an independent clone with retired rows false. Since dones affects the inspected builder only in its final row-clearing step, this derivation is exactly the builder's local done semantics at unchanged dependencies. It avoids invoking callbacks a second time merely for candidate dones. It does NOT make the first base-mask calculation pure, authenticate an old mask at changed item/position/hour state, or establish fresh ownership of action_space's base return. Current reset does not already capture/store an action mask; adding such capture is explicit owning implementation, not a fictional existing cache.

**Purity verdict:** builder has no direct RNG draw, VFS evaluate/tick/reset, physical action or self-state assignment. Its local tensor logic can stage candidate dones/mask before publication. Full build is **not yet source-proved pure** for all supported configurations: it calls actual external methods and a supplied callable, and receives a base tensor whose alias contract is unread. The old builtin purity receipt certifies observation-specific items_in_world/holder_of/normalization/visibility/egocentric reads, not items_at, compute_custom_action_masks, is_on_position or action-space mask ownership. No production qualification may substitute a no-op custom handler, fake callback or item-free setup for required supported paths.

All genuine mask computations/callbacks, owned cloning, finite geometry validation, live-legal checks, comparison and result allocations must finish BEFORE ENV status publication. After publication the planned two-owner success suffix must only install preallocated references/markers and return retained result. In particular do not call get_action_masks, _get_observations, .clone, issuer.issue, _record, VFS/gate/item callbacks or population validation after that cut. A delegated callback that can mutate must be guarded/validated before publication; no rollback claim follows from running it early.

## Actual observation/reset reading integrity

ENV._get_observations calls the actual encoder with _build_token_publish_context, not a stored current-observation cache. The context explicitly contains positions, encoded velocity, meters, affordance layout/deployment, vision range, agent_slots=None, item slots and effect slots. It contains no dones/step_counts/global_tick or time_of_day argument. Thus changing only dones does not change this ENV-built context. This is a direct dependency fact; byte equality under actual encoder/builtin fixed-state behavior additionally uses the qualified observation-read capsules, not a reread of encoder/publishers here.

_affordance_layout DOES lazily retain a positions/deployed cache. Reset invalidates/refills layout through configured/randomized placement, then its final _get_observations warms that cache before successful reset returns. Do not describe arbitrary _get_observations calls as globally cache-write-free; successful supported reset already provides the genuine reading needed for this operation. Item/effect assembly allocates local publish tensors and reads actual managers; no VFS evaluation is invoked by _get_observations itself. The historical observation-read purity proof assumes supported builtins and fixed state, not arbitrary replaced callbacks or concurrent mutation.

_reset_world_state sets genuine positions/zero velocity/initial meters, false dones/zero counts/ones intrinsic weights, global_tick0, registry episode state/tick/hour0, history/effects/items and evaluated reset-time expressions, then initial item spawn and final observation. reset(reservation) owns actual VFS projection first, calls that physical reset once, creates actual accepted token/generation and reset WorldRecord containing accepted+observation, then moves to active-awaiting-activation. No action mask is stored in that receipt. Public WorldRecord observation ownership/cloning is supplied by the qualified world contract; its implementation was not reopened.

Duplicate equal reset authenticates retained reservation identity and allowed phase, then returns **the original reset record** before another physical reset. Its observation is historical reset data. It does not recalculate observation/masks or undo a future initial-participation decision; it must not become current activity authority. Proposed decision state/guard must fence duplicate reset reentry as well, because this early-return branch otherwise bypasses later reset validation. Existing activation merely checks token/issued population+BANK receipts and installs phase active; it does not reconstruct physical masks or observation.

For preparation, retain exact current accepted/reservation/reset identities plus generation/revision, owned original dones/counts/meters and physical observation, and staged candidate status/mask. Receipt observation can supply the original physical reset reading; it cannot prove that publicly mutable current positions/meters/items/effects/VFS have not changed meanwhile. At prepublication commit, compare actual original physical reading/state with retained evidence under the guard, before any publication. If re-encoding is used for that check, it is a genuine prepublication read with the documented fixed-builtin/cache premises, never a deferred postpublication call. Observation equality alone cannot detect mutations to unencoded physical/hidden state: the exact additional state comparison contract must cover the design's preservation claim (positions/velocity/items/effects/layout/history/VFS/time), or be supplied by actual owner revision discipline. Do not infer immutable state from an owned historical tensor.

## Revision and guard windows

Current _world_revision initializes0 and increments at the accepted step cut AFTER claim and BEFORE tick-scoped reset/physical writes. Reset advances _world_generation and replaces accepted/reservation/reset identities; it does not increment _world_revision in its body. freeze/close pins the revision. Public live tensor writes do not increment it automatically. Therefore revision equality alone cannot detect tampered dones/meters/counts/positions; preserve actual byte snapshots/comparisons required by design. Successful participation must increment the proposed own revision/consume marker as designed, without claiming an already-existing implementation.

Current ENV has phase/identity checks but no per-operation lock/initial-participation transaction guard. get_action_masks and _get_observations can be called without phase checks. activate_episode can currently open active during the proposed window if no added guard; reset duplicate can currently return its retained record; step changes revision after its claim. Proposed prepare/commit must exclude activation/step/close/reset/restore/reentrant participation and callbacks entering these operations for the entire staged transaction, including prepublication reads. Postpublication population assignment suffix must not expose an intermediate activation opportunity. Define support for concurrent threads through the actual owners' lock discipline; existing phase checks alone do not provide it.

## Exact remaining external owner questions

Provide source-backed public facts, not another body in this context:

- `townlet.environment.action_builder.ComposedActionSpace.get_base_action_mask`: does each supported call return fresh owned bool[N,A], and are get_action_by_name/get_base_action_mask nonmutating/RNG-free at fixed configuration?
- Actual `townlet.items.ItemActionHandler.compute_custom_action_masks` and `ItemManager.world_of_agent/items_at`: enumerate mask-call writes/callbacks, whether they read-only inspect positions/item state without RNG/VFS/history mutation, and whether output writes are confined to supplied working mask. Existing observation-only manager capsule is insufficient for items_at/custom handling.
- Supported substrate `is_on_position` and temporal `VTCAffordanceGateProgram.is_affordance_open` read purity/returned geometry and dependencies. Existing geometric normalization/visibility certificate is a different named graph.
- Parent/ENV owner must settle how fixed reset-state freshness covers unencoded mutable item/effect/VFS state across prepare/commit, and its actual guard/lock order. This capsule proves the dependency boundary; it does not invent a complete snapshot schema or assert all live mutation is revisioned.

These questions do not prevent staging all local calculations before publication or require a user permission question. They are finite owning source facts required before calling the proposed operation pure. Existing builder already supplies the required inactive-false semantics. No extra mask-row compatibility path, constructor-only fix, native/parent stability acceptance, C closure or global release claim follows.
