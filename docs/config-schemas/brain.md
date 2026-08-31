# brain.yaml Configuration Reference

> Verified against `src/townlet/config/brain_config.py` on 2026-08-31. Architecture names and
> nested blocks are closed vocabularies; obsolete architecture keys fail validation.


Brain configuration defines agent architecture, optimizer, loss function, Q-learning parameters, and replay buffer strategy.

## File Location

Each config pack requires a pack-root `brain.yaml`, and any level MAY override it with a
complete `brain.yaml` of its own:

```
configs/<pack>/
├── brain.yaml              # Pack brain: architecture and learning (REQUIRED)
├── stratum.yaml
├── actions.yaml
└── levels/<level>/
    ├── brain.yaml          # OPTIONAL complete override for this level (PDR-0027)
    ├── bars.yaml
    ├── drive.yaml
    └── training.yaml
```

**Per-level override semantics (PDR-0027):**

- A level's `brain.yaml` is a **complete file**, not a patch. If present it replaces the
  pack brain as that level's effective base; if absent the level inherits the pack brain
  unchanged. There is no partial merge — partial merges need default semantics, which the
  No-Defaults Principle forbids.
- **Overriding a brain forks the lineage.** `brain_hash` covers the effective config for
  the compiled level, so the override moves it; the compiled artifact also carries
  `pack_brain_hash` (the pack baseline under the same training overrides), and every
  checkpoint stamps both. A checkpoint whose two hashes differ is stated as a fork at load
  time — you never discover it by observing wrong behaviour. Forked artifacts are NOT
  interchangeable with unforked artifacts of the same pack.

## Schema Version

```yaml
version: "1.0"
description: "Human-readable description"
```

## Architecture Types

The `architecture` section defines the neural network architecture. Four types are supported:
feedforward, recurrent, dueling, and token_set.

### Feedforward

Standard feedforward MLP over the compiled flat token serialization. It can consume either
global or partial observations, but it carries no memory across steps.

```yaml
architecture:
  type: feedforward
  feedforward:
    hidden_layers: [256, 128]  # MLP layer sizes
    activation: relu           # relu, gelu, swish, tanh, elu
    dropout: 0.0               # Dropout probability [0, 1)
    layer_norm: true           # LayerNorm after each layer
```

**Parameters:**
- `hidden_layers` (list[int], required): Layer sizes for MLP (e.g., [256, 128])
- `activation` (string, required): Activation function
  - Options: `relu`, `gelu`, `swish`, `tanh`, `elu`
- `dropout` (float, required): Dropout probability
  - Range: [0.0, 1.0)
  - Typical: 0.0 (no dropout for standard DQN)
- `layer_norm` (bool, required): Apply LayerNorm after each layer
  - Typical: `true` for stable training

**Example Use Cases:**
- L0_0_minimal: Temporal credit assignment (3×3 grid)
- L0_5_dual_resource: Multiple resources (7×7 grid)
- L1_full_observability: Full observability baseline (8×8 grid)

### Recurrent token set with LSTM

The recurrent architecture uses the same per-type token projections, learned type embeddings,
and declared set aggregator as `token_set`. It encodes every frame independently, presents the
pooled frame sequence to one LSTM call, and applies the Q-head to every recurrent output. The
compiled `TokenSpec` owns the roster, capacities, payload widths, and flat serialization layout.

```yaml
architecture:
  type: recurrent
  recurrent:
    token_embed_dim: 128
    q_head_hidden_dim: 128
    aggregator:
      type: attention
      num_heads: 4
    lstm:
      hidden_size: 128
      num_layers: 1
      dropout: 0.0
```

**Parameters:**

- `token_embed_dim` (int, required): Embedding width for every live token type.
- `q_head_hidden_dim` (int, required): Hidden width of the Q-value head.
- `aggregator` (block, required): The same closed `mean` or `attention` contract documented
  under `token_set`. `attention` requires `num_heads`, and `token_embed_dim` must be divisible
  by it; `mean` takes no `num_heads`.

