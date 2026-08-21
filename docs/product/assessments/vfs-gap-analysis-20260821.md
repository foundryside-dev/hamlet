# VFS capability surface: ACTUAL vs DECLARED

**Tracker:** hamlet-dd05122527
**Date:** 2026-08-21
**Author:** independent gap analyst (fresh eyes; no trial records or tracker read before the sweep)
**Scope:** the Variable & Feature System — every member of its declared config vocabulary,
classified by execution.

---

## 1. Tree state and method

### Tree state

The tree moved under this analysis mid-run; both states are recorded because honesty about
what was measured is load-bearing.

| moment | `git rev-parse HEAD` | `git diff --stat src/townlet/` |
|---|---|---|
| session start | `6e3b53a587f4c65b750b92a8a8cd54095a9f08c3` | `effects/context.py +7`, `effects/executor.py +21/-4`, `universe/compilers/effects.py +16/-2`, `world/expression/context.py +6` (44 insertions, 6 deletions, 4 files) |
| session end | `0f0f2b5771891cc77807cfc9a8f2f8d4c9a8cd93` — *"fix(vfs): expressions honor a variable's declared scope — the global expression-write class opens (hamlet-cf16cdb6c4)"* | clean |

**The code content did not change.** The four-file global-scope fix that was uncommitted at
start was *committed* (not reverted) by a concurrent session at `0f0f2b57`. Every compiled
artifact this analysis produced carries
`compiler_git_sha='0f0f2b5771891cc77807cfc9a8f2f8d4c9a8cd93'`, so **all verdicts below were
measured against the fix-applied tree**. Cells that plausibly depend on that fix are flagged
`[dep: cf16cdb6c4]`.

`docs/architecture/vfs.md` is modified in the working tree by another session; untouched here.

**A second concurrent edit landed while §6 was being written**: `src/townlet/universe/__main__.py`,
`compiled.py`, `compiler.py` plus a new
`tests/test_townlet/unit/universe/test_agent_profile_cache_serialization.py` appeared in the
working tree — evidently work on `hamlet-a141ab5db3`. **Every verdict in this document was
measured before those edits**, on `0f0f2b57` with a clean `src/`. Only G-17 plausibly
intersects them; re-check G-17 against the tree rather than against this document.

### Method

Two evidence layers, and the distinction is enforced:

- **L2 (authoring)** — YAML written into a scratch pack → `UniverseCompiler().compile(pack,
  primary_level=...)` in-process → `VectorizedHamletEnv(...)` → `reset()` → `step()` → assert
  on registry storage and/or the observation row. **A WORKS verdict requires L2.**
- **L1 (mechanism)** — direct `VariableRegistry` / registry-API calls, no config route. L1 alone
  never yields WORKS; it characterises mechanism only.

Every WORKS verdict carries a **negative control**: the declared value was changed and the
observed behaviour was required to change with it. A probe that only saw the positive case is
reported as inconclusive, not as WORKS.

Base pack: a copy of `configs/simple` (grid 8×8, 4 meters, 4 affordances, one level
`L0_simple`, baseline `observation_spec.total_dims=108`).

**Stale-artifact check.** `configs/simple/.compiled/universe-L0_simple.msgpack` exists and
carries `compiled_schema_version: '1.17'` against the tree's `COMPILED_SCHEMA_VERSION = "1.18"`
(`universe/compiled.py:66`). Every scratch pack therefore inherited an artifact that *always*
fails the version gate, logs `Compiled universe schema mismatch ... found '1.17', expected
'1.18'`, and falls back to a fresh in-process compile. **No verdict below rests on a cached
artifact.** Probes:
`/tmp/claude-1000/-home-john-hamlet/e2011576-c34c-4ad0-af75-30cd3c19c2d7/scratchpad/vfs-gap-analysis/`
(`p00`–`p11`, logs under `logs/`). These are scratch and will not survive the session; every
verbatim refusal needed downstream is reproduced inline below.

Verdict vocabulary as commissioned: **WORKS** / **ABSENT** (no config key exists — an unbuilt
option, not debt) / **INERT** (declares, validates, compiles clean, does nothing) / **BLOCKED**
(declared and refused loudly).

---

## 2. The enumeration — the coverage contract

This is the declared vocabulary, read from source. Every row is either probed with a verdict in
§3, or listed in §5 as NOT PROBED with a reason.

### 2.1 Declaration surfaces (four, with sharply different powers)

| surface | file | DTO | scopes it can name | lifetime | access roles | init sources |
|---|---|---|---|---|---|---|
| **environment variables** | `environment.yaml` `environment.variables[]` | `config/environment_config.py:248 VariableConfig` | `global`, `agent`, `agent_private` | **none** — hardcoded `"tick"` (`compilers/observation.py:866`) | **none** — hardcoded `readable_by=["agent","engine"]`, `writable_by=["engine"]` | none (default 0.0 / zero-vector) |
| **global profile** | `vfs_profiles.yaml` `global_profile.variables[]` | `config/vfs_profiles_config.py:22 GlobalVFSVariableConfig` | `global` only (implied) | **none** — hardcoded `"persistent"` (`compilers/vfs.py:90`) | **none** — hardcoded (`compilers/vfs.py:283-284`) | `initial_value` \| `initial_value_mode` \| `expression` (XOR-validated) |
| **agent profile** | `vfs_profiles.yaml` `agent_profile.variables[]` | `AgentVFSVariableConfig` | `agent` only (implied) | **none** — hardcoded `"episode"` (`compilers/vfs.py:94`) | **none** — hardcoded | same XOR trio |
| **item profiles** | `vfs_profiles.yaml` `item_profiles[].variables[]` | `ItemVFSVariableConfig` | `item` only (implied) | n/a | n/a | `initial_value` \| `expression` (XOR) |
| **static overlay** | `variables_reference.yaml` (optional, pack root) | `vfs/schema.py:392 VariableDef` | **all nine** except `item` (rejected) | `tick` \| `episode` \| `persistent` | `readable_by` / `writable_by` free-string lists | `default`, `initial_value_mode`, `initial_value_params` |

`variables_reference.yaml` is the *only* surface that lets an author name a scope, a lifetime,
or an access-control role. Everything else is compiler-assigned.

### 2.2 Scopes — `VariableScope`, `vfs/schema.py:30`

`global`, `agent`, `agent_private`, `item`, `pair`, `group`, `affordance`, `zone`, `message`.

Runtime allocation is `VariableRegistry._scope_prefix_shape` (`vfs/registry.py:452`). The
**only** construction site is `environment/vectorized_env.py:621`, which passes
`num_agents`, `device`, `max_items`, `num_affordances`, `item_profiles` — and **not**
`num_groups`, `num_zones`, `num_message_slots`, `pair_storage_mode`, `pair_edges`,
`dynamic_variable_mode`.

### 2.3 Types

- `VariableDef.type` (17): `scalar`, `bool`, `vec2i`, `vec3i`, `vec2f`, `vec3f`, `vecNi`,
  `vecNf`, `agent_ref`, `item_ref`, `affordance_ref`, `effect_ref`, `tensor1d`, `tensor2d`,
  `tensor3d`, `tensorNd`, `message_token`.
- `GlobalVFSVariableConfig.type` (13): `int`, `float`, `bool`, `vec2i`, `vec3i`, `vecNi`,
  `vecNf`, `agent_ref`, `item_ref`, `tensor1d/2d/3d/Nd`.
- `AgentVFSVariableConfig.type` (15): the above + `affordance_ref`, `effect_ref`.
- `ItemVFSVariableConfig.type` (9): `int`, `float`, `bool`, `vec2i`, `vec3i`, `agent_ref`,
  `item_ref`, `affordance_ref`, `effect_ref`.
- `VariableConfig.type` (2): `scalar`, `vector`.
- The compiler's runtime type gate `_RUNTIME_VFS_TYPES` (`compilers/vfs.py:19`) admits only
  10: `scalar`, `bool`, `tensor1d/2d/3d/Nd`, `agent_ref`, `item_ref`, `affordance_ref`,
  `effect_ref` (+ `int`/`float` normalised to `scalar`).

### 2.4 Lifetimes

`tick` \| `episode` \| `persistent`. Reset semantics: `reset_tick_scoped()` (tick only) called
at the top of `step()` (`vectorized_env.py:1014`); `reset_episode_scoped()` (tick+episode)
called by `reset()` (`vectorized_env.py:823`). `persistent` is restored by neither.

### 2.5 Access control

