# Trial B — `tensorNd` evidence audit: RECORD

Date: 2026-08-21
Author: commissioned evidence auditor (fresh agent; executed neither run of Trial B)
Pin: `1ef1d950`
Pre-commitment: `B-tensornd-audit-precommitment-20260821.md` (read in full before any probe was run)
Pattern: `PDR-0098` — outcome branches fixed before the audit ran.

---

## 1. The question

> **Does a global-profile `tensorNd` VFS variable express "an entity that is a set of occupied
> cells rather than a point" at pin `1ef1d950`, as facet B-F2 pre-committed it?**

B-F2's binding accepted evidence (from `B-blind-countersigned-facets-20260820.md`, ~line 42):

> an in-process probe reads the organism's extent from the compiled/runtime state … and prints
> (a) the container's shape or the enumerated occupied coordinates, and (b) `occupied_count` —
> showing a value **> 1** at some tick. Each occupied cell is a 5-tuple.
> **Exclusion, binding:** an "occupied set" obtained by **unioning N agents' individual position
> vectors** does **not** satisfy B-F2. … If the only state locating the organism is a per-agent
> `positions` tensor of shape `(n_agents, 5)`, the entity is a point (or a bag of points) and
> B-F2 fails.

## 2. VERDICT

**Branch A — SOUND.** Run 2's B-F2 PASS **stands**.

All four clauses of B-F2 hold on the pre-committed accepted evidence, and each was verified by a
probe written for this audit rather than taken from the record:

| clause | verified | evidence |
|---|---|---|
| readable state | YES | compiled artifact, raw registry storage, and `registry.get()` all agree |
| belonging to **one entity** | YES | `scope: global`; storage `(3,3,3,3,3)` — **no agent prefix**, confirmed at `population.size: 2` |
| occupied count **can exceed 1** | YES | 3 at reset from a declared asymmetric pattern; 243 after a declared decision |
| occupied count **can change** | YES | 1→243, 1→81, 1→162 by three distinct declared routes |
| **not** a union of agent positions | YES | `positions` is `(n_agents, 5)`, a separate variable; container shape is independent of `n_agents` |

The pre-commitment's named discriminator — "is there an index-selected *cell* write, or is
whole-container assignment the only write?" — **resolves as: there is no index-selected cell
write.** That is established below with verbatim refusals. It is recorded, and it does **not**
fail B-F2, for the reason given in §6.

---

## 3. Method

### 3.1 Worktree and freeze

Worked only in the pinned worktree
`/tmp/.../scratchpad/tensornd-audit`, at `1ef1d9508b8908b533f901438bbf8aa9c13ccffd`.

```
$ git rev-parse HEAD
1ef1d9508b8908b533f901438bbf8aa9c13ccffd

$ git status --porcelain -- src/townlet/
(end)                      <- empty: PDR-0090 substrate freeze held; nothing touched

$ diff -rq -x '__pycache__' src/townlet /home/john/hamlet/src/townlet
(source diff end — empty means pin == live for .py)
```

The last line **independently confirms the pre-commitment's own load-bearing claim** (§"Constraints
on the audit": `git diff --stat 1ef1d950..HEAD -- src/townlet/` is empty, "verified by the
commissioning agent"). This audit verified it separately, by direct tree comparison rather than by
git range. A finding at the pin is therefore a finding at HEAD, with no drift caveat required.

Everything created by this audit is an untracked scratch config pack under `configs/audit_*`.
No file under `src/townlet/` was read-modified, and no ticket was filed.

### 3.2 Interpreter provenance (recorded because it is not the documented invocation)

`uv sync` in the worktree had not finished when probing began, so probes ran under the live
tree's already-populated virtualenv **with `PYTHONPATH` pinned to the worktree source**. That the
code under test came from the pin, not the live tree, was verified explicitly:

```
$ PYTHONPATH=$(pwd)/src /home/john/hamlet/.venv/bin/python -c "import torch, townlet; ..."
torch 2.11.0+cu130
townlet from: /tmp/.../scratchpad/tensornd-audit/src/townlet/__init__.py
registry from: /tmp/.../scratchpad/tensornd-audit/src/townlet/vfs/registry.py
```

