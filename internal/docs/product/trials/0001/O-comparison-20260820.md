# Trial O — blind re-run comparison            2026-08-20 · comparer (executed neither run)

Adjudicates PRD-0001 criterion 3 for corpus idea **O — Adversarial bidding**, comparing:

- **Run 1** — `docs/product/trials/0001/O-20260818.md`, standing agent, pin
  `a33186246da17d7ceb3fecdc15ebdfcb100a5f96` on `project-recovery-2`.
- **Run 2 (blind)** — `docs/product/trials/0001/O-blind-20260820.md`, fresh agent, worktree at the
  same pin, detached HEAD.

Governed by protocol §7 (blind re-run) as amended by A.8 (blind re-run governance). Neither trial
record was edited; this is a new file (A.5).

**Pre-brief received** (A.8 requires it be given to the comparer and only to the comparer): run 1's
facet 4 never exercised the tie case. Weighed in §2.4 below.

## 0. Method, and why checks run at HEAD are valid at the pin

Both packs are landed in the main tree: run 1's as `configs/trial_o_bidding/`, run 2's as
`configs/trial_o_bidding_blind/` (renamed on landing to avoid the collision — both records name
the pack `configs/trial_o_bidding/`).

I re-ran no trial. I did check specific engine claims where the two records could conflict or
where a record's load-bearing fact was worth confirming. Those checks ran at `HEAD`
(`30423381`), which is legitimate here because:

```
$ git diff --stat a3318624..HEAD -- src/townlet/
(empty — zero output)
```

The engine has not moved one line between the pin and HEAD. Every source read and probe below is
therefore a reading of the pinned substrate. Commands run are listed in §7.

**One scope note that shapes everything below.** §12's scope rule states that blind re-runs of the
four completed trials (L, F, M, O) "use the protocol text **as of the first run's pinned commit**
(i.e. without this appendix)." So Appendix A's *execution* rules — A.1 facet countersigning, A.2
search pre-registration, A.4 probe additions including the boundary-case and N≥3 rules — **did not
bind this blind executor.** A.8 is *comparison* governance and binds me by its own terms (it
pre-registers the pre-brief for exactly this run). Where the blind record volunteered A.2-shaped
and A.4-shaped rigor, that was executor-elective, not protocol-driven, and §5 below diagnoses it
accordingly. The blind record also cites a "§'one additional recording requirement'" that is not
in the pinned protocol text; recorded here neutrally so no reader mistakes it for protocol.

---

## 1. Headline verdict comparison

| | run 1 | run 2 (blind) |
|---|---|---|
| Corpus prediction | FAIL, ABSENT | FAIL, ABSENT |
| Leg (a) — zero `src/townlet/` diff | empty / empty | empty / empty |
| Facets enumerated | 6 | 8 |
| Facets passing both legs | 6 of 6 | 8 of 8 |
| **Headline** | **PASS** | **PASS** |
| Budget-limited | no | no |
| Prediction | falsified | falsified |
| Idea-level bucket (A.6 / A.6.1) | none — no failing facet | none — no failing facet |

