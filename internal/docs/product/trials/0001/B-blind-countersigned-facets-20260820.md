# Countersigned facet list — idea B, blind re-run

(enumerated independently under §4 as amended by B.2; countersigner has not seen any prior run,
any trial record, any PDR, or any existing `configs/trial_*` pack)

**Scope.** The corpus entry states *"Scored as ONE corpus entry on B2; B1/B3 are diagnostic
facets."* Facets B-F1…B-F8 below are enumerated from the **B2 headline** only — *"spread across a
5-D discrete landscape toward a food warehouse"* — and the §1 headline PASS/FAIL is determined by
these eight alone. B1 and B3 are carried as non-gating diagnostics with their own IDs (see below).

**Pack location** (B.5): the blind run authors at `configs/trial_b_blind_<slug>/`.

**Evidence discipline** (B.3): no facet below pre-commits evidence that `inspect --format json`
cannot produce. That command is used only for `substrate`, `action_count`, `affordance_ids`,
`meter_names`, and a *recorded-only* scalar `observation_dim`. Every claim about observation
fields, offsets, scopes, effects, VFS profiles or population size is pre-committed against the
in-process `CompiledUniverse` / runtime registry / stepped env.

**Surface phrasing.** Accepted evidence is stated as a *property to be demonstrated*, not as a
named YAML key, so that any surface may win it (A.2's first-reach vs any-surface distinction is
preserved; the winning surface is recorded per-facet at verdict time under B.4).

---

### Facet B-F1 — Environment premise: the pack **is** a 5-D discrete `gridnd` world containing exactly **one** organism as a single decision locus

The trial pack must *satisfy* the premise, not merely tolerate it: five live spatial dimensions,
and one organism that is one policy acting on the whole mass.

- **Accepted evidence (leg b):**
  1. `UV_CACHE_DIR=.uv-cache uv run python -m townlet.universe inspect configs/trial_b_blind_<slug> --primary-level <level> --format json` reports a `gridnd`-family substrate; paste the substrate block. Record `action_count` (a 5-D discrete grid implies 2×5 substrate moves plus the non-substrate actions; the value is recorded either way and the facet does not turn on the arithmetic).
  2. **Dimensionality is live, not decorative:** an in-process probe prints a coordinate/extent vector of **length 5**, and demonstrates non-degenerate extent or motion along at least one axis of index ≥ 2 (0-based) — i.e. the 3rd/4th/5th dimensions are usable, not a 5-D declaration collapsed onto two.
  3. **Agent/decision-locus count.** `inspect` does **not** report population (B.3), so this is in-process: the probe prints the agent dimension of the position tensor (the corpus's own reference point is Trial 001's `positions` shape `(4, 6)`) together with any declared population/agent count. **The passing value is 1.** Any N > 1 used to represent the spreading mass **FAILS B-F1** and is recorded verbatim as *the group-of-agents workaround* — it is never partial credit toward the headline, per §1 ("90%-authorable is FAIL").
  4. Temporal mode is recorded: the premise requires only that state advances per tick so growth accumulates; no day/night mode is presupposed. If the pack declares one, it is recorded, not required.
- **Surface (filled at verdict time):** —
- **Derivation:** Spec B2 *"spread across a **5-D discrete landscape**"*; Spec *"**An** organism rooted at point A … must learn"* (singular ⇒ agent count 1); Stresses *"`gridnd` at 5-D"*. B.2(iii) names agent count, substrate and temporal mode as the premise facet's three components.

### Facet B-F2 — The organism exists in world state as a **set of occupied cells** of variable cardinality, not as a position

There is readable state, belonging to one entity, whose occupied-cell count can exceed 1 and can change.

- **Accepted evidence (leg b):** an in-process probe reads the organism's extent from the compiled/runtime state (registry variable, compiled occupancy/claim structure, or whatever surface the pack declares) and prints (a) the container's shape or the enumerated occupied coordinates, and (b) `occupied_count` — showing a value **> 1** at some tick. Each occupied cell is a 5-tuple.
  - **Exclusion, binding:** an "occupied set" obtained by **unioning N agents' individual position vectors** does **not** satisfy B-F2. The extent must be readable as **one entity's state** — one thing whose value is a set of cells. If the only state locating the organism is a per-agent `positions` tensor of shape `(n_agents, 5)`, the entity is a point (or a bag of points) and B-F2 fails.
