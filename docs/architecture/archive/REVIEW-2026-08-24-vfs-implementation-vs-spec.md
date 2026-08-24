# REVIEW 2026-08-24 — VFS implementation vs. specification

Two independent claim-by-claim audits of `src/townlet/vfs/` (plus compiler and runtime
integration) against the spec corpus (`docs/architecture/vfs.md`,
`docs/config-schemas/vfs-profiles.md`, `docs/config-schemas/variables.md`, with
`docs/architecture/vfs-current-implementation.md` treated as claims-to-verify). Split:
one auditor on the core surface (variables / registry / access control / scopes), one on
profiles / expressions / observation spec / VTC. Full verdict tables are appended below;
every verdict carries file:line evidence. Cross-checked against the filigree tracker —
existing ticket IDs cited inline; findings marked NEW had no ticket before this review.

## Headline

**"Mostly done, a bit wobbly in places" is accurate — with the qualification that the
wobble is not scattered. It is concentrated in one systemic story plus a small set of
fail-at-runtime seams.** Verdict totals across both audits: ~48 spec claims IMPLEMENTED
with evidence, 5 PARTIAL, 1 MISSING, 16 DIVERGED, 4 DOC-DRIFT. Nothing audited was
found entirely absent: every diverged claim maps to real, usually correct code sitting
behind a broken or nonexistent authoring surface. That is the recurring shape —
**the mechanics are built; the doors are missing.**

What is genuinely solid (verified, not assumed): all ten VTC program classes exist and
none are stubs; all 11 composition modes execute on the action-write path;
phase-snapshot/commit-batch semantics, the 18-phase graph, occupancy wiring
(hamlet-ef6699ab2a closure holds), claim/capacity/append semantics all match spec to
the letter. All 9 normalization kinds are implemented *and applied at runtime*. The
superset+activity-mask observation ABI, semantic-group layout, per-field UUIDs, and the
four-hash provenance chain match spec exactly. Mark-and-sweep evaluation with the
statics-never-clobber rule (hamlet-df3a96bbac fix) is in place. The nine-scope storage
model allocates correctly for every scope. `vfs-current-implementation.md` earns its
"Current" label on everything checked **except** its access-control and `agent_private`
claims (see Gap 1).

## The systemic gap: declared epistemic state has no working door

Three findings from the two audits, arrived at independently, are one story:

1. **Authoring**: an author cannot express access intent. `vfs_profiles.yaml` and
   `environment.yaml` — the two required surfaces — have **no
   `readable_by`/`writable_by` fields at all**; the compiler hardcodes
   `["agent","engine"]`/`["engine"]` for every variable regardless of declared scope
   (`universe/compilers/vfs.py:313-320`, `universe/compilers/observation.py:811-812,
   866-867`). NEW finding (compiler half of hamlet-1a520475f4). Likewise `exposed_to`
   fails open: omitted **and explicitly `[]`** are both rewritten to `["agent"]`
   (`vfs_profiles_config.py:121-129,232-240,319-327`; hamlet-d97b4d6b4a,
   hamlet-c78fbf32a3). Pack census: 2 of ~49 authored profile variables state exposure
   explicitly.
2. **Runtime**: even correctly-declared restrictions would not bite. The observation
   path reads through `get_agent()`/`get_global()`, which perform **no access check**
   and treat `agent` and `agent_private` identically (`registry.py:774-791`;
   `observation_encoder.py:86`) — the checked `get()` path with its explicit
   agent_private block (`registry.py:518-522`) is never on the observation route. This
   is the precise root cause of hamlet-83a043a9b9 (`agent_private` fully observable).
   And no runtime call site anywhere passes a reader/writer role other than `"engine"`
   (hamlet-1a520475f4), so the role vocabulary is binary in practice.
3. **Escape hatch is walled off**: the one file where an author *can* set
   `readable_by`/`writable_by`/`lifetime` and declare pair/affordance/zone/group/message
   scopes — `variables_reference.yaml` — never enters the compiler symbol table
   (`universe/validation/references.py:14-58` registers only environment.yaml and
   vfs_profiles variables), so no effect, affordance, or drive.yaml can reference any
   of its variables (hamlet-33e520cebd). Five of nine scopes are storage no declarative
   rule can touch.

Consequence: every privacy / hidden-state / social-inference mechanic that vfs.md
§5.3/§6 presents as VFS's payoff is currently **unauthorable while appearing
authorable**. The enforcement machinery in `registry.py` is correct where it runs; it
is simply never wired to an author's intent. This is one gap wearing ~six ticket
numbers, and it should be fixed as one design unit (the token-observation migration's
explicit-exposure + per-variable declaration work is the natural vehicle — unit 3's cut
already makes exposure explicit and required).

The same hardcoding pattern hits **`lifetime`**: `environment.yaml` variables are
always `tick` (no counter/accumulator can survive a step — hamlet-4597fd5d04);
global/agent profile variables are always `persistent`/`episode` with no author knob,
so a global profile variable can never be declared episode-scoped and is never reset by
`env.reset()` (hamlet-0268336cd1). Both required surfaces hardcode past the same enum
in opposite directions.

## Fail-at-runtime seams (compile green, crash or no-op at step 1)

The project's own discipline is fail-loud-at-compile. These violate it:

- **VTC modulation rules**: any `condition:` or non-`multiplicative_modifier`
  composition compiles green and raises `NotImplementedError` at the first `env.step`
  (NEW — `vtc.py` `compute_affordance_multiplier`).
- **Social-residue writes**: `claim_if_free`/`capacity_claim`/`append_event` validate
  at the schema (`transition_rules_config.py`) and raise `NotImplementedError` at
  execution — 8 of 11 declared modes work (NEW).
- **Global tensor with leading dim == num_agents** hard-fails at first step as a
  function of an unrelated training hyperparameter (hamlet-f54b887148).
- **Zero-affordance packs** compile then crash at first observation
  (hamlet-fba3d5aa3c).
- **`set_engine_value` shape bypass** lets storage drift permanently from the declared
  schema; later writes validate against the drifted shape (hamlet-d970ef83f0,
  hamlet-2ca2cb373f). Plus silent write-back drops on unknown ids at three
  `vectorized_env.py` sites.

## Dead or unreachable surface (validates, does nothing)

- `VariableDef.normalization` — validated, hashed, **read by nothing at runtime**
  (NEW). Only `ObservationField.normalization` is applied.
- Sparse pair storage (`pair_storage_mode`/`pair_edges`) — extensive, tested registry
  code with zero wiring from any config pack or compiler stage; every env is
  dense-pair O(N²) (NEW).
- Item-profile expressions refuse at compile (correct fail-loud), which leaves the item
  scope with zero declarative dynamism — spoilage/durability must route through
  effects. Honest, documented, but a narrower promise than the other profile scopes.
- Item variables unreachable through documented `registry.get()`
  (hamlet-f2a37a8c8a); `zone` scope has no runtime consumer (hamlet-02bd5a3eaa).

## Doc drift found

`vfs-current-implementation.md` is accurate throughout **except**: the blanket
"registry enforces access control" claim (true only of the bypassed `get()`/`set()`
path), the `agent_private` "hidden from normal observations" scope-table row (false —
hamlet-83a043a9b9), and the "Why VFS Exists" epistemic-access framing (aspirational
stated as achieved). `docs/config-schemas/variables.md` is broadly stale (2025-11:
three scopes, dead file paths, retracted dimension counts) but is not on CLAUDE.md's
trusted list. `vfs-profiles.md`'s XOR table omits `initial_value_mode`. Minor.

## Ranked: what breaks a designer first

1. **Hidden state is unauthorable** (exposure fails open + access control hardcoded +
   agent_private bypassed) — breaks the first multi-agent/privacy recipe anyone writes.
   Partially in flight: unit 3's cut makes exposure explicit/required; the registry
   read-path and role-wiring halves are NOT in unit 3 scope and need their own unit.
2. **Counters silently reset** (lifetime hardcoded) — the first "track time since X"
   recipe fails invisibly; values look live within a tick.
