# PRD-0001 — Idea corpus            **FROZEN 2026-08-17**

Drafted 2026-08-17 (agent), riffed the same session (owner), frozen the same session. Every
prediction below was recorded **before the corpus was closed and before any trial ran** — the
pre-registration property (`PRD-0001` criterion 2). This file is now content-hashed and committed;
**editing it after any trial begins voids that trial** (criterion 1).

**Origin mix** — the corpus's own bias profile, per the owner's *"I draft, you riff"*:
**7 owner-supplied** (B, I, J, K, L, O, P) · **3 owner-riffed** (A, D, E) · **5 agent-drafted**
(C, F, G, H, M). A reader who distrusts the number should start here.

## Axis buckets (the stratification the draw runs over)

| bucket | ideas |
|---|---|
| physical | A, B |
| environmental | K |
| temporal | C, L |
| items | F, G |
| contention | H, O |
| action-structure | M |
| social-economic | D, E, I, J, P |

## Draw protocol (reproducible; run it yourself and check)

The trial set is **drawn mechanically, never chosen** — that is what stops anyone, including me,
from leaning toward winnable ideas.

1. **Seed** = `int(sha256(<this file, bytes>).hexdigest(), 16)`. Nobody picks the seed; it is a
   pure function of the frozen corpus. Change one character here and the draw changes, which is
   why criterion 1 voids trials run against an edited corpus.
2. Buckets are taken in **alphabetical order**; `random.Random(seed)` draws **one idea from each**
   (7 ideas, guaranteeing every axis is represented).
3. From the 8 remaining, the same generator draws **2 more**, for **N = 9**.
4. The 6 undrawn ideas stay in the pool for the next read of the same corpus.

The residual, stated: the stratification is what actually bounds bias; the seed only orders picks
*within* buckets. Since I wrote much of this file's text, I could in principle have influenced the
hash — the guarantee that matters is the per-bucket floor, not the seed.

---

## A — Momentum and a real physics model
**Spec.** Agents carry velocity and thrust rather than teleport between cells; drag, and elastic
boundaries. Push a genuine Newtonian point-mass model, not a token continuous pack.
**Source.** *Asteroids*; Newtonian point-mass dynamics with drag.
**Stresses.** `continuous` / `continuousnd` substrate, `bounce` boundary mode, velocity as an
observed quantity, force-style action semantics.
**Predict: PASS on the substrate, PARTIAL on the model.**
**Origin.** Agent-drafted; **owner-riffed** — the owner's framing is the load-bearing part: this
is expected to *"expose gaps in the implementation rather than bugs."* A gap and a bug are
different findings with different routes (WS-4 vs. the tracker), and this trial is chosen to
produce the former.

## B — The spreading organism (owner's headline idea, three variants)
**Spec.** (Scored as ONE corpus entry on B2; B1/B3 are diagnostic facets.) An organism rooted at point A grows outward and must learn to spread toward food.
- **B1 — baseline:** spread on a 2-D grid toward a static food source.
- **B2 — headline:** spread across a **5-D discrete landscape** toward a food warehouse.
- **B3 — contested:** two organisms grow toward one food source (this absorbs the original
  "territory capture" seed).

