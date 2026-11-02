# T15 existing provider construction API

Static handoff at HEAD `75bc8e438caaf4eadf8f4e0f6b522f84c680c1e7`. Reuses exactly five whole sources/1,593 lines from `T15-provider-contracts.md`; hashes/counts rechecked unchanged. No new implementation source, imports, runtime, tests, index changes, branches/worktrees/copies or subagents. Only this ignored prose is written. Root reports T14 6,696 passed/16 skipped and source CI green; this worker does not rerun or broaden that qualification.

## Exact public constructors

`townlet.exploration.rnd.RNDExploration` — RND123,131–141:
```python
def __init__(
    self, obs_dim: int = 70, embed_dim: int = 128,
    learning_rate: float = 1e-4, training_batch_size: int = 128,
    epsilon_start: float = 1.0, epsilon_min: float = 0.01,
    epsilon_decay: float = 0.995,
    device: torch.device = torch.device("cpu"),
):
```
These are existing signature defaults, not proposed test or production defaults. `training_batch_size` must be a positive exact `int` (RND154–155). Constructor stores dimensions/device/epsilon controls, builds fixed and predictor `RNDNetwork(obs_dim, embed_dim)`, freezes fixed parameters and creates predictor Adam with `lr=learning_rate`; no policy/config object is accepted (RND156–189).

`townlet.exploration.adaptive_intrinsic.AdaptiveIntrinsicExploration` — AD12,21–38:
```python
def __init__(
    self, obs_dim: int = 70, embed_dim: int = 128,
    rnd_learning_rate: float = 1e-4, rnd_training_batch_size: int = 128,
    initial_intrinsic_weight: float = 1.0, min_intrinsic_weight: float = 0.0,
    variance_threshold: float = 100.0, min_survival_fraction: float = 0.4,
    max_episode_length: int = 500, survival_window: int = 100,
    decay_rate: float = 0.99, epsilon_start: float = 1.0,
    epsilon_min: float = 0.01, epsilon_decay: float = 0.995,
    device: torch.device = torch.device("cpu"),
):
```
Exact contained-provider call (AD59–68): `RNDExploration(obs_dim=obs_dim, embed_dim=embed_dim, learning_rate=rnd_learning_rate, training_batch_size=rnd_training_batch_size, epsilon_start=epsilon_start, epsilon_min=epsilon_min, epsilon_decay=epsilon_decay, device=device)`. Own fields store initial/current/min scale, variance threshold, survival fraction/horizon/window/decay/device and `int(min_survival_fraction * max_episode_length)`; history begins empty (AD70–83). No policy/config object is accepted.

`townlet.exploration.count_based.CountExploration` — COUNT65,68:
```python
def __init__(self, policy: ResolvedExplorationPolicy, *, quantization_width: float, max_entries: int, device: torch.device | str):
```
The actual class name is **`CountExploration`**, not `CountBasedExploration`. Requires genuine `ResolvedExplorationPolicy`, `policy.strategy == "count_based"`, finite positive width and positive integer capacity (bool refused). Width/capacity must equal `policy.provider_parameters["quantization_width"]`/`["max_entries"]`; constructor copies policy through `ResolvedExplorationPolicy.from_dict(policy.to_dict())` (COUNT69–80). Exact inherited-init call (COUNT82): `super().__init__(epsilon=policy.epsilon_start, epsilon_decay=policy.epsilon_decay, epsilon_min=policy.epsilon_end)`. No omitted count-parameter derivation happens here.

`townlet.exploration.icm.ICMExploration` — ICM39,46–60:
```python
def __init__(
    self, policy: ResolvedExplorationPolicy, *, obs_dim: int, action_dim: int,
    feature_dim: int, hidden_dim: int, learning_rate: float,
    inverse_weight: float, forward_weight: float, training_batch_size: int,
    max_pending_transitions: int, device: torch.device | str,
):
```
Requires genuine `ResolvedExplorationPolicy`, `policy.strategy == "icm"`; positive integer dimensions/batch/capacity (bool refused), positive finite learning rate, finite nonnegative inverse/forward weights, capacity >= batch (ICM61–78). The **entire** `dict(policy.provider_parameters)` must equal `{feature_dim, hidden_dim, learning_rate, inverse_weight, forward_weight, training_batch_size, max_pending_transitions}` with their passed values; obs/action dimensions are separate inputs. Exact inherited-init call (ICM79): `super().__init__(epsilon=policy.epsilon_start, epsilon_decay=policy.epsilon_decay, epsilon_min=policy.epsilon_end)`. Builds float32 encoder/inverse/forward models and Adam over all three (ICM80–101).

