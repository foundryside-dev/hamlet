# Trial F — evidence audit            2026-08-20 · auditor (did not execute Trial F)

Audits whether the recorded **PASS** in `docs/product/trials/0001/F-20260818.md` rests on evidence
that was actually produced.

Triggered by **AM-3** of `docs/product/trials/0001/O-comparison-20260820.md`, which found that
protocol §4's worked example of acceptable leg-(b) evidence —
*"`inspect --format json` shows an observation field for the wear variable"* — describes an output
the command cannot produce, and named Trial F as "a live risk … whose idea *is* the worked example."

**This file does not edit `docs/product/trials/0001/F-20260818.md`** (record integrity, §12/A.5),
does not touch `src/townlet/`, the frozen corpus, or the protocol, and is **not** a re-run of the
trial. It is a reading of a record plus re-execution of that record's own commands.

**Verdict up front: F's PASS stands.** The reasoning that discriminates it from the
"pre-committed evidence was not what was executed" reading is §1.

---

## 0. Substrate validity — the checks below are readings of the pinned substrate

Trial F pinned `e5f7dd7a50d0dcb2ac26b5dbe9035a2ce98412da` on `project-recovery-2` (P5). That commit
is the immediate parent of the trial's own landing commit `fb56fbbd`, verified by
`git merge-base --is-ancestor`.

```
$ git diff --stat e5f7dd7a50d0dcb2ac26b5dbe9035a2ce98412da..HEAD -- src/townlet/
(empty — zero output)
```

`HEAD` at audit time is `e65f59e1`. **The engine has not moved one line between F's pin and HEAD**,
so every command re-run below at HEAD is a reading of the pinned substrate. Stated explicitly
because the task asked for it to be verified rather than assumed.

The pack has drifted once since the trial, commit `a3318624`, *"lint: wrap two over-length probe
output lines in the Trial F probe script"*. The full diff is two `print(...)` calls split across
lines; no expression, value, action, or assertion changed. The YAML is untouched.

The corpus is unchanged: `sha256sum docs/product/prds/0001-corpus-FROZEN.md` =
`48840cc3…8de935d9`, matching P1, and the F entry still reads Spec *"An item degrades per use and
eventually breaks"* / Stresses *"Item-scoped variables that decay on use; item destruction"* /
**Predict: PASS**, exactly as the record quotes.

**The record's pasted probe output reproduces byte-for-byte at HEAD.** I re-ran the record's own
command:

```
$ UV_CACHE_DIR=.uv-cache PYTHONPATH=$(pwd)/src uv run python configs/trial_f_durability/probe_trial_f.py
== Facet 1: compiled wear state ==
  item_profile_vars = {'tool_stats': ('durability',)}
  item_vars_per_slot = 1, item_vfs_dim = 1
  field 'obs_item_slots': offset=58 dims=1 feature='item_slots'
  total_dims=59
  item actions available: ['DROP_SLOT_0', 'GET', 'USE_SLOT_0']

  spawned hammer at (2, 2), vfs_index=0, durability=3.0   <- expect 3.0 (facet 1)

== Facet 2/4: pick up, use, idle, use again ==
  after GET       durability=3.0 energy=0.5 obs_item_slots=[3.0]
  after USE #1    durability=2.0 energy=0.6 obs_item_slots=[2.0]   <- expect 2.0, +0.1 energy
  after 5 WAITs   durability=2.0 energy=0.6 obs_item_slots=[2.0]   <- expect durability UNCHANGED (per-use, not per-tick)
  after USE #2    durability=1.0 energy=0.7 obs_item_slots=[1.0]   <- expect 1.0, +0.1 energy
  after USE #3    durability=0.0 energy=0.8 obs_item_slots=[0.0]   <- expect 0.0, +0.1 energy

== Facet 3: at zero wear the tool stops working ==
  after USE #4    durability=0.0 energy=0.8 obs_item_slots=[0.0]   <- expect NO energy change, durability stays 0.0
  after USE #5    durability=0.0 energy=0.8 obs_item_slots=[0.0]   <- same
```

