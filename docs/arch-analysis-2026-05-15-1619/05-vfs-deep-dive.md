# VFS Subsystem — Completeness & Brittleness Deep Dive

**Date:** 2026-05-15
**Scope:** `src/townlet/vfs/` (2,299 LOC) + compile-side adapters (`universe/compilers/vfs.py`, `universe/adapters/vfs_adapter.py`) + runtime integration in `environment/vectorized_env.py`. Tests: 5,790 LOC under `tests/test_townlet/{unit,integration}/vfs/` and related directories.

**Method:** Read every VFS source file; cross-referenced 60+ importers across `effects/`, `items/`, `environment/`, `universe/`, `config/`; verified specific claims with grep/wc. The catalog in [`02-subsystem-catalog.md`](02-subsystem-catalog.md) treats VFS as part of the broader compilation pipeline; this document re-examines it as a standalone subsystem against a stricter rubric.

---

## Headline verdict

**Refactor incrementally; do not ship in current shape if VFS is on the production path.** The subsystem is functionally complete enough to run all five active config packs and is heavily covered by tests (5,790 LOC of tests for 2,299 LOC of source). But there is a single structural defect at its core that everything else is symptomatic of:

**`vfs/registry.py` defines two unrelated classes, `VariableRegistry` (line 35) and `ScopedVariableRegistry` (line 653), with no shared base.** The runtime instantiates `VariableRegistry` at `environment/vectorized_env.py:324` and then, at line 1028, lies to the type system via `cast(ScopedVariableRegistry, self.vfs_registry)` so that `build_vfs_observation` (which is typed against `ScopedVariableRegistry`) will accept it. The cast works only because both classes happen to expose `list_global` / `get_global` / `list_agent` / `get_agent` / `item_vfs` / `item_profile_map` with compatible semantics. It is duck-typing dressed as static typing.

Almost every other brittleness finding below — the direct `_storage` mutation, the `getattr` defensive lookups, the dual `get/set` vs `read/write` API, the type-universe mismatch — is downstream of this one. Unify the two registries (either merge into one, or define a real `Protocol`/ABC and have both implement it) and the rest of the recommendations sequence cleanly.

---

## 1. Completeness

What VFS *claims* to do, by reading the schema, the docstrings, and the public API. What it *actually delivers*, by reading the implementation and tracing call sites.