- **Surface (filled at verdict time):** —
- **Derivation:** Stresses — *"the deep one — **an entity that is a set of occupied cells rather than a point**. Every agent in this engine carries a position … a spreading mass is not a position."*

### Facet B-F3 — The organism is **rooted at point A**: its extent initializes at one declared origin cell

- **Accepted evidence (leg b):** compile, `env.reset()`, then the probe prints the occupied set. It contains **exactly one** cell, and that cell's 5-D coordinate **equals the coordinate declared in the pack** (the declaring file/construct is recorded in the surface column). A root that is random, engine-chosen, or not pinnable to a declared cell fails the facet.
- **Surface (filled at verdict time):** —
- **Derivation:** Spec *"An organism **rooted at point A**"*.

### Facet B-F4 — A **food warehouse** exists as a distinct entity at a declared location in the 5-D landscape

- **Accepted evidence (leg b):**
  1. `inspect --format json` — if the warehouse is authored as an affordance, its id appears in `affordance_ids`; if it feeds a meter, that meter appears in `meter_names`. Paste the relevant list (this is within what B.3 says the command reports).
  2. **Placement**, which `inspect` does *not* report: an in-process probe prints the warehouse entity's position vector (length 5) and it equals the coordinate declared in the pack, distinct from the organism's root cell.
- **Recorded, not required:** whether the warehouse holds a *depletable stock* (see Enumeration note 4). The facet turns on existence + declared location + distinctness from the organism, not on depletability.
- **Surface (filled at verdict time):** —
- **Derivation:** Spec B2 *"toward a **food warehouse**"*.

### Facet B-F5 — **Spread**: occupancy propagates additively from occupied cells to adjacent cells over ticks

Growth, not movement: the mass accumulates.

- **Accepted evidence (leg b):** with **whatever growth surface the pack declares** — action, passive dynamic, cascade, effect, or a combination — reset and step N ticks, printing the occupied set at t=0, at intermediate ticks, and at t=N. All three assertions must hold and be pasted:
  1. **Growth:** `occupied_count(0) == 1` and `occupied_count(N) > occupied_count(0)`.
  2. **Adjacency:** for at least one recorded growth event, every newly occupied cell is adjacent to a cell occupied at the previous tick under the pack's declared distance metric — print the coordinate pair.
  3. **Accumulation (the separating check):** for every recorded tick, `occupied(t) ⊆ occupied(t+1)`. A cell that becomes unoccupied because the entity moved is **movement, not spreading**, and fails B-F5.
- **Surface (filled at verdict time):** —
- **Derivation:** Spec *"grows outward"* / *"must learn to **spread**"*; Stresses *"a **spreading** mass"*.

### Facet B-F6 — The spread is **directable by the policy**, so "toward food" is a choice the agent can learn

- **Accepted evidence (leg b):** from an identical reset state, the probe applies two different declared decisions (e.g. extend along +axis0 versus +axis3) and prints the two resulting occupied sets; **the sets differ**, and the difference corresponds to the chosen direction. That is, the frontier's growth direction is a function of the agent's action, not solely of a fixed passive rule.
  - Fails if growth is isotropic/passive with no action dependence — the agent then cannot "learn to spread **toward**" anything. Classify the failure under §6's decision tree (ABSENT if no direction surface exists at all; INERT if one declares and compiles but the two probes produce identical sets; BLOCKED if the declaration itself is loudly refused).
- **Surface (filled at verdict time):** —
- **Derivation:** Spec *"must **learn to spread toward** food"* — the verb chain requires the direction of growth to be under the policy's control.

### Facet B-F7 — Reaching the warehouse produces a **declared consequence** attributable to the organism

Without this there is no gradient and "toward food" is unlearnable.

- **Accepted evidence (leg b):** either of —
  - **Reward:** capture the reward vector from `env.step()` at the tick where the organism's extent first reaches (occupies or adjoins, per the pack's declaration) the warehouse cell, and assert a non-zero delta against a control tick where it does not. Paste both vectors.
  - **Meter:** a meter appearing in `inspect`'s `meter_names` changes on that tick; print its value immediately before and after.
- **Note for the comparer:** this probe is *shaped* like A.4's reward assertion but is **not** A.4's non-gating leg-(c) column. It is a §4 Spec-derived facet and it gates. One probe can serve both records.
- **Surface (filled at verdict time):** —
- **Derivation:** Spec *"must learn to spread **toward food**"* + *"a food warehouse"*.