All four classes define their own constructors. Count/ICM inherit `EpsilonGreedyExploration`; RND/Adaptive inherit `ExplorationStrategy`. The two `super().__init__` calls above are source-verified; base constructor signatures/implementation are excluded. No public construction classmethod or provider factory appears in these five files. Factory/config/base sources were not opened, and **no existing public factory is claimed**. The fifth actual provider (`none`/plain epsilon) and its constructor/selector come from root's separate epsilon receipt, not this note. Do not replace a required resolved policy with a duck-typed stub: Count/ICM perform `isinstance` checks. Full policy construction/validation fields belong to the separate verified policy producer; this note enumerates only fields actually accessed here.

## Inputs and real effects to preserve in all-five selection controls

- RND `select_actions(q_values, agent_states, action_masks=None)` (RND191–211) calls `epsilon_greedy_action_selection(q_values=q_values, epsilons=agent_states.epsilons, action_masks=action_masks)`. Adaptive's identical public signature delegates `self.rnd.select_actions(q_values, agent_states, action_masks)` (AD85–101). Q `[N,A]`, aligned state epsilons `[N]`, optional bool mask `[N,A]`; provider scalar epsilon is **not** the selection argument. Count/ICM define no local selector; use the separate epsilon receipt for their actual inherited body/state reads.
- Strict shared function call is `epsilon_greedy_action_selection_eligible(q_values, epsilons, action_masks, *, eligible)` (AS91–120), with explicit bool `[N]` real entry membership, exact mask shape/device and live-empty refusal; inactive rows consume no RNG. It does not call provider services. Preserve public full-N/provided-selector roles under root's chosen adapter rather than silently bypassing unknown effects.
- RND reward: `compute_intrinsic_rewards(observations, update_stats=False)` (RND213–242), observations `[N,obs_dim]`; `True` updates shared RMS, not parameters. Training: `update(batch)` requires `batch["observations"]` when present (RND244–266), or configured `admit_and_service(observations, *, vector_tick: int)` (RND298–359). `configure_service(options: RNDOptions)` requires all resolved options explicit; accessed service fields are `service_mode`, `max_updates_per_tick`, `max_pending_rows`, `overflow_policy`, with capacity >= minibatch (RND280–296,315–345). Service validates finite matching network dtype/width, consumes actual eligible predecessor rows and performs real predictor Adam minibatches; pending work may be serviced with zero new rows. No config-construction signature is claimed.
- Adaptive delegates reward/update, adds `update_on_episode_end(survival_time: float)`, `get_intrinsic_weight()` and `decay_epsilon()` (AD103–191). Real completion appends history and may change scale; action selection alone does neither. Once-only outcomes and synchronization of passed state epsilons remain caller responsibilities.
- Count reward: `compute_intrinsic_rewards(observations, *args, **kwargs)` accepts one optional bool `update_stats`, finite floating `[N,D]` with D>0 on configured device (COUNT88–117). `True` performs count/LRU admissions in row order, queries are pure. `admit_and_service(context: IntrinsicTransitionContext)` is intentionally all-zero service, **not** a second count update (COUNT118–147). No neural update exists.
- ICM reward: `compute_transition_novelty(context: IntrinsicTransitionContext, *, update_stats: bool)` (ICM124–137); actual predecessor/successor finite float32 `[N,obs_dim]`, int64 actions `[N]`, bool `active_on_entry[N]`, common provider device, eligible action bounds (ICM103–122). Returns raw detached novelty, zero inactive; `update_stats=True` alone does not admit/train. `admit_and_service(context)` accesses `context.vector_tick`, `policy.overflow_policy`, `policy.service_mode`, `policy.max_updates_per_tick`, snapshots active actual transitions and performs real encoder/inverse/forward Adam minibatches (ICM145–203). Observation-only reward/update refuses (ICM139–143). Accepted T18a prose supplies context spelling `IntrinsicTransitionContext(*, predecessor, actions, successor, active_on_entry, vector_tick)` and owned snapshots; its implementation remains excluded.

## Source identity and verification

| Alias/path under `src/townlet/exploration/` | Whole lines | SHA256 |
|---|---:|---|
| AS `action_selection.py` | 120 | `2a2ddfbd9aaf01afa14b0d1907fa1f3c8823f253dcdc8d16a8ff4054bf3768b8` |
| AD `adaptive_intrinsic.py` | 226 | `80ecb26fb33626cc9efd271422c69cdae495412f5db94a505eb59628b58b6cd9` |
| RND `rnd.py` | 661 | `3a774dfb042cdbf20b66555c41f75c2d537b6ff49472395877dfcf5595e26e72` |
| COUNT `count_based.py` | 206 | `163cb33f06799a75c887ff7beb58e4897875c94a4780ab722d019f714b33e9c1` |
| ICM `icm.py` | 380 | `8004aec68d19c962df0cf6785b00af32c8553a3746fee95be39009555f9d44b8` |

The detailed companion records accepted-prose identities and all scope limits. This target is covered by `.git/info/exclude:7:/.superpowers/`. Provider hashes/counts and HEAD are checked before/after this write; active other writers' status is not treated as this worker's exclusive custody. No approval of provider-effect removal, full-N narrowing, shared/private substitution or broader completion is implied. Returned stationary.