| Capability | Claimed | Delivered | Verdict |
|---|---|---|---|
| `global` scope (singleton state, shared across agents) | ✅ | ✅ via `VariableRegistry._storage` (`shape ()`) | Complete |
| `agent` scope (per-agent, observable by all) | ✅ | ✅ via `VariableRegistry._storage` (`shape (num_agents,)`) | Complete |
| `agent_private` scope (per-agent, owner-only) | ✅ | ⚠️ "owner-only" is enforced by a hard-coded `reader == "agent"` rejection (`registry.py:262–266`), not by a per-row mask. Any non-agent reader (engine, acs) can still read all rows. | Partial / by convention |
| `item` scope (per-item state via profiles) | ✅ | ⚠️ Implemented on a **second**, profile-based storage layout (`item_vfs: torch.Tensor[max_items, max_vars]`) reached via `read_item` / `write_item`, not `get` / `set`. Rejected from `variables_reference.yaml` despite the schema's Literal allowing it (`registry.py:418–422`). | Partial / mis-located |
| Variable types: `scalar`, `bool` | ✅ | ✅ | Complete |
| Variable types: `vec2i`/`vec3i`/`vec2f`/`vec3f`/`vecNi`/`vecNf` | ✅ | ✅ | Complete |
| Variable types: `tensor1d`/`tensor2d`/`tensor3d`/`tensorNd` | ✅ | ✅ with `initial_value_mode` ∈ `{zeros, ones, eye, random_normal, random_uniform}` | Complete |
| Variable types: `agent_ref`, `item_ref` | ✅ | ✅ (long dtype, default −1 for "no ref") | Complete |
| Access control (`readable_by` / `writable_by`) | ✅ | ⚠️ Enforced by `get` / `set` (`registry.py:257, 296`) — **but bypassed by direct `_storage` mutation in `vectorized_env.py:1445`**. Not a universal invariant. | Partial / by convention |
| `lifetime: tick | episode | persistent` | ✅ Schema declares it | ❌ **Dead field.** Confirmed: `grep -rn '\.lifetime' src/townlet/` returns zero non-test hits. No code reads it; tick-lifetime variables are not reset per-tick; episode-lifetime are not reset per-episode by the registry. Either remove the field or implement enforcement. | **Declared, never delivered** |
| Expression DSL (`var.expression`) | Schema says "Phase 2: future work" (`schema.py:7–8`, `WriteSpec` docstring) | ✅ **Phase 2 is shipped** — `vfs/profiles.py:213–272`, `world/expression/*`, `compilers/vfs.py` all parse, type-check, and evaluate expressions. The DSL note in the schema is doc drift. | Complete; docs lag |
| Topological sort over variable expression dependencies | ✅ | ✅ via networkx (`profiles.py:170–211`) with `CircularDependencyError` | Complete |
| Type-checked expressions at compile time | ✅ | ✅ via `TypeChecker.check()` (`profiles.py:253–257`) | Complete |
| Mark-and-sweep evaluation | ✅ | ⚠️ When `marks is None`, silently degrades to eager — see brittleness B-7. Functionally fine but the "and-sweep" claim is selectively honoured. | Complete but soft |
| Temporal history (`lag`, `delta`, `moving_average`, `ema`, `rate_of_change`, `rising_edge`, `falling_edge`) | ✅ | ✅ Window requirements collected at compile time (`history.py`) and replayed at runtime through `TemporalHistory` | Complete |
| Observation extraction (variables → flat tensor for agent obs) | ✅ | ✅ via `build_vfs_observation()` | Complete (but see B-3 for the perf footnote) |
| `VariableRegistry.read()` / `write()` (scope-based API used by Effects) | ✅ Method signatures present | ❌ **`NotImplementedError` for everything except ITEM scope** (`registry.py:484, 519`). Inline comment: "simplified implementation for testing". Effects can only use scope-based read/write for items; for global/agent they must use `get`/`set` with reader/writer strings. | **Declared, half-delivered** |
| Variable observation marks (which scopes are exposed at curriculum level) | ✅ | ✅ via `extract_observation_marks` (`compilers/vfs.py:112–132`) | Complete |
| Integration test: full variable → observation flow | Test file present | ❌ `tests/test_townlet/integration/vfs/test_variable_to_observation_flow.py` is **0 bytes**. Integration stub never written. | Missing |

**Completeness summary:** the subsystem covers ~85% of its declared API at production quality. The gaps are concentrated in three places:

1. **`lifetime` is a dead field** (declared, no implementation, no reader).
2. **`read()` / `write()` is half-implemented** (works for items, raises for everything else, while `get` / `set` covers those other scopes via a separate signature).
3. **One integration test is a stub.**

None of these are show-stoppers for current curriculum levels, but every one of them is a place where a config / API change can pass review and break silently.

---

## 2. Brittleness

Twelve concrete failure modes, each with a file:line citation and a description of what silently goes wrong. Ordered by severity.

### B-1. The two registry classes are not related, but the runtime treats them as one

**Where:** `vfs/registry.py:35` defines `class VariableRegistry:` and `vfs/registry.py:653` defines `class ScopedVariableRegistry:` — no inheritance, no shared base, no `Protocol`. They have different storage layouts (`_definitions` + `_storage` dicts vs. three `_global_storage`/`_agent_storage`/`_item_storage` dicts) and different access APIs.

**The lie:** `environment/vectorized_env.py:324` instantiates `VariableRegistry`. `vectorized_env.py:1028` does `cast(ScopedVariableRegistry, self.vfs_registry)` so it can pass to `build_vfs_observation`, which is typed against `ScopedVariableRegistry`. The cast happens to work because both classes expose `list_global` / `get_global` / `list_agent` / `get_agent` / `item_vfs` / `item_profile_map` with compatible semantics — but nothing in the type system or the test suite enforces that compatibility.

**Why it breaks silently:** if someone renames a method on `ScopedVariableRegistry`, mypy will be satisfied (the cast hides everything), but `build_vfs_observation` will raise `AttributeError` at runtime — and only when an item-bearing curriculum runs.

**Fix shape:** define `VFSRegistryProtocol` (or an ABC) and make both registries implement it; remove the cast. Or merge the two classes outright — there is no reason for two parallel storage layouts.

### B-2. Direct `_storage` mutation bypasses access control and shape validation

**Where:** `environment/vectorized_env.py:1441–1445`:

```python
expected_dtype = self.vfs_registry._expected_dtypes.get(var_name, torch.float32)
if value.dtype != expected_dtype:
    value = value.to(dtype=expected_dtype)
# Direct storage access - bypasses shape validation for engine writes
self.vfs_registry._storage[var_name] = value.to(self.vfs_registry.device).clone()
```

The inline comment is honest about what's happening: the post-evaluation writeback bypasses `set()` to avoid its shape check. The justification (a few lines above): bar-referencing expressions produce batched `[num_agents]` results even for `scalar`-declared variables; `set()` would reject this. So the runtime knowingly violates the registry's own invariant.

**Why it breaks silently:** the access-control contract (`writable_by=["engine"]`) is enforced by `set()`. The hot path doesn't call `set()`, so it doesn't enforce the contract. A misconfigured variable with `writable_by=[]` would be writable by the engine anyway. The "engine has god-mode" rule is conventional, not enforced.

**Fix shape:** add `set_unchecked()` (or `_set_engine_internal()`) as a first-class registry method that documents why shape isn't validated and at least logs/asserts writer identity. Stop reaching into `_storage`.

### B-3. Dual API: `get`/`set` (reader/writer strings) vs. `read`/`write` (scope enum)

**Where:** `vfs/registry.py:228–309` defines `get(variable_id, reader: str)` and `set(variable_id, value, writer: str)`. Lines 451–519 define `read(variable_id, context_index, scope: VariableScope)` and `write(...)` which `raise NotImplementedError` for non-ITEM scopes.

**The split:** `Effects` runtime context (`effects/context.py`) uses `read`/`write` for items; `vectorized_env.py` uses `get`/`set` for globals and agents. Two callers, two APIs, partial overlap. There is no documented reason for the split — it reads like an in-progress migration that stopped.

**Why it breaks silently:** new callers must guess which API to use. A reasonable developer reading `registry.read()` first would assume it's the canonical method and hit `NotImplementedError` on agent-scope variables — at runtime, not at type-check time.

**Fix shape:** pick one. Most likely: keep `get`/`set` for hot-path tensor access (with reader/writer strings encoding the access-control identity), make `read`/`write` either delete-on-sight or rename to `read_item`/`write_item` to match what they actually do.

### B-4. Two parallel from-profiles paths in `VFSObservationSpec`

**Where:** `vfs/observation_builder.py:79–159` (`from_profiles`) and `vfs/observation_builder.py:161–234` (`from_compiled_profiles`). The bodies are ~80% identical: both iterate over global / agent / item profiles, filter by `exposed_to`, sum dimensions, build `item_profile_vars`.

**Why it breaks silently:** when someone adds a new observation type (or changes how `exposed_to` is filtered), they have to remember both. Drift between them produces a "looks right under uncompiled DTOs but wrong under cached `CompiledUniverse`" bug — exactly the kind of pre/post-cache divergence the cache fast-path makes hardest to catch.

**Fix shape:** extract a `_compute_dims_from_iter(global_iter, agent_iter, item_iter)` core; both public classmethods become thin shims.

### B-5. Type universe mismatch between profile-side and registry-side

**Where:** `VariableDef.type` (`schema.py:261`) is a `Literal` containing `"scalar"` and 13 others. `_variable_observation_dim` (`observation_builder.py:31`) accepts `{"int", "float", "bool", "agent_ref", "item_ref", "affordance_ref", "effect_ref", vec*, tensor*}` — and **does not accept `"scalar"`**. `CompiledVariable.type` (`profiles.py:34`) is a bare `str`. The bridge: `VFSCompiler._normalize_runtime_vfs_type` (`compilers/vfs.py:269–275`) maps `int|float → scalar`.

**Cuts both ways:**

- **Completeness:** the bridge function works; the system is self-consistent in practice.
- **Brittleness:** any code path that bypasses `_normalize_runtime_vfs_type` and sees raw profile types (`int`/`float`/`affordance_ref`/`effect_ref`) will not be type-compatible with code paths that see runtime types (`scalar`). And `affordance_ref`/`effect_ref` are accepted by the observation-dim function but not declared anywhere in the schema's runtime type Literal — they may be dead branches, or they may be relied on by an unverified caller.

**Fix shape:** make `CompiledVariable.type` a `Literal` that matches the profile DTO's vocabulary, and document the bridge as the single point where translation happens. Audit `_variable_observation_dim` for the `affordance_ref`/`effect_ref` cases — confirm they're live or delete them.