`readable_by` / `writable_by`, open string lists, enforced in `registry.get` (`:513`),
`registry.set` (`:552`), `registry.set_engine_value` (`:579`), plus the `agent_private` special
case in `get` (`:518`). The docstrings name `agent`, `engine`, `actions`, `vtc`, `social_model`,
`acs` as the vocabulary.

### 2.6 Init sources

`initial_value`; `initial_value_mode` ∈ {`zeros`, `ones`, `eye`, `random_normal`,
`random_uniform`} with `initial_value_params`; `expression` (parsed + type-checked);
`default` (on `VariableDef`).

### 2.7 Write routes

1. affordance interaction `modify: vfs.X`
2. affordance interaction `modify: target.vfs.X`
3. affordance interaction `modify: self.vfs.X`
4. effect (`on_spawn`/`on_tick`/`on_despawn`) `modify: vfs.X`
5. effect `modify: target.vfs.X`
6. effect `modify: self.vfs.X`
7. item interaction (`on_use`/`on_pickup`/`on_drop`) `modify: self.vfs.X`
8. `initial_state` overrides on `spawn_item`
9. VTC action writes / `WriteSpec` (`composition` × 11, `phase`, `priority`, `clamp`,
   `condition`, `telemetry_label`)
10. VTC affordance occupancy claims (`claim_if_free`, `capacity_claim`)
11. global-profile expression writeback (`vectorized_env.py:1081`)
12. engine observation-primitive publication (`observation_encoder.py:175`)

### 2.8 Read routes

effect/affordance `value:` expressions; `if:` gates; item spawn `when:` predicates;
`drive.yaml` `extrinsic.variable_bonuses[]`, `modifiers.*.variable`,
`shaping[].type=vfs_variable`; the observation encoder; `_current_vfs_state()` (reads **every**
variable as `engine`, every phase, every step).

### 2.9 Observation exposure

`exposed_to` (profile surfaces); `observable` (`VariableDef`); `semantic_type` (closed
6-member vocabulary, `vfs/semantic_type.py`); `normalization` (`NormalizationSpec`, 9 kinds);
`curriculum_active`; the per-scope layout in `build_vfs_observation`
(`vfs/observation_builder.py:334`) and `_build_observation_field_from_vfs`
(`observation_encoder.py:51`).

---

## 3. The matrix

### 3.0 Tally

**Counting convention, stated so the denominator is auditable.** One cell = one
(capability member × declaration surface) pair that an author could write, where each *member*
of an enumerated vocabulary counts separately (each of the 17 types, each of the 5
`initial_value_mode` members, each of the 9 normalization kinds, each of the 9 scopes) and each
non-enumerated key counts once per surface (`lifetime` on 4 surfaces = 4 cells). Two
consequences worth flagging: a capability whose *whole vocabulary* is unreachable is counted by
its members, not as one — so `WriteSpec` contributes 16 ABSENT cells (11 compositions + phase +
priority + clamp + condition + telemetry_label), not 1. The earlier draft of this table counted
it as 1; corrected here.

| verdict | count | where the mass sits |
|---|---|---|
| **WORKS** | 63 | `variables_reference.yaml` type vocabulary (17); profile type vocabularies past the compiler gate (19); 3 lifetimes × 2 reset boundaries (6); DAC read routes (3); expression/gate read routes (3); the 2 reachable normalization methods; observation exposure for global/agent/vector/tensor/item (7); affordance write routes (3); effect bare-`vfs` route (2); item write+gate route (1) |
| **INERT** | 9 | `agent_private` privacy; global / agent / item expression evaluation (3); `pair` scope; `affordance` scope; `observable` on varref; `exposed_to` on varref; `normalization` on varref |
| **BLOCKED** | 26 | `group`/`zone`/`message`/`item`-via-varref scopes (4); 4 vec types × 2 profiles (8); 5 `initial_value_mode` × profile surface (5); global multi-rank tensor at the `num_agents` collision (1); item list-typed `initial_value` (1); effect `self.vfs` (1) and `target.vfs` (1); affordance `spawn_effect target: self` (1) and `self.vfs` (1); varref variables referenced from effects/affordances/DAC (1); non-`engine` `readable_by` (1) and `writable_by` (1) |
| **ABSENT** | 31 | `WriteSpec` (16); the 7 meter-only normalization kinds on the variable surface; `lifetime` on 4 surfaces; `readable_by`+`writable_by` on 3 profile surfaces (2, counted per key not per surface); `initial_value_mode` on `environment.yaml`; `normalization` on `vfs_profiles.yaml`; `curriculum_active`; sparse `pair` storage; `dynamic_variable_mode` |

129 cells. **The INERT column is the debt.** Nine cells, and two of them — `agent_private`
(G-1) and declarative expressions (G-2) — are the VFS's two most advertised authoring promises.
The ABSENT column is large but honest: per project rules it is a list of unbuilt options, not a
backlog. The BLOCKED column is loud and therefore comparatively cheap; the four cells in it
that fail *after* a clean compile (G-3, G-5, G-6, G-12) are the ones that behave like debt.

### 3.1 Scope × lifecycle

Probe: `p02_scopes_varref.py` (all nine via `variables_reference.yaml`, L2), plus
`p01_envyaml_scopes.py` and `p03_profile_types.py` for the profile surfaces.

| scope | declare | compile | env construct | storage shape (N=2) | read/write | verdict |
|---|---|---|---|---|---|---|
| `global` | ✔ | ✔ | ✔ | `()` | ✔ | **WORKS** |
| `agent` | ✔ | ✔ | ✔ | `(2,)` | ✔ | **WORKS** |
| `agent_private` | ✔ | ✔ | ✔ | `(2,)` | ✔ | **INERT as a privacy declaration** — see G-1 |
| `item` | ✔ | ✘ | — | — | — | **BLOCKED** at load (varref); **WORKS** via `item_profiles` |
| `pair` | ✔ | ✔ | ✔ | `(2, 2)` | ✔ (L1 only) | **INERT** — allocates, no author route in or out; see G-8 |
| `group` | ✔ | ✔ | ✘ | — | — | **BLOCKED** at env construction |
| `affordance` | ✔ | ✔ | ✔ | `(4,)` = affordance_count | ✔ (L1 only) | **INERT** — allocates, no author route; see G-8 |
| `zone` | ✔ | ✔ | ✘ | — | — | **BLOCKED** at env construction |
| `message` | ✔ | ✔ | ✘ | — | — | **BLOCKED** at env construction |

Verbatim refusals:

```
# scope: item, in variables_reference.yaml — compile, Stage 1
townlet.universe.errors.CompilationError: Stage 1: Load v2.1 Configs failed:
  - [LOAD_ERROR] .../variables_reference.yaml - Failed to load variables reference from
    variables_reference.yaml: variables_reference.yaml cannot define item-scoped variables;
    use vfs_profiles.yaml item_profiles.
```

```
# scope: group — VectorizedHamletEnv(...) construction
ValueError: Variable 'probe_var' uses group scope but num_groups must be positive
  File ".../townlet/vfs/registry.py", line 464, in _scope_prefix_shape
      return (self._positive_extent(var_def, "num_groups"),)
  File ".../townlet/vfs/registry.py", line 481, in _positive_extent
```

```
# scope: zone — VectorizedHamletEnv(...) construction
ValueError: Variable 'probe_var' uses zone scope but num_zones must be positive
  File ".../townlet/vfs/registry.py", line 468, in _scope_prefix_shape
```

```
# scope: message — VectorizedHamletEnv(...) construction
ValueError: Variable 'probe_var' uses message scope but num_message_slots must be positive
  File ".../townlet/vfs/registry.py", line 470, in _scope_prefix_shape
```

All three are the same mechanism: the extent parameter has no config route to
`vectorized_env.py:621`, so `_positive_extent` cannot ever be satisfied. `group` / `zone` /
`message` are unreachable **by construction**, not by accident of this pack.

### 3.2 Types × surface

Probes: `p03_profile_types.py`, `p04_items_and_tensornd.py`, `p10_varref_types_and_vtc.py`
(all L2: compile → construct → step).

**`variables_reference.yaml` (`VariableDef`) — all 17 types, agent scope, N=3:**

| type | verdict | storage |
|---|---|---|
| `scalar` | WORKS | `(3,)` f32 |
| `bool` | WORKS | `(3,)` bool |
| `vec2i` / `vec3i` | WORKS | `(3,2)` / `(3,3)` i64 |
| `vec2f` / `vec3f` | WORKS | `(3,2)` / `(3,3)` f32 |
| `vecNi` / `vecNf` | WORKS | `(3,4)` i64 / f32 |
| `agent_ref` / `item_ref` / `affordance_ref` / `effect_ref` | WORKS | `(3,)` i64 |
| `tensor1d/2d/3d/Nd` | WORKS | `(3,…shape)` f32 |
| `message_token` (dims=4) | WORKS *as storage* | `(3,4)` f32 — but nothing consumes it; see §5 |