Identical to the block pasted in the record. The compile gate also reproduces:
`python -m townlet.universe validate configs/trial_f_durability --primary-level L0_tools` →
`Validation succeeded in 74.9 ms`.

Leg (a) — `git diff --stat -- src/townlet/` and `git status --porcelain src/townlet/`, both empty
in the record — is confirmed by the pin-to-HEAD diff above and by the pack containing no Python
outside its own probe script.

---

## 1. Why AM-3 does not land on Trial F

AM-3 is correct about the protocol and correct that F is the shape §4's example was drawn from.
It does not follow that F's verdict depends on that example, and it does not.

**Facet 1's pre-committed evidence is a disjunction.** Verbatim from the record's facet table:

> "`inspect --format json` **(or the compiled artifact)** shows the wear variable declared for the
> item, and after `env.reset()` a registry read returns the declared initial value"

The three parenthesised words are load-bearing. The executor pre-committed **two** instruments and
executed the sound one — the in-process `CompiledUniverse`
(`universe.vfs_observation_spec.item_profile_vars == {'tool_stats': ('durability',)}`). This is
precisely the object AM-3's own proposed replacement text names as the correct instrument
(*"Evidence naming any of those must be pre-committed against the in-process `CompiledUniverse`"*).

**Facet 4 never named `inspect` at all.** Verbatim:

> "the encoded observation tensor carries the wear value at a compiled offset (item-slot block or
> a declared observation field **named by the compiled spec**); after a use the observation at that
> offset shows the decremented value"

Facets 2 and 3 pre-committed runtime probes only.

So **no facet of Trial F pre-committed the broken command as its sole instrument, and no command
was substituted for a pre-committed one.** The reading "the pre-committed evidence was not what
was executed" describes a record that names X and runs Y. F's record names X-or-Y and runs Y.

**The clean split the audit is asked for:**

| | |
|---|---|
| **Protocol defect** | **Confirmed, and confirmed harder than AM-3 states** (§3). §4's worked example is unexecutable. |
| **Verdict defect** | **Absent.** F's PASS does not rest on the worked example. |

---

## 2. Per-facet audit

Three things stated separately per facet, as required.

### Facet 1 — an item carries a declared wear state (item-scoped variable, no Python)

| | |
|---|---|
| **Pre-committed standard** | "`inspect --format json` (or the compiled artifact) shows the wear variable declared for the item, and after `env.reset()` a registry read returns the declared initial value" |
| **What was executed** | The **compiled-artifact disjunct**. `UniverseCompiler().compile(PACK, primary_level="L0_tools", use_cache=False)` → printed `item_profile_vars = {'tool_stats': ('durability',)}`, `item_vars_per_slot = 1`, `item_vfs_dim = 1`. Then `env.reset()` and a registry read `env.vfs_registry.item_vfs[inst.vfs_index, item_profile_map["tool_stats"]["durability"]]` → `3.0`, the value declared in `vfs_profiles.yaml` (`initial_value: 3.0`). |
| **Does it meet the standard?** | **MEETS.** Both conjuncts satisfied, via an explicitly pre-committed alternative instrument. Not a substitution. |

Supporting authoring fact, verified: `durability` is written by exactly one declarative surface in
the whole pack — `items.yaml` `on_use`. `grep -rn "durability" configs/trial_f_durability/
--include=*.yaml` returns only `vfs_profiles.yaml` (the declaration), `items.yaml` (the two
`modify` commands and comments) and `experiment.yaml` (the pack name). No Python declares it.

### Facet 2 — use decrements wear; not a passive per-tick drain