The venv supplies only third-party dependencies. Combined with the `diff -rq` above (pin and live
`src/townlet/*.py` are byte-identical), the finding is a finding at the pin.

### 3.3 Cache hygiene

The live pack `configs/trial_b_blind_organism/` ships a `.compiled/universe-L1_spread.msgpack`.
It was **deleted from every audit copy** before compiling, so no result below can be a stale-cache
artifact. (`CLAUDE.md` already warns that a green `validate` writes no artifact while `inspect`
then fails; a shipped cache is a false-pass vector in the other direction.)

### 3.4 Independence from the artifact under audit

`configs/trial_b_blind_organism/probe_trial_b.py` is the artifact under audit. It was **not
imported or executed** as evidence. It was read once, only to learn the mechanical convention for
forcing an affordance interaction (set `env.positions` to the affordance's deployed position, then
step `INTERACT`). Every number in this record comes from probes written for this audit:
`audit_probe.py`, `route_test.py`, `obs_and_extras.py`, `final_checks.py`, `c3b_2ag.py`.

### 3.5 The falsification design

Run 2 only ever exhibited `occupied_count ∈ {1, 243}` — all-zero-plus-one-cell, and all-one. Those
two states are exactly the states that a **broadcasting accessor**, a **read-of-a-default**, or a
**never-allocated variable** would also produce. So the audit's primary probe is not a
re-execution of run 2's: it authors a pack whose declared initial pattern is **asymmetric** —
ones at `(0,0,0,0,0)`, `(0,0,0,0,1)`, `(1,2,0,2,1)` — a configuration **no broadcast can
produce**. If the read-back matches those coordinates exactly, per-cell state is real.

Pack `configs/audit_b_asym` is byte-identical to run 2's pack except for that one line:

```
$ diff <(sed 's/initial_value: \[\[\[\[\[.*/INITVAL_LINE/' configs/audit_b_repro/vfs_profiles.yaml) \
       <(sed 's/initial_value: \[\[\[\[\[.*/INITVAL_LINE/' configs/audit_b_asym/vfs_profiles.yaml)
IDENTICAL apart from the initial_value line
```

---

## 4. What was executed

### 4.1 Probe 1 — the asymmetric read-back (the decisive test)

```
$ PYTHONPATH=$(pwd)/src python audit_probe.py configs/audit_b_asym
========================================================================
PACK  : .../configs/audit_b_asym
LEVEL : L1_spread
========================================================================

--- [1] COMPILED ARTIFACT ---
vfs_variables count      : 10
var id                   : organism_cells
var scope                : global
var type                 : tensorNd
var shape (declared)     : [3, 3, 3, 3, 3]
var lifetime             : persistent
var readable_by          : ['agent', 'engine']
var writable_by          : ['engine']
default is None          : False
default tensor shape     : (3, 3, 3, 3, 3)
default occupied count   : 3
default occupied coords  : [(0, 0, 0, 0, 0), (0, 0, 0, 0, 1), (1, 2, 0, 2, 1)]

observation total_dims   : 270

--- [2] RUNTIME REGISTRY (stepped env) ---
registry num_agents      : 1
RAW storage tensor shape : (3, 3, 3, 3, 3)
RAW dtype                : torch.float32
RAW occupied count       : 3
RAW occupied coords      : [(0, 0, 0, 0, 0), (0, 0, 0, 0, 1), (1, 2, 0, 2, 1)]
reg.get() shape          : (3, 3, 3, 3, 3)
reg.get() occupied count : 3
reg.get() occupied coords: [(0, 0, 0, 0, 0), (0, 0, 0, 0, 1), (1, 2, 0, 2, 1)]

--- [3] AFTER env.reset() ---
shape                    : (3, 3, 3, 3, 3)
occupied count           : 3
occupied coords          : [(0, 0, 0, 0, 0), (0, 0, 0, 0, 1), (1, 2, 0, 2, 1)]

--- [4] PERSISTENCE ACROSS TICKS (WAIT only) ---
occupied_count per tick  : [3, 3, 3, 3]
final occupied coords    : [(0, 0, 0, 0, 0), (0, 0, 0, 0, 1), (1, 2, 0, 2, 1)]
```

