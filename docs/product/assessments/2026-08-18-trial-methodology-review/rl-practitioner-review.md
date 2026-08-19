# PRD-0001 methodology review — deep-RL practitioner lens

Reviewer: general-purpose agent on Fable, fresh context, with the yzmir-deep-rl evaluation
skills. Ran its own empirical probe against `configs/trial_o_bidding` at the then-current
tree (post-`2dcc2273`) — findings marked [PROBE] are executed observations, not inference.
Dispatched 2026-08-18 at the owner's direction; delivered same day.
Adjudication: `PDR-0086`. Archived verbatim below.

Standing-agent annotation at archive time (not the reviewer's): F8's determinism concern
(unseeded `torch.randint` in spawn placement) underweights that `seed_all` seeds the global
torch RNG — bit-identical traces under seed were verified CPU and CUDA at the oracle tag —
so F8 reads lower-severity than stated. The rest of the findings were adjudicated as
delivered; F2's reset leak converges with the previously-filed `hamlet-d76684f549`.

---

# Trial Methodology Review — Deep-RL Practitioner's Lens

**Scope reviewed:** `docs/product/prds/0001-measure-the-authoring-claim.md`, `docs/product/prds/0001-trial-protocol.md`, all four trial records (`docs/product/trials/0001/{L,F,M,O}-20260818.md`), the four packs under `/home/john/hamlet/configs/trial_{l_cooldown,f_durability,m_combo,o_bidding}/`, and the engine paths the packs exercise (`vectorized_env.py`, `dac_engine.py`, `effects/manager.py`, `vfs/registry.py`, `universe/compilers/vfs.py`, `substrate/grid2d.py`). I also ran my own empirical probe against `configs/trial_o_bidding` at the current tree (script preserved in the session scratchpad); its outputs are cited below as [PROBE].

**Headline answer to the question asked:** The instrument is an unusually honest *authoring-cost* meter — pre-registration, both-legs verdicts, and the ABSENT/INERT/BLOCKED taxonomy are better discipline than most published RL evaluation. But it certifies a strictly weaker predicate than the sentence it is quoted against. `docs/product/vision.md:67` promises "a running, **trainable**, reproducible environment"; the trials verify *declarable + observable under scripted actions for ~15 ticks, single reset*. Between those two predicates sit exactly four things, and I found live, confirmed instances of three of them in the four packs already run. None of the four PASS verdicts is wrong *under the protocol's own definition* — the defect is that the protocol's definition does not reach the word "trainable," and the north-star will be read as if it did.

## Severity-ranked findings

### F1 — CRITICAL: `drive.yaml` is a required declarative surface that no trial ever leg-(b) checks; by the protocol's own logic every trial's reward function could be INERT and the trial would still PASS

**Evidence.** All four packs carry a full, No-Defaults-compliant `drive.yaml`. Three of them are byte-similar boilerplate (constant base 0.01 + `0.5*(energy)` + `0.5*(health)` per tick — `configs/trial_l_cooldown/levels/L0_effects/drive.yaml`, `.../trial_f_durability/levels/L0_tools/drive.yaml`, `.../trial_m_combo/levels/L0_combo/drive.yaml`); Trial O swaps in `wins`/`credits` bonuses. Every probe calls `env.step()` and **discards the reward tensor** — see `configs/trial_o_bidding/probe_trial_o.py:67` (`obs, *_ = e.step(...)`). No facet in any of the four records mentions reward. Yet the protocol's sharpest idea — INERT, "leg (a) passes while leg (b) fails, the worst failure mode for a declarative product" (`0001-trial-protocol.md:24-25`, the `range_type` precedent) — applies verbatim to DAC here: a reward declaration that compiled but computed garbage would be invisible to all four trials.

**What it threatens:** "trainable" — the reward function *is* the trainability surface, and it is the one declared behavior systematically exempted from leg (b).
**Inside or outside the protocol:** INSIDE. This is not a new instrument; it is the existing leg (b) applied consistently.
**Cheapest check:** one facet per trial, ~5 lines in the probe the executor already writes: capture the reward vector from `env.step()` at a tick where a declared component must move it, and assert the delta. For Trial O: on the clearing tick, winner reward jumps by `0.5*Δwins − 0.5*Δ(1−credits)` per `src/townlet/environment/dac_engine.py:196-201` (`bonus = scale * (bar_value - center)`, read off the **raw** meters tensor). Nearly free; the probe already steps through the exact ticks.

### F2 — CRITICAL (confirmed empirically): episode/reset semantics leak Trial O's mechanic across episodes — the pack is correct under the single-reset probe and broken as an episodic RL environment

**Evidence, all verified in code and by [PROBE]:**
- `VectorizedHamletEnv.reset()` (`src/townlet/environment/vectorized_env.py:788-882`) resets meters, ticks, the delayed-command scheduler, items — but **never clears active effects**: `effect_manager.reset_scheduler()` and `cancel_scheduled_for_entity()` touch only the delay scheduler; `EffectManager.agent_effects` / `global_effects` (`src/townlet/effects/manager.py:89-90`) survive.
- Global-profile VFS variables compile with `lifetime="persistent"` (`src/townlet/universe/compilers/vfs.py:90`), and `reset_episode_scoped()` resets only `{"tick","episode"}` lifetimes (`src/townlet/vfs/registry.py:593-595`).
- [PROBE] on `configs/trial_o_bidding`: active effects **1 before reset, 1 after**; `auction_timer=1.0` and `highest_bid=0.3` survive `env.reset()` unchanged; the ghost `auction_house` keeps ticking in the new episode (`auction_timer` 1.0 → 2.0 after one WAIT) before any agent has bid. Both variables are observation fields (offsets 61 and 62, `total_dims=63`), so **the first observation of every episode after the first carries stale previous-episode auction state**.

**Consequences for training:** the clearing-window phase at episode start depends on the tick the *previous* episode ended — a non-stationary, non-Markov initial-state distribution across the 10-episode × 100-step training run the pack itself declares; and with `reapply_policy: renew` + `duration: 100000` the effect is effectively immortal for the whole run. Whether persistent-lifetime globals + surviving effects is authored intent or a framework defect is precisely the question the protocol cannot currently ask, because no facet in any record ever resets twice.
**What it threatens:** "trainable" and "reproducible."
**Inside or outside:** INSIDE — one standard facet appended to every trial: *after `env.reset()`, re-run the probe's first assertion block; every mechanic state must be back at its declared initial unless the pack declares persistence.* ~4 lines. It would have flipped nothing in L/F/M (meters are re-initialized at `vectorized_env.py:817`, item state at `:853-856`) and would have caught O's leak cold.

### F3 — HIGH: no training-smoke leg — the cheapest leg (c) and what it would have caught

The four gaps in question 1, ranked by threat to the claim:

1. **Reward-surface observability** (F1) — threatens "trainable" directly, IN scope by the protocol's own INERT logic. Rank 1 because it is a *false-pass class already defined by the protocol* and left open.
2. **Reset/episode-semantics × mechanic** (F2) — threatens "trainable" and "reproducible," confirmed live. IN scope, near-zero cost.
3. **Mechanical trainability** — env survives the actual training loop: no crash, no NaN, finite rewards, obs in bounds, episodes terminate. IN scope as a new leg (c). Note the packs already declare complete `training.yaml` files (`seed: 42`, `max_episodes: 10`, `batch_size: 10`) that **no trial has ever executed** — an entire required config surface certified by parse alone.
4. **Learnability proper** (does an agent *learn* the mechanic; sample efficiency; multi-agent equilibrium) — legitimately OUT of an authoring-cost metric. A PASS conditioned on learning would depend on hyperparameters, seeds, and algorithm choice; doing it honestly requires multi-seed protocols (5–10 seeds minimum per the evaluation discipline) that would destroy the one-session trial budget and conflate "the substrate can express it" with "DQN can solve it." Keeping it out is the right call — *provided the north-star stops borrowing the word "trainable"* (see F7).

**Cheapest concrete leg (c):** two parts, both cheap. (c1) the reward assertion from F1 inside the existing scripted probe. (c2) K random-policy episodes (K≈5) through `VectorizedHamletEnv` — or one `DemoRunner` invocation with the pack's own `training.yaml` at `max_episodes: 5` — asserting: no exception, rewards finite and nonconstant, every obs component within its declared normalization bounds, and episode-start state consistent across resets. Minutes on CPU.
**What it would have caught in the four packs already run:** O's cross-episode leak and stale first observation (multi-episode by construction); F's raw-value observation breach (F5 below); and it converts F's lucky by-catch — the zero-affordance pack that "validates and compiles, then crashes at the first observation" (`F-20260818.md:53-57`, filed `hamlet-fba3d5aa3c`) — from an accident of authoring order into a systematic detection class. L and M would pass (c) clean, which is also information.

### F4 — HIGH (confirmed empirically): Trial O's mechanic is degenerate at exactly the action profile training converges to — ties award everyone, and the budget constraint is silently unenforced

**Evidence [PROBE]:**
- **Tie:** both agents bid 0.3 → **both** get `wins=1.0`, **both** pay (`cred=0.70` each). The clearing branch is `if target.bar.bid >= vfs.highest_bid` (`configs/trial_o_bidding/effects.yaml`, award phase) — `>=` makes every max-tier bidder a "winner." Facet 4's declared standard was "the contested thing goes to the **winner only**" (`O-20260818.md:33`); the scripted probe only ever tested 0.3-vs-0.1, so the equality case — the single most likely case under symmetric learners — was never exercised. This is a facet-evidence gap in the record as written, not just an RL concern.
- **Budget:** an agent at `credits=0.00` kept winning (wins climbed to 7) because `credits - bid` clamps at the bar's `min: 0.0`. Nothing gates BID on affordability. After ~3 wins, bidding is free.
- **Reward geometry:** DAC reads raw meters (`dac_engine.py:199`), so one win yields a *standing* +0.5/tick (`wins` bonus) against a one-time credits drop worth at most −0.15/tick. Both independent learners are therefore driven to BID_HIGH every window → permanent tie → everyone wins every round, payment stops binding → the "adversarial, contested" mechanic self-destructs under the optimization pressure the product exists to apply. The authored pack is a correct 3-tick demo and a degenerate game.

**What it threatens:** "trainable" (mechanic collapses under optimization) and the internal honesty of leg (b) (declared facet standard not actually evidenced).
**Inside or outside:** split. *Inside:* a protocol rule that comparison/branch facets must pre-commit and probe their boundary case (equality, zero, saturation) — two lines in the O probe would have surfaced the tie award. *Outside:* "does the mechanic survive optimization" is a distinct instrument (see F7) — demanding it inside the trial would smuggle game-design review into an authoring-cost metric.

### F5 — MEDIUM (confirmed): observation-space bounds and conditioning are never checked, and two of the four packs have live encoding problems at network input

**Evidence:**
- **Trial F:** `obs_item_slots=[3.0]` at compiled offset 58 (`F-20260818.md:88`) — the item-slot block emits **raw durability** into an observation vector whose every other component is normalized to [0,1]. The record read the 3.0, printed it, and PASSed facet 4 without noting the convention breach. An unnormalized, unbounded feature at network input is a classic silent trainer-degrader.
- **Trial L:** the cooldown timer is declared `minmax` over `[0, 1000]` (`configs/trial_l_cooldown/levels/L0_effects/bars.yaml`, `since_bed` max 1000.0) for a mechanic whose entire decision-relevant band is 0–10 ticks. The record's own numbers: encoded 0.009 (gated) vs 0.011 (open) (`L-20260818.md:96-98`) — the gate boundary is a **0.002 difference at network input**, with the feature spiking to 1.0 at reset (initial 1000). Distinguishable in principle, atrociously conditioned in practice; the state *is* encoded, and a DQN will mostly not read it.

**What it threatens:** "trainable" (sample efficiency, conditioning), plus framework hygiene (the item-slot raw emit looks like an engine defect worth filing, not an authoring choice).
**Inside or outside:** the **bounds assertion goes INSIDE** — one loop in leg (c): every obs component within its declared normalization range across the probe run (this alone flags F). The **conditioning/scale review goes OUTSIDE**, ideally as a compiler lint ("feature's active dynamic range < 5% of its declared normalization range" — a warning at compile time serves the novice author far better than a trial finding), which is itself a WS-4-shaped declarative-surface improvement.

### F6 — MEDIUM (confirmed): in L and M the reward surface renders the trialed mechanic irrelevant — a trained agent would demonstrate nothing about it

**Evidence:** Trial M's `COMBO_A` is cost-free, ungated, repeatable, +0.05 energy per use (`configs/trial_m_combo/levels/L0_combo/affordances.yaml:15-20`); energy (capped at 1.0) is the sole reward carrier, and `did_a`/`did_b` appear **nowhere** in `drive.yaml` (grep: zero hits). Spam-A maxes reward; B and C are never needed. Trial L: attempting a gated INTERACT is free — no cost, no penalty — so "sit at BED and spam" is optimal and the timer observation need never be read. Both mechanics are authored correctly and are *decoration* with respect to the objective.

**What it threatens:** the product's own motivating sentence — "I wonder what agents would do with this mechanic" (`vision.md:66-67`). The honest trained answer for L and M is: ignore it. A novice author will experience that as the framework failing.
**Inside or outside:** OUTSIDE the PASS/FAIL — making PASS depend on incentive design would grade the author's game, not the substrate. But a cheap **non-gating recorded observation belongs inside**: "do the mechanic's state variables appear in any reward component?" is a one-grep note per trial record. For L, F, M today the answer is no.

### F7 — MEDIUM: the north-star's name writes a check the instrument doesn't cash — "trainable" needs its own metric row, not a bigger PASS bar

The PRD is internally honest — it measures "expressible as a config pack alone" (`0001-measure-the-authoring-claim.md:56-57`) and explicitly scopes fixing out. But the vision sentence it operationalizes contains three predicates (running, trainable, reproducible) and the trials evidence roughly one and a half. A 4-of-4 (soon N-of-9) reading *will* be quoted against the full sentence. The clean fix is not to inflate PASS (which would break the pre-registered instrument mid-corpus — the amendments window closed 2026-08-17) but to add leg (c) as a **separately reported column** ("trains-without-incident: yes/no") that does not move the headline for the current corpus, plus its own `metrics.md` row going forward. That preserves the frozen instrument and stops the word-borrowing.
**Inside or outside:** the column inside the record; the metric row outside the trial protocol.

### F8 — LOW: determinism and vectorization consistency — once globally, not per trial (with one exception)

- **Determinism:** agent spawns come from the unseeded global torch RNG (`src/townlet/substrate/grid2d.py:82-90`, `torch.randint` with no generator); the probes never notice because they teleport agents (`park()`). `training.yaml: seed: 42` is declared in every pack and consumed by no trial. Effects vocabulary includes `sample` — packs using it would be silently nondeterministic under an unseeded env.
- **Vectorization:** probes run `num_agents` 1–2 on CPU; the product claim is GPU-batched, and O's clearing runs a Python-level `for_each: all_agents` loop.

Neither belongs per-trial: they are engine invariants, and re-proving them nine times is ceremony. **One global conformance fixture** (same pack, same seed → identical trajectories at N∈{1,2,32}, CPU vs GPU; obs bit-identical) covers all packs at once. **Exception:** any mechanic with cross-agent resolution (the O class) should carry one N≥3 probe case inside its trial — "three bidders, middle one loses" — because per-agent-loop clearing logic is exactly where N=2 hides ordering and aggregation bugs. Two lines.

## Confidence Assessment

**Overall Confidence: High**

| Finding | Confidence | Basis |
|---|---|---|
| F1 — reward never leg-(b) checked; probes discard rewards | High | All four records read; `probe_trial_o.py:67` discards; drive.yamls read; `dac_engine.py:196-201` verified |
| F2 — effects + persistent globals survive reset; O leaks across episodes | High | Code (`vectorized_env.py:788-882`, `manager.py:89-90,340-343`, `registry.py:593-595`, `vfs.py:90`) **and** executed probe confirming 1 active effect and timer/highest_bid surviving reset |
| F4 — tie awards all; zero-credit bidder keeps winning | High | Executed probe: both `wins=1.0` on tie; `wins=7` at `cred=0.00` |
| F4 — both learners converge to BID_HIGH | Moderate | Inference from reward arithmetic (verified: raw meters, +0.5/tick standing wins bonus); no training run performed |
| F5 — F emits raw 3.0 in obs; L gate band is 0.002 wide at input | High | F record line 88 and my field dump (offsets verified); L record's own encoded values at `L-20260818.md:96-98` |
| F6 — spam-A dominates M; traces absent from drive | High | `affordances.yaml:15-20` read; grep for `did_a|did_b` in drive.yaml returned nothing |
| F8 — unseeded spawn RNG | High | `grid2d.py:82-90` read |
| Claim that L/F/M would pass an F2-style reset check | Moderate | Reset paths for meters/items verified in code; not empirically re-probed |

## Risk Assessment

**Implementation Risk (of adopting these recommendations): Low** · **Reversibility: Easy** — all proposed checks are additive probe lines and a new non-gating record column; none touches `src/townlet/` or the frozen corpus.

| Risk | Severity | Likelihood | Mitigation |
|---|---|---|---|
| Changing leg definitions mid-corpus voids comparability of trials 5–9 with 1–4 | High | High if leg (c) is made *gating* now | Report leg (c) as a separate non-gating column for this corpus; gate only from the next corpus |
| Retro-running leg (c) on L/F/M/O produces findings that pressure re-verdicts | Medium | Medium | Findings file as gaps (§8 discipline), verdicts stand — the protocol already separates finding from verdict |
| F2's engine behavior (persistent effects) gets "fixed" reactively, breaking a mechanic some pack relies on | Medium | Low | File as WS-4 design question (persist-across-reset should be *declarable*, per the project's own declarative principle), not a hotfix |
| Blind re-runs (criterion 3) diverge on O because facet 4's evidence was underspecified for ties | Medium | Medium | If O is chosen for a blind re-run, the comparer should know the tie case is undefined by the first record |