### B-6. Item observation construction is a Python double-`for` loop on the hot path

**Where:** `vfs/observation_builder.py:338–356`:

```python
for agent_idx in range(batch_size):
    for slot_idx in range(spec.max_items_per_agent):
        vfs_idx = int(inventory_indices[agent_idx, slot_idx].item())
        if vfs_idx == -1:
            continue
        ...
        item_obs[agent_idx, dest_start:dest_end] = item_vfs_storage[vfs_idx, selected_indices]
```

For `batch=64, max_items_per_agent=3` that's 192 Python iterations per tick, each with a `.item()` GPU sync and an indexed assignment. In a codebase whose stated invariant is "no per-agent loops in the hot path" ([catalog §2 Subsystem 3](02-subsystem-catalog.md#3-environment-runtime--dac-reward-engine)), this is the largest visible perf regression.

**Why it breaks silently:** it works. Performance degrades roughly linearly with `batch_size × max_items_per_agent`; nothing tests perf so nothing catches it. A bigger curriculum (more agents, more inventory slots) will hit this before any other VFS issue.

**Fix shape:** rewrite as a vectorised `torch.gather` against `item_vfs_storage` with `inventory_indices` as the gather index, masking the `-1` slots. The work is comparable to the existing tensor gymnastics in `meter_dynamics.py`.

### B-7. Mark-and-sweep silently degrades to eager when `marks is None`

**Where:** `vfs/evaluator.py:117–122`:

```python
if marks is None:
    vars_to_eval = {var.name for var in profile.variables}
```

And `evaluator.py:137–138` silently ignores marks that are not part of this profile ("Ignore marks that are not part of this profile"). So passing `marks={"typo_var_name"}` evaluates **nothing extra** in that profile, while `marks=None` evaluates **everything**.

**Why it breaks silently:** mark-and-sweep is an optimisation. Both failure modes (typo → nothing; None → everything) are "the program still runs and produces plausible numbers," but with different perf characteristics. A `marks` typo that the developer thinks they're hitting will silently fall through.

**Fix shape:** require an explicit `evaluate_eager()` entrypoint when callers want all variables. Make `marks` non-`None` mandatory in `MARK_AND_SWEEP` mode and raise on marks that don't resolve.

### B-8. Defensive `getattr` lookups for attributes the registry always defines

**Where:** `vectorized_env.py:1427–1429`:

```python
item_vfs=getattr(self.vfs_registry, "item_vfs", None),
item_profile_map=getattr(self.vfs_registry, "item_profile_map", None),
item_index_to_profile=getattr(self.vfs_registry, "item_vfs_index_to_profile", None),
```

These attributes are **always** initialised on `VariableRegistry` (lines 94–98). The `getattr` defaults are dead. But they're an honest fingerprint of B-1: the author wasn't certain the registry was the type they thought it was, so they hedged. The same pattern appears at `vectorized_env.py:348`: `getattr(universe, "vfs_history_spec", None)` — the universe DTO always carries this field.

**Why it matters:** defensive lookups against a known type are a smell, not a bug. They suggest the contract isn't trusted; in this codebase that suspicion is justified (see B-1).

**Fix shape:** delete the defaults once B-1 is resolved and the registry's interface is enforced.

### B-9. Environment-variable behaviour switches violate the no-defaults discipline

**Where:** `vfs/evaluator.py:37` (`HAMLET_DEBUG_VFS`) and `environment/vectorized_env.py:346` (`VFS_EVAL_MODE`). Both gate behavioural changes (debug logging; mark-and-sweep vs. eager).

**Why it's a problem here specifically:** the project's [`CLAUDE.md`](../../CLAUDE.md) requires every behavioural parameter to be in config. These two env vars are off-config behaviour gates, and they don't appear in the no-defaults lint script's purview.

**Fix shape:** move both to the `vfs_profiles_config` DTO. Delete the env-var lookups.

### B-10. `exposed_to` default is applied in two places and could disagree

**Where:** `schema.py:335–336` (in the `VariableDef` post-init validator) and `profiles.py:234, 261` (`getattr(var, "exposed_to", []) or ["agent"]`). Both default to `["agent"]` when missing or empty.

**Why it breaks silently:** if one defaulting site is changed (e.g. to `["engine"]`), behaviour silently splits depending on whether a variable arrives via DTO construction or via compiled-profile construction.