**Headline: AGREE.** Both runs return PASS, both record zero engine diff, both record the corpus
prediction `FAIL, ABSENT` as falsified in the same direction and for substantially the same
reason — the effects command vocabulary (`for_each: all_agents` over global VFS scratch, ticking
engine-side after every agent's action) *is* a declarative clearing surface, reached only after
the obvious surface turned out to be unreachable.

---

## 2. Per-facet comparison

### 2.1 The mapping

The lists are different lengths and use different numbering, so the mapping is established first.
Run 1 enumerated six facets from the Stresses' four-step clearing decomposition plus bid
declaration and observability. Run 2 enumerated eight, deriving O1–O2 from the Spec's *nouns*
("agents … against each other", "a contested item") and O3–O7 from the Stresses' verbs, with
"collect" split in two, plus O8 for observability.

| run 1 facet | run 2 facet | basis for the mapping | correspondence |
|---|---|---|---|
| — | **O1** Multi-agent contention (≥2 agents in one world) | no run-1 counterpart | **blind-only** |
| — | **O2** A contested item (single indivisible good, one holder) | no run-1 counterpart | **blind-only** |
| **1** Bid declaration — an agent action records a per-agent bid amount | **O3** Agent-chosen bid amount | both: an agent action writes a per-agent bid value; both require two distinct selectable levels | **mapped** |
| **2** Simultaneous collection — both bids live in one window, no first-come ordering | **O4** Simultaneous collection — all bids collected before any award | near-verbatim same facet; both accept a both-orderings swap test | **mapped** |
| **3** Clearing: highest bid wins — a declared surface compares across agents | **O5** Clearing comparison (highest-value rule) — declared cross-agent max | both: the max must be computed by a declared config surface, not by the probe | **mapped** |
| **4** Award — the contested thing goes to the winner only | **O6** Award to the highest bidder — exactly one agent, the argmax bidder | both: winner's award state set, loser's not | **mapped** |
| **5** Charge — the winner pays their bid; losers pay nothing | **O7** Charge the winner — winner's money down by the bid, losers unchanged | verbatim same facet | **mapped** |
| **6** Observability — bid state and/or outcome in the encoded observation | **O8** The contest is observable — won-state and clearing price at the compiled offset | both: compiled observation field plus a runtime read at the offset | **mapped** |

**Six mapped pairs. Two blind-only facets. Zero run-1 facets without a blind counterpart** — the
blind list is a strict superset of the run-1 list at the capability level.

### 2.2 Verdicts and classifications on the mapped pairs

| pair | run 1 result / class | run 2 result / class | agree? |
|---|---|---|---|
| 1 ↔ O3 | PASS / — | PASS / — | ✅ |
| 2 ↔ O4 | PASS / — | PASS / — | ✅ |
| 3 ↔ O5 | PASS / — | PASS / — | ✅ |
| 4 ↔ O6 | PASS / — | PASS / — | ✅ |
| 5 ↔ O7 | PASS / — | PASS / — | ✅ |
| 6 ↔ O8 | PASS / — | PASS / — | ✅ |

**6 mapped pairs agreed, 0 differed.** No facet in either record carries a classification: §6
defines ABSENT/INERT/BLOCKED as a per-*failing*-facet operation, and neither run has a failing
facet. The compared set is `{PASS, —} × 6` against `{PASS, —} × 8`; **no classification conflict
is constructible.**

### 2.3 The two blind-only facets

| facet | run 2 result | does run 1's pack satisfy it? |
|---|---|---|
| **O1** Multi-agent contention | PASS (`population.size: 3`, meters `(3, 4)`) | **Yes, implicitly.** `configs/trial_o_bidding/levels/L0_auction/training.yaml` declares `population: size: 2`; run 1's probe drove agents 0 and 1 in one world. Never enumerated, but satisfied. |
| **O2** A contested item | PASS (global `prize_available` + `prize_holder` single holder index; the `items.yaml`/`spawn_item` route was found BLOCKED — G-3) | **No.** Run 1 modelled the award as a per-agent `wins` counter incremented inside the `for_each`. A per-agent counter is exactly the "per-agent copy" O2's accepted evidence excludes. There is no single indivisible good in run 1's pack. |

O2 is the one genuine content gap between the lists, and §2.4 settles what it does and does not
mean.

### 2.4 The two adversarial readings, answered

A reviewer will press on the tie and on O2. Both are pre-answered here.

**(a) The tie case (the A.8 pre-brief).** Run 1's facet 4 was evidenced at 0.3-vs-0.1 only. I
confirmed the mechanism directly from `configs/trial_o_bidding/effects.yaml`: the award branch is
`if: "target.bar.bid >= vfs.highest_bid"` inside `for_each: all_agents` with **no uniqueness
guard**, so on equal maximum bids every tied bidder gets `wins += 1` and is charged — as run 1's
own post-verdict note records. Run 2 tested the tie explicitly (ROUND 4) and its pack awards
exactly once, uniqueness enforced declaratively by the `auction_awarded` / `prize_available`
guards in the award condition.

This is **a difference in evidence depth, not a difference in verdict**, on three independent
grounds:

1. §4 makes the accepted-evidence entry binding and immutable; facet 4's binding standard is the
   0.3/0.1 check it pre-committed, and that check passed. Classification applies only to failing
   facets (§6); facet 4 did not fail its own standard.
2. §12's scope rule explicitly forbids re-scoring L/F/M/O under the appendix, and the
   boundary-case rule that would have required a tie probe is A.4 — prospective, trials five
   onward. Re-scoring run 1's facet 4 on A.4 would breach the protocol's own scope rule.
3. **The counterfactual, which is the load-bearing part.** Had run 1 pre-committed a tie check,
   its pack as authored would have failed it — but run 2 demonstrates at the *identical substrate*
   that a single-winner guard is declarable in config alone. Run 1's executor would have amended
   its pack (pack editing is the trial) and PASSed. So the stricter standard changes the pack, not
   the idea-level verdict.

**(b) O2 unmapped.** Same shape. Run 2 PASSed O2 at the same pin using a surface available to run
1 (`vfs_profiles.yaml` global profile — run 1 already used exactly that file for `highest_bid` and
`auction_timer`). So run 1's omission conceals no latent FAIL.

Stated once, plainly: **the union of both facet lists is all-PASS and evidenced — six facets by
run 1, eight by run 2, with O2 and the tie case both settled PASS by run 2 at the byte-identical
substrate.** No facet enumerated by either executor is un-demonstrated at the pin.

---

## 3. Surface-path comparison (A.8, mandatory)

A.8: *"same headline via a different surface is recorded as a search-dependence finding even when
verdicts agree."* Six mapped pairs agreed on verdict. **Four of the six resolved through
materially different declarative surfaces.** This section is the most valuable output of the
exercise and is not compressed.

The mechanical root of most of the divergence, established by reading both packs:
`configs/trial_o_bidding/vfs_profiles.yaml` declares **`agent_profile: null`** — run 1 carried
every per-agent auction quantity as a **bar/meter**. `configs/trial_o_bidding_blind/vfs_profiles.yaml`
declares a real **`agent_profile:`** — run 2 carried them as **agent-scoped VFS variables**. One
authoring choice at the state-substrate level propagated into four of the six facets and into an
entire class of tooling defects that run 1 could not have hit.

### 3.1 Per-mapped-facet surface paths

| pair | run 1's winning surface | run 2's winning surface | same? | finding |
|---|---|---|---|---|
| 1 ↔ O3 | affordance `interactions.on_start` → `modify: target.bar.bid` (**bar/meter**), BID_HIGH 0.3 / BID_LOW 0.1 | affordance `interactions.on_start` → `modify: target.vfs.bid` (**agent-profile VFS var**), BID_HIGH 3.0 / BID_LOW 1.0 | family same, **substrate different** | **SD-1** |
| 2 ↔ O4 | a **declared 3-tick auction window** (`vfs.auction_timer` counter gating the clearing branch): bids coexist until the window closes | **no window** — relies on the engine ordering fact that `EffectManager.tick()` runs after `_execute_actions` in the same `step()` | **different mechanism** | **SD-2** |
| 3 ↔ O5 | `for_each: all_agents` + global VFS scratch, running max spelled as `if target.bar.bid > vfs.highest_bid then modify` | `for_each: all_agents` + global VFS scratch, running max spelled as `modify: vfs.clearing_price value: "max(vfs.clearing_price, target.vfs.bid)"` | **same load-bearing surface**, different spelling | **SD-3** |
| 4 ↔ O6 | per-agent `bar.wins += 1` inside the loop; the winner is never *named* in world state, so no index is needed | global `vfs.prize_holder` single index, obtained via a hand-rolled **scan-counter idiom** (`vfs.scan_index`) because `for_each` binds no iterator symbol | **different surface, materially harder** | **SD-5** |
| 5 ↔ O7 | `modify: target.bar.credits value: "target.bar.credits - target.bar.bid"` — a custom `credits` bar, charged the agent's own bid | `modify: target.bar.money value: "target.bar.money - vfs.clearing_price"` — the shipped `money` bar, charged the clearing price | family same, **referent different** | **SD-6** |
| 6 ↔ O8 | **bars pipeline**: meters compile to `obs_meter_bid` (31), `obs_meter_wins` (32), `obs_meter_credits` (33); global `highest_bid` (61) | **VFS-profile pipeline**: global and agent profile variables compile to their own custom observation fields `[134:142]`; found in a `GlobalVFSVariableConfig` **docstring** | **different pipeline** | **SD-7** |

### 3.2 SD-3 — the reproducibility result

Two executors who never communicated, starting from different base packs, with different facet
lists and different state substrates, both converged on **the same load-bearing surface**:
an effect whose `on_tick` iterates the `all_agents` collection, accumulating a running maximum
into global VFS scratch, then branching on it to award and charge. Both reached it *second*, after
the obvious surface failed. Both independently recorded that `all_agents` is undocumented — run 2
files it as a doc defect (G-8); run 1 records finding it by reading
`src/townlet/effects/collections.py`.

This convergence is what makes the "no" in §4 defensible rather than lucky. If the two runs had
agreed on PASS through wholly unrelated surfaces, the agreement would be an artifact of the idea
being over-determined. It is not: the idea has exactly one working surface at this pin, both
executors found it, and both found it only by reading source.

### 3.3 SD-7 — the finding that most damages a metric the project intends to publish

The same facet — observability — reads, in run 1, as the *free* consequence of using meters: bars
compile to observation fields through the documented bars pipeline, and run 1's record shows no
search cost at all for facet 6. In run 2 the same facet is annotated
**"source-reading-required"**, found in a docstring on `GlobalVFSVariableConfig`, with run 2
explicitly noting "nothing in `docs/config-schemas/` says so."

Same capability, same engine, same commit. The discovery path differed because the *pack design
choice made three facets earlier* (bars vs VFS variables) determined which pipeline had to carry
the observation.

**Conclusion: discovery path is a property of the (executor, pack-design) pair, not of the
facet.** That is a finding about the instrument. A.3 makes discovery-path annotation a recorded
column and directs it to be "derived retroactively for L/F/M/O from their authoring logs" as the
data for a prospective novice-authorability row in `metrics.md`. This comparison is direct
evidence that such a derived number would not mean what the metrics row will claim it means: it
measures the authoring route the executor happened to take, and a second competent executor
produced a different reading for the same facet at the same commit. A.3 is marked *(non-gating)*,
so nothing is invalidated — but the construct needs a caveat before any reading publishes.

### 3.4 The remaining search-dependence findings

**SD-1 — state substrate (bars vs agent-profile VFS variables).** Beyond being a different
surface, this choice had a consequence run 1 could not have encountered: declaring an
`agent_profile:` breaks the compiled-artifact cache. I reproduced this on clean copies of both
packs (§7): run 1's pack writes `universe-L0_auction.msgpack` and `inspect` works; run 2's pack
prints "Compilation succeeded", exits 0, and leaves `.compiled/` **empty**. Run 2 filed this as
G-2 (BLOCKED, tooling). It is a genuine engine defect, and run 1's inability to find it is a
direct consequence of a state-substrate choice made for unrelated reasons.

**SD-2 — simultaneity by declaration vs by engine ordering.** Run 1 *declares* the simultaneity it
claims: a 3-tick window inside which bids coexist. Run 2 does not declare it; it establishes it by
reading `vectorized_env.py` and showing that `_execute_actions` (line 1016) precedes
`effect_manager.tick` (line 1035) — verified, the claim is correct. Both PASS, but the
epistemic basis differs: run 1's PASS survives a change to engine phase ordering; run 2's does
not. A protocol that compares only classifications cannot see this distinction.

**SD-4 — opposite authoring responses to the same INERT surface.** Both executors independently
found that `EffectDefinition.scope: global` validates, compiles, and is silently spawned
agent-scoped (`_execute_spawn_effect` hardcodes `scope=EffectScope.AGENT`; verified, with the
in-source comment "scope hardcoded to AGENT for now"). Their responses were **opposite**: run 1
declared its effect `scope: agent` with a comment recording the wart; run 2 declared `scope:
global` anyway and recorded that the declared global phase is an emulation. Same defect, same
INERT classification, contrary authoring choices — and run 2's pack now contains a declaration
that does nothing, which is exactly the shape the INERT class exists to flag.

**SD-5 — the award representation, and the ABSENT gap it exposed.** Run 1 never needed to name
*which* agent won, because `target.*` is rebound per iteration and the counter lives on the agent.
Run 2's stricter O2 required a single holder index in world state, which required the index of the
element being examined, which `for_each` does not bind — forcing a hand-rolled scan counter and
producing gap G-4 (ABSENT). Run 1 could not have found G-4. This is the clearest case in the
comparison of **facet granularity determining which engine gaps are discoverable at all.**

**SD-6 — charge referent.** `credits` (a custom bar) vs `money` (the shipped bar); own bid vs
clearing price. Identical in a first-price auction, and both PASS. Worth recording because run 1's
own post-verdict note flags that `credits - bid` clamps at the bar floor, producing a degenerate
zero-credit perpetual winner. Run 2 did not probe its `money` bar at the floor, so whether the
same degeneracy exists in its pack is untested by either run.

**SD-8 — both runs abandoned the same pre-committed artifact probe, for different reasons.** Both
records pre-committed leg-(b) evidence naming `inspect --format json`; both abandoned it; both
substituted the in-process `CompiledUniverse`. Run 1: the command works but under-reports. Run 2:
the command fails outright (G-2). Convergent workaround, divergent trigger. §6.1 records the
factual refinement this exposes.

**SD-9 — base pack and agent count.** Run 1 copied `configs/trial_m_combo` (`population.size: 2`);
run 2 copied `configs/L5_multi_agent` (`population.size: 3`), chosen *because* it enumerated O1.
Run 2 therefore satisfied A.4's N≥3 rule, which did not bind it, while run 1 ran the N=2 case A.4
warns "hides ordering and aggregation bugs". Neither run's verdict turns on this; it is recorded
because facet enumeration drove base-pack choice drove probe strength.

### 3.5 Gap-classification convergence (not compared by §7 — recorded because it is the strongest available evidence on the classification vocabulary)

§7 compares per-facet classifications, and there are none. The two records *do* both carry a gaps
table classified in the same ABSENT/INERT/BLOCKED vocabulary, and comparing those is the only way
to test whether two executors apply that vocabulary the same way.

| gap | run 1 | run 2 | agree? |
|---|---|---|---|
| `scope: global` on an effect validates and is silently agent-scoped | **INERT** (`hamlet-4cd664a955`) | **INERT** (G-6) | ✅ exact, same function |
| No declarative path to a standing world process; clearing must be ignited by an agent action | **ABSENT** (`hamlet-77e4f8b3e3`) | **ABSENT** (G-7) | ✅ exact |
| VTC clearing vocabulary (`composition: max`) unreachable from config | not found | **ABSENT** (G-1) | blind-only |
| `agent_profile` breaks the artifact cache; `compile` still exits 0 | not reachable | **BLOCKED** (G-2) | blind-only |
| `spawn_item` cannot run from any effect `on_tick` | not reached | **BLOCKED** (G-3) | blind-only |
| `for_each` binds no iterator symbol | not reached | **ABSENT** (G-4) | blind-only |
| `reduce` cannot range over agents | not reached | **BLOCKED** (G-5) | blind-only |
| `effects.md` teaches `global.vfs.*`, omits `all_agents` | partially noted in the log | **doc defect** (G-8) | blind-only |

**Both gaps run 1 found were independently rediscovered by run 2 with identical classifications.**
Run 2 found six more; run 1 found none run 2 missed. The by-catch INERT surface count (A.7) is
**1 in both records, and it is the same surface**. On the only two data points where the two
executors classified the same defect, the vocabulary reproduced exactly.

The blind run's gap set being 4× larger is not a protocol failure — it is the expected
consequence of a longer facet list (SD-5), a different state substrate (SD-1), and one executor
electing to probe surfaces (`items.yaml`, `reduce`, VTC writes) the other never needed.

---

## 4. The §7 call

> **Does §7's reject branch fire? — NO.**

§7 compares exactly two things: **"headline verdict and per-facet classifications."**

- **Headline verdict:** PASS in run 1, PASS in run 2. Identical.
- **Per-facet classifications:** classification is defined by §6 as an operation on *failing*
  facets. Neither run has a failing facet. Every entry in both facet tables is result PASS,
  classification `—`. No conflict exists to find.

The instrument is **ACCEPTED** on criterion 3 for idea O. A north-star reading is not blocked by
this comparison.

**What differs, and why §7 does not name it.** Four differences are real and are recorded above:
facet cardinality (6 vs 8), evidence depth (the tie case), base pack (`trial_m_combo` N=2 vs
`L5_multi_agent` N=3), and surface path (four of six mapped pairs). §7 names none of these. A.8
names surface path explicitly and directs it to be recorded as a finding *"even when verdicts
agree"* — i.e. A.8 treats a differing surface as reportable data, not as a disagreement, and it
leaves §7's reject branch "UNCHANGED". A difference §7 does not name is not automatically a
disagreement.

**And, equally, no real classification conflict is being waved away.** The two candidates for one
were examined at length in §2.4 rather than dismissed: the tie case does not convert to a
classification conflict because facet 4's binding standard is its own immutable pre-commitment,
§12 forbids re-scoring it under A.4, and run 2 proves the capability declarable anyway; O2 does
not, because run 2 PASSed it at the identical substrate. Had either counterfactual gone the other
way — had run 2 found O2 ABSENT, or had a tie probe established a capability that is not
declarable — the branch would fire, and I would be recording that instead.

The honest weakness in this "no" is that agreement between two all-PASS records is cheap: with
zero failing facets, the classification comparison is vacuous by construction, and §7's
discriminating power was never exercised on this idea. The substantive reproducibility evidence is
elsewhere and is real — SD-3's convergence on the single working surface, and §3.5's exact
agreement on both classified gaps. Those, not the vacuous table in §2.2, are what the "no" rests
on.

---

## 5. Diagnosis: protocol ambiguity vs search variance

A.8: the diagnosis "informs what is rebuilt, not whether the branch fires."

| # | difference | diagnosis | reasoning |
|---|---|---|---|
| D1 | Facet cardinality 6 vs 8 | **protocol ambiguity** | §4 says "every separable capability the Spec requires" and gives no granularity rule, no derivation requirement, and no worked mapping from Spec text to facet count. Two competent executors read the same two sentences and produced 6 and 8. Run 2 volunteered a derivation note; §4 does not ask for one. |
| D2 | O2 ("a contested item") absent from run 1 | **protocol ambiguity** (special case of D1) | The Spec's noun *is* a capability under run 2's noun-extraction rule and was folded into "award" by run 1. Nothing in §4 says whether Spec nouns generate facets. |
| D3 | Tie case probed by run 2, not run 1 | **protocol ambiguity at the pin, already self-corrected** | The pinned protocol contains no boundary-case requirement. A.4's boundary-case rule closes it prospectively. This comparison is empirical confirmation that the amendment was necessary: two packs with materially different tie semantics both scored PASS on the same facet. |
| D4 | Base pack and agent count (N=2 vs N=3) | **protocol ambiguity, mild** | §5 permits any copy source and §4 never requires the pack to satisfy the idea's own premise (here: multi-agent). Run 2 arrived at N=3 only because it enumerated O1. Downstream of D1. |
| D5 | Surface path on pairs 1↔O3, 2↔O4, 4↔O6, 6↔O8 | **search variance** | Both surfaces exist, both are legitimate, the protocol is not underspecified about which to prefer, and §5 explicitly permits reading anything. This is the instrument working as designed: it measures whether *a* surface exists, not which one is found. |
| D6 | Gap set size 2 vs 8 | **search variance**, downstream of D1/D5 | Longer facet list and a different state substrate exposed more engine surface. No classification conflict on the overlap. |
| D7 | `inspect --format json` pre-committed by both and executable by neither | **protocol ambiguity / protocol defect** | §4's own worked example and §6's standard-probe list name a command that structurally cannot supply the evidence they describe. It reproduced across two independent executors — that is the signature of a protocol defect, not executor error. |
| D8 | Run 2 applied A.2/A.4-shaped rigor that did not bind it | **neither — recorded for accuracy** | §12 scopes the appendix away from this run. Run 2's search pre-registration, tie probe and N≥3 case were elective. A future comparer must not read this run's extra rigor as evidence that the pinned protocol produces it. |

---

## 6. What the protocol should say that it does not

Four amendments, each earned by a difference above. **Proposed text only — not applied.**

### AM-1 (sharpest). §7 × A.1 precedence, and how a comparison handles unmapped facets

The single most dangerous thing this comparison found is not in either record: **A.1 and §7 give
contradictory instructions for a blind re-run of trials five onward, and nothing resolves them.**
A.1 requires the facet list to be enumerated by a non-executing party and adopted by the executor.
§7 requires the blind executor never to open a prior record. If a blind re-run *inherits* the
first run's countersigned list, the pre-commitment step — the very step where this comparison
found its largest divergence — is no longer independently reproduced, and the re-run tests only
authoring, not enumeration. If it gets its own independently countersigned list, cardinality
diverges again exactly as it did here. A.1 does not fix D1; it *suppresses* D1 by single-sourcing
the list, which is not the same thing. A.8 is silent. This did not bind the present run only
because §12 scopes the appendix away from L/F/M/O — it will bind the second blind re-run if that
re-run is of trial five or later.

> **Proposed, §7, new bullet:**
> "A blind re-run enumerates its own facet list under §4, independently. It never inherits the
> first run's facet list, and its A.1 countersigner must not have seen that list. Where §7's
> blinding requirement and A.1's single-list requirement conflict, blinding wins: the point of the
> re-run is to test whether the protocol reproduces the *enumeration* as well as the authoring."
>
> **Proposed, §7, replacing "then a third step compares headline verdict and per-facet
> classifications":**
> "then a third step (a) establishes an explicit mapping between the two facet lists, naming every
> mapped pair, every blind-only facet and every first-run-only facet; (b) compares headline verdict
> and per-facet classification on the mapped pairs; and (c) for each unmapped facet, states whether
> the other run's pack satisfies it and whether the capability was demonstrated declarable at the
> same pin by either run. **Facet cardinality alone never fires the reject branch.** An unmapped
> facet that neither run demonstrated declarable at the pin *is* a disagreement and fires it."

### AM-2. §4 — a facet-granularity rule, so independent enumeration converges

Without this, AM-1's independent enumeration reproduces D1 every time.

> **Proposed, §4, inserted before the numbered list:**
> "Facet granularity is not at the executor's discretion. Enumerate, at minimum:
> (i) one facet per **entity noun** in the Spec that the mechanic must instantiate in world state
> (idea O's 'a contested item' is one facet, distinct from awarding it);
> (ii) one facet per **verb** in the Stresses' decomposition;
> (iii) one facet for the **environment premise** the idea presupposes (agent count, substrate,
> temporal mode) — and the trial pack must satisfy that premise, not merely tolerate it;
> (iv) one facet for **observability** of the state the agent must perceive to act on the mechanic.
> Write a derivation note mapping each facet to the Spec/Stresses text it came from. Two executors
> enumerating the same idea should produce the same count; a differing count is a defect in this
> section, reported by the comparer."

### AM-3. §6 — correct the standard artifact probe, which cannot do what §4's own example claims

Verified against source and by execution (§7 below): `inspect --format json` emits
`UniverseMetadata` plus five hashes. It reports `meter_names`, `affordance_ids`, `action_count` and
a scalar `observation_dim`. It reports **no** observation-field enumeration, **no** offsets, **no**
scopes, **no** effect catalog, and **no** population/agent count. §4's worked example —
*"`inspect --format json` shows an observation field for the wear variable"* — describes an output
the command cannot produce. Both O executors pre-committed evidence against it; both had to
abandon it; both substituted the in-process `CompiledUniverse`. This is also a live risk to
trial F, whose idea *is* the worked example.

> **Proposed, §6 "Standard probes", replacing the artifact bullet:**
> "artifact: `... inspect ... --format json` reports **only** `UniverseMetadata` (universe/level
> names, substrate, `meter_names`, `affordance_ids`, `action_count`, a scalar `observation_dim`,
> provenance) plus five schema hashes. It does **not** enumerate observation fields, offsets,
> variable scopes, effects, VFS profiles or population size. Evidence naming any of those must be
> pre-committed against the in-process `CompiledUniverse` — `u.observation_spec.fields`,
> `u.observation_activity.active_mask`, `u.compiled_effect_catalog` — which is the same object
> `inspect` serialises. §4's worked example is corrected to name the compiled artifact directly.
> Note also that `compile` reports 'Compilation succeeded' and exits 0 when the cache write fails,
> and the CLI's 'Cache artifact written to' line is gated on the path existing rather than on the
> write — so a green `compile` is not evidence that `inspect` will work, or that an artifact on
> disk is fresh."

### AM-4. §7 — record the surface path in the trial record, not only in the comparison

A.8 requires the *comparison* to record surface paths, but a comparer can only recover them from
whatever the authoring log happened to mention. Recovering SD-1 through SD-7 here required reading
both packs' YAML directly, because neither record tabulates its surfaces per facet (run 2's
discovery-path table came closest; run 1 has none). A comparer working from records alone would
have missed most of §3.

