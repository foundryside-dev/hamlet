# Teachable Moments

> ✅ **Index rewritten 2026-08-26.** The previous README indexed 5 of 15 files, was dated
> 2025-10-28, and every path in its "Related Files" section was dead. It was **left in the
> archive** (`docs/zzz. archive/teachable_moments/README.md`) rather than recovered. This is a
> fresh index; it covers everything actually in this directory.

Emergent behaviours and "interesting failures" preserved as teaching material rather than
immediately fixed. Per `CLAUDE.md`, this is deliberate: **pedagogical value is a property of
the framework, not the mission.** A reward-hacking agent is a finding, not just a bug.

---

## ⚠️ Read this before you trust any number in this directory

These documents were written between 2025-10 and 2026-05, against an engine that has since been
substantially rebuilt — the Python reward-strategy layer was deleted, meters moved into
`bars.yaml` and VFS, and the observation representation is mid-migration. Each file was
re-verified against source on **2026-08-26** and carries its own banner naming what is wrong.

Three failure patterns recur, and they are worth recognising by shape:

| Pattern | What it looks like | Why it is dangerous |
|---|---|---|
| **Deleted mechanism** | A `Status: Implemented ✅` line for Python that no longer exists | Reads as a record; is actually intent |
| **Inverted arithmetic** | Costs and rewards that shipped config *contradicts* | Worse than unbuilt — the lesson's premise is false |
| **Prediction laundered into result** | Figures stated as "Hypothesis" in one section, "Result" in another | Same file argues both ways; the numbers were never measured |

**Never quote an observation width, action count, or dimension figure from this directory.**
Every such literal here is wrong. Observation width is not a constant, it is not one quantity,
and the accessor for it is *currently changing* — the artifact is the only authority. Ask the
compiled universe, and check `CLAUDE.md` §"State Representation" for the current accessor
before you do.

---

## The reward-design arc

Read these three together — they form a bug → diagnosis → proposed fix sequence, and they are
the strongest material here.

| Doc | The lesson |
|---|---|
| [`interoception_reward_design.md`](interoception_reward_design.md) | **Proposes** a multiplicative `health × energy` reward, so an agent must keep *every* meter alive rather than trade one off |
| [`low_energy_delerium.md`](low_energy_delerium.md) | **Diagnoses** why that reward fails: as extrinsic reward collapses toward zero, a fixed intrinsic weight dominates and the agent explores instead of surviving |
| [`milestone_rewards_design.md`](milestone_rewards_design.md) | **Argues the general form:** dense per-step rewards pay for oscillation; sparse milestone rewards do not |

The fix side of the delirium story *ships today*, declaratively — every level's `drive.yaml`
declares an `energy_crisis` modifier that zeroes the intrinsic term in crisis. The bug side is
**authorable but not shipped**: `multiplicative` is a working DAC extrinsic type, but no shipped
level declares one, so the contrast is a config edit away rather than an engine change. See the
banner in `low_energy_delerium.md` — it corrects `CLAUDE.md` on this point.

## Reward hacking

| Doc | The lesson |
|---|---|
| [`reward_hacking_interact_spam.md`](reward_hacking_interact_spam.md) | Agents optimize what you measure. ⛔ Mechanism contradicted by shipped config — read the banner |
| [`flight_sim_reward_hacking_story.md`](flight_sim_reward_hacking_story.md) | An external war story from a prior project. ✅ Cleanest file here |

## Action masking

| Doc | The lesson |
|---|---|
| [`action_masking_wall_evidence.md`](action_masking_wall_evidence.md) | Invalid actions the agent must *learn* to avoid are wasted capacity. ✅ **Most accurate file in this directory** — its mechanism claim still matches source |
| [`action_masking_boundaries.md`](action_masking_boundaries.md) | Same ground, weaker. ⚠️ Contains a false claim and contradicts its own numbers. Prefer the file above |

## Representation and complexity

| Doc | The lesson |
|---|---|
| [`from_potato_to_attention.md`](from_potato_to_attention.md) | Why flat concatenation limits relational reasoning. **Still live** — `SetEncoderQNetwork` / `TokenSetQNetwork` are this argument's descendants |
| [`complexity_types.md`](complexity_types.md) | Non-stationarity and context-dependence, not dimensionality, drive sample complexity |

## Pedagogy

| Doc | The lesson |
|---|---|
| [`trick_students_pedagogy.md`](trick_students_pedagogy.md) | Let students predict, then be wrong. ✅ Near-zero code claims |
| [`three_stages_of_learning.md`](three_stages_of_learning.md) | Teach RL as a three-act story told through checkpoints. Framework durable, ⚠️ figures unverifiable |

---

## Left in the archive

Four files stayed at `docs/zzz. archive/teachable_moments/`:

| File | Why |
|---|---|
| `DISCOVERED_INSIGHTS.md` | A session log against a hardcoded-Python meter engine that no longer exists. Two paragraphs are genuinely durable — the "debugging with incorrect information" meta-lesson and the cliff-effect-vs-smooth-gradient note — and deserve lifting into a new doc rather than recovering this one |
| `session_observations_2025-10-28.md` | Dated session log; its durable content is already covered above |
| `episode_1_hospital_bankruptcy.md` | Real lesson, but the most factually corrupt file in the set — it claims an affordability check in action masking that does not exist, in a universe (Hospital, $15, $30 starting capital) that was never shipped |
| `README.md` | Superseded by this index |

## Related

- `CLAUDE.md` §"Development Philosophy" — why interesting failures are preserved
- `docs/config-schemas/drive_as_code.md` — the reward vocabulary these lessons argue about
- `docs/product/vision.md` — the product framing