**lstm** (required):
- `hidden_size` (int, required): LSTM hidden-state width.
- `num_layers` (int, required): Number of stacked LSTM layers, from 1 through 4.
- `dropout` (float, required): Inter-layer dropout in `[0.0, 1.0)`. It must be `0.0` when
  `num_layers` is 1 because PyTorch applies LSTM dropout only between stacked layers.

**Example Use Cases:**
- Partially observable token environments that require memory.
- Sequence-sensitive training with explicit hidden-state threading and terminal boundaries.

### Dueling (Value/Advantage Decomposition)

Dueling DQN architecture with separate value and advantage streams. Improves learning by decomposing Q(s,a) = V(s) + (A(s,a) - mean(A)).

```yaml
architecture:
  type: dueling
  dueling:
    shared_layers: [256, 128]   # Shared feature extraction layers
    value_stream:
      hidden_layers: [128]      # Value stream V(s) layers
      activation: relu
    advantage_stream:
      hidden_layers: [128]      # Advantage stream A(s,a) layers
      activation: relu
    activation: relu            # Activation for shared layers
    dropout: 0.0                # Dropout probability
    layer_norm: true            # LayerNorm after shared layers
```

**Parameters:**
- `shared_layers` (list[int], required): Shared feature extraction layer sizes
  - Must have at least one layer (min_length=1)
- `value_stream` (DuelingStreamConfig, required): Value stream configuration
  - `hidden_layers` (list[int]): Layer sizes for V(s) stream
  - `activation` (string): Activation function
- `advantage_stream` (DuelingStreamConfig, required): Advantage stream configuration
  - `hidden_layers` (list[int]): Layer sizes for A(s,a) stream
  - `activation` (string): Activation function
- `activation` (string, required): Activation for shared layers
- `dropout` (float, required): Dropout probability [0.0, 1.0)
- `layer_norm` (bool, required): Apply LayerNorm after shared layers

**Architecture Details:**
- Shared layers extract features from observations
- Value stream outputs scalar V(s) (state value)
- Advantage stream outputs per-action A(s,a) (action advantages)
- Aggregation: Q(s,a) = V(s) + (A(s,a) - mean(A(s,:)))
- Mean subtraction ensures identifiability

**Example Use Cases:**
- Experimental: Testing value/advantage decomposition
- Ablation studies: Comparing against standard feedforward

### Token Set

Token-native Q-network over the compiled `TokenSpec`. The roster, capacities, compact layout,
and static context are compiler-owned; the brain declares only network geometry and aggregation.

```yaml
architecture:
  type: token_set
  token_set:
    token_embed_dim: 64
    q_head_hidden_dim: 256
    aggregator:
      type: attention   # or: mean
      num_heads: 4      # attention only; token_embed_dim must divide by it
```

**Parameters:**
- `token_embed_dim` (int, required): Embedding size for the pooled token set.
- `q_head_hidden_dim` (int, required): Hidden size for Q-value prediction.
- `aggregator` (block, required): How the embedded token set is aggregated. No default —
  the choice is declared, never an engine fact.
  - `type: mean` — masked mean-pool over embedded rows (DeepSets). Takes no other keys.
  - `type: attention` — self-attention over the embedded rows (empty rows excluded via
    key-padding mask), then the same masked mean-pool. Requires `num_heads` (int > 0);
    `token_embed_dim` must be divisible by it. Both aggregators are permutation-invariant:
    token rows are a set, not a sequence.

**Example Use Cases:**
- Mixed typed-token policies over compiled observations.
- Generalisation experiments where token rosters differ while type names preserve parameter identity.

## Optimizer Configuration

The `optimizer` section defines the optimization algorithm and learning rate schedule.

```yaml
optimizer:
  type: adam                # adam, adamw, sgd, rmsprop
  learning_rate: 0.00025    # Learning rate (Atari DQN standard)
  adam_beta1: 0.9           # Adam beta1 parameter
  adam_beta2: 0.999         # Adam beta2 parameter
  adam_eps: 1.0e-8          # Adam epsilon for numerical stability
  weight_decay: 0.0         # L2 regularization weight
  schedule:
    type: constant          # constant, step_decay, cosine, exponential
```

