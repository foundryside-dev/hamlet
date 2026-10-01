# Truthful Episode Lanes Implementation Plan

> **For the implementing agent:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task by task. Use systematic-debugging on a failed witness and verification-before-completion for acceptance.

**Goal:** Make eligible experience, once-only completion and published outcomes agree with authored episode events, satisfying every criterion of PRD-0005.

**Architecture:** The environment publishes transition eligibility and new terminal/retirement events. Population owns per-lane completion and snapshots; runner consumes them for truthful sinks and explicitly closes surviving lanes on a caller stop. Replay `dones` retains MDP-terminal meaning, while a runner truncation closes the episode without suppressing successor bootstrap.

**Tech Stack:** Python 3.13, locked PyTorch 2.11, Pydantic/YAML compiler, vectorized tensors, SQLite, TensorBoard, msgpack/LZ4 recording and pytest.

**Prerequisites:**

- Approved product contract: `docs/product/prds/0005-truthful-episode-lanes.md`, PDR-0157/0158; planning `hamlet-87d3ef8e23`, engine bug `hamlet-d6fc84d147`.
- Source inspected and probed: `ec463fdaaa632e4e1f778b938ace94f53a73a745`, branch `fix/episode-lane-accounting`. Runtime source is identical to merged main `95b2f828`; intervening changes are product documentation.
- Read `AGENTS.md`, `CLAUDE.md`, and `docs/product/evidence/episode-lanes/planning/receipt.md`. There is zero backwards compatibility: reject incompatible artifacts, retain historical files, create fresh run paths, never migrate or delete old databases.
- Use a clean execution worktree and its own environment: `uv sync --extra dev --extra recording --locked`. No symlinks to the primary `.venv`, silent main-environment rebuild or unrelated cleanup. Verify `import townlet` points at that worktree.
- Tool startup: Filigree session context, atomic work claim for the execution handoff; fresh Loomweave index before structural queries. Claim planning only if resuming an unfinished planning ticket; do not close the bug on a plan.
- Before the first runtime edit, retain the exact parent capture in E0. Planning probes are feasibility/defect evidence, not candidate qualification. Existing prerequisite gate passed 20 tests with one existing stochastic-affordance skip in 58.42 s; no new full suite or convergence run has occurred.

---

## Contract resolved by planning

| Surface | Required behavior |
| --- | --- |
| Eligible row | Lane active on entry; its death/retirement transition remains eligible. Later sticky-done rows are excluded. |
| Required environment events | `active_on_entry`, `newly_terminal`, `newly_retired`: bool tensors of shape `[num_agents]`, on the environment device, owned snapshots. `step_counts` remains required and frozen after completion. |
| Authored death / retirement | Actual replay `done=True`. Death wins coincidence; genuine retirement receives exactly one +1 bonus and preserves its final live DAC reward. |
| Caller cap / budget / shutdown / checkpoint cut | Close a nonempty surviving lane once with explicit reason; do not fabricate a transition or turn its final replay `done` into true. Bootstrap uses the stored successor. |
| Completion ownership | Population owns eligibility, event snapshots and adaptive completion history. Runner publishes the snapshots and invokes its existing curriculum batch-completion route once. |
| Final outcomes | Own CPU clones of final observation/meters; accrued totals and per-lane action/recording contributions freeze. Shared simulation slots and valid shared learner updates may continue. |
| Reset | Reset this package's counters, completed flags/outcomes, recurrent containers and rollout hidden state. No partial lane auto-reset. |
| Default runner cap | It equals configured environment lifespan today. Reaching that boundary is retirement, not a new truncation rule. A lower caller horizon is tested through explicit population completion; budget six exercises a reachable runner truncation. |
| Checkpoint contract | Learned-state resume at a fresh episode, not exact mid-episode continuation. Preserve existing checkpoint cut with an explicit reason; repeated flush is inert. Population format 5→6 rejects contaminated learned artifacts before mutation. Outer format 6 and replay formats remain unchanged because their payload/MDP semantics stay unchanged; validate nested version in training and serving. |
| Persistence contract | Slot-0 DB survival remains slot-0. Add explicit batch vector ticks, live transitions and completion reason. Recording format 1→2 requires completion reason. Existing incompatible files are retained and refused, not reinterpreted. |

Do not change Q train frequency or PER beta from vector ticks to transitions. Target synchronization counts optimizer updates; epsilon decays once per batch episode. Adaptive history advances once per lane completion. RND predictor cadence follows eligible sample occupancy, so removing phantom samples intentionally changes its update timing. `RND.step_counter` is unused and is not an acceptance clock. Correct any contrary target-frequency documentation in `docs/config-schemas/brain.md`, without changing scheduling policy.

Scope excludes effect reset, item/cache ownership, RNG isolation, warmup redesign, general schedule redesign, checkpoint atomicity, UI design, BAC, Murk and convergence. If ordinary recorder shutdown loses the required acceptance artifact, or another excluded seam proves a dependency, retain the failure and amend scope in a PDR before implementation there. Waiting in a probe is not a product repair.

## Delivery order and acceptance custody

Execute E0 before source changes, then E1→E2→E3→P1→P2→P3→S1→S2→S3→S4, followed by E4 and F. E2/E3/P1 establish a usable environment/population tracer before sink work; do not defer all integration to the last task. Intermediate commits can leave enclosing tests red only for explicitly planned required-interface caller updates; record that state and complete the dependent task before proposing a candidate.

The plan contains proposed new symbols/files; they are labelled as creations. Existing source anchors are navigation hints at `ec463fda`, not stable line APIs. Reviewers check the complete diff and production callers against the final candidate. Commit only task files; never `git add .`.


## Environment, authored fixture and baseline attribution

This section proposes implementation; no runtime change is accepted by this plan.
Source anchors are primary `ec463fdaaa632e4e1f778b938ace94f53a73a745`, whose runtime matches PRD baseline `95b2f828`.
Use the actual clean implementation parent for new baseline receipts; do not substitute the historical 4,277-test receipt.

### E0. Bank the clean parent before adding tests, scripts, fixtures or runtime edits

Files read: `scripts/check_epistemic_access.py`, `src/townlet/oracle/driver.py`, `src/townlet/oracle/trace_io.py`, `src/townlet/oracle/harness.py`, `src/townlet/oracle/matrix.py`.
Retain outputs under `runs/episode-lanes/2026-10-02/implementation/parent/`, outside Git.
Run from the implementation worktree using its own valid interpreter and explicit source import root:

```bash
PYTHONPATH="$PWD/src" .venv/bin/python -P scripts/check_epistemic_access.py capture \
  --output runs/episode-lanes/2026-10-02/implementation/parent/static-access
```

This existing capture banks 31 inherited compiler inventories, ten CPU traces, eleven reset recipes and all committed config bytes.
Its manifest must name the full clean parent SHA, actual imported source root and artifact digests.
`capture` refuses execution-bearing dirty/untracked files; perform it before E1.
Retain source identity and reset outputs, including completed-lane counters, from the scoped lifecycle collector described in E1.
Also retain the existing planning probes without claiming they are implementation-parent captures.
No source commit occurs in E0; record command, exit status and digests in the eventual verification receipt.

The retained planning oracle probe ran successfully with:

```bash
PYTHONPATH=/home/john/hamlet/.oracle/oracle-2026-08-17/src \
  .venv/bin/python -P runs/episode-lanes/2026-10-02/planning/oracle-lanes-probe.py
```

It imported `.oracle/oracle-2026-08-17/src/townlet/__init__.py`, SHA `4222a9176e68e232a0e46c7004183440e27f22c3`.
It compiled untouched `oracle_fixtures/configs/default_curriculum` with `use_cache=False`.
All 33 frozen files remained byte-identical; inventory digest `b18d933c1f17b8bfcc997531cd8d4e20d18ab8ad552d7fc44fad2f6877db6171`.
Controlled fixture differences were initial energy `[.015,.045]` in both cases and only a runtime lifespan override `1000 -> 5` in the second.
No frozen config, metadata, worktree or matrix entry was edited.
Both cases reported survival `[5,5]` versus independently counted `[2,5]`; lifespan five produced tick-five rewards `[1,1]`.
Oracle script/log SHA-256 are respectively `dd09937a41690cb0710f02f6031ead389c3a291aabac1a511461acf88bc4addd` and
`ba9ab2526e4bef2a9ebc8c5f2a09d9e217a72b1bf9b0fcebc18165308a1c9fba`.
This proves the old bug; it does not itself qualify a future divergence.

### E1. Commit the authored lifecycle instrument and its failing product assertions

New files: `configs/test/episode_lanes/{experiment,stratum,environment,actions,brain,effects,variables,items}.yaml`;
`configs/test/episode_lanes/levels/L0_test/{bars,affordances,curriculum,drive,training}.yaml`.
Copy the complete existing single-level `configs/test/model_config` skeleton; rename experiment metadata to describe the witness.
Keep its supported compiled feedforward `brain.yaml`; never replace it with the stale architecture name `mlp`.
Add this supported custom action to `actions.yaml`, and add `END_LANE` to the selected level's `training.enabled_actions.custom`:

```yaml
- name: END_LANE
  description: Deterministic lifecycle witness
  enabled_by_default: true
  writes:
    - variable_id: energy
      expression: "0.0"
      condition: null
      composition: overwrite
      phase: apply_action_effects
      priority: 0
      clamp: null
      telemetry_label: end_lane
```

Existing support: bar targets in `tests/test_townlet/unit/vfs/test_vtc_action_writes.py:128`;
compiled lethal bounds in `src/townlet/vfs/vtc.py:2783` and `VTCTerminalConditionProgram.apply` at `:1427`.
Do not add a new terminal declaration language, agent index expression or runtime meter injection for this authoring witness.
Compile the new fixture with `UniverseCompiler.compile(..., primary_level="L0_test", use_cache=False)`.
Construct `VectorizedPopulation` from `universe.brain` or its normal `apply_training_overrides` result.
Select a recorded schedule through the normal exploration-selection seam while executing real brain forwards:
`[WAIT,WAIT]`, `[END_LANE,WAIT]`, `[WAIT,WAIT]`, `[WAIT,WAIT]`, `[WAIT,END_LANE]`.
Assert initial energy is authored and equal for both lanes; derive action IDs from the compiled action space.
The planning probe verified this exact mechanism on copied shipped `default_curriculum/L0_0_minimal`, with compiled feedforward layers `[256,128]`.
Qualification of the new compact committed fixture is still required; do not claim that unexecuted copy is already proven.

