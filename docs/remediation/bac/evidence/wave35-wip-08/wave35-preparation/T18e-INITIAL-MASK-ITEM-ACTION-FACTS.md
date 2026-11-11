# Initial mask: item and action owner facts

Finite read-only source capsule, 2026-11-11, against coordinator-supplied exact HEAD `d4426803` (not independently queried). Read repository AGENTS.md. Only this designated ignored prose is written. No implementation, tests, runtime/import/probe, git/index, branch/worktree/checkout, source-copy or new-agent action. Scope is fixed genuine reset state, supported builtins, no arbitrary uncooperative callback or concurrent mutation. This is source evidence, not qualification or acceptance closure.

## Custody

SHA256 and whole-file line counts were checked BEFORE reading any of these three source bodies. Exactly three bodies, 1486 lines, within hard 5 bodies/5000 lines; no additional helper implementation was opened. Some already charged text was reread after combined tool output truncation.

| Source | Lines | SHA256 |
| --- | ---: | --- |
| `src/townlet/environment/action_builder.py` | 90 | `b274b517c3485e0adb51c6cd59bf1b6f31de15d4111e98bc22cf9c6fbafad944` |
| `src/townlet/items/action_handlers.py` | 356 | `496a19a3e7c2b3deb261b644c54f663d607697cbced8f8c01c57ebe525420b9e` |
| `src/townlet/items/manager.py` | 1040 | `f9a769b0777a65c96fd965b636ebbd6f30c0f02e3a5fb6df71d64e123fd51616` |

Read `T18e-INITIAL-PARTICIPATION-MASK-OWNER-FACTS.md`, SHA256 `5559dec45a7864e49aae9aa9a39ed24457cfcf95fe63759d069d5504fd187ea4`. All mask-builder/ENV facts below are attributed to that capsule, not expanded source bodies. Read historical `T18e-ITEM-REGISTRY-READ-PURITY.md`, SHA256 `779cece2ba19da3fb25fb7968d4f53f79a44ebaa8283398116883a1c463cb04d`, as attributed observation-specific proof only. Its inventory/item ordinary-field premises are consistent with this mask traversal; its proof did not cover `items_at` or custom mask computation. No registry/inventory/instance body was expanded here.

## Actual action-space ownership

`ComposedActionSpace.get_base_action_mask(num_agents, device)` (72–90) allocates `torch.ones(num_agents, self.action_dim, dtype=torch.bool, device=device)` on every call, clears disabled columns by enumerating `self.actions`, then returns that allocation. `action_dim` is `len(self.actions)` (36–42). The returned dense bool[N,A] has fresh tensor storage; it is not a retained/cached view or tensor alias to action-space state. Only this newly allocated tensor is written. No random operation, state assignment, simulator callback, VFS operation or history access occurs in that method.

`get_action_by_name(name)` (53–58) traverses the stored action list, compares names, returns the matching existing `ActionConfig`, or raises `ValueError`. It does not mutate or draw RNG. Its return is a live configuration object, not a copied immutable snapshot. The constructor retains the caller's actions list and enabled-name set (30–34); neither the list nor configs are globally immutable. Fixed supported configuration is the premise. Actual mask enabling consults each action's `enabled`, not the separately retained `enabled_action_names` set. No additional action-config implementation is needed to explain these named ordinary-field reads under that premise.

## Actual custom-mask behavior

`ItemActionHandler.compute_custom_action_masks(action_space, action_masks, agent_positions)` (243–272) returns immediately for no cached custom specs. Otherwise it iterates `custom_action_specs.items()` in stored dictionary order, looks up action name/id through the above action space (missing names are skipped), allocates a fresh bool[N] `available` initialized false, and follows one of two read paths:

- Inventory scope: enumerate actual `inventory.slots` rows; convert each row to a Python list; ignore `-1`; look up the instance in `inventory.items`; match `item.item_type`; stop at first matching item. No inventory method or mutation is invoked.
- Local scope: enumerate the supplied actual `agent_positions`; call `manager.world_of_agent(agent_idx)` and `manager.items_at(world, agent_pos)`; mark available if any returned item has matching type.

The only persistent/output tensor writes in this method are `action_masks[~available, action_id] = False`; other writes target local `available`. It does not enable a disabled action, execute a command, evaluate a verb condition/Effects program, call `agent_positions` stored callback, access meters/VFS/history, advance items/time or draw RNG. `command_name` is unpacked but unused during masking. The command/executor paths in this same file are separate interaction/dispatch methods and are not reached by mask computation. Construction cached custom specs once (57–60); mask reads do not rebuild them.

