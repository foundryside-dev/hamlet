# PDR-0106 — Idea B's blind re-run REJECTS the instrument: §7's reject branch fires on substantive disagreement, criterion 3 is NOT met, and no north-star reading publishes

Date: 2026-08-20   Status: **accepted** for the adjudication (mechanical, pre-registered, inside
*accept against criteria*) · **ESCALATED** for what happens next to the instrument
Author: Claude (standing product owner, acting as comparer — A.8-eligible, having executed
neither B run)

Fires: `PDR-0095`'s reversal trigger — *"no north-star reading publishes until idea B's blind
re-run agrees"*
Does NOT fire: `PDR-0096`'s reversal trigger (see below — B.1 worked)
Record: `docs/product/trials/0001/B-comparison-20260820.md`, with
`B-blind-20260820.md` (975 lines) and `B-blind-countersigned-facets-20260820.md`
Related: `PDR-0078` (acceptance sits on the instrument, not the number), `PDR-0089` (the O+B
re-run pair), `PDR-0087` (Trial B run 1), `PDR-0098` (the commissioned-evidence-audit pattern)

## Context

`PDR-0095` recorded criterion 3 as **half met**: idea O's blind re-run reproduced PASS, but the
comparison refused to bank the win and said so in its own text — two all-PASS records make §7's
classification comparison **vacuous by construction**. It named **idea B as the discriminating
re-run**: a FAIL carrying BLOCKED facets, the first to actually exercise the ABSENT/INERT/BLOCKED
vocabulary. `PDR-0096` then pre-registered **Appendix B** specifically so that run would execute
under a protocol that could not fire a *false* reject.

This session ran it. The owner authorized subagent dispatch; the countersigner and blind executor
were separate fresh agents; the standing agent adjudicated as comparer.

**Blinding held at three checkpoints, each of which could have silently voided the run:**