New tests: `tests/test_townlet/regressions/test_episode_lane_environment.py` and
`tests/test_townlet/integration/test_authored_episode_lanes.py`.
RED: retain current `[5,5]` readings as discovery evidence, then assert required `[2,5]`, seven live transitions and five world ticks.
Require exactly one terminal event per lane and the terminal transition itself; no fixture-only state injection satisfies the integration assertion.
Exercise lane order reversal, a single lane, simultaneous endings and unequal endings.
Use a copied training config with lifespan five for authored-death/lifespan coincidence and a no-END_LANE healthy retirement case.
GREEN for the instrument means compile/construction and independent event enumeration work, not that the runtime repair passes.
Commit fixture, collector and regression tests separately as `test(episodes): add authored lane and attribution witnesses`.

New scoped tool: `scripts/check_episode_lanes.py`; tool tests: `tests/test_townlet/unit/oracle/test_episode_lane_comparator.py`.
Use a subprocess producer with explicit source/config roots, full revision, seed, action stream and recipe version in its manifest.
Its direct-parent producer must run against the preserved parent code with exactly the same authored config bytes and recorded actions.
Capture independent active-on-entry/new-terminal events from pre/post sticky dones so the old side needs no new product API.
Record the absence of new info keys in the parent receipt; candidate keys are mandatory, not a fallback alias.
Capture per-tick counts, global ticks, rewards/components, completion causes, admitted row identities and reset readings.
Keep consumer-specific learner/RND evidence in the population tasks; the tool must identify its measured fields explicitly.
Before runtime edits, declare exact expected differences below and prove the comparator rejects altered undesignated readings.
This tool does not replace or broaden `check_epistemic_access.py`'s unchanged-stream contract.

### E2. Fix authoritative environment counting and one-shot terminal classification

Edit only `src/townlet/environment/vectorized_env.py` for this atomic runtime step.
Current source: capture `prev_dones` at `:1068`; VTC terminals at `:1175`; unmasked counts at `:1178`;
retirement at `:1194`; bonus at `:1198`; delayed-agent cancellation at `:1203`.
Use one authoritative entry mask and publish required clones in `info`; keep public sticky `dones` behavior.

```python
prev_dones = self.dones.clone()
active_on_entry = ~prev_dones
# Existing action, VTC, effect and expression phases retain their placement.
self._apply_vtc_terminal_conditions()
authored_terminal = active_on_entry & self.dones
self.step_counts += active_on_entry.to(dtype=self.step_counts.dtype)
self.global_tick += 1
# Existing item aging/respawn placement remains here.
newly_retired = (
    active_on_entry
    & ~authored_terminal
    & (self.step_counts >= self.agent_lifespan)
)
# Retain the existing reward call timing; E3 adds row eligibility/components.
rewards = self._reward_calculator._calculate_shaped_rewards()
rewards = torch.where(newly_retired, rewards + 1.0, rewards)
self.dones = self.dones | newly_retired
newly_terminal = authored_terminal | newly_retired
```

Publish `info["active_on_entry"]`, `info["newly_terminal"]`, `info["newly_retired"]` as cloned boolean tensors.
Population consumes these keys directly and derives retirement versus authored termination; it must not reconstruct events from sticky dones.
Use this same `newly_terminal` for delayed-agent cancellation, replacing the separately reconstructed mask.
Never count using post-step `~self.dones`: that loses the legitimate ending transition.
RED: tick three currently reports `[3,3]`; the first lane must already remain at two.
GREEN: deaths at two/five retain `[2,5]`; tick-two/tick-five new-terminal masks are `[True,False]`/`[False,True]`.
The lifespan-five death fixture has `newly_retired=[False,False]` on every step; genuine healthy retirement sets it once.
Keep `global_tick` advancing once per vector tick. Do not repurpose it into summed live transitions.
Do not suspend all dead-agent meter/effect/shared-world activity in this task; capture completed outcomes by value downstream.
Commit as `fix(env): count eligible lanes and classify terminal events once` after the affected runtime tests pass.

### E3. Keep canonical reward components and eligibility aligned

Files: `src/townlet/environment/reward_calculator.py`, `src/townlet/environment/vectorized_env.py`;
update direct tests in `tests/test_townlet/unit/environment/{test_reward_calculator,test_vectorized_env}.py` and
`tests/test_townlet/performance/test_environment_step_benchmarks.py` for the required argument.
The environment's existing `_calculate_shaped_rewards` forwarding method at `vectorized_env.py:1361` gets the same required argument.
No default entry mask, legacy signature or whole-batch normalization fallback is allowed.

```python
# RewardCalculator and the environment forwarding method:
def _calculate_shaped_rewards(self, *, active_on_entry: torch.Tensor) -> torch.Tensor:
    env = self._env
    intrinsic_raw = torch.zeros(env.num_agents, device=env.device)
    if env.exploration_module is not None and bool(active_on_entry.any()):
        observations = env._get_observations()
        intrinsic_raw[active_on_entry] = env.exploration_module.compute_intrinsic_rewards(
            observations[active_on_entry], update_stats=True
        )
    # Existing VTC/DAC apply call retains its context, timing and full lane shape.
```

Keep `ExplorationStrategy.compute_intrinsic_rewards(observations, update_stats)` unchanged.
The calculator selects eligible rows and scatters results; RND owns no second lifecycle mask.
Guard the empty selected batch before normalization. Include newly dying/retiring rows because they were active on entry.
Perform the existing DAC calculation before retirement is ORed into `self.dones`, preserving genuine retirement's final shaped reward.
After that calculation and before publishing components, account the retirement reward exactly once:

```python
rewards = self._reward_calculator._calculate_shaped_rewards(active_on_entry=active_on_entry)
bonus = newly_retired.to(dtype=rewards.dtype)
components = self._last_reward_components
components["extrinsic"] = components["extrinsic"] + bonus
rewards = rewards + bonus
rewards = torch.where(active_on_entry, rewards, torch.zeros_like(rewards))
for name, component in components.items():
    components[name] = torch.where(active_on_entry, component, torch.zeros_like(component))
self.intrinsic_weights = torch.where(active_on_entry, self.intrinsic_weights, torch.zeros_like(self.intrinsic_weights))
```

`extrinsic`, `intrinsic`, `shaping` remain the composed reward contributors; `intrinsic_raw` remains diagnostic.
Do not introduce an undocumented fifth component or leave total reward one above its canonical component sum.
Preserve `time_of_day`'s update after reward calculation (`vectorized_env.py:1208–1212`) and the existing global tick write point.
RED: lifespan-five early-dead and coincident-death rows currently receive one each; candidate must give `[0,0]` at tick five.
RED: existing retirement total/components differ by one; candidate extrinsic component and total both include one bonus.
GREEN: genuine retirement gets final live DAC reward plus exactly one bonus, and total equals extrinsic+intrinsic+shaping.
Use record-only exploration spies with identifiable rows to assert normalization batches `[2,2,1,1,1]`, totaling seven.
Assert dead rows have zero published contributions and an all-completed extra step ingests no novelty observations.
Run real RND updates later in population qualification; these calculator spies alone do not satisfy PRD learner acceptance.
Commit as `fix(rewards): compose retirement once from eligible lane experience`.

### E4. Qualify exact baseline differences and reject misleading controls

The scoped comparator must retain every concrete changed reading, not just permit a field or stream to differ.
For the two/five witness, old count trajectories are `[1,1],[2,2],[3,3],[4,4],[5,5]`;
candidate trajectories are `[1,1],[2,2],[2,3],[2,4],[2,5]`.
Both sides retain world ticks one through five, the exact scripted actions and sticky done trajectory.
For the controlled passive-energy lifespan-five case, expected terminal reward change is only tick-five `[1,1] -> [0,0]`.
For genuine healthy retirement, total reward stays unchanged; extrinsic component gains the existing single retirement contribution.
These unchanged-live-reward expectations apply to the controlled environment recipe with exploration disabled. With RND/adaptive exploration, selecting eligible normalization samples intentionally changes RMS variance and may change subsequent valid survivor rewards; once-only adaptive completion can also change effective weights. Such full-population numerical changes require a preregistered recipe/coordinate contract, independent eligible-row normalization/composition reference and exact measured old/new causal-commit receipts. Do not apply no-exploration equality to them, or exempt an entire reward stream. No live-lane meter, temporal phase, action or input change is implicitly authorized by these expectations.
The full population qualification separately names expected replay/RND/history changes and exact sample identities.
Reset across two episodes must restore this package's eligibility/counters/accumulation; unrelated effect reset remains separately scoped.

Run the inherited static-access comparison on the clean candidate:

```bash
PYTHONPATH="$PWD/src" .venv/bin/python -P scripts/check_epistemic_access.py compare \
  --before runs/episode-lanes/2026-10-02/implementation/parent/static-access \
  --output runs/episode-lanes/2026-10-02/implementation/candidate/static-access \
  --attributions runs/episode-lanes/2026-10-02/implementation/attributions.json
```

Supply `{"entries": []}` when no inherited identities move; never fabricate a DIV reference to satisfy this gate.
Record new fixture input paths explicitly in `after-inputs.json`; historical/frozen config bytes remain untouched.
Inherited streams and resets must stay exact; this tool cannot excuse intended reward output changes with hash attributions.
If an inherited recipe observes a legitimate terminal difference, record the failure and adjudicate it through the scoped comparator/PDR.
Do not weaken its unchanged-stream contract or make its failure disappear through broad allowances.
Run the frozen standing harness normally (`.venv/bin/python -m townlet.oracle.harness --scripted`) without re-freezing inputs.
Format-four oracle traces store obs/rewards/dones/actions and hashes, not survival, replay, RND or completion history.
Default matrix cells run 100 ticks; a passing matrix does not qualify a configured 1000-tick retirement boundary.
Preserve the pinned-oracle controlled lifecycle receipt alongside the direct-parent comparator for that blind spot.
Do not widen existing matrix/register allowances; any new intended divergence needs exact attribution and owner process first.

Comparator negative controls must fail when: a terminal step is dropped; counts are correct only in aggregate;
one retirement bonus survives on an earlier death; one live reward/action/clock/reset reading is changed;
or a proposed allowance is unused/stale. Population controls must additionally catch repeated completion and phantom samples.
Target comparisons must catch zero bootstrap on a runner-truncated row and nonzero bootstrap on actual death/retirement.
Normal `training_loop.max_steps_per_episode` is also `env.agent_lifespan` (`vectorized_env.py:144`), so reaching that ordinary bound is retirement.
Only a lower caller cap, live-transition budget stop or shutdown before lifespan qualifies the separate truncation test.
Use the last valid successor and replay done=False; do not invent a terminal transition just to close the runner episode.
Commit final retained verification summaries only after these controls and package-wide gates pass; no convergence claim follows.