**`vfs_profiles.yaml` global/agent profiles:**

| type | verdict | evidence |
|---|---|---|
| `int`, `float` | WORKS | normalised to `scalar`; one observation field emitted |
| `bool` | WORKS | bool storage; one observation field |
| `agent_ref`, `item_ref` (+ `affordance_ref`, `effect_ref` on agent) | WORKS | i64 storage; one observation field |
| `tensor1d` | WORKS | `global=(3,)` / `agent=(2,3)`; obs widens correctly |
| `tensor2d`, `tensor3d`, `tensorNd` — **agent** | WORKS | obs widens to `prod(shape)` |
| `tensor2d`, `tensor3d`, `tensorNd` — **global** | **BLOCKED at first step** when `shape[0] == num_agents` | G-3 |
| `vec2i`, `vec3i`, `vecNi`, `vecNf` | **BLOCKED at compile** | G-4 |

```
# vecNf (and vec2i / vec3i / vecNi) in vfs_profiles.yaml, either profile
ValueError: Unsupported VFS variable type 'vecNf' for variable 'probe_var'.
  Valid types: ['affordance_ref', 'agent_ref', 'bool', 'effect_ref', 'item_ref', 'scalar',
                'tensor1d', 'tensor2d', 'tensor3d', 'tensorNd']
  File ".../townlet/universe/compilers/vfs.py", line 298, in _normalize_runtime_vfs_type
```

```
# global tensor2d shape [2,2] with num_agents=2 — first env.step()
ValueError: global_active_mask length 4 does not match global_vfs_dim 2.
  File ".../townlet/vfs/observation_builder.py", line 329, in _apply_active_mask
```

**`item_profiles` — all 9 types:** every one compiles and constructs. Storage is one f32
column per variable in `item_vfs [max_items, max_profile_vars]`. `vec2i` / `vec3i` widen the
*observation* to 2 / 3 dims but still get a single storage column, and crash at spawn (G-6).

**`environment.yaml`:** `scalar` and `vector` (with `dims`) only — WORKS, negative control in
`p01`. Tensor types are unreachable here; `compilers/observation.py:837-856` contains a
tensor-type branch (`is_tensor`, `initial_value_mode`, `initial_value_params` reads) that
`VariableConfig` can never satisfy — dead code, not an author surface.

### 3.3 Init sources

| cell | surface | verdict | evidence |
|---|---|---|---|
| `initial_value` | global/agent profile | **WORKS** | negative control `p03`: 3 → storage 3.0, 0.5 → 0.5 |
| `initial_value` | item profile | **WORKS at spawn** | `p09` J1: declared 42.0 → `item_vfs[[42.0],[0.0]]` after `spawn_item`; 7 → 7.0; `True` → 1.0. **Not** applied at registry allocation (zeros until an item spawns) |
| `initial_value` (list types) | item profile | **BLOCKED at spawn** | G-6 |
| `initial_value_mode` ×5 | global/agent profile | **BLOCKED at compile, all five** | G-5 |
| `initial_value_mode` ×5 | `variables_reference.yaml` | **WORKS, all five** | `p07` M2: `zeros`→`[0,0,0,0]`, `ones`→`[1,1,1,1]`, `eye`→`[1,0,0,1]`, `random_normal(mean=5,std=.001)`→`~5.0`, `random_uniform(low=7,high=7.001)`→`~7.0` |
| `initial_value_mode` | `environment.yaml` | **ABSENT** (no key) | `extra_forbidden` on `environment.variables.0.initial_value_mode` |
| `initial_value_params` | `variables_reference.yaml` | **WORKS** | mean/std and low/high both observed above |
| `expression` | global profile | **INERT under the shipped `mark_and_sweep`** | G-2 |
| `expression` | agent profile | **INERT unconditionally** | G-2 |
| `expression` | item profile | **INERT unconditionally** | G-2 |
| `default` | `variables_reference.yaml` | **WORKS** | all 17 types in `p10` T1 |

```
# initial_value_mode: <any of zeros|ones|eye|random_normal|random_uniform>
# in vfs_profiles.yaml global_profile or agent_profile — compile
AttributeError: 'NoneType' object has no attribute 'expandtabs'
  File ".../pyparsing/core.py", line 1332, in parse_string
      instring = instring.expandtabs()
```

```
# item profile variable of type vec2i with initial_value [1, 2] — at ItemManager.spawn_item
TypeError: float() argument must be a string or a real number, not 'list'
  File ".../townlet/items/manager.py", line 358, in spawn_item
      item_vfs[vfs_index, var_idx] = float(compiled_var.initial_value)
```

### 3.4 Write routes × scope

Probes `p05b`, `p05c`, `p06`, `p09` — every one carries the in-list positive control
`modify: target.bar.energy` (energy must drop) and asserts `successful_interactions` is
non-empty, so an "it did not fire" is never mistaken for INERT.

| # | route | target scope | verdict | evidence |
|---|---|---|---|---|
| 1 | affordance `modify: vfs.X` | global profile | **WORKS** `[dep: cf16cdb6c4]` | `gvar` 0 → 10.0; control energy 1.0 → 0.49 |
| 1b | affordance `modify: vfs.X` | agent profile | **WORKS with a semantic hazard** | writes the WHOLE batch, once per interacting agent: 2 agents × +5 → both read 10.0. See G-9 |
| 2 | affordance `modify: target.vfs.X` | agent profile | **WORKS** | `avar` → `[5.0, 5.0]` |
| 2b | affordance `modify: target.vfs.X` | `environment.yaml` agent var | **WORKS within the tick** | `envvar` → `[5.0,5.0]`, observed at col 102 as 0.05; wiped next tick (G-7) |
| 3 | affordance `modify: self.vfs.X` | any | **BLOCKED** | `ValueError: self_index not set - cannot use 'self' target` — `affordance_engine.py:512` sets `self_index=None` ("Affordances don't have self yet") |
| 4 | effect `modify: vfs.X` | global profile | **WORKS** `[dep: cf16cdb6c4]` | `on_spawn`+`on_tick`: 0 → 22 → 42 → 62 → 82 |
| 4b | effect `modify: vfs.X` | agent profile | **WORKS with the same hazard** | whole-batch write per effect instance: `[20,20]`→`[40,40]`→`[60,60]`. G-9 |
| 5 | effect `modify: target.vfs.X` | agent profile | **BLOCKED at runtime** | `KeyError: 'avar'` — `executor.py:71`; `target_vfs` is only populated when `target_index is not None`, and `EffectManager.spawn_effect` sets `self_index=target_entity_id, target_index=None` (`manager.py:225-226`). Compiles clean. G-10 |
| 6 | effect `modify: self.vfs.X` | agent profile | **BLOCKED at compile** | the effects schema never emits `self.vfs.*` for non-item variables. G-10 |
| 7 | item `on_use` `modify: self.vfs.X` (+ `if: self.vfs.X > 0` gate) | item | **WORKS** | full lifecycle, negative control below |
| 8 | `spawn_item(initial_state=...)` | item | **NOT PROBED** (no author surface found for it in `items.yaml`) |
| 9 | VTC action writes / `WriteSpec` | any | **ABSENT** | G-11 |
| 10 | VTC occupancy claims | affordance | **ABSENT** (same: no `WriteSpec` surface) |
| 11 | global-profile expression writeback | global profile | **INERT under `mark_and_sweep`** | G-2 |
| 12 | engine observation-primitive publication | agent | **WORKS** (engine-internal, not an author surface) | baseline `p00` |
| — | `modify: vfs.X` where X is `pair`/`affordance`-scoped | pair, affordance | **BLOCKED at compile** | G-8 |

```
# effect on_spawn: modify self.vfs.<agent profile var> — compile, Stage 6
CompilationError: Stage 6: Enrich shared schemas and effects failed:
  - [VFS-PROFILE-COMPILE] .../vfs_profiles.yaml - Effect 'abump' failed to compile:
    Path 'self.vfs.avar' not found in schema. Available: ['intensity', 'elapsed_ticks',
    'duration_remaining', 'bar.energy', 'target.bar.energy', ..., 'vfs.avar',
    'target.vfs.avar']
```

```
# effect on_spawn: modify target.vfs.<agent profile var> — first env.step()
KeyError: 'avar'
  File ".../townlet/effects/manager.py", line 238, in spawn_effect
  File ".../townlet/effects/executor.py", line 165, in _execute_modify
  File ".../townlet/effects/executor.py", line 71, in get
      return self.target_vfs[".".join(parts[2:])]
```

