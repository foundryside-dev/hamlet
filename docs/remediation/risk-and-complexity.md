# Remediation plan: bounded risk and complexity

Written 2026-10-24, after VFS round-1 (WP1-WP8, merged), compiler WP1/WP2 and effects WP1/WP2
(PR 53), with compiler WP3/WP4 and effects WP3 in the working tree, and VFS round 2
(`review-2026-10-24/findings_vfs_round2.md`) proposing WP9-WP17 and spec decision S1.
These are order-of-magnitude estimates. The point is that each range names what bounds it.

## 1. Method

- **Bounded** means a range plus the assumption that sets each end. Low end: the planned work
  packages land at today's measured rate and the next review of the seam finds nothing that needs
  remediation. High end: planned packages plus one further review round at the yield VFS round 2
  actually produced, plus its remediation. Outside the range means an assumption broke.
- **Complexity unit: the sprint.** One sprint is one parallel phase of about four packages with
  verifiers, roughly half a day of wall-clock. Package sizes from the plans are converted to points
  (S = 1, M = 2, L = 4). **Measured today:** 12 packages (VFS WP1-8, compiler WP1-2, effects WP1-2)
  landed between 06:55 and 15:21 in three phases: VFS round 1 was 11 points in 2 sprints, phase 3
  was 5 points in 1 sprint. Rate used: **5 points per sprint**. A review round costs 1 sprint.
- **Risk** is the probability that the subsystem is NOT done after its planned packages, i.e. that a
  fresh review of the seam would still find at least one P1 inside its scope and force another full
  review-remediate cycle. "Done" is undefined in every plan (see section 3.2), so this document
  assumes that stop rule.
- **Evidence:** the five remediation plans, `REVIEW_SYNTHESIS.md`, the six findings files (round-1
  bodies read via summaries, gap tables and coverage sections), `git log` for throughput, source
  and test volumes, and direct reads of `configs/default_curriculum` and the code sites cited below.
- **Base rate for risk.** VFS round 1 found 3 P1 / 7 P2. All eight packages landed. Round 2, the
  same day and one layer deeper, found **5 P1 / 8 P2 / 1 P3 plus 10 spec problems**. The P1 count
  rose after remediation. No other seam has had a round 2, so none can claim a lower base rate.

## 1a. Volumes (source lines, test files)

| area | src lines | test files | reviewed in this campaign |
|---|---|---|---|
| `vfs/` | 6,084 | 53 | rounds 1 and 2 |
| `universe/` + `config/` | 7,937 + 4,268 | 47 + 24 | round 1 |
| `substrate/` | 3,305 | 33 | round 1 |
| `effects/` + `world/expression/` | 3,984 + 2,888 | 43 | round 1 |
| `items/` + reward/affordance parts of `environment/` | 1,578 + 5,878 (shared) | 20 + 33 | round 1 |
| `population/`, `agent/`, `exploration/`, `training/`, `curriculum/` | 2,051 + 1,246 + 858 + 3,522 + 865 | 6 + ~4 + 16 | **not reached** (checkpoint gate only) |
| `demo/`, `recording/` | 3,486 + 1,776 | 8 | **not reached** |
| total `src/townlet` | 51,923 | 417 files, 97k lines; 4,751 tests collected | |

One collection error today (`tests/test_townlet/unit/demo/test_presentation.py` imports a deleted
`PresentationError`) is the in-flight compiler WP4, evidence the tree is mid-sprint, not a finding.
About 13.8k source lines (27%) were outside every reviewer's scope.

## 2. Per subsystem

### 2.1 VFS