## Population, replay, exploration and checkpoint work

Baseline: `ec463fdaaa632e4e1f778b938ace94f53a73a745`; required environment
info fields from the preceding task are `active_on_entry`, `newly_terminal`,
`newly_retired`. Keep actual MDP termination in replay `dones`; an external
cap/budget/checkpoint cut closes an episode without changing its last `done`.
Truncations bootstrap; authored termination and retirement do not. This follows
[Gymnasium time-limit semantics](https://gymnasium.farama.org/tutorials/gymnasium_basics/handling_time_limits/).

### Task P1 — Admit eligible experience and complete each lane once

Files: create `src/townlet/training/episode.py` for shared completion reason types and the outcome dataclass; modify `src/townlet/population/vectorized.py`, `src/townlet/demo/runner.py`,
`tests/test_townlet/regressions/test_episode_lane_population.py` (new),
`tests/test_townlet/unit/population/test_recurrent_training.py`,
`tests/test_townlet/unit/demo/test_runner_seeding.py`, `tests/test_townlet/integration/test_training_loop.py`.

1. RED: add a standard/PER/recurrent regression using the shared authored fixture
   and existing `VectorizedPopulation` constructor. Pass all constructor arguments:
   `env`, `curriculum`, `exploration`, `agent_ids`, `device`, `brain_config`,
   `obs_dim`, `action_dim`, `train_frequency=1`, `batch_size=128`,
   `sequence_length=1`, `max_grad_norm=1.0`. Use `StaticCurriculum(1.0)` and
   `AdaptiveIntrinsicExploration(obs_dim=env.observation_dim,
   rnd_training_batch_size=128, device=torch.device("cpu"))`.
   The authored fixture must use supported compiled brain construction; existing
   `minimal_brain_config`/`recurrent_brain_config` fixtures remain appropriate for
   unit variants. PER uses a validated replay config with prioritized=True,
   alpha=.6, beta=.4, beta_annealing=False; recurrent+PER remains unsupported.
2. Assert exact 2/5 survival, seven replay transitions, two terminal rows,
   recurrent lengths `[2,5]`, two finalizations/history entries and registry
   `[2,5]`. Spy on finalization while invoking the original method. Add reversed
   lanes, simultaneous endings, one lane and two consecutive batch episodes.
3. Run `.venv/bin/pytest -q --no-cov tests/test_townlet/regressions/test_episode_lane_population.py`.
   Retain RED failures; the parent stores ten transitions and phantom episodes.
4. GREEN: implement the following state and replacement blocks. Keep the existing
   optimizer/update block and its relative ordering. Required masks are consumed
   directly; no legacy readers, hidden defaults or `.get` mask fallbacks.

```python
CompletionReason = Literal[
    "authored_terminal", "retirement", "cap", "budget", "shutdown", "checkpoint"
]
RunnerCompletionReason = Literal["cap", "budget", "shutdown", "checkpoint"]

@dataclass(frozen=True)
class EpisodeCompletion:
    agent_idx: int
    reason: CompletionReason
    survival_time: int
    final_observation: torch.Tensor
    final_meters: torch.Tensor
```

Add imports and initialize the transient fields below. Reality check at ec463fda
and in the planning worktree: neither VectorizedPopulation nor PopulationManager
declares `__slots__`; these assignments use the existing instance dictionary.
Do not introduce a new slot declaration. RewardTensor's slots are unrelated.

```python
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal, cast
```

```python
self.episode_completed = torch.zeros(self.num_agents, dtype=torch.bool, device=self.device)
self.episode_completions: list[EpisodeCompletion | None] = [None for _ in range(self.num_agents)]
```

Before the existing `env.reset()` add a guard; refusal must happen before any environment/counter/registry/hidden mutation:

```python
pending = (self.episode_step_counts > 0) & ~self.episode_completed
if bool(pending.any()):
    raise RuntimeError("Complete pending lanes with an explicit stop reason before reset")
```

Update short-horizon callers in `tests/test_townlet/integration/test_training_loop.py` (current lines302–305,380–384,578–585) and every real early-reset caller to flush nonempty surviving lanes with reason="cap" before reset. Empty/repeated resets stay inert. Add regression assertions that a rejected early reset preserves observations, environment tensors, pending replay sequences, counters, adaptive history, registry and hidden state byte-for-byte. A successful cap completion retains done=False and then permits reset.

Extend `reset` after the existing `env.reset()` and retain exploration sync:

```python
self.episode_step_counts.zero_()
self.episode_completed.zero_()
self.episode_completions = [None for _ in range(self.num_agents)]
if self.is_recurrent:
    self.current_episodes = [self._new_episode_container() for _ in range(self.num_agents)]
    recurrent_network = cast(RecurrentTokenQNetwork, self.q_network)
    self.rollout_hidden = recurrent_network.initial_hidden(self.num_agents, self.device)
for agent_idx in range(self.num_agents):
    self.runtime_registry.record_survival_time(agent_idx=agent_idx, steps=0)
```

At `step_population` entry, before the forward pass:

```python
if bool(self.episode_completed.all()):
    raise RuntimeError("Population episode is complete; call reset before stepping.")
active_on_entry = ~envs.dones.clone()
if bool((active_on_entry & self.episode_completed).any()):
    raise RuntimeError("A completed population lane cannot enter another transition.")
```

Do not advance inactive recurrent rollout memory. Preserve the current full-batch Q-value interface to adversarial curriculum; zero placeholder Q rows would introduce a new entropy/difficulty behavior. Evaluate the existing full forward, then restore inactive hidden rows:

```python
assert self.rollout_hidden is not None
recurrent_network = cast(RecurrentTokenQNetwork, self.q_network)
h, c = self.rollout_hidden
inactive_h = h[:, ~active_on_entry, :].clone()
inactive_c = c[:, ~active_on_entry, :].clone()
q_sequence, (next_h, next_c) = recurrent_network(self.current_obs.unsqueeze(1), (h, c))
next_h[:, ~active_on_entry, :] = inactive_h
next_c[:, ~active_on_entry, :] = inactive_c
self.rollout_hidden = (next_h, next_c)
q_values = q_sequence[:, 0, :]
```

The terminal row is still active for its final forward, then completion zeroes its hidden state. Add a fixed-model unequal-ending adversarial-curriculum witness in `tests/test_townlet/regressions/test_episode_lane_population.py`, using `tests/test_townlet/unit/curriculum/test_curriculums.py` construction patterns. Record Q values, entropy, selected depletion multiplier, stage changes and live-lane actions before/after the seam. Preserve existing full Q rows and decision ordering; no zero-dead-Q placeholder, compacted agent IDs or new shared-difficulty selection policy. Assert completed hidden rows stay zero across later ticks while active hidden rows advance. Exact unexpected live-output changes require source-backed attribution and scope review before accepting; do not hide them behind the StaticCurriculum witness.

After stepping, read `active_on_entry = info["active_on_entry"]`,
`newly_terminal = info["newly_terminal"]`, `newly_retired = info["newly_retired"]`,
and `components = info["reward_components"]`. For standard/PER admission:

```python
eligible_rewards = RewardTensor.from_dac(
    total=rewards[active_on_entry],
    extrinsic=components["extrinsic"][active_on_entry],
    intrinsic=components["intrinsic"][active_on_entry],
    shaping=components["shaping"][active_on_entry],
)
self.replay_buffer.push(
    observations=self.current_obs[active_on_entry], actions=actions[active_on_entry],
    rewards=eligible_rewards, next_observations=next_obs[active_on_entry],
    dones=dones[active_on_entry],
)
```

For recurrent admission preserve every existing field, but iterate eligible rows:

```python
for agent_idx in torch.nonzero(active_on_entry, as_tuple=False).flatten().tolist():
    episode = self.current_episodes[agent_idx]
    episode["observations"].append(self.current_obs[agent_idx].detach().cpu().clone())
    episode["actions"].append(actions[agent_idx].detach().cpu().clone())
    episode["rewards"].append(rewards[agent_idx].detach().cpu().clone())
    episode["rewards_extrinsic"].append(components["extrinsic"][agent_idx].detach().cpu().clone())
    episode["rewards_intrinsic"].append(components["intrinsic"][agent_idx].detach().cpu().clone())
    episode["rewards_shaping"].append(components["shaping"][agent_idx].detach().cpu().clone())
    episode["dones"].append(dones[agent_idx].detach().cpu().clone())
    episode["next_observations"].append(next_obs[agent_idx].detach().cpu().clone())
```

Compute logging novelty and ingest predictor observations only from eligible rows:

```python
intrinsic_rewards = torch.zeros_like(rewards)
if isinstance(self.exploration, RNDExploration | AdaptiveIntrinsicExploration):
    intrinsic_rewards[active_on_entry] = self.exploration.compute_intrinsic_rewards(
        self.current_obs[active_on_entry], update_stats=False
    )
    rnd = self.exploration.rnd if isinstance(self.exploration, AdaptiveIntrinsicExploration) else self.exploration
    rnd.obs_buffer.extend(row.detach().cpu().clone() for row in self.current_obs[active_on_entry])
    self.last_rnd_loss = rnd.update_predictor()
```

Keep exploration APIs unchanged: eligibility is selected by their lifecycle
callers. The environment task similarly selects/scatters eligible observations
for normalization with update_stats=True; it must not pass terminal masks after
the step, which would omit genuine final transitions.

After existing learning, replace the current counter/finalization block:

```python
self.current_obs = next_obs
self.episode_step_counts += active_on_entry.long()
new_completions = []
for agent_idx in torch.nonzero(newly_terminal, as_tuple=False).flatten().tolist():
    reason: CompletionReason = "retirement" if bool(newly_retired[agent_idx]) else "authored_terminal"
    completion = self._finalize_episode(agent_idx, reason)
    if completion is not None:
        new_completions.append(completion)
info["episode_completions"] = tuple(new_completions)
```

Replace finalization and flush; do not zero survival counts until reset:

```python
def _finalize_episode(self, agent_idx: int, reason: CompletionReason) -> EpisodeCompletion | None:
    if bool(self.episode_completed[agent_idx]):
        return None
    survival_time = int(self.episode_step_counts[agent_idx].item())
    if survival_time == 0:
        return None
    if self.is_recurrent and not self._store_episode_and_reset(agent_idx):
        raise RuntimeError("A nonempty episode lost its recurrent transitions.")
    completion = EpisodeCompletion(
        agent_idx=agent_idx, reason=reason, survival_time=survival_time,
        final_observation=self.current_obs[agent_idx].detach().cpu().clone(),
        final_meters=self.env.meters[agent_idx].detach().cpu().clone(),
    )
    self.episode_completed[agent_idx] = True
    self.episode_completions[agent_idx] = completion
    self.runtime_registry.record_survival_time(agent_idx=agent_idx, steps=survival_time)
    if isinstance(self.exploration, AdaptiveIntrinsicExploration):
        self.exploration.update_on_episode_end(survival_time=survival_time)
    self.sync_exploration_metrics()
    self._reset_hidden_state(agent_idx)
    return completion

def flush_episode(self, agent_idx: int, reason: RunnerCompletionReason) -> EpisodeCompletion | None:
    return self._finalize_episode(agent_idx, reason)
```

5. Remove the terminal-successor-is-post-reset comment. Update every flush caller
   immediately with explicit reasons: runner cap/budget/shutdown before publication;
   `DemoRunner.flush_all_agents` uses reason="checkpoint". Keep empty/already-complete
   calls inert. Update the synthetic flush signature in unit/demo/test_runner_seeding.py.
   This caller update is atomic with P1, not deferred until a later broken commit.
6. Add cap/budget/duplicate-checkpoint tests; final replay done stays False for
   truncations. Snapshot tensors use clones so later mutable slots cannot revise outcomes.
7. GREEN commands: run the new module plus unit/population/test_recurrent_training.py,
   unit/population/test_runtime_registry.py, unit/demo/test_runner_seeding.py and integration/test_training_loop.py with
   `.venv/bin/pytest -q --no-cov`. Then stage only P1's files and commit:

```bash
.venv/bin/pytest --no-cov -q tests/test_townlet/regressions/test_episode_lane_population.py tests/test_townlet/unit/population/test_recurrent_training.py tests/test_townlet/unit/population/test_runtime_registry.py tests/test_townlet/unit/demo/test_runner_seeding.py tests/test_townlet/integration/test_training_loop.py
git add src/townlet/training/episode.py src/townlet/population/vectorized.py src/townlet/demo/runner.py \
  tests/test_townlet/regressions/test_episode_lane_population.py \
  tests/test_townlet/unit/population/test_recurrent_training.py \
  tests/test_townlet/unit/demo/test_runner_seeding.py \
  tests/test_townlet/integration/test_training_loop.py
git commit -m "fix(population): admit live lanes and finalize episodes once"
```

### Task P2 — Execute real learner/predictor updates and qualify targets

Files: `tests/test_townlet/regressions/test_episode_lane_learning.py` (new),
`tests/test_townlet/unit/population/test_double_dqn_algorithm.py`,
`tests/test_townlet/unit/training/test_sequential_replay_buffer.py`.

1. RED tests must observe the real training path, not calculate an unused target.
   Use actual replay/population/optimizer with batch_size=2 and train_frequency=1.
   RND training_batch_size=7 admits precisely one fixture batch at tick5. Capture
   SHA256 row identities from independent active-on-entry observation ledgers;
   record both predecessor predictor rows and successor normalization rows.
2. Wrap real replay sample/sample_sequences to record returned observations/dones;
   call the original method. Register an RND predictor forward_pre_hook and record
   rows only when torch.is_grad_enabled() is True. Assert seven predictor inputs,
   no phantom identities, seven RMS samples, actual optimizer calls and changed parameters.
3. Keep a distinct one-episode seven-row ingestion/statistics test. The nine-episode learner witness expects 63 eligible predecessor/predictor-admitted rows and 63 successor normalization samples cumulatively, with per-episode seven; predictor mini-batches and Q sampling may reuse eligible history according to their existing algorithms. Require actual update counts >0 and changed parameters, not a prescribed number of updates.
   Recurrent uses NINE 2-agent 2/5 episodes, or 16 genuine prefilled episodes.
   The eighth corrected batch reaches16 episodes after its final training check;
   the ninth executes learning without changing existing warmup. Include seq_len=1
   (detects one-step phantom negative control) and seq_len=2 (boundary successor).
4. Set target-network parameters to zero, then set the final nn.Linear output bias
   to3.0. Keep online parameters trainable. Capture the actual original loss target:
   a forward_pre_hook for the feedforward nn loss; a wrapper around F.huber_loss or
   F.smooth_l1_loss for PER/recurrent, invoking the original loss. Record sampler rows.
   Terminal target must equal sampled reward; truncation target must equal reward+gamma*3.
   Exercise vanilla and Double DQN. Confirm an optimizer step changes online parameters.
   Require observed terminal rows >0 and truncated boundary rows >0 in distinct update cases; recurrent witnesses must actually sample a window ending at each real boundary. Use controlled sampler RNG or valid predetermined real-buffer indices while invoking the original sampler; never fabricate replacement batches. Reject if a category is empty. Ordinary eligible nonterminal rows remain a third assertion category.
5. Also hook target-network input to prove the stored final successor is evaluated,
   not a reset observation. For recurrent, test the final sampled window position
   for both real termination and truncation; terminal index remains a valid loss row.
6. RED negative controls: post-step eligibility loses terminal rows; missing active
   filtering supplies ghosts; sticky-done finalization repeats completion; marking
   truncation done destroys bootstrap. Require each control to fail its matching assertion.
7. Parent setup is already feasible: /tmp/episode-lane-gradient-setup.py and seq1/seq2
   logs show real updates at ec463fda, not candidate acceptance. seq1 sampled15 phantom
   recurrent Q rows; seq2 excluded one-step ghosts by its sequence-length filter.
8. GREEN: preserve existing Q-target formulas and sequential successor persistence.
   Repair only failures in eligible admission/completion exposed by these tests.
   Run `.venv/bin/pytest -q --no-cov tests/test_townlet/regressions/test_episode_lane_learning.py`
   plus unit/population/test_double_dqn_algorithm.py and unit/training/test_sequential_replay_buffer.py.
   Then stage only P2's files and commit:

```bash
git add src/townlet/population/vectorized.py tests/test_townlet/regressions/test_episode_lane_learning.py tests/test_townlet/unit/population/test_double_dqn_algorithm.py tests/test_townlet/unit/training/test_sequential_replay_buffer.py
git commit -m "test(training): qualify episode eligibility and truncation targets"
```

### Task P3 — Refuse obsolete learned artifacts without expanding resume

Files: src/townlet/population/vectorized.py; tests/test_townlet/unit/population/test_vectorized_population.py;
tests/test_townlet/integration/test_checkpointing.py; tests/test_townlet/integration/test_live_inference_checkpoint_identity.py.

1. RED: valid outer version6 payload with nested population version5 must refuse
   before network/optimizer/replay/exploration/curriculum/layout/budget mutation in
   DemoRunner and before q_network.load_state_dict in live inference. Preserve a
   valid digest/identity so the assertion exercises nested semantics, not an earlier gate.
2. GREEN: change only POPULATION_CHECKPOINT_FORMAT_VERSION from5 to6. Outer
   CHECKPOINT_FORMAT_VERSION remains6; three replay formats remain unchanged.
   Exact nested validation already runs at runner359 and live_inference467.
3. Update exact version assertions at integration/test_checkpointing.py222,1032 and
   unit/population/test_vectorized_population.py866,1000,1049. Add current-format
   roundtrip and old-format refusal with state snapshots/spies proving no mutation.
4. Keep fresh-episode checkpoint resume: restore learned/replay/curriculum/layout/
   live-budget state, then population.reset. Do not persist new transient completed
   masks, observations, recurrent containers or hidden state. Existing checkpoint
   flush explicitly truncates pending nonempty lanes, and emits no duplicate history.
5. Run `.venv/bin/pytest -q --no-cov` on the four files above plus
   tests/test_townlet/unit/demo/test_runner_seeding.py and
   tests/test_townlet/unit/training/test_token_checkpoint_gates.py.
   Then stage only P3's files and commit:

```bash
git add src/townlet/population/vectorized.py tests/test_townlet/unit/population/test_vectorized_population.py tests/test_townlet/integration/test_checkpointing.py tests/test_townlet/integration/test_live_inference_checkpoint_identity.py
git commit -m "fix(checkpoint): reject pre-episode-lane population state"
```

Scheduling invariants: total_steps/train_frequency and PER-beta numerator/horizon
retain vector-step units; target synchronization retains optimizer-update units;
epsilon decays once per batch episode; adaptive annealing checks once per lane
completion; predictor cadence follows eligible sample ingestion. RND.step_counter
is unused. Correct docs/config-schemas/brain.md's target-frequency "episodes" wording
to training updates; do not redesign schedules or change the warmup policy.


## Runner, durable sinks, schema and exporters

Planning baseline: `ec463fdaaa632e4e1f778b938ace94f53a73a745`.
These tasks depend on the environment/population lifecycle and completion-snapshot tasks.
They are instructions for later execution, not implementation performed by this checkpoint.
Use the shared completion reason vocabulary from that lifecycle contract; add no parallel enum.

### Evidence and invariants

Retained discovery: `runs/episode-lanes/2026-10-02/planning/runner-sinks/`.
`receipt.json` records source identity, hashes, copied paths and probe limitations.
Two real episodes contain 14 eligible transitions; DB/TB report survival `[5,5]` each.
Recording slot 0 contains five rows, with dones `[False,True,True,True,True]`.
A real budget-six stop at vector tick four has true survival `[2,4]`, published `[4,4]`.
The baseline exporter reports 20 and eight transitions, instead of 14 and six.
The regression exporter already preserves the correct checkpoint-backed transition count.
CPU terminal health `.9900000095` changes to published `.9750000238` through an aliased capture.
The probe suppressed gradients and waited for the actual writer file before cleanup.
It proves sink defects; it does not qualify ordinary recorder shutdown or candidate acceptance.

Keep `DemoRunner.completed_live_agent_steps`: it already counts active-on-entry lanes.
One environment terminal step counts; later sticky terminal flags are not new experience.
Population owns once-only completion and frozen snapshots; runner consumes them before reset.
Retain one curriculum update route at batch completion, with each lane represented once.
An external budget/cap stop finalizes survivors without changing their replay MDP done flags.
The ordinary configured loop cap currently equals environment retirement lifespan.
Qualify a genuinely distinct lower caller cap; do not mislabel retirement as truncation.
DB rows remain slot-0 outcomes plus explicit batch context, not a new per-agent database.

### Task S1 — cut the database and recording artifact contracts atomically

**Files:** modify `src/townlet/demo/database.py`, `src/townlet/demo/runner.py`, `src/townlet/recording/data_structures.py`, `src/townlet/recording/recorder.py`, `src/townlet/recording/replay.py` and `src/townlet/demo/live_inference.py`.
Modify `tests/test_townlet/unit/recording/test_database.py`, `test_data_structures.py`, `test_recorder.py`, `test_criteria.py`; `tests/test_townlet/utils/builders.py`; and current recording integration fixtures listed below. All required metadata constructors, format producers/readers and index mappings belong to this foundational cut.
Modify the closed-DB caller in `tests/test_townlet/integration/test_runner_integration.py`.
Add `tests/test_townlet/unit/demo/test_episode_database_schema.py` for the schema cut.

1. RED: add fresh-DB round-trip tests requiring these episode fields:
   - `survival_time`: slot-0 eligible episode length, two in the 2/5 fixture.
   - `batch_episode_steps`: vector ticks for this batch, five in that fixture.
   - `live_agent_transitions`: eligible transitions across lanes, seven in that fixture.
   - `completion_reason`: slot-0 reason from its frozen completion snapshot.
   Keep existing reward, stage, exploration, timestamp and observation identity columns.
2. RED: build an old-layout DB in `tmp_path`; snapshot its bytes, schema and rows.
   Opening it with `DemoDatabase` must reject before journal-mode, DDL or row writes.
   Prove rejection leaves the old artifact unchanged, including no new tables/columns.
   Also reject missing required columns, unsupported schema stamps and malformed layouts.
   A valid current-layout DB reopens normally; this is same-version persistence, not migration.
3. RED: recording-index round-trip keeps `recording_reason='periodic'` and separately stores
   required `completion_reason`; filtering by recording selection reason still uses its own column.
4. Run RED: `.venv/bin/python -m pytest -q --no-cov tests/test_townlet/unit/demo/test_episode_database_schema.py tests/test_townlet/unit/recording/test_database.py`.
   Failures must name absent fields or unsupported-layout acceptance, not fixture construction.
5. GREEN: revise `_create_schema` and initialization ordering in `DemoDatabase`.
   Detect an existing nonempty database through read-only schema/stamp inspection first.
   Validate the exact supported schema before setting WAL mode or applying any DDL.
   Close a rejected connection cleanly without changing journal mode or creating sidecar files.
   Fresh databases create the new schema and its explicit current stamp.
   Reject old/incompatible schemas with a clear error; never ALTER, copy, upgrade or delete them.
   Distinguish new empty DB creation from a nonempty artifact whose required tables are absent.
6. GREEN: make the three added batch/context fields required in `insert_episode`.
   Its only production caller is `DemoRunner.run` in `src/townlet/demo/runner.py:724`.
   The only other direct caller is the closed-DB test at `test_runner_integration.py:481`.
   Update that test with explicit new arguments so it still exercises the closed-connection error.
   Add required recording completion reason to the index DDL and `insert_recording` mapping.
   Leave `recording_reason` meaning and filters unchanged; no compatibility reads or defaults.
   In this same atomic task introduce required `EpisodeMetadata.completion_reason`, the shared format2 constant, strict reader validation and observer reason projections. Update all current constructors/success payloads listed in S3 step7 before S1's GREEN gate. The field is frozen/slotted, so no ad-hoc assignment or temporary reason can bridge the change. S3 owns only eligible production collection and ordinary persisted acceptance after this foundation exists.
7. Update the runner insert call to obtain all required values from the lifecycle contract.
   Do not pass temporary dummy values merely to satisfy the signature.
8. Run GREEN: repeat step 4, then `.venv/bin/python -m pytest -q --no-cov tests/test_townlet/integration/test_runner_integration.py`.
   Include strict current-format roundtrip/refusal and constructor tests from S3 in S1's focused gate. Stage only this task's source and test files; inspect the diff and commit:
   `feat(demo): require truthful episode outcome and batch fields`.

### Task S2 — make runner collection consume eligible rows and frozen completions

**Files:** modify `src/townlet/demo/runner.py` and `src/townlet/training/tensorboard_logger.py`.
Add `tests/test_townlet/regressions/test_episode_lane_sinks.py`.
Extend `tests/test_townlet/unit/demo/test_runner_environment_budget.py`.
Extend `tests/test_townlet/integration/test_runner_integration.py` where existing assertions change.

1. RED: build an isolated pack through `config_pack_factory`/config-builder helpers.
   Use real compiler, environment, population, runner, DB and TensorBoard writer.
   Control initial energy for deaths at two/five and select WAIT deterministically.
   Instrument initial state/action selection and curriculum calls; do not replace sink producers.
   Keep Q/RND learning disabled only for this accounting witness, not all package tests.
2. RED: require DB slot-0 survival two, batch ticks five and live transitions seven.
   Read real event files with `EventAccumulator`: per-agent survival must be `[2,5]`.
   Verify totals equal independent eligible-row sums, not a reconstructed expected scalar.
   Collect the real curriculum call and require one `[2,5]` completion batch.
3. RED: retain a clone of lane-zero meters at death, then let lane one continue.
   Published lane-zero final meters must match the tick-two clone, not tick-five live storage.
   Verify final observation/outcome snapshots survive later env mutation and the next reset.
   Reverse lane order and repeat for two consecutive episodes; fresh counters must not accumulate.
4. RED: budget six must yield survival `[2,4]`, batch ticks four and live transitions six.
   Lane zero keeps authored termination; lane one gets the explicit budget truncation reason.
   The surviving last replay row keeps done=False and later snapshot publication is once-only.
   Verify budget zero-work refusal creates no phantom completed episode or empty recording.
   Exercise the separate caller-cap fixture from the lifecycle task, not the retirement threshold.
5. Run RED: `.venv/bin/python -m pytest -q --no-cov tests/test_townlet/regressions/test_episode_lane_sinks.py tests/test_townlet/unit/demo/test_runner_environment_budget.py`.
6. GREEN: use the shared active-on-entry/newly-completed contract in `DemoRunner.run`.
   Keep live budget accounting at lines 585–610; add an episode-local live-transition delta.
   Count actual taken vector steps separately; never infer batch ticks from slot-zero survival.
   Mask reward accumulation, interaction/affordance transitions and custom-action usage.
   Do not count a selected action for a lane already complete on entry.
   Read required canonical masked DAC components for component totals; remove lines 625–634's
   raw-RND/base-weight subtraction, which ignores effective modifiers and composed shaping.
   Preserve the declared component meaning and intended retirement contribution from the reward task.
7. GREEN: consume each population completion snapshot for survival, reason and final outcome.
   Clone captured CPU tensor data with `detach().cpu().clone()`; detach/cpu alone aliases CPU storage.
   Delete `info.get('step_counts', population.episode_step_counts.clone())` at line 700.
   Missing canonical lifecycle/accounting data must fail, not choose a counter fallback.
   On explicit cap/budget stop, request once-only completion of remaining live lanes before reading
   snapshots; already completed lanes retain their original reason and snapshot.
8. GREEN: retain one batch-completion curriculum route and remove any duplicate death route.
   Use truthful snapshot survival values and one completion flag per finished lane.
   Ensure checkpoint `flush_all_agents` cannot complete a lane for a second time.
   Log per-agent TensorBoard outcome values from completed snapshots.
   Publish batch tick/live-transition counters under explicit units, not misleading survival tags.
   Carry canonical per-agent completion reason into episode logging; validate it against the shared
   vocabulary and read the resulting real event payload in the sink witness. Replace survival/reason
   missing-field defaults in the canonical multi-agent caller with required accesses. Update current
   unit `training/test_tensorboard_logger.py` and integration `test_tensorboard_logger.py` callers
   explicitly; a missing lifecycle field must reject instead of publishing zero or a guessed reason.
   Preserve permitted shared learner updates while another lane is live.
9. Run GREEN: repeat step 5, then `.venv/bin/python -m pytest -q --no-cov tests/test_townlet/integration/test_runner_integration.py tests/test_townlet/integration/test_tensorboard_logger.py tests/test_townlet/integration/test_curriculum_signal_purity.py`.
   Commit the scoped source/tests after diff review:
   `fix(demo): publish immutable eligible episode outcomes`.

### Task S3 — qualify eligible slot-zero collection and ordinary persistence

**Files:** modify `src/townlet/recording/data_structures.py`, `recorder.py`, `replay.py`.
Modify `src/townlet/demo/runner.py` and `src/townlet/demo/live_inference.py`.
Extend `tests/test_townlet/regressions/test_episode_lane_sinks.py`.
Extend unit `recording/test_data_structures.py`, `test_recorder.py`, `test_database.py`.
Extend integration `test_recording_recorder.py`, `test_recording_playback.py`,
`test_recording_replay_manager.py`; add observer-projection cases in unit `demo/test_live_inference_unit.py`.

1. RED: ordinary real runner recording at periodic interval one must persist its output file.
   Read the actual SQLite recording row and decompress/unpack the LZ4/msgpack file.
   Require format 2, slot-zero survival two, two eligible rows and one terminal row.
   Require frozen completion reason to agree with DB outcome and recording index.
   Require WAIT usage two, not five; later sticky done ticks contribute no recorded frames.
   Repeat a second episode to detect buffered frames crossing a boundary.
2. RED: recording-selection `recording_reason='periodic'` remains different from completion reason.
   Budget/cap survivor recordings have explicit truncation reasons and no forged MDP terminal flag.
   Require observer replay-loaded and replay-step metadata to forward completion reason.
3. RED: reader refuses format 1, missing/unknown required metadata, invalid reason values/types,
   malformed step payloads and unsupported versions before installing any replay state.
   A failed load must not install a partial episode; preserve the existing explicit failure API.
   Current-format recordings load and preserve their reason without synthesizing a default.
4. Run RED: `.venv/bin/python -m pytest -q --no-cov tests/test_townlet/regressions/test_episode_lane_sinks.py tests/test_townlet/unit/recording/test_data_structures.py tests/test_townlet/integration/test_recording_replay_manager.py`.
5. Foundational ownership in S1: add required `completion_reason` to frozen `EpisodeMetadata` and define one shared current recording format constant with value2 and strict payload validation before S1 GREEN. S3 verifies this already-implemented contract.
   Writer and reader use that constant; remove hard-coded version-1 producers/readers.
   Validate the supported top-level/metadata/step shapes and canonical reason before publishing
   `ReplayManager` state; do not add a version-1 compatibility path or missing-field defaults.
   Keep existing legitimate optional step fields explicit as the current dataclass emits them.
   Choose the existing recording DTO's flat `affordance_layout: dict[str, tuple[int, ...]]` as the format2 contract. Current `env.get_affordance_positions()` returns a checkpoint envelope `{positions, ordering, position_dim}`, which the current runner incorrectly puts in recording metadata; the retained ordinary artifact makes `deserialize_metadata` raise TypeError on integer `position_dim`, and observer projection expects flat positions. S1 must extract and own only `env.get_affordance_positions()["positions"]` for recording metadata/top-level affordances, validating dimension/coordinates before writing. Keep the environment/checkpoint envelope unchanged. Strict format2 reader, deserialize_metadata and all current fixtures must agree on flat named positions. Add ordinary runner artifact → actual ReplayManager.load_episode → observer replay-step integration, not merely unpacking the file and loading a synthetic fixture. This is a direct artifact-boundary prerequisite of strict validation, not a spatial API redesign.
6. GREEN: gate `DemoRunner` recording on slot zero being active on entry.
   Its metadata comes from slot zero's frozen completion; batch-end finish is safe only if no
   post-completion rows were appended and the queued metadata is detached from mutable slots.
   Keep recording-selection reason separate through `RecordingWriter` and `DemoDatabase`.
   Forward completion reason in `LiveInferenceServer` replay-loaded and replay-step projections
   at `live_inference.py:997–1002,1147–1153`; no frontend redesign belongs to this task.
7. S1 must update every current `EpisodeMetadata(...)` constructor before its GREEN gate, explicitly, without defaults. S3 verifies the sweep is complete:
   `src/townlet/demo/runner.py`, `src/townlet/recording/data_structures.py` deserialization;
   `tests/test_townlet/utils/builders.py`;
   unit recording `test_criteria.py`, `test_recorder.py`, `test_database.py`, `test_data_structures.py`;
   integration `test_recording_video_export.py`, `test_recording_replay_manager.py`,
   `test_recording_playback.py`, `test_recording_recorder.py`.
   Replace version-1 handcrafted payloads in current success fixtures with format 2.
   Keep explicit version-1 rejection fixtures, not historical input rewrites.
8. Recorder shutdown is presently unqualified: `shutdown` sets writer.running=False immediately.
   Discovery waited for persistence to isolate accounting; acceptance must exercise ordinary finish
   and cleanup without an injected sleep, polling wrapper or fake writer that conceals lost markers.
   If ordinary persistence fails, retain a failing witness, stop this acceptance task and record the
   evidenced prerequisite/scope amendment. Do not silently absorb general recorder lifecycle repair.
9. Run GREEN: `.venv/bin/python -m pytest -q --no-cov tests/test_townlet/unit/recording tests/test_townlet/integration/test_recording_recorder.py tests/test_townlet/integration/test_recording_playback.py tests/test_townlet/integration/test_recording_replay_manager.py tests/test_townlet/integration/test_recording_video_export.py tests/test_townlet/unit/demo/test_live_inference_unit.py tests/test_townlet/regressions/test_episode_lane_sinks.py`.
   Commit the reviewed scoped changes:
   `fix(recording): persist eligible lane outcomes in format two`.

### Task S4 — export distinct lane, batch and transition units

**Files:** modify `scripts/l2_baseline.py` and `scripts/l2_token_regression.py`.
Extend `tests/test_townlet/unit/scripts/test_l2_baseline.py` and `test_l2_token_regression.py`.
Extend the real sink regression to invoke both exporters against its fresh task DB/event files.

1. RED: extend the SQL fixtures with required episode outcome/batch fields.
   Fixture slot-zero survival two must export as two; batch ticks five must export as five.
   Require per-episode live transitions seven and cumulative fourteen after two fixture episodes.
   Invoke each actual exporter, read its emitted CSV and compare against DB plus real TB events.
   Keep checkpoint `transitions.csv` final-counter and digest verification intact.
2. RED: missing accounting columns/TB disagreement/duplicate lane survival events must reject.
   Missing required counts may not silently become zero, an empty cell or a warning-only export.
   Verify format rejection leaves original input DB/event/checkpoint files untouched.
3. Run RED: `.venv/bin/python -m pytest -q --no-cov tests/test_townlet/unit/scripts/test_l2_baseline.py tests/test_townlet/unit/scripts/test_l2_token_regression.py tests/test_townlet/regressions/test_episode_lane_sinks.py`.
4. GREEN: `l2_token_regression.write_training_curves` reads actual `batch_episode_steps` and explicit
   slot-zero survival/live counts; its existing DB survival-to-batch relabel at lines 379–385 ends.
   Preserve verified-checkpoint cumulative transition artifacts and their identity checks.
   `l2_baseline.cmd_curves` reads explicit live counts and cross-checks per-agent TB survival sums.
   Remove blanket missing-accounting fallback at lines 260–261 and reject inconsistent units.
   Keep established event-directory layout selection; it selects a location, not an old data contract.
5. Update current exporter SQL fixtures and headers; never rewrite historical M4 CSVs/metadata.
   Current executables must refuse incompatible old inputs rather than reinterpret their semantics.
   Read greedy evaluator active-on-entry counters against the new environment contract;
   retain their independent survival counter witness and unchanged historical evaluation evidence.
6. Run GREEN: repeat step 3 and inspect emitted fixture CSVs and the source diff.
   Commit only scripts and affected current tests:
   `fix(eval): export explicit episode accounting units`.

### Negative controls and acceptance handoff

Mutate one freshly generated test artifact at a time, preserving its original witness.
A falsely incremented dead-lane survival must fail DB/TB/event-count reconciliation.
An extra post-terminal recorder row must fail the exact eligible-frame assertion.
An omitted genuine terminal row must fail terminal-row and completion reconciliation.
An aliased CPU final meter must fail the retained tick-two snapshot comparison.
A repeated curriculum completion must fail the per-lane completion-call count.
A renamed survival-to-batch column must fail the unequal-death exporter fixture.
Missing completion reason/version 1 must fail the strict current reader/schema contract.
Before acceptance, read ordinary persisted recorder evidence and all direct consumers at one candidate.
Keep local tests, full-suite gates, integration, hosted delivery and learning as separate readings.
No successful sink fixture establishes convergence, reset isolation of effects or general recorder reliability.


## Task F: qualify the candidate and hand it to independent acceptance

**Files:** update `docs/product/evidence/episode-lanes/verification.md` (create), `docs/product/prds/0005-truthful-episode-lanes.md`, `docs/product/current-state.md`, `docs/product/metrics.md`; append a new numbered PDR. Update `docs/config-schemas/brain.md` for the verified target-update clock. Do not rewrite historical PDRs or baseline receipts.

1. Run the new regressions individually after each owning task. At this checkpoint run all episode modules plus the enclosing runtime, replay, exploration, runner, recording and persistence tests. Expected: no accounting failures, no hidden deselection of new cases. Retain skip reasons and exact collection counts; do not predict a pass count in advance.

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 .venv/bin/pytest --no-cov -q \
  tests/test_townlet/regressions/test_episode_lane_environment.py \
  tests/test_townlet/regressions/test_episode_lane_population.py \
  tests/test_townlet/regressions/test_episode_lane_learning.py \
  tests/test_townlet/regressions/test_episode_lane_sinks.py \
  tests/test_townlet/unit/oracle/test_episode_lane_comparator.py \
  tests/test_townlet/integration/test_authored_episode_lanes.py \
  tests/test_townlet/unit/population \
  tests/test_townlet/unit/exploration \
  tests/test_townlet/unit/training \
  tests/test_townlet/unit/recording \
  tests/test_townlet/unit/demo \
  tests/test_townlet/unit/scripts/test_l2_token_regression.py \
  tests/test_townlet/integration/test_episode_execution.py \
  tests/test_townlet/integration/test_training_loop.py \
  tests/test_townlet/integration/test_intrinsic_exploration.py \
  tests/test_townlet/integration/test_rnd_loss_tracking.py \
  tests/test_townlet/integration/test_recurrent_bootstrap_runtime.py \
  tests/test_townlet/integration/test_recurrent_bptt_runtime.py \
  tests/test_townlet/integration/test_runner_integration.py \
  tests/test_townlet/integration/test_recording_recorder.py \
  tests/test_townlet/integration/test_recording_replay_manager.py \
  tests/test_townlet/integration/test_recording_playback.py \
  tests/test_townlet/integration/test_checkpointing.py \
  tests/test_townlet/integration/test_live_inference_checkpoint_identity.py
```

2. Run fleet/compiler and CI lint/type/no-defaults gates. Correct failure causes, with focused retesting. Expected exit 0 for every command; no broadened default whitelist or legacy reader.

```bash
.venv/bin/python scripts/validate_compiler_cli.py
.venv/bin/pytest --no-cov -q tests/test_townlet/integration/test_pack_smoke.py
.venv/bin/ruff check .
.venv/bin/black --check src tests
.venv/bin/mypy src/townlet --show-error-codes
.venv/bin/python scripts/no_defaults_lint.py src/townlet/ --whitelist .defaults-whitelist.txt
git diff --check
```

3. Run E4's candidate capture, exact attribution comparison and negative controls, plus the unchanged standing frozen harness:

```bash
.venv/bin/python -m townlet.oracle.harness --scripted
```

Expected all CPU cells satisfy their existing registered comparison contract, unless an exact newly observed boundary difference was preregistered and independently qualified. CUDA skipped without a CUDA execution claim. The standing matrix is not lane-learning/sink acceptance; format 4 cannot observe those surfaces. Do not widen a stream allowance to make a failed comparison green. If a production counter changes a VFS-observed live output beyond the predeclared boundary, stop and record the exact cause/contract implication rather than allow it post hoc.

4. On the complete candidate run the unfiltered default suite with coverage, including slow-marked tests. Do not use `-m`, `-k`, ignores or test exclusions. There is no convergence campaign in this gate.

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 .venv/bin/pytest
```

Expected exit 0, coverage ≥70%, exact passed/skipped/warning readings retained. Skips must be reported individually; a fixture intentionally bypassing real learning, I/O or authored construction cannot stand in for its required acceptance witness.

5. Commit runtime/test/config changes before final qualification receipts; record full candidate SHA/tree, actual import paths, environment/lock identity, commands, exit codes, timestamps, log/artifact digests and exact causal-commit attribution. Rerun only the affected gates if receipt preparation changes executable content. An independent reviewer reads PRD criteria 1–8 against retained evidence, checks production callers and negative controls, and either accepts that identified candidate or returns failures. Review by October 9 or the first proposed candidate, whichever is earlier; absent evidence remains unaccepted.

6. Record product acceptance separately from local integration, push/PR, exact-main CI and learning. Close the engine bug only after verification and its valid tracker transition; keep effect-reset and recovery-exit tickets open. Backout restores the previous source checkpoint while preserving every newer artifact unchanged; use fresh run/DB paths, never consume newer formats with old code or migrate them. Any later merge requires the established README verification method and exact-head delivery checks. This plan does not itself authorize a public release, announcement or artifact deletion.

```bash
git add docs/product/evidence/episode-lanes/verification.md \
  docs/product/prds/0005-truthful-episode-lanes.md \
  docs/product/current-state.md docs/product/metrics.md \
  docs/config-schemas/brain.md "$EPISODE_PDR_PATH"
git commit -m "docs(product): record episode lane qualification"
```

Set `EPISODE_PDR_PATH` to the next actual numbered PDR file created in this task before staging it; no placeholder path is executable.

**Definition of Done:** all PRD criteria verified at one candidate; independently retained eligible sample/target and persisted sink evidence; exact parent/oracle attribution with negative controls; fleet, lint, type, no-defaults and unfiltered suite green. No convergence or recovery-exit claim.

## Acceptance evidence matrix

| PRD criterion | Required retained evidence | Reject condition |
| --- | --- | --- |
| 1 Runtime | Authored pack through compiler/compiled brain; independent entry-event ledger; 2/5, reverse, single, simultaneous fixtures | Missing terminal step; aggregate-only assertion; state injection used as authored claim |
| 2 Replay | Actual standard/PER row identities and recurrent sequence lengths `[2,5]`; reset/cross-episode tests | Any later dead row or lost terminal row |
| 3 Learning/exploration | Seven normalized/ingested identities; real Q/RND updates and parameter changes; captured actual loss targets; recurrent seq1/seq2/Double DQN | Phantom sample, wrong target, duplicate adaptive completion, no real update |
| 4 Rewards/outcomes | One genuine retirement bonus; death wins coincidence; components sum to total; frozen CPU outcomes under later mutation | Later bonus, nonzero dead contribution, aliasing or unexplained live reward change |
| 5 Consumers | Real SQLite, EventAccumulator, curriculum calls, decompressed persisted recordings and both CSV exporters | Wrong lane survival, ticks/transitions conflated, recording sticky-done rows |
| 6 Endings/reset | Budget six `[2,4]`, explicit lower cap and checkpoint cuts, two consecutive episodes and repeated flush | Done rewritten on truncation, duplicated/lost completion, hidden leakage |
| 7 Attribution/gates | Exact parent bank, frozen oracle receipt, narrow exact difference manifest, failing corrupted controls, full gate logs | Broad exception, frozen rewrite, unexplained difference, hidden deselection |
| 8 Acceptance | Independent criterion-by-criterion verdict at identified candidate | Treating plan, suite, publication or budget spend as acceptance/convergence |


## Concrete implementation anchors for the new instrument and sink contracts

These fragments define new code to be created in the indicated tasks. They are not existing APIs or claims of implementation. Insert the tensor blocks into their named methods with the existing context; standalone comparator and schema validation examples include their imports.

**E1 independent event ledger.** Create `tests/test_townlet/regressions/fixtures/episode_lanes.py` and its package `__init__.py`; reuse it across the new regressions. The ledger consumes dones returned by the normal environment and records the pre-step eligibility independently of the candidate info keys. Bind row hashes to `(episode, tick, agent)` and bytes; a hash seen in both eligible/phantom roles is ambiguous and must fail qualification rather than prove exclusion by set subtraction.

```python
from dataclasses import dataclass
import torch

@dataclass
class LaneLedger:
    counts: torch.Tensor
    terminal_counts: torch.Tensor
    vector_ticks: int
    live_transitions: int

    @classmethod
    def create(cls, num_agents: int, device: torch.device) -> "LaneLedger":
        return cls(
            counts=torch.zeros(num_agents, dtype=torch.long, device=device),
            terminal_counts=torch.zeros(num_agents, dtype=torch.long, device=device),
            vector_ticks=0,
            live_transitions=0,
        )

    def observe(self, before_done: torch.Tensor, after_done: torch.Tensor) -> None:
        active = ~before_done
        new_end = active & after_done
        self.counts += active.long()
        self.terminal_counts += new_end.long()
        self.vector_ticks += 1
        self.live_transitions += int(active.sum().item())
```

For the configured 2/5 schedule, assert ledger counts `[2,5]`, terminal counts `[1,1]`, ticks5 and transitions7 before comparing runtime counts/snapshots to it. Pure truncation has no new terminal event, but its explicit population completion closes the nonempty surviving ledger once. Do not derive this reference from the candidate `step_counts` or completion mask.

**E1/E4 scoped attribution API.** Define these new tool commands explicitly; `capture` invokes a producer in an isolated subprocess with the selected source/config roots and recipe. A clean parent source worktree remains at the E0 SHA, while the new instrument and copied authored config live outside it; record their separate digests. Never run parent imports through an installed candidate editable package accidentally. Before runtime cuts, bank both the preserved parent and pinned-oracle controlled receipts, then commit a manifest of intended coordinates to `docs/product/evidence/episode-lanes/intended-differences.md` and a new entry in `docs/oracle/known-divergences.md` (next free ID, currently DIV-016). The entry names old/candidate behavior, controlled recipe and instrument blind spots. This registration is required even if no standing matrix cell observes the boundary; do not fabricate matrix bindings or widen a whole reward stream. PDR-0058 exit remains open.

The intended manifest is a two-phase record: exact recipe, coordinates, before values and required contract after values are committed before the seam changes. After source commits, append causal commit receipts/bisection results and exact measured after values to verification evidence; never invent a future SHA in the preregistration or rewrite it after seeing an unexplained delta.

```bash
.venv/bin/python scripts/check_episode_lanes.py capture \
  --source-root "$EPISODE_PARENT_ROOT" \
  --config-root "$PWD/configs/test/episode_lanes" \
  --recipe authored-two-five \
  --output runs/episode-lanes/2026-10-02/implementation/parent/lanes
.venv/bin/python scripts/check_episode_lanes.py capture \
  --source-root "$PWD" --config-root "$PWD/configs/test/episode_lanes" \
  --recipe authored-two-five \
  --output runs/episode-lanes/2026-10-02/implementation/candidate/lanes
.venv/bin/python scripts/check_episode_lanes.py compare \
  --before runs/episode-lanes/2026-10-02/implementation/parent/lanes \
  --after runs/episode-lanes/2026-10-02/implementation/candidate/lanes \
  --expected docs/product/evidence/episode-lanes/intended-differences.md \
  --output runs/episode-lanes/2026-10-02/implementation/comparison.json
```

Set `EPISODE_PARENT_ROOT` to the clean preserved parent worktree created at the E0 SHA, not the candidate root. The Markdown manifest contains a fenced JSON payload with exact reading keys `[recipe, field, tick, agent, coordinate]`; the tool extracts that one payload and refuses extra/missing blocks. Additional supported recipes are `passive-two-five`, `death-at-lifespan`, `healthy-retirement`, `two-episodes-reset` and `budget-six`. Every invocation declares its recipe and configuration-byte identity. A recipe whose runner/population fields are absent on the old side records explicit absence, and separately evaluates candidate contract assertions; absence is not a legacy API fallback.

Core exact-coordinate validation for `scripts/check_episode_lanes.py`:

```python
from collections.abc import Mapping, Sequence
from typing import Any

ReadingKey = tuple[str, str, int, int, str]

def compare_exact(
    before: Mapping[ReadingKey, Any],
    after: Mapping[ReadingKey, Any],
    intended: Sequence[tuple[ReadingKey, Any, Any]],
) -> None:
    declarations = {}
    for key, old, new in intended:
        if key in declarations:
            raise ValueError(f"Duplicate intended difference: {key}")
        if type(old) is type(new) and old == new:
            raise ValueError(f"Unused intended difference: {key}")
        declarations[key] = (old, new)
    missing = object()
    changed = {}
    for key in before.keys() | after.keys():
        old, new = before.get(key, missing), after.get(key, missing)
        if type(old) is not type(new) or old != new:
            changed[key] = (old, new)
    if changed.keys() != declarations.keys():
        raise ValueError("Observed differences do not match the exact declaration set")
    for key, (old, new) in changed.items():
        expected_old, expected_new = declarations[key]
        if old is missing or new is missing:
            raise ValueError(f"Undeclared presence change: {key}")
        if type(old) is not type(expected_old) or type(new) is not type(expected_new):
            raise ValueError(f"Reading type changed: {key}")
        if old != expected_old or new != expected_new:
            raise ValueError(f"Unexpected exact values: {key}")
```

Flatten known finite scalars plus dtype/shape/byte-hash readings; serialize absent new event keys as explicit `present=False` readings. Refuse NaN/Inf, duplicate reading keys, inconsistent source/config/action identity, malformed manifests, unknown fields/recipes, wrong import roots and stale source stamps before comparison. The whole-key equality and exact old/new values reject dropped terminal steps, extra allowances and unauthorized live changes. Independently check candidate contract values and events; byte comparison alone is not a semantic oracle. Negative-control tests mutate one coordinate or introduce an unused declaration and must fail.

**S1 strict DB inspection before mutation.** New schema constant `DEMO_SCHEMA_VERSION = 1` stamps the first explicitly versioned layout with `PRAGMA user_version`; old unversioned layout is incompatible. Centralize expected complete column tuples for all five existing tables from the revised literal DDL, including new episode context and recording completion reason. Do not infer supported columns from an input DB. The initialization gate is:

```python
from pathlib import Path
import sqlite3
from collections.abc import Mapping

DEMO_SCHEMA_VERSION = 1

def inspect_existing_demo_schema(
    path: Path, expected_columns: Mapping[str, tuple[str, ...]]
) -> None:
    if not path.exists() or path.stat().st_size == 0:
        return
    connection = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    try:
        version = connection.execute("PRAGMA user_version").fetchone()[0]
        if version != DEMO_SCHEMA_VERSION:
            raise ValueError(f"Unsupported demo schema version: {version}")
        actual_tables = {
            row[0] for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
        }
        if actual_tables != expected_columns.keys():
            raise ValueError("Unsupported demo table layout")
        for table, columns in expected_columns.items():
            if not table.isidentifier():
                raise ValueError("Invalid internal schema table name")
            actual = tuple(row[1] for row in connection.execute(f'PRAGMA table_info("{table}")'))
            if actual != columns:
                raise ValueError(f"Unsupported demo columns: {table}")
    finally:
        connection.close()
```

Extend validation to the expected declared types, NOT NULL and primary-key metadata, not just names. Run this gate before opening the write/WAL connection or executing DDL. A malformed/nonempty SQLite artifact errors; it does not become a new database. Fresh creation must write revised tables/stamp as one transaction; no old artifact is upgraded. Current-layout reopen validates first. Queries/inserts bind values using SQLite placeholders; only trusted internal schema identifiers are interpolated.

S1's runner payload is taken from population outcomes after explicit survivor completion:

```python
completion = population.episode_completions[0]
if completion is None:
    raise RuntimeError("Cannot publish an episode without a slot-zero completion")
db.insert_episode(
    episode_id=episode, timestamp=timestamp,
    survival_time=completion.survival_time,
    batch_episode_steps=batch_episode_steps,
    live_agent_transitions=episode_live_agent_transitions,
    completion_reason=completion.reason,
    total_reward=float(episode_rewards[0].item()),
    extrinsic_reward=float(episode_extrinsic_rewards[0].item()),
    intrinsic_reward=float(episode_intrinsic_rewards[0].item()),
    intrinsic_weight=intrinsic_weight, curriculum_stage=curriculum_stage,
    epsilon=epsilon, observation_schema_hash=level_meta.observation_schema_hash,
)
```

Names for loop-local variables above are proposed new names; `level_meta.observation_schema_hash` is the existing runner identity accessor. The scalar snapshot and eligibility-based totals are required regardless of variable naming. The DDL/signature/SQL mapping must include all required new fields, and all current callers/fixtures must supply them.

**S2 eligible contributions.** Immediately after a population step, accumulate canonical composed components with its required entry mask; no raw-novelty reconstruction. `intrinsic` already includes base weight/modifiers; `shaping` remains a separate contributor.

```python
active = agent_state.info["active_on_entry"]
components = agent_state.info["reward_components"]
episode_rewards += torch.where(active, agent_state.rewards, torch.zeros_like(agent_state.rewards))
episode_extrinsic_rewards += torch.where(active, components["extrinsic"], torch.zeros_like(agent_state.rewards))
episode_intrinsic_rewards += torch.where(active, components["intrinsic"], torch.zeros_like(agent_state.rewards))
episode_shaping_rewards += torch.where(active, components["shaping"], torch.zeros_like(agent_state.rewards))
batch_episode_steps += 1
episode_live_agent_transitions += int(active.sum().item())
```

At ordinary batch end, require one nonempty snapshot per participated lane; untouched zero-step batches publish nothing. Log per-agent final meters/survival/reason from snapshots, not current mutable storage. Repeated checkpoints cannot revise these values. Add aggregate batch/live TensorBoard scalars with explicit names, alongside existing per-agent survival tags.

**Task commit and done receipts.** E1/E2/E3 and S1–S4 each end with an explicit task-file `git add` followed by their stated Conventional Commit subject; use the exact file lists above, including all discovered required-field constructors. Never stage an enclosing directory containing unrelated work. Each task is done only when its RED failure was observed for the stated cause, its focused GREEN command exits0, dependent callers are updated, the scoped diff is inspected and its commit is recorded. F's complete-candidate gates remain required after all intermediate commits.

## Literal task commands

The following complete the prose commit instructions above. Run from the execution worktree; inspect staged paths with `git diff --cached --stat` before each commit. Include any additionally discovered required-interface caller in that same scoped task; list it explicitly in the receipt.

**E1:** new integration module contains separate `test_authored_pack_compiles` and behavior tests; compiler-only green does not conceal the expected behavioral RED. The comparator module exercises the standalone exact-coordinate function and its corrupted controls.

```bash
.venv/bin/pytest --no-cov -q tests/test_townlet/integration/test_authored_episode_lanes.py::test_authored_pack_compiles tests/test_townlet/unit/oracle/test_episode_lane_comparator.py
.venv/bin/pytest --no-cov -q tests/test_townlet/regressions/test_episode_lane_environment.py tests/test_townlet/integration/test_authored_episode_lanes.py
git add configs/test/episode_lanes/experiment.yaml configs/test/episode_lanes/stratum.yaml \
  configs/test/episode_lanes/environment.yaml configs/test/episode_lanes/actions.yaml \
  configs/test/episode_lanes/brain.yaml configs/test/episode_lanes/effects.yaml \
  configs/test/episode_lanes/variables.yaml configs/test/episode_lanes/items.yaml \
  configs/test/episode_lanes/levels/L0_test/bars.yaml \
  configs/test/episode_lanes/levels/L0_test/affordances.yaml \
  configs/test/episode_lanes/levels/L0_test/curriculum.yaml \
  configs/test/episode_lanes/levels/L0_test/drive.yaml \
  configs/test/episode_lanes/levels/L0_test/training.yaml \
  scripts/check_episode_lanes.py tests/test_townlet/regressions/fixtures/__init__.py \
  tests/test_townlet/regressions/fixtures/episode_lanes.py \
  tests/test_townlet/regressions/test_episode_lane_environment.py \
  tests/test_townlet/integration/test_authored_episode_lanes.py \
  tests/test_townlet/unit/oracle/test_episode_lane_comparator.py \
  docs/product/evidence/episode-lanes/intended-differences.md docs/oracle/known-divergences.md
git commit -m "test(episodes): add authored lane and attribution witnesses"
```

Expected first command exit0; second command exposes the parent defects until E2/E3 repair them. Retain its precise failures rather than reporting E1 as a green product gate.

**E2/E3:** split their changes as described above; E2 counting/event cases green, reward/statistics cases remain explicit RED until E3. The complete environment/authored modules must pass E3.

```bash
.venv/bin/pytest --no-cov -q tests/test_townlet/regressions/test_episode_lane_environment.py tests/test_townlet/integration/test_authored_episode_lanes.py
git add src/townlet/environment/vectorized_env.py tests/test_townlet/regressions/test_episode_lane_environment.py
git commit -m "fix(env): count eligible lanes and classify terminal events once"
.venv/bin/pytest --no-cov -q tests/test_townlet/regressions/test_episode_lane_environment.py tests/test_townlet/integration/test_authored_episode_lanes.py tests/test_townlet/unit/environment/test_reward_calculator.py tests/test_townlet/unit/environment/test_vectorized_env.py tests/test_townlet/performance/test_environment_step_benchmarks.py
git add src/townlet/environment/vectorized_env.py src/townlet/environment/reward_calculator.py \
  tests/test_townlet/regressions/test_episode_lane_environment.py \
  tests/test_townlet/unit/environment/test_reward_calculator.py \
  tests/test_townlet/unit/environment/test_vectorized_env.py \
  tests/test_townlet/performance/test_environment_step_benchmarks.py
git commit -m "fix(rewards): compose retirement once from eligible lane experience"
```

**S1:** schema, required metadata constructors, version2 producers/readers and index mappings are atomic here. The S3 list is a sweep/verification inventory, not deferred ownership of those prerequisites. Runner record-row filtering follows in S2/S3.

```bash
.venv/bin/pytest --no-cov -q tests/test_townlet/unit/demo/test_episode_database_schema.py tests/test_townlet/unit/recording tests/test_townlet/integration/test_recording_replay_manager.py tests/test_townlet/integration/test_recording_recorder.py tests/test_townlet/integration/test_recording_playback.py tests/test_townlet/integration/test_recording_video_export.py tests/test_townlet/unit/demo/test_live_inference_unit.py tests/test_townlet/integration/test_runner_integration.py
git add src/townlet/demo/database.py src/townlet/demo/runner.py src/townlet/demo/live_inference.py \
  src/townlet/recording/data_structures.py src/townlet/recording/recorder.py src/townlet/recording/replay.py \
  tests/test_townlet/unit/demo/test_episode_database_schema.py \
  tests/test_townlet/unit/demo/test_live_inference_unit.py tests/test_townlet/utils/builders.py \
  tests/test_townlet/unit/recording/test_database.py tests/test_townlet/unit/recording/test_data_structures.py \
  tests/test_townlet/unit/recording/test_recorder.py tests/test_townlet/unit/recording/test_criteria.py \
  tests/test_townlet/integration/test_recording_video_export.py \
  tests/test_townlet/integration/test_recording_replay_manager.py \
  tests/test_townlet/integration/test_recording_playback.py \
  tests/test_townlet/integration/test_recording_recorder.py \
  tests/test_townlet/integration/test_runner_integration.py
git commit -m "feat(demo): require truthful episode and recording contracts"
```

Expected all current constructor/schema/reader tests green. New runtime accounting assertions added in S2/S3 have their own RED then GREEN cycle; S1 does not claim eligible recording rows already pass.

**S2/S3/S4:** execute each task's literal RED/GREEN commands above, then commit only its owning files and explicitly listed affected tests.

```bash
git add src/townlet/demo/runner.py src/townlet/training/tensorboard_logger.py \
  tests/test_townlet/regressions/test_episode_lane_sinks.py \
  tests/test_townlet/unit/demo/test_runner_environment_budget.py \
  tests/test_townlet/unit/training/test_tensorboard_logger.py \
  tests/test_townlet/integration/test_runner_integration.py \
  tests/test_townlet/integration/test_tensorboard_logger.py
git commit -m "fix(demo): publish immutable eligible episode outcomes"
git add src/townlet/demo/runner.py tests/test_townlet/regressions/test_episode_lane_sinks.py
git commit -m "fix(recording): retain only eligible completed lane experience"
git add scripts/l2_baseline.py scripts/l2_token_regression.py \
  tests/test_townlet/unit/scripts/test_l2_baseline.py \
  tests/test_townlet/unit/scripts/test_l2_token_regression.py \
  tests/test_townlet/regressions/test_episode_lane_sinks.py
git commit -m "fix(eval): export explicit episode accounting units"
```