```
# affordance on_start: spawn_effect target: "self" — first env.step()
ValueError: self_index not set - cannot use 'self' target
  (effects/executor.py:206; affordance_engine.py:512 passes self_index=None)
```

**Route 7 evidence (L2, `p09` follow-up).** `items.yaml` `on_use`:
`if: self.vfs.durability > 0.0` → `then: [modify target.bar.energy +0.1, modify
self.vfs.durability -1.0]`, `initial_value: 3.0`. Spawn → `GET` → four uses:

```
handle_get_action -> True   slots=[[0], [-1]]
use#0: item_vfs=[[2.0],[0.0]]  energy_delta=[+0.1, 0.0]
use#1: item_vfs=[[1.0],[0.0]]  energy_delta=[+0.1, 0.0]
use#2: item_vfs=[[0.0],[0.0]]  energy_delta=[+0.1, 0.0]
use#3: item_vfs=[[0.0],[0.0]]  energy_delta=[ 0.0, 0.0]   <-- gate stops firing at 0
after a real GET action through env.step(): slots=[[0], [-1]]
```

Both halves of the negative control hold: the write lands and decrements, and the `if:` gate
flips the behaviour off exactly when the declared condition goes false. The `GET` action
through `env.step()` also works. **Item scope is the one non-`global`/`agent` scope with a
complete, working declarative read+write+observe loop.**

*(Secondary, not a gap: `ItemManager.spawn_item` is type-hinted `position: tuple[int,...] |
tuple[float,...]` and stores the value verbatim, while `_position_index` coerces with
`tuple(int(c) for c in position)`. Passing a `torch.Tensor` — which nothing in config does —
produces an item that indexes correctly but can never be picked up, because
`action_handlers.py:165` compares `active_item.position == tuple(agent_position.tolist())`.
This cost me one wrong reading before I caught it; recorded so the next probe author does not
repeat it.)*

```
# affordance on_start: modify vfs.<pair- or affordance-scoped varref variable> — Stage 3
CompilationError: Stage 3: Reference Resolution failed:
  - [UAC-RES-VFS] .../affordances.yaml - Affordance 'SLEEP' interaction uses unknown VFS
    variable 'pvar'.
```

```
# actions.yaml custom_actions[].writes — Stage 1
CompilationError: Stage 1: Load v2.1 Configs failed:
  - [LOAD_ERROR] .../actions.yaml - Failed to load actions from actions.yaml:
    1 validation error for ActionsConfig
    actions.custom_actions.0.writes
      Extra inputs are not permitted [type=extra_forbidden, ...]
```

### 3.5 Read routes

| route | verdict | evidence |
|---|---|---|
| affordance/effect `value:` expression reading `vfs.X` | **WORKS** | `vfs.gvar + 5.0` compounds correctly across steps |
| affordance `if:` gate on `vfs.X` | **WORKS** | `if vfs.gvar < 1.0 then 99.0 else -99.0` selected the `then` branch |
| item `on_use` `if: self.vfs.X > 0` | **WORKS** | gate flips off at durability 0 — §3.4 route 7 |
| `drive.yaml` `extrinsic.variable_bonuses[]` | **WORKS** | `p11` D1, negative control: `avar` 0/3/7 → reward 1.0/4.0/8.0 at `weight: 1.0` |
| `drive.yaml` `modifiers.<m>.variable` | **WORKS** | `p11` D2b: `avar=0.0` (range `[0,0.5)`, mult 0) → `intrinsic_weight=[0,0]`; `avar=0.9` (range `[0.5,1]`, mult 1) → `intrinsic_weight=[1,1]` |
| `drive.yaml` `shaping[].type: vfs_variable` | **WORKS** | `p11` D3, negative control: `avar` 0/3 → reward 1.0/7.0 at `weight: 2.0` (Δ = 2×3) |
| `drive.yaml` referencing a `variables_reference.yaml` variable | **BLOCKED** | `[DAC-REF-005] ... Extrinsic variable bonus references undefined VFS variable: avar` |
| `_current_vfs_state()` reading every variable as `engine` | **WORKS** — and is what makes `readable_by` unusable (G-12) |

**Note on `modifiers.<m>.variable`:** the range validator requires ranges to start at 0.0 and
end at 1.0 regardless of source, so an unbounded VFS variable cannot be gated —
`Value error, Ranges must end at 1.0, got 100.0`. The route works; its domain is hardcoded to
the bar domain.

### 3.6 Observation exposure

| cell | verdict | evidence |
|---|---|---|
| `environment.yaml` var, `scope: agent` → observation field | **WORKS** | field emitted; negative control 50→0.5, 10→0.1 |
| `environment.yaml` var, `scope: global` → broadcast to all rows | **WORKS** | 70→0.7 in every agent's row |
| `environment.yaml` var, `scope: agent_private` → observed | **WORKS mechanically, INERT as privacy** | G-1 |
| `environment.yaml` var, `type: vector, dims: 3` | **WORKS** | 3 contiguous columns, all tracking |
| profile variable → its own observation field | **WORKS** | one field per exposed profile variable, width `prod(shape)` |
| `exposed_to: [agent]` | **WORKS as a gate** | field present, `global_vfs_dim=1` |
| `exposed_to: [engine]` / `[bac]` | **WORKS as a gate** (excluded) | field absent, `total_dims` back to 108 |
| `exposed_to: [agent, bac]` | **WORKS** (any list containing `agent`) | field present |
| `exposed_to: []` | **HIDDEN DEFAULT** | silently rewritten to `["agent"]` by `default_metadata` (`vfs_profiles_config.py:122/232/320`); field present. An author cannot declare "expose to nobody" |
| `exposed_to` on `variables_reference.yaml` | **INERT** | no observation field is emitted for varref variables under any value |
| `observable: true` on `variables_reference.yaml` | **INERT as "observable"**, repurposed as a mark | G-2 / G-13 |
| `normalization` on `environment.yaml` vars — `normalize` (→minmax) | **WORKS** | `clip:false` range `[0,10]`: 1→0.1, 3→0.3. `clip:true` range `[0,2]`: 1→0.5, 3→**1.0** (clamped) |
| `normalization` on `environment.yaml` vars — `standardize` (→zscore) | **WORKS** | mean 1, std 2: 1→0.0, 3→1.0 |
| the other 7 `NormalizationSpec` kinds on VFS variables | **ABSENT** | `NormalizationConfig.method` is `Literal["normalize","standardize"]`; the 9-kind vocabulary is reachable only for **meters** via `range_type` |
| `normalization` on `vfs_profiles.yaml` variables | **ABSENT** | `extra_forbidden` — no key |
| `normalization` on `variables_reference.yaml` | **INERT** | key accepted and validated, but varref variables get no observation field |
| `semantic_type` on profile/env variables | **WORKS** (required, closed vocabulary, drives group layout) | baseline field ordering |
| `curriculum_active` on VFS profile variables | **ABSENT + structurally dead** | `extra_forbidden` on the DTO; `CompiledVariable` has no such attribute (`hasattr(...) == False`), so `global_active_mask`/`agent_active_mask` are all-`True` by construction and `item_active_mask` is built as `tuple(True for _ in range(item_dim))` unconditionally |
| item variable → `obs_item_slots` | **WORKS** | negative control: `ivar` 5.0 → col 108 = 5.0; `write_item(...,99.0)` → 99.0. Requires the inventory slot to hold the item; a spawned-but-unheld item reads 0.0 |

### 3.7 Reset semantics × lifetime

Probe `p05c` L1/L2/L3, L2 evidence.

| lifetime | surface that can declare it | `step()` boundary | `reset()` | verdict |
|---|---|---|---|---|
| `tick` | varref only (hardcoded for `environment.yaml`) | **restored to default at the top of every step** | restored | **WORKS** (and is the mechanism behind G-7) |
| `episode` | varref; hardcoded for agent profile | survives | **restored** (5→10→15→20, then 0.0 after `reset()`) | **WORKS** |
| `persistent` | varref; hardcoded for global profile | survives | **survives** (20.0 before and after `reset()`) | **WORKS** |

`reset()` does **not** rebuild the registry (`reg is env.vfs_registry` → `True` across the
call), so `persistent` is genuinely persistent across episodes within one env instance.

---

## 4. Gap list

Ordered by product significance. INERT first, as commissioned.

---

### G-1 — `agent_private` is INERT: the privacy declaration does not privatize *(INERT, highest significance)*