| | |
|---|---|
| **Pre-committed standard** | "runtime probe: agent acquires and uses the item; wear read back (registry or observation) decreases by the declared per-use amount on use, and does NOT change across ticks with no use" |
| **What was executed** | Exactly that. `GET` → `USE` (3.0 → 2.0, i.e. the declared `- 1.0`), 5× `WAIT` (2.0 → 2.0), `USE` (2.0 → 1.0), `USE` (1.0 → 0.0). Read back both ways in the same line — registry (`durability=`) and observation (`obs_item_slots=`) — which agree at every step. |
| **Does it meet the standard?** | **MEETS.** The declared per-use amount is 1.0 and the observed decrement is exactly 1.0 at each of three uses. |

**Honest weakness, recorded (does not change the result).** The negative half is a weak test *in
this pack*: `bars.yaml` declares zero passive depletion, `effects.yaml`'s four effect definitions
are inherited dead config from the `trial_l_cooldown` copy and are referenced by nothing
(`grep` for their ids outside `effects.yaml` returns nothing; `BENCH` has empty interactions and
`on_use` spawns no effect), and no declared surface anywhere in the pack touches item VFS per tick.
So "does not change across ticks" tests engine hygiene — that nothing drifts the value uninvited —
rather than testing that the author *bound* decay to use rather than to ticks. The positive half is
the load-bearing one and it is strong. This is a note about evidential strength, not a defect: the
executed check is verbatim the pre-committed one.

### Facet 3 — at zero wear the item breaks or stops working

| | |
|---|---|
| **Pre-committed standard** | "runtime probe: drive wear to zero by repeated use; the declared consequence is observed — the item is destroyed/removed (slot empties or item disappears from world state) **OR** its use is refused/has no further effect, **whichever the pack declares**" |
| **What was executed** | Wear driven to 0.0 by three uses; then `USE #4` and `USE #5` → `durability=0.0 energy=0.8` unchanged at both. The pack declares the stops-working disjunct: `on_use: [if self.vfs.durability > 0.0 → then: (+0.1 energy; −1.0 durability); else: []]` — the guarded branch is the tool's entire effect. |
| **Does it meet the standard?** | **MEETS**, against the pre-committed lower disjunct. |

**Two confounds an adversarial reader should demand be ruled out; both are ruled out.**

1. *Was the "no further effect" just energy saturation?* No. `bars.yaml` declares
   `energy.bounds.max: 1.0` and energy sat at 0.8 when the effect stopped. There was 0.2 of
   headroom.
2. *Did `USE` even dispatch at #4/#5, or was the null result an INERT-style false pass — the action
   silently dropped, the guard never evaluated?* **Settled empirically.** On a scratchpad copy of
   the pack (never in the working tree — `git status --porcelain configs/trial_f_durability/` is
   empty), I replaced only `else: []` with an observable command
   (`modify: target.bar.health → target.bar.health - 0.25`) and re-ran the same action sequence:

   ```
   after GET    dur=3.0 energy=0.5 health=1.0  held=[0] slots=[[0]]
   after USE#1  dur=2.0 energy=0.6 health=1.0  held=[0] slots=[[0]]  obs[58]= 2.0
   after USE#2  dur=1.0 energy=0.7 health=1.0  held=[0] slots=[[0]]  obs[58]= 1.0
   after USE#3  dur=0.0 energy=0.8 health=1.0  held=[0] slots=[[0]]  obs[58]= 0.0
   after USE#4  dur=0.0 energy=0.8 health=0.75 held=[0] slots=[[0]]  obs[58]= 0.0
   after USE#5  dur=0.0 energy=0.8 health=0.5  held=[0] slots=[[0]]  obs[58]= 0.0
   ```

   The `else` branch **fires** at #4 and #5. So `USE` still dispatches at zero wear, the declared
   guard is evaluated, evaluates false, and the empty `else` is what produces the null. The item
   also remains held throughout (`held=[0] slots=[[0]]`). Facet 3's PASS is a positive observation
   of a declared consequence, not an absence of dispatch.