| remaining package | content | size | on `default_curriculum` path |
|---|---|---|---|
| WP9 | evaluate profiles at end of `reset()`; one tick for `tick`, `day_phase`, `time_of_day` | S | **yes** (L3 clock lag and stale reset hour) |
| WP10 | expression source and `semantic_type` into `vfs_hash`; `variables_hash` pack hash | S | **yes** (reproducible resume) |
| WP11 | shared per-slot visibility mask for item and item-state publishers | S | no (no items) |
| WP12 | shape-proved writes; refuse writes to expression-owned targets; spawn schema; token-spec diagnostics | M | no |
| WP13 | rule S1, then implement (per-world `global` axis, or declared agents-per-world) | M-L | no (decision is still blocking, see 3.1) |
| WP14 | temporal history operators: admit or delete | M | no |
| WP15 | delete or complete `agent_private`, `message`, `pair`; clean L5 | M | no |
| WP16 | checkpoint `persistent`-lifetime registry state | S | **yes** (`day_phase` is `persistent`) |
| WP17 | spec text: identity rule by brain type, one-spelling resolver, rule `reads`/`kind`, inline expressions | M | partial |

| measure | low | high | what bounds it |
|---|---|---|---|
| complexity (sprints) | 3 | 7 | low: 14-16 points, but ordering (WP9-11, then S1, then WP12 before WP14, WP13 before WP15) forces at least 3 phases. high: + round-3 review + remediation at round-2 yield |
| risk of not done | 60% | 80% | round 2 out-found round 1; ten spec problems still open |

**Top risk drivers**

1. **S1 changes storage shape.** Option A gives `global` a per-world axis (registry, publishers,
   VTC, effects writes, every `vfs_hash`); option B makes the agent token real (token spec, strata,
   items). Either way the change lands after other locks have been taken.
2. **Bugs live at the consumers.** Round-2 P1s sat on VFS's boundary with items (F3 item-state
   publisher), the env reset/step loop (F1, F2) and checkpointing (F5, F13). A VFS-only review
   cannot finish them while those consumers are open.
3. **Spec still moving.** S3 (identity rule gated on brain type) couples VFS to BaC; S5 (one
   resolver for five spellings) rewrites effects, item spawn and DAC entry points.