**Surface.** `environment.yaml` `variables[].scope: agent_private`; also
`VariableScope.AGENT_PRIVATE`, documented at `vfs/schema.py:35` as *"Hidden from agent
observations"* and at `:400` as *"observable only by owner"*.

**Mechanism.** Two enforcement points exist and neither is on the observation path:

- `registry.get(reader="agent")` refuses (`registry.py:518`) — but **nothing in the runtime
  ever calls `get` with `reader="agent"`**. A grep of `src/townlet/` finds `reader="agent"` at
  exactly three sites, all inside docstring examples (`registry.py:94, 500, 504`). The only
  reader string the runtime passes is `"engine"` (6 sites) plus DAC's
  `vfs_reader = "engine"` (`dac_engine.py:78`).
- `observation_encoder._build_observation_field_from_vfs` (`:86`) branches
  `elif declared.scope in ("agent", "agent_private"):` — treating them identically — and reads
  through `registry.get_agent()`, which has **no access control at all**
  (`registry.py:774`).

**Evidence (L2, `p01`).** `probe_private` declared `scope: agent_private`,
`semantic_type: custom`, `normalization: normalize [0,100]`. It compiles to observation field
`probe_private` at columns `[103:104]`. Written to 99.0:

```
PRIVACY probe_private=99 -> agent0 row cols[103:104]=[0.99] agent1 row=[0.99]
registry.get('probe_private', reader='agent'): PermissionError: 'agent' is not allowed to
  read agent_private variable 'probe_private'. Only privileged readers (engine, acs, etc.)
  may access raw values.
registry.get_agent('probe_private')  [no access control]: [99.0, 99.0]
```

Negative control: 60→0.6, 20→0.2 — the column tracks. The value is not only observed, it is
observed *identically by every agent*, because the encoder broadcasts one variable into one
column per agent's own row — so the declaration is not merely a no-op, it is a no-op on a
surface an author will read as a guarantee.

**Product significance.** An author who writes `agent_private` to model hidden information
(a private goal, a secret inventory, an unobserved internal state) gets a fully observable
variable, silently, with no warning at compile or run. Every information-asymmetry mechanic
the framework advertises is unimplementable and *appears* implemented.

---

### G-2 — Declarative VFS expressions are INERT on the shipped default; the mark that revives them lives in a different file *(INERT, second-highest)*

**Surface.** `vfs_profiles.yaml` `global_profile` / `agent_profile` / `item_profiles`
variables declared with `expression:`, and `evaluation_mode: mark_and_sweep`.

**Three separate INERT cells:**

**(a) Global profile + `mark_and_sweep` + no `variables_reference.yaml` → never evaluated.**
`vectorized_env.py:1059` computes `marks = self.vfs_observation_marks.get("global", set()) if
self.vfs_observation_marks else set()`. `vfs_observation_marks` is `None` whenever the pack has
no `variables_reference.yaml` (`compiler.py:463`), so `marks` is the **empty set**, and
`VFSEvaluator.evaluate_global_profile` under `MARK_AND_SWEEP` evaluates `vars_to_eval = {}`.

Evidence (`p08` K2, L2), two chained expression variables under the shipped default:

```
K2: step0 a=[0.0] b=[0.0]   (expected a = 2*energy ≈ 1.98, b = a+1)
K2: step1 a=[0.0] b=[0.0]
```

Negative control by switching one key (`p07` E1):

| `evaluation_mode` | `variables_reference.yaml` | `derived` after step0 / step1 |
|---|---|---|
| `mark_and_sweep` | absent | `0.0` / `0.0` |
| `eager` | absent | `99.0` / `98.0` ✔ |
| `mark_and_sweep` | present, declaring `derived` with `observable: true` | `99.0` / `98.0` ✔ |

**`evaluation_mode: mark_and_sweep` is what every shipped pack declares** —
`configs/default_curriculum/vfs_profiles.yaml`, `configs/simple`, `configs/trial_f_durability`,
`configs/trial_b_blind_organism`. So the shipped default is the inert one, and the only way to
revive a global expression is to declare a *shadow variable of the same name* in
`variables_reference.yaml` with `observable: true` — a different file, a different DTO, a
different scope model, and a key whose name says "observable" while its function is
"evaluate this".

**(b) Agent-profile expressions are never evaluated in ANY mode.** `vectorized_env.py:1048-1081`
evaluates `compiled_vfs_profiles.global_profile` and nothing else; `evaluate_global_profile` is
called at exactly one site in the whole tree. Evidence (`p07` E2, `evaluation_mode: eager`):

```
E2 (eager): step0 energy=[0.99, 0.99] aderived=[0.0, 0.0]   (expression = energy*100)
E2 (eager): step1 energy=[0.98, 0.98] aderived=[0.0, 0.0]
```

**(c) Item-profile expressions are never evaluated.** Nothing in the runtime evaluates
`CompiledItemProfile.variables[].ast`. Evidence (`p08` I1, `eager`):

```
I1: step0 item_vfs=[[0.0], [0.0]]   (expr = energy*100, energy ≈ 0.99)
I1: step1 item_vfs=[[0.0], [0.0]]
```

Item expressions also cannot reference bars the way global/agent expressions do — the item
schema uses bare bar names, not the `bar.` namespace:

```
CompilationError: Stage 6: ... Path 'bar.energy' not found in schema.
  Available paths: ['energy', 'health', 'money', 'sustenance']
```

**Product significance.** "Derived state as config" is the VFS's headline authoring promise.
On the shipped default it produces a variable that compiles, gets an observation field, is fed
to the network — and holds its initial value forever. Two of the three profile kinds cannot be
revived at all.

---

### G-3 — A global tensor variable whose first dimension equals `num_agents` hard-fails at the first step *(BLOCKED, and live on a shipped pack)*

**Surface.** `vfs_profiles.yaml` `global_profile` with `type: tensor2d/3d/Nd`.

**Mechanism.** `_flatten_to_batch` (`observation_builder.py:511`) decides "already batched,
don't double-broadcast" from `value.shape[0] == batch_size` alone. For a *global* variable that
test is a coincidence, not a fact: a global `tensor2d` of shape `[2,2]` under `num_agents=2`
is reshaped to `(2, 2)` and contributes 2 columns where the spec computed 4.

**Evidence (`p04` (c), L2).** One pack, `global_profile: probe_var, tensor2d, shape [2,2]`:

| `num_agents` | `env.step()` |
|---|---|
| 1 | OK — obs `(1,112)`, last 4 = `[1.0, 2.0, 3.0, 4.0]` ✔ |
| **2** | **`ValueError: global_active_mask length 4 does not match global_vfs_dim 2.`** |
| 3 | OK — obs `(3,112)` ✔ |
| 4 | OK — obs `(4,112)` ✔ |

Same for `tensorNd [2,2,2,2]`: `global_active_mask length 16 does not match global_vfs_dim 8`.

**Demonstrated on an unmodified shipped pack.** `configs/trial_b_blind_organism` declares a
global `tensorNd shape [3,3,3,3,3]` and its probe runs at `num_agents=1`:

```
trial_b_blind_organism num_agents=1: OK obs=(1, 270) declared_total_dims=270
trial_b_blind_organism num_agents=3: ValueError: global_active_mask length 243 does not
                                     match global_vfs_dim 81.
```

**Product significance.** The pack compiles, the artifact is valid, and whether it runs depends
on a training hyperparameter the author may change for unrelated reasons. This is the
worst-shaped failure available: silent at authoring time, non-deterministic across
configurations. It is **not hypothetical** — a shipped trial pack fails today at an agent count
one edit away, and the pack's own evidence was gathered at the single agent count that avoids
it. Any global tensor whose leading dimension is a small integer (3, 4, 8 — the shapes authors
actually write) sits one hyperparameter change from this.

---

### G-4 — `vec2i` / `vec3i` / `vecNi` / `vecNf` are accepted by the profile DTOs and rejected by the compiler *(BLOCKED)*

The DTO `Literal` and the compiler's `_RUNTIME_VFS_TYPES` disagree by four members. The DTO
validator even enforces `dims` for `vecNi`/`vecNf` — a validation rule for a type that can
never compile. Verbatim in §3.2. `configs/trial_b_blind_organism/vfs_profiles.yaml` carries an
in-tree comment recording this same collision, so it is known; it is listed here as an
independent re-observation with the verbatim message.

---

### G-5 — `initial_value_mode` is a DTO-legal declaration that crashes the compiler with an internal parser error *(BLOCKED)*

**Surface.** `vfs_profiles.yaml` global/agent profile, any of the five modes.