## Information Gaps

1. Whether any trial pack survives `DemoRunner` end-to-end — I did not run the training loop; F3's cost estimate ("minutes on CPU") is from config scale, not measurement.
2. GPU behavior — no GPU in this environment; the vectorization-consistency concern (F8) is untested in both directions.
3. The five unrun trials (B, D, E, J, K) — whether the gaps found here generalize; D/E/J are multi-agent and will stress F2/F4 harder than O did.
4. Intent behind `lifetime="persistent"` for global-profile vars (`vfs.py:90`) — design docs may record this as deliberate; I found no declarative override surface, but did not sweep `docs/architecture/vfs*.md` for it.

## Caveats & Required Follow-ups

**Before relying on this analysis:** (1) re-run my probe from a clean checkout — it lives in the session scratchpad (`probe_reset_tie.py`) and depends only on the committed pack; (2) confirm the O record's pinned commit vs the current tree — my probe ran at the current `project-recovery-2` HEAD, not at pin `a3318624`; the reset/tie behaviors are in code paths unchanged by the trial commits, but strictly the verdict-commit binding differs.

**Assumptions:** trials continue to be scored under the frozen protocol (no retro-void of the four PASSes — nothing here justifies one: every verdict is correct under the stated criterion); the product's training path is the DQN family in `src/townlet/agent/networks.py` (my learnability comments assume feedforward/recurrent Q-learning, not an arbitrary algorithm).

**Limitations:** I did not train any agent, so every "would converge to / would ignore" statement is reward-arithmetic inference, not a learning curve; multi-seed empirical confirmation of F4/F6 is exactly the separate instrument I recommend, not something this review substitutes for.

**Recommended next steps:** (1) add the F1 reward assertion and F2 double-reset facet to the probe template before Trial 5 (non-gating for this corpus); (2) file the F2 persistent-effects question and F5 raw-item-obs emit as WS-4 items; (3) create the leg-(c) training-smoke as a separate `metrics.md` row so "trainable" gets its own denominator instead of borrowing the authoring rate's; (4) if O is picked for the blind re-run, pre-brief the comparer on the tie-case underspecification.