This is a diagnostic on a copy for the purpose of attributing the record's own result. It is not a
re-run of the trial and it produces no new verdict; the pack, the record and the engine are
unchanged.

The higher standard the corpus Spec's word "breaks" could bear — physical destruction/despawn at
zero — was adjudicated by the owner on 2026-08-18 (`PDR-0086`, restated at protocol A.9): **PASS
stands against the declarable standard; the un-declarable higher standard is a captured ABSENT
gap** (`hamlet-83806979f7`). Not re-litigated here. (Under A.2/AM-2's prospective granularity rule
"item destruction" would likely be enumerated as its own facet; that is already captured, and A.2
and AM-2 do not bind F either way.)

### Facet 4 — wear is observable to the agent  *(the facet AM-3 implicates)*

| | |
|---|---|
| **Pre-committed standard** | "the encoded observation tensor carries the wear value at a compiled offset (item-slot block or a declared observation field named by the compiled spec); after a use the observation at that offset shows the decremented value" |
| **What was executed** | The compiled spec located `obs_item_slots` at cumulative **offset 58, dims 1, feature `item_slots`**, `total_dims=59`. The probe then read `obs[0, 58]` from the tensor **returned by `env.step()`** at every step: `3.0` after `GET`, `2.0 / 1.0 / 0.0` after uses 1–3, `2.0` across the five idle ticks. |
| **Does it meet the standard?** | **MEETS**, and it is the best-evidenced facet in the record once the four checks below are added. |

The record asserts offset 58 without showing that 58 is really where that field lands in the
tensor, so I verified the chain independently:

1. **Offset arithmetic is faithful to the encoder.** `ObservationEncoder._get_observations`
   (`src/townlet/environment/observation_encoder.py:26-49`) iterates `env.observation_spec.fields`
   in order, appends one tensor per field and `torch.cat`s them on dim 1. The probe's cumulative
   sum over `spec.fields` is therefore *the* layout, not a guess. Full layout at this pack:

   ```
     0.. 24  dims=25  obs_grid_encoding            feature='grid_encoding'
    25.. 26  dims= 2  obs_position                 feature='position'
    27.. 28  dims= 2  obs_velocity                 feature='velocity'
    29.. 29  dims= 1  obs_meter_energy             feature='meter'
    30.. 30  dims= 1  obs_meter_health             feature='meter'
    31.. 32  dims= 2  obs_affordance_at_position   feature='affordance_at_position'
    33.. 56  dims=24  obs_effects                  feature='effects'
    57.. 57  dims= 1  day_count                    feature='variable'
    58.. 58  dims= 1  obs_item_slots               feature='item_slots'
   sum(dims) = 59 = total_dims
   ```

2. **The slot is active, not a masked-to-zero allocation.** `observation_activity.active_mask` has
   length 59, 59 active, `mask[58] = True`. (The encoder multiplies by this mask, so an inactive
   field would read 0.0 regardless of state.)

3. **The observation read is independent of the registry read, and is agent-facing.** Immediately
   after `env.reset()` with nothing held, `obs[0,58] = 0.0`; after `GET`, `3.0`; after one `USE`,
   `2.0`; after `DROP_SLOT_0`, `obs[0,58]` returns to `0.0` **while the registry still holds
   `2.0`**. The observation therefore tracks the agent's own inventory slot, not a global dump of
   the registry, and it is not an echo of the same read the probe prints alongside it. Source
   agrees: `_publish_item_slots` (`observation_encoder.py:206-236`) builds the block from
   `env.item_inventory.slots` — "the exposed item-profile variables of the item in each of the
   agent's slots".

4. **No coincidence.** After `GET`, the complete set of non-zero observation entries is
   `[(12, 1.0), (24, 1.0), (25, 0.5), (26, 0.5), (29, 0.5), (30, 1.0), (32, 1.0), (58, 3.0)]`.
   Index 58 is the only entry carrying the wear value; nothing else in the tensor could have been
   mistaken for it.