**Source.** StarCraft *creep*; moss growth; and the real-world case — *Physarum polycephalum*
slime mould solving network-optimization problems (Tero et al., 2010).
**Stresses.** `gridnd` at 5-D; and the deep one — **an entity that is a set of occupied cells
rather than a point**. Every agent in this engine carries a position (Trial 001 measured
`positions` shape `(4, 6)`); a spreading mass is not a position.
**Predict: FAIL, or a heavy PARTIAL via a group-of-agents workaround.** If a workaround is the
only path, that is itself the finding — the question is whether an *author* could reach it.
**Origin.** **Owner-supplied** (B1/B3 are agent-drafted framings of the owner's idea).

## C — Sleep pressure (two-process model)
**Spec.** A homeostatic accumulator and a circadian oscillator jointly gate the value of rest.
**Source.** Borbély's two-process model of sleep regulation (1982).
**Stresses.** VFS aggressively — two coupled processes, one driving the other's effect. Trial 002
proved a single `sin(time)` process authorable through `effects.yaml`; coupling two is untested.
**Predict: PARTIAL.**
**Origin.** Agent-drafted; **owner-selected over the "shop hours" seed** as *"a better version
that exercises VFS more aggressively."* Shop hours is dropped — I could already name its failure
(no world clock in effect expression scope), and an idea whose failure is already known tests
nothing.

## D — Barter, with advertising broadcast in a region
**Spec.** Two agents exchange items by mutual consent — **and** an agent advertises goods for sale
by broadcasting into a spatial region.
**Source.** *Settlers of Catan* trading; EVE Online regional market orders.
**Stresses.** `message` scope and whether it can be **spatially scoped**; `pair` scope for the
transaction; item transfer between agents.
**Predict: FAIL on the transfer, UNKNOWN on the broadcast** — `message` is in `VariableScope` and
I have no evidence either way that it is live. The genuine unknown makes this a strong trial.
**Origin.** Agent-drafted; **owner-riffed** (the advertising/broadcast half is the owner's).

## E — Hidden prey in a pack of predators, kept alive by reputation
**Spec.** One NPC is secretly prey among predators; its reputation is what keeps it alive.
**Source.** Social deduction (*Among Us*, Werewolf); and the real-world case — **Batesian
mimicry**, a harmless species surviving by resembling a dangerous one.
**Stresses.** `agent_private` scope (the hidden type), agent **heterogeneity** (differing roles
and action sets), a variable written by *other* agents' observations, and predator decisions
gated on observed reputation rather than hidden truth. Also a direct test of the **name-blindness
invariant** — `vision.md` names reputation explicitly as something the runtime must not know.
**Predict: FAIL.** Heterogeneous agents and cross-agent writes are two things I doubt are
declarable, and this idea needs both.
**Origin.** **Owner-riffed** — the merge of the reputation and predator seeds into one idea, and
the hidden-prey framing, are the owner's. It is a sharper test than either seed alone.

## F — Tool durability
**Spec.** An item degrades per use and eventually breaks.
**Source.** *Breath of the Wild* weapon breaking; *Minecraft* tool durability.
**Stresses.** Item-scoped variables that decay on use; item destruction.
**Predict: PASS.**
**Origin.** Agent-drafted.

## G — Crafting
**Spec.** Combine two carried items into a third.
**Source.** *Minecraft*.
**Stresses.** Item consumption and creation from an affordance.
**Predict: PARTIAL.**
**Origin.** Agent-drafted.

## H — Queueing at a scarce resource
**Spec.** One machine, many agents, contention and waiting.
**Source.** M/M/1 queue; *Theme Park* ride queues.
**Stresses.** Occupancy claims, contention.
**Predict: PASS.**
**Origin.** Agent-drafted.

## I — Holding down a job
**Spec.** Turn up at a workplace during a window, get paid, be penalized for absence.
**Stretch:** discover a better-paying job and switch to it.
**Source.** *The Sims* career tracks; labour-supply modelling.
**Stresses.** A persistent **scheduled obligation**, wage differentials, switching cost — and
almost certainly the same world-clock gap the dropped "shop hours" seed would have hit.
**Predict: PARTIAL/FAIL, blocked on the world clock.** Worth keeping *despite* overlapping the
dropped seed's gap: it reaches that gap through a mechanic someone actually wants, which is a
much stronger argument for fixing it than a synthetic shop-hours probe.
**Origin.** **Owner-supplied.**

## J — Faction tasking via a notice board
**Spec.** An agent posts a job to a notice board (*go fetch a widget*); a different agent picks the
job up, fetches the thing, returns it, and is settled with.
**Source.** MMO / *Monster Hunter* quest boards, bounty boards; and the real-world case — task
marketplaces (Mechanical Turk-style spot labour).
**Stresses.** The one genuinely new shape in the corpus: **an agent's goal originating from another
agent.** Underneath that — a posting that is persistent world state outliving the poster's action
and readable by others; **claim semantics** on a non-spatial object (one taker, not many); a
multi-tick obligation carried across fetch → return → settle; and inter-agent transfer of both the
widget and the payment.
**Predict: FAIL, ABSENT on several facets.** Posting looks like an action that creates durable
shared state with no declarative path; settlement needs the same cross-agent transfer I predict
absent in D.
**Overlap, stated honestly.** D and J both touch `message` scope and inter-agent transfer, and I,
D, J are all economic. They are structurally distinct — D is a *simultaneous* exchange between two
consenting agents, I is a *schedule-driven* obligation to an employer, J is an *asynchronous posted
contract* with claim and settlement — but the corpus is now tilted toward the social/economic axis
and that is a diversity cost worth naming before the freeze.
**Origin.** **Owner-supplied.**


## K — Responding to the universe
**Spec.** The world imposes a condition the agent must adapt to: it gets too cold, and the agent
must put on a shirt, go inside, or lose comfort/health.
**Source.** *The Long Dark*, *Don't Starve* winter, *Oxygen Not Included*; and the real-world case
— thermoregulation and thermal-comfort modelling (Fanger's PMV model).
**Stresses.** The axis nothing else in the corpus touches: **the world acting on the agent**, and
the agent adapting. Every other idea is agent→world (A, B, D, F, G, H, I, J), internal (C), or
agent→agent (E). Underneath it, three *different* mitigation paths for one pressure, each landing
in a different subsystem: **equip an item** (an equipped item modifying how an incoming effect
lands), **change location** (`zone` scope carrying different environmental properties), or **eat
the cost** (meter dynamics).
**Predict: PARTIAL — and the split is the point.** The *pressure* is likely authorable: Trial 002
proved a global process driving a bar through `effects.yaml`. Both *responses* are doubtful —
`zone` scope is in `VariableScope` with no evidence it is live, and an equipped item conditioning
the magnitude of an incoming effect is a modifier chain I have not seen a path for. If that is how
it lands, the finding is sharp: **an author can express the problem but not the answers to it**,
and a pressure with no expressible relief is not the mechanic anyone wanted.
**Origin.** **Owner-supplied.**


> *(The letter N is skipped throughout — it is reserved for the corpus size.)*

## L — Cooldown management (as distinct from resource management)
**Spec.** An action is gated by *time since last use* rather than by a stock you spend and refill.
The skill is timing, not budgeting.
**Source.** MOBA/RPG ability cooldowns; refractory periods in real systems.
**Stresses.** Per-agent, per-affordance *time-since-last-use* state, and gating availability on it.
The owner's framing is the load-bearing part: **the entire shipped demo is resource-based** —
eight meters, all stocks — and nothing in it is cooldown-based, so this probes a mechanic class the
substrate has never been asked for.
**Predict: PARTIAL, and — uniquely in this corpus — I predict it lands INERT rather than ABSENT.**
`time_since_last_eat` and `time_since_last_sleep` are **already declared observation fields with
zero writers** (`hamlet-dc8f887cd5`). If that is what the trial hits, the surface exists, validates,
and does nothing — which is the debt class, not the not-yet-built class. That makes L the corpus's
first live test of the ABSENT/INERT distinction and of the escalation clause built on it.
**Origin.** **Owner-supplied.**

## M — Combo actions (A enables B enables C)
**Spec.** Performing action A makes B available; B makes C available. Sequential unlocking.
**Source.** Fighting-game combo chains (*Street Fighter*); MOBA ability sequences.
**Stresses.** Action **preconditions** — availability conditioned on a prior action. VFS names
"action dependencies" among its purposes, while the authorability ledger records that **VTC action
writes have no YAML path** and custom actions are structural no-ops. Those two facts point opposite
ways, which is exactly why it is worth measuring rather than arguing about.
**Predict: PARTIAL, possibly INERT** — a declared dependency surface that nothing enforces would be
the same shape as L.
**Origin.** Agent-drafted from the owner's concept.

## O — Adversarial bidding
**Spec.** Agents bid against each other for a contested item; highest bid wins and pays.
**Source.** Auction theory (Vickrey, 1961); *Modern Art* / *Ra*.
**Stresses.** A **global resolution phase over simultaneous agent submissions** — collect bids,
compare, award, charge. Nothing else in the corpus needs the engine to run a clearing step. Sits in
deliberate contrast with H: same contention problem, different clearing rule (first-come vs.
highest-value), which isolates the rule as the variable.
**Predict: FAIL, ABSENT.**
**Origin.** **Owner-supplied.**

## P — A faction researches a technology and votes on the next one
**Spec.** Members contribute collectively toward unlocking a technology, then **vote** on which
technology to pursue next. (The owner's merge of *shared bidding / shared research* with *faction
voting* — one idea, not two.)
**Source.** *Civilization* tech tree plus council voting; and the real-world case — collective
action and public-goods provision (Ostrom).
**Stresses.** The corpus's strongest test of `group` scope: many agents contributing to one shared
accumulator, a **vote aggregated into a group decision**, and a **persistent mid-episode unlock**
that changes the available affordance set. Pairs against M — both are "availability changes with
state", but M is per-agent and sequential where P is group-level and persistent.
**Predict: FAIL.** Group accumulators, a vote-aggregation step, and mid-episode affordance unlock
are three separate things I doubt, and it needs all three.
**Origin.** **Owner-supplied** (including the merge).


---

## Standing note

This corpus is a durable asset, not a one-shot. Re-running the same 15 ideas after further WS-4
units land yields a number **comparable to today's**, because it is the same ideas scored the same
way — the first thing `metrics.md`'s Trend column has ever had real content for.