**Parameters:**
- `type` (string, required): Optimizer algorithm
  - Options: `adam`, `adamw`, `sgd`, `rmsprop`
  - Typical: `adam` (standard for DQN)
- `learning_rate` (float, required): Learning rate
  - Typical: 0.00025 (Atari DQN standard)
- `adam_beta1` (float, required for Adam/AdamW): Exponential decay rate for 1st moment
  - Typical: 0.9
- `adam_beta2` (float, required for Adam/AdamW): Exponential decay rate for 2nd moment
  - Typical: 0.999
- `adam_eps` (float, required for Adam/AdamW): Epsilon for numerical stability
  - Typical: 1.0e-8
- `weight_decay` (float, required): L2 regularization weight
  - Typical: 0.0 (no regularization for standard DQN)
- `schedule` (ScheduleConfig, required): Learning rate schedule
  - `type` (string): Schedule type
    - `constant`: No decay
    - `step_decay`: Step-wise decay at intervals
    - `cosine`: Cosine annealing
    - `exponential`: Exponential decay

**Learning Rate Schedule Examples:**

Constant (no decay):
```yaml
schedule:
  type: constant
```

Step decay:
```yaml
schedule:
  type: step_decay
  step_size: 1000      # Decay every N episodes
  gamma: 0.95          # Multiply LR by gamma at each step
```

Cosine annealing:
```yaml
schedule:
  type: cosine
  t_max: 10000         # Maximum number of episodes
  eta_min: 0.00001     # Minimum learning rate
```

Exponential decay:
```yaml
schedule:
  type: exponential
  gamma: 0.9999        # Decay rate per episode
```

## Loss Function

The `loss` section defines the loss function for Q-value regression.

```yaml
loss:
  type: huber         # mse, huber, smooth_l1
  huber_delta: 1.0    # Required only for Huber loss
```

**Parameters:**
- `type` (string, required): Loss function type
  - `mse`: Mean Squared Error (standard DQN)
  - `huber`: Huber loss (robust to outliers)
  - `smooth_l1`: Smooth L1 loss (similar to Huber)
- `huber_delta` (float, required only for `type: huber`): Delta parameter for Huber loss
  - Must be omitted for `mse` and `smooth_l1`
  - Typical: 1.0

**Loss Function Comparison:**
- **MSE**: Standard choice, sensitive to large errors
- **Huber**: Robust to outliers, combines MSE (small errors) and MAE (large errors)
- **Smooth L1**: Alternative to Huber with similar properties

## Q-Learning Configuration

The `q_learning` section defines Q-learning hyperparameters.

```yaml
q_learning:
  gamma: 0.99                    # Discount factor
  target_update_frequency: 100   # Episodes between target network updates
  use_double_dqn: true           # Use Double DQN vs Vanilla DQN
```

**Parameters:**
- `gamma` (float, required): Discount factor for future rewards
  - Range: [0.0, 1.0]
  - Typical: 0.99 (values future rewards highly)
  - Higher gamma = more long-term planning
- `target_update_frequency` (int, required): Episodes between target network updates
  - Typical: 100 (every 100 episodes)
  - Lower values = more frequent updates, less stable
  - Higher values = more stable, but slower adaptation
- `use_double_dqn` (bool, required): Use Double DQN algorithm
  - `true`: Double DQN (decouples action selection and evaluation)
  - `false`: Vanilla DQN (uses target network for both)
  - **Recommendation**: Use `true` for better value estimates

**Double DQN vs Vanilla DQN:**

Vanilla DQN:
- Q-target: `r + γ * max_a Q_target(s', a)`
- Susceptible to Q-value overestimation

Double DQN:
- Q-target: `r + γ * Q_target(s', argmax_a Q_online(s', a))`
- Reduces overestimation by decoupling action selection and evaluation
- Typically converges faster and more stably

## Replay Buffer

The `replay` section defines the experience replay buffer strategy.

### Standard Replay (Uniform Sampling)

```yaml
replay:
  capacity: 10000       # Maximum transitions in buffer
  prioritized: false    # Use standard uniform sampling
```