Note that **both** the private storage tensor (`registry._storage["organism_cells"]`) **and** the
public accessor (`registry.get(...)`) were read, and both returned the same asymmetric pattern.
That is what closes the "accessor returns a synthesised default" class.

### 4.2 Probe 2 — "one entity" is structural, not an artifact of `population.size: 1`

The sharpest available attack on the PASS: if global-scope tensors carry a leading agent
dimension, then "one entity's state" would be an accident of there being one agent. Source says
otherwise — `registry.py:452-456`:

```python
def _scope_prefix_shape(self, var_def: VariableDef) -> tuple[int, ...]:
    scope = VariableScope(var_def.scope)
    if scope == VariableScope.GLOBAL:
        return ()
    if scope in (VariableScope.AGENT, VariableScope.AGENT_PRIVATE):
        return (self.num_agents,)
```

Confirmed empirically by recompiling the same pack at `population.size: 2`:

```
$ python audit_probe.py configs/audit_b_asym_2ag --agents 2
registry num_agents      : 2
RAW storage tensor shape : (3, 3, 3, 3, 3)      <- unchanged
RAW occupied count       : 3
RAW occupied coords      : [(0, 0, 0, 0, 0), (0, 0, 0, 0, 1), (1, 2, 0, 2, 1)]
```

The container's shape is **independent of the agent count**. The attack is closed.

### 4.3 Probe 3 — write-surface enumeration

Each route builds a variant pack, compiles, constructs a stepped env, forces `GROW`, and reads
back the occupied set. Classification vocabulary: **ABSENT** (no such surface), **INERT**
(declares, validates, no-ops), **BLOCKED** (fails loudly), **WORKS**.