**Mechanism.** `GlobalVFSVariableConfig.validate_value_xor_expression` accepts exactly one of
`initial_value` / `initial_value_mode` / `expression`. `VFSProfileCompiler.compile_variable`
(`vfs/profiles.py:234`) then branches only on `if var.initial_value is not None:` and otherwise
falls through to `self.parser.parse(var.expression)` with `expression = None`.

**Evidence (`p07` M1).** All five modes, identical failure:

```
AttributeError: 'NoneType' object has no attribute 'expandtabs'
  File ".../pyparsing/core.py", line 1332, in parse_string
```

The same five modes **work** through `variables_reference.yaml` (`p07` M2, values verified per
mode). So this is not an unbuilt capability; it is a built capability with one broken door.
The error names neither the variable, the file, nor the key.

---

### G-6 — An item variable of a list type crashes at spawn, not at compile *(BLOCKED, latent)*

`ItemVFSVariableConfig` admits `vec2i` / `vec3i`. `VFSObservationSpec` sizes them at 2 / 3
observation dims. `item_vfs` gives every variable exactly **one** f32 column. And
`ItemManager.spawn_item` (`items/manager.py:358`) does `float(compiled_var.initial_value)`:

```
TypeError: float() argument must be a string or a real number, not 'list'
```

Compiles, constructs, survives `reset()`, and dies the first time an item of that type spawns.
Even setting the crash aside, the observation width (2 or 3) and the storage width (1) disagree
permanently: the extra columns can never be anything but zero.

---

### G-7 — An `environment.yaml` variable can never carry state across ticks, and there is no key to change that *(ABSENT surface, real consequence)*

`compilers/observation.py:866` hardcodes `lifetime="tick"` for every `environment.yaml`
variable; `reset_tick_scoped()` runs at the top of every `step()`.

**Evidence (`p05c` L1 vs L2, L2, four consecutive successful interactions each):**

| step | `environment.yaml` var (`lifetime=tick`) | agent-profile var (`lifetime=episode`) |
|---|---|---|
| 0 | 5.0 | 5.0 |
| 1 | 5.0 | 10.0 |
| 2 | 5.0 | 15.0 |
| 3 | 5.0 | 20.0 |

The write *does* land and *is* observed within the same tick (col 102 reads 0.05 for raw 5.0
against range `[0,100]`), so the variable is not useless — but every accumulator, counter,
cooldown, or memory an author writes here silently resets. The names in `configs/simple`'s own
`environment.yaml` — `time_since_last_sleep`, `time_since_last_doctor`,
`time_since_last_cook` — are exactly the shape that cannot work on this surface.

---

### G-8 — `pair` and `affordance` scopes allocate storage that no declarative route can read or write *(INERT)*

Both scopes allocate correctly (`pair` → `[N,N]`, `affordance` → `[affordance_count]`), survive
`reset()`, and are read every phase by `_current_vfs_state()`. But `variables_reference.yaml`
variables are **not in the compiler symbol table** (`symbol_table.vfs_variables` is
`{**self.variables, **self.profile_vfs_variables}` — `environment.yaml` variables plus profile
variables only), so every reference to one is refused at Stage 3:

```
[UAC-RES-VFS] ... Affordance 'SLEEP' interaction uses unknown VFS variable 'pvar'.
[DAC-REF-005] drive_as_code.yaml:extrinsic.variable_bonuses[0] - Extrinsic variable bonus
  references undefined VFS variable: avar
```

And the profile surfaces cannot name these scopes at all. So `pair` and `affordance` variables
are write-only-from-Python state: they exist, they are hashed into `variable_schema_hash`, and
no config can touch them. `configs/L5_multi_agent/variables_reference.yaml` declares exactly
two such variables (`trust` at pair scope, `occupied_by` at affordance scope).

The same symbol-table gap makes **every** `variables_reference.yaml` variable unreferenceable
from effects, affordances, and `drive.yaml`, whatever its scope.

---

### G-9 — A bare `vfs.X` write to an agent-scoped variable writes every agent, once per actor *(WORKS-with-hazard)*

`ExecutionContext.set_path` for `vfs.*` (`effects/context.py:276`) calls
`registry.set(var_name, value, writer="engine")` with the whole tensor, no per-agent indexing.
The affordance engine runs the command list once per interacting agent
(`affordance_engine.py:505`), and the effect manager once per active effect instance.

**Evidence.** `modify: vfs.avar` / `value: vfs.avar + 5.0` on an agent-scoped variable, 2 agents
both interacting: `avar` → `[10.0, 10.0]` (not `[5.0, 5.0]`). Effect route, `+10.0` per tick,
2 effect instances: `[20,20] → [40,40] → [60,60]`. A global write shows the same doubling:
`vfs.gvar + 5.0` → 10.0 with two interacting agents.

The correct per-agent form (`target.vfs.X`) exists in the affordance route and gives
`[5.0, 5.0]`. But nothing warns, and `vfs.X` is the *shorter and more obvious* spelling.

---

### G-10 — `self.` and `target.` mean opposite things in effects and in affordances, and the wrong one fails with a raw `KeyError` *(BLOCKED)*

| context | `self_index` | `target_index` | working per-entity prefix |
|---|---|---|---|
| affordance interaction (`affordance_engine.py:512-513`) | `None` | the interacting agent | `target.` |
| effect lifecycle (`effects/manager.py:225-226`) | the target entity | `None` | `self.` — *for bars and item VFS only* |

Consequences, all L2-verified:

- effect + `target.vfs.X` → compiles clean, `KeyError: 'avar'` at runtime.
- effect + `self.vfs.X` on a non-item variable → **compile error**: the effects schema builder
  (`compilers/effects.py`) emits only `vfs.X` and `target.vfs.X`.
- affordance + `spawn_effect target: "self"` → `ValueError: self_index not set`.

**Net: there is no working route from an effect to a single agent's VFS variable.** The only
route that reaches agent VFS from an effect is the bare `vfs.X` whole-batch write (G-9).

---

### G-11 — `WriteSpec` — 11 composition members, phases, priorities, clamps, conditions, telemetry labels — has no authoring surface at all *(ABSENT)*

`vfs/schema.py:220` defines `WriteSpec` with `composition ∈ {overwrite, additive_delta,
multiplicative_modifier, min, max, clamp, priority_write, last_write_wins, claim_if_free,
capacity_claim, append_event}`, plus `phase`, `priority`, `clamp`, `condition`,
`telemetry_label`, all validated. `ActionConfig.writes: list[WriteSpec]` exists at
`environment/action_config.py:84`. `vectorized_env.py:513` reads `action.writes`.

But `actions.yaml`'s `CustomActionConfig` (`config/actions_config.py:38`) has exactly three
fields — `name`, `description`, `enabled_by_default` — and forbids extras; and
`compilers/actions.py:205` emits `writes=()` and `reads=()` unconditionally. Measured on the
compiled artifact: `set(tuple(a.writes) for a in u.runtime_action_space.actions) == {()}`, same
for `reads`. **Zero of the eleven composition members is reachable from any config file.** The
occupancy members (`claim_if_free`, `capacity_claim`) are the declarative surface the
`affordance` scope would need, which is why G-8 and G-11 are the same hole seen from two sides.

---

### G-12 — Access control is genuinely enforced, and that makes any non-default `readable_by`/`writable_by` a runtime crash *(BLOCKED)*

`registry.get` / `set` / `set_engine_value` all check the role lists, verified L1:

```
PermissionError: 'engine' is not allowed to write variable 'wvar'. Writable by: ['actions']
  (both registry.set(writer="engine") and registry.set_engine_value — the "bypass" path
   checks too)
PermissionError: 'social_model' is not allowed to read variable 'wvar'.
  Readable by: ['agent', 'engine']
```

But `_current_vfs_state()` (`vectorized_env.py:1210`) reads **every** variable with
`reader="engine"` on every VTC phase of every step, and the writeback path writes with
`"engine"`. So, L2:

```
# variables_reference.yaml, readable_by: [agent]  — first env.step()
PermissionError: 'engine' is not allowed to read variable 'rvar'. Readable by: ['agent']

# variables_reference.yaml, writable_by: [actions] — first env.step()
PermissionError: 'engine' is not allowed to write variable 'wvar'. Writable by: ['actions']
```

The role vocabulary the docstrings advertise (`actions`, `vtc`, `social_model`, `acs`) is
honoured by nothing: the runtime passes `"engine"` at all 12 writer sites and all 6 non-docstring
reader sites. `readable_by` / `writable_by` are therefore two-valued in practice — "contains
`engine`" (works) or "does not" (crashes on step 1) — and the mechanism is real enough that the
crash is loud rather than silent.