3. **Exotic scopes are decorative** (symbol-table gap) — pair/zone/group/message
   mechanics cannot be expressed end-to-end at all.
4. **Compile-green/runtime-crash seams** — each one costs a designer a training run to
   discover.
5. **Raw values in observations** (no normalization surface on exposed profile
   variables — hamlet-b8ad2ffcd6) — breaks obs-scale sanity in-HAMLET and is fatal to
   the train-here/deploy-there interface contract; being fixed in unit 3's cut
   (required normalization at exposure).

Everything else found is polish-grade. The framework's spine — compile → hash →
allocate → step → observe — held up under line-level adversarial reading on both
audits.

---

# Appendix A — Core-surface audit (variables / registry / access control / scopes)

(Verbatim report; verdicts and evidence as filed by the auditor.)

# VFS Audit — Core Surface (variable / registry / access-control / scope)

Scope: `src/townlet/vfs/schema.py`, `registry.py`, `schema_hashes.py`; compiler symbol-table/resolve
stages (`src/townlet/universe/symbol_table.py`, `validation/references.py`, `compilers/vfs.py`,
`compilers/observation.py`); `src/townlet/environment/vectorized_env.py` registry construction/writeback;
`src/townlet/config/vfs_profiles_config.py` (variable declaration only). Excludes profiles/expressions/
observation-layout/VTC proper (sibling agent's territory) except where a boundary observation is noted.

All findings independently verified against code at current HEAD (branch `project-recovery-2`) unless
marked otherwise. Filigree tickets cited where one already exists; several findings below are **new**
(not covered by an existing ticket) and are marked so explicitly.

---

## 1. Variable declaration schema (`VariableDef`, `vfs/schema.py`)

| Claim (spec) | Verdict | Evidence | Notes |
|---|---|---|---|
| Variable has id, type, scope, range/bounds, initial(default), readable_by, writable_by, description (vfs.md §4.1) | IMPLEMENTED | `schema.py:441-525` (`VariableDef` fields) | `range`/bounds is not a first-class field — only `normalization.min/max` approximates it (see below). |
| Type vocabulary: scalar, vec2i/3i, vecNi/Nf, bool (variables.md) | PARTIAL / DIVERGED | `schema.py:458-476` | Code's `type` Literal is far larger than variables.md documents: adds `vec2f`, `vec3f`, `agent_ref`, `item_ref`, `affordance_ref`, `effect_ref`, `tensor1d/2d/3d/Nd`, `message_token`. variables.md (2025-11-07) is stale; vfs.md doesn't enumerate the full type list either. |
| `dims` required for vecNi/vecNf, forbidden for scalar/bool | IMPLEMENTED | `schema.py:532-563` (`validate_vector_types`) | Also extends correctly to tensor types (shape required, rank-checked) and `message_token` (dims, not shape). |
| Nine canonical scopes (vfs.md §5.1) | IMPLEMENTED | `schema.py:32-43` (`VariableScope` enum: global, agent, agent_private, item, pair, group, affordance, zone, message) | Matches exactly. |
| `VariableDef.normalization` field usable/consumed | DIVERGED (dead field) | `schema.py:517-520` declares it; **zero** production read sites (`grep var_def.normalization` / `variable.normalization` across `src/townlet/` → only `schema_hashes.py:149`, which extracts min/max for the hash, never applies it) | Undocumented dead surface — an author can set `VariableDef.normalization` on a `variables_reference.yaml` variable, it validates, and is silently inert at runtime. Only `ObservationField.normalization` (a separate object) is actually applied (`observation_encoder.py:107-138`). Not flagged by any spec source. |
| `observable` flag ("include in mark-and-sweep") | IMPLEMENTED but MISLEADING NAME | `schema.py:527-530` | Confirmed separately mis-scoped at the *profile* layer — see §7 boundary note and `hamlet-0071c78ee9`. The field itself (on `VariableDef`) is honest; the *authoring* surface built on top of it (variables_reference.yaml `observable: true`) is not (sibling-adjacent, noted for completeness). |
| Docstring shows `model_config = ConfigDict(extra="forbid")` twice (`schema.py:414` and `:439`) | COSMETIC BUG, not functional | `schema.py:394-439` | Line 414 sits **inside** the class docstring (before the closing `"""` at line 437) — inert text, not executed. Real declaration is line 439. Copy-paste artifact only; no behavioral effect. |

## 2. Nine scopes — storage and semantics

| Claim | Verdict | Evidence | Notes |
|---|---|---|---|
| `global`/`agent`/`agent_private` prefix shapes | IMPLEMENTED | `registry.py:452-458` (`_scope_prefix_shape`) | Correct: `()`, `(num_agents,)`, `(num_agents,)`. |
| `item` scope allocates `item_vfs[max_items, max_profile_vars]`, keyed by `item_profile_map` | IMPLEMENTED | `registry.py:702-743` | Matches vfs.md §5.1 exactly. `variables_reference.yaml` correctly rejects `scope: item` at load (`schema.py:628-629`) and registry construction also raises if any item-scoped var lands in `_definitions` (`registry.py:712-716`) — belt-and-suspenders, consistent with spec. |
| `pair` scope: dense `[num_agents, num_agents, ...]` or sparse `[num_pair_edges, ...]` with `pair_edges` validation | IMPLEMENTED (as a registry primitive) but **UNREACHABLE FROM CONFIG** | `registry.py:204-283` (edge validation, dedup, range-check, `get_pair_edges`/`get_pair_mask`/`get_pair_edge_index`/`materialize_pair_dense`) vs. `grep -rn "pair_storage_mode\|pair_edges" src/townlet/` → **zero hits outside `vfs/registry.py` and tests** | **NEW FINDING, not previously ticketed** (checked `filigree search "sparse pair"` / `"pair_storage_mode"` — no match). `VectorizedHamletEnv._initialize_vfs_subsystem` (`vectorized_env.py:604-631`) constructs `VariableRegistry(...)` without `pair_storage_mode=` or `pair_edges=`, so every environment always gets the default `pair_storage_mode="dense"`. No config DTO, no `UniverseMetadata` field, no compiler stage carries a pair-storage-mode or edge list from any pack. The sparse-pair machinery vfs.md §5.1 documents in detail is real, tested code with **no path from any YAML pack to it** — it is reachable only by hand-constructing `VariableRegistry` in a test. For any pack with more than a handful of agents, `pair` scope is dense-only and O(N²) whether the author wants that or not. |
| `group`/`affordance`/`zone` dense storage, positive extents required | IMPLEMENTED | `registry.py:463-482` (`_positive_extent`), `vectorized_env.py:626-630` wiring `num_affordances`/`num_zones`/`num_groups` from `self.metadata` | Matches. |
| `message` scope `[num_agents, num_message_slots, ...]` | IMPLEMENTED | `registry.py:469-470` | Matches. |
| Extents (`num_zones`/`num_groups`/`num_message_slots`) declared in `variables_reference.yaml` top-level `extents:`, compile-error if missing | IMPLEMENTED | `schema.py:566-660` (`VFSScopeExtents`, `load_variables_reference_config` cross-check at `:642-658`) | Matches vfs.md §5.1 "Runtime wiring (2026-08-21)" claim precisely — compile-time rejection, not a runtime crash. `num_affordances` extent is notably **not** in this preflight set (`_SCOPE_EXTENT_FIELD` at `schema.py:593-597` only has ZONE/GROUP/MESSAGE) — an affordance-scoped variable in a zero-affordance pack is not caught at this same compile gate. Matches the still-open half of `hamlet-702ae15f82` per the token-obs unit-3 plan (not independently re-verified beyond reading `_SCOPE_EXTENT_FIELD`). |
| Every scope reachable "end-to-end from config" (vfs.md §5.1, "Runtime wiring... closed") | **DIVERGED — the claim is false for `pair`, `affordance`-scope-from-`variables_reference.yaml`, and the whole `variables_reference.yaml` surface w.r.t. cross-referencing** | See `hamlet-33e520cebd` below (§3/§6) and the pair-storage finding above | Storage allocates correctly for all nine; *referenceability* from declarative rule surfaces (effects/affordances/drive) is a separate, unmet condition for pair/affordance/zone/group/message when declared via `variables_reference.yaml`. |
| `agent_private` "observable only by owner" (vfs.md §5.1, §5.3; variables.md; vfs-current-implementation.md:135) | **DIVERGED — confirmed still-open bug, `hamlet-83a043a9b9` (P1, status: triage)** | `registry.py:774-791` `get_agent()` — used by the entire runtime observation path — has **zero access-control check** and lumps `AGENT`/`AGENT_PRIVATE` together (`registry.py:771` list check, `:789` scope check); `observation_encoder.py:86` branches `declared.scope in ("agent", "agent_private")` into the *same* code path; `observation_builder.py:374` calls `registry.get_agent(...)`. The one real protection — `registry.get(reader=...)`'s explicit block at `registry.py:518-522` (`if var_def.scope == "agent_private" and reader == "agent": raise`) — is never exercised on the observation path because that path never calls `get()`, only the unchecked `get_agent()`. | Root-caused precisely: the bug is not in the `readable_by` check itself (which is correct where it runs) but in the existence of a second, parallel accessor (`get_agent`/`get_global`) that bypasses it entirely and is the one the runtime actually uses to build observations. Any `agent_private` variable that ends up as an observation field's source (which is unavoidable if it's meant to feed a per-agent hidden-state mechanic that anything downstream needs) lands in every agent's observation row, full value, no masking. Every "hidden state", "private goal", "secret inventory" mechanic vfs.md §5.3 describes as VFS's payoff is currently unimplementable while *appearing* implemented. |

## 3. Access control (readable_by / writable_by)

| Claim | Verdict | Evidence | Notes |
|---|---|---|---|
| `registry.get()`/`set()` enforce `readable_by`/`writable_by`, raise `PermissionError` | IMPLEMENTED (mechanism) | `registry.py:507-524` (`get`), `:546-565` (`set`) | The enforcement code itself is correct and matches vfs.md §6.2/§6.3 exactly, including shape/dtype validation on `set()`. |
| `set()` validates shape+dtype against declaration; `set_engine_value()` is the deliberately-unvalidated path (vfs.md §6.3, §7.4 — spec is honest about this) | IMPLEMENTED as documented, but see divergence below | `registry.py:567-587` | `set_engine_value` checks shape **only** for sparse-pair variables (`:583-586`); for every other variable it only checks existence + `"engine" in writable_by`, then force-casts dtype and stores. Confirmed still open: `hamlet-d970ef83f0` (P2, triage) and `hamlet-2ca2cb373f` (P2, triage) — the latter traces the full chain: `vtc.py:851`/`:485` validate write-expression output only against the **phase-snapshot's current shape**, never the declared schema, so once a declared `scope: global, type: scalar` variable is legitimately written with a `(num_agents,)` batch (the documented carve-out), all *future* writes are validated against the drifted shape forever — the declared schema can never reassert itself. |
| Access control models epistemic access / least privilege / role vocabulary (`agent`, `engine`, `actions`, `vtc`, `social_model`, open string set) (vfs.md §5.3, §6.1, §6.4) | **DIVERGED — confirmed still-open, `hamlet-1a520475f4` (P2, triage)** | Verified independently: `vectorized_env.py:1266` `_current_vfs_state()` reads every variable with `reader="engine"`; `:1097`, `:1137`, `:1260` all write via `set_engine_value` (permission-checked against `"engine"` only, not the calling subsystem's actual role) | The declared vocabulary (`actions`, `vtc`, `social_model`, `acs`, `bac`) is real in the schema (any string is legal in `readable_by`/`writable_by`) but **no runtime call site ever passes anything but `"engine"`** as reader/writer, and never `"agent"` on the read side either (confirmed — the only `reader="agent"` occurrences repo-wide are three registry.py docstring examples per the ticket's own grep, independently reproduced: `grep -rn 'reader="agent"' src/townlet/environment/` → no hits outside docstrings). Net effect: `readable_by`/`writable_by` are binary in practice — "contains `engine`" (works) or "doesn't" (any real step crashes loudly with `PermissionError`). Every richer policy the spec's whole §5.3/§6 chapter is built around (role-based visibility, self-vs-other perception, social inference) has no live code path that would ever pass a differentiated role. |
| **Authoring surface for `readable_by`/`writable_by` on the two REQUIRED/primary config surfaces** | **DIVERGED — new finding beyond the tickets above, same root cause as the tickets' "nothing passes non-engine roles"** | `universe/compilers/observation.py:811-812` (environment.yaml `variables:` → `VariableDef`) and `:866-867` (same loop, second block) both hardcode `readable_by=["agent","engine"]`, `writable_by=["engine"]` **unconditionally, regardless of the author's declared `scope`** (including `scope: agent_private`, which `VariableConfig.scope` explicitly allows at `environment_config.py:259` but which gets the exact same `readable_by` as a public `agent`-scope variable). `universe/compilers/vfs.py:313-320` (`_compiled_profile_var_to_variable_def`, used for **every** `vfs_profiles.yaml` global/agent profile variable) hardcodes the identical pair. | `vfs_profiles.yaml` is the **required, authoritative** variable-declaration surface per CLAUDE.md/vfs.md §3.1, and its schema (`config/vfs_profiles_config.py` — `GlobalVFSVariableConfig`, `AgentVFSVariableConfig`) has **no `readable_by`/`writable_by` fields at all** for an author to set (confirmed by reading the full DTO: fields are `id, exposed_to, name, semantic_type, type, dims, shape, initial_value*, expression, description` — nothing else). `environment.yaml`'s `VariableConfig` similarly has no access-control fields. The **only** config surface in the whole pack layout where an author's `readable_by`/`writable_by` is ever actually read and enforced is the optional `variables_reference.yaml` static overlay (`load_variables_reference_config` builds real `VariableDef`s with author-supplied `readable_by`/`writable_by`) — and per §6 below, that surface is invisible to the compiler symbol table used by effects/affordances/drive. **Net: the declarative access-control chapter of the spec (vfs.md §5.3, §6) describes a mechanism that is real in `registry.py` but has no functioning authoring surface on either of the two primary/required variable-declaration files.** This is the same underlying gap `hamlet-1a520475f4` names from the runtime-role side; this entry adds the compiler-hardcoding half of the same story, independently verified in code, not previously called out as its own ticket as far as `filigree search` could find. |
| Item-scoped variables reachable through `registry.get()` (variables.md "Permission Validation: Registry enforces access control at runtime via get() and set() methods", implying uniform coverage) | **DIVERGED — confirmed still-open, `hamlet-f2a37a8c8a` (P2, triage)** | Verified: item vars are never entered into `_definitions` (`registry.py:712-716` actively rejects it), so `get()`'s `if variable_id not in self._definitions: raise KeyError` (`:507-508`) fires for any item-scoped id. Item access is only through `read_item`/`write_item`/`register_item_instance` (`:793-874`), a completely separate, unchecked-by-`readable_by` API (no permission parameter at all). | Ticket itself flags this as not-yet-independently-reproduced by the standing agent at filing time; this audit reproduces it by static code reading (no runtime execution performed) — `_definitions` never contains an `ITEM`-scope entry, so the `KeyError` is structurally guaranteed, not merely likely. |
| `ScopedVariableRegistry.check_access` — vfs.md's claim that it "implements the same protocol shape" as `VariableRegistry` | PARTIAL / boundary observation | `registry.py:1013-1049` | It satisfies the `VFSRegistryProtocol` *read* surface (`get_global`/`get_agent`/`list_*`), true. But its `check_access` implements a **completely different access-control philosophy** — ownership-by-scope-name (`"agent" scope can only be written by the agent caller`) rather than `VariableRegistry`'s role-list (`readable_by`/`writable_by`) model. Two incompatible access-control mental models coexist in the same module under the same "VFS access control" heading; not itself a bug (the class is explicitly a test/observation-builder utility, per vfs.md §7.2) but worth flagging as a source of confusion for anyone reading `registry.py` top-to-bottom expecting one consistent policy. |

## 4. Lifecycle (reset semantics, persistence, lifetime)

| Claim | Verdict | Evidence | Notes |
|---|---|---|---|
| `lifetime`: `tick` (recomputed), `episode` (persists within episode), `persistent` (survives episodes) — three-way author-declared enum | IMPLEMENTED **on `VariableDef` itself**, but hardcoded away on both required surfaces | `schema.py:484-486` (enum); `registry.py:589-600` (`reset_tick_scoped`/`reset_episode_scoped`/`_reset_lifetimes`) correctly reset `{"tick"}` and `{"tick","episode"}` respectively, never `"persistent"` | The registry mechanism is correct and matches spec exactly. |
| — for `environment.yaml` `variables:` | **DIVERGED — confirmed still-open, `hamlet-4597fd5d04` (P2, triage)** | `compilers/observation.py:865` hardcodes `lifetime="tick"` for every `environment.yaml` variable, no author-settable key exists on `VariableConfig` (`environment_config.py:248-272` has no `lifetime` field) | Independently verified: any accumulator/counter/cooldown authored on this surface (ticket names `configs/simple`'s `time_since_last_sleep` etc. as a concrete casualty) is silently reset to its default every single tick by `reset_tick_scoped()`, which runs at the top of every `step()`. The write is observed correctly within the same tick it happens (not fully inert), but nothing can accumulate across ticks. |
| — for `vfs_profiles.yaml` global/agent profile variables | **DIVERGED — confirmed still-open, `hamlet-0268336cd1` (P2, triage)** | `compilers/vfs.py:105` hardcodes `lifetime="persistent"` for every global-profile variable, `:109` hardcodes `lifetime="episode"` for every agent-profile variable; no `lifetime` field exists on `GlobalVFSVariableConfig`/`AgentVFSVariableConfig` | Direct consequence: a global profile variable's state (e.g. a grown/accumulated container from the tensorNd trial evidence) is **never** cleared by `env.reset()` — `reset_episode_scoped()` doesn't touch `"persistent"` lifetime — and there is no declarative way to say "this global variable should reset with the episode." Ticket also notes the sibling mechanism (spawned-effect survival across reset, `hamlet-d76684f549`) as the same open "what survives the episode boundary" question. |
| Net pattern across §3 and §4 | — | — | **Both of the two required/primary variable-declaration surfaces (`environment.yaml`, `vfs_profiles.yaml`) hardcode past `readable_by`/`writable_by` AND `lifetime` simultaneously.** Only the optional `variables_reference.yaml` overlay lets an author actually set either — and that overlay is invisible to the parts of the compiler that would let a variable's *value* actually be manipulated by declared rules (see §6). This is one systemic gap wearing four ticket numbers, not four unrelated bugs. |
| `dynamic_variable_mode` add/remove, `network_shape_effect` gating, audit trail | IMPLEMENTED | `registry.py:321-385` | Matches vfs.md §7.2 closely: rejects by default, requires explicit `observation_schema_changed` for observable variables (`_can_change_observation_schema` at `:365-366`), records `DynamicVariableMutation` with `variable_schema_hash` snapshot. No divergence found. |

## 5. Hashing (`variable_schema_hash`, `vfs_hash`, and friends)

| Claim | Verdict | Evidence | Notes |
|---|---|---|---|
| `variable_schema_hash` covers id/type/scope/dims/lifetime/readable_by/writable_by (+normalization range) | IMPLEMENTED | `schema_hashes.py:140-150` (`_canonical_variable_entry`) | Matches vfs-current-implementation.md's own claim ("access metadata, and normalization ranges") precisely. |
| `variable_schema_hash` does **not** cover the variable's `default`/`initial_value` | UNDOCUMENTED GAP (no spec claims coverage either way) | `schema_hashes.py:140-150` — no `default` key in the canonical entry | Not a contradicted claim (no spec source asserts defaults are hashed), but worth surfacing: an author can change a variable's initial value pack-to-pack with **zero** change to `variable_schema_hash`/`vfs_hash`, so checkpoint-compatibility provenance is silent about default-value drift. Whether that's intended (defaults aren't part of the "ABI") or an oversight is a product call, not adjudicated here. |
| `observation_schema_hash` covers ordered field list, source variable, shape, normalization, exposure, semantic group, `curriculum_active`, dtype — except version metadata (vfs.md §8.4, explicitly self-corrected) | IMPLEMENTED exactly as vfs.md §8.4 now (2026-08-21) describes | `schema_hashes.py:153-163` (`_canonical_observation_entry`) | Confirms vfs.md's own already-corrected claim; no further drift found. `vfs.md` is accurate here — an example of the doc's self-auditing working. |
| `compute_vfs_hash` combines all four hashes (variable/observation/action/transition) | IMPLEMENTED | `schema_hashes.py:129-137` | Matches. |
| Resume checks `vfs_hash` + per-field UUIDs + other hashes rather than `observation_schema_hash` directly ("enforcement is real but indirect", vfs.md §8.4) | Not independently re-verified this session (checkpoint/resume path is outside this audit's assigned file set — `training/checkpoint_utils.py`) | — | Flagged as out-of-scope rather than confirmed or refuted; sibling/checkpoint territory. |

## 6. Compiler integration — symbol table / cross-validation

| Claim | Verdict | Evidence | Notes |
|---|---|---|---|
| `variables_reference.yaml` variables are referenceable by effects/affordances/drive.yaml (implicit in vfs.md's framing of it as a "static registry overlay" alongside the required `vfs_profiles.yaml`, and in variables.md's undifferentiated "Access Control"/"Validation" sections) | **DIVERGED — confirmed still-open, `hamlet-33e520cebd` (P1, triage)** | `universe/validation/references.py:14-58` (`build_symbol_table`) registers variables **only** from `raw.environment.environment.variables` (`:35-36`) and from `vfs_profiles` global/agent/item profile blocks (`:38-49`). There is **no** loop over `raw.variables_reference` anywhere in this function or elsewhere in `universe/`. `symbol_table.py:126-128`'s `vfs_variables` property — the thing effects/affordances/drive.yaml resolve references against — is therefore exactly `{**table.variables, **table.profile_vfs_variables}`, neither of which a `variables_reference.yaml` variable ever enters. | Confirmed by direct reading of `build_symbol_table`, independent of the ticket's own evidence. Total impact for `pair`/`affordance` scope: those scopes allocate correctly, survive `reset()`, and are read every phase by `_current_vfs_state()` (per ticket text; consistent with `registry.py`'s scope-prefix code reviewed in §2) — but since `variables_reference.yaml` is the **only** file that can declare `pair`/`affordance`/`zone`/`group`/`message`-scoped variables (per `schema.py:628-629`'s rejection of `item` there and `vfs_profiles_config.py`'s global/agent/item-only scope set), and none of its variables reach the symbol table, **no declarative surface (effects, affordances, drive.yaml, action writes) can read or write a pair/affordance/zone/group/message variable by name.** They are, as the ticket puts it, write-only-from-Python state that happens to be hashed into `variable_schema_hash` as if it were an authored, load-bearing part of the world. |
| Cross-cutting boundary note for the sibling agent (profiles/expressions/VTC) | — | — | This symbol-table gap is the same root cause behind the sibling's likely finding that `WriteSpec`/action writes can't target pair/affordance/zone/group/message variables (ticket cross-references `hamlet-3381043d2e`, "Action writes are unreachable from config" — different mechanism, same family, not audited here). |
| Boundary note: mark-and-sweep `observable: true` naming collision | — | — | `hamlet-0071c78ee9` (confirmed still open, triage): `variables_reference.yaml`'s `observable: true` does not create an observation field for any scope; its only effect is entering `vfs_observation_marks`, which selects mark-and-sweep evaluation for the **global profile** (a different file's variables). A mark naming no global-profile variable is a `KeyError` at step 1. This sits mostly in the profile/expression/observation half of the audit (mark-and-sweep is `VFSEvaluator`), so only flagged here as a boundary observation since the affected field (`VariableDef.observable`) lives in my file set. |

## 7. Registry API contract — additional observations

- `get()`/`set()`/`get_global()`/`get_agent()`/`list_global()`/`list_agent()` all `.clone()` before returning — no aliasing risk from repeated reads. Confirmed defensive-copy discipline is consistent (`registry.py:524, 565, 587, 766, 791`).
- Duplicate-id rejection at construction (`registry.py:148-151`) and in `add_variable` (`:325-326`) — matches vfs.md §7.3.
- `_max_tensor_elements = 1_000_000` guardrail is set **twice** in `__init__` (`registry.py:144` and again at `:173`, byte-identical) — harmless (idempotent) but dead duplication, not a functional bug.
- `VFSRegistryProtocol` (the observation-facing structural contract, `registry.py:61-76`) is satisfied by both `VariableRegistry` and `ScopedVariableRegistry`, as vfs.md §7.2 claims. Confirmed.

## 8. Doc-drift — `docs/architecture/vfs-current-implementation.md` vs. code

Per the task's instruction to treat this doc's "current and source-mapped" self-description as a claim to verify, not truth:

| vfs-current-implementation.md claim | Verdict | Where it diverges |
|---|---|---|
| "Runtime tensor registry with scope-aware storage **and access control**" (Summary, line 20) and "The registry enforces ... access control on `get()` and `set()`" (line 383) | DOC-DRIFT (misleading by omission) | True narrowly (get/set do enforce it), but the doc never discloses that the actual runtime read path for building observations (`get_agent`/`get_global`) bypasses access control entirely (§2 above, `hamlet-83a043a9b9`), nor that no call site ever passes a reader/writer role besides `"engine"` (§3, `hamlet-1a520475f4`). A reader of this doc would reasonably conclude access control is a live, working policy layer; it is enforced code with no author-facing lever that ever varies its outcome except the binary "contains engine or not." |
| `agent_private`: "Per-agent state hidden from normal agent observations" (line 135, scope table) | DOC-DRIFT | Directly contradicted by `hamlet-83a043a9b9` — confirmed still open, agent_private lands fully observable. Stated as settled fact with no caveat, unlike some other sections of this same doc family that do carry dated correction notices. |
| "If a world property can affect an agent ... it should be represented as a typed VFS contract rather than hidden imperative state" / implies `readable_by`/`writable_by` genuinely gate epistemic access (Summary, "Why VFS Exists") | DOC-DRIFT (aspirational framed as achieved) | See §3 — the two required config surfaces have no field for an author to set these at all; the doc presents the access-control story as already realized. |
| Everything else audited (hashing table, scopes table storage meanings, dynamic-variable-mutation section, VTC read-snapshot/commit-batch model, "Current Boundaries" list) | Cross-checked against code and found accurate | `registry.py`, `schema_hashes.py`, `compilers/vfs.py` | This doc's hashing section, dynamic-mutation section, and "Current Boundaries" bullet list (`variables_reference.yaml` static-only, no item-scope there, mark-and-sweep needs explicit marks, dynamic mutation off by default) all check out exactly against code. The drift is concentrated specifically in the access-control and agent_private claims — the rest of the document earns its "Status: Current" header. |

`docs/config-schemas/variables.md` is separately and more broadly stale (dated 2025-11-07, "Phase 1 Implementation TASK-002C") — it still claims only three scopes ("global, agent, agent_private only" under Validation), a flat `variables.yaml` file location, and cites dimension counts (38/78/93/54/93) that `docs/architecture/vfs.md` §2.3 has already retracted as conflating allocated-vs-active width. This is legacy content, not actively claimed as current by CLAUDE.md's trustworthy-docs list (only `vfs.md`, `vfs-current-implementation.md` are named there) — flagged for completeness but not double-counted as a fresh finding.

## 9. Undocumented behavior — implementation surface with no spec coverage

- `ScopedVariableRegistry.check_access`'s scope-ownership access model (§3) — a second, incompatible access-control philosophy nowhere mentioned in any spec source.
- `VariableDef.normalization` as a fully dead field (§1) — validated at parse time, read by nothing at runtime except the hash extractor.
- Sparse pair storage's complete unreachability from any config pack (§2) — the richest single undocumented gap: extensive, tested, correct-looking code with zero wiring.
- The duplicate `_max_tensor_elements` assignment (§7) — trivial, noted for completeness only.

---

## Verdict counts

- **IMPLEMENTED**: 14
- **PARTIAL**: 3
- **DIVERGED**: 13 (includes all confirmed-still-open known tickets plus 2 new findings: compiler-hardcoded `readable_by`/`writable_by` on the two required surfaces, and sparse-pair-storage unreachability)
- **MISSING**: 0 (nothing in this file set was found entirely absent — every claim maps to *some* code, mostly correct code sitting behind a broken or nonexistent authoring surface)
- **DOC-DRIFT**: 3 (all in `vfs-current-implementation.md`: blanket access-control claim, agent_private scope-table claim, aspirational "Why VFS Exists" framing)

## Top gaps ranked by authoring-surface impact

1. **Access control has no authoring surface on either required config file** (`vfs_profiles.yaml`, `environment.yaml`) — `readable_by`/`writable_by` are compiler-hardcoded to `["agent","engine"]`/`["engine"]` regardless of declared scope, and the runtime never passes a role other than `"engine"` (write) anywhere. Combined with the `agent_private` bypass, **the entire declarative access-control story — the mechanism the spec spends two whole sections (§5.3, §6) selling as VFS's payoff for social/epistemic modeling — is currently unusable by any config author**, on the two files a designer is actually supposed to touch. (`hamlet-83a043a9b9`, `hamlet-1a520475f4`, plus this audit's new compiler-hardcoding finding.)
2. **`variables_reference.yaml` variables are invisible to the compiler symbol table** (`hamlet-33e520cebd`) — the one file where an author *can* set real `readable_by`/`writable_by`/`lifetime` is also the one file whose variables no affordance, effect, or drive.yaml can ever reference. Pair/affordance/zone/group/message scopes are consequently storage nobody's config can touch.
3. **`lifetime` is hardcoded on both required surfaces**, in opposite directions (`environment.yaml` → always `tick`, `vfs_profiles.yaml` → always `persistent`/`episode`) — no accumulator/counter/cooldown is authorable on `environment.yaml`, and no global profile variable can ever be author-declared to reset with the episode. (`hamlet-4597fd5d04`, `hamlet-0268336cd1`.)
4. **`set_engine_value` shape-bypass lets declared schema drift permanently** once any VTC/evaluator write legitimately produces a batched result for a nominally-global-scalar variable — all future validation silently anchors to the drifted shape instead of the declaration. (`hamlet-d970ef83f0`, `hamlet-2ca2cb373f`.)
5. **Silent write-back drops on unknown variable ids** at three sites in `vectorized_env.py` (global-profile writeback, agent-profile writeback, `_commit_vtc_transition_state`) — a compiled write to a vanished/renamed variable disappears with no error, a real hazard during any variable-rename refactor. (`hamlet-0ddc83e377`.)
6. **Item-scoped variables aren't reachable through the documented `registry.get()` accessor** — "read the variable I declared" fails for one of nine scopes via the API the docs point to. (`hamlet-f2a37a8c8a`.)
7. **Global-tensor variables hard-fail exactly when their leading dimension equals `num_agents`** — a config can compile clean and then crash at the first `env.step()` purely as a function of an unrelated training hyperparameter. (`hamlet-f54b887148`.)
8. **Sparse pair storage is fully unreachable from any config pack** (new finding) — real, tested code with no wiring; lower-ranked than the above because dense pair storage at least works and no shipped pack currently needs sparse.


---

# Appendix B — Profiles / expressions / observation-spec / VTC audit

(Verbatim report; verdicts and evidence as filed by the auditor.)

# VFS Audit — Profiles / Expressions / Observation-Spec / VTC surface

Scope: vfs_profiles.yaml (global/agent/item profiles), expression language, observation
fields/spec/hashes, variables_reference.yaml overlay, VTC (transition compiler). Sibling agent
covers registry/access-control/scopes.

Spec sources read in full: `docs/architecture/vfs.md` (2637 lines), `docs/config-schemas/vfs-profiles.md`,
`docs/config-schemas/variables.md`, `docs/architecture/vfs-current-implementation.md`.

Implementation read in full: `src/townlet/vfs/schema.py`, `src/townlet/vfs/observation_builder.py`,
`src/townlet/vfs/profiles.py`, `src/townlet/vfs/evaluator.py`, `src/townlet/vfs/schema_hashes.py`,
`src/townlet/vfs/semantic_type.py`, `src/townlet/vfs/transition_graph.py`,
`src/townlet/config/vfs_profiles_config.py`, `src/townlet/config/transition_rules_config.py`,
`src/townlet/universe/compilers/vfs.py`, `src/townlet/universe/compilers/observation.py`,
`src/townlet/universe/dto/observation_spec.py`, `src/townlet/universe/dto/observation_feature.py`,
`src/townlet/environment/observation_encoder.py`, `src/townlet/vfs/vtc.py` (3150 lines, via
forked sub-agent), `src/townlet/vfs/transition_schedule.py`. Plus a pack census over all 36
shipped `configs/**/vfs_profiles.yaml` files.

---

## Area 1 — `vfs_profiles.yaml` (global/agent/item profiles)

| Claim | Verdict | Evidence | Notes |
|---|---|---|---|
| Schema version `"1.0"` required, validated | IMPLEMENTED | `vfs_profiles_config.py:341` (`Literal["1.0"]`); `profiles.py:94-98` `validate_version` | |
| Exactly one of `initial_value` / `initial_value_mode` / `expression` (global & agent) | IMPLEMENTED | `vfs_profiles_config.py:61-74` (global), `:172-185` (agent) | Doc's "XOR Constraint" table (vfs-profiles.md §"Required Fields") only lists two members (`initial_value`, `expression`); code has three. Minor **DOC-DRIFT** — not false, just incomplete. |
| Item-profile: exactly one of `initial_value` / `expression` (no `initial_value_mode`) | IMPLEMENTED | `vfs_profiles_config.py:276-285` | Matches doc — item profiles never got the tensor-init-mode extension. |
| Item-profile `expression:` refuses at compile | IMPLEMENTED | `profiles.py:339-346` — `compile_item_profile` raises `ValueError` for any item variable declaring `expression` | Doc (`vfs-profiles.md`) has already been corrected in place to describe this as current behavior (hamlet-bc0a5deeff), so this is doc-matches-code, not drift. See Area 2 for the feature-gap framing. |
| `semantic_type` required for global/agent vars, forbidden value `bars`, absent for item vars | IMPLEMENTED | `vfs_profiles_config.py:37` (`GlobalVFSVariableConfig.semantic_type: SemanticType`, no default), `:146` (agent, same); `ItemVFSVariableConfig` (`:245-295`) has **no** `semantic_type` field at all | `bars` rejection enforced downstream at `compilers/observation.py:386-393`, not in the DTO itself. |
| Unique variable names within one profile | IMPLEMENTED | `field_validator validate_unique_names` in `GlobalVFSProfileConfig`, `AgentVFSProfileConfig`, `ItemVFSProfileConfig` | |
| Item profile forbids tensor types | IMPLEMENTED | `vfs_profiles_config.py:287-292` `validate_tensor_disallowed` | Matches vfs-current-implementation.md "Current Boundaries". |
| Dependency resolution: topological sort, cycle detection | IMPLEMENTED | `profiles.py` `CircularDependencyError`, `topological_sort_with_dependencies`, `build_dependency_graph` (AST-based, not regex) | |
| Cross-profile dependency rule ("only same-profile refs become edges") | IMPLEMENTED | `profiles.py:126-128` — edge only added `if dep in variable_names` (same profile's variable set) | Cross-profile bare-name references simply fail type-check downstream (undefined name), matching doc's "Undefined Variable Error" troubleshooting entry. |
| **`exposed_to` empty → silently rewritten to `["agent"]`** | **DIVERGED (doc-acknowledged)** | `vfs_profiles_config.py:121-129` (`GlobalVFSProfileConfig.default_metadata`), `:232-240` (agent), `:319-327` (item) — `if not var.exposed_to: var.exposed_to = ["agent"]` | Violates No-Defaults Principle. `vfs-profiles.md` itself flags this ("hidden default... tracked for WS-4"), so it is a **known, registered** divergence, not silent doc drift. See "Top Gaps" #1 below — the check is `if not var.exposed_to`, which fires identically whether the field is omitted **or explicitly set to `[]`**, so there is currently no way to author a genuinely hidden profile variable. |
| Ambient engine name `tick` admitted into expression schema without becoming a dependency edge | IMPLEMENTED (undocumented) | `profiles.py:29-35` `AMBIENT_ENGINE_NAMES = {"tick": "float"}`; excluded from `_extract_variable_refs` deps at `:124` | Not mentioned anywhere in `vfs.md`/`vfs-profiles.md`. Sensible design (token-obs ruling 6) but is unwritten authoring surface. |
| Pack census: how many profile variables declare `exposed_to` explicitly | **CONFIRMED** | Census over 36 shipped `vfs_profiles.yaml` files: ~49 total profile variables declared; only **2** (`trial_f_durability`, `test/set_encoder_smoke`) declare `exposed_to` explicitly. `default_curriculum/vfs_profiles.yaml` declares zero global/agent profile variables at all (only an empty item profile). | Matches the "1 of 31" figure in spirit — overwhelming majority of authored profile variables rely on the silent default. |

## Area 2 — Expression language

| Claim | Verdict | Evidence | Notes |
|---|---|---|---|
| Namespace access `bar.<name>`, `temporal.<field>`, `self.<field>` (item only), bare var-name references | PARTIAL (corroborated, not independently traced through `world/expression/`) | `profiles.py:307-309` builds `bar.<name>` schema entries; `compilers/vfs.py:145-151` builds `vfs.<name>` / `self.vfs.<name>` / `target.vfs.<name>` schema entries for effects | `world/expression/` itself (parser, type checker, evaluator) is out of the files I read in full — flagging as corroborated-but-not-exhaustive. |
| Agent-profile expressions evaluate at runtime | IMPLEMENTED | `evaluator.py` `VFSEvaluator.evaluate_global_profile` is used for **both** global and agent profiles (`compilers/vfs.py:74-77` calls `compile_global_profile` on the agent profile too) | Confirms known fact: agent-profile expressions do evaluate. |
| Item-profile expressions have no evaluator (refuse at compile) | **MISSING** (feature) / **IMPLEMENTED** (the loud-refusal behavior) | `profiles.py:339-346` | The refusal itself is correctly implemented (fail-loud, matches project philosophy). But the underlying **feature** — declarative computed item state — does not exist for the entire item scope. Every item-profile variable must be static; dynamic item state (spoilage, durability decay) must go through effects instead of VFS profile expressions, contradicting the general "declare relationships, not code" framing for this one scope class. |
| Mark-and-sweep evaluation: statics never marked, never clobber engine writes | IMPLEMENTED | `compilers/vfs.py:155-180` `derive_evaluation_marks` (only expression vars with `exposed_to` or overlay `observable:true` are marked); `evaluator.py:182-197` — in `MARK_AND_SWEEP` mode, a static reached via dependency-chase does **not** overwrite `context.vfs[var.name]` (comment explicitly cites hamlet-df3a96bbac) | Confirms the "write-back skips statics" fix (commit c0ffb214) is in place and behaves as documented. |

## Area 3 — Observation fields / spec / activity mask

| Claim | Verdict | Evidence | Notes |
|---|---|---|---|
| Each exposed global/agent profile variable compiles to its OWN observation field, named after the variable, author's declared `semantic_type` | IMPLEMENTED | `compilers/observation.py:365-410` (PDR-0075) | Collision against environment.yaml vars / meter fields / compiler blocks is a compile error (`:369-378`). |
| Item-profile variables observed via ONE compiler feature `obs_item_slots` (slot × profile-position) | IMPLEMENTED | `compilers/observation.py:412-439`; `ITEM_SLOTS_OBSERVATION_FIELD` constant `:57` | `obs_vfs` (the old single-block design) is fully gone from live code — only referenced in historical comments (`grep` confirmed zero live occurrences). |
| Fixed semantic-group layout order `spatial, bars, affordance, effects, custom, temporal`, contiguity enforced | IMPLEMENTED | `semantic_type.py:46` `SEMANTIC_GROUP_ORDER`; `observation.py:468` stable-sort; `:546-575` `_assert_semantic_groups_are_contiguous` | `bars` reserved to meters, compile error if an authored/profile variable declares it (`:319-328`, `:386-393`). |
| `curriculum_active` preserves fixed ABI width, masks inactive dims | IMPLEMENTED | `schema.py` `ObservationField.curriculum_active`; `observation.py:510-544` `build_activity` | |
| All 9 normalization kinds implemented and reachable (not "mostly minmax/zscore") | IMPLEMENTED | `observation_builder.py:106-164` `apply_normalization` implements `none, minmax, zscore, cyclical_sin_cos, binary, one_hot, log_scaled, rank_scaled, masked_value`; `clip` required on `minmax`/`log_scaled`, forbidden elsewhere (`schema.py:151-165`) | `rank_scaled` at `observation_builder.py:93-103` confirmed (argsort-based rank / (N-1)). |
| Declared normalization is actually **applied** at runtime (not just compiled+hashed) | IMPLEMENTED | `observation_encoder.py:109-148` `_apply_declared_normalization` | Code comment explicitly documents the prior bug (WS-1(e): compiled/hashed but never called) as now fixed. |
| Feature-dispatch vocabulary (`variable`, `grid_encoding`, `local_window`, `position`, `velocity`, `meter`, `affordance_at_position`, `effects`, `temporal`, `item_slots`) drives runtime, never field name | IMPLEMENTED | `observation_feature.py`; `observation_encoder.py:332-342` `_FEATURE_PUBLISHERS` (9 engine publishers + `variable` skip) | No `if field.name == "obs_..."` branches remain anywhere in the read files. |
| Observation-field UUID computed deterministically, includes `semantic_type` | IMPLEMENTED | `dto/observation_spec.py:18-41` `compute_observation_field_uuid` | |
| `observation_schema_hash` payload = ordered fields + source var + shape + normalization + `exposed_to` + `curriculum_active` + dtype + semantic_type, **except version metadata** | IMPLEMENTED-AS-DOCUMENTED | `schema_hashes.py:153-163` `_canonical_observation_entry` | Matches vfs.md §8.4's own caveat exactly — no version field in the payload. |
| `full_manual` mode reorders fields to `include_fields`; group contiguity still enforced downstream | IMPLEMENTED | `observation.py:878-902` `_apply_observation_mode`; contiguity check (`_assert_semantic_groups_are_contiguous`) runs in `build_activity`, called after mode filtering | |
| Superset + per-level activity mask semantics (allocated width constant, active width varies) | IMPLEMENTED (by design, not re-measured) | `ObservationActivity.active_mask` / `group_slices` (`observation.py:510-544`) | Did not re-run the compiler to re-verify the specific 124/95/56/99 figures in vfs.md §2.3 — the doc itself already flags those as a dated measurement, not a spec. |

## Area 4 — `variables_reference.yaml` static overlay

| Claim | Verdict | Evidence | Notes |
|---|---|---|---|
| Optional at pack root; static only (no `expression`) | IMPLEMENTED | `schema.py:606-627` `load_variables_reference_config` raises if any variable declares `expression` | |
| Cannot define item-scoped variables | IMPLEMENTED | `schema.py:628-629` | |
| `zone`/`group`/`message` scopes require matching top-level `extents:` entry; missing extent is a compile error, not a runtime crash | IMPLEMENTED | `schema.py:566-660` `VFSScopeExtents`, `_SCOPE_EXTENT_FIELD`, extent-presence check `:642-658` | Matches hamlet-9e1ae3b7a2 closure claim. |
| `observable: true` overlay entry marks an expression profile variable for mark-and-sweep evaluation even without `exposed_to` | IMPLEMENTED | `compilers/vfs.py:155-180` `derive_evaluation_marks` — `overlay_observable & expression_vars` unioned into marks | |
| Duplicate IDs in the overlay act as an observation-metadata overlay onto an existing variable | **NOT INDEPENDENTLY VERIFIED** | Not located in the files read (likely lives in `universe/compiler.py` orchestration, not `vfs/schema.py` or `compilers/vfs.py`) | Flagged as a verification gap, not a finding either way. |

## Area 5 — VTC (transition compiler)

*(Detailed line-level verification of `vtc.py` performed by a forked sub-agent against 12 specific claims; results folded in below.)*

| Claim | Verdict | Evidence | Notes |
|---|---|---|---|
| All 11 `WriteSpec` composition modes declared in schema | IMPLEMENTED | `schema.py:273-287` `WriteSpec.composition` Literal (11 members); `transition_rules_config.py:52-64` mirrors the same 11 for social-residue writes | |
| All 11 modes **executed** by `VTCActionWriteProgram` | IMPLEMENTED | `vtc.py` `_compose_candidate` handles overwrite/last_write_wins/priority_write/clamp/additive_delta/multiplicative_modifier/min/max; `_apply_composed_write` dispatches `claim_if_free`/`capacity_claim`/`append_event` to dedicated methods | |
| **`VTCSocialResidueProgram` supports only 8 of 11 modes** | **DIVERGED (undocumented)** | `VTCSocialResidueProgram._apply_composed_write` explicitly raises `NotImplementedError` for `claim_if_free`/`capacity_claim`/`append_event` | Schema allows authoring these on a social-residue write; nothing stops an author until runtime. Not called out anywhere in vfs.md §16. See Top Gaps. |
| Phase-snapshot / commit-batch execution model (§13.4) | IMPLEMENTED | `VTCActionWriteProgram.apply` (snapshot → compute against snapshot → commit fresh `phase_values`); same pattern in `VTCSocialResidueProgram.apply` | |
| `claim_if_free`: bool rows free when false; numeric/reference rows free when every element negative | IMPLEMENTED | `_row_free_for_claim` — bool dtype uses `~row_any`; else `_row_all(value < 0)` | Exact match to doc wording. |
| `capacity_claim`: integer `clamp` = capacity, deterministic order, no over-allocation | IMPLEMENTED | `_apply_capacity_claim` requires `write.clamp`, `_capacity_from_clamp` enforces non-negative int, `eligible_indices[:remaining_capacity]` | |
| `append_event`: first zero/false slot, full buffers unchanged | IMPLEMENTED | `_apply_append_event` — `if free_slot_indices.numel()==0: continue` | |
| `VTCBoundsClampProgram`: one rule/meter, no active mask, applies to every agent | IMPLEMENTED | `vtc.py` (class definition confirmed); docstring states the "dead agent still bounded" rationale | |
| All 10 claimed VTC program classes exist | IMPLEMENTED | `VTCActionWriteProgram`, `VTCThresholdCascadeProgram`, `VTCPassiveDepletionProgram`, `VTCBoundsClampProgram`, `VTCModulationProgram`, `VTCAffordanceGateProgram`, `VTCInteractionProgressProgram`, `VTCTerminalConditionProgram`, `VTCSocialResidueProgram`, `VTCRewardProgram` — all present, none stubbed | |
| `VTCRewardProgram` is a validation contract, not reward math | IMPLEMENTED | `apply()` calls `reward_backend.calculate_rewards(...)` (delegates), then only validates tensor shapes and required component keys | Confirms doc's "reward math stays in `DACEngine`" framing exactly. |
| Compiler-generated writes validate against phase-snapshot shape, not declared `VariableDef` schema | CONFIRMED AS DOCUMENTED GAP | `_coerce_expression_tensor` validates only against the phase-snapshot tensor's shape/dtype, never `VariableDef` | Matches vfs.md §7.4/§21.1's own "known gap" wording exactly — not a new finding, a confirmation. |
| `transition_graph_hash` payload = phase graph + rules from all 9 rule-bearing programs | IMPLEMENTED | `schema_hashes.py:56-94` `canonical_transition_graph_schema` | One stale artifact: `_canonical_transition_rule` (`:183-237`) still has a `hasattr(write, "target")` branch that can never fire now that `target` was removed from the write DTO (§16.3) — dead code, harmless. |
| Default transition phase graph (18 phases) matches vfs.md §11.4 exactly | IMPLEMENTED | `transition_graph.py:7-26` `DEFAULT_TRANSITION_PHASES` — identical order to the doc | |
| Affordance occupancy "wired end-to-end" (hamlet-ef6699ab2a) | IMPLEMENTED | `transition_schedule.py` `build_vtc_transition_schedule` routes **all** runtime actions through `compile_vtc_affordance_occupancy_with_phase_graph`, not just ones with `source_affordance` | |
| Social residue: 3 rule kinds, rule+write condition combination, pair-scope `active[i] & active[j]` masking, `target` field rejected at compile | IMPLEMENTED | `_SOCIAL_RESIDUE_RULE_KINDS` set; `_combined_condition` (`(rule) and (write)`); `_active_mask_for_target` (`active.reshape(N,1) & active.reshape(1,N)`); `_coerce_social_residue_write` raises on `"target" in raw_write` | Matches §16.3 exactly, including the "removed 2026-08-22" claim. |
| Social-residue authoring surface: `transition_rules.yaml`, `extra="forbid"`, `condition`/`clamp`/`effect`/`scope` required-nullable (no default, `null` must be explicit) | IMPLEMENTED | `transition_rules_config.py` — all four fields have no `default=`, so Pydantic requires them present (value or `null`) | Matches No-Defaults Principle precisely, and matches doc's own description of the DTO. |
| No shipped pack currently declares `transition_rules.yaml` | CONFIRMED | `find configs -iname transition_rules.yaml` → zero results | Matches vfs.md §21.1 item 7 ("no shipped pack declares rules yet"). |
| **`VTCModulationProgram` rejects `condition:` and non-`multiplicative_modifier` compositions only at runtime** | **DIVERGED (undocumented)** | `compute_affordance_multiplier` raises `NotImplementedError` for any modulation rule with a non-null `condition_ast`, or any composition other than `multiplicative_modifier` | The scripted-kernel path only covers the one composition mode it was written for. A config author declaring `condition:` on a modulation rule (a plausible reading of §14.2/§14.3's `RelationshipSpec` examples, which do show conditions on other rule kinds) **compiles green** and crashes on the first `env.step`. Not mentioned in vfs.md §14. |

## Area 6 — Provenance hashes

| Claim | Verdict | Evidence | Notes |
|---|---|---|---|
| `variable_schema_hash` payload: id, type, scope, dims, lifetime, readable_by, writable_by, normalization range | IMPLEMENTED | `schema_hashes.py:140-150` `_canonical_variable_entry` | |
| `action_schema_hash` payload: id, name, type, source, enabled, costs, effects, delta, teleport_to, source_affordance, reads, writes | IMPLEMENTED | `schema_hashes.py:166-180` `_canonical_action_entry` | |
| `vfs_hash` = sha256(variable_hash + observation_hash + action_hash + transition_hash) | IMPLEMENTED | `schema_hashes.py:129-137` `compute_vfs_hash` | |
| All hashes canonicalized via sorted-key JSON before SHA-256 | IMPLEMENTED | `schema_hashes.py:260-267` `_hash_payload` (`sort_keys=True`) | |

---

## Verdict tally

- **IMPLEMENTED**: ~34
- **PARTIAL**: 2 (expression-language namespace access not independently traced; duplicate-ID overlay merge not located)
- **MISSING**: 1 (item-profile expression evaluation as a *feature* — the refusal behavior itself is correctly implemented)
- **DIVERGED**: 3 (`exposed_to` silent default; `VTCSocialResidueProgram`'s 3 missing composition modes; `VTCModulationProgram`'s runtime-only rejection of unsupported rule shapes)
- **DOC-DRIFT**: 1 (minor — vfs-profiles.md's XOR table omits `initial_value_mode` as a third option for global/agent variables)

No divergence found where `vfs-current-implementation.md` actually misdescribes shipped code in this audit's scope — every claim checked there (semantic-type vocabulary, feature vocabulary, hash contents, evaluator statics behavior, current-boundaries list) matched the source precisely. That document earns its "Status: Current" label for the surface covered here.

---

## Top gaps ranked by authoring-surface impact

1. **`vfs_profiles.yaml` cannot currently author a hidden global/agent variable.** `default_metadata`'s `if not var.exposed_to: var.exposed_to = ["agent"]` fires identically whether `exposed_to` is omitted *or explicitly declared `[]`* (`vfs_profiles_config.py:121-129`, `:232-240`). That means every worked example in `vfs-profiles.md`'s own "Best Practices #4" ("Hidden (internal state): `readable_by: ["engine"]`") and every private/epistemic-access scenario in `vfs.md` §5.3 ("Social observability and privacy" — `perceived_health`, `internal_motivation`-style variables) is **unauthorable through `vfs_profiles.yaml` today**: the variable will always compile an observation field and always be exposed to the agent, regardless of author intent. This is the single sharpest gap in this audit's scope because it silently contradicts the framework's central multi-agent/epistemic-access pitch, and because — per the pack census — it is already the behavior 96%+ of authored profile variables are unknowingly relying on. (Whether the compiled field then actually fails a runtime read-permission check is a `registry.get_agent()` question outside this agent's scope — flagged as a boundary observation for the sibling audit.)

2. **`VTCModulationProgram` fails at runtime, not compile time, for a plausible authoring pattern.** A modulation rule with `condition:` set, or any composition mode other than `multiplicative_modifier`, compiles without error and only raises `NotImplementedError` on the first `env.step`. The project's own stated discipline (fail loud at compile time, not at the first observation/tick — see e.g. `compilers/observation.py`'s extensive compile-time guardrails for exactly this class of mistake) is not applied here. A designer following §14.2/§14.3's `RelationshipSpec` examples (which show conditions freely) has no way to know modulation rules are more restrictive until training crashes.

3. **`VTCSocialResidueProgram` silently supports only 8 of the 11 declared composition modes.** `claim_if_free`, `capacity_claim`, and `append_event` all validate at the schema layer (`transition_rules_config.py`) but raise `NotImplementedError` at execution. Lower urgency than #2 today because no shipped pack authors social-residue rules yet, but it is exactly the kind of rule (contested claims, witnessed events) a multi-agent author would reach for first once L5/L6 content ships.

4. **Item-profile scope has zero declarative dynamism.** Every item-profile variable must be static (`initial_value` only); spoilage/durability/etc. must be driven by effects instead. This is honestly documented (not hidden), but it means one of VFS's three profile scopes is, in practice, not "declarative variables" at all — it's "declarative storage, imperative-via-effects update," which is a narrower authoring promise than the other two scopes give.

5. **`exposed_to` default (item #1) is the same root cause behind the census finding** that ~96% of authored profile variables never state their exposure explicitly — already tracked by the project as WS-4, so this is a known backlog item rather than a fresh discovery, but the audit's pack census (2 of ~49) puts a concrete number on how total the reliance on the silent default currently is.

## Boundary observations (sibling agent's area, not audited here)

- Whether `registry.get_global()` / `registry.get_agent()` (used by `observation_builder.build_vfs_observation`) enforce `readable_by` at all, or bypass it the way `set_engine_value()` bypasses shape checks — directly relevant to gap #1 above (does a hidden-but-accidentally-exposed variable crash at runtime, or does the observation pipeline read straight past `readable_by`?).
- The duplicate-ID "observation metadata overlay" merge behavior for `variables_reference.yaml` (Area 4, not located in the files this audit covered — likely in `universe/compiler.py` orchestration).