| # | route (declared in `GROW.on_start`) | compile | runtime | class |
|---|---|---|---|---|
| R1 | `modify: vfs.organism_cells[0][0][0][0][1]` | REFUSED | — | **BLOCKED** |
| R2 | `value: "max(vfs.organism_cells, vfs.growth_mask_1)"` | OK | RAISED | **BLOCKED** |
| R3 | `value: "scatter(vfs.organism_cells, 1, 1.0)"` | OK | RAISED | **BLOCKED** |
| R4 | `value: "masked_set(vfs.organism_cells, 1.0, vfs.growth_mask_1 > 0.5)"` | OK | RAISED | **BLOCKED** |
| R5 | `value: "vfs.organism_cells + vfs.growth_mask_1"` | OK | RAISED | **BLOCKED** |
| R6 | `modify: vfs.organism_cells`, `value: "1.0"` (run 2's route) | OK | OK | **WORKS** — floods to 243 |
| R8 | `value: "max(global.vfs.organism_cells, …)"` | OK | RAISED (type check) | **BLOCKED** |
| C3a | `value: "max(target.vfs.organism_cells, target.vfs.growth_mask_1)"` | OK | RAISED | **BLOCKED** |
| C3b | `modify: target.vfs.organism_cells`, `value: "1.0"` | OK | OK | **WORKS** — writes 81 |
| C3c | `modify: self.vfs.organism_cells`, `value: "1.0"` | OK | RAISED (type check) | **BLOCKED** |
| E1 | `organism_cells` declared via `expression:` | REFUSED | — | **BLOCKED** |
| E2 | `initial_value_mode: eye` at rank 5 | REFUSED (badly) | — | **BLOCKED** |
| E3 | `cascade_graph` edge targeting the container | REFUSED | — | **ABSENT** |

Verbatim, for the load-bearing ones:

**R1 — the cell-indexed write. Reconfirms run 2's refusal exactly.**

```
CompilationError: Stage 3: Reference Resolution failed:
  - [UAC-RES-VFS] .../configs/audit_rt_r1-indexed-modify/levels/L1_spread/affordances.yaml -
    Affordance 'GROW' interaction uses unknown VFS variable 'organism_cells[0][0][0][0][1]'.
```

**R2 / R4 / R5 — any expression that reads the container back.**

```
File ".../src/townlet/vfs/registry.py", line 559, in set
    raise ValueError(f"Value for '{variable_id}' has shape {tuple(value.shape)}, expected {tuple(expected_shape)}")
ValueError: Value for 'organism_cells' has shape (1, 3, 3, 3, 3), expected (3, 3, 3, 3, 3)
```

**R3 — `scatter`.**

```
IndexError: index 1 is out of bounds for dimension 0 with size 1
```

**R8 — the `global.vfs.*` read form does not exist in the type-checker schema.**

```
TypeCheckError: Path 'global.vfs.organism_cells' not found in schema. Available paths:
['intensity', 'elapsed_ticks', 'duration_remaining', 'bar.energy', 'target.bar.energy',
 'bar.biomass', 'target.bar.biomass', 'vfs.organism_cells', 'target.vfs.organism_cells',
 'vfs.warehouse_position', 'target.vfs.warehouse_position', 'vfs.organism_size',
 'target.vfs.organism_size', 'vfs.growth_mask_1', 'target.vfs.growth_mask_1', 'self.vfs.is_body']
```

**E1 — the variable's own `expression:` field.**

```
CompilationError: Stage 6: Enrich shared schemas and effects failed:
  - [VFS-PROFILE-COMPILE] .../configs/audit_e1/vfs_profiles.yaml -
    Reference traversal requires schema entry for 'vfs.organism_cells'
```

**E3 — cascades. `CascadeConfig` is meter-to-meter by construction** (`environment_config.py:161-168`,
`source: str` / `target: str` documented as "Source meter name").

```
CompilationError: Stage 1b: v2.1 Semantic Validation failed:
  - [CASCADE_INVALID_METER] .../environment.yaml - environment.yaml cascade_graph references
    unknown meters: ('energy', 'organism_cells')
```

**R6 — run 2's whole-container write, reproduced exactly.**

```
occupied BEFORE : n=1 [(0, 0, 0, 0, 0)]
  tick 1: n=243  tick 2: n=243  tick 3: n=243
occupied_count series : [1, 243, 243, 243]
=> FLOODED to all cells
```

### 4.4 Probe 4 — a write route run 2 did not find

`modify: target.vfs.organism_cells` compiles, runs, and produces a cardinality that is **neither
1 nor 243**:

```
ROUTE C3b  write to target.vfs.organism_cells directly
COMPILE : OK
before  : occupied=1
  tick 1: occupied=81  [(0,0,0,0,0), (0,0,0,0,1), (0,0,0,0,2), (0,0,0,1,0), (0,0,0,1,1)]
  tick 2: occupied=81
```

The mechanism is `effects/context.py` `set_path`, `target.` branch: it fetches the whole tensor
and mutates a slice in place — `original[self.target_index] = value` — rather than calling
`vfs_registry.set(...)`. `target_index` is the **agent index**, so it selects along axis 0 of the
container. Confirmed by re-running at two agents:

```
$ python c3b_2ag.py
container shape : (3, 3, 3, 3, 3)
before          : 1
  tick 1: occupied=162  distinct axis-0 indices written = [0, 1]
  tick 2: occupied=162  distinct axis-0 indices written = [0, 1]
```

So an index-selected write **does** exist — but its index is bound to the agent index, is not
author-declarable, and its granularity is a rank-4 slab of 81 cells, not a cell. It cannot express
"add this one adjacent cell". Its effect on B-F2 is discussed in §6; it is filed as a gap in §7.

### 4.5 Probe 5 — observation encoding

```
total_dims : 270
name                         type            dims  start    end scope    active
obs_grid_encoding            spatial_grid       5      0      5 agent    True
obs_position                 vector             5      5     10 agent    True
obs_velocity                 vector             5     10     15 agent    True
organism_cells               vector           243     15    258 global   True
warehouse_position           vector             5    258    263 global   True
organism_size                scalar             1    263    264 global   True
obs_meter_energy             scalar             1    264    265 agent    True
obs_meter_biomass            scalar             1    265    266 agent    True
obs_affordance_at_position   vector             3    266    269 agent    True
obs_item_slots               vector             1    269    270 agent    True
sum of field dims: 270

runtime observation tensor shape : (1, 270)
active_mask length               : 270  active count: 270
organism slice 15:258 all active : True
```

And the encoding is not merely present but **per-cell faithful**. With the asymmetric pack, the
three declared cells must land at row-major flat indices `81a+27b+9c+3d+e`, offset by the field's
`start_index` of 15:

```
C1 — FLATTEN ORDER
declared occupied cells      : [(0, 0, 0, 0, 0), (0, 0, 0, 0, 1), (1, 2, 0, 2, 1)]
row-major flat index + 15    : [15, 16, 157]
actual nonzero obs indices   : [15, 16, 157]
EXACT MATCH                  : True
```

After the declared growth decision, the observation changes accordingly:

```
after GROW: container occupied   : 243
after GROW: nonzero obs count    : 251 (was 17)
observation CHANGED              : True
```

### 4.6 Probe 6 — durability across `reset()`

```
C2 — DURABILITY
after first reset   : occupied=1
after GROW          : occupied=243
after SECOND reset  : occupied=243
reset restores declared root (243 == 1) : False
```

The container is durable — in fact **over-durable**: `lifetime: persistent`, and `env.reset()`
does not restore the declared `initial_value`. This confirms run 2's own note N1/G-10. It
satisfies B-F2's "readable state that persists and changes"; it bears on **B-F3** (rooted at point
A), which this audit does **not** score.