---

### G-13 — `observable: true` does not make a variable observable *(INERT / misnamed)*

On `variables_reference.yaml`, `observable: true` emits **no observation field** for any scope
(verified for `global`, `agent`, `agent_private`, `pair`, `affordance` — `'probe_var' in
observation field names == False` in every case, `total_dims` unchanged at 108). Its only
effect is to enter `vfs_observation_marks`, which is consumed as the mark-and-sweep evaluation
set for the **global profile** — a different file's variables.

The two roles are not merely different, they collide. A mark that names no global-profile
variable is a hard runtime failure:

```
# variables_reference.yaml declares `other` observable: true; the global profile has `gvar`
KeyError: "VFS mark(s) not found in profile: ['other']"
  File ".../townlet/vfs/evaluator.py", line 134, in evaluate_global_profile
```

So on a pack with a global profile, `observable: true` on any variable that is not also a
global-profile variable name **crashes the environment on step 1**. `extract_observation_marks`
(`compilers/vfs.py:139-143`) silently drops marks for `pair`/`group`/`affordance`/`zone`/
`message` scopes, so only `global` and `agent`/`agent_private` marks can reach the evaluator —
and only `global` ones are ever read.

---

### G-14 — `exposed_to: []` is silently rewritten to `["agent"]` *(hidden default)*

`GlobalVFSProfileConfig.default_metadata` / `AgentVFSProfileConfig.default_metadata` /
`ItemVFSProfileConfig.default_metadata` all do `if not var.exposed_to: var.exposed_to =
["agent"]`. Measured: `exposed_to: []` → observation field present, `global_vfs_dim=1`,
`total_dims=109` — identical to `exposed_to: ["agent"]`. An author cannot declare a
profile variable that is state-only. Direct No-Defaults Principle violation on an
observation-affecting key.

---

### G-15 — `curriculum_active` cannot be declared on a VFS variable, and the VFS active masks are structurally all-`True` *(ABSENT)*

`ObservationField.curriculum_active` exists and is hashed into the observation schema
(`schema_hashes.py:155`). `VFSObservationSpec._from_variable_iterables` reads
`getattr(var, "curriculum_active", True)` per variable — but `CompiledVariable`
(`vfs/profiles.py:30`) has no such field (`hasattr(...) == False`, measured), and the profile
DTOs reject the key (`extra_forbidden`). `item_active_mask` is built as
`tuple(True for _ in range(item_dim))` with no per-variable input at all. So the VFS-side
activity mask is a mechanism with no author input and one reachable value.

---

### G-16 — Only 2 of the 9 normalization kinds are reachable for a VFS variable *(ABSENT)*

`NormalizationSpec.kind` has nine members and `apply_normalization` implements all nine.
`environment.yaml`'s `NormalizationConfig.method` is `Literal["normalize", "standardize"]`.
Measured: `normalize` and `standardize` both work with negative controls (§3.6);
`log_scaled`, `binary`, `cyclical_sin_cos` are rejected as
`environment.variables.0.normalization.method`. The full nine-member vocabulary is reachable
only for **meters**, via `range_type`. `vfs_profiles.yaml` has no `normalization` key at all;
`variables_reference.yaml` accepts one and it reaches nothing (G-13).

---

### G-17 — The compile-writes-no-artifact defect fires for `agent_profile` packs *(observed, secondary)*

Captured verbatim while probing (a pack with only an `agent_profile`):

```
Failed to write cache artifact to .../.compiled/universe-L0_simple.msgpack:
  can not serialize 'CompiledGlobalProfile' object
```

Compile still exits 0 and returns a valid in-process `CompiledUniverse`. This is why every
probe here used the in-process object, per the brief.

---

## 5. Coverage statement

**Probed with a verdict:** all 9 scopes × (compile, construct, storage, read, write, step,
reset); all 17 `VariableDef` types via `variables_reference.yaml`; all 13/15/9 profile-DTO type
vocabularies; all 5 `initial_value_mode` members × 3 surfaces; `initial_value` / `default` /
`expression` × 4 surfaces; all 3 lifetimes × both reset boundaries; `readable_by` /
`writable_by` × 3 registry entry points × runtime step; `exposed_to` × 5 value shapes × 2
surfaces; `observable` × 5 scopes; `curriculum_active`; `normalization` × 6 method values;
10 of the 12 enumerated write routes; 8 of the 8 enumerated read routes; observation offsets and
values with negative controls for global / agent / agent_private / vector / tensor / item.

**NOT PROBED, and why:**

1. **Item `on_pickup` and `on_drop` command stages.** `on_use` is now **WORKS** with a full
   negative control (§3.4 route 7) — my first reading of "GET does not pick up" was a probe
   artifact (a tensor position passed to `spawn_item`, see the note in §3.4), corrected before
   filing. `on_pickup` and `on_drop` were not separately exercised. Note that
   `hamlet-628e202bf7` files *"Item `on_drop` is INERT: parsed, compiled and dispatchable, but
   no call site ever invokes it"*; my `on_use` result does not bear on that either way, and I
   have no independent evidence for or against it.
2. **`spawn_item(initial_state=...)` (route 8).** `ItemManager.spawn_item` implements it, but I
   found no `items.yaml` / effects key that supplies it; classifying it needs a source trace I
   did not complete.
3. **The 11 `WriteSpec` composition members individually.** With no authoring surface (G-11)
   there is no L2 cell to probe. Their runtime behaviour under `compile_vtc_action_writes` was
   not exercised.
4. **VTC threshold cascades, passive depletion, terminal conditions, social residue, and
   interaction progress as VFS write routes.** These run every step and commit through
   `set_engine_value`, but their authoring surfaces are `bars.yaml` / `drive.yaml` / affordance
   configs rather than VFS declarations; they are out of the commissioned scope.
5. **`message_token` as a consumed type.** It allocates correctly at agent scope
   (`(3,4)` f32), but `MESSAGE`-scope storage is unreachable (§3.1) and `vfs/communication.py`
   is 27 lines. Whether anything consumes a message token was not traced.
6. **Sparse `pair` storage, `dynamic_variable_mode`, `add_variable`/`remove_variable`,
   `get_pair_edges`/`get_pair_mask`/`materialize_pair_dense`.** No config route reaches the
   constructor parameters that enable them (§2.2), so these are an ABSENT cluster stated from
   source, not probed for behaviour.
7. **`history_spec` / `TemporalHistory` / `vfs.X` history references.** Not reached.
8. **GPU device paths.** Everything ran on `torch.device("cpu")`.
9. **Multi-level packs.** Every probe used a single-level pack; per-level VFS divergence was
   not exercised.

**Where I stopped:** after the DAC read routes (`p11`) plus three advisor-prompted follow-ups
(`eye` at rank 5 via varref; `trial_b_blind_organism` at `num_agents=3`; the item `on_use`
lifecycle). The type × scope cross-product is complete for every surface that can name a scope;
the write/read-route axes are complete except for the two item command stages (1) and the
unreachable `WriteSpec` family (3).

**One correction I made to my own work, recorded because the correction is the evidence.**
I initially read the item write route as un-exercisable because `GET` left the inventory empty.
That was my probe's fault, not the framework's: I passed a `torch.Tensor` position to
`spawn_item`, whose contract is a tuple, and `handle_get_action` compares against a tuple. On
the advisor's prompting I split the route with a direct handler call, found the cause, and the
cell resolved to **WORKS** with a clean negative control. Any verdict in this document that
rests on "the thing did not happen" was checked the same way — with an in-list positive control
proving the surrounding machinery ran.

---

## 6. Cross-check against filed gaps

Cross-check performed **after** §§1–5 were written to disk, against
`filigree list --label prd-0001-trial` (32 issues), per the commissioned method. The trial
records in `docs/product/trials/` were not read at any point.

