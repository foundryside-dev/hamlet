# Blind re-run comparison — idea B (the spreading organism)

**The second of two blind re-runs (criterion 3). Executed under protocol Appendix B, which was
pre-registered for this run specifically.**

| | run 1 | run 2 (blind) |
|---|---|---|
| date | 2026-08-19 | 2026-08-20 |
| record | `B-20260819.md` | `B-blind-20260820.md` |
| pin | `1ef1d950` | `1ef1d950` (worktree, detached) |
| pack | `configs/trial_b_organism`, `configs/trial_b_organism_2d` | `configs/trial_b_blind_<slug>` (B.5) |
| core facets | 5 (+2 diagnostic) | 8 (+2 diagnostic) |
| leg (a) | PASS — empty | PASS — empty |
| **headline** | **FAIL** | **FAIL** |
| idea-level bucket | **BLOCKED** | **INERT** |

Comparer: the standing agent. A.8 bars the original executor; the standing agent executed
**neither** B run, which `current-state.md` recorded in advance as the condition making it
eligible to adjudicate this one.

---

## VERDICT OF THIS COMPARISON: §7's REJECT BRANCH **FIRES**

**The instrument is NOT accepted. No north-star reading publishes.**

It does **not** fire on facet cardinality — B.1 forbids that, and B.1 worked. It fires on
**substantive classification disagreement on mapped pairs**: the two runs reached **opposite
conclusions about the idea's core stress** at the same commit.

The headline verdicts agree (FAIL, FAIL). That agreement is **not** sufficient and must not be
quoted as if it were: §7 rejects on *verdict OR classification* disagreement, and A.8 keeps that
branch unchanged. Two runs agreeing on FAIL for **incompatible reasons** is precisely the failure
mode a blind re-run exists to expose.

---

## (a) Explicit facet mapping — B.1 step (a)