---

## 5. The five sub-questions, answered

### 5.1 Is the container real?

**YES, on every surface checked.** It compiles (`scope: global`, `type: tensorNd`,
`shape: [3,3,3,3,3]`, `lifetime: persistent`), allocates at exactly the declared rank and shape
with **no agent prefix**, persists unchanged across four ticks of `WAIT`, survives `reset()`, and
reads back per-cell — as the private storage tensor and through the public accessor, in agreement.
The read-back reproduces an asymmetric three-cell pattern that no broadcast could produce. Each
occupied cell is a 5-tuple.

### 5.2 Is there an index-selected write?

**No index-selected *cell* write exists.** Twelve routes were tried (§4.3). The cell-indexed
`modify` is refused at compile Stage 3 — of the construct, not of a typo: the resolver reads the
whole indexed expression as a variable *name*. Every expression that reads the container back is
BLOCKED at runtime by a shape mismatch, because `vfs.<name>` resolves as **agent-scoped** even for
a global variable (`world/expression/context.py:73-75, 87-97`), yielding `(1,3,3,3,3)` where the
registry expects `(3,3,3,3,3)`. `global.vfs.*` is not in the type-checker schema at all. Cascades
are meter-only. The variable's `expression:` field cannot reference the container.

**One index-selected *slab* write does exist and run 2 missed it** (§4.4): `target.vfs.<name>`
writes `container[agent_index]` — 81 cells — bypassing `registry.set`. Its index is the agent
index, not an authored coordinate.

So: whole-container assignment is **not** the only write, as run 2's enumeration stated — but the
correction does not produce cell-level addressing.

### 5.3 Does cardinality change by declared means, and is it growth?

**It changes by declared means; it is not growth.** Observed cardinalities reachable from config:
**1 → 243** (whole-container scalar write, R6), **1 → 81** (agent-slab write, C3b, one agent),
**1 → 162** (C3b, two agents). It cannot go **1 → 2 → 3**. There is no adjacency-respecting
propagation: the function registry (`world/expression/functions.py`) offers no `roll`, `shift`,
`pad`, `conv`, `dilate`, or `neighbor` — the 46 registered functions are reductions, clamps,
elementwise math, noise, temporal and distance helpers — so a dilation cannot be written even as a
whole-container expression, and in any case every container-reading expression is BLOCKED.