`agent_positions` is passed by reference. Iterated `agent_pos` tensors are views of its rows; this method does not write them but passes each to `items_at`. Thus proving the named handler locally read-only does not by itself certify its delegated geometry call against live-position mutation. No retained position alias is assigned by the mask method.

## Actual item lookup traversal and dependencies

`ItemManager.world_of_agent(agent_idx)` (321–324) is a static identity return, S1 world i = agent i. It has no range check, RNG, write or external helper. `world_state(world)` (330–333), used by `items_at`, checks bounds then returns the existing world object without mutation.

`items_at(world, position)` (355–368) takes a new Python list of `world_state(world).active.values()`; it excludes `held`. Empty active returns a fresh empty list without geometry. Otherwise it reads `substrate.position_dtype`, constructs a fresh tensor from ordinary item positions with that dtype on `position.device`, reshapes to `[len(active), substrate.position_dim]`, then calls:

`substrate.is_on_position(item_positions, position.to(dtype=dtype))`.

It converts the predicate result to a list and filters with `zip(active, here.tolist(), strict=True)`. Consequently result order follows active dictionary insertion order (documented spawn order), not VFS-row sorting or position-index set iteration. Result is a fresh list of the original `ItemInstance` references, not a deep snapshot. Shared held items can remain in active; lifted exclusive items reside in held and are excluded. This lookup does not pop/reorder storage or repair/rebuild a position index. No predicate means absence of items; an invalid shape/dtype/helper can raise rather than yielding a certified normal mask.

The new item-position tensor owns its storage. `position.to(dtype=dtype)` may return the original live position tensor/view when dtype already matches; there is no guaranteed defensive clone. The delegated predicate must not mutate either argument, including the second argument. No position/item/manager assignment, VFS read/write/evaluation, tick/expiry/respawn processing, history/log call or RNG draw occurs in the inspected lookup code. In particular `_grid_cells` lazy cache, item spawning/placement, scheduling, world RNG reseeding and lifecycle mutators are not called by `items_at` or `world_of_agent`. Those other methods visibly do mutate state/use RNG, so no globally pure manager/handler/action-space claim follows.

## Bounded staging verdict and exact external questions

The action-space freshness question is resolved: the actual builtin base call owns fresh bool[N,A]. The item/custom-mask path has no direct simulator or RNG writes; all its intentional writes are to the fresh working mask and local allocations. The only newly essential project helper reached by these named item reads is the selected supported substrate's `is_on_position`, plus its ordinary `position_dtype`/`position_dim` properties. No command compiler/executor, VFS evaluator, history API, item-row-world registry helper or lifecycle method needs opening for this named call graph. Imports and mutation methods existing in the same modules are not mask execution.

Exact remaining geometry question: for every supported selected builtin substrate, does `is_on_position` return a deterministic bool vector of active-item count for input `[M,D]` and single position `[D]`, without writing substrate/positions/items/RNG or either argument? The same predicate also has the mask builder's affordance input form `[N,D]` with its actual affordance position representation. Its returned shape, aspatial D=0 behavior, discrete equality and continuous radius semantics must follow actual implementation; this capsule does not infer them from observation normalization/visibility certificates. `position_dtype`/`position_dim` accesses must also be ordinary nonmutating fixed geometry reads. The second argument's possible live alias makes nonmutation an essential contract.

The mask-owner capsule separately leaves temporal `VTCAffordanceGateProgram.is_affordance_open` and its actual callback chain to their owner. That question remains external here; it is not a new dependency introduced by item traversal. Fixed reset-state freshness and guard/lock discipline across preparation/publication remain the ENV owner's question. No new arbitrary-callback or concurrent-mutation audit is requested.

Therefore one normal genuine all-active legal mask can be captured before publication with fresh bool[N,A] ownership and no direct writes from the action/item components examined here; the full-build no-simulator/no-RNG-write conclusion remains conditional only on the named supported geometry and temporal callback facts from their owners, with the fixed-state premise. Once those facts hold, retain that actual mask, derive a separate candidate by cloning it and clearing exactly retired rows, and complete all clone/validation/live-legal checks before publication. The mask-owner capsule establishes dones is used only for final row clearing, so this derivation matches local builder done semantics at unchanged dependencies. Never temporarily mutate ENV.dones, and do not invoke callbacks a second time merely to derive candidate rows. Retained masks are owned tensor values, not proof that live item/config/position state cannot subsequently change.