**Fix shape:** delete the post-init mutation in `VariableDef.validate_vector_types` — leave the field strictly required at the schema layer — and remove the `or ["agent"]` fallbacks in `profiles.py`.

### B-11. ITEM scope rejected at registry, accepted at DTO

**Where:** `schema.py:257` lists `"item"` in `VariableDef.scope`'s Literal. `registry.py:418–422` raises `ValueError("Item-scoped variables in variables_reference.yaml are not supported...")` if any `VariableDef.scope == ITEM` is passed in.

**Why it breaks silently:** **it doesn't break silently** (it raises) — but the deferred validation is a footgun. A YAML author can pass DTO validation with `scope: item`, then watch the registry blow up at universe init time. The error message is clear, but the failure should be in the schema.

**Fix shape:** add a `model_validator` to `VariableDef` that rejects `scope == "item"` in `variables_reference.yaml`'s entry point, since item-scope variables are supposed to come from `vfs_profiles.yaml`'s `item_profiles` instead.

### B-12. `item_profile_map.get(name, {})` falls through to "no exposed vars"

**Where:** `vfs/observation_builder.py:334`: `idx_map = registry_profile_map.get(profile_name, {})`. If the registry has no entry for `profile_name`, this returns an empty dict; the subsequent `exposed_indices = [idx_map[name] for name in var_names if name in idx_map]` yields `[]`; the observation construction silently contributes zero dimensions for that slot.

**Why it breaks silently:** an item with an unknown profile name (typo, missing registration, stale cache) produces zero observation contribution rather than raising. Combined with B-6's `for`-loop structure, this means a misconfigured item is undiagnosable from telemetry.

**Fix shape:** `idx_map = registry_profile_map[profile_name]` (raise on miss) or explicit `raise RuntimeError` with the available profiles in the message.

---

## 3. Findings that cut both ways

Three findings are best understood as "the design is complete but the seam is fragile":

| # | Finding | Completeness | Brittleness |
|---|---|---|---|
| C-1 | `_normalize_runtime_vfs_type` (compilers/vfs.py:269) bridges `int`/`float` profile types to `scalar` runtime types | The bridge works; both vocabularies coexist | Two type universes; any path that bypasses the bridge sees the wrong vocabulary |
| C-2 | `evaluate_global_profile` takes 12 parameters, most Optional with `getattr` defaults | Every parameter is used by at least one code path | The contract is too broad to memorise; new state gets bolted on rather than factored into a context object |
| C-3 | `VFSObservationSpec` can be reconstructed from a serialised dict via `_vfs_observation_spec_from_plain` (compiled.py:666) | Cache deserialisation is complete | This is exactly the "rebuild config DTOs from artefacts" round-trip the prior compiler-cleanup pass flagged for elimination (see [compiler-cleanup discovery doc](../arch-analysis-2026-05-15-compiler-cleanup/01-discovery-findings.md) §"Runtime Consumption"); the modern `vfs_adapter.py` hasn't displaced it |

---

## 4. Test coverage signal vs. reality

The numerics are strong on paper: 5,790 LOC of tests vs. 2,299 LOC of source, a 2.5:1 ratio. But the topology of the tests tells a different story:

- **One integration test is a 0-byte stub** (`tests/test_townlet/integration/vfs/test_variable_to_observation_flow.py`).
- **Seven separate `test_expression_*` files** in `unit/vfs/` — granular unit coverage of the expression evaluator, but fragmented.
- **`test_registry.py` is 809 lines** — the largest VFS test file. Strong unit coverage of `VariableRegistry`'s `get`/`set` API. No coverage of `ScopedVariableRegistry`.
- **`test_scoped_registry.py` is 219 lines** — covers `ScopedVariableRegistry` independently. **No test exercises the `cast()` from one to the other.**
- **No perf test** for `build_vfs_observation`'s inner `for` loop (B-6).
- **No fuzz / property test** for `marks={typo}` (B-7) — the silent-skip behaviour is not asserted in either direction.

The tests are dense around the behaviour each registry promises in isolation, and sparse around the integration seams where the brittleness lives. A high coverage number is not a high confidence signal here.

---

## 5. Recommended refactor sequence

Ordered by impact × ease. R-1 is the keystone; R-2 through R-5 fall out of it.