This is the pre-commitment's named discriminator. Its status: **confirmed as predicted, and
non-binding on B-F2** — see §6.

### 5.4 Is it one entity's state, not a union of agent positions?

**YES — the exclusion is respected, structurally.** The container is one global VFS variable of
shape `(3,3,3,3,3)`. The agent `positions` tensor is `(n_agents, 5)`, a different variable
entirely. The container's shape is provably independent of the agent count (`_scope_prefix_shape`
returns `()` for `GLOBAL`; verified at `population.size: 2`, §4.2). Nothing about the extent is
obtained by unioning position vectors. B-F2's binding exclusion does not engage.

Note for completeness: C3b couples a *write's index* to the agent index. That is a property of one
write route, not of the state — the state remains one container whose value is a set of cells, and
at `population.size: 2` the container did not grow an agent dimension.

### 5.5 Is the extent observation-encoded?

**YES, fully and faithfully.** `organism_cells` compiles to its own observation field of **243
dims at indices 15–258**, `scope: global`, `curriculum_active: True`, and all 243 slots are active
in `observation_activity.active_mask`. The runtime observation tensor is `(1, 270)`. The declared
asymmetric cells appear at exactly their row-major flat indices (`[15, 16, 157]`, exact match), and
the vector changes when the container changes. The agent can perceive the extent at per-cell
resolution. B-F2 did not require this; it strengthens the PASS and removes the branch-C route the
pre-commitment flagged ("readable in-process but with no observation encoding").

---

## 6. Why the discriminator does not fail B-F2

The pre-commitment named the load-bearing sub-question as whether an index-selected cell write
exists, and observed that "a container that can only go from all-zero to all-one holds a set of
cells in the type-theoretic sense while being unable to represent *a* spreading mass."

The audit confirms there is no cell-level write. It nonetheless finds B-F2 satisfied, for three
reasons, stated so the commissioner can disagree with the reasoning rather than the facts:

1. **The countersigned list assigns adjacency and directability elsewhere.** B-F2's derivation
   line is *"an entity that is a set of occupied cells rather than a point"*; **B-F5**'s is
   *"grows outward" / "must learn to spread"* and it pre-commits adjacency and accumulation as its
   own three assertions; **B-F6**'s is directability. Reading a cell-indexed write into B-F2 makes
   it swallow B-F5 whole and makes the countersigned list redundant. B-F2's own accepted evidence
   asks for exactly: shape or coordinates, `occupied_count > 1` at some tick, 5-tuple cells, and
   not-a-union-of-positions. All four are met.

2. **The premise "it can only go all-zero to all-one" is now false.** C3b reaches 81 and 162.
   The container is not restricted to `{0, N}`. That weakens the pre-commitment's own conditional
   without rescuing growth.

3. **The failure the discriminator describes was already scored, at the right facet.** Run 2
   scored **B-F5 FAIL/ABSENT** and **B-F6 FAIL/INERT** on precisely this ground. The capability
   gap is recorded in the trial; it is not un-recorded by B-F2 passing.

This is the strongest argument *against* branch A, and it is why the record states it explicitly
rather than burying it. A reader who holds that B-F2's phrase "a set of occupied cells" implicitly
requires per-cell authorability would land on branch C. The audit does not adopt that reading,
because the countersigned text pre-commits its evidence at a lower bar and `PDR-0098`'s discipline
is to score the letter of the pre-commitment rather than re-adjudicate at maximum-knowledge time.

---

## 7. False-pass classes ruled out

