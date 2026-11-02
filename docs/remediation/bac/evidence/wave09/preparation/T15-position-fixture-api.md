# T15 ENV position fixture API — finite supplier supplement

Read-only static supplement, 2026-11-01, HEAD `75bc8e438caaf4eadf8f4e0f6b522f84c680c1e7`. Reuses the already-read **five complete files / 2609 lines**. No sixth substrate/DTO/mask-builder/encoder/helper source was opened.

| Complete source | Lines | Unchanged SHA256 |
|---|---:|---|
| `src/townlet/environment/vectorized_env.py` (ENV) | 1714 | `849cacc1b94e13109d3ba5391b1d30668a89db308a3e228f3476a0f5457b595d` |
| `tests/test_townlet/_fixtures/environment.py` (FE) | 460 | `21bd79b1736efd53fdacb76ca6a6f4abaf3917340204aef74994ba20b6af745c` |
| `tests/test_townlet/_fixtures/config.py` | 145 | `f25801c31ddb8354cc8b63a25fa145b518a65c05b275d19f558cf6f4e3f04fb8` |
| `tests/test_townlet/helpers/config_builder.py` | 181 | `3cc6dc19e579d03835692146ee88f4befada29c403174cfa406049c4a4d2235a` |
| `tests/test_townlet/_fixtures/brain_configs.py` | 109 | `aac8397902f8f038bee0c3da913c1a6b3930478d70c8a82156898231605cc9f4` |

**Position access is source-proven:** `env.positions` is an ordinary public instance tensor attribute, initialized at ENV310–314 with shape **`[env.num_agents, env.substrate.position_dim]`**, dtype `env.substrate.position_dtype`, device `env.device`. It is not a guessed alias for observations or a copy returned by a getter. ENV402 passes the live tensor into the observation-publish context; ENV1052 passes that live tensor to action-mask construction. The tensor at `info['positions']` is instead a clone (ENV1210), so editing that returned snapshot does not edit the live attribute.

**No public agent-position setter/validator is defined in the complete ENV source.** The class's own initialization/reset assigns `self.positions`, but this alone is not a source-backed validation/synchronization contract for an external boundary-state edit. Python/Torch mutability of this ordinary attribute is distinct from a verified supported fixture mutation API. The public `set_affordance_positions` at ENV1555–1567 changes affordance layout, not agent positions; do not use it as an agent setter.

**Public masks:** `env.get_action_masks()` at ENV1043–1059 returns the documented bool tensor `[num_agents, action_dim]`, with True meaning valid. Every call invokes the external builder using current `self.positions`, dones, inventory/item state, affordances and opening predicate. ENV298–307 describes this builder as stateless with per-tick state passed to it; no local ENV mask-cache refresh method is present. The actual grid out-of-bounds movement law still belongs to the excluded builder/substrate implementation and is not proved by this delegation alone.

**Observation refresh boundary:** the direct current-state serializer is private **`env._get_observations()`**, ENV876–878, which calls the excluded encoder with a freshly built publish context. There is no public observation-only getter/refresh method in this complete class. Public `reset()` returns observations (ENV756–845) but rebinds/randomizes agent positions at779–788, resets clocks/state, and is not a refresh after an edit. Public `step(...)` returns observations but executes transitions and advances the clock (ENV1061–1218). Neither is an observation-only synchronization API.

**No exact authored deterministic agent-spawn declaration is visible in these five sources.** ENV775–788 uses `randomize_affordance_positions()` or `substrate.initialize_positions(..., generator=None)`; even configured affordance positions leave agents randomly initialized (ENV785–788). ENV1631–1714 describes collision-free sampling helpers, not an explicit agent spawn declaration. FE's visible position edits at441–453 affect affordance deployment; its explicit continuous3d bounds at405–426 do not establish a grid-boundary contract. Fixture docstrings saying “8×8” or “3×3” are not proof of current compiled grid geometry.

**Precise remaining producer boundary for root:** this context establishes live position access and public mask recomputation, but not a complete supported deterministic grid-boundary fixture. A separate supplier must establish the selected grid's coordinate/bounds semantics, the actual boundary-mask rule, and the supported way to install agent coordinates while keeping any associated observation/VFS/motion state coherent (or an actual deterministic authored spawn route). If a public observation-only API is required, that supplier must name it rather than relabel the private serializer. No boundary coordinate literal, setter spelling, private refresh permission or “zero is a boundary” claim is invented here.

Only this ignored receipt was written. Fresh postwrite readback/HEAD/source count/hash/ignore checks verify custody, not runtime acceptance. No imports/runtime, source/tests/index/metadata edits, branch/worktree/copy/subagent or gate activity was performed. Runtime remains paused; return stationary.