1. The **live protocol at HEAD leaks B's verdict** — line 244, *"Trial B's existing BLOCKED bucket
   is unchanged"*, added by A.6.1 the previous day. The briefing used the protocol **at B's pin**
   (`1ef1d950`, 252 lines vs HEAD's 434, containing no A.6.1 and no mention of B) plus Appendix B —
   exactly what B's own scope override prescribes. **This is the second consecutive re-run where
   the protocol's scope rule caught a blinding hazard the agent would otherwise have walked into.**
2. Appendix B itself was scanned and is clean — no verdict, no gap IDs, no domain terms.
3. The pin **predates run 1's packs**, so `configs/trial_b_organism*` do not exist in the worktree
   at all. The executor was additionally barred from the four earlier trial packs that do.

## The finding

| | run 1 (2026-08-19) | run 2 (blind, 2026-08-20) |
|---|---|---|
| core facets | 5 | 8 |
| leg (a) | PASS — empty | PASS — empty |
| **headline** | **FAIL** | **FAIL** |
| F2 — entity as a set of cells | **BLOCKED** | **PASS, first reach** |
| F5 ↔ B-F7 — trainable signal | **PASS** | **BLOCKED** |
| idea bucket | **BLOCKED** | **INERT** |

**The headline verdicts agree, and that agreement is not sufficient.** §7 rejects on *verdict OR
classification* disagreement and A.8 leaves that branch unchanged. Two runs agreeing on FAIL **for
incompatible reasons** is precisely the failure mode a blind re-run exists to expose, and it must
never be quoted as agreement.

**Three of five mapped core pairs disagree; two invert.**

- **F2 ↔ B-F2 — BLOCKED vs PASS.** Run 1 concluded *"every declarative route to a durable organism
  cell is refused loudly"* — the corpus's deep stress, the trial's central finding, and the source
  of four filed tickets. Run 2 expressed it **first reach** with a global-profile **`tensorNd`**
  VFS variable, one agent, no group-of-agents workaround. `tensorNd` was **verified real at the
  pin** by the comparer: a validated type in both profile validators (`vfs_profiles_config.py`),
  in `vfs/schema.py`, and in `env_factory.py`'s allowed set, with rank checking. Run 1 searched
  `spawn_item`, per-cell scope, agent spawn positions and N-D item placement; it never tried it.
  **Diagnosis: search variance.**
- **F5 ↔ B-F7 — PASS vs BLOCKED.** Run 2 *initially* scored this PASS on **exactly the measurement
  run 1 made** — an agent standing on the warehouse — then caught that its control tick was invalid
  and re-ran against its pre-committed extent-attributed bar: zero meter delta, byte-identical
  reward vectors. Run 1's F5 bar is satisfiable by a point-agent, the very representation its own
  F2 had just ruled insufficient. **That internal tension survived a full single-run review** and
  surfaced only because a second executor pre-committed a stricter bar and held itself to it.
- **F3 ↔ B-F3 + B-F5 — BLOCKED vs (PASS + ABSENT).** Both agree growth fails; they disagree on why
  and on class, which under A.6.1's precedence is what drives the idea buckets apart.

**`B-F6` (directable) fires the branch independently**: a blind-only facet that **neither run
demonstrated declarable at the pin**, which B.1 explicitly says *is* a disagreement.

**Agreements worth keeping:** F1/B-F1 and F4/B-F4 both PASS, first reach, both runs. And **both
diagnostics localize identically** — the failure is *not* dimensionality; run 2's B-D1 reproduced
the refusal on 2-D *at a compile stage before any substrate is consulted*. Two independent routes
to the same localization is the strongest agreement in the comparison.

## Decision

**§7's reject branch FIRES. The instrument is NOT accepted. Criterion 3 is NOT met. No north-star
reading publishes.** The 6-of-9 reading, the 0/0/2 split and the ≥80% arithmetic are all
unpublishable pending an owner decision.

Firing the branch is **mechanical and pre-registered** — it is not a judgment call, which is why it
is recorded as `accepted` rather than escalated. **What happens next to the instrument is a
judgment call and is escalated.**

## Why `PDR-0096`'s trigger does NOT fire

`PDR-0096` armed: *if B's re-run fires the reject branch on a mapping/cardinality ground B.1 was
written to prevent, B.1 failed and Appendix B reopens.*

**It does not fire, and this is the session's most reassuring result.** Cardinality diverged 5 vs 8
— precisely the scenario B.1 called *"the only finding to date that could produce a false REJECT"*
— and B.1's mapping step **absorbed it**. No facet was rejected for being unmatched. B.2's
granularity rule measurably worked: run 1's F3 split into B-F3 + B-F5 along the entity/verb seam
B.2 specifies, rather than diverging arbitrarily. The rejection rests on substantive classification
disagreement on mapped pairs plus one undemonstrable unmapped facet — both grounds B.1 preserves.

**B.1 prevented a false reject and permitted a true one. That was the entire design goal, and this
run was its first real test.** Appendix B does not reopen.

## Rationale

`PDR-0078` deliberately placed acceptance on the **instrument** rather than the number, so that a
low reading could not be gamed by picking an easy corpus. This is the same principle collecting on
the other side: an instrument that cannot reproduce its own classifications cannot be allowed to
publish a number just because the number is interesting. `PDR-0095` pre-committed to exactly this
outcome — *"a disagreeing discriminating comparison outvotes an agreeing cheap one"* — before
knowing which way B would go.

The comparison deliberately does **not** settle whether run 2's `tensorNd` reading survives
scrutiny. That call should not be made by the pass that found it.

## What this does NOT establish

- **Not** that the substrate is more capable than run 1 reported — only that two competent
  executors disagreed at one commit and run 2 reached a surface run 1 missed.
- **Not** a re-scoring of run 1. Appendix B's scope rule forbids it; run 1's record stands. What is
  in question is the **instrument**, not that record.
- **Not** an invalidation of run 1's four filed tickets. Run 2's result is *evidence bearing on*
  `hamlet-1b9af9088c` / `hamlet-3f97369711`; re-reading them is WS-4 work, not a comparison finding.

## Escalated to the owner — recommendation, not action

1. **Commission an evidence audit of run 2's `tensorNd` result first**, on the `PDR-0098` pattern
   used for Trial F. It forks everything: if `tensorNd` expresses a set-of-cells entity, run 1's
   central finding is wrong and four tickets need re-reading; if it does not, run 2's B-F2 PASS is
   wrong and the disagreement narrows sharply. **Highest-information next step; it should precede
   any decision about the instrument.**
2. **Do not rebuild the protocol yet.** The diagnosis is *search variance*, not protocol ambiguity,
   and A.8 says the diagnosis informs what is rebuilt. Rebuilding enumeration rules would be
   treating the wrong cause.
3. The corpus's prediction (*"FAIL, or a heavy PARTIAL via a group-of-agents workaround"*) is
   **confirmed by run 1 and falsified on mechanism by run 2** — the workaround was never needed and
   the real blocker is one level down: **no cell of a container is addressable in any direction.**
   That divergence is itself part of what is now unpublishable.

## Protocol defects found by this run

- **G-P1 (structural, new).** §3/P6 orders the executor to copy `TEMPLATE.md` from
  `docs/product/trials/` — **the exact directory §7 forbids a blind executor to open.** P6 is
  unexecutable as written by a blind executor. Run 2 complied with §7, did not open it, and
  reconstructed the record structure from the protocol body. **This is the same shape as B.1's own
  finding** (a §7 blinding rule contradicting a procedural rule elsewhere) and is the second
  instance. It needs the B.1 treatment: blinding wins, and the dispatcher supplies the template.
- **A.6.1 is doing more work than it was scoped for.** Ruled to settle K's bucket, it is here the
  mechanism by which two runs of the *same idea* land in different buckets — because bucket follows
  *which facets fail*, and facet enumeration is what a blind re-run varies. Mechanical bucketing was
  chosen deliberately over executor judgment; this is the cost of that choice and should be recorded
  rather than reflexively patched.

## Reversal trigger

- If the commissioned `tensorNd` audit finds run 2's B-F2 PASS **unsound**, the largest
  disagreement collapses to an executor error rather than search variance, and this rejection is
  re-adjudicated on the remaining two disagreements — which may or may not still fire the branch.
- If the audit finds it **sound**, the rejection stands and a further question opens that this PDR
  does not answer: whether run 1's four filed tickets misdescribe the substrate.
- If any future reading is published from this corpus while criterion 3 remains unmet, `PDR-0078`
  and `PDR-0095` have both been violated and the instrument's governance has failed outright.