### R-1. Unify the two registry classes

**Choose one:**

- **(a) Merge.** Have one `VariableRegistry` that supports all four scopes with one storage layout. Easiest if `ScopedVariableRegistry`'s separate dicts are an artefact of prototyping rather than a design point.
- **(b) Protocol.** Define `class VFSRegistryProtocol(Protocol):` with `list_global` / `get_global` / `list_agent` / `get_agent` / `item_vfs` / `item_profile_map` / `device`. Make both classes inherit (or re-tag with `@runtime_checkable`). Re-type `build_vfs_observation` against the protocol, delete the `cast()`.

Either way: **the keystone fix**. Without it, every other recommendation has to negotiate around the two-class split.

### R-2. Promote the engine's writeback to a typed registry method

Replace `self.vfs_registry._storage[var_name] = value.to(...).clone()` at `vectorized_env.py:1445` with a new `registry.set_engine(var_name, value)` that documents why shape isn't checked and asserts the writer identity. Then make `_storage` and `_expected_dtypes` actually private (rename to `__storage`, `__expected_dtypes` if needed; Python doesn't enforce, but linters can).

### R-3. Resolve the dual `get`/`set` vs. `read`/`write` API

- Delete `read()` and `write()` from `VariableRegistry` (the non-item branches raise `NotImplementedError` anyway).
- Rename the item-scope variants to `read_item` / `write_item` (they already exist; the `read` / `write` wrappers are pure indirection).
- Update `effects/context.py` to call `read_item` / `write_item` directly.

### R-4. Implement `lifetime` enforcement — or remove it

- If lifetimes are a real product requirement: have the registry expose `reset_tick_scoped()` and `reset_episode_scoped()` and wire them into the env's tick/reset paths.
- If not: delete the field from `VariableDef`. Right now it's a documented feature that does nothing.

### R-5. Vectorise the item observation extraction

Rewrite `build_vfs_observation` lines 338–356 as a `torch.gather` against `item_vfs_storage`, masking `-1` slots. Recommend benchmarking against the current Python loop with `batch ∈ {16, 64, 256}` × `max_items ∈ {3, 8}`. Expect 10×–50× speedup.

### Secondary cleanups (small, independent)

- Move `HAMLET_DEBUG_VFS` and `VFS_EVAL_MODE` env vars into config DTOs (B-9).
- Fix the docstring drift in `schema.py:7–8` and `WriteSpec.docstring` claiming "Phase 2: future work" — Phase 2 is shipped.
- Add a `model_validator` to `VariableDef` rejecting `scope == "item"` at the schema layer (B-11).
- Replace `getattr(self.vfs_registry, "item_vfs", None)` etc. at `vectorized_env.py:1427–1429` with direct attribute access once R-1 is done (B-8).
- Extract the shared core between `VFSObservationSpec.from_profiles` and `from_compiled_profiles` (B-4).
- Write the empty integration test (`test_variable_to_observation_flow.py`).
- Make `idx_map = registry_profile_map[profile_name]` raise on miss instead of falling through (B-12).
- Audit `_variable_observation_dim` for `affordance_ref` and `effect_ref` (C-1) — confirm live or delete.

---

## 6. Triage call

If you're asking "ship or refactor?" — refactor. Specifically, do **R-1 before anything depends on VFS for inference at scale.** The structural split between `VariableRegistry` and `ScopedVariableRegistry` is the kind of foundation crack that survives every other tidy-up. Once R-1 is in place, R-2 through R-5 are individually small (each a half-day to a day), and the secondary cleanups can be batched into a single sweep.

The dead `lifetime` field, the half-implemented `read`/`write`, the empty integration test, and the env-var behaviour switches are evidence that the subsystem is mid-evolution. That's fine for a pre-release codebase, but the next step is to land the structural changes before more callers accrete around the current shape. The runtime hub `vectorized_env.py` is already reaching into VFS internals at four places (lines 1028, 1038, 1441, 1445); every additional caller compounds the cost of getting R-1 right later.

**Confidence:** High on the structural assessment (B-1, B-2, B-6, B-7, R-1 are all verified by direct source-and-grep evidence). Medium on the perf claim in B-6 (the `for`-loop is real; the projected speedup is reasoning by analogy with similar GPU rewrites in `meter_dynamics.py`, not measured). High on completeness gaps (the `.lifetime` and empty-test claims are both confirmed by grep / wc).