---

## 3. The `inspect --format json` question, settled on F's own pack

AM-3 asserted the shortfall from run-1/run-2 of Trial O. I confirmed it against **this** pack, and
found it fails in **two** independent ways rather than one:

**(a) At HEAD the command does not run at all on this pack.**

```
$ python -m townlet.universe inspect configs/trial_f_durability --primary-level L0_tools --format json
Artifact not found: /home/john/hamlet/configs/trial_f_durability/.compiled/universe-L0_tools.msgpack
exit=1
```

`inspect` reads a prebuilt cache artifact. The trial pack ships none — the executor deleted the
copied `.compiled/` cache during authoring (authoring-log step 1, the Trial L stale-cache lesson)
and the probe compiles with `use_cache=False`. **A `use_cache=False` probe workflow never produces
the artifact `inspect` requires.** AM-3's proposed §6 replacement text covers the adjacent
*stale-or-failed-write* case ("a green `compile` is not evidence that `inspect` will work, or that
an artifact on disk is fresh") but not this *never-written* case, where `compile` was never run at
all because the trial's own probe path bypasses the cache. Additive to that amendment, not a
correction of it.

**(b) With the cache built, the payload still cannot show a wear variable.** Built on a scratchpad
copy (so no `.compiled/` was written into the working tree — verified empty `git status
--porcelain configs/trial_f_durability/`), `inspect --format json` succeeds and returns:

```
TOP KEYS: ['action_schema_hash', 'artifact', 'metadata', 'observation_schema_hash',
           'transition_graph_hash', 'variable_schema_hash', 'vfs_hash']
observation_dim: 59            (a scalar int)
meter_names: ['energy', 'health']
'obs_item_slots' in payload?  False
'item'    substring anywhere?  False
'profile' substring anywhere?  False
'field'   substring anywhere?  False
'offset'  substring anywhere?  False
```

No observation-field enumeration, no offsets, no VFS profiles, no item slots. `meter_name_to_index`
exists for meters; there is no equivalent for item or profile variables. **AM-3 is confirmed on
Trial F's own pack: had facet 1 named `inspect --format json` as its sole instrument, that facet
could not have been evidenced as written.**

**One methodological note worth carrying.** My first automated check reported
`'durability' in payload? True`. It is a **false positive**: the string occurs only in the artifact
*path* (`…/trial_f_durability/.compiled/…`) and the universe display name
(`"Trial F — Tool durability"`). It resolves to zero declarations. This is exactly the
"grep that falsely confirms whatever you were checking" failure CLAUDE.md warns about, and it fired
inside this audit — a substring test against a payload keyed by pack name is not evidence.

---

## 4. Where the letter of the standard and the spirit of the idea diverge

Recorded as by-catch, **not** as facet failures. Under the pre-committed standards these are met;
under the corpus's own words a designer would want more. Neither changes the verdict.

| # | finding | why it is not a verdict defect |
|---|---|---|
| 1 | **A broken tool and an empty hand are the same observation.** `obs[58] = 0.0` when the held hammer's durability is 0, and `obs[58] = 0.0` when nothing is held (§2 facet 4, check 3). At the exact state the mechanic exists to represent, the agent cannot distinguish "my tool is broken" from "I have no tool". | Facet 4's pre-committed evidence is "the observation at that offset shows the decremented value", and 3→2→1→0 does exactly that. The collision is an item-slot **encoding** limitation (empty slot encodes as zeros, no occupancy flag), not a failure of the pre-committed check. But idea F's own words are *"wear is observable to the agent"*, and this is the one place the letter and the spirit come apart. |
| 2 | **The wear value enters the observation unnormalized.** `obs[58]` carries raw `3.0` in a tensor whose every other live component sits in [0,1]. Item-profile variables carry no `semantic_type` and no normalization spec (PDR-0075), so nothing normalizes them. | Appendix A.4's obs-bounds loop would have flagged this; A.4 is prospective from trial five (§12 scope rule) and does not bind F, and no facet pre-committed a bounds check. |
| 3 | **24 of 59 observation dims are dead config.** `obs_effects` occupies 33..56 for four effect definitions inherited from the `trial_l_cooldown` copy that nothing in the pack references. | Inherited pack litter, invisible to every facet. Relevant only to §9 pack disposition (still **OUTSTANDING**, deadline 2026-10-06). |
| 4 | **Item-scoped variables are unreachable through the documented accessor.** Facet 1's second conjunct pre-committed "a **registry** read"; the probe indexes `vfs_registry.item_vfs[vfs_index, item_profile_map["tool_stats"]["durability"]]` raw. Verified: `"durability" in env.vfs_registry.variables` is **False** and `registry.get("durability", "agent")` raises `KeyError: "Variable 'durability' not found in registry"`. CLAUDE.md names `registry.get()`/`set()` as the access-control-enforcing read path; item variables do not travel it. | Immaterial to the verdict — facet 4 reads the same value through the real encoder path (`env.step()` → `obs[0,58]`) and independently confirms it reaches the agent, so the mechanic is demonstrated regardless of which accessor the probe used. But the record's own authoring-log step 7 discovered this the hard way, and it is a declarative-surface gap of the same family as rows 1–2. |

Items 1, 2 and 4 are candidates for filing under §8 (file, never fix). I have filed nothing: this
is an audit of a record, and filing is the trial executor's or owner's call.

---

## 5. Record integrity — what is verified, and the one thing that is not

**Verified: the facet table was not edited after the verdict landed.** This audit's whole verdict
turns on three parenthesised words in facet 1 — "(or the compiled artifact)". If those had entered
the record later, under the scrutiny of the 2026-08-18 methodology review, the verdict here would
invert. They did not. The record has exactly two commits, and the diff between them is one
appended section and nothing else:

```
$ git diff fb56fbbd 1ef1d950 -- docs/product/trials/0001/F-20260818.md
@@ -124,3 +124,13 @@ No facet-attached gaps: all four facets passed.
 OUTSTANDING
+
+## Post-verdict adjudication note (2026-08-18, owner-ruled at the methodology review, `PDR-0086`)
+  … (10 added lines; zero removed, zero modified)
```

`git show fb56fbbd:docs/product/trials/0001/F-20260818.md` carries facet 1's
"`inspect --format json` (or the compiled artifact)" and facet 4's "named by the compiled spec"
**verbatim, at the trial commit itself**. The record's own closing claim — *"the facet table above
is unchanged"* — is true, and is now checked rather than trusted.

**Not verified, and not verifiable: temporal priority *within* the trial commit.** F's record and
F's pack landed together in `fb56fbbd`, so P6's *"this record created before authoring: yes"* and
§4's append-only property are, for the window before that commit, **self-attested rather than
git-witnessed**. Nothing in git orders the facet table against the probe output inside a single
commit.

This is a scope boundary, **not a breach finding**. A.5 ("no verdict-section text may exist in a
record before the corresponding command output does") is prospective from trial five by §12's
scope rule, which names L/F/M/O as not re-scored, so it did not bind Trial F. What this audit
*can* say is the operative thing: **every executed command matches a standard recorded in the
facet table, every pasted output reproduces exactly at HEAD, the pin is the parent commit of the
trial's landing commit, and the table is byte-identical from that commit to now.** One further
sign points the same way: facet 1's disjunction *includes the instrument that fails*
(`inspect --format json`), which is not what a table written backwards from a successful run
would contain.

---

## 6. Verdict

| facet | meets pre-committed standard? |
|---|---|
| 1 — item carries a declared wear state | **MEETS** (via the pre-committed "or the compiled artifact" disjunct) |
| 2 — use decrements wear, not per-tick | **MEETS** (positive half strong; negative half weak in this pack, §2) |
| 3 — at zero wear the tool stops working | **MEETS** (lower disjunct, as the pack declares; mechanism confirmed by the else-branch diagnostic) |
| 4 — wear is observable to the agent | **MEETS** (offset, activity mask, agent-slot semantics and independence all independently verified) |

## **F's PASS stands.**

The record's evidence was produced, is reproducible at HEAD against an engine that has not drifted
one line from the pin, and satisfies the standards the record pre-committed. AM-3's defect is real
and is confirmed here more strongly than AM-3 states — but it is a **protocol defect** in §4's
worked example, not a **verdict defect** in Trial F. F escaped it because facet 1's pre-commitment
named two instruments and facet 4 named the compiled spec rather than the CLI.

The AM-3 amendment should proceed on its own merits (and should absorb the prebuilt-artifact trap
from §3(a)). It requires no change to Trial F's record or verdict.

---

## 7. Commands run (I re-ran no trial)

All at `HEAD` = `e65f59e1`, valid at the pin because `git diff --stat e5f7dd7a..HEAD -- src/townlet/`
is empty. Scratchpad copies were used wherever a command would write a `.compiled/` artifact;
`git status --porcelain configs/trial_f_durability/` is empty after every check.

| # | check | result |
|---|-------|--------|
| 1 | `git diff --stat e5f7dd7a..HEAD -- src/townlet/` | empty — no engine drift |
| 2 | `git log --oneline -- configs/trial_f_durability/` + full diff `fb56fbbd..a3318624` | one post-trial commit, cosmetic line-wrapping of two `print`s |
| 3 | `git merge-base --is-ancestor e5f7dd7a fb56fbbd` | true — the pin is the trial commit's parent |
| 4 | `sha256sum docs/product/prds/0001-corpus-FROZEN.md` | `48840cc3…8de935d9` — matches P1 |
| 5 | re-ran `configs/trial_f_durability/probe_trial_f.py` | output byte-identical to the record |
| 6 | `python -m townlet.universe validate configs/trial_f_durability --primary-level L0_tools` | `Validation succeeded` |
| 7 | dumped `observation_spec.fields` cumulative layout + `observation_activity.active_mask` | `obs_item_slots` at 58, dims 1, `mask[58]=True`, 59/59 active |
| 8 | read `ObservationEncoder._get_observations` / `_publish_item_slots` | field order == `torch.cat` order; item block reads `item_inventory.slots` |
| 9 | probe variant: `obs[0,58]` after reset / GET / USE / DROP | `0.0 / 3.0 / 2.0 / 0.0` with registry still `2.0` after DROP |
| 10 | full non-zero observation dump after GET | index 58 uniquely carries the wear value |
| 11 | scratchpad pack copy with an observable `else` branch, same action sequence | `else` fires at USE#4/#5 → `USE` dispatches, the declared guard is what stops the effect |
| 12 | `inspect --format json` on the pack as it ships | exit 1, `Artifact not found` (no `.compiled/`) |
| 13 | `compile` then `inspect --format json` on a scratchpad copy | 1809-byte payload; no fields/offsets/items/profiles; `observation_dim` scalar 59 |
| 14 | `grep -rn "durability" configs/trial_f_durability/ --include=*.yaml` | declared once, written once (`items.yaml` `on_use`); no per-tick surface |
| 15 | `grep` for the four `effects.yaml` ids elsewhere in the pack | zero hits — inherited dead config occupying dims 33..56 |
| 16 | `git diff fb56fbbd 1ef1d950 -- docs/…/F-20260818.md` + `git show fb56fbbd:…` | only the post-verdict note appended; facet table byte-identical since the trial commit |
| 17 | `"durability" in vfs_registry.variables` / `registry.get("durability", "agent")` | `False` / raises `KeyError` — item variables are unreachable through the documented accessor |