| class | ruled out by |
|---|---|
| **validates but is never allocated** | raw `registry._storage["organism_cells"]` exists at `(3,3,3,3,3)`, `torch.float32`, before any step |
| **a broadcasting accessor / all-zero-or-all-one container** | asymmetric three-cell pattern `(0,0,0,0,0)`, `(0,0,0,0,1)`, `(1,2,0,2,1)` reads back exactly — unreachable by broadcast. `registry.py:669-693` `expand`s a mismatched default, so this was the live risk; the exact-shape branch was taken |
| **a read that returns a default rather than written state** | the private storage tensor and the public `registry.get()` were read separately and agreed; and the value *changes* under a declared write (1→243, 1→81, 1→162) and *persists* across ticks |
| **a write accepted at parse that silently no-ops (INERT)** | no route was INERT. Every route either changed observable state or raised loudly. R6 and C3b changed it; nine routes raised with verbatim errors |
| **state that exists only in the compiled artifact** | verified in a stepped `VectorizedHamletEnv` across `reset()` and four `step()` calls |
| **"one entity" as an artifact of `population.size: 1`** | recompiled at `population.size: 2`; container shape unchanged at `(3,3,3,3,3)` |
| **stale compiled cache** | `.compiled/` deleted from every audit pack before compiling |
| **circular evidence from the artifact under audit** | run 2's `probe_trial_b.py` was never executed as evidence |

---

## 8. Gaps found (for the standing agent to file — NOT filed here, nothing fixed)

**Scope note:** none of the following re-scores B-F5, B-F6, B-F3, or any other facet of either
run. They are engine defects observed while enumerating surfaces, recorded with evidence.

**A-G1 — `vfs.<name>` resolves as agent-scoped even for `scope: global` variables. (BLOCKED)**
`world/expression/context.py:73-75` routes root `vfs` into `_resolve_entity_path(... scope="agent")`
with `base_indices = self._default_indices()`, which then gathers along dim 0. For a global rank-5
container this returns `(1,3,3,3,3)` — i.e. it treats the container's **first spatial axis as the
agent axis**, silently returning 81 of 243 cells. Consequences: every expression that reads the
container back is rejected by `registry.set` (`registry.py:559`) with
`Value for 'organism_cells' has shape (1, 3, 3, 3, 3), expected (3, 3, 3, 3, 3)`; and run 2's
separately-recorded `IndexError: index 2 is out of bounds for dimension 0 with size 1` has the same
root cause. This is the single defect that closes `max`/`masked_set`/`scatter`/arithmetic as growth
surfaces. A `global.` root exists in `context.py:65-68` with the correct `scope="global"` /
`base_indices=None` semantics, but is **not registered in the type-checker schema**, so
`global.vfs.organism_cells` is refused at compile: `Path 'global.vfs.organism_cells' not found in
schema`. Fixing the schema registration may be sufficient to open the whole class.

**A-G2 — `target.vfs.<global tensor>` writes bypass `registry.set` entirely. (defect, currently WORKS)**
`effects/context.py` `set_path`, `target.` branch, does `original = self.get_path(rest)` then
`original[self.target_index] = value` — an in-place mutation of the registry's storage that skips
the writer authorization check, the shape validation, and any mark-and-sweep bookkeeping in
`registry.set`. Demonstrated: `modify: target.vfs.organism_cells` writes 81 cells at one agent,
162 at two. This is simultaneously the only index-selected write reachable from config and an
access-control hole.

**A-G3 — `initial_value_mode: eye` at rank 5 crashes the error path. (BLOCKED, badly)**
`registry.py:653-654` intends to raise `initial_value_mode 'eye' requires square 2D shape`. What
surfaces instead is `AttributeError: 'NoneType' object has no attribute 'expandtabs'` — the
compiler's error formatter fails on the raised error before the author ever sees the real message.
The refusal is correct; the diagnostic is unusable.

**A-G4 — no adjacency/neighbourhood primitive in the expression vocabulary. (ABSENT)**
`world/expression/functions.py` registers 49 functions (`len(FUNCTION_SPECS)`); **none** is
`roll`, `shift`, `pad`, `conv`, `pool`, `dilate`, or `neighbor` — verified by regex over the
registry, which returns the empty list. Combined with A-G1 (every container-reading expression is
BLOCKED), **no dilation is reachable at this pin** — the container can take only a uniform or
wholesale change. Stated precisely, because it is easy to overclaim: this audit shows no *named*
neighbourhood/shift primitive exists and no expression route is currently open. Whether fixing
A-G1 would let some *composition* of the registered functions (e.g. `gather` with computed
indices) express a shift was **not** tested — A-G1 blocks the attempt, and the substrate freeze
barred fixing it. See §9. This is the substantive capability gap behind the trial, and it is a
*framework* gap, not a pack gap.