| run 1 | run 2 (blind) | mapping | agree? |
|---|---|---|---|
| F1 5-D discrete substrate | B-F1 5-D + exactly one organism | **mapped** (B-F1 strictly broader: adds the agent-count pre-commitment) | ✅ PASS / PASS |
| F2 mass, not point | B-F2 entity **is** a set of occupied cells | **mapped** | ❌ **BLOCKED / PASS** |
| F3 rooted outward growth | B-F3 rooted at declared cell **+** B-F5 spread (adjacency, accumulation) | **mapped, 1→2 split** | ❌ **BLOCKED / (PASS + ABSENT)** |
| F4 food warehouse as world entity | B-F4 warehouse at declared 5-D cell | **mapped** | ✅ PASS / PASS |
| F5 trainable spread-toward-food signal | B-F7 extent-attributed consequence | **mapped** | ❌ **PASS / BLOCKED** |
| — | B-F6 directable by policy | **blind-only** | see (c) |
| — | B-F8 observability | **blind-only** (partly inside run 1's F2 evidence bar) | see (c) |
| F6 *(diag B1)* 2-D baseline | B-D1 2-D baseline | mapped, both diagnostic | ✅ both localize to 2-D |
| F7 *(diag B3)* contested growth | B-D2 contested | mapped, both diagnostic, neither fully runnable | ✅ |

**Cardinality: 5 vs 8.** Under B.1 this alone fires nothing, and it should not — B.2's granularity
rule did most of its job, since run 1's F3 splits cleanly into B-F3 + B-F5 rather than diverging
arbitrarily. Cardinality is **not** the ground of this rejection.

## (b) Classification comparison on mapped pairs — B.1 step (b)

**Three of five mapped core pairs disagree. Two of them invert.**

### Disagreement 1 — F2 ↔ B-F2 — **BLOCKED vs PASS**. The load-bearing one.

Run 1: *"every declarative route to a durable organism cell is refused loudly"*, three verbatim
refusals, and the only reachable representation was the pre-named group-of-agents workaround,
which the countersigner had pre-ruled never-PASS. Filed `hamlet-1b9af9088c` (P1),
`hamlet-3f97369711`, `hamlet-4857e6824b`, `hamlet-6c49488b22`.

Run 2: **PASS on the first reach**, via a global-profile `tensorNd` VFS variable declared in
`vfs_profiles.yaml`. Run 2's own words: *"The workaround was never needed — the pack runs on one
agent, and a global `tensorNd` expresses a set-of-cells entity cleanly."*

This is not two readings of one evidence bar. Run 1's F2 bar asked for *"a declared per-cell
occupancy state attributable to the one organism"*, ≥2 cells at one tick, readable in the encoded
observation at a compiled offset. **Run 2's `tensorNd` appears to satisfy run 1's bar as written**
— it is one entity's state, it reached 243 occupied cells, and run 2's B-F8 confirms it is
observation-encoded. Run 1 searched `spawn_item`, per-cell/spatial-field scope, agent spawn
positions, and N-D item placement; it never tried a global `tensorNd`.

**Diagnosis: SEARCH VARIANCE, and consequential.** Run 1 concluded the substrate *cannot* express
an entity as a set of cells. Run 2 shows it *can*. Under A.8 the diagnosis informs what is
rebuilt, not whether the branch fires — but this diagnosis also bears directly on four filed
tickets and on the corpus's headline finding.

### Disagreement 2 — F5 ↔ B-F7 — **PASS vs BLOCKED**. The inverse direction.

Run 1 scored its trainable-signal facet PASS: *"rooted agent absorbs exactly +0.2, unrooted
control at the same cell absorbs 0"*, and step-toward `0.260000` > step-away `0.256667`.

Run 2 scored the mapped facet BLOCKED — and got there by **catching and correcting exactly the
measurement run 1 made**. Run 2's own correction note: B-F7 was *initially* scored PASS on a probe
measuring the **agent** standing on the warehouse, not the **extent** reaching it, and on a control
tick that was invalid because GROW fired on it. Re-run properly against the pre-committed
evidence: zero meter delta, byte-identical reward vectors.

**Run 1's F5 PASS measures an agent contacting a warehouse. The idea's Spec requires the
organism's extent to reach it.** Run 1's F5 evidence bar is satisfiable by a point-agent, which
is the representation its own F2 had just ruled insufficient — an internal tension no single-run
review caught, and which only surfaced because a second executor pre-committed a stricter,
extent-attributed bar and then held itself to it.

**Diagnosis: EVIDENCE-BAR DIVERGENCE, with run 2's bar the more faithful to the Spec.**

### Disagreement 3 — F3 ↔ B-F3 + B-F5 — **BLOCKED vs (PASS + ABSENT)**

Run 1 failed rooted-outward-growth BLOCKED: the occupied set *shrank* at tick 1, and A stayed
occupied only by parking an agent on it.

Run 2 split it: rooting at a declared cell **PASS** (`organism_cells.initial_value`), spread
**FAIL/ABSENT** — growth is wholesale (`1 → 243` in one tick), adjacency violated at Manhattan
distance 10, accumulation never tested because no cell is individually addressable.

Both agree growth fails. **They disagree on why and on class** — BLOCKED (a declared route refused)
vs ABSENT (no route exists). Under A.6.1's precedence that difference is exactly what drives the
idea-level bucket apart.

### Agreements

- **F1 ↔ B-F1: PASS / PASS.** 5-D `gridnd` is real and cheap, both runs, first reach.
- **F4 ↔ B-F4: PASS / PASS.** A warehouse at a declared 5-D coordinate is expressible.
- **Both diagnostics localize identically**: the failure is **not** dimensionality. Run 1 reproduced
  its refusal on 2-D; run 2's B-D1 reproduced its refusal on 2-D *at a compile stage before any
  substrate is consulted*. Two independent routes to the same localization is the strongest
  agreement in this comparison.

## (c) Unmapped facets — B.1 step (c)

B.1 requires, per unmapped facet: does the other run's pack satisfy it, and was the capability
demonstrated declarable at the same pin by **either** run?

| blind-only facet | run 1's pack satisfy it? | declarable at pin by either run? | fires reject? |
|---|---|---|---|
| **B-F6** directable by policy | **No.** Run 1 had no per-cell write at all, so directionality was never reachable. | **No.** Run 2 declared a direction surface that compiled and then produced identical occupied sets — INERT. Neither run demonstrated it. | **YES** — B.1: *"An unmapped facet that neither run demonstrated declarable at the pin IS a disagreement and fires it."* |
| **B-F8** observability | **Partly.** Run 1 observation-encoded extent *cardinality* (`organism_size`, offset 47) but explicitly **not** spatial layout. | **Partly.** Run 2 PASSed with the warehouse half via a declared-constant workaround annotated *"found by search"*. | Contributes; does not independently fire. |

**B-F6 fires the branch on its own, independently of the mapped-pair disagreements.** This matters:
even if a reviewer disputed disagreements 1–3 as evidence-reading differences, B.1's unmapped-facet
rule fires here on its own terms, and that rule was written and adopted **before** this run.

---

## Why B.1 did NOT fail, and why `PDR-0096`'s reversal trigger does NOT fire

`PDR-0096` armed this trigger: *if B's re-run fires the reject branch on a mapping/cardinality
ground B.1 was written to prevent, B.1 failed and Appendix B reopens.*

**It does not fire.** B.1 performed exactly as designed:

- Cardinality diverged 5 vs 8 — the precise scenario B.1 called *"the only finding to date that
  could produce a false REJECT."* B.1's mapping step absorbed it. No facet was rejected for being
  unmatched.
- B.2's granularity rule measurably worked: run 1's F3 split into B-F3 + B-F5 along the entity/verb
  seam B.2 specifies, rather than diverging arbitrarily.
- The rejection rests on **substantive classification disagreement on mapped pairs**, plus one
  unmapped facet neither run could demonstrate — both grounds B.1 explicitly preserves.

**B.1 prevented a false reject and permitted a true one. That is the whole design goal, and this
run is its first real test.** Appendix B does not reopen.

## Protocol defects found by this run

- **G-P1 (new, structural).** §3/P6 mandates copying `TEMPLATE.md` from `docs/product/trials/` —
  **the exact directory §7 forbids the blind executor to open.** P6 cannot be executed as written
  by a blind executor. Run 2 complied with §7, did not open it, and reconstructed the record
  structure from the protocol body. This is the **same shape as B.1's finding** (a §7 blinding rule
  contradicting a procedural rule elsewhere) and is the second instance. It needs the B.1 treatment:
  blinding wins, and the template must be supplied to the executor by the dispatcher.