> **Proposed, §4, added as item 4:**
> "4. A per-facet **surface column**, filled in at verdict time: the config file and construct the
> facet's verdict resolved through (e.g. `effects.yaml` / `for_each: all_agents`; `vfs_profiles.yaml`
> / `agent_profile`; `bars.yaml` / meter). One line per facet. This is what a blind-re-run
> comparison diffs under A.8, and it cannot be reconstructed reliably from an authoring log."

### Two minor items, not numbered amendments

- **A.4's boundary-case rule is empirically confirmed necessary.** D3 shows two packs with
  materially different tie semantics both scoring PASS on the same facet at the same commit. No
  change proposed — recording that the amendment already made was the right one, and that its
  *(non-gating)* status is the reason this comparison did not have to adjudicate it.
- **Blind pack naming.** Both runs authored at `configs/trial_o_bidding/` and the collision had to
  be resolved on landing. §7 should say the blind run's pack is authored at
  `configs/trial_<x>_blind_<slug>/`.

### 6.1 Factual refinement to the blind record (recorded here; that record is not edited)

Run 2 attributes its inability to run `inspect --format json` entirely to G-2 (the `agent_profile`
cache-serialisation defect). That attribution is correct but **incomplete**. Even with a working
artifact, `inspect --format json` could not have satisfied either pre-committed check: O1 named it
for "the pack's population/agent count" and O8 for "an observation field for the auction
variable(s)", and the payload contains neither. Verified by dumping the payload for run 1's pack,
which *does* cache successfully:

```
TOP KEYS: ['action_schema_hash', 'artifact', 'metadata', 'observation_schema_hash',
           'transition_graph_hash', 'variable_schema_hash', 'vfs_hash']
observation_dim: 63          (a scalar)
meter_names: ['energy', 'health', 'bid', 'wins', 'credits']
population/agent count key present? []
any field/offset/effect enumeration? []
```

So G-2 and the `inspect` shortfall are two independent defects that happened to land on the same
command. Run 1's honesty note — that `inspect --format json` "emits a hash/metadata summary only
(meters `bid`/`wins`/`credits` appear in its `meter_names`; it does not enumerate fields or
effects)" — is **exactly correct**, and is the better description of the underlying defect. The
two records do not contradict each other; run 2's is narrower than the fact warrants.

---

## 7. Checks I ran (I re-ran neither trial)

All at `HEAD` = `30423381`, valid at the pin because `git diff --stat a3318624..HEAD -- src/townlet/`
is empty. Packs were copied to a scratchpad before compiling, so no `.compiled/` artifact was
written into the working tree.

| # | check | result |
|---|---|---|
| C1 | `git diff --stat a3318624..HEAD -- src/townlet/` | empty — zero engine drift between pin and HEAD |
| C2 | `src/townlet/effects/executor.py` `_execute_spawn_effect` | `scope=EffectScope.AGENT` hardcoded, with the in-source comment "scope hardcoded to AGENT for now". Both records' INERT finding confirmed; run 1 cites :228-231, run 2 cites :222 — same block, not a conflict |
| C3 | `src/townlet/environment/vectorized_env.py` step ordering | `_execute_actions` at :1016 precedes `effect_manager.tick` at :1035. Run 2's O4 basis confirmed |
| C4 | `src/townlet/universe/compiler.py:545-552`, `__main__.py:100-103` | bare `except Exception` + `logger.warning` around `save_to_cache`; CLI success line gated on `cache_path.exists()`. Run 2's G-2 mechanism confirmed |
| C5 | `compile` on clean copies of both packs | run 1's pack (`agent_profile: null`) writes `universe-L0_auction.msgpack`; run 2's pack (real `agent_profile`) prints "Compilation succeeded", exits 0, leaves `.compiled/` **empty**. G-2 reproduced, and its cause confirmed as the state-substrate choice |
| C6 | `inspect --format json` payload on run 1's pack + `UniverseMetadata` dataclass | metadata + 5 hashes; no field/offset/effect/population enumeration. §6.1 |
| C7 | `configs/trial_o_bidding/effects.yaml` award branch | `target.bar.bid >= vfs.highest_bid` in `for_each: all_agents`, no uniqueness guard → ties award and charge every tied bidder. Pre-brief confirmed at the source |
| C8 | `configs/trial_o_bidding_blind/effects.yaml` award branch | `... and vfs.auction_awarded < 0.5 and vfs.prize_available > 0.5` → single winner enforced declaratively. Run 2's tie result confirmed at the source |
| C9 | both packs' `vfs_profiles.yaml` and `training.yaml` | `agent_profile: null` / `size: 2` vs real `agent_profile` / `size: 3`. Roots SD-1 and SD-9 |