| # | finding | status | issue | note |
|---|---|---|---|---|
| G-1 | `agent_private` is INERT as privacy | **NEW** | — | No filed issue names `agent_private`, the privacy semantics, or `get_agent()`'s missing access control. The nearest neighbours (`hamlet-9e1ae3b7a2`, `hamlet-02bd5a3eaa`) cover the scopes that *crash*; this is the scope that *silently succeeds at the wrong thing*. |
| G-2(a) | global-profile expressions never evaluate under `mark_and_sweep` | **NEW** | — | `hamlet-c6c6c241c5` is a different mechanism (an expression *referencing* VFS state is refused at Stage 6). Mine is orthogonal and downstream: even a Stage-6-clean expression is never evaluated, because `marks` is empty whenever the pack has no `variables_reference.yaml`. Fixing `c6c6c241c5` would not make a single shipped pack's expression run. |
| G-2(b) | agent-profile expressions never evaluate in any mode | **NEW** | — | `evaluate_global_profile` is called at exactly one site and only for `global_profile`. |
| G-2(c) | item-profile expressions never evaluate; item schema uses the bare bar namespace | **NEW** | — | Adjacent to `hamlet-f2a37a8c8a` (item accessor gap) but a distinct mechanism. |
| G-3 | global multi-rank tensor crashes at step 1 iff `shape[0] == num_agents` | **NEW — and live on a shipped pack** | — | Distinct from `hamlet-57a5126baa`, which is a *write*-path bypass on `target.vfs.<global tensor>`. Mine is the *observation* path: `_flatten_to_batch`'s batch-detection heuristic. Demonstrated directly on the unmodified in-tree pack (§4 G-3). |
| G-4 | `vec2i/vec3i/vecNi/vecNf` accepted by profile DTOs, rejected by the compiler | **CONFIRMS (untracked)** | — | Recorded in-tree as a comment in `configs/trial_b_blind_organism/vfs_profiles.yaml` ("gap G-5") but I find **no filigree issue** for it. Independently re-measured here with the verbatim refusal for both profiles and all four types. Recommend filing. |
| G-5 | `initial_value_mode` (all five) crashes the profile compiler | **CONTRADICTS** | `hamlet-8c354c90bb` | That issue says: *"registry.py:653-654 INTENDS to raise 'initial_value_mode eye requires square 2D shape' … The compiler's error formatter fails on the raised error before the real message reaches the author. The refusal is right; the diagnostic is unusable"* — a **failure-loudness** defect specific to `eye` at rank 5. **Three measurements contradict that root cause.** (i) All five modes fail identically on a *valid square `[2,2]`* shape in both profiles — shape and mode are irrelevant. (ii) The crash is `VFSProfileCompiler.compile_variable` (`vfs/profiles.py:234`) branching only on `initial_value is not None` and reaching `parser.parse(None)`; `registry.py:653` is never reached, so nothing is being mangled *after* a refusal. (iii) **Decisive:** the exact filed shape — `initial_value_mode: eye`, `shape: [3,3,3,3,3]` — declared through `variables_reference.yaml` produces the intended message, in full and legible: `ValueError: initial_value_mode 'eye' requires square 2D shape; got [3, 3, 3, 3, 3]` (and `[2,3]` gives the same message, `[3,3]` succeeds). The formatter is fine; the intended refusal is fine. What is broken is that `vfs_profiles.yaml` never reaches either. Reclassify: not a P2 diagnostics defect but a **BLOCKED capability on one surface** — five working init modes with no door from the profile files. |
| G-6 | item list-typed `initial_value` crashes at `spawn_item` | **NEW** | — | Adjacent to `hamlet-bf42ac60b5` / `hamlet-17a7f03bc9` (item-slot observation semantics) but a different defect: `float(list)` at `items/manager.py:358`, plus the permanent storage/observation width disagreement (1 column vs 2–3 dims). |
| G-7 | `environment.yaml` variables are hardcoded `lifetime: tick` and cannot accumulate | **NEW** | — | Same family as `hamlet-0268336cd1` but the opposite end. |
| — | *"env.reset() does not restore a global VFS variable's initial_value, and there is no declarative way to say 'episode-scoped global'"* | **CONFIRMS, with a mechanism correction** | `hamlet-0268336cd1` | Both halves confirmed for the case filed. **First half:** a `vfs_profiles.yaml` global survives `reset()` — reproduced (§3.7; `lifetime` is hardcoded `"persistent"` at `compilers/vfs.py:90`). **Second half — the correction, which does *not* weaken the issue:** the *lifetime-reset mechanism* is not unbuilt. `variables_reference.yaml` with `scope: global, lifetime: episode` resets correctly on `env.reset()` (set 0.75 → 0.25, against a `persistent` control that stays 0.75). But moving the variable there is **not** a workaround for the filed case: G-8 and G-13 show a varref variable gets **no observation field** under any `observable`/`exposed_to` value and is **refused at Stage 3** from effects, affordances, and `drive.yaml`. Trial B's container must be observed and config-written, so it cannot live on the only surface where `lifetime` is declarable. **Net: the issue's headline stands.** The defect is precisely located at `compilers/vfs.py:90` hardcoding `lifetime`, and the remedy is *make `lifetime` declarable on `vfs_profiles.yaml`* — not "reclassify" and not "use varref". |
| G-8 | `pair`/`affordance` allocate but no declarative route reads or writes them; all `variables_reference.yaml` variables are absent from the compiler symbol table | **NEW** | — | `hamlet-02bd5a3eaa` covers `zone` as dead vocabulary. `pair` and `affordance` are a *different* class: they allocate successfully and are read every step by `_current_vfs_state()`, yet every config reference to them is refused at Stage 3 (`[UAC-RES-VFS]`, `[DAC-REF-005]`). `configs/L5_multi_agent/variables_reference.yaml` ships exactly these two. |
| G-9 | bare `vfs.X` writes the whole agent batch, once per actor | **NEW** | — | The counterpart to `hamlet-57a5126baa`: that issue covers the *indexed* `target.` route's bypass; this covers the *unindexed* `vfs.` route's fan-out. Together they are the whole write-addressing question. `[dep: cf16cdb6c4]` |
| G-10 | `self.`/`target.` invert between effects and affordances; no working effect→per-agent-VFS route | **NEW** | — | Same family as `hamlet-a737e444c0` ("effects cannot read position or time — the effects expression context threads neither"): the same context-threading root, one axis over. Candidate to triage as one unit. |
| G-11 | `WriteSpec` has no authoring surface (11 composition members unreachable) | **CONFIRMS** | `hamlet-3381043d2e` | Fully corroborated: `compilers/actions.py:205` hardcodes `writes=()`; measured `set(tuple(a.writes) for a in u.runtime_action_space.actions) == {()}`. **Adds the missing half of that issue's self-correction:** it notes there is no `CustomActionConfig` in `environment/action_config.py` (true) — but there *is* one in `config/actions_config.py:38`, and it *does* refuse a `writes` key under `extra="forbid"`. Verbatim in §3.4. So the blind record's original attribution was right about a different module. Also related to `hamlet-f1dec55b9d` (custom actions are structural no-ops). |
| G-12 | any non-`engine` `readable_by`/`writable_by` crashes on step 1; the advertised role vocabulary is honoured by nothing | **NEW** | — | No filed issue covers access-control roles. |
| G-13 | `observable: true` emits no observation field; it is a mark-and-sweep selector, and a mark that names no global-profile variable crashes at step 1 | **NEW** | — | |
| G-14 | `exposed_to: []` is silently rewritten to `["agent"]` | **NEW** | — | No-Defaults Principle violation on an observation-affecting key. |
| G-15 | `curriculum_active` is unreachable for VFS variables; VFS active masks are structurally all-`True` | **NEW** | — | |
| G-16 | only 2 of 9 normalization kinds reachable for a VFS variable | **NEW** | — | The other seven are meter-only, via `range_type`. |
| G-17 | compile exits 0 while writing no artifact, for `agent_profile` packs | **CONFIRMS** | `hamlet-a141ab5db3` | Same verbatim warning (`can not serialize 'CompiledGlobalProfile' object`), independently reproduced on a scratch pack with an `agent_profile` and no `global_profile` — so the failure is not specific to `trial_o_bidding_blind`. Issue is already `fixing`. |
| — | `group` / `zone` / `message` crash at env construction | **CONFIRMS** | `hamlet-9e1ae3b7a2` | Independently reproduced with identical verbatim messages and the same root cause (`vectorized_env.py:621` passes none of the three extents). Also confirms `hamlet-02bd5a3eaa` for `zone`. |

**Tally:** 15 NEW · 5 CONFIRMS (one of them untracked and worth filing; one with a mechanism
correction that *strengthens* the issue) · 1 CONTRADICTS.

One filed issue should be **re-read against this evidence before it is worked**:
`hamlet-8c354c90bb`. Its root cause (an error formatter mangling a correct refusal in
`registry.py`) is wrong, and its severity class (P2 failure-loudness) understates it — the
intended refusal is legible on the surface that reaches it, and what is actually broken is
five unreachable init modes. Working it as filed would produce a fix to the wrong module.

`hamlet-0268336cd1` should be worked **as filed**, with the fix located at
`compilers/vfs.py:90` rather than in the reset machinery — the reset machinery is correct and
demonstrably so.