**Parameters:**
- `capacity` (int, required): Maximum number of transitions in buffer
  - Typical range: 1,000 - 100,000
  - L0_0_minimal: 1,000 (small grid)
  - L1_full_observability: 10,000 (moderate)
  - Larger buffers = more diverse samples, slower training
- `prioritized` (bool, required): Use Prioritized Experience Replay (PER)
  - `false`: Uniform sampling (standard DQN)

### Prioritized Experience Replay (PER)

Samples transitions proportional to TD error (priority). High TD-error transitions are sampled more frequently, improving sample efficiency.

```yaml
replay:
  capacity: 50000                    # Maximum transitions (larger for PER)
  prioritized: true                  # Enable PER
  priority_alpha: 0.6                # Prioritization exponent
  priority_beta: 0.4                 # Importance sampling exponent
  priority_beta_annealing: true      # Anneal beta to 1.0 over training
```

**Parameters:**
- `capacity` (int, required): Maximum transitions in buffer
  - Typical: 50,000+ for PER (larger than standard replay)
- `prioritized` (bool, required): Enable PER
  - `true`: TD-error-based sampling
- `priority_alpha` (float, required when prioritized=true): Prioritization exponent
  - Range: [0.0, 1.0]
  - 0.0 = uniform sampling
  - 1.0 = full prioritization (sample proportional to TD error)
  - Typical: 0.6 (partial prioritization)
- `priority_beta` (float, required when prioritized=true): Importance sampling exponent
  - Range: [0.0, 1.0]
  - Anneals to 1.0 over training to correct sampling bias
  - Typical: 0.4 (initial value)
- `priority_beta_annealing` (bool, required when prioritized=true): Anneal beta to 1.0
  - `true`: Gradually increase beta from initial value to 1.0
  - Typical: `true` (recommended)

**PER Algorithm Details:**
- Sampling probability: `P(i) ∝ (p_i)^alpha`
- Importance sampling weight: `w_i = (N * P(i))^(-beta)`
- TD error update: `p_i = |TD_error_i| + epsilon`
- Beta annealing: `beta_t = beta_0 + (1.0 - beta_0) * (t / T)`

**PER Limitations:**
- Not yet supported for recurrent networks (LSTM)
- Only supported for feedforward and dueling architectures

## Complete Examples

### L0_0_minimal: Standard Feedforward

```yaml
version: "1.0"
description: "Standard feedforward Q-network for L0_0_minimal"

architecture:
  type: feedforward
  feedforward:
    hidden_layers: [256, 128]
    activation: relu
    dropout: 0.0
    layer_norm: true

optimizer:
  type: adam
  learning_rate: 0.00025
  adam_beta1: 0.9
  adam_beta2: 0.999
  adam_eps: 1.0e-8
  weight_decay: 0.0
  schedule:
    type: constant

loss:
  type: mse

q_learning:
  gamma: 0.99
  target_update_frequency: 100
  use_double_dqn: true

replay:
  capacity: 1000
  prioritized: false
```

### L2_partial_observability: Recurrent LSTM

```yaml
version: "1.0"
description: "Recurrent Q-network with LSTM for POMDP"

architecture:
  type: recurrent
  recurrent:
    token_embed_dim: 128
    q_head_hidden_dim: 128
    aggregator:
      type: attention
      num_heads: 4
    lstm:
      hidden_size: 128
      num_layers: 1
      dropout: 0.0

optimizer:
  type: adam
  learning_rate: 0.0001
  adam_beta1: 0.9
  adam_beta2: 0.999
  adam_eps: 1.0e-8
  weight_decay: 0.0
  schedule:
    type: constant

loss:
  type: huber
  huber_delta: 1.0

q_learning:
  gamma: 0.99
  target_update_frequency: 100
  use_double_dqn: true

replay:
  capacity: 5000
  prioritized: false  # PER not yet supported for recurrent
```

### Experimental: Dueling DQN