## 8. Summary

**Read the verdict table with §4's caveat attached.** Agreement between two all-PASS records is
cheap: with zero failing facets in either run, the classification comparison §7 specifies is
vacuous by construction, and §7's discriminating power was never exercised on this idea. The "no"
below does **not** rest on the six all-`—` rows in §2.2. It rests on two things that could have
come out otherwise and did not: **SD-3**, two non-communicating executors converging on the single
working surface for the clearing step, and **§3.5**, exact agreement on the ABSENT/INERT
classification of both defects that both runs found.

| question | answer |
|---|---|
| Headline verdict | **AGREE** — PASS / PASS |
| Mapped facet pairs | 6 |
| Mapped pairs agreeing on verdict **and** classification | **6 of 6** |
| Mapped pairs differing | **0** |
| Blind-only facets | 2 (O1 satisfied implicitly by run 1's pack; O2 not satisfied, but PASSed by run 2 at the same pin) |
| Run-1-only facets | 0 |
| Mapped pairs reached via a *different* declarative surface | **4 of 6** (SD-1, SD-2, SD-5, SD-7) |
| Gaps classified by both runs | 2, agreeing exactly (INERT, ABSENT) |
| A.7 by-catch INERT surface count | 1 in each record — the same surface |
| **§7 reject branch** | **does NOT fire** |
| Instrument status for idea O, criterion 3 | **ACCEPTED** |

---

## 9. Addendum by the standing product agent, 2026-08-20 (NOT the comparer)

Added after the comparer's document was accepted and after the owner adopted its four amendments
as protocol **Appendix B**. Everything above this line is the comparer's and is unedited. This
section exists so the trial-record corpus is self-contained for an auditor working without git
history — four facts below currently live only in commit messages and tracker tickets.

### 9.1 Does O's own verdict survive B.1? — YES, and the check is not circular

The comparison passed under the old §7 and the amendment was adopted immediately afterwards. A
skeptical reader should ask whether the amended rule, applied to this very comparison, would still
return "does not fire". Checked explicitly rather than assumed:

B.1's new trigger is *"an unmapped facet that **neither** run demonstrated declarable at the pin
IS a disagreement and fires it."* The two unmapped facets are both blind-only:

- **O1** (multi-agent contention) — run 1's pack satisfies it implicitly (`population.size: 2`).
  Demonstrated by run 1. Does not fire.
- **O2** (a contested item, indivisible, single holder) — run 1's pack does **not** satisfy it;
  run 1 modelled the award as a per-agent `wins` counter, which is the per-agent copy O2 excludes.
  But run 2 **PASSed O2 at the identical pin**. So it is not the case that *neither* run
  demonstrated it declarable. Does not fire.

**O's verdict stands unchanged under B.1.** Had run 2 found O2 ABSENT, B.1 would fire where the old
§7 did not — which is the point of the amendment, and evidence it was written to catch a real case
rather than to ratify this one.

### 9.2 Provenance of the two killed suite runs (the blind record cannot be edited)

The blind record reports two full-suite re-runs *"killed by the machine (exit 144 / 143) ...
unrelated pytest running concurrently"*. That was not the machine, and the concurrent pytest was
not unrelated: **the standing agent killed those runs from the parent session**, deliberately,
because the blind executor had finished and its orphaned run in the scratch worktree was competing
for the GPU with the main-tree suite required for the §10 commit guardrail. The blind executor
could not have known this and its caution was correct on the evidence it had.

Superseding measurement, main tree, blind pack present:
**3281 passed, 16 skipped, 0 failed, exit 0** (1210.02s), plus `validate` exit 0 on the pack.

### 9.3 Two blind-record claims NOT adopted into tracker filings

Both were checked at HEAD and did not reproduce as stated. The blind record is not edited; the
filings simply exclude them, and say so.

1. **"`CustomActionConfig` forbids a `writes` key."** There is no `CustomActionConfig` in
   `src/townlet/environment/action_config.py` (the classes are `ActionConfig` and
   `ActionSpaceConfig`), and `writes: list[WriteSpec]` is **present** at `action_config.py:84`
   rather than forbidden. The substantive finding survives and is what `hamlet-3381043d2e` carries:
   `compilers/actions.py:205` hardcodes `writes=()`, and no `WriteSpec` is constructed anywhere
   under `src/townlet/` outside its own class definition and two docstrings.
2. **"`effects.md` teaches `global.vfs.*`, which raises `Invalid path`."**
   `world/expression/context.py:65-68` **does** resolve a `global` root and dispatches to
   `_resolve_vfs_chain(..., scope="global")`, so the path form is not categorically invalid. The
   omission half of that gap is verified and filed (`hamlet-7eadeb214c`); the raise half is not.

### 9.4 B.3's mandated replacement probe was verified executable before adoption

B.3 removes an unexecutable probe from §6 and mandates three `CompiledUniverse` attributes in its
place. Adopting those names on the comparer's word would have reintroduced the exact defect B.3
exists to remove, one paragraph later. Measured at HEAD against
`configs/default_curriculum` / `L1_full_observability`:

| mandated by B.3 | resolves |
|---|---|
| `u.observation_spec` | yes |
| `u.observation_spec.fields` | yes |
| `u.observation_activity` | yes |
| `u.observation_activity.active_mask` | yes |
| `u.compiled_effect_catalog` | yes |

`observation_spec` also carries `total_dims`, `get_field_by_name`, `get_fields_by_feature` and
`get_fields_by_semantic_type`. B.3 stands as written; no correction needed.

### 9.5 Criterion 3 is HALF met — the discriminating re-run has not run

Stated here because §8's row *"Instrument status for idea O, criterion 3: ACCEPTED"* is easy to
read as "criterion 3 is met". It is not. Criterion 3 requires **2 of 9** re-run blind. One has run.
And by this document's own §8 caveat, the one that ran was the **cheap** one: two all-PASS records
make the classification comparison vacuous by construction. **Idea B is the discriminating re-run**
— a FAIL carrying BLOCKED facets, so it is the first re-run that will actually exercise the
ABSENT/INERT/BLOCKED comparison the reject branch turns on. No north-star reading publishes until
it has run and agreed.