**What collapses the range:** an S1 ruling written down before WP12 starts (removes the M-L
uncertainty and settles WP15's keep-or-delete); a decision to delete rather than complete `pair`,
`message`, `agent_private` and the history pipeline (turns WP14/WP15 into S deletions).

**Edges:** feeds strata WP3/WP4 and items WP1/WP5 (via S1), effects WP6 and items spawn (via S5),
compiler (F5 hash, F12 diagnostics), BaC (S3), checkpointing in `demo/runner.py` (WP16).

### 2.2 Universe compiler

| remaining package | content | size | on default path |
|---|---|---|---|
| WP3, WP4 | dead required fields; `presentation` one vocabulary; item capacity rule | M + S | in flight, counted as landing |
| WP5 | identity discriminator; indistinguishability over affordances and effects | S | no |
| WP6 | CLI diagnostics; cache fingerprint path- and cwd-aware; `inspect` freshness | S | partial (C11 is a reproducibility leak) |
| WP7 | residue; wall-clock asserts out of the default selection | S | no |

| measure | low | high | what bounds it |
|---|---|---|---|
| complexity (sprints) | 1 | 4 | low: 3 own points plus in-flight completion. high: + first round-2 review + remediation |
| risk of reopen | 80% | 95% | every other plan adds cross-validate refusals here |
| risk of redesign | 15% | 25% | discovery, merge, cache and round trip were heavily refuted in round 1 |

**Top risk drivers**

1. **It is the landing zone for everyone else's refusals.** Strata WP3/WP4, items WP3/WP4, effects
   WP3/WP7 and VFS WP12 all add checks to cross-validate. The compiler cannot be locked before UaC.
2. **Every deletion moves a hash.** WP3 moves `training_hash` and friends on every pack; that is
   free now but invalidates any baseline or checkpoint taken before the last deletion lands.
3. **No round 2.** Round 1 found 2 P1 / 7 P2. The VFS base rate says a second pass finds as much.

**What collapses the range:** split "reopen" from "redesign" explicitly in the stop rule: new
refusals added by another seam's package do not reopen the compiler lock; changes to discovery,
artifact shape or the identity gate do.

**Edges:** consumes VFS (F5, F12), strata, items and effects refusals; feeds the checkpoint gate.

### 2.3 Strata

| package | content | size | on default path |
|---|---|---|---|
| WP1 | boundary-aware masking via a substrate method; at-least-one-legal guarantee | M | no (default is `clamp`) |
| WP2 | single scaling in Continuous2D; `action_discretization` conditional | S | no |
| WP3 | refuse over-capacity instead of silently disabling randomization | S | partial (fires only if population is raised; 8 + 14 fits 64 cells) |
| WP4 | rank-generic item placement (shared with items WP1) | M | no |
| WP5 | one `WAIT` vocabulary; true ordering contract | S | no |
| WP6 | bounded velocity; delete name branches on `velocity_*` | S | no |
| WP7 | vocabulary hygiene; label signs | S | no (viewer only) |
| WP8 | residue | S | no |

| measure | low | high | what bounds it |
|---|---|---|---|
| complexity (sprints) | 2.5 | 5 | low: 12 points. high: + round-2 review + ~1.5 sprints remediation |
| risk of not done | 40% | 60% | lowest in the plan: geometry refuted across every family, metric and boundary |

**Top risk drivers**

1. **S1 reaches here.** The capacity check counts `len(self.affordances) + self.num_agents` against
   grid cells (`vectorized_env.py:1600`). Under the token spec's independent-worlds reading that is
   one agent per world, so the check WP3 hardens is wrong by construction until S1 is ruled.
2. **Shared ownership.** WP4 is items WP1; neither seam can lock alone.
3. **Thin shipped content.** No continuous-2D or continuousND pack ships; the families most changed
   by WP1/WP2/WP6 have only test packs to check against.

**What collapses the range:** the S1 ruling (fixes WP3's formula); one shipped non-grid pack.

**Edges:** VFS S1; items WP1 (WP4 shared); compiler cross-validate (WP3, WP4).

### 2.4 UaC: effects and expressions

| package | content | size | on default path |
|---|---|---|---|
| WP3 | time and position into effects; refuse history operators | M | in flight, counted as landing |
| WP4 | type checker and evaluator agree on all 49 functions | M | partial (affordance `modify` expressions) |
| WP5 | one clock for `time_in_window` and hours | S | no (24 matches by accident) |
| WP6 | entity addressing per scope (`self`/`target`, `effect.*` namespace) | M | no |
| WP7 | typed `switch`; honest budgets; bind `for_each ... as:`; `active_effects` | M | no |
| WP8 | indistinguishability over affordances and effects (shared with compiler WP5) | S | no |
| WP9 | residue; regenerate `effects.md` and `expressions.md` from the registry | M | no |

| measure | low | high | what bounds it |
|---|---|---|---|
| complexity (sprints) | 2 | 6 | low: 10 points. high: + round-2 review + remediation at round-1 yield (5 P1 / 12 P2) |
| risk of not done | 70% | 90% | highest P2 count of any seam; WP6/WP7 are design decisions, not fixes |

**Top risk drivers**

1. **Spec unsettled.** What `self` and `target` mean per scope, whether `for_each` binds, what
   `active_effects` returns: each is decided inside a package, so later review can dispute it.
2. **Coupled to VFS S5 and S1.** The one-spelling resolver rewrites the effects context; global
   effects writes change meaning under S1 option A.
3. **No shipped content.** `default_curriculum` declares `effect_definitions: []`; lifecycle, catalog
   and spawn paths are exercised only by `configs/test/*`.

Note: the command executor is on the default path. `affordance_engine.py` runs every affordance
`on_start` (`modify: target.bar.satiation ...`) through `CommandExecutor`, so effects WP2 (landed)
was load-bearing for `default_curriculum`.

**What collapses the range:** a one-page addressing table (WP6) agreed before implementation;
deleting `active_effects` and history operators rather than completing them.

**Edges:** VFS (S1, S5, WP8 context), compiler (WP5 = WP8), items (WP5 clock = items WP3;
WP3 positions feed items WP6 `spawn_item`).

### 2.5 UaC: items, affordances, meters, rewards

| package | content | size | on default path |
|---|---|---|---|
| WP1 | items on every substrate (needs strata WP4, compiler WP1) | M | no (no item types) |
| WP2 | DAC on declared semantics: normalize before compare, delete `or 1.0`, completion means completion | M | **yes** (see note) |
| WP3 | hours validated against `day_length`; refuse on non-temporal levels | S | no |
| WP4 | dead agents gated; overlapping affordances; metric-aware `approach_reward` | S | **yes** (shaping uses `approach_reward`) |
| WP5 | held items and item identity | M | no |
| WP6 | `on_drop`, `spawn_item`, interaction progress | M | no |
| WP7 | delete inert vocabulary incl. intrinsic dual authority | M | **yes** (intrinsic part) |
| WP8 | declared retirement bonus; spawn accounting | S | **yes** (hard-coded `+1.0` retirement) |
| WP9 | whitelist | S | no |

| measure | low | high | what bounds it |
|---|---|---|---|
| complexity (sprints) | 3 | 7 | low: 14 points. high: + round-2 review + remediation at round-1 yield (6 P1 / 8 P2) |
| risk of not done | 70% | 85% | 6 P1 in round 1; item identity and locality spec unsettled; three shared packages |

Note on the default reward stream: I3, I4 and I5 do not fire on `default_curriculum`. Its only
modifier is on `energy` (bounds 0..1), `base_reward` is 0.01 (truthy), and all interactions are
`instant` (70 of 70 across the five levels), so completion equals interaction. The stream is correct by parameter accident, not by
construction. "Believable" means WP2, WP7 (one intrinsic authority: `training.yaml: intrinsic.*`
and `drive.yaml: intrinsic` both exist today) and WP8 (an undeclared `+1.0` in every reward).

**Top risk drivers**

1. **Dependency-blocked.** WP1 waits on strata WP4; WP3 on effects WP5; WP6 on effects WP3.
2. **S1 reaches here.** One `ItemManager` serves the whole batch (`vectorized_env.py:638`), so items
   are world-shared while the token spec says worlds are independent.
3. **Reward and intrinsic code sits in unreviewed territory.** Intrinsic strategy selection lives in
   `exploration/` and `population/`, which no reviewer reached.

**What collapses the range:** the S1 ruling; an explicit decision that items stay a test-pack
feature until a second authored world needs them (moves WP1, WP5, WP6 off the critical path).

**Edges:** strata WP4, compiler WP1 (landed), effects WP3/WP5, VFS S1, BaC layer 2 (intrinsic).

### 2.6 BaC (two rows, not one)

| row | scope | complexity (sprints) | risk of not done | on default path |
|---|---|---|---|---|
| Layer 2 hardening | network/optimizer/loss/replay, `population/`, `agent/`, `exploration/`, `training/`, `curriculum/` (~8.5k lines) | 2-6 | 60-85% | **yes** |
| Layers 1 and 3 | cognitive topology, module registry, execution graph, cognitive hash | 12-30 | 90%+ | no |

Layer 2: no review has run, so there is no plan. Low end: 1 review sprint plus 1 sprint of fixes;
high end: round-1 yield seen elsewhere (9 to 17 P1+P2 per seam) plus a second pass. Layers 1 and 3:
zero code (`cognitive_topology`, `execution_graph`, `agent_architecture` return no hits), design
content only in archived documents with false status lines; low end is 2-4 sprints of design and
owner decisions plus about 10 of implementation; high end assumes one redesign.

**Top risk drivers**

1. **Layer 2 is the learning loop and nobody has read it this campaign.** Population has 6 test
   files for 2,051 lines. README says intrinsic strategy integration is unfinished.
2. **Randomness is not isolated.** `exploration/action_selection.py:85-88` draws from the global
   torch RNG (`torch.randint`, `torch.rand`) with no per-stream generator.
3. **Layers 1/3 spec unsettled and DQN-shaped runtime.** A think-loop graph has to fit a batched
   value-based training loop; that fit has never been designed.

**What collapses the range:** a Layer 2 review now (one sprint) converts the widest unknown on the
default path into a plan; for Layers 1/3, a written spec reviewed against the token-set encoder
before any code.

**Edges:** VFS S3 (identity rule by brain type), items WP7 (intrinsic authority), checkpointing,
shakedown.

### 2.7 End-to-end shakedown and integration

| measure | low | high | what bounds it |
|---|---|---|---|
| complexity (sprints) | 4 | 10 | low: one pass over train, resume, serve, reproduce on `default_curriculum` L1-L3 with fixes. high: two passes plus `demo/`/`recording/` review |
| risk of needing a second pass | 75% | 90% | covers 27% of source never reviewed; CUDA never exercised |
| wall-clock outside agent time | not estimated | | training runs to a learning signal cost GPU hours, not sprints |

**Top risk drivers**

1. **Reproducibility has no owning subsystem.** It needs pieces of VFS, compiler, BaC layer 2 and
   the demo checkpoint payload to all be right at once (section 3.3).
2. **Learning signal is a property of the whole stack.** Reward, intrinsic RND, annealing, DQN and
   curriculum have never been measured together on the current tree.
3. **S1 semantics surface only in combination.** Placement, items, globals and occupancy each look
   correct alone.

**What collapses the range:** a continuous canary from now on (section 3.2), so the shakedown starts
with known failures rather than discovering them.

**Edges:** every subsystem; `demo/runner.py` checkpoint payload (VFS WP16), checkpoint gate
(compiler WP2 landed, VFS WP10).

### 2.8 Summary table

| subsystem | remaining packages | complexity (sprints) | risk not done | default-path sprints |
|---|---|---|---|---|
| VFS | WP9-WP17 + S1 | 3-7 | 60-80% | 1-2 (WP9, WP10, WP16) |
| Compiler | WP5-WP7 (+WP3/4 in flight) | 1-4 | reopen 80-95%, redesign 15-25% | 0-1 (WP6 cache identity) |
| Strata | WP1-WP8 | 2.5-5 | 40-60% | 0-0.5 (WP3, partial) |
| Effects + expressions | WP4-WP9 (+WP3 in flight) | 2-6 | 70-90% | 0-0.5 (WP4 partial) |
| Items + affordances + rewards | WP1-WP9 | 3-7 | 70-85% | 1-2 (WP2, WP4, WP7 part, WP8) |
| BaC layer 2 | unplanned | 2-6 | 60-85% | 2-6 |
| BaC layers 1 + 3 | unplanned | 12-30 | 90%+ | 0 |
| Shakedown | unplanned | 4-10 | 75-90% | 3-8 |
| **Total, full plan excl. BaC L1/L3** | | **17.5-45** | | |
| **Total, `default_curriculum` goal** | | | | **7-20** |

At two sprints per working day: full plan 9 to 23 days; default-curriculum goal 3.5 to 10 days. Both
exclude owner decision latency and training wall-clock.

## 3. Overall

### 3.1 Critical path

```text
                    +--> VFS WP13/WP15 --------------------------------+
S1 ruling ----------+--> strata WP3 (capacity), WP4 --> items WP1/WP5 -+--> full-plan locks
                    +--> items ItemManager scope ----------------------+
                    +--> effects global writes (WP6) ------------------+

VFS WP9, WP10, WP16 --------------------------+
items WP2, WP7 (intrinsic), WP8 --------------+--> default_curriculum shakedown --> trainable,
BaC layer 2 review + fixes -------------------+    (L1, L2, L3; resume; 2 seeds)    reproducible
```

- **Full plan:** S1 is the root. Four lock candidates (VFS, strata, items, effects) depend on it.
  Next longest chain: strata WP4 then items WP1/WP5/WP6 then effects WP3/WP5 dependents, about
  4-5 sequential sprints before items can be reviewed for a lock.
- **Default-curriculum goal:** the critical path does not run through S1 (its only global, `tick`
  via `day_phase`, is legitimately batch-uniform) and runs through BaC layer 2, which has no
  review and no plan. That is the widest single range on the path that matters.
- The owner's sequence (VFS and compiler, then UaC, then BaC, then shakedown) puts the unreviewed
  training stack last, after every lock. The default goal needs it first.

### 3.2 Where "lock a subsystem as done" is weakest

1. **No stop rule exists.** None of the five plans defines done. Without one, "iterate until bug
   free" is unbounded, and the only data point (VFS round 2) shows discovery rising, not falling.
   Proposed rule: a seam locks when a fresh review of its declared scope finds zero P1 and at most a
   small fixed number of P2, and additive refusals from another seam's package do not reopen it.
2. **Compiler lock reopens on every UaC package.** Certain but cheap, if the stop rule says so.
3. **VFS lock reopens on S1 and S5.** S1 changes storage shape; S5 changes the entry points of
   effects, item spawn and DAC. Locking VFS before both are ruled is a lock that reopens.
4. **Items and strata cannot lock independently.** Strata WP4 = items WP1; effects WP5 = items WP3;
   effects WP8 = compiler WP5; VFS WP8 touched the effects context. Shared packages mean shared locks.
5. **Hash churn invalidates any interim baseline.** Compiler WP3, items WP7 (`layout_hash` via
   `recovery.natural`), VFS WP10 (new `vfs_hash` inputs), S1 option A, strata WP6/WP7 all move
   identity. Learning baselines taken before the last of these are throwaway; smoke runs are not.

**Mitigation for the lock-then-shakedown shape:** run a canary after every sprint, now: `run_demo`
on L1 and L3 for a few hundred episodes, checkpoint, resume, two seeds, compare streams. It costs
minutes, it is not a learning claim, and it turns the shakedown's unknowns into a running list.

### 3.3 Integration risks no per-subsystem sprint retires

| risk | why no seam owns it | evidence |
|---|---|---|
| Reproducible resume | needs VFS (F5 expression hash, F13 persistent state), compiler (C11 path-blind cache), BaC L2 (global RNG in action selection), demo checkpoint payload, CUDA determinism | `findings_vfs_round2.md` F5/F13; `exploration/action_selection.py:85-88`; CUDA never exercised |
| Shared world vs independent worlds | S1 shows up in placement capacity, the single `ItemManager`, `global` storage, affordance occupancy (never exercised at runtime by any reviewer); only visible when they run together | `vectorized_env.py:638, 1600`; `token_spec.py:1294-1307` |
| Learning signal | a property of reward + intrinsic RND + annealing + DQN + curriculum; four of those five are unreviewed; M4 evidence is from `9d4e942f`, not the current tree | README "M4"; review coverage limits |

### 3.4 Honest total

Reaching **a trainable, reproducible environment on `default_curriculum` with a believable reward
stream** is about **7 to 20 sprints (3.5 to 10 working days at today's rate)** if scoped to that goal:
VFS WP9/WP10/WP16, items WP2/WP4/WP7/WP8, a BaC layer 2 review and its fixes, and a
default-only shakedown. Probability that it is reached without a further unplanned cycle somewhere:
**about 15-30%**, mostly because the training stack has never been reviewed and reproducibility has
no owner. Pursued as written (every seam locked before the shakedown), the same goal sits behind
**17.5 to 45 sprints (9 to 23 days)** with a **near-certain (90%+) reopening of at least one lock**
during the shakedown, chiefly VFS and items on S1 and the compiler on additive refusals. BaC layers
1 and 3 are a separate 12-30 sprint body of work with an unwritten spec and are not on either path.

## 4. Where the estimates are weakest

- Throughput is one day of data on S/M packages with pre-written specs; design-bearing work (S1,
  effects addressing, BaC) will not run at 5 points per sprint.
- Round-1 findings bodies were read through summaries, gap tables and coverage; no reproduction
  was re-run for this document.
- BaC layer 2 and the shakedown have no review data at all; their ranges are analogies to other seams.
- Owner decision latency (S1, S3, S5, WP6 addressing) and training wall-clock are not modelled.
- Whether `global_tick` survives checkpoint resume (relevant to WP16 and L3) was not verified.