- **A.6.1's precedence rule is doing more work than it was scoped for.** It was ruled to settle
  K's bucket. Here it is the mechanism by which two runs of the *same idea* land in different
  buckets (BLOCKED vs INERT) — because bucket follows *which facets fail*, and facet enumeration is
  what a blind re-run varies. Mechanical bucketing was chosen deliberately over executor judgment;
  this is the cost of that choice, and it should be recorded rather than patched reflexively.

## What this comparison does NOT establish

- It does **not** establish that the substrate is more capable than run 1 reported. It establishes
  that **two competent executors disagreed at one commit**, and that run 2 reached a surface run 1
  missed. Whether run 2's `tensorNd` reading survives scrutiny is a separate question that this
  comparison deliberately does not settle — it is exactly the kind of call that should not be made
  by the same pass that found it.
- It does **not** re-score run 1. Under Appendix B's scope rule nothing here re-scores B; run 1's
  record stands as recorded. What is now in question is the **instrument**, not that record.
- It does **not** by itself invalidate the four tickets run 1 filed. Run 2's `tensorNd` result is
  evidence bearing on `hamlet-1b9af9088c` / `hamlet-3f97369711`, and those tickets should be
  re-read against it — but re-reading them is WS-4 triage work, not a comparison finding.

## Consequences, stated plainly

1. **`PDR-0095`'s reversal trigger has FIRED.** It read: *no north-star reading publishes until
   idea B's blind re-run agrees.* It does not agree. **No north-star reading publishes.**
2. **Criterion 3 is NOT met.** It was half-met on idea O. The discriminating re-run — the one
   `PDR-0095` said would actually test the classification vocabulary — rejects.
3. **`PDR-0096`'s trigger does NOT fire.** B.1 worked. Appendix B stays as adopted.
4. **The 6-of-9 reading, the 0/0/2 split, and the ≥80% arithmetic are all now unpublishable**
   pending a decision on what happens to the instrument.
5. This is a **finding about the instrument**, and it is the finding the instrument was built to be
   capable of producing. `PDR-0078` placed acceptance on the instrument rather than the number
   precisely so that a result like this could not be quietly absorbed.

## Recommendation to the owner — not actioned

The reject branch is pre-registered and mechanical; firing it is not a judgment call and this
comparison fires it. **What happens next is a judgment call and is escalated.** The live options:

- **Adjudicate run 2's `tensorNd` result first**, by commissioned evidence audit (the
  `PDR-0098` pattern used on Trial F). If `tensorNd` does express a set-of-cells entity, run 1's
  central finding is wrong and four filed tickets need re-reading. If it does not, run 2's B-F2 PASS
  is wrong and the disagreement narrows. **This is the highest-information next step and it should
  precede any decision about the instrument.**
- **Do not rebuild the protocol yet.** The rejection's diagnosis is *search variance*, not protocol
  ambiguity — and A.8 says the diagnosis informs what is rebuilt. Rebuilding enumeration rules would
  be treating the wrong cause.
- The corpus's prediction (*"FAIL, or a heavy PARTIAL via a group-of-agents workaround"*) is
  **falsified on mechanism by run 2** — the workaround was never needed, and the real blocker is one
  level down: no cell of a container is addressable in any direction. Run 1 confirmed the prediction;
  run 2 falsified it. That divergence is itself part of what is now unpublishable.