### Facet B-F8 — **Observability**: the agent perceives, in the encoded observation, both its own extent and the warehouse's location

- **Accepted evidence (leg b),** all against the in-process `CompiledUniverse` and a stepped env (B.3 — `inspect` cannot supply any of this):
  1. `u.observation_spec.fields` contains a field bound to the organism's occupancy/extent state **and** a field bound to the warehouse's location; print each field's name, offset and width.
  2. `u.observation_activity.active_mask` shows those offsets **active** at the trial's primary level.
  3. Runtime: reset, grow, and read the observation tensor at those compiled offsets — the extent-bound values **change as the extent grows**, and the warehouse-bound values encode the declared warehouse coordinate.
  - `observation_dim` from `inspect --format json` is recorded for provenance only and is **not** sufficient evidence for this facet.
  - **Both components must hold.** Occupancy state that exists in the registry but is bound to no observation field means the agent cannot perceive its own body — the facet fails (the classic INERT/ABSENT split, resolved by §6's tree).
- **Surface (filled at verdict time):** —
- **Derivation:** B.2(iv), applied to Spec *"must learn to spread toward food"* — the state the agent must perceive to act on the mechanic is its own occupied-cell set (or frontier) and the food warehouse's position.

---

## A.4 pre-committed probe additions — **non-gating**, recorded beside the facets

A.4 is headed *(non-gating for this corpus)*. These are pre-committed here to satisfy A.4's
pre-commit requirement **without** entering any facet's accepted-evidence block. Nothing below can
fail the headline.

| # | check | applied to |
|---|---|---|
| N1 | **Double-reset**: after growth, re-run the B-F3 assertion block — the extent must return to the single declared root cell unless the pack declares persistence | B-F3 state |
| N2 | **Boundary cases**: growth into an already-occupied cell; growth at the 5-D grid boundary under the declared boundary mode; growth when the frontier is fully enclosed | B-F5 / B-F6 |
| N3 | **Obs-bounds loop**: every observation component within its declared normalization range across the probe run | B-F8 offsets |
| N4 | **Random-policy smoke**: ~5 episodes (or one reduced-`max_episodes` `DemoRunner` run): no exception, rewards finite and non-constant, episodes terminate | whole pack |
| N5 | **Reward-relevance note**: do the occupancy/extent variables appear in any reward component? "No" is a legitimate authoring choice and a fact the record states | B-F7 context |
| N6 | **N≥3 rule**: applies only if diagnostic B-D2 is explored — any cross-organism resolution probe carries ≥3 organisms | B-D2 only |

---

## Treatment of the diagnostic variants

The corpus scores idea B as **one entry on B2**. B1 and B3 therefore contribute **no gating
facets** and **no facet-count**. Gating on B3 would make the headline strictly harder than the
headline idea; gating on B1 would make it strictly easier. Both are carried as identified,
explicitly non-gating diagnostic rows so that B.1's third step can *map* them if the other run
enumerated them as facets, rather than logging them as unmapped facets and risking the
false-REJECT branch B.1 exists to close.

| ID | variant | status | what is recorded, and when |
|---|---|---|---|
| **B-D1** | B1 baseline — *"spread on a 2-D grid toward a static food source"* | **Diagnostic, non-gating** | Recorded **only if** a facet fails at 5-D: does the same facet hold on a 2-D grid? This isolates *"`gridnd`/5-D is the blocker"* from *"the set-extent entity is the blocker"* — the two Stresses. A B-D1 success **never** converts a B-F failure into headline credit. |
| **B-D2** | B3 contested — *"two organisms grow toward one food source"* | **Diagnostic, non-gating** | Explored **only if** all eight headline facets pass. Records whether a second organism instantiates with per-cell identity distinct from the first, and how contention over a cell resolves. If explored, N6 (N≥3) applies. Its absence never fails the headline. |

## Enumeration notes

1. **"Organism" and "set of occupied cells" are one facet, not two (B-F2).** The Stresses define the organism *as* the cell set (*"an entity that **is** a set of occupied cells"*), so splitting identity from extent would double-count one noun and yield 9. A splitter's extra facet maps cleanly onto B-F2 for the comparer.
2. **Agent count lives in B-F1, by B.2(iii)'s own wording** ("agent count, substrate, temporal mode"). This is deliberately where the corpus's predicted **group-of-agents workaround** is adjudicated, and B-F1's passing value is written as `1` *before* authoring precisely so that adjudication is not made at maximum-knowledge time. B-F2's union-of-positions exclusion is the second half of the same pre-commitment.
3. **Observability is one facet (B-F8), per B.2(iv)'s literal "one facet"** — though it carries two components (own extent, warehouse location). Both must hold for the facet to be demonstrated. A split into two would be defensible; it is not taken, for cardinality convergence.
4. **Ambiguity, flagged not resolved by fiat:** B2 says *"food **warehouse**"* where B1 says *"static food **source**"*. A warehouse plausibly implies a depletable stock. Because the corpus's own baseline tolerates a non-depleting source, B-F4 requires existence + declared 5-D location + distinctness only, and *records* depletability rather than gating on it. If the executor's reading differs, it is reconciled in a dated note before authoring (A.1), not after.
5. **B-F6 and B-F7 are Spec-derived, not Stresses-derived.** B.2 is a floor ("at minimum"), and §4 item 1 requires *every separable capability the Spec requires*. Without B-F6 the phrase *"must **learn** to spread **toward** food"* is untestable, and without B-F7 there is no signal to learn from.
6. **The facet set is stable under both readings of B.2(ii).** Whether *"the Stresses' decomposition"* means the literal Stresses verbs (*carries* / *spreading* / *is not*) or the Spec's verb chain (*rooted* / *grows outward* / *learn* / *spread toward*), the same four verb facets fall out: B-F3, B-F5, B-F6, B-F7. This is offered as the convergence argument for the cardinality of 8.
7. **Temporal mode adds no facet.** The premise needs only tick advancement so growth accumulates; no day/night mode is presupposed. Recorded in B-F1 so a second enumerator does not add a ninth facet for it.
8. **B.3 compliance audit of this list:** `inspect --format json` is relied on only in B-F1 (`substrate`, `action_count`) and B-F4 (`affordance_ids`, `meter_names`), and for a recorded-only `observation_dim` in B-F8. Every field/offset/scope/effect/population claim is pre-committed against the in-process `CompiledUniverse` or a stepped env. Note also B.3's warning that a green `compile` is not evidence an artifact on disk is fresh — prefer the in-process object.
9. **B.4:** every facet above carries a `Surface (filled at verdict time)` line. It is filled with the config file and construct the facet's verdict resolved through, one line per facet, at verdict time — this is what the A.8 comparison diffs.
10. **"Heavy PARTIAL" is not a protocol verdict class.** §1 gives a **binary** headline (PASS iff *every* facet is demonstrated on both legs; *"90%-authorable is FAIL"*) plus per-facet ABSENT / INERT / BLOCKED, and A.6 makes the idea count as INERT if any failing facet is INERT. The prediction's "heavy PARTIAL" must therefore be mapped by the executor onto PASS/FAIL plus the per-facet classes; it must not be recorded as a third headline outcome.

## §4 item 3 — the corpus's predicted verdict, copied verbatim

> **Predict: FAIL, or a heavy PARTIAL via a group-of-agents workaround.** If a workaround is the
> only path, that is itself the finding — the question is whether an *author* could reach it.

---

## Countersigner's non-contamination disclosure (verbatim)

> I opened only the two files I was given — `idea-B-corpus-entry.md` and `protocol-at-pin.md` —
> and opened no prohibited source: no file under `docs/product/trials/`, no
> `docs/product/decisions/`, no `metrics.md` / `roadmap.md` / `current-state.md`, no
> `configs/trial_*` directory, no git log or commit message, no `src/townlet/`, and not the live
> `docs/product/prds/0001-trial-protocol.md`. Engine facts used (substrate type names,
> action-count arithmetic, `CompiledUniverse` attribute names, the `positions` shape reference)
> came from the CLAUDE.md already in my context, from §6/B.3 of the pinned protocol, and from the
> corpus entry itself.

**Recorded by the dispatching agent:** the countersigner declined engine-source access entirely,
which A.1 permits ("no engine-source access required of it"). Its use of the ambient `CLAUDE.md`
is disclosed above and noted here rather than passed over silently; `CLAUDE.md` contains no idea-B
verdict, facet list, or trial outcome, so it is not a blinding leak.