**A-G5 — cascades cannot target VFS variables. (ABSENT)**
`config/environment_config.py:161-168` types `CascadeConfig.source`/`.target` as meter names and
validation refuses anything else (`[CASCADE_INVALID_METER]`). There is no declarative
per-tick passive dynamic that can touch a tensor container. `variables_reference.yaml` is
documented as static-only, so it does not fill the hole either.

**A-G6 — a variable declared with `expression:` cannot reference VFS state. (BLOCKED)**
`organism_cells` with `expression: "max(vfs.organism_cells, 1.0)"` is refused at Stage 6:
`Reference traversal requires schema entry for 'vfs.organism_cells'`. The `expression:` field is
accepted by the DTO (`vfs_profiles_config.py:57`) and is one of the three mutually-exclusive init
sources, so it reads as an available passive-dynamics surface and is not one for this scope.

**A-G7 — `env.reset()` does not restore a global variable's declared `initial_value`. (defect)**
Grow to 243, `reset()`, still 243 (§4.6). `lifetime: persistent` is doing what it says, but there
is no declarative way to say "episode-scoped global". This is run 2's G-10, independently
reproduced. **It bears on B-F3 and is flagged, not scored.**

**A-G8 — `tensorNd` is entirely undocumented.** Confirming run 2's G-1: the DTO accepts
`tensor1d`/`tensor2d`/`tensor3d`/`tensorNd` (`config/vfs_profiles_config.py:39-52`) and
`docs/config-schemas/vfs-profiles.md` documents a smaller vocabulary. The container type that
carries this entire trial — and that, per this audit, genuinely works — cannot be discovered from
the documentation. Recorded here because the audit's finding is that the capability is *real*,
which raises the cost of it being invisible.

**Observed, consistent with an existing gap:** `warehouse_position` reads `2.0` at observation
indices 258–262, outside `[0,1]`. That is run 2's G-6; not re-derived, noted only because this
audit's observation dump shows it.

---

## 9. What this audit could not establish

- **Whether A-G1 is the *only* thing closing the expression-write class.** Registering
  `global.vfs.*` in the type-checker schema is a plausible one-line opening, but the audit did not
  modify `src/townlet/` (freeze in force), so this is inference from source reading, not a
  demonstrated fix. It should be treated as a hypothesis for whoever files A-G1, not a finding.
- **Whether any surface outside the twelve enumerated routes writes a cell.** The enumeration
  covered `modify` paths (`vfs.`, `self.`, `target.`, indexed), the expression function registry,
  the variable `expression:` field, cascades, and `initial_value`/`initial_value_mode`. Run 2
  additionally closed VTC action writes (`actions.py:204-205` hardcodes `writes=()`),
  `spawn_item` positions, and `for_each`; those were **not** re-executed here — they are taken
  from run 2's record and are outside what this audit independently verified. A reader wanting
  full coverage should treat those three as run-2-attested rather than audit-attested.
- **Behaviour at other ranks and shapes.** Everything was tested at rank 5, shape `[3,3,3,3,3]`,
  on CPU, at one and two agents. `tensor1d` was exercised only incidentally
  (`warehouse_position`). Whether the agent-axis confusion in A-G1 behaves differently when the
  container's first axis happens to equal `num_agents` was not tested, and is the obvious
  follow-up: it could silently *appear* to work.
- **Training-time behaviour.** No training run was performed. Whether a 243-dim observation block
  is learnable, or how it interacts with the network architectures, is untouched and unclaimed.

---

## 10. Record integrity

The pre-commitment file was read in full before any pack was authored or any probe was run. No
section of this record predates the command output it cites. The verdict in §2 was written after
all probes in §4 had produced output. Nothing under `src/townlet/` was modified; nothing was
filed; nothing was fixed.