```yaml
version: "1.0"
description: "Experimental dueling DQN architecture"

architecture:
  type: dueling
  dueling:
    shared_layers: [256, 128]
    value_stream:
      hidden_layers: [128]
      activation: relu
    advantage_stream:
      hidden_layers: [128]
      activation: relu
    activation: relu
    dropout: 0.0
    layer_norm: true

optimizer:
  type: adam
  learning_rate: 0.00025
  adam_beta1: 0.9
  adam_beta2: 0.999
  adam_eps: 1.0e-8
  weight_decay: 0.0
  schedule:
    type: constant

loss:
  type: mse

q_learning:
  gamma: 0.99
  target_update_frequency: 100
  use_double_dqn: true

replay:
  capacity: 10000
  prioritized: false
```

### Experimental: Prioritized Experience Replay

```yaml
version: "1.0"
description: "Experimental prioritized experience replay"

architecture:
  type: feedforward
  feedforward:
    hidden_layers: [256, 128]
    activation: relu
    dropout: 0.0
    layer_norm: true

optimizer:
  type: adam
  learning_rate: 0.00025
  adam_beta1: 0.9
  adam_beta2: 0.999
  adam_eps: 1.0e-8
  weight_decay: 0.0
  schedule:
    type: constant

loss:
  type: mse

q_learning:
  gamma: 0.99
  target_update_frequency: 100
  use_double_dqn: true

replay:
  capacity: 50000
  prioritized: true
  priority_alpha: 0.6
  priority_beta: 0.4
  priority_beta_annealing: true
```

## Checkpoint Provenance: brain_hash

Every checkpoint includes a `brain_hash` field — the SHA256 of the **effective** brain
config **at the primary level**: `brain.yaml` merged with that level's `training.yaml`
overrides. It is **not** the hash of `brain.yaml`. Because `training.yaml` is per-level,
`brain_hash` is level-scoped, exactly as `drive_hash` is.

```python
from pathlib import Path

from townlet.config.brain_config import apply_training_overrides, compute_brain_hash
from townlet.universe.compiler import UniverseCompiler

universe = UniverseCompiler().compile(Path("configs/default_curriculum"), primary_level="L1_full_observability")

# The stamped value, reproduced:
level = universe.get_level(universe.metadata.primary_level)
brain_hash = compute_brain_hash(apply_training_overrides(universe.brain, level.training))
assert brain_hash == universe.brain_hash
```

Alongside it the checkpoint carries four **per-level content hashes** —
`curriculum_hash`, `bars_hash`, `affordances_hash`, `training_hash` — each compared on
resume. A change to any of those four files rejects the checkpoint with a
`Checkpoint <field> mismatch` error naming which one moved.

**Purpose:**
- Ensures checkpoints match brain configuration
- Prevents loading incompatible checkpoints
- Enables reproducible experiments

## References

- **DQN**: Mnih et al. 2015 - "Human-level control through deep reinforcement learning"
- **Double DQN**: van Hasselt et al. 2016 - "Deep Reinforcement Learning with Double Q-learning"
- **Dueling DQN**: Wang et al. 2016 - "Dueling Network Architectures for Deep Reinforcement Learning"
- **PER**: Schaul et al. 2016 - "Prioritized Experience Replay"

## Related Documentation

- **Training**: `docs/config-schemas/training.md` (training loop, exploration, curriculum)
- **Drive As Code**: `docs/config-schemas/drive_as_code.md` (reward functions)
- **Variables**: `docs/config-schemas/variables.md` (state space configuration)
- **Substrate**: Substrate configuration (grid size, topology, boundaries)

## See Also

- Curriculum configs: `configs/default_curriculum/levels/L0_0_minimal/` through
  `.../levels/L3_temporal_mechanics/`
  (⚠ corrected 2026-08-26 — the flat `configs/L0_0_minimal/` paths previously listed here are
  dead; levels live under a pack root, and `brain.yaml` is a **pack-level shared file** with no
  per-level override)
- ⚠ There is no `configs/experiments/` directory (the `dueling_network` and
  `prioritized_replay` example packs listed here previously do not exist). For a pack that
  actually declares `type: dueling`, see `configs/simple/brain.yaml` or
  `configs/L5_multi_agent/brain.yaml` — but note `docs/bugs/JANK-08-...md`: the `dueling` flag
  reaches the network builder and is then **ignored by the training path**.
